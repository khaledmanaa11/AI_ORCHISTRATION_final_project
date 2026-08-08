"""Error-class-to-LlmFailureReason mapping tests for AnthropicProvider.

Split from test_anthropic_provider.py at the 150-code-line gate (Segal
Table 5) -- shared fakes are defined there and imported here (QUAL-02),
mirroring the test_gatekeeper.py / test_gatekeeper_retry.py precedent.
"""

import anthropic
import httpx
import pytest

from pursuit.services.llm.gatekeeper import GatekeeperOverflow
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason
from tests.unit.services.test_anthropic_provider import (
    FakeClient,
    FakeMessage,
    make_provider,
    patch_client,
)

_REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _status_error(cls: type, status_code: int, message: str = "error") -> Exception:
    response = httpx.Response(status_code, request=_REQUEST)
    return cls(message, response=response, body=None)


class OverflowingGatekeeper:
    async def submit(self, fn, *, estimated_tokens: int):
        raise GatekeeperOverflow("queue depth 1 exceeded (Table 19 row 5)")


@pytest.mark.parametrize(
    ("build_error", "expected_reason"),
    [
        (lambda: _status_error(anthropic.AuthenticationError, 401), LlmFailureReason.AUTH),
        (lambda: _status_error(anthropic.RateLimitError, 429), LlmFailureReason.RATE_LIMITED),
        (lambda: _status_error(anthropic.BadRequestError, 400), LlmFailureReason.BAD_REQUEST),
        (lambda: _status_error(anthropic.NotFoundError, 404), LlmFailureReason.BAD_REQUEST),
        (lambda: anthropic.APITimeoutError(request=_REQUEST), LlmFailureReason.TIMEOUT),
        (lambda: anthropic.APIConnectionError(request=_REQUEST), LlmFailureReason.CONNECTION),
        (lambda: RuntimeError("boom"), LlmFailureReason.UNKNOWN),
    ],
)
async def test_every_error_class_maps_to_its_reason(monkeypatch, build_error, expected_reason) -> None:
    client = FakeClient(error=build_error())
    patch_client(monkeypatch, client)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u")

    assert isinstance(result, LlmFailure)
    assert result.reason == expected_reason
    assert provider.served_model is None


async def test_gatekeeper_overflow_maps_to_overflow_without_calling_the_sdk(monkeypatch) -> None:
    client = FakeClient(FakeMessage("unused", model="claude-haiku-4-5-20251001"))
    patch_client(monkeypatch, client)
    provider = make_provider(OverflowingGatekeeper())

    result = await provider.complete(system_prompt="s", user_prompt="u")

    assert result.reason == LlmFailureReason.OVERFLOW
    assert client.messages.create_calls == 0


async def test_failure_message_names_the_exception_class(monkeypatch) -> None:
    client = FakeClient(error=_status_error(anthropic.AuthenticationError, 401, "invalid x-api-key"))
    patch_client(monkeypatch, client)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u")

    assert "AuthenticationError" in result.message
