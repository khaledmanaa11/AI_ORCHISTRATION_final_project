"""ValueSearchBrain: solve the turn's matrix game, sample the equilibrium.

One class serves both seats against the same weight vector (module doc), so the
cop's barrier lives inside the same solved matrix as its moves and the thief
seat must never receive one (D-12, STRAT-05). Reproducibility matters: rule 20
requires a logged seed to replay a game exactly in the viewer.
"""

from __future__ import annotations

import random

import pytest

from pursuit.constants import MoveSource
from pursuit.sdk.actions import cop_actions, thief_actions
from pursuit.shared.state import GameState
from pursuit.strategy.base import Observation
from pursuit.strategy.valuebrain import ValueSearchBrain
from pursuit.strategy.weights import PRIOR


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn)


def _obs(state, role):
    own = state.cop if role == "cop" else state.thief
    target = state.thief if role == "cop" else state.cop
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=0, barriers_used=0, turn_index=state.turn
    )


def _brain(role, default_params, **overrides):
    kwargs = {
        "role": role,
        "game_params": default_params,
        "weights": PRIOR,
        "rng": random.Random(1),
    }
    kwargs.update(overrides)
    return ValueSearchBrain(**kwargs)


def test_cop_barrier_decision_leaves_the_move_at_the_cops_own_cell(default_params):
    """Rule 46: sealing the thief's pre-move cell wins regardless of its reply,
    so the solved matrix's saddle row is that barrier -- move must stay put."""
    state = _state((3, 3), (3, 4))
    decision = _brain("cop", default_params)._decide_move(_obs(state, "cop"), state)
    assert decision.barrier == (3, 4)
    assert decision.move == state.cop


def test_thief_decision_never_carries_a_barrier(default_params):
    state = _state((0, 0), (6, 6))
    brain = _brain("thief", default_params, rng=random.Random(3))
    decision = brain._decide_move(_obs(state, "thief"), state)
    assert decision.barrier is None


def test_same_seed_reproduces_the_same_decision(default_params):
    state = _state((3, 3), (4, 4))
    left = _brain("cop", default_params, rng=random.Random(7))
    right = _brain("cop", default_params, rng=random.Random(7))
    decision_left = left._decide_move(_obs(state, "cop"), state)
    decision_right = right._decide_move(_obs(state, "cop"), state)
    assert (decision_left.move, decision_left.barrier) == (decision_right.move, decision_right.barrier)


def test_different_seeds_can_differ_on_a_mixed_position(default_params):
    """(3,3)/(4,4) has no pure saddle -- solve() genuinely mixes there (probed
    offline: seeds 1 and 2 diverge)."""
    state = _state((3, 3), (4, 4))
    first = _brain("cop", default_params, rng=random.Random(1))._decide_move(_obs(state, "cop"), state)
    second = _brain("cop", default_params, rng=random.Random(2))._decide_move(_obs(state, "cop"), state)
    assert first.move != second.move


def test_epsilon_zero_reports_equilibrium(default_params):
    state = _state((0, 0), (6, 6))
    brain = _brain("cop", default_params, epsilon=0.0)
    decision = brain._decide_move(_obs(state, "cop"), state)
    assert decision.source is MoveSource.EQUILIBRIUM


def test_epsilon_above_zero_reports_exploration(default_params):
    state = _state((0, 0), (6, 6))
    brain = _brain("cop", default_params, epsilon=1.0, rng=random.Random(5))
    decision = brain._decide_move(_obs(state, "cop"), state)
    assert decision.source is MoveSource.EXPLORATION


def test_seed_reseeds_the_draw(default_params):
    """seed() must swap the live RNG, not just record a number."""
    state = _state((3, 3), (4, 4))
    brain = _brain("cop", default_params, rng=random.Random(1))
    brain.seed(2)
    reseeded = brain._decide_move(_obs(state, "cop"), state).move
    fresh = _brain("cop", default_params, rng=random.Random(2))._decide_move(_obs(state, "cop"), state)
    assert reseeded == fresh.move


@pytest.mark.parametrize(
    ("cop", "thief", "role"),
    [((3, 3), (4, 4), "cop"), ((0, 0), (6, 6), "thief"), ((6, 0), (0, 6), "cop")],
)
def test_returned_move_is_always_legal(default_params, cop, thief, role):
    state = _state(cop, thief)
    brain = _brain(role, default_params, rng=random.Random(11))
    decision = brain._decide_move(_obs(state, role), state)
    if role == "cop":
        legal = {action.destination(state.cop) for action in cop_actions(state, default_params)}
    else:
        legal = set(thief_actions(state, default_params))
    assert decision.move in legal
