"""D-56 end-to-end, offline (Task 3): two REAL loopback `PeerRuntime`s with
`SharedSecretMiddleware` active, proving the channel where CI can see it --
no ngrok, no internet. This is the shape 05-03's smoke script repeats
through the real tunnel.

Unlike `tests/integration/two_peer_game.py` (in-memory `Client(server)`
transport, RESEARCH Pattern 5), the middleware only runs for a REAL ASGI
HTTP request -- so this module binds real loopback sockets via
`PeerRuntime.start()`, the same pattern `test_agent_lifecycle_resilience.
py::test_game_over_releases_the_port` already established.
"""

from __future__ import annotations

import asyncio
import dataclasses
import socket
import time

import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from pursuit.network.peer_runtime import PeerRuntime
from pursuit.shared.network_config import NetworkParams

_HEADER = "X-Pursuit-Secret-Test"
_SECRET = "correct-horse-battery-staple"


def _free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


async def _wait_until_accepting(port: int, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return
        except OSError:
            await asyncio.sleep(0.01)
    raise AssertionError(f"127.0.0.1:{port} never accepted a connection")


@pytest.fixture
async def guarded_pair(network_params: NetworkParams):
    """Two real, loopback-bound PeerRuntimes, both requiring the SAME
    shared secret, started and ready to accept connections. Ports are
    freshly probed (not the real config/*/network.json 8001/8002 pair) so
    this test never collides with a real dev-launched agent."""
    port_a, port_b = _free_port(), _free_port()
    net_a = dataclasses.replace(
        network_params, host="127.0.0.1", port=port_a,
        opponent_url=f"http://127.0.0.1:{port_b}/mcp",
    )
    net_b = dataclasses.replace(
        network_params, host="127.0.0.1", port=port_b,
        opponent_url=f"http://127.0.0.1:{port_a}/mcp",
    )
    runtime_a = PeerRuntime(net_a, "pursuit-secret-test-a", shared_secret=(_HEADER, _SECRET))
    runtime_b = PeerRuntime(net_b, "pursuit-secret-test-b", shared_secret=(_HEADER, _SECRET))
    await runtime_a.start()
    await runtime_b.start()
    await _wait_until_accepting(port_a, timeout=2.0)
    await _wait_until_accepting(port_b, timeout=2.0)
    try:
        yield runtime_a, runtime_b
    finally:
        await runtime_a.stop()
        await runtime_b.stop()


async def test_correct_secret_completes_a_real_call(guarded_pair):
    """A peer holding the exchanged secret plays normally."""
    runtime_a, _runtime_b = guarded_pair
    async with runtime_a.client() as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == {
        "handshake", "receive_move", "receive_barrier", "game_over", "receive_hint",
        "receive_commit", "receive_ack", "receive_reveal", "receive_final_reveal",
    }


async def test_missing_header_dies_at_the_boundary_before_mcp_routing(guarded_pair, caplog):
    """An unauthenticated request through the public URL dies at the
    boundary with 403 -- the PLAIN-TEXT "Forbidden" body (not an MCP
    JSON-RPC error) proves it never reached MCP session/tool routing."""
    _runtime_a, runtime_b = guarded_pair
    url = f"http://127.0.0.1:{runtime_b.params.port}/mcp"
    with caplog.at_level("WARNING"):
        async with httpx.AsyncClient() as raw:
            response = await raw.post(url, json={})
    assert response.status_code == 403
    assert response.text == "Forbidden"
    assert any("SharedSecretMiddleware rejected" in r.message for r in caplog.records)


async def test_wrong_secret_fails_every_call(guarded_pair):
    """A client with a wrong secret fails every call -- proven twice, on
    two independent attempts, never a one-off flake."""
    _runtime_a, runtime_b = guarded_pair
    transport = StreamableHttpTransport(
        runtime_b.params.opponent_url, headers={_HEADER: "not-the-real-secret"}
    )
    bad_client = Client(transport, timeout=runtime_b.params.response_timeout)

    for _attempt in range(2):
        with pytest.raises(httpx.HTTPStatusError, match="403"):
            async with bad_client:
                await bad_client.list_tools()
