"""Tests for SharedSecretMiddleware (D-56, Task 1) -- the lock, driven with
no server at all: `httpx.ASGITransport` wraps the middleware directly around
a trivial inner app, and non-http scopes are called with a raw fake
receive/send pair (no HTTP machinery involved at all).
"""

from __future__ import annotations

import httpx
import pytest
from starlette.responses import PlainTextResponse

from pursuit.network.secret_guard import SharedSecretMiddleware

_HEADER = "X-Pursuit-Secret"
_SECRET = "correct-horse-battery-staple"


async def _inner_app(scope, receive, send) -> None:
    response = PlainTextResponse("ok")
    await response(scope, receive, send)


def _client() -> httpx.AsyncClient:
    app = SharedSecretMiddleware(_inner_app, header_name=_HEADER, expected=_SECRET)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


async def test_missing_header_is_rejected_with_403():
    async with _client() as client:
        response = await client.get("/mcp")
    assert response.status_code == 403


async def test_wrong_value_is_rejected_with_403():
    async with _client() as client:
        response = await client.get("/mcp", headers={_HEADER: "not-it"})
    assert response.status_code == 403


async def test_correct_value_reaches_the_inner_app():
    async with _client() as client:
        response = await client.get("/mcp", headers={_HEADER: _SECRET})
    assert response.status_code == 200
    assert response.text == "ok"


async def test_rejection_is_logged_at_warning_without_the_secret_value(caplog):
    with caplog.at_level("WARNING"):
        async with _client() as client:
            await client.get("/mcp")
    assert any(record.levelname == "WARNING" for record in caplog.records)
    assert _SECRET not in caplog.text


async def test_wrong_value_rejection_is_also_logged_without_the_secret_value(caplog):
    with caplog.at_level("WARNING"):
        async with _client() as client:
            await client.get("/mcp", headers={_HEADER: "not-it"})
    assert any(record.levelname == "WARNING" for record in caplog.records)
    assert _SECRET not in caplog.text


@pytest.mark.parametrize("scope_type", ["lifespan", "websocket"])
async def test_non_http_scopes_pass_through_untouched(scope_type):
    seen = {}

    async def _record_inner(scope, receive, send) -> None:
        seen["type"] = scope["type"]

    async def _noop_receive():
        return {"type": f"{scope_type}.startup"}

    async def _noop_send(message) -> None:
        return None

    middleware = SharedSecretMiddleware(_record_inner, header_name=_HEADER, expected=_SECRET)
    await middleware({"type": scope_type}, _noop_receive, _noop_send)
    assert seen["type"] == scope_type
