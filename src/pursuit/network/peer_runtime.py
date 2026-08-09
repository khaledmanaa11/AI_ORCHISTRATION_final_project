"""Factory-built FastMCP server + fastmcp.Client in one process (NET-03).

Each agent constructs exactly one `PeerRuntime` per process (NET-02): its own
`FastMCP` server, its own `asyncio.Queue`, zero module-level state. Two rules
verified against the pinned FastMCP 3.4.5 source (RESEARCH.md) govern this
module:

- Pitfall 1: `host`/`port` are supplied to `run_async()`, never to the
  `FastMCP(...)` constructor — both are in `_REMOVED_KWARGS` and raise
  `TypeError` at construction time in 3.4.5.
- Pitfall 3: the server's blocking synchronous entry point (it wraps
  `anyio.run()`) is never called; the server backgrounds as
  `asyncio.create_task(run_async(...))` alongside the orchestrator
  coroutine on the same event loop.

RESEARCH Open Question 2 (measured in 02-06 Task 3): `task.cancel()` alone
does not release the listening port. FastMCP 3.4.5's `run_http_async`
constructs its `uvicorn.Server` in a local variable and never returns or
stores it, so there is no public handle to request a graceful
`should_exit` shutdown from outside; cancellation skips uvicorn's own
`Server.shutdown()` (which is what actually closes the listener) entirely,
since that only runs after a normal `main_loop()` return. The fix binds the
listening socket here, ourselves, via the documented `sockets=` parameter
of `run_async`/`run_http_async` ("pre-bound sockets to pass to Uvicorn"),
so `stop()` can close the real OS socket directly without needing
cooperation from uvicorn's internals.

D-56 (CLOUD-01, Phase 5 plan 02): `shared_secret`, when supplied, wires
`SharedSecretMiddleware` into the SAME `run_async` call that already passes
`sockets=` -- the ASGI boundary, before any MCP session/tool machinery runs
-- and adds the matching header to every outgoing `client()` call. `None`
(the default, and every existing caller/test) installs no middleware and
sends no secret header: loopback dev and CI never notice the feature
exists.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
from collections.abc import Awaitable, Callable

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

from pursuit.network.secret_guard import build_middleware, client_headers
from pursuit.network.tools import HandshakeHandler, register_tools
from pursuit.shared.network_config import NetworkParams

ServeCallable = Callable[[], Awaitable[None]]


def build_server(
    queue: asyncio.Queue,
    server_name: str,
    *,
    handshake_handler: HandshakeHandler | None = None,
) -> FastMCP:
    """Construct this agent's server and attach the D-05 tool surface.

    Takes no host and no port: FastMCP 3.4.5 rejects both in the
    constructor (Pitfall 1). They are supplied to `run_async()` at call
    time by `PeerRuntime._run_http`.

    `handshake_handler` is forwarded untouched to `register_tools`; `None`
    keeps the generic D-05 stub ack. 02-09 passes 02-08's
    `respond_to_handshake` through here.
    """
    mcp = FastMCP(server_name)
    register_tools(mcp, queue, handshake_handler=handshake_handler)
    return mcp


class PeerRuntime:
    """One agent's server + client + queue, on one event loop (NET-02, NET-03)."""

    def __init__(
        self,
        params: NetworkParams,
        server_name: str,
        *,
        serve: ServeCallable | None = None,
        handshake_handler: HandshakeHandler | None = None,
        shared_secret: tuple[str, str] | None = None,
    ) -> None:
        self._params = params
        self._queue: asyncio.Queue = asyncio.Queue()
        self._mcp = build_server(
            self._queue, server_name, handshake_handler=handshake_handler
        )
        self._serve: ServeCallable = serve or self._run_http
        self._server_task: asyncio.Task | None = None
        self._listen_socket: socket.socket | None = None
        # D-56: (header_name, secret_value) or None -- the tunnel-off default
        # every existing caller/test uses unchanged.
        self._shared_secret = shared_secret

    @property
    def server(self) -> FastMCP:
        """The factory-built server (for in-memory `Client(runtime.server)`)."""
        return self._mcp

    @property
    def queue(self) -> asyncio.Queue:
        """The per-process inbound queue, consumed by 02-07/02-09."""
        return self._queue

    @property
    def params(self) -> NetworkParams:
        """Read-only accessor for the configuration this runtime was built from."""
        return self._params

    async def _run_http(self) -> None:
        """Serve over streamable HTTP (D-03). Host/port at CALL time (Pitfall 1).

        Binds the listening socket ourselves and hands it to `run_async`
        via `sockets=` so `stop()` can close the real OS socket directly
        (RESEARCH Open Question 2 — see module docstring).

        D-57: `host_origin_protection` is left at its fastmcp default (off)
        deliberately -- every peer here binds loopback, so `"auto"` mode
        would 421-reject every real request arriving through the tunnel
        with the ngrok hostname as its `Host:` header, before
        `SharedSecretMiddleware` even runs (RESEARCH Pitfall 2). If a later
        phase turns it on, `allowed_hosts` MUST carry both peers' ngrok
        hostnames from config, never a literal.
        """
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listen_socket.bind((self._params.host, self._params.port))
        self._listen_socket.listen()
        await self._mcp.run_async(
            transport="http",
            host=self._params.host,
            port=self._params.port,
            sockets=[self._listen_socket],
            middleware=build_middleware(self._shared_secret),
        )

    def client(self) -> Client:
        """A fresh client aimed at the opponent (NET-03).

        The caller owns the async-context-manager lifetime; the runtime
        never holds an open client of its own.

        D-56 / Pitfall 1: a bare `Client(url_string)` infers a transport
        with NO headers at all (fastmcp 3.4.5's own `inference.py`) -- so
        the transport is ALWAYS constructed explicitly here, never by
        handing a plain string to `Client(...)`, or the shared secret and
        the ngrok bypass header would silently stop being sent.
        """
        headers = client_headers(self._shared_secret)
        transport = StreamableHttpTransport(self._params.opponent_url, headers=headers)
        return Client(transport, timeout=self._params.response_timeout)

    async def start(self) -> None:
        """Background the server on THIS event loop (Pitfall 3 — never the blocking run())."""
        if self._server_task is None:
            self._server_task = asyncio.create_task(self._serve())

    async def stop(self) -> None:
        """Cancel the background server task and release the port. Idempotent."""
        task, self._server_task = self._server_task, None
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        listen_socket, self._listen_socket = self._listen_socket, None
        if listen_socket is not None:
            listen_socket.close()
