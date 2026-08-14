"""05-09: the REAL-SOCKET anchor for the connect-failure containment.

Everything else about this fix is asserted against constructed exceptions. This file asserts it
against the thing itself: a real `fastmcp.Client`, built exactly the way `PeerRuntime.client()
builds it (an explicit `StreamableHttpTransport`, never a bare URL string -- D-56/Pitfall 1),
pointed at a port with nothing listening on it. That is the situation a peer that has already
torn down really presents, and it is the one the 2026-08-13 remote round produced.

Why it has to be a real socket. A mocked failure proves nothing about the wire shape -- 05-04
recorded `httpx.ConnectError` (a mid-session `call_tool` failure), and the tuple widening built
on that reading alone still left the late peer with no verdict at all, because the CONNECT path
wraps. `test_secret_channel.py` established the same discipline for the 403: drive the real
client over a real socket and assert what actually comes back.

Assertions ordered narrow-to-broad: first WHAT is raised (documenting fastmcp's wrapper as
measured, so a version bump that changes it fails here loudly rather than silently reopening the
crash), then that `call_with_retry` contains it as a verdict.
"""

from __future__ import annotations

import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from pursuit.network.deadline import call_with_retry
from pursuit.network.deadline_errors import unwraps_to_retryable
from pursuit.network.secret_guard import client_headers
from pursuit.network.verdict import TechnicalWinReason
from tests.integration.test_secret_channel import _free_port

_TIMEOUT_SECONDS = 5.0
_RETRIES = 2
_NO_BACKOFF = 0.0


def _client_at(port: int) -> Client:
    """The exact construction `PeerRuntime.client()` performs."""
    transport = StreamableHttpTransport(f"http://127.0.0.1:{port}/mcp", headers=client_headers(None))
    return Client(transport, timeout=_TIMEOUT_SECONDS)


async def _push_to_a_dead_port(port: int) -> object:
    async with _client_at(port) as client:
        return await client.call_tool("receive_final_reveal", {"turn": 1, "sender": "police"})


async def test_a_closed_peer_port_raises_fastmcps_wrapper_not_the_raw_httpx_error():
    """MEASURED, not assumed. fastmcp 3.4.5 re-raises a connect-path fault as
    `RuntimeError(f"Client failed to connect: {exc}") from exc` (client/client.py:616-624),
    preserving only `httpx.HTTPStatusError` and `McpError` unwrapped. Every outgoing envelope in
    this codebase opens a fresh `async with ctx.runtime.client()`, so this -- not the raw
    `httpx.ConnectError` -- is the shape the ladder normally has to contain."""
    port = _free_port()

    with pytest.raises(RuntimeError) as caught:
        await _push_to_a_dead_port(port)

    assert not isinstance(caught.value, httpx.HTTPError), "the raw httpx error escaped unwrapped"
    assert isinstance(caught.value.__cause__, httpx.ConnectError)
    assert unwraps_to_retryable(caught.value) is True


async def test_the_ladder_turns_a_closed_peer_port_into_a_verdict_over_a_real_socket():
    """THE CONTAINMENT, end to end over loopback. Before 05-09 this call raised straight through
    `call_with_retry`, out of `run_agent`, and killed the process -- leaving US as the side that
    published no nonces (rule 36) with no verdict in our own log. It now returns measured
    evidence the caller can record, and the accusation is correct here because the peer really
    was unreachable for the whole ladder."""
    port = _free_port()

    outcome = await call_with_retry(
        lambda: _push_to_a_dead_port(port),
        timeout=_TIMEOUT_SECONDS, retries=_RETRIES, backoff=_NO_BACKOFF,
    )

    assert outcome.succeeded is False
    assert outcome.attempts == _RETRIES + 1
    assert outcome.verdict.reason is TechnicalWinReason.OPPONENT_UNRESPONSIVE
    assert "ConnectError" in outcome.verdict.last_error
    assert outcome.verdict.elapsed_seconds >= 0.0
