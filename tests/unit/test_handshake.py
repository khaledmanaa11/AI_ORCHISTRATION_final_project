"""Agreement + connectivity suite for the D-08 handshake (NET-03, NET-09).

No live socket, no subprocess: every path here runs through a fake caller.
The real in-memory FastMCP transport test and the 02-06 tool-name contract
pin live in tests/unit/test_handshake_client.py (split at the 150-code-line
gate; shared fakes below are imported from there). Failure paths raise
``McpError`` -- NOT ``MCPError`` as 02-RESEARCH.md's cited snippet spells it;
see 02-07-SUMMARY.md's finding that the installed fastmcp 3.4.5 / mcp
packages spell the class ``McpError`` (mixed case).
"""

from mcp import McpError
from mcp.types import ErrorData

from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.handshake import (
    HANDSHAKE_TURN,
    HandshakeKey,
    HandshakeOutcome,
    perform_handshake,
)
from pursuit.network.state_machine import State, TransitionSeverity, TurnStateMachine

_FAKE_RPC_ERROR_CODE = -1  # test scaffolding only; any JSON-RPC error code works


class FakeReporter:
    """Records every reporter call. Mirrors 02-03's TransitionReporter Protocol."""

    def __init__(self):
        self.calls = []

    def __call__(self, *, current, target, severity, reason):
        self.calls.append(
            {"current": current, "target": target, "severity": severity, "reason": reason}
        )


def fake_caller(reply: dict):
    """Return a HandshakeCaller that answers with `reply` (an envelope dict)."""

    async def _call(envelope):
        return reply

    return _call


def raising_caller(exc: BaseException):
    """Return a HandshakeCaller that raises `exc` instead of answering."""

    async def _call(envelope):
        raise exc

    return _call


def peer_reply(digest: str, role: str) -> dict:
    """Build the reply envelope dict a well-behaved peer returns."""
    return Envelope(
        type=MessageType.HANDSHAKE,
        turn=HANDSHAKE_TURN,
        sender=role,
        payload={HandshakeKey.DIGEST: digest},
    ).to_dict()


async def test_matching_digests_reach_handshake_state():
    """D-08 happy path through a fake caller."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    digest = config_digest("config/police/game_params.json")
    result = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=digest,
        local_role="police",
        call_peer=fake_caller(peer_reply(digest, "thief")),
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert result.agreed is True and result.aborted is False
    assert result.local_digest == digest and result.remote_digest == digest
    assert result.peer_role == "thief"
    assert machine.state is State.HANDSHAKE
    assert reporter.calls == []
    # ...and the path to move 1 is OPEN — the exact contrast with the D-15 abort.
    assert machine.attempt(State.MY_TURN).accepted is True
    assert machine.state is State.MY_TURN


async def test_real_config_pair_agrees():
    """Rule 11 / D-15 end to end on the ACTUAL repo files: both sides really agree."""
    police = config_digest("config/police/game_params.json")
    thief = config_digest("config/thief/game_params.json")
    assert police == thief
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=police,
        local_role="police",
        call_peer=fake_caller(peer_reply(thief, "thief")),
    )
    assert result.outcome is HandshakeOutcome.AGREED


async def test_unreachable_peer_is_not_a_mismatch():
    """D-08 / startup-skew guard. The peer is not listening yet."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    digest = config_digest("config/police/game_params.json")
    exc = McpError(ErrorData(code=_FAKE_RPC_ERROR_CODE, message="no route"))
    result = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=digest,
        local_role="police",
        call_peer=raising_caller(exc),
    )
    assert result.outcome is HandshakeOutcome.UNREACHABLE
    assert result.remote_digest is None
    assert result.outcome is not HandshakeOutcome.CONFIG_MISMATCH
    assert machine.state is not State.ERROR  # transient — the caller may retry
    assert result.aborted is False
    assert len(reporter.calls) == 1
    assert reporter.calls[0]["severity"] is TransitionSeverity.RECOVERABLE


async def test_retry_after_unreachable_still_agrees():
    """Proves design note 3: a second perform_handshake on the SAME machine works."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    digest = config_digest("config/police/game_params.json")
    exc = McpError(ErrorData(code=_FAKE_RPC_ERROR_CODE, message="no route"))

    first = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=digest,
        local_role="police",
        call_peer=raising_caller(exc),
    )
    assert first.outcome is HandshakeOutcome.UNREACHABLE

    second = await perform_handshake(
        machine=machine,
        reporter=reporter,
        local_digest=digest,
        local_role="police",
        call_peer=fake_caller(peer_reply(digest, "thief")),
    )
    assert second.outcome is HandshakeOutcome.AGREED
    assert machine.state is State.HANDSHAKE
    assert any(c["severity"] is TransitionSeverity.RECOVERABLE for c in reporter.calls)
