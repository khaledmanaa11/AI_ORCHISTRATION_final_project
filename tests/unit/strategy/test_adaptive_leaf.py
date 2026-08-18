"""Rule-46 forced-capture leaf and its evidence gate (run 3).

Distance 1 with quota remaining is a capture ONE turn later -- the seal lands
on the cell the thief is leaving -- so an armed leaf must score it just below
a real capture, and the "adaptive" gate must arm it exactly when the visible
state carries evidence of a sealing opponent (any barrier is the cop's).
"""

from __future__ import annotations

import json

import pytest

from pursuit.shared.state import GameState
from pursuit.shared.strategy_config import load_strategy_config
from pursuit.strategy.matrix import FORCED_CAPTURE_VALUE, leaf_value
from pursuit.strategy.valuebrain import ValueSearchBrain
from pursuit.strategy.weights import PRIOR


def _state(cop, thief, placed=0, turn=1):
    return GameState(cop=cop, thief=thief, barriers=frozenset(),
                     barriers_placed=placed, turn=turn)


def test_gap_one_with_quota_scores_forced_capture(default_params):
    state = _state((3, 3), (3, 4))
    value = leaf_value(state, None, PRIOR, default_params, forced_capture=True)
    assert value == FORCED_CAPTURE_VALUE


def test_gap_two_stays_on_the_squashed_estimate(default_params):
    state = _state((3, 3), (3, 5))
    value = leaf_value(state, None, PRIOR, default_params, forced_capture=True)
    assert -1.0 < value < FORCED_CAPTURE_VALUE


def test_exhausted_quota_disarms_the_forced_leaf(default_params):
    state = _state((3, 3), (3, 4), placed=default_params.barrier_quota)
    value = leaf_value(state, None, PRIOR, default_params, forced_capture=True)
    assert value != FORCED_CAPTURE_VALUE


def test_default_keyword_preserves_stock_behaviour(default_params):
    state = _state((3, 3), (3, 4))
    stock = leaf_value(state, None, PRIOR, default_params)
    assert stock == leaf_value(state, None, PRIOR, default_params, forced_capture=False)
    assert stock != FORCED_CAPTURE_VALUE


@pytest.mark.parametrize(
    ("mode", "turn", "placed", "armed"),
    [
        ("adaptive", 3, 0, True),    # early: evidence still possible
        ("adaptive", 20, 1, True),   # a barrier exists: proven sealer
        ("adaptive", 20, 0, False),  # late and never sealed: relax
        ("stock", 3, 1, False),
        ("cautious", 20, 0, True),
    ],
)
def test_forced_leaf_gate(default_params, mode, turn, placed, armed):
    brain = ValueSearchBrain("thief", game_params=default_params,
                             leaf_mode=mode, relax_turn=10)
    state = _state((0, 0), (6, 6), placed=placed, turn=turn)
    assert brain._forced_leaf(state) is armed


def _write_config(tmp_path, leaf_mode="adaptive", relax_turn=10):
    payload = {"version": "1.10", "strategy": {
        "thief_class": "value_search", "weights_path": "",
        "epsilon_eval": 0.0, "max_decision_ms": 50,
        "leaf_mode": leaf_mode, "relax_turn": relax_turn,
    }}
    path = tmp_path / "strategy.json"
    path.write_text(json.dumps(payload))
    return path


def test_loader_accepts_the_new_keys(tmp_path):
    params = load_strategy_config(_write_config(tmp_path))
    assert params.leaf_mode == "adaptive"
    assert params.relax_turn == 10


def test_loader_rejects_an_unknown_leaf_mode(tmp_path):
    with pytest.raises(ValueError, match="leaf_mode"):
        load_strategy_config(_write_config(tmp_path, leaf_mode="bogus"))


def test_loader_rejects_a_negative_relax_turn(tmp_path):
    with pytest.raises(ValueError, match="relax_turn"):
        load_strategy_config(_write_config(tmp_path, relax_turn=-1))
