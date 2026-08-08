"""Tests for AnthropicProvider/build_client -- claude_api behind the one
gatekeeper door (D-32, D-33, D-34). The SDK is fully mocked: no test here
performs network I/O (CLAUDE.md).

Error-class-to-reason mappings live in test_anthropic_provider_errors.py,
split at the 150-code-line gate (Segal Table 5); shared fakes are defined
here and imported there (QUAL-02), mirroring the test_gatekeeper.py /
test_gatekeeper_retry.py precedent.
"""

import anthropic
import pytest

from pursuit.services.llm.anthropic_provider import AnthropicProvider
from pursuit.services.llm.client import build_client
from pursuit.services.llm.gatekeeper import Gatekeeper
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason, LlmResult
from tests.unit.services.test_bucket import FakeClock
from tests.unit.services.test_gatekeeper import FakeSleep, _params


class FakeBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class FakeMessage:
    def __init__(
        self, text: str, *, model: str, input_tokens: int = 5, output_tokens: int = 5
    ) -> None:
        self.content = [FakeBlock(text)]
        self.usage = FakeUsage(input_tokens, output_tokens)
        self.model = model


class FakeMessages:
    def __init__(self, message: FakeMessage | None = None, *, error: Exception | None = None) -> None:
        self._message = message
        self._error = error
        self.create_calls = 0

    async def create(self, **kwargs: object) -> FakeMessage:
        self.create_calls += 1
        if self._error is not None:
            raise self._error
        assert self._message is not None
        return self._message


class FakeClient:
    def __init__(self, message: FakeMessage | None = None, *, error: Exception | None = None) -> None:
        self.messages = FakeMessages(message, error=error)


class SpyGatekeeper:
    """Records every estimated_tokens it was asked to submit; runs fn itself."""

    def __init__(self) -> None:
        self.submit_calls: list[int] = []

    async def submit(self, fn, *, estimated_tokens: int):
        self.submit_calls.append(estimated_tokens)
        result = await fn()
        return result.value


def real_gatekeeper() -> Gatekeeper:
    return Gatekeeper(params=_params(), clock=FakeClock(), sleep=FakeSleep())


def make_provider(gatekeeper=None) -> AnthropicProvider:
    return AnthropicProvider(
        gatekeeper=gatekeeper if gatekeeper is not None else real_gatekeeper(),
        model_id="claude-haiku-4-5",
        max_tokens=300,
        timeout_seconds=30,
    )


def patch_client(monkeypatch: pytest.MonkeyPatch, client: FakeClient) -> None:
    monkeypatch.setattr("pursuit.services.llm.anthropic_provider.build_client", lambda **_: client)


async def test_successful_call_returns_text_usage_and_served_model(monkeypatch) -> None:
    client = FakeClient(FakeMessage("scent is strong north", model="claude-haiku-4-5-20251001"))
    patch_client(monkeypatch, client)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u")

    assert isinstance(result, LlmResult)
    assert result.text == "scent is strong north"
    assert result.parsed is None
    assert result.model == "claude-haiku-4-5-20251001"
    assert provider.served_model == "claude-haiku-4-5-20251001"


async def test_budget_settles_from_real_usage_not_the_estimate(monkeypatch) -> None:
    client = FakeClient(
        FakeMessage("hi", model="claude-haiku-4-5-20251001", input_tokens=11, output_tokens=7)
    )
    patch_client(monkeypatch, client)
    gk = real_gatekeeper()
    provider = make_provider(gk)

    await provider.complete(system_prompt="s", user_prompt="u")

    report = gk.budget.report()
    assert report["input_tokens"] == 11
    assert report["output_tokens"] == 7


async def test_schema_supplied_returns_parsed_json(monkeypatch) -> None:
    client = FakeClient(FakeMessage('{"cell": [1, 2]}', model="claude-haiku-4-5-20251001"))
    patch_client(monkeypatch, client)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u", schema={"type": "object"})

    assert result.parsed == {"cell": [1, 2]}


async def test_schema_supplied_but_response_not_json_is_schema_invalid(monkeypatch) -> None:
    client = FakeClient(FakeMessage("not json", model="claude-haiku-4-5-20251001"))
    patch_client(monkeypatch, client)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u", schema={"type": "object"})

    assert isinstance(result, LlmFailure)
    assert result.reason == LlmFailureReason.SCHEMA_INVALID


async def test_no_schema_leaves_parsed_none(monkeypatch) -> None:
    client = FakeClient(FakeMessage("free text bluff", model="claude-haiku-4-5-20251001"))
    patch_client(monkeypatch, client)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u")

    assert result.parsed is None


async def test_unset_api_key_yields_no_key(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = make_provider()

    result = await provider.complete(system_prompt="s", user_prompt="u")

    assert result == LlmFailure(LlmFailureReason.NO_KEY, "ANTHROPIC_API_KEY is not set")


async def test_unset_api_key_never_touches_the_gatekeeper(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    spy = SpyGatekeeper()
    provider = make_provider(spy)

    await provider.complete(system_prompt="s", user_prompt="u")

    assert spy.submit_calls == []


async def test_sdk_is_called_only_through_gatekeeper_submit(monkeypatch) -> None:
    client = FakeClient(FakeMessage("hi", model="claude-haiku-4-5-20251001"))
    patch_client(monkeypatch, client)
    spy = SpyGatekeeper()
    provider = make_provider(spy)

    await provider.complete(system_prompt="s", user_prompt="u")

    assert len(spy.submit_calls) == 1
    assert client.messages.create_calls == 1


def test_build_client_returns_none_without_a_key(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert build_client(timeout_seconds=30) is None


def test_build_client_constructs_when_a_key_is_present(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-dummy-not-a-real-key")
    client = build_client(timeout_seconds=30)
    assert client is not None
    assert isinstance(client, anthropic.AsyncAnthropic)
    assert client.api_key == "test-dummy-not-a-real-key"
    assert client.max_retries == 0


def test_no_anthropic_key_literal_in_source_or_config() -> None:
    """grep -rn "sk-ant" src/ config/ -- must be empty (CLAUDE.md rules 39-40)."""
    from pathlib import Path

    root = Path(__file__).parent.parent.parent.parent
    offenders = [
        str(path)
        for directory in (root / "src", root / "config")
        for path in directory.rglob("*")
        if path.is_file() and "sk-ant" in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == []
