"""Tool-dispatch tests: enqueue/ack, {x, y} round-trip, the handshake seam,
and malformed-payload rejection. Split from test_tools.py (registration /
signature / coroutine-function guards) to stay within the 150-code-line
limit — same module under test, same in-memory Client(mcp) transport, no
socket anywhere in this file.
"""

import asyncio

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from pursuit.network.tools import register_tools

from pursuit.network.envelope import MessageType


def _server_with_queue() -> tuple[FastMCP, asyncio.Queue]:
    queue: asyncio.Queue = asyncio.Queue()
    mcp = FastMCP("pursuit-test-peer")
    register_tools(mcp, queue)
    return mcp, queue


async def test_receive_move_enqueues_and_acks(network_params, default_params):
    """D-07 + NET-08 happy path — the enqueue-then-ack round trip.

    The wait_for bound is the point: a handler that blocked waiting on the
    opponent (instead of enqueuing and returning) would never return here.
    """
    x, y = default_params.thief_start
    mcp, queue = _server_with_queue()
    async with Client(mcp) as client:
        result = await asyncio.wait_for(
            client.call_tool(
                "receive_move",
                {"turn": 1, "sender": "police", "payload": {"x": x, "y": y}},
            ),
            timeout=network_params.response_timeout,
        )
    assert result.data["status"] == "ack"
    assert queue.qsize() == 1
    envelope = queue.get_nowait()
    assert envelope.type is MessageType.MOVE
    assert envelope.turn == 1
    assert envelope.sender == "police"
    assert envelope.payload["x"] == x
    assert envelope.payload["y"] == y


async def test_handler_does_not_wait_for_a_consumer(network_params, default_params):
    """D-07 structural proof: nothing drains the queue, both calls still ack."""
    x, y = default_params.thief_start
    payload = {"x": x, "y": y}
    mcp, queue = _server_with_queue()
    async with Client(mcp) as client:
        first = await client.call_tool(
            "receive_move", {"turn": 1, "sender": "police", "payload": payload}
        )
        second = await client.call_tool(
            "receive_move", {"turn": 2, "sender": "police", "payload": payload}
        )
    assert first.data["status"] == "ack"
    assert second.data["status"] == "ack"
    assert queue.qsize() == 2


async def test_receive_barrier_and_game_over_and_handshake_ack(network_params):
    """Phase-2 stub bodies: ack + enqueue for the remaining three tools."""
    mcp, queue = _server_with_queue()
    cases = (
        ("receive_barrier", MessageType.BARRIER),
        ("game_over", MessageType.GAME_OVER),
        ("handshake", MessageType.HANDSHAKE),
    )
    async with Client(mcp) as client:
        for turn, (tool_name, message_type) in enumerate(cases):
            result = await client.call_tool(
                tool_name, {"turn": turn, "sender": "police", "payload": {}}
            )
            assert result.data["status"] == "ack"
            envelope = queue.get_nowait()
            assert envelope.type is message_type
    assert queue.qsize() == 0


async def test_handshake_without_a_handler_keeps_the_generic_ack(network_params):
    """The DEFAULT branch, pinned on its own so adding the seam cannot
    silently change it — 02-08's fake-peer tests rely on this behaviour."""
    mcp, queue = _server_with_queue()
    async with Client(mcp) as client:
        result = await client.call_tool(
            "handshake", {"turn": 0, "sender": "police", "payload": {}}
        )
    assert result.data["status"] == "ack"
    assert queue.qsize() == 1


async def test_injected_handshake_handler_replaces_the_generic_ack(network_params):
    """THE SEAM TEST — 02-09 binds 02-08's respond_to_handshake through here."""
    calls: list[tuple] = []

    async def _fake_responder(turn: int, sender: str, payload: dict) -> dict:
        calls.append((turn, sender, payload))
        return {
            "type": "handshake",
            "turn": turn,
            "sender": "thief",
            "payload": {"digest": "0000"},
        }

    queue: asyncio.Queue = asyncio.Queue()
    mcp = FastMCP("pursuit-test-peer")
    register_tools(mcp, queue, handshake_handler=_fake_responder)
    async with Client(mcp) as client:
        result = await client.call_tool(
            "handshake", {"turn": 0, "sender": "police", "payload": {}}
        )
    assert result.data == {
        "type": "handshake",
        "turn": 0,
        "sender": "thief",
        "payload": {"digest": "0000"},
    }
    assert "status" not in result.data
    assert calls == [(0, "police", {})]
    assert queue.qsize() == 0


async def test_injected_handshake_handler_does_not_affect_the_other_tools(
    network_params, default_params
):
    """The seam is handshake-only — the other three tools keep the generic ack."""
    x, y = default_params.thief_start

    async def _fake_responder(turn: int, sender: str, payload: dict) -> dict:
        return {"type": "handshake", "turn": turn, "sender": "thief", "payload": {}}

    queue: asyncio.Queue = asyncio.Queue()
    mcp = FastMCP("pursuit-test-peer")
    register_tools(mcp, queue, handshake_handler=_fake_responder)
    async with Client(mcp) as client:
        result = await client.call_tool(
            "receive_move",
            {"turn": 1, "sender": "police", "payload": {"x": x, "y": y}},
        )
    assert result.data["status"] == "ack"
    assert queue.qsize() == 1


async def test_malformed_payload_is_rejected_and_nothing_enqueued(network_params):
    """ERROR CASE — payload wrong type, missing argument, and blank sender
    all raise `fastmcp.exceptions.ToolError` through the Client and leave
    the queue empty (verified directly against the installed FastMCP)."""
    mcp, queue = _server_with_queue()
    bad_calls = (
        {"turn": 1, "sender": "police", "payload": "not-a-dict"},
        {"turn": 1, "sender": "police"},
        {"turn": 1, "sender": "", "payload": {}},
    )
    async with Client(mcp) as client:
        for arguments in bad_calls:
            with pytest.raises(ToolError):
                await client.call_tool("receive_move", arguments)
            assert queue.qsize() == 0
