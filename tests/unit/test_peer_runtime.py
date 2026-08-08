"""Runtime tests: factory isolation, no module-level server, start/stop
lifecycle via an injected fake serve, client built from NetworkParams, and
the handshake_handler seam forwarded through both construction paths.

D-05's tool surface itself is covered by test_tools.py/test_tools_dispatch.py;
this file is NET-02 (no shared runtime state) and NET-03 (server + client in
one process) plus PeerRuntime's own start/stop lifecycle. No test here opens
a socket, spawns a subprocess, or contacts the opponent.
"""

import ast
import asyncio
import pathlib

from fastmcp import Client

from pursuit.network.peer_runtime import PeerRuntime, build_server
from pursuit.shared.network_config import load_network_config

_THIEF_CONFIG = (
    pathlib.Path(__file__).parent.parent.parent / "config" / "thief" / "network.json"
)


async def _fake_serve(started: asyncio.Event) -> None:
    """Runs forever until cancelled; binds nothing (socket-free lifecycle test)."""
    started.set()
    await asyncio.Event().wait()


async def test_build_server_registers_the_tool_surface():
    """build_server wires register_tools onto a freshly constructed FastMCP."""
    queue: asyncio.Queue = asyncio.Queue()
    mcp = build_server(queue, "pursuit-test-peer")
    async with Client(mcp) as client:
        names = {t.name for t in await client.list_tools()}
    assert names == {"handshake", "receive_move", "receive_barrier", "game_over", "receive_hint"}


async def test_two_runtimes_share_no_runtime_state(network_params):
    """NET-02 — the disqualification test: nothing crosses between two agents."""
    police = PeerRuntime(network_params, "pursuit-police")
    thief = PeerRuntime(load_network_config(_THIEF_CONFIG), "pursuit-thief")
    assert police.server is not thief.server
    assert police.queue is not thief.queue
    police.queue.put_nowait(object())
    assert thief.queue.qsize() == 0
    assert police.params.port != thief.params.port


def test_no_module_level_server_instance():
    """Structural guard for NET-02 — no module-level FastMCP singleton."""
    for path in (
        "src/pursuit/network/tools.py",
        "src/pursuit/network/peer_runtime.py",
    ):
        tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
        for node in tree.body:
            assert not (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", "") == "FastMCP"
            )


async def test_client_is_built_from_network_params(network_params):
    """NET-03 — the same process holds a client aimed at the opponent.

    fastmcp 3.4.5's Client exposes no public timeout attribute (only the
    private `_session_kwargs['read_timeout_seconds']`; verified by probe,
    see 02-06-SUMMARY.md), so per this plan's documented fallback this test
    pins client identity (a fresh Client per call, so the caller controls
    the context-manager lifetime) and the opponent URL via the public
    `transport.url` attribute rather than a private field.
    """
    runtime = PeerRuntime(network_params, "pursuit-police")
    client_a = runtime.client()
    client_b = runtime.client()
    assert isinstance(client_a, Client)
    assert client_a is not client_b
    assert client_a.transport.url == network_params.opponent_url


async def test_handshake_handler_is_forwarded_by_build_server_and_by_peer_runtime(
    network_params,
):
    """The seam has to survive BOTH construction paths (02-09 builds a
    PeerRuntime, never a bare server) and the default must stay inverted."""

    async def _fake_responder(turn: int, sender: str, payload: dict) -> dict:
        return {
            "type": "handshake",
            "turn": turn,
            "sender": "thief",
            "payload": {"digest": "0000"},
        }

    queue: asyncio.Queue = asyncio.Queue()
    mcp = build_server(queue, "pursuit-test-peer", handshake_handler=_fake_responder)
    async with Client(mcp) as client:
        result = await client.call_tool(
            "handshake", {"turn": 0, "sender": "police", "payload": {}}
        )
    assert "status" not in result.data
    assert result.data["payload"]["digest"] == "0000"

    handled_runtime = PeerRuntime(
        network_params, "pursuit-police", handshake_handler=_fake_responder
    )
    async with Client(handled_runtime.server) as client:
        result = await client.call_tool(
            "handshake", {"turn": 0, "sender": "police", "payload": {}}
        )
    assert "status" not in result.data
    assert result.data["payload"]["digest"] == "0000"

    default_runtime = PeerRuntime(network_params, "pursuit-police")
    async with Client(default_runtime.server) as client:
        result = await client.call_tool(
            "handshake", {"turn": 0, "sender": "police", "payload": {}}
        )
    assert result.data["status"] == "ack"


async def test_start_then_stop_cancels_the_server_task(network_params):
    """Lifecycle without a socket, via the injected `serve` seam."""
    started = asyncio.Event()
    runtime = PeerRuntime(
        network_params, "pursuit-police", serve=lambda: _fake_serve(started)
    )
    await runtime.start()
    await asyncio.wait_for(started.wait(), timeout=network_params.response_timeout)
    task = runtime._server_task
    await runtime.stop()
    assert task.cancelled() or task.done()
    await runtime.stop()  # a second stop() must be a no-op, not raise


async def test_stop_before_start_is_a_noop(network_params):
    """ERROR CASE — stopping a runtime that never started must not raise."""
    runtime = PeerRuntime(network_params, "pursuit-police")
    await runtime.stop()
