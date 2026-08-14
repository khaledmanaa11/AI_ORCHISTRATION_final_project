"""D-62 follow-up: Step-0 declaration CONTENT verification -- split from
test_handshake_step0.py at the 150-code-line gate. Proves
`step0_sign.verify_declaration` now has a real production caller
(`handshake_step0._step0_verified`): a genuine declaration whose content
still hashes to its own digest agrees; a declaration mutated AFTER its
digest was computed is caught before move 1 (the actual gap this
follow-up closes); a digest-only peer (we cannot force an opponent team's
own implementation to publish content) still agrees.
"""

from __future__ import annotations

import pytest

from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.handshake import (
    HANDSHAKE_TURN,
    HandshakeKey,
    HandshakeOutcome,
    perform_handshake,
)
from pursuit.network.state_machine import State, TurnStateMachine
from pursuit.security import step0_collect, step0_sign
from tests.unit.test_handshake import FakeReporter, fake_caller

_CONFIG_DIGEST = config_digest("config/police/game_params.json")
_GENUINE_DECLARATION = step0_collect.collect_declaration(
    role="thief", team_code="khm-mn17", llm_name="claude-haiku-4-5",
    code_version="1.00", games_played=0,
)
_SIGNATURE = step0_sign.sign_declaration(_GENUINE_DECLARATION, secret=None)
_ENVELOPE = {"declaration": _GENUINE_DECLARATION, **_SIGNATURE}


def _reply(*, step0_digest: str | None, step0_declaration: dict | None) -> dict:
    payload = {HandshakeKey.DIGEST: _CONFIG_DIGEST}
    if step0_digest is not None:
        payload[HandshakeKey.STEP0_DIGEST] = step0_digest
    if step0_declaration is not None:
        payload[HandshakeKey.STEP0_DECLARATION] = step0_declaration
    return Envelope(
        type=MessageType.HANDSHAKE, turn=HANDSHAKE_TURN, sender="thief", payload=payload,
    ).to_dict()


async def _handshake(*, step0_digest, step0_declaration, shared_secret=None):
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_step0_digest="aa" * 32, shared_secret=shared_secret,
        call_peer=fake_caller(
            _reply(step0_digest=step0_digest, step0_declaration=step0_declaration),
        ),
    )
    return result, machine


async def test_declaration_content_matching_its_digest_agrees():
    result, machine = await _handshake(
        step0_digest=_SIGNATURE["digest"], step0_declaration=_ENVELOPE,
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "verified" in result.detail
    assert machine.state is State.HANDSHAKE
    assert result.peer_step0_declaration == _ENVELOPE


async def test_declaration_tampered_after_its_digest_was_computed_fails_before_move_1():
    """THE actual gap this follow-up closes: content mutated AFTER the
    digest was computed no longer hashes to its own claimed digest."""
    tampered = {**_ENVELOPE, "declaration": {**_GENUINE_DECLARATION, "role": "police"}}
    result, machine = await _handshake(
        step0_digest=_SIGNATURE["digest"], step0_declaration=tampered,
    )
    assert result.outcome is HandshakeOutcome.STEP0_MISMATCH
    assert result.aborted is True
    assert machine.state is State.ERROR
    assert "does not hash" in result.detail
    # House style (test_handshake_abort.py): the report names the FACT,
    # never accuses.
    lowered = result.detail.lower()
    assert "cheat" not in lowered and "lie" not in lowered and "opponent" not in lowered
    follow_up = machine.attempt(State.MY_TURN)
    assert follow_up.accepted is False


async def test_a_digest_only_peer_still_agrees():
    """An opponent team's own implementation might only ever send a
    digest -- we cannot force them to publish content; stays acceptable."""
    result, _machine = await _handshake(
        step0_digest=_SIGNATURE["digest"], step0_declaration=None,
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "digest-only" in result.detail
    assert result.peer_step0_declaration is None


@pytest.mark.parametrize("container", ["a-string", ["a", "list"], 7, 3.5])
async def test_a_declaration_container_that_is_not_an_object_does_not_kill_us(container):
    """05-10, INSTANCE 6 of `audit.py`'s boundary rule, found by sweeping for a
    sixth. `_step0_verified` did `remote_envelope.get("declaration")` on
    whatever the peer put in `step0_declaration`, so a str/list/number raised
    `AttributeError` -- measured: `'str' object has no attribute 'get'`.
    `evaluate`'s try/except wraps the DECODE block only, and on the outbound
    half this escaped `perform_handshake` into `run_agent` and killed the
    process AT THE HANDSHAKE, costing the league game before move 1.

    It resolves to the EXISTING digest-only outcome -- there is no content to
    verify -- named distinctly in the detail so the log still says what
    happened. Aborting instead would be a new false-accusation path against an
    honest foreign container shape (rules 16/22), and it would buy nothing: a
    peer wanting this outcome can already have it by sending no declaration."""
    result, machine = await _handshake(
        step0_digest=_SIGNATURE["digest"], step0_declaration=container,
    )

    assert result.outcome is HandshakeOutcome.AGREED
    assert result.aborted is False
    assert machine.state is State.HANDSHAKE
    assert "unreadable" in result.detail


async def test_declaration_hmac_mismatch_when_our_own_secret_is_wrong():
    """Confirms the HMAC branch of verify_declaration is ALSO reached from
    this real call site -- a wrong local secret fails HMAC verification
    even though the digest itself still matches."""
    secret = "match-negotiated-secret"
    signed = step0_sign.sign_declaration(_GENUINE_DECLARATION, secret=secret)
    envelope = {"declaration": _GENUINE_DECLARATION, **signed}

    agreed, _m1 = await _handshake(
        step0_digest=signed["digest"], step0_declaration=envelope, shared_secret=secret,
    )
    assert agreed.outcome is HandshakeOutcome.AGREED

    mismatched, machine = await _handshake(
        step0_digest=signed["digest"], step0_declaration=envelope, shared_secret="wrong-secret",
    )
    assert mismatched.outcome is HandshakeOutcome.STEP0_MISMATCH
    assert machine.state is State.ERROR
