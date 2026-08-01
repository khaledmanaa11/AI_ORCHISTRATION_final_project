"""Tests for training/eval_scenarios.py -- the fixed eval scenario set and
D-23's held-out-seed guarantee."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pursuit.shared.strategy_config import load_strategy_config
from training.eval_scenarios import (
    DEFAULT_SCENARIOS_PATH,
    Scenario,
    assert_seeds_held_out,
    load_scenarios,
    repeat_seeds,
)

_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


def _cop_params():
    return load_strategy_config(_CONFIG_DIR / "police" / "strategy.json")


def test_committed_scenario_file_loads_and_matches_configured_size() -> None:
    scenarios = load_scenarios(DEFAULT_SCENARIOS_PATH)
    assert len(scenarios) == _cop_params().eval_scenarios
    assert all(isinstance(s, Scenario) for s in scenarios)
    assert len({s.id for s in scenarios}) == len(scenarios), "scenario ids must be unique"


def test_committed_scenario_seeds_are_held_out() -> None:
    scenarios = load_scenarios(DEFAULT_SCENARIOS_PATH)
    assert_seeds_held_out(scenarios, _cop_params())  # must not raise


def test_assert_seeds_held_out_raises_when_a_seed_collides_with_training(tmp_path: Path) -> None:
    params = _cop_params()
    colliding = Scenario(
        id="bad", group="normal", seed=params.seed, cop_start=(0, 0), thief_start=(1, 1),
        preplaced_barriers=(), role_under_test="both", expected="baseline_relative",
    )
    with pytest.raises(AssertionError):
        assert_seeds_held_out([colliding], params)


def test_assert_seeds_held_out_raises_on_duplicate_seeds() -> None:
    params = _cop_params()
    base = params.seed + params.eval_seed_offset
    dup = Scenario(
        id="a", group="normal", seed=base, cop_start=(0, 0), thief_start=(1, 1),
        preplaced_barriers=(), role_under_test="both", expected="baseline_relative",
    )
    with pytest.raises(AssertionError):
        assert_seeds_held_out([dup, dup], params)


def test_start_turn_defaults_to_zero_when_absent(tmp_path: Path) -> None:
    payload = {
        "scenarios": [
            {
                "id": "x", "group": "normal", "seed": 1, "cop_start": [0, 0],
                "thief_start": [1, 1], "preplaced_barriers": [],
                "role_under_test": "both", "expected": "baseline_relative",
            }
        ]
    }
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    scenarios = load_scenarios(path)
    assert scenarios[0].start_turn == 0


def test_start_turn_is_read_when_present(tmp_path: Path) -> None:
    payload = {
        "scenarios": [
            {
                "id": "x", "group": "stall", "seed": 1, "cop_start": [0, 0],
                "thief_start": [1, 1], "preplaced_barriers": [[2, 2]],
                "start_turn": 30, "role_under_test": "thief", "expected": "thief_survives",
            }
        ]
    }
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    scenarios = load_scenarios(path)
    assert scenarios[0].start_turn == 30
    assert scenarios[0].preplaced_barriers == ((2, 2),)


def test_load_scenarios_raises_on_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"scenarios": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="zero scenarios"):
        load_scenarios(path)


def test_repeat_seeds_derives_a_deterministic_disjoint_run() -> None:
    scenario = Scenario(
        id="a", group="normal", seed=100, cop_start=(0, 0), thief_start=(1, 1),
        preplaced_barriers=(), role_under_test="both", expected="baseline_relative",
    )
    seeds = repeat_seeds(scenario, 5)
    assert seeds == [100, 101, 102, 103, 104]
