"""ChaserCop and GreedyEvader -- the fixed, non-drifting self-play anchors.

Not strawmen: measured against each other on the book board they produce a 57%
capture rate (module doc). use_barriers is a materially different opponent, so
True/False gets its own assertion on the cop side, and STRAT-05 means the thief
must never place at all.
"""

from __future__ import annotations

import random

from pursuit.sdk.actions import cop_actions, thief_actions
from pursuit.shared.state import GameState
from pursuit.strategy.base import Observation
from pursuit.strategy.graphcache import distances, passable
from pursuit.strategy.naive import ChaserCop, GreedyEvader


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn)


def _obs(state, role):
    own = state.cop if role == "cop" else state.thief
    target = state.thief if role == "cop" else state.cop
    return Observation(
        own_cell=own, target_cell=target, blocked_mask=0, barriers_used=0, turn_index=state.turn
    )


def _gap(state, params, source, dest):
    return distances(passable(state.barriers, params.board_size), source).get(dest)


def test_chaser_cop_moves_to_reduce_bfs_distance(default_params):
    state = _state((0, 0), (6, 6))
    before = _gap(state, default_params, state.thief, state.cop)
    brain = ChaserCop(game_params=default_params, use_barriers=False, rng=random.Random(1))
    decision = brain._decide_move(_obs(state, "cop"), state)
    after = _gap(state, default_params, state.thief, decision.move)
    assert after < before


def test_chaser_cop_with_barriers_can_place_one(default_params):
    """Seed 1 draws below SEAL_PREFERENCE with a seal in reach -- probed offline."""
    state = _state((3, 3), (3, 4))
    brain = ChaserCop(game_params=default_params, use_barriers=True, rng=random.Random(1))
    decision = brain._decide_move(_obs(state, "cop"), state)
    assert decision.barrier is not None
    assert decision.move == state.cop


def test_chaser_cop_without_barriers_never_places_one(default_params):
    state = _state((3, 3), (3, 4))
    for seed in range(1, 8):
        brain = ChaserCop(game_params=default_params, use_barriers=False, rng=random.Random(seed))
        decision = brain._decide_move(_obs(state, "cop"), state)
        assert decision.barrier is None


def test_greedy_evader_increases_distance_from_the_cop(default_params):
    state = _state((3, 3), (3, 4))
    before = _gap(state, default_params, state.cop, state.thief)
    brain = GreedyEvader(game_params=default_params, rng=random.Random(1))
    decision = brain._decide_move(_obs(state, "thief"), state)
    after = _gap(state, default_params, state.cop, decision.move)
    assert after > before


def test_greedy_evader_never_places_a_barrier(default_params):
    """STRAT-05: the thief may not place -- structural, never a policy choice."""
    state = _state((3, 3), (3, 4))
    brain = GreedyEvader(game_params=default_params, rng=random.Random(2))
    decision = brain._decide_move(_obs(state, "thief"), state)
    assert decision.barrier is None


def test_chaser_cop_move_is_always_legal(default_params):
    state = _state((0, 0), (6, 6))
    brain = ChaserCop(game_params=default_params, use_barriers=False, rng=random.Random(4))
    decision = brain._decide_move(_obs(state, "cop"), state)
    legal = {action.move for action in cop_actions(state, default_params) if not action.is_barrier}
    assert decision.move in legal


def test_greedy_evader_move_is_always_legal(default_params):
    state = _state((0, 0), (6, 6))
    brain = GreedyEvader(game_params=default_params, rng=random.Random(4))
    decision = brain._decide_move(_obs(state, "thief"), state)
    assert decision.move in thief_actions(state, default_params)
