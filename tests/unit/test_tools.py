"""Tool-surface tests: registration, wire signatures, coroutine-function guard.

D-05 pins the five-tool surface (D-47 adds receive_hint); NET-08 needs typed
envelope fields on the wire. Split from test_tools_dispatch.py (enqueue/ack/
seam/malformed-payload behavior) to stay within the 150-code-line limit —
same module under test, same in-memory Client(mcp) transport, no socket in
either file.
"""

import asyncio

from fastmcp import Client, FastMCP

from pursuit.network.envelope import MessageType
from pursuit.network.tools import register_tools

_TOOL_NAMES = {"handshake", "receive_move", "receive_barrier", "game_over", "receive_hint"}


def _server_with_queue() -> tuple[FastMCP, asyncio.Queue]:
    """A fresh server + queue pair, socket-free (in-memory Client transport)."""
    queue: asyncio.Queue = asyncio.Queue()
    mcp = FastMCP("pursuit-test-peer")
    register_tools(mcp, queue)
    return mcp, queue


async def test_all_five_tools_registered():
    """D-05, D-47: exactly the five named tools registered — not a subset, not a superset."""
    mcp, _ = _server_with_queue()
    async with Client(mcp) as client:
        names = {t.name for t in await client.list_tools()}
    assert names == _TOOL_NAMES


async def test_tool_signatures_carry_envelope_fields():
    """D-06: turn/sender/payload are on the wire schema for every tool."""
    mcp, _ = _server_with_queue()
    async with Client(mcp) as client:
        tools = {t.name: t for t in await client.list_tools()}
    for name in _TOOL_NAMES:
        properties = tools[name].inputSchema["properties"]
        assert {"turn", "sender", "payload"} <= properties.keys()


async def test_every_handler_is_a_coroutine_function():
    """RESEARCH Pitfall 2 guard: a plain `def` body runs in a worker
    threadpool and could not safely touch the main-loop asyncio.Queue.

    `mcp.get_tools()` (plural, dict-returning) does NOT exist on the
    installed FastMCP 3.4.5 — the real accessor is the per-name coroutine
    `mcp.get_tool(name) -> FunctionTool`, whose wrapped callable lives on
    `.fn` (verified by probe; see 02-06-SUMMARY.md).
    """
    mcp, _ = _server_with_queue()
    for name in _TOOL_NAMES:
        tool = await mcp.get_tool(name)
        assert asyncio.iscoroutinefunction(tool.fn)


async def test_receive_hint_acknowledges_without_awaiting_the_game_loop():
    """D-47: receive_hint acks immediately -- nothing ever drains the
    queue in this test, proving the ack does not wait on the game loop."""
    mcp, queue = _server_with_queue()
    payload = {"text": "heading uptown past the park", "intent": "truth", "turn": 1}
    async with Client(mcp) as client:
        result = await client.call_tool(
            "receive_hint", {"turn": 1, "sender": "police", "payload": payload}
        )
    assert result.data["status"] == "ack"
    assert queue.qsize() == 1
    envelope = queue.get_nowait()
    assert envelope.type is MessageType.HINT
    assert envelope.payload == payload
