"""The one interface every LLM provider satisfies, and the one failure type
every provider returns instead of raising (D-33, D-52, LANG-06).

Provider is structural (Protocol) -- template_provider.py's TemplateProvider
and anthropic_provider.py's AnthropicProvider both satisfy it with no shared
base class, and neither imports the other. Both import Provider/LlmResult/
LlmFailure from here and call register_provider() on themselves at the
bottom of their own file, so PROVIDER_REGISTRY fills in as a side effect of
import rather than this module importing its own implementations (which
would cycle: this module gets imported by both of them). Import
pursuit.services.llm (the package __init__) to guarantee every provider has
registered before calling get_provider_class() -- that package assembles
all of them for exactly this reason.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class LlmFailureReason(str, Enum):
    """D-33's exhaustive vocabulary for why a call did not produce a result.

    UNKNOWN is the floor for an SDK error class no provider maps
    explicitly -- anthropic_provider.py's final ``except Exception`` arm
    still degrades to a value here, never lets an unmapped class escape.
    """

    NO_KEY = "no_key"
    AUTH = "auth"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    BAD_REQUEST = "bad_request"
    SCHEMA_INVALID = "schema_invalid"
    OVERFLOW = "overflow"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LlmFailure:
    """A provider's non-exceptional failure -- returned, never raised (D-33)."""

    reason: LlmFailureReason
    message: str


@dataclass(frozen=True)
class LlmResult:
    """A provider's successful completion.

    parsed is set only when the caller supplied a JSON schema, else None.
    model is the actually-served model name when the provider has one to
    report (None for TemplateProvider, which never touches a network).
    """

    text: str
    parsed: dict | None
    input_tokens: int
    output_tokens: int
    model: str | None = None


@runtime_checkable
class Provider(Protocol):
    """Given a system prompt, a user prompt and an optional JSON schema,
    return LlmResult or LlmFailure -- never raise (D-33, LANG-06)."""

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> LlmResult | LlmFailure: ...


_REGISTRY: dict[str, type[Provider]] = {}


def register_provider(name: str, cls: type[Provider]) -> type[Provider]:
    """Register cls under the config string name.

    Returns cls unchanged, so a leaf provider module can call this as a
    plain top-level statement at the bottom of its own file.
    """
    _REGISTRY[name] = cls
    return cls


def get_provider_class(name: str) -> type[Provider]:
    """The registered class for name.

    Raises
    ------
    ValueError
        If name is not registered -- names the bad value and every known
        name, so a bad config fails at load, never as a runtime surprise
        (D-52: only "template" and "claude_api" are ever registered here;
        "ollama"/"claude_cli" are documented extension points, not code).
    """
    if name not in _REGISTRY:
        known = sorted(_REGISTRY)
        raise ValueError(f"Unknown LLM provider {name!r}; known providers: {known}")
    return _REGISTRY[name]
