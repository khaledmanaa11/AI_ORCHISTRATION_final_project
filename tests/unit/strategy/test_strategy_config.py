"""Tests for the strategy config loader (QUAL-02, QUAL-11, D-18).

Run-2 (docs/PRD_matrix_mover.md): the live decision path reads exactly
three tunables -- weights_path, epsilon_eval, max_decision_ms -- plus
brain_class. Every Q-learner-only key from run 1 is gone; this file
absorbed test_strategy_config_run2.py's still-meaningful assertion shapes
(missing key fails loud, wrong type raises, unit-interval range check, role
files share their key set) rather than losing that coverage.
"""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.config_keys import StrategyKey
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
    assert params.weights_path == raw[StrategyKey.GROUP][StrategyKey.WEIGHTS_PATH]
    assert params.epsilon_eval == raw[StrategyKey.GROUP][StrategyKey.EPSILON_EVAL]
    assert params.max_decision_ms == raw[StrategyKey.GROUP][StrategyKey.MAX_DECISION_MS]


def test_field_types() -> None:
    """Loaded fields carry the correct Python types."""
    params = load_strategy_config(POLICE_STRATEGY)
    assert isinstance(params.brain_class, str)
    assert isinstance(params.weights_path, str)
    assert isinstance(params.epsilon_eval, float)
    assert isinstance(params.max_decision_ms, int)


def test_params_are_frozen() -> None:
    """StrategyParams is immutable — assignment raises FrozenInstanceError."""
    params = load_strategy_config(POLICE_STRATEGY)
    with pytest.raises(FrozenInstanceError):
        params.max_decision_ms = 999  # type: ignore[misc]


def test_role_configs_yield_independent_objects() -> None:
    """NET-02-style guarantee: police/thief loads never share a live object."""
    police = load_strategy_config(POLICE_STRATEGY)
    thief = load_strategy_config(THIEF_STRATEGY)
    assert police is not thief
    assert load_strategy_config(POLICE_STRATEGY) is not police


def test_role_files_carry_an_identical_key_set() -> None:
    """D-03: both role files declare the same knobs -- only the class value differs."""
    police_raw = json.loads(POLICE_STRATEGY.read_text(encoding="utf-8"))
    thief_raw = json.loads(THIEF_STRATEGY.read_text(encoding="utf-8"))
    police_keys = set(police_raw[StrategyKey.GROUP]) - {StrategyKey.POLICE_CLASS}
    thief_keys = set(thief_raw[StrategyKey.GROUP]) - {StrategyKey.THIEF_CLASS}
    assert police_keys == thief_keys


def test_missing_key_raises(tmp_path: Path) -> None:
    """A missing required key fails loud, naming the key (never silently defaulted)."""
    bad = _write_variant(
        tmp_path, lambda d: d[StrategyKey.GROUP].pop(StrategyKey.MAX_DECISION_MS)
    )
    with pytest.raises(KeyError) as excinfo:
        load_strategy_config(bad)
    assert StrategyKey.MAX_DECISION_MS in str(excinfo.value)


def test_wrong_typed_key_raises(tmp_path: Path) -> None:
    """A wrong-typed key fails loud with TypeError."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[StrategyKey.GROUP].__setitem__(StrategyKey.MAX_DECISION_MS, "fast"),
    )
    with pytest.raises(TypeError):
        load_strategy_config(bad)


def test_epsilon_eval_out_of_range_raises(tmp_path: Path) -> None:
    """epsilon_eval outside [0, 1] fails loud with ValueError."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[StrategyKey.GROUP].__setitem__(StrategyKey.EPSILON_EVAL, 1.5),
    )
    with pytest.raises(ValueError):
        load_strategy_config(bad)


def test_weights_path_defaults_empty() -> None:
    """An empty weights_path is valid -- ValueSearchBrain falls back to the
    hand-set prior (docs/PRD_matrix_mover.md Sec8) rather than failing."""
    params: StrategyParams = load_strategy_config(POLICE_STRATEGY)
    assert params.weights_path == ""
