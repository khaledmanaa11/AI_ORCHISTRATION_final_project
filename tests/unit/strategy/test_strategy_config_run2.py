"""Tests for the run-2 config surface strategy_config.py gained in plan 03-13
(D-06-superseded, D-18, QUAL-11). Split out of test_strategy_config.py at the
150-line gate -- same pattern as 03-05/06/07/08's own splits."""

import json
from pathlib import Path

import pytest

from pursuit.config_keys import StrategyKey, TrainingKey
from pursuit.shared.strategy_config import load_strategy_config

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


def test_every_run2_key_loads_with_declared_type() -> None:
    """Every key 03-14..03-25 needs is declared and loadable from both role files."""
    for path in (POLICE_STRATEGY, THIEF_STRATEGY):
        params = load_strategy_config(path)
        assert isinstance(params.search_depth_cap, int)
        assert isinstance(params.feature_scale_divisor, float)
        assert isinstance(params.weights_path, str)
        assert isinstance(params.learner_rule, str)
        assert isinstance(params.barrier_candidate_min_degree, int)
        assert isinstance(params.barrier_weight_cycle_rank, float)
        assert isinstance(params.barrier_weight_component_size, float)
        assert isinstance(params.barrier_weight_territory, float)
        assert isinstance(params.barrier_weight_distance, float)
        assert isinstance(params.pfsp_exponent, float)
        assert isinstance(params.weak_opponent_floor, int)
        assert isinstance(params.min_distinct_starts, int)
        assert isinstance(params.terminal_spread_min, float)
        assert isinstance(params.terminal_spread_ratio_max, float)
        assert isinstance(params.floor_episode_fraction_max, float)


def test_barrier_weight_ordering_matches_03_17_objective_ranking() -> None:
    """cycle_rank > component_size > territory > distance (engineering default, 03-17)."""
    params = load_strategy_config(POLICE_STRATEGY)
    assert (
        params.barrier_weight_cycle_rank
        > params.barrier_weight_component_size
        > params.barrier_weight_territory
        > params.barrier_weight_distance
    )


def test_missing_new_key_raises_naming_it(tmp_path: Path) -> None:
    """A missing run-2 key fails loud, naming the key, same as every existing key."""
    bad = _write_variant(
        tmp_path, lambda d: d[StrategyKey.GROUP].pop(StrategyKey.SEARCH_DEPTH_CAP)
    )
    with pytest.raises(KeyError) as excinfo:
        load_strategy_config(bad)
    assert StrategyKey.SEARCH_DEPTH_CAP in str(excinfo.value)


def test_wrong_typed_new_key_raises(tmp_path: Path) -> None:
    """A wrong-typed run-2 key fails loud with TypeError."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[StrategyKey.GROUP].__setitem__(StrategyKey.SEARCH_DEPTH_CAP, "deep"),
    )
    with pytest.raises(TypeError):
        load_strategy_config(bad)


def test_floor_episode_fraction_max_out_of_range_raises(tmp_path: Path) -> None:
    """floor_episode_fraction_max is a genuine [0, 1] fraction and is range-checked."""
    bad = _write_variant(
        tmp_path,
        lambda d: d[TrainingKey.EVAL_GROUP].__setitem__(
            TrainingKey.FLOOR_EPISODE_FRACTION_MAX, 1.5
        ),
    )
    with pytest.raises(ValueError):
        load_strategy_config(bad)


def test_role_files_carry_an_identical_key_set() -> None:
    """D-03: both role files declare the same knobs -- only the class/path values differ."""
    police_raw = json.loads(POLICE_STRATEGY.read_text(encoding="utf-8"))
    thief_raw = json.loads(THIEF_STRATEGY.read_text(encoding="utf-8"))
    police_keys = set(police_raw[StrategyKey.GROUP]) - {StrategyKey.POLICE_CLASS}
    thief_keys = set(thief_raw[StrategyKey.GROUP]) - {StrategyKey.THIEF_CLASS}
    assert police_keys == thief_keys
    for group in (TrainingKey.TRAINING_GROUP, TrainingKey.EVAL_GROUP, TrainingKey.MONITORING_GROUP):
        assert set(police_raw[group]) == set(thief_raw[group])


def test_turn_bucket_fractions_absent_from_both_role_files() -> None:
    """D-06 superseded (plan 03-13): the bucket key is gone, replaced by turns_remaining."""
    police_raw = json.loads(POLICE_STRATEGY.read_text(encoding="utf-8"))
    thief_raw = json.loads(THIEF_STRATEGY.read_text(encoding="utf-8"))
    assert "turn_bucket_fractions" not in police_raw[StrategyKey.GROUP]
    assert "turn_bucket_fractions" not in thief_raw[StrategyKey.GROUP]
    assert not hasattr(load_strategy_config(POLICE_STRATEGY), "turn_bucket_fractions")
