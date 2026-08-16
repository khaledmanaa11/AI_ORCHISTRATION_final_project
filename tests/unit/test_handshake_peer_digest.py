"""05-12 / G9: NO peer-controlled digest slot can kill us at the handshake.

A sweep of the WHOLE corridor rather than one function, because that is the
shape of the defect: `security/audit.py`'s boundary rule has now produced
NINE instances in this phase, and each was found because someone probed one
door further than the last sweep. Four peer-controlled values reach
`secrets.compare_digest` before move 1 -- `payload.digest` (config),
`payload.scent_digest`, `payload.step0_digest`, and the `hmac` inside
`payload.step0_declaration` -- and every one of them raised `TypeError` on a
non-str at HEAD `0437559`, escaping `evaluate()`, escaping `perform_handshake`
and `respond_to_handshake` (whose own docstring says "Pure, synchronous, never
raises"), and escaping `run_agent`, whose only guard is `except ToolError`.

The consequence is the artifact this whole phase exists to prevent: the
process dies BEFORE move 1, so WE are the side that published no nonces
(rule 36), with no verdict in our own log and exit code 1 -- which
REMOTE-ROUND-RUNBOOK.md:195-196 teaches the operator to read as a technical
loss recorded against us.

Every case below therefore asserts a NAMED outcome. Split into its own file
rather than added to test_handshake.py (134/150) or test_handshake_step0.py,
so the corridor is readable in one place and neither host file is compressed.
"""

from __future__ import annotations

import pytest

from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import EnvelopeKey, MessageType
from pursuit.network.handshake import (
    HANDSHAKE_TURN,
    HandshakeKey,
    HandshakeOutcome,
    perform_handshake,
    respond_to_handshake,
)
from pursuit.network.state_machine import State, TurnStateMachine
from pursuit.security import step0_sign
from tests.unit.test_handshake import FakeReporter, fake_caller

_CONFIG_DIGEST = config_digest("config/police/game_params.json")
_LOCAL_SCENT_DIGEST = "bb" * 32
_LOCAL_STEP0_DIGEST = "aa" * 32
_DECLARATION = {"role": "thief", "team_code": "khm-mn17"}
_HOSTILE = (1234, [1, 2], {"a": 1}, True, 3.5)


def _raw(**payload) -> dict:
    """A raw handshake envelope dict -- built by hand, never via `build_offer`,
    because the whole point is a payload value no honest builder would emit."""
    return {
        EnvelopeKey.TYPE: MessageType.HANDSHAKE.value,
        EnvelopeKey.TURN: HANDSHAKE_TURN,
        EnvelopeKey.SENDER: "thief",
        EnvelopeKey.PAYLOAD: payload,
    }


async def _perform(raw: dict, **opt_in):
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    return await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST,
        local_role="police", call_peer=fake_caller(raw), **opt_in,
    )


@pytest.mark.parametrize("hostile", _HOSTILE)
async def test_a_non_str_config_digest_is_a_named_mismatch(hostile):
    """Slot 1, UNCONDITIONAL on every handshake either side ever performs."""
    result = await _perform(_raw(digest=hostile))
    assert result.outcome is HandshakeOutcome.CONFIG_MISMATCH
    assert "not a string" in result.detail
    assert result.aborted is True


@pytest.mark.parametrize("hostile", _HOSTILE)
async def test_a_non_str_scent_digest_is_a_named_mismatch(hostile):
    """Slot 2, live in production: `agent_entrypoint.py:80,85` ALWAYS supplies
    `local_scent_digest`, so this branch is never skipped in a real game."""
    result = await _perform(
        _raw(digest=_CONFIG_DIGEST, scent_digest=hostile),
        local_scent_digest=_LOCAL_SCENT_DIGEST,
    )
    assert result.outcome is HandshakeOutcome.SCENT_MISMATCH
    assert "scent digest present in peer payload but not a string" in result.detail


@pytest.mark.parametrize("hostile", _HOSTILE)
async def test_a_non_str_step0_digest_is_downgraded_never_an_abort(hostile):
    """Slot 3, found by probe DURING 05-12 and outside its written scope: it
    only fires when the peer ALSO sends a declaration, which is why 05-10's
    sweep -- which stopped at the declaration CONTAINER -- did not reach it.

    Downgraded, NOT aborted. The first draft of this fix routed it through
    `unusable_peer_digest` and turned it into a STEP0_MISMATCH, which the
    control below caught: that would have converted a peer this codebase
    AGREED with at `0437559` into a technical loss over a JSON type on a
    field we never compare on that path (rules 16/22)."""
    result = await _perform(
        _raw(digest=_CONFIG_DIGEST, step0_digest=hostile,
             step0_declaration={"declaration": _DECLARATION, "hmac": None}),
        local_step0_digest=_LOCAL_STEP0_DIGEST,
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "unreadable, nothing to verify content against" in result.detail


@pytest.mark.parametrize("hostile", _HOSTILE)
async def test_a_non_str_step0_digest_alone_agrees_exactly_as_it_did_before(hostile):
    """THE NO-NEW-ACCUSATION CONTROL for slot 3. Measured at `0437559`:
    `step0_digest=1234` with NO declaration returned `agreed: 'config digests
    agree; step0 digest present (declaration content not sent, digest-only)'`.
    That verdict, detail string included, must survive this plan untouched --
    a containment that costs an already-agreeing peer the game is not a
    containment, it is the defect wearing a fix's clothes."""
    result = await _perform(
        _raw(digest=_CONFIG_DIGEST, step0_digest=hostile),
        local_step0_digest=_LOCAL_STEP0_DIGEST,
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert result.detail == (
        "config digests agree; step0 digest present "
        "(declaration content not sent, digest-only)"
    )


@pytest.mark.parametrize("hostile", _HOSTILE)
async def test_a_non_str_declaration_hmac_is_downgraded_never_an_abort(hostile):
    """Slot 4, the same probe. Resolved DIFFERENTLY on purpose: the hmac is
    OPTIONAL and its ABSENCE already agrees, so an unreadable one is treated
    as unsigned and named in the detail. Accusing here would invent a
    false-accusation path (rules 16/22) with no evasion closed in return."""
    result = await _perform(
        _raw(digest=_CONFIG_DIGEST,
             step0_digest=step0_sign.digest_declaration(_DECLARATION),
             step0_declaration={"declaration": _DECLARATION, "hmac": hostile}),
        local_step0_digest=_LOCAL_STEP0_DIGEST, shared_secret="a-shared-secret",
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "hmac unreadable -- treated as unsigned" in result.detail


def test_respond_to_handshake_really_is_pure_and_never_raises():
    """Pins the docstring claim the probe disproved. The RESPONDER half runs
    inside the FastMCP tool body, so a raise there is our own server dying on
    an inbound message we chose to answer."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    reply, result = respond_to_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST,
        local_role="thief", local_scent_digest=_LOCAL_SCENT_DIGEST,
        incoming=_raw(digest={"nested": "object"}, scent_digest=[1]),
    )
    assert result.outcome is HandshakeOutcome.CONFIG_MISMATCH
    assert reply[EnvelopeKey.TYPE] == MessageType.HANDSHAKE.value
    assert machine.state is State.ERROR
    assert machine.attempt(State.MY_TURN).accepted is False  # move 1 unreachable


async def test_the_honest_controls_stay_exactly_where_they_were():
    """The three outcomes that must NOT have moved: an agreeing peer still
    agrees, a wrong-but-str digest is still `config_mismatch`, and an absent
    digest is still `malformed_reply` (it never reaches the comparison at
    all -- `payload["digest"]` is a plain lookup)."""
    agreed = await _perform(_raw(digest=_CONFIG_DIGEST))
    assert agreed.outcome is HandshakeOutcome.AGREED

    differed = await _perform(_raw(digest="b" * 64))
    assert differed.outcome is HandshakeOutcome.CONFIG_MISMATCH
    assert "mismatch" in differed.detail and "not a string" not in differed.detail

    absent = await _perform(_raw(scent_digest=_LOCAL_SCENT_DIGEST))
    assert absent.outcome is HandshakeOutcome.MALFORMED_REPLY
    assert HandshakeKey.DIGEST in absent.detail
