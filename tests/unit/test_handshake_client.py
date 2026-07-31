"""Real-transport half of the D-08 handshake suite (NET-03, NET-08, NET-09).

Split from tests/unit/test_handshake.py at the 150-code-line gate (QUAL-02:
the shared fakes live there and are imported here, not duplicated) -- same
split pattern 02-07 used for test_deadline_retry.py. These two tests are the
only ones in the plan that touch a real FastMCP server; both still run over
the in-memory Client(server) transport (RESEARCH Pattern 5), never a socket.
"""

import asyncio

from fastmcp import Client, FastMCP

from pursuit.network.config_hash import config_digest
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.handshake import (
    HANDSHAKE_TOOL,
    HandshakeOutcome,
    make_client_caller,
    perform_handshake,
    respond_to_handshake,
)
from pursuit.network.peer_runtime import build_server
from pursuit.network.state_machine import State, TurnStateMachine
from tests.unit.test_handshake import FakeReporter


async def test_agreed_over_in_memory_client():
    """NET-03 + D-08 through the REAL FastMCP transport, with a test-local peer."""
    digest = config_digest("config/police/game_params.json")
    peer_mcp = FastMCP("test-peer")
    peer_reporter = FakeReporter()
    peer_machine = TurnStateMachine(peer_reporter)

    @peer_mcp.tool
    async def handshake(turn: int, sender: str, payload: dict) -> dict:
        incoming = Envelope(
            type=MessageType.HANDSHAKE, turn=turn, sender=sender, payload=payload
        ).to_dict()
        reply, _ = respond_to_handshake(
            machine=peer_machine,
            reporter=peer_reporter,
            local_digest=digest,
            local_role="thief",
            incoming=incoming,
        )
        return reply

    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    async with Client(peer_mcp) as client:
        result = await perform_handshake(
            machine=machine,
            reporter=reporter,
            local_digest=digest,
            local_role="police",
            call_peer=make_client_caller(client),
        )
    assert result.outcome is HandshakeOutcome.AGREED
    assert result.remote_digest == digest
    assert machine.state is State.HANDSHAKE
    assert peer_machine.state is State.HANDSHAKE  # the responder advanced too (symmetry)


async def test_handshake_tool_name_matches_02_06():
    """Contract pin against 02-06 — read-only, never edits tools.py or peer_runtime.py."""
    mcp = build_server(asyncio.Queue(), "pursuit-handshake-contract")
    async with Client(mcp) as client:
        names = {t.name for t in await client.list_tools()}
    assert HANDSHAKE_TOOL == "handshake"
    assert HANDSHAKE_TOOL in names
