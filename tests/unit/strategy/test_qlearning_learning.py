"""Tests for QLearningBrain's exploration seeding, greedy eval mode, the
Q-update rule, decision-path I/O isolation, and role isolation (D-03/D-19,
AI-SPEC E11). Config wiring and the min_visits trigger live in
test_qlearning.py (150-line gate split, see 03-06-SUMMARY.md)."""

from __future__ import annotations

import ast
import random
from pathlib import Path

import pytest

from pursuit.constants import Action, cell_for
from pursuit.shared.config import GameParams
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


def _exploring_brain(
    tmp_path: Path, default_params: GameParams, seed: int, name: str
) -> QLearningBrain:
    obs = make_obs()
    params = params_for("cop", tmp_path / f"{name}.json")
    key = encode_state(obs, params, default_params)
    seeded_table(key, MIN_VISITS, action=4, value=0.0).save(params.qtable_path)
    brain = QLearningBrain(
        role="cop", params=params, game_params=default_params, rng=random.Random(seed)
    )
    brain.epsilon = 1.0  # force exploration on every decision
    return brain


def test_exploration_is_seeded_reproducible_and_diverges_on_seed(
    tmp_path: Path, default_params: GameParams
) -> None:
    obs = make_obs()
    state = make_state(obs.own_cell, obs.target_cell)
    brain_a = _exploring_brain(tmp_path, default_params, seed=7, name="a")
    brain_b = _exploring_brain(tmp_path, default_params, seed=7, name="b")
    brain_c = _exploring_brain(tmp_path, default_params, seed=99, name="c")

    seq_a = [brain_a._pick_move(obs, state).move for _ in range(20)]
    seq_b = [brain_b._pick_move(obs, state).move for _ in range(20)]
    seq_c = [brain_c._pick_move(obs, state).move for _ in range(20)]

    assert seq_a == seq_b
    assert seq_a != seq_c


def test_greedy_at_eval_never_explores(tmp_path: Path, default_params: GameParams) -> None:
    obs = make_obs()
    params = params_for("cop", tmp_path / "qtable.json")
    key = encode_state(obs, params, default_params)
    seeded_table(key, MIN_VISITS, action=1, value=3.0).save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)
    assert brain.epsilon == 0.0  # config's epsilon_eval, wired without override
    state = make_state(obs.own_cell, obs.target_cell)
    moves = {brain._pick_move(obs, state).move for _ in range(200)}
    assert moves == {cell_for(Action(1), obs.own_cell)}


def test_update_rule_matches_formula_and_bumps_visits(
    tmp_path: Path, default_params: GameParams
) -> None:
    params = params_for("cop", tmp_path / "qtable.json")
    prev_key = encode_state(make_obs(own=(1, 1)), params, default_params)
    next_key = encode_state(make_obs(own=(2, 2)), params, default_params)
    table = QTable()
    table.set(prev_key, 1, 0.2)
    table.set(next_key, 0, 0.9)
    table.set(next_key, 3, 0.4)
    table.save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)

    brain.update(prev_key, 1, reward=1.0, next_key=next_key)

    expected = 0.2 + params.alpha * (1.0 + params.gamma * 0.9 - 0.2)
    assert brain._table.get(prev_key, 1) == pytest.approx(expected)
    assert brain._table.visits(prev_key) == 1


def test_terminal_update_bootstraps_from_reward_alone_and_ignores_next_key(
    tmp_path: Path, default_params: GameParams
) -> None:
    """R4: with terminal=True the target collapses to `reward` alone --
    seeding next_key's Q-values arbitrarily large must not change the
    stored result (the leak this plan closes), and prev_key's visit count
    still bumps exactly as the non-terminal case does."""
    params = params_for("cop", tmp_path / "qtable.json")
    prev_key = encode_state(make_obs(own=(1, 1)), params, default_params)
    next_key = encode_state(make_obs(own=(2, 2)), params, default_params)
    table = QTable()
    table.set(prev_key, 1, 0.2)
    table.set(next_key, 0, 999.0)  # seeded arbitrarily large -- must be ignored
    table.save(params.qtable_path)
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)

    brain.update(prev_key, 1, reward=1.0, next_key=next_key, terminal=True)

    expected = 0.2 + params.alpha * (1.0 - 0.2)  # bootstrap term dropped entirely
    assert brain._table.get(prev_key, 1) == pytest.approx(expected)
    assert brain._table.visits(prev_key) == 1


def test_no_io_on_decision_path(
    tmp_path: Path, default_params: GameParams, monkeypatch: pytest.MonkeyPatch
) -> None:
    obs = make_obs()
    params = params_for("cop", tmp_path / "qtable.json")
    key = encode_state(obs, params, default_params)
    seeded_table(key, MIN_VISITS - 1).save(params.qtable_path)  # exercises the fallback path
    brain = QLearningBrain(role="cop", params=params, game_params=default_params)

    def _raise(*_a, **_k):
        raise AssertionError("no file I/O expected on the decision path")

    monkeypatch.setattr("builtins.open", _raise)
    decision = brain._pick_move(obs, make_state(obs.own_cell, obs.target_cell))
    assert decision.move is not None


def test_two_role_instances_share_no_table(tmp_path: Path, default_params: GameParams) -> None:
    QTable().save(tmp_path / "cop.json")
    QTable().save(tmp_path / "thief.json")
    cop = QLearningBrain(
        role="cop", params=params_for("cop", tmp_path / "cop.json"), game_params=default_params
    )
    thief = QLearningBrain(
        role="thief",
        params=params_for("thief", tmp_path / "thief.json"),
        game_params=default_params,
    )
    assert cop._table is not thief._table
    cop._table.set("shared-looking-key", 0, 42.0)
    assert thief._table.get("shared-looking-key", 0) == 0.0


def test_no_class_level_mutable_state() -> None:
    """D-03/project rule 2: only __init__-assigned instance attributes exist,
    so one QLearningBrain instance can never leak state into another's."""
    tree = ast.parse(Path("src/pursuit/strategy/qlearning.py").read_text(encoding="utf-8"))
    class_node = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    for node in class_node.body:
        assert not isinstance(node, ast.Assign | ast.AnnAssign)
