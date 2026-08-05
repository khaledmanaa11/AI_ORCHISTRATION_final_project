"""QUAL-01 delegation tests for the SDK engine facade (plan 01-04).

One test per SDK method. Each test verifies delegation behaviour only —
internal logic (movement, barrier rules, capture conditions) is covered by
the respective shared-module test files (test_board.py, test_barrier.py,
test_capture.py).  No numeric game-parameter values are hardcoded here.
"""

import pytest

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.shared.state import GameState


def test_make_state(default_params):
    """make_state returns a canonical GameState from config start positions."""
    state = engine.make_state(default_params)
    assert state.cop == default_params.cop_start
    assert state.thief == default_params.thief_start
    assert state.barriers == frozenset()
    assert state.barriers_placed == 0
    assert state.turn == 0


def test_legal_moves_delegates(default_params, start_state):
    """legal_moves delegates to get_legal_moves; stay is always legal."""
    moves = engine.legal_moves(start_state, "thief", default_params)
    assert isinstance(moves, list)
    assert start_state.thief in moves


def test_apply_cop_action_move_only(default_params, start_state):
    """apply_cop_action with move only: cop repositioned, no capture."""
    dest = (0, 1)
    new_state, outcome = engine.apply_cop_action(start_state, dest, None, default_params)
    assert new_state.cop == dest
    assert new_state.thief == start_state.thief
    assert outcome is None


def test_apply_cop_action_barrier_no_move(default_params, start_state):
    """Barrier with move_to=None: barrier placed, cop stays, quota incremented."""
    barrier = (0, 1)
    new_state, outcome = engine.apply_cop_action(start_state, None, barrier, default_params)
    assert barrier in new_state.barriers
    assert new_state.barriers_placed == start_state.barriers_placed + 1
    assert new_state.cop == start_state.cop
    assert outcome is None


def test_apply_cop_action_barrier_move_to_own_cell(default_params, start_state):
    """Barrier with move_to == state.cop behaves like move_to=None (D-12)."""
    barrier = (0, 1)
    new_state, outcome = engine.apply_cop_action(
        start_state, start_state.cop, barrier, default_params
    )
    assert barrier in new_state.barriers
    assert new_state.barriers_placed == start_state.barriers_placed + 1
    assert new_state.cop == start_state.cop
    assert outcome is None


def test_apply_cop_action_move_and_barrier_raises(default_params, start_state):
    """A real move plus a barrier in the same turn violates move-XOR-barrier (D-12)."""
    with pytest.raises(ValueError, match="cannot move to"):
        engine.apply_cop_action(start_state, (0, 1), (1, 0), default_params)


def test_apply_cop_action_barrier_on_thief_is_capture(default_params):
    """Cop adjacent to the thief places a barrier on the thief's cell -> CAPTURE (BASE-04)."""
    state = GameState(cop=(3, 2), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0)
    new_state, outcome = engine.apply_cop_action(state, None, state.thief, default_params)
    assert state.thief in new_state.barriers
    assert outcome is Outcome.CAPTURE


def test_apply_thief_move_increments_turn(default_params, start_state):
    """apply_thief_move repositions thief and increments turn counter."""
    dest = (3, 4)
    new_state, outcome = engine.apply_thief_move(start_state, dest, default_params)
    assert new_state.thief == dest
    assert new_state.turn == start_state.turn + 1
    assert outcome is None


def test_check_capture_delegates(default_params):
    """check_capture delegates to detect_capture; cop==thief yields CAPTURE."""
    state = GameState(
        cop=(3, 3),
        thief=(3, 3),
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )
    result = engine.check_capture(state, default_params)
    assert result is Outcome.CAPTURE


def test_score_delegates(default_params):
    """score delegates to score_outcome; values match params.score_capture_*."""
    cop_score, thief_score = engine.score(Outcome.CAPTURE, default_params)
    assert cop_score == default_params.score_capture_cop
    assert thief_score == default_params.score_capture_thief
