"""D-15 abort suite: mismatch aborts before move 1, symmetric responder abort,
malformed replies, and ToolError-is-not-unreachable (RESEARCH Pitfall 4).

No live socket: failure paths run through a fake caller. Shared fakes
(FakeReporter/fake_caller/raising_caller/peer_reply) live in
tests/unit/test_handshake.py and are imported here, not duplicated
(QUAL-02) -- the same split pattern 02-07 used for test_deadline_retry.py.
"""

import pytest
from fastmcp.exceptions import ToolError

from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.handshake import (
    HandshakeKey,
    HandshakeOutcome,
    perform_handshake,
    respond_to_handshake,
)
from pursuit.network.state_machine import State, TransitionSeverity, TurnStateMachine
from tests.unit.test_handshake import FakeReporter, fake_caller, peer_reply, raising_caller

_LOCAL_DIGEST = config_digest("config/police/game_params.json")
_REMOTE_MISMATCH_DIGEST = "0" * len(_LOCAL_DIGEST)  # structurally valid, deliberately different


async def test_mismatched_digests_abort_before_move_1():
    """THE core D-15 / NET-09 / rule-11 assertion."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=_LOCAL_DIGEST,
        local_role="police",
        call_peer=fake_caller(peer_reply(_REMOTE_MISMATCH_DIGEST, "thief")),
    )
    assert result.outcome is HandshakeOutcome.CONFIG_MISMATCH
    assert result.aborted is True
    assert machine.state is State.ERROR
    assert machine.state is not State.MY_TURN  # move 1 is unreachable
    # and it STAYS unreachable — ERROR is terminal (02-03):
    follow_up = machine.attempt(State.MY_TURN)
    assert follow_up.accepted is False
    assert machine.state is State.ERROR


async def test_abort_report_records_both_digests():
    """Truthful-evidence assertion (RULES.md; design note 6)."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=_LOCAL_DIGEST,
        local_role="police",
        call_peer=fake_caller(peer_reply(_REMOTE_MISMATCH_DIGEST, "thief")),
    )
    assert _LOCAL_DIGEST in result.detail and _REMOTE_MISMATCH_DIGEST in result.detail
    abort_reports = [c for c in reporter.calls if c["target"] is State.ERROR]
    assert len(abort_reports) == 1
    reason = abort_reports[0]["reason"]
    assert _LOCAL_DIGEST in reason and _REMOTE_MISMATCH_DIGEST in reason
    assert abort_reports[0]["severity"] is TransitionSeverity.PROTOCOL_VIOLATION
    # and the report accuses no one:
    assert "opponent" not in reason.lower() and "cheat" not in reason.lower()


def test_responder_replies_with_its_digest_even_on_mismatch():
    """Design note 4 — the responder must not raise, and must still hand back its digest."""
    peer_reporter = FakeReporter()
    peer_machine = TurnStateMachine(peer_reporter)
    reply, result = respond_to_handshake(
        machine=peer_machine,
        reporter=peer_reporter,
        local_digest=_LOCAL_DIGEST,
        local_role="thief",
        incoming=peer_reply(_REMOTE_MISMATCH_DIGEST, "police"),
    )
    assert result.outcome is HandshakeOutcome.CONFIG_MISMATCH
    decoded = Envelope.from_dict(reply)
    assert decoded.payload[HandshakeKey.DIGEST] == _LOCAL_DIGEST  # our digest, not the peer's
    assert decoded.sender == "thief"
    assert decoded.type is MessageType.HANDSHAKE


def test_responder_aborts_symmetrically():
    """NET-03 — the responder escalates its OWN machine; it does not wait to be told."""
    peer_reporter = FakeReporter()
    peer_machine = TurnStateMachine(peer_reporter)
    _, result = respond_to_handshake(
        machine=peer_machine,
        reporter=peer_reporter,
        local_digest=_LOCAL_DIGEST,
        local_role="thief",
        incoming=peer_reply(_REMOTE_MISMATCH_DIGEST, "police"),
    )
    assert peer_machine.state is State.ERROR
    assert result.aborted is True

    # And the agreement case does advance it, not abort it:
    agree_reporter = FakeReporter()
    agree_machine = TurnStateMachine(agree_reporter)
    _, agree_result = respond_to_handshake(
        machine=agree_machine,
        reporter=agree_reporter,
        local_digest=_LOCAL_DIGEST,
        local_role="thief",
        incoming=peer_reply(_LOCAL_DIGEST, "police"),
    )
    assert agree_machine.state is State.HANDSHAKE
    assert agree_result.aborted is False


async def test_malformed_peer_reply_is_protocol_violation():
    """A reply that is not a valid envelope is a protocol violation, NOT connectivity."""
    malformed_shapes = ({}, {**peer_reply(_LOCAL_DIGEST, "thief"), "payload": {}})
    for bad_reply in malformed_shapes:
        reporter = FakeReporter()
        machine = TurnStateMachine(reporter)
        result = await perform_handshake(
            machine=machine,
            reporter=reporter,
            local_digest=_LOCAL_DIGEST,
            local_role="police",
            call_peer=fake_caller(bad_reply),
        )
        assert result.outcome is HandshakeOutcome.MALFORMED_REPLY
        assert result.outcome is not HandshakeOutcome.UNREACHABLE
        assert machine.state is State.ERROR
        assert result.remote_digest is None


async def test_tool_error_is_not_swallowed():
    """RESEARCH Pitfall 4 — only McpError means "unreachable"."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    with pytest.raises(ToolError):
        await perform_handshake(
            machine=machine,
            reporter=reporter,
            local_digest=_LOCAL_DIGEST,
            local_role="police",
            call_peer=raising_caller(ToolError("peer blew up")),
        )
