"""Tests for `network/language_wiring.py` -- the LLM half of a process's
language pipeline, built once (D-34, D-35, D-52)."""

import dataclasses
import logging

from pursuit.network.language_wiring import (
    _FALLBACK_LANGUAGE_SEED,
    _build_provider,
    _resolve_seed,
    build_language_runtime,
)
from pursuit.services.llm.anthropic_provider import AnthropicProvider
from pursuit.services.llm.gatekeeper import Gatekeeper
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.shared.deception_config import load_deception_config
from pursuit.shared.language_config import load_language_config


def _language_params():
    return load_language_config("config/police/language.json")


def _deception_params():
    return load_deception_config("config/police/deception.json")


def test_resolve_seed_returns_a_given_seed_unchanged():
    assert _resolve_seed(42, label="t") == 42


def test_resolve_seed_derives_and_logs_a_fallback_when_null(caplog):
    with caplog.at_level(logging.WARNING):
        assert _resolve_seed(None, label="t") == _FALLBACK_LANGUAGE_SEED
    assert any("seed is null" in r.message for r in caplog.records)


def test_build_provider_returns_a_template_provider_for_the_template_name():
    language = _language_params()
    template_model = {**language.model, "provider": "template"}
    provider = _build_provider(template_model, Gatekeeper(params=language))
    assert isinstance(provider, TemplateProvider)


def test_build_provider_returns_an_anthropic_provider_for_claude_api():
    language = _language_params()
    provider = _build_provider(language.model, Gatekeeper(params=language))
    assert isinstance(provider, AnthropicProvider)


def test_build_language_runtime_wires_matching_word_limit_and_arena():
    language, deception = _language_params(), _deception_params()
    runtime = build_language_runtime(
        language=language, deception=deception, board_size=7, seed=123,
    )
    assert runtime.decode_context.word_limit == runtime.bluff_context.word_limit
    assert runtime.decode_context.arena == runtime.bluff_context.arena
    assert runtime.decode_context.provider is runtime.bluff_context.provider
    assert runtime.deception_config is deception


def test_build_language_runtime_derives_a_seed_when_none_is_given():
    language, deception = _language_params(), _deception_params()
    runtime = build_language_runtime(language=language, deception=deception, board_size=7, seed=None)
    assert isinstance(runtime.deception_rng.random(), float)


def test_language_runtime_is_a_plain_mutable_dataclass_so_degrade_level_refreshes():
    language, deception = _language_params(), _deception_params()
    runtime = build_language_runtime(language=language, deception=deception, board_size=7, seed=1)
    refreshed = dataclasses.replace(runtime.bluff_context, degrade_level="anything")
    assert refreshed.degrade_level == "anything"
