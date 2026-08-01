"""Tests for the strategy config loader (QUAL-02, QUAL-11, D-18, D-21, D-22)."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.config_keys import StrategyKey, TrainingKey
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config

_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
POLICE_STRATEGY = _CONFIG_DIR / "police" / "strategy.json"
THIEF_STRATEGY = _CONFIG_DIR / "thief" / "strategy.json"


def _write_variant(tmp_path: Path, mutate) -> Path:
    """Write a mutated copy of the police strategy.json to tmp_path."""
    data = json.loads(POLICE_STRATEGY.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "strategy.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def test_loads_all_fields() -> None:
    """A good file loads and returns the expected values (no literal repeated here)."""
    raw = json.loads(POLICE_STRATEGY.read_text(encoding="utf-8"))
    params = load_strategy_config(POLICE_STRATEGY)
    assert params.brain_class == raw[StrategyKey.GROUP][StrategyKey.POLICE_CLASS]
    assert params.qtable_path == raw[StrategyKey.GROUP][StrategyKey.QTABLE_PATH]
    assert params.min_visits == raw[StrategyKey.GROUP][StrategyKey.MIN_VISITS]
    assert params.alpha == raw[TrainingKey.TRAINING_GROUP][TrainingKey.ALPHA]
    assert params.sparring_mix == raw[TrainingKey.TRAINING_GROUP][TrainingKey.SPARRING_MIX]
    assert params.eval_games == raw[TrainingKey.EVAL_GROUP][TrainingKey.EVAL_GAMES]
    assert (
        params.fallback_rate_alert
        == raw[TrainingKey.MONITORING_GROUP][TrainingKey.FALLBACK_RATE_ALERT]
    )


def test_field_types() -> None:
    """Loaded fields carry the correct Python types."""
    params = load_strategy_config(POLICE_STRATEGY)
    assert isinstance(params.min_visits, int)
    assert isinstance(params.alpha, float)
    assert isinstance(params.sparring_mix, list)
    assert isinstance(params.qtable_path, str)


def test_params_are_frozen() -> None:
    """StrategyParams is immutable — assignment raises FrozenInstanceError."""
    params = load_strategy_config(POLICE_STRATEGY)
    with pytest.raises(FrozenInstanceError):
        params.min_visits = 999  # type: ignore[misc]


def test_role_configs_yield_independent_objects() -> None:
    """NET-02-style guarantee: police/thief loads never share a live object."""
    police = load_strategy_config(POLICE_STRATEGY)
    thief = load_strategy_config(THIEF_STRATEGY)
    assert police is not thief
    assert police.qtable_path != thief.qtable_path
    assert load_strategy_config(POLICE_STRATEGY) is not police


def test_missing_key_raises(tmp_path: Path) -> None:
    """A missing required key fails loud, naming the key (never silently defaulted)."""
    bad = _write_variant(tmp_path, lambda d: d[StrategyKey.GROUP].pop(StrategyKey.MIN_VISITS))
    with pytest.raises(KeyError) as excinfo:
        load_strategy_config(bad)
    assert StrategyKey.MIN_VISITS in str(excinfo.value)


def test_non_numeric_alpha_raises(tmp_path: Path) -> None:
    """A non-numeric alpha fails loud with TypeError."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[TrainingKey.TRAINING_GROUP].__setitem__(TrainingKey.ALPHA, "fast"),
    )
    with pytest.raises(TypeError):
        load_strategy_config(bad)


def test_epsilon_out_of_range_raises(tmp_path: Path) -> None:
    """epsilon_start outside [0, 1] fails loud with ValueError."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[TrainingKey.TRAINING_GROUP].__setitem__(TrainingKey.EPSILON_START, 1.5),
    )
    with pytest.raises(ValueError):
        load_strategy_config(bad)


def test_win_rate_bar_out_of_range_raises(tmp_path: Path) -> None:
    """win_rate_margin outside [0, 1] fails loud with ValueError."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[TrainingKey.EVAL_GROUP].__setitem__(TrainingKey.WIN_RATE_MARGIN, -0.1),
    )
    with pytest.raises(ValueError):
        load_strategy_config(bad)


def test_artifacts_dir_defaults_outside_onedrive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-22: an empty artifacts_dir resolves under LOCALAPPDATA, never a literal path."""
    fake_local = tmp_path / "fake_local_appdata"
    monkeypatch.setenv("LOCALAPPDATA", str(fake_local))
    params = load_strategy_config(POLICE_STRATEGY)
    assert str(fake_local) in params.artifacts_dir


def test_reference_impl_path_defaults_empty() -> None:
    """D-21: reference_impl_path is an opt-in empty default, never invented."""
    params: StrategyParams = load_strategy_config(POLICE_STRATEGY)
    assert params.reference_impl_path == ""
