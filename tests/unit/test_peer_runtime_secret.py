"""D-56 (05-02): PeerRuntime's `shared_secret` seam, split out of
test_peer_runtime.py at the 150-code-line gate (same reasoning as every
prior `test_*_<topic>.py` split in this repo, e.g. test_qtable_durability.py).

`client()`'s headers are checked with no socket at all (`.transport.headers`
is public, verified directly against the installed fastmcp source in
05-RESEARCH.md). `_run_http()`'s `middleware=` kwarg is checked by
monkeypatching the real FastMCP instance's `run_async` to a recording fake
-- only the listening socket (bound to port 0, closed at the end of each
such test) is real; no serve loop ever actually runs.
"""

import dataclasses

from pursuit.network.peer_runtime import PeerRuntime


async def test_client_headers_carry_secret_and_ngrok_bypass_when_configured(
    network_params,
):
    """The explicit transport carries both entries, no network call."""
    runtime = PeerRuntime(
        network_params, "pursuit-police", shared_secret=("X-Pursuit-Secret", "s3cr3t")
    )
    headers = runtime.client().transport.headers
    assert headers["X-Pursuit-Secret"] == "s3cr3t"
    assert headers["ngrok-skip-browser-warning"] == "true"


async def test_client_headers_carry_no_secret_when_unconfigured(network_params):
    """Default — every existing caller/test: no secret header sent, only
    the always-on ngrok bypass header."""
    runtime = PeerRuntime(network_params, "pursuit-police")
    headers = runtime.client().transport.headers
    assert "X-Pursuit-Secret" not in headers
    assert headers == {"ngrok-skip-browser-warning": "true"}


async def test_run_http_installs_middleware_when_secret_configured(network_params):
    """The SAME run_async call that passes sockets= also gets
    middleware=[...] when a secret is configured."""
    net = dataclasses.replace(network_params, host="127.0.0.1", port=0)
    runtime = PeerRuntime(net, "pursuit-test-secret", shared_secret=("X-Test", "s3cr3t"))
    captured = {}

    async def fake_run_async(**kwargs):
        captured.update(kwargs)

    runtime._mcp.run_async = fake_run_async
    try:
        await runtime._run_http()
    finally:
        runtime._listen_socket.close()

    assert captured["middleware"] is not None
    assert len(captured["middleware"]) == 1


async def test_run_http_installs_no_middleware_when_secret_absent(network_params):
    """Default — every existing test/dev flow: middleware=None."""
    net = dataclasses.replace(network_params, host="127.0.0.1", port=0)
    runtime = PeerRuntime(net, "pursuit-test-nosecret")
    captured = {}

    async def fake_run_async(**kwargs):
        captured.update(kwargs)

    runtime._mcp.run_async = fake_run_async
    try:
        await runtime._run_http()
    finally:
        runtime._listen_socket.close()

    assert captured["middleware"] is None
