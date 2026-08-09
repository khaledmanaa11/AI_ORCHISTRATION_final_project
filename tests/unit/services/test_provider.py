"""Tests for provider.py's Protocol/registry and TemplateProvider (D-33, D-52).

Covers Task 1's own verify criteria: the template provider satisfies the
protocol with zero usage, an unknown provider name raises at "load" (i.e.
at get_provider_class(), independent of any config file), and LlmFailure is
never raised anywhere in the package (a repo-grep, encoded here too so a
regression fails CI, not just a manual check).
"""

import random
import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.services.llm.provider import (
    LlmFailure,
    LlmFailureReason,
    LlmResult,
    Provider,
    get_provider_class,
)
from pursuit.services.llm.template_provider import TemplateProvider

_LLM_PACKAGE_ROOT = Path(__file__).parent.parent.parent.parent / "src" / "pursuit" / "services" / "llm"


def test_template_provider_satisfies_the_protocol() -> None:
    assert isinstance(TemplateProvider(phrases=["hi"]), Provider)


async def test_template_provider_returns_zero_usage_and_no_parsed() -> None:
    provider = TemplateProvider(phrases=["scent is strong east"], rng=random.Random(1))
    result = await provider.complete(system_prompt="s", user_prompt="u")
    assert isinstance(result, LlmResult)
    assert result.text == "scent is strong east"
    assert result.parsed is None
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.model is None


async def test_template_provider_selects_via_the_injected_rng() -> None:
    phrases = ["north", "south", "east", "west"]
    provider = TemplateProvider(phrases=phrases, rng=random.Random(42))
    expected = random.Random(42).choice(phrases)
    result = await provider.complete(system_prompt="s", user_prompt="u")
    assert result.text == expected


def test_empty_phrases_raises() -> None:
    with pytest.raises(ValueError, match="at least one phrase"):
        TemplateProvider(phrases=[])


def test_template_is_registered() -> None:
    assert get_provider_class("template") is TemplateProvider


def test_unknown_provider_name_raises_at_load() -> None:
    with pytest.raises(ValueError, match="bogus"):
        get_provider_class("bogus")


def test_unknown_provider_error_names_every_known_provider() -> None:
    with pytest.raises(ValueError, match="template"):
        get_provider_class("bogus")


def test_llm_failure_is_never_raised_in_the_package() -> None:
    """grep -rn "raise LlmFailure" src/pursuit/services/llm -- must be empty (D-33)."""
    pattern = re.compile(r"raise LlmFailure")
    offenders = [
        str(path)
        for path in _LLM_PACKAGE_ROOT.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_llm_failure_reason_covers_the_must_haves_list() -> None:
    required = {
        "no_key",
        "auth",
        "rate_limited",
        "timeout",
        "connection",
        "bad_request",
        "schema_invalid",
        "overflow",
        "budget_exhausted",
        "disabled",
    }
    assert required.issubset({reason.value for reason in LlmFailureReason})


def test_llm_failure_is_frozen() -> None:
    failure = LlmFailure(reason=LlmFailureReason.NO_KEY, message="no key")
    with pytest.raises(FrozenInstanceError):
        failure.message = "changed"  # type: ignore[misc]
