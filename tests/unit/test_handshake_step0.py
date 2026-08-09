"""D-62 Step-0 digest-presence suite + D-61 game_id negotiation for the
D-08 handshake -- mirrors test_handshake_scent.py's own structure and
shared fakes, with a LOCAL envelope builder (never extending
test_handshake.py's own `peer_reply` a second time for this phase).

D-62 note (see handshake_evaluate.py's own docstring): the digest itself
is checked for PRESENCE, not equality against ours -- unlike SCENT_DIGEST,
a Step-0 declaration is inherently per-agent, so two roles' digests are
NEVER expected to match. Declaration CONTENT verification (the peer's
declaration hashing to its own claimed digest) is the sibling
test_handshake_step0_declaration.py, split out at the same gate.
"""

from __future__ import annotations

from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.handshake import (
    HANDSHAKE_TURN,
    HandshakeKey,
    HandshakeOutcome,
    perform_handshake,
    respond_to_handshake,
)
from pursuit.network.state_machine import State, TurnStateMachine
from tests.unit.test_handshake import FakeReporter, fake_caller

_CONFIG_DIGEST = config_digest("config/police/game_params.json")
_LOCAL_STEP0_DIGEST = "aa" * 32
_PEER_STEP0_DIGEST = "cc" * 32  # deliberately DIFFERENT -- declarations are per-agent


def _reply(
    digest: str, role: str, *, step0_digest: str | None = None, game_id: str | None = None,
) -> dict:
    """Local envelope builder carrying an optional STEP0_DIGEST/GAME_ID key."""
    payload = {HandshakeKey.DIGEST: digest}
    if step0_digest is not None:
        payload[HandshakeKey.STEP0_DIGEST] = step0_digest
    if game_id is not None:
        payload[HandshakeKey.GAME_ID] = game_id
    return Envelope(
        type=MessageType.HANDSHAKE, turn=HANDSHAKE_TURN, sender=role, payload=payload,
    ).to_dict()


async def test_a_present_but_different_step0_digest_still_agrees():
    """The core D-62 correction: unlike scent, step0 is presence-only."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_step0_digest=_LOCAL_STEP0_DIGEST,
        call_peer=fake_caller(_reply(_CONFIG_DIGEST, "thief", step0_digest=_PEER_STEP0_DIGEST)),
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "step0" in result.detail
    assert machine.state is State.HANDSHAKE


async def test_missing_step0_digest_aborts_before_move_1():
    """Case: we opted in, the peer's reply carries no step0 key at all --
    rule 24's actual failure mode (Step-0 never ran on the peer's side)."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_step0_digest=_LOCAL_STEP0_DIGEST,
        call_peer=fake_caller(_reply(_CONFIG_DIGEST, "thief")),  # no step0 key sent
    )
    assert result.outcome is HandshakeOutcome.STEP0_MISMATCH
    assert result.aborted is True
    assert machine.state is State.ERROR
    assert "absent" in result.detail
    follow_up = machine.attempt(State.MY_TURN)
    assert follow_up.accepted is False  # move 1 stays unreachable


async def test_local_not_opted_in_skips_step0_even_if_peer_sends_one():
    """Mirrors scent's own opt-out test: a call site not passing
    local_step0_digest gets config-only AGREEMENT regardless of the peer."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        call_peer=fake_caller(_reply(_CONFIG_DIGEST, "thief", step0_digest="anything-at-all")),
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "step0" not in result.detail


def test_game_id_negotiation_resolves_to_the_initiators_value():
    """THE load-bearing D-61 test (must_haves): the two sides propose
    DELIBERATELY DIFFERENT local_game_id values -- never the same string on
    both sides, so this can only pass if negotiation genuinely happened.
    The responder's own local value ("thief-uid-bbb") must NOT win."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    _, result = respond_to_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="thief",
        local_game_id="thief-uid-bbb",
        incoming=_reply(_CONFIG_DIGEST, "police", game_id="police-uid-aaa"),
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert result.peer_game_id == "police-uid-aaa"


def test_peer_game_id_is_present_even_on_a_mismatch():
    """Evidence, not just success -- an abort report still names what
    game_id the peer proposed."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    _, result = respond_to_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="thief",
        local_game_id="thief-uid-bbb", local_step0_digest=_LOCAL_STEP0_DIGEST,
        incoming=_reply(_CONFIG_DIGEST, "police", game_id="police-uid-aaa"),  # no step0 key
    )
    assert result.outcome is HandshakeOutcome.STEP0_MISMATCH
    assert result.peer_game_id == "police-uid-aaa"
