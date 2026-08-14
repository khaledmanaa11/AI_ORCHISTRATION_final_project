"""Haiku 4.5 provider: claude_api behind the single Gatekeeper door (D-32, D-34).

AnthropicProvider.complete() builds one messages.create request, hands it to
Gatekeeper.submit() as a zero-argument callable, and maps every SDK error
class (plus GatekeeperOverflow) onto an LlmFailure -- never raises (D-33).
The client itself is built lazily by client.py's build_client() and cached
on self, so a missing ANTHROPIC_API_KEY never constructs an SDK client at
all: NO_KEY returns immediately, before Gatekeeper.submit() is ever called,
so a call known to fail never consumes a queue slot.

Token estimation is a local, zero-network heuristic (_estimate_tokens), not
a live count_tokens() call -- this plan's own must_haves is explicit that
"the provider never calls the API directly", with no carve-out, and a live
count_tokens() call would itself be a second, ungated request, doubling
traffic against Table 19's tight requests_per_minute floor for every single
hint. TokenBudget.settle() (budget.py) reconciles the estimate against real
response.usage after every call regardless (D-35), so the estimate's only
job is sizing the degrade-level bookkeeping before the call runs, never
billing accuracy.
"""

import json

import anthropic

from pursuit.services.llm.client import API_KEY_ENV_VAR, build_client
from pursuit.services.llm.gatekeeper import CallResult, Gatekeeper, GatekeeperOverflow
from pursuit.services.llm.provider import (
    LlmFailure,
    LlmFailureReason,
    LlmResult,
    register_provider,
)

_CHARS_PER_TOKEN_ESTIMATE = 4  # a common rough ratio; reconciled by TokenBudget.settle()

# Most-specific subclass first: APITimeoutError IS-A APIConnectionError, and
# the first matching entry wins in _map_exception's linear scan.
_EXCEPTION_REASONS: tuple[tuple[type[Exception], LlmFailureReason], ...] = (
    (GatekeeperOverflow, LlmFailureReason.OVERFLOW),
    (anthropic.APITimeoutError, LlmFailureReason.TIMEOUT),
    (anthropic.APIConnectionError, LlmFailureReason.CONNECTION),
    (anthropic.AuthenticationError, LlmFailureReason.AUTH),
    (anthropic.RateLimitError, LlmFailureReason.RATE_LIMITED),
    (anthropic.APIStatusError, LlmFailureReason.BAD_REQUEST),
)


def _map_exception(exc: Exception) -> LlmFailureReason:
    """The reason for the first matching entry in _EXCEPTION_REASONS, or
    UNKNOWN when no provider or gatekeeper class claims it (D-33's floor)."""
    for exc_type, reason in _EXCEPTION_REASONS:
        if isinstance(exc, exc_type):
            return reason
    return LlmFailureReason.UNKNOWN


def _estimate_tokens(system_prompt: str, user_prompt: str, *, max_tokens: int) -> int:
    """input chars / 4 (a common rough ratio) plus the full output ceiling --
    conservative, cheap, zero-network; reconciled against real usage after
    every call by TokenBudget.settle()."""
    input_chars = len(system_prompt) + len(user_prompt)
    return (input_chars // _CHARS_PER_TOKEN_ESTIMATE) + max_tokens


class AnthropicProvider:
    """claude_api: Haiku 4.5 through the one gatekeeper door (D-32, D-34, LANG-06).

    served_model stays None until the first response the SDK itself returns
    successfully -- a wrong model_id 404s (mapped to BAD_REQUEST here) and
    served_model never gets set, which is exactly the signal a live run
    must check (a wrong model id is otherwise invisible: D-33 quietly
    degrades it to a template hint and the game finishes looking healthy).
    """

    def __init__(
        self,
        *,
        gatekeeper: Gatekeeper,
        model_id: str,
        max_tokens: int,
        timeout_seconds: int,
    ) -> None:
        self._gatekeeper = gatekeeper
        self._model_id = model_id
        self._max_tokens = max_tokens
        self._timeout_seconds = timeout_seconds
        self._client: anthropic.AsyncAnthropic | None = None
        self.served_model: str | None = None

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> LlmResult | LlmFailure:
        if self._client is None:
            self._client = build_client(timeout_seconds=self._timeout_seconds)
            if self._client is None:
                return LlmFailure(LlmFailureReason.NO_KEY, f"{API_KEY_ENV_VAR} is not set")
        client = self._client

        request: dict = {
            "model": self._model_id,
            "max_tokens": self._max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if schema is not None:
            request["output_config"] = {"format": {"type": "json_schema", "schema": schema}}

        async def _call() -> CallResult:
            response = await client.messages.create(**request)
            return CallResult(
                value=response,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        estimate = _estimate_tokens(system_prompt, user_prompt, max_tokens=self._max_tokens)
        try:
            response = await self._gatekeeper.submit(_call, estimated_tokens=estimate)
        except Exception as exc:  # every provider/gatekeeper failure degrades (D-33)
            return LlmFailure(_map_exception(exc), f"{type(exc).__name__}: {exc}")

        if self.served_model is None:
            self.served_model = response.model

        text = response.content[0].text
        parsed = None
        if schema is not None:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                return LlmFailure(LlmFailureReason.SCHEMA_INVALID, f"invalid JSON: {exc}")

        return LlmResult(
            text=text,
            parsed=parsed,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
        )


register_provider("claude_api", AnthropicProvider)
