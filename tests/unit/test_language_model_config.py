"""Tests for language_model_config.py's validate_model_group() (D-32, D-52).

Added beyond 04-06-PLAN.md's own files_modified list per CLAUDE.md's "every
module gets a test file" rule -- language_model_config.py itself was split
out of language_config.py at the line-limit gate, so it gets its own test
file (04-03's own SUMMARY set this exact precedent for test_language_config.py).
"""

import pytest

from pursuit.shared.language_model_config import ModelKey, validate_model_group

_SOURCE = "language.json"


def _valid_model(**overrides: object) -> dict:
    model = {
        "provider": "claude_api",
        "model_id": "claude-haiku-4-5",
        "max_tokens": 300,
        "timeout_seconds": 30,
        "every_n_steps": 1,
        "game_arena": "New York",
        "hint_word_limit": 15,
    }
    model.update(overrides)
    return model


def test_valid_model_group_raises_nothing() -> None:
    validate_model_group(_valid_model(), source=_SOURCE)


def test_template_provider_is_also_a_valid_registry_key() -> None:
    validate_model_group(_valid_model(provider="template"), source=_SOURCE)


def test_unregistered_provider_name_raises_naming_the_key() -> None:
    with pytest.raises(ValueError, match="provider"):
        validate_model_group(_valid_model(provider="ollama"), source=_SOURCE)


def test_empty_model_id_raises_naming_the_key() -> None:
    with pytest.raises(ValueError, match=ModelKey.MODEL_ID.value):
        validate_model_group(_valid_model(model_id=""), source=_SOURCE)


def test_every_n_steps_zero_is_rejected() -> None:
    with pytest.raises(ValueError, match=ModelKey.EVERY_N_STEPS.value):
        validate_model_group(_valid_model(every_n_steps=0), source=_SOURCE)


def test_every_n_steps_negative_is_rejected() -> None:
    with pytest.raises(ValueError, match=ModelKey.EVERY_N_STEPS.value):
        validate_model_group(_valid_model(every_n_steps=-1), source=_SOURCE)


def test_every_n_steps_above_one_is_a_valid_warmup_knob() -> None:
    validate_model_group(_valid_model(every_n_steps=5), source=_SOURCE)


def test_max_tokens_zero_is_rejected() -> None:
    with pytest.raises(ValueError, match=ModelKey.MAX_TOKENS.value):
        validate_model_group(_valid_model(max_tokens=0), source=_SOURCE)


def test_timeout_seconds_zero_is_rejected() -> None:
    with pytest.raises(ValueError, match=ModelKey.TIMEOUT_SECONDS.value):
        validate_model_group(_valid_model(timeout_seconds=0), source=_SOURCE)


def test_empty_game_arena_is_valid_and_means_generic_cues() -> None:
    validate_model_group(_valid_model(game_arena=""), source=_SOURCE)


def test_hint_word_limit_zero_is_rejected() -> None:
    """04-10, Table 14 row 2: the limit is our own, but it must be positive."""
    with pytest.raises(ValueError, match=ModelKey.HINT_WORD_LIMIT.value):
        validate_model_group(_valid_model(hint_word_limit=0), source=_SOURCE)


def test_hint_word_limit_negative_is_rejected() -> None:
    with pytest.raises(ValueError, match=ModelKey.HINT_WORD_LIMIT.value):
        validate_model_group(_valid_model(hint_word_limit=-1), source=_SOURCE)


def test_hint_word_limit_missing_raises_key_error() -> None:
    model = _valid_model()
    del model["hint_word_limit"]
    with pytest.raises(KeyError):
        validate_model_group(model, source=_SOURCE)


def test_hint_word_limit_may_be_negotiated_above_the_default() -> None:
    """Negotiable (Table 14 row 2), unlike the Table 19 minima -- no ceiling here."""
    validate_model_group(_valid_model(hint_word_limit=25), source=_SOURCE)


def test_missing_provider_key_raises_key_error() -> None:
    model = _valid_model()
    del model["provider"]
    with pytest.raises(KeyError):
        validate_model_group(model, source=_SOURCE)


def test_wrong_type_model_id_raises_type_error() -> None:
    with pytest.raises(TypeError):
        validate_model_group(_valid_model(model_id=123), source=_SOURCE)


def test_model_key_enum_has_no_numeric_literal() -> None:
    """D-05 discipline: every ModelKey value is a field name, not a number."""
    for key in ModelKey:
        assert isinstance(key.value, str)
        assert not key.value.isdigit()
