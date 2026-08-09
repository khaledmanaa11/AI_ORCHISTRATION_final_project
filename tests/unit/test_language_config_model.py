"""Integration tests: load_language_config() wires in model-group validation
(04-06, D-32, D-52). Split from test_language_config.py at the
150-code-line gate (Segal Table 5) -- shared fixtures (_write_variant,
POLICE_LANGUAGE) are defined there and imported here (QUAL-02), mirroring
the test_gatekeeper.py / test_gatekeeper_retry.py precedent.

Field-by-field validation of validate_model_group() itself lives in
test_language_model_config.py; this file only proves the WIRING -- that
load_language_config() actually calls it, and that a missing API key is
never a load-time failure (D-33).
"""

from pathlib import Path

import pytest

from pursuit.shared.language_config import LanguageKey, load_language_config
from tests.unit.test_language_config import POLICE_LANGUAGE, _write_variant


def test_bad_provider_name_fails_at_load_naming_the_key(tmp_path: Path) -> None:
    bad = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_MODEL].__setitem__("provider", "ollama"),
    )
    with pytest.raises(ValueError, match="provider"):
        load_language_config(bad)


def test_every_n_steps_zero_is_rejected_through_load(tmp_path: Path) -> None:
    bad = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_MODEL].__setitem__("every_n_steps", 0),
    )
    with pytest.raises(ValueError, match="every_n_steps"):
        load_language_config(bad)


def test_empty_model_id_fails_at_load_through_the_full_file(tmp_path: Path) -> None:
    bad = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_MODEL].__setitem__("model_id", ""),
    )
    with pytest.raises(ValueError, match="model_id"):
        load_language_config(bad)


def test_hint_word_limit_zero_fails_at_load_through_the_full_file(tmp_path: Path) -> None:
    """04-10: the emission side's word limit is validated on the same path
    every other model-group field already is."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[LanguageKey.GROUP_MODEL].__setitem__("hint_word_limit", 0),
    )
    with pytest.raises(ValueError, match="hint_word_limit"):
        load_language_config(bad)


def test_loading_succeeds_with_anthropic_api_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """A provider of claude_api with no key set is not a load-time error (D-33)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert load_language_config(POLICE_LANGUAGE) is not None
