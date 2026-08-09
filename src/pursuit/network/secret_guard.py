"""D-56 -- SharedSecretMiddleware: the lock on the public door.

A pure ASGI callable enforcing the tunnel's shared-secret header BEFORE any
FastMCP session/tool machinery ever sees the request. This is the ASGI
BOUNDARY seam the RESEARCH doc names -- attached via
`middleware=[Middleware(SharedSecretMiddleware, ...)]` in the SAME
`run_async` call that already passes `sockets=` (peer_runtime.py, Task 2) --
never a check inside an individual `@mcp.tool` handler in `tools.py`
(RESEARCH Anti-Patterns: five copies would drift out of sync, and a
malformed non-tool request would still reach the server before any of them
ran).

The comparison uses `secrets.compare_digest`, the same discipline
`config_hash.digests_match` already established as this project's one
digest-comparison idiom (CLAUDE.md) -- a timing oracle on the interim
shared secret would be a silly gift ahead of Phase 6's real commit-reveal
values.

The rejection log records the remote peer address and the missing/mismatched
FACT only -- never the header name's expected value (must_haves, rule 4:
"never commit secrets" extends to logs).

`build_middleware`/`client_headers` below are the two small factories
`peer_runtime.py` calls at its `run_async(middleware=...)` and `client()`
seams -- kept here (not duplicated in peer_runtime.py) so this module stays
the SINGLE owner of the shared-secret shape on both sides of the channel;
peer_runtime.py sat at its own 150-code-line ceiling once both the server
and client wiring were added in place.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

logger = logging.getLogger(__name__)

_FORBIDDEN_BODY = "Forbidden"
_MISSING = "missing"
_MISMATCHED = "mismatched"

# Pitfall 4 (RESEARCH): ngrok's free-tier browser interstitial only ever
# triggers on `Accept: text/html`, which MCP's client never sends -- this
# header is a zero-cost defensive no-op off ngrok and rides on every
# outgoing call regardless of whether a shared secret is configured.
NGROK_SKIP_WARNING_HEADER = "ngrok-skip-browser-warning"
NGROK_SKIP_WARNING_VALUE = "true"


class SharedSecretMiddleware:
    """Pure ASGI callable. Non-`http` scopes (lifespan, websocket) pass
    through untouched. An `http` scope missing `header_name`, or carrying a
    value that fails `secrets.compare_digest` against `expected`, gets a
    plain 403 and never reaches the wrapped app -- no session, no tool
    dispatch, no partial MCP state."""

    def __init__(self, app: Any, *, header_name: str, expected: str) -> None:
        self._app = app
        self._header_name = header_name
        self._expected = expected

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request = Request(scope=scope)
        supplied = request.headers.get(self._header_name)
        if supplied is not None and secrets.compare_digest(supplied, self._expected):
            await self._app(scope, receive, send)
            return

        reason = _MISSING if supplied is None else _MISMATCHED
        logger.warning(
            "SharedSecretMiddleware rejected a %s header from %s (%s %s)",
            reason, request.client, request.method, request.url.path,
        )
        response = PlainTextResponse(_FORBIDDEN_BODY, status_code=403)
        await response(scope, receive, send)


def build_middleware(shared_secret: tuple[str, str] | None) -> list[Middleware] | None:
    """The ASGI middleware list for `run_async(middleware=...)`, or `None`
    when no secret is configured -- the tunnel-off default every existing
    caller/test uses unchanged."""
    if shared_secret is None:
        return None
    header_name, secret_value = shared_secret
    return [
        Middleware(SharedSecretMiddleware, header_name=header_name, expected=secret_value)
    ]


def client_headers(shared_secret: tuple[str, str] | None) -> dict[str, str]:
    """The headers dict for `PeerRuntime.client()`'s explicit
    `StreamableHttpTransport`: the ngrok bypass header always, the
    shared-secret header only when `shared_secret` is configured."""
    headers = {NGROK_SKIP_WARNING_HEADER: NGROK_SKIP_WARNING_VALUE}
    if shared_secret is not None:
        header_name, secret_value = shared_secret
        headers[header_name] = secret_value
    return headers
