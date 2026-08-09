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
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

from starlette.requests import Request
from starlette.responses import PlainTextResponse

logger = logging.getLogger(__name__)

_FORBIDDEN_BODY = "Forbidden"
_MISSING = "missing"
_MISMATCHED = "mismatched"


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
