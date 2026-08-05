"""Tests for training/rewards.py -- Table-17-sourced terminal rewards and the
unchanged non-terminal step shaping (R2 fix, 03-14).
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from pursuit.constants import Outcome
from pursuit.shared.config import load_game_params
from pursuit.shared.strategy_config import load_strategy_config
from training.rewards import step_reward, terminal_reward

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "config"


def _game_params():
    return load_game_params(_CONFIG_DIR / "police" / "game_params.json")


def _cop_params():
    return load_strategy_config(_CONFIG_DIR / "police" / "strategy.json")


@pytest.mark.parametrize(
    "role, outcome, field",
    [
        ("cop", Outcome.CAPTURE, "score_capture_cop"),
        ("thief", Outcome.CAPTURE, "score_capture_thief"),
        ("cop", Outcome.SURVIVAL, "score_survival_cop"),
        ("thief", Outcome.SURVIVAL, "score_survival_thief"),
    ],
)
def test_terminal_reward_matches_table_17_for_every_role_outcome_pair(role, outcome, field):
    game_params = _game_params()
    expected = getattr(game_params, field)
    assert terminal_reward(role, outcome, game_params) == expected
    assert expected != 0  # none of Table 17's four terminal values is zero


@pytest.mark.parametrize("outcome", [Outcome.TIE, Outcome.TECHNICAL_LOSS])
def test_terminal_reward_raises_on_an_unmapped_outcome(outcome):
    """Phase 3 emits only CAPTURE/SURVIVAL -- an unmapped pair must raise,
    not silently return 0.0 (that would reintroduce the R2 zero-signal
    bug this module exists to close)."""
    with pytest.raises(ValueError):
        terminal_reward("cop", outcome, _game_params())


def test_step_reward_cop_with_barrier_exceeds_without_by_exactly_the_gain():
    params = _cop_params()
    without = step_reward("cop", barrier_placed=False, params=params)
    with_barrier = step_reward("cop", barrier_placed=True, params=params)
    assert with_barrier - without == pytest.approx(params.reward_barrier_gain)


def test_step_reward_ignores_the_barrier_flag_for_the_thief():
    params = _cop_params()  # reward_step schema is identical across role config files
    with_flag = step_reward("thief", barrier_placed=True, params=params)
    without_flag = step_reward("thief", barrier_placed=False, params=params)
    assert with_flag == without_flag == params.reward_step


def test_no_reward_magnitude_literal_in_the_rewards_module():
    """AST guard (D-18, project rule 1): every terminal/step magnitude must
    come from config, never a literal written in this module."""
    tree = ast.parse(pathlib.Path("training/rewards.py").read_text(encoding="utf-8"))
    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
    ]
    assert literals == []
