"""Tests for QLearningBrain's config wiring, the min_visits fallback trigger,
and decision provenance (STRAT-01/02, D-08, AI-SPEC E2/E3). Exploration, the
update rule, decision-path I/O, and role isolation live in
test_qlearning_learning.py (150-line gate split, see 03-06-SUMMARY.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pursuit.constants import Action, MoveSource, cell_for
from pursuit.shared.config import GameParams
from pursuit.strategy import registry
from pursuit.strategy.encoding import encode_state
from pursuit.strategy.qlearning import QLearningBrain
from pursuit.strategy.qtable import QTable
from tests.unit.strategy._qlearning_fixtures import (
    MIN_VISITS,
    make_obs,
    make_state,
    params_for,
    seeded_table,
)


def test_builds_via_build_brain_from_config_for_both_roles(
    tmp_path: Path, default_params: GameParams
) -> None:
    QTable().save(tmp_path / "cop.json")
    QTable().save(tmp_path / "thief.json")
    cop = registry.build_brain("cop", params_for("cop", tmp_path / "cop.json"), default_params)
    thief = registry.build_brain(
        "thief", params_for("thief", tmp_path / "thief.json"), default_params
    )
    assert isinstance(cop, QLearningBrain)
    assert isinstance(thief, QLearningBrain)


def test_decide_move_on_open_board_proposes_no_barrier(
    tmp_path: Path, default_params: GameParams
) -> None:
    """03-07: the cop's barrier sub-policy is wired, but this scenario is a
    wide-open board with no chokepoint, so choose_barrier legitimately
    returns None here too -- see test_barriers.py for the wired, non-None
    case and for the thief-always-None guarantee under both brains."""
    params = params_for("cop", tmp_path / "qtable.json")
    QTable().save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)
    obs = make_obs()
    decision = brain._decide_move(obs, make_state(obs.own_cell, obs.target_cell))
    assert decision.barrier is None
    assert decision.source is MoveSource.FALLBACK


def test_at_min_visits_uses_table_with_qtable_source(
    tmp_path: Path, default_params: GameParams
) -> None:
    obs = make_obs()
    params = params_for("cop", tmp_path / "qtable.json")
    key = encode_state(obs, params, default_params)
    seeded_table(key, MIN_VISITS).save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)
    decision = brain._pick_move(obs, make_state(obs.own_cell, obs.target_cell))
    assert decision.source is MoveSource.QTABLE
    assert decision.move == cell_for(Action(2), obs.own_cell)


def test_one_below_min_visits_uses_fallback_despite_strong_value(
    tmp_path: Path, default_params: GameParams
) -> None:
    obs = make_obs()
    params = params_for("cop", tmp_path / "qtable.json")
    key = encode_state(obs, params, default_params)
    seeded_table(key, MIN_VISITS - 1).save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)
    decision = brain._pick_move(obs, make_state(obs.own_cell, obs.target_cell))
    assert decision.source is MoveSource.FALLBACK


def test_absent_key_uses_fallback(tmp_path: Path, default_params: GameParams) -> None:
    params = params_for("cop", tmp_path / "qtable.json")
    QTable().save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)
    obs = make_obs()
    decision = brain._pick_move(obs, make_state(obs.own_cell, obs.target_cell))
    assert decision.source is MoveSource.FALLBACK


@pytest.mark.parametrize("visits", range(0, MIN_VISITS + 3))
def test_boundary_sweep_routes_correctly(
    visits: int, tmp_path: Path, default_params: GameParams
) -> None:
    obs = make_obs()
    params = params_for("cop", tmp_path / "qtable.json")
    key = encode_state(obs, params, default_params)
    seeded_table(key, visits).save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)
    decision = brain._pick_move(obs, make_state(obs.own_cell, obs.target_cell))
    expected = MoveSource.QTABLE if visits >= MIN_VISITS else MoveSource.FALLBACK
    assert decision.source is expected
