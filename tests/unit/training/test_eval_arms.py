"""Tests for training/eval_arms.py -- the three GATE-4 arms and the
read-only game runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from pursuit.constants import Outcome
from pursuit.shared.config import GameParams, load_game_params
from pursuit.strategy.heuristic import HeuristicBrain
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable
from training.eval_arms import (
    ARM_BASELINE,
    ARM_COP_LEARNER,
    ARM_THIEF_LEARNER,
    MissingQTableError,
    build_arm_brains,
    play_game,
)
from training.eval_scenarios import Scenario

_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


def _game_params() -> GameParams:
    return load_game_params(_CONFIG_DIR / "police" / "game_params.json")


def _scenario(**overrides) -> Scenario:
    fields = {
        "id": "s", "group": "normal", "seed": 1, "cop_start": (0, 0), "thief_start": (3, 3),
        "preplaced_barriers": (), "role_under_test": "both", "expected": "baseline_relative",
    }
    fields.update(overrides)
    return Scenario(**fields)


def test_baseline_arm_builds_two_heuristic_brains(default_params: GameParams) -> None:
    cop, thief = build_arm_brains(ARM_BASELINE, default_params, seed=1, cop_qtable="x", thief_qtable="y")
    assert isinstance(cop, HeuristicBrain)
    assert isinstance(thief, HeuristicBrain)


def test_cop_learner_arm_raises_missing_qtable_when_absent(tmp_path: Path, default_params: GameParams) -> None:
    with pytest.raises(MissingQTableError):
        build_arm_brains(
            ARM_COP_LEARNER, default_params, seed=1,
            cop_qtable=tmp_path / "no-such-table.json", thief_qtable="unused",
        )


def test_thief_learner_arm_builds_qlearning_and_heuristic(tmp_path: Path, default_params: GameParams) -> None:
    table_path = tmp_path / "thief.json"
    QTable().save(table_path)
    cop, thief = build_arm_brains(
        ARM_THIEF_LEARNER, default_params, seed=1, cop_qtable="unused", thief_qtable=table_path
    )
    assert isinstance(cop, HeuristicBrain)
    assert isinstance(thief, QLearningBrain)


def test_unknown_arm_raises_value_error(default_params: GameParams) -> None:
    with pytest.raises(ValueError, match="unknown arm"):
        build_arm_brains("not-an-arm", default_params, seed=1, cop_qtable="x", thief_qtable="y")


def test_play_game_reaches_a_terminal_outcome(default_params: GameParams) -> None:
    """Adjacent cop/thief on an open board: the cop must capture quickly,
    well inside the move_ceiling budget -- proves the read-only loop
    actually terminates rather than looping to the safety bound."""
    cop, thief = build_arm_brains(ARM_BASELINE, default_params, seed=1, cop_qtable="x", thief_qtable="y")
    scenario = _scenario(cop_start=(3, 3), thief_start=(3, 4))
    result = play_game(cop, thief, scenario, seed=1, game_params=default_params)
    assert result.outcome is Outcome.CAPTURE
    assert result.scenario_id == "s"
    assert result.seed == 1


def test_play_game_honours_a_nonzero_start_turn(default_params: GameParams) -> None:
    """A thief that starts already past survival_threshold - 1 survives on
    its very next turn without needing to evade anything."""
    cop, thief = build_arm_brains(ARM_BASELINE, default_params, seed=1, cop_qtable="x", thief_qtable="y")
    scenario = _scenario(
        cop_start=(0, 0), thief_start=(6, 6), start_turn=default_params.survival_threshold - 1
    )
    result = play_game(cop, thief, scenario, seed=1, game_params=default_params)
    assert result.outcome is Outcome.SURVIVAL


def test_play_game_replays_preplaced_barriers(default_params: GameParams) -> None:
    """A cop walled in on every side except its own cell cannot move off it;
    the game still terminates (via evaluate_turn_end) rather than crashing."""
    size = default_params.board_size
    barriers = tuple(
        cell for cell in [(0, 1), (1, 0)] if 0 <= cell[0] < size and 0 <= cell[1] < size
    )
    cop, thief = build_arm_brains(ARM_BASELINE, default_params, seed=1, cop_qtable="x", thief_qtable="y")
    scenario = _scenario(cop_start=(0, 0), thief_start=(6, 6), preplaced_barriers=barriers)
    result = play_game(cop, thief, scenario, seed=1, game_params=default_params)
    assert result.outcome in (Outcome.CAPTURE, Outcome.SURVIVAL)
