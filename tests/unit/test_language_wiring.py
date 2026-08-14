"""Tests for `network/language_wiring.py` -- the LLM half of a process's
language pipeline, built once (D-34, D-35, D-52)."""

import dataclasses
import logging

import pytest

from pursuit.network.language_wiring import (
    _FALLBACK_LANGUAGE_SEED,
    _build_provider,
    _resolve_seed,
    build_language_runtime,
)
from pursuit.services.llm.anthropic_provider import AnthropicProvider
from pursuit.services.llm.client import API_KEY_ENV_VAR
from pursuit.services.llm.gatekeeper import Gatekeeper
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.shared.deception_config import load_deception_config
from pursuit.shared.language_config import load_language_config

#: Fake, never a credential -- present so the assertions below can search
#: for it and prove no log record ever carries the VALUE (CLAUDE.md rule 4).
_SENTINEL_KEY = "not-a-real-key-05-07-sentinel"
_WIRING_LOGGER = "pursuit.network.language_wiring"


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


def _build(provider_name: str | None = None):
    language = _language_params()
    model = language.model if provider_name is None else {**language.model, "provider": provider_name}
    return _build_provider(model, Gatekeeper(params=language))


def _wiring_warnings(caplog):
    return [
        record for record in caplog.records
        if record.name == _WIRING_LOGGER and record.levelno >= logging.WARNING
    ]


def test_a_real_provider_with_no_key_warns_exactly_once_naming_the_env_var(monkeypatch, caplog):
    """UAT G5: the keyless run is legible now. The provider is still built,
    unchanged -- the warning is the only new behaviour."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    with caplog.at_level(logging.WARNING):
        provider = _build()
    warnings = _wiring_warnings(caplog)
    assert len(warnings) == 1
    assert API_KEY_ENV_VAR in warnings[0].getMessage()
    assert isinstance(provider, AnthropicProvider)


def test_a_real_provider_with_a_key_present_warns_about_nothing(monkeypatch, caplog):
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    with caplog.at_level(logging.DEBUG):
        provider = _build()
    assert _wiring_warnings(caplog) == []
    assert isinstance(provider, AnthropicProvider)


@pytest.mark.parametrize("key_present", [True, False])
def test_the_template_provider_never_warns_whatever_the_key_says(monkeypatch, caplog, key_present):
    """`template` makes no call by design, so a missing key tells the
    operator nothing -- the warning keys off the resolved CLASS, not the
    environment alone."""
    if key_present:
        monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    else:
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    with caplog.at_level(logging.WARNING):
        provider = _build("template")
    assert isinstance(provider, TemplateProvider)
    assert _wiring_warnings(caplog) == []


def test_the_keyless_warning_never_carries_a_key_shaped_value(monkeypatch, caplog):
    """Control for CLAUDE.md rule 4: the sentinel is in the environment for
    the first build and gone for the second, so ANY record that ever
    interpolated the value (rather than the NAME) would surface here."""
    monkeypatch.setenv(API_KEY_ENV_VAR, _SENTINEL_KEY)
    with caplog.at_level(logging.DEBUG):
        _build()
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
        _build()
    assert any(API_KEY_ENV_VAR in record.getMessage() for record in caplog.records)
    assert all(_SENTINEL_KEY not in record.getMessage() for record in caplog.records)


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
