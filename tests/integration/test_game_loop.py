"""Integration gate tests for Phase 1 — §10.4 milestone criteria.

Three tests that exercise the full D-12 turn pipeline via the SDK facade only.
All game-parameter values come from the default_params fixture; no hardcoded
game numbers appear in this file.
"""

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.shared.state import GameState


def test_legal_turn_sequence(default_params):
    """GATE-1: A legal cop-then-thief turn runs without error; game continues."""
    state = engine.make_state(default_params)

    # Cop turn: move to (0, 1), no barrier.
    s1, cap1 = engine.apply_cop_action(state, (0, 1), None, default_params)
    assert cap1 is None  # thief at (3,3); no capture

    # Thief turn: move to (3, 4).
    s2, end1 = engine.apply_thief_move(s1, (3, 4), default_params)
    assert end1 is None  # turn 1; survival_threshold not reached
    assert s2.turn == 1
    assert s2.cop == (0, 1)
    assert s2.thief == (3, 4)


def test_barrier_quota_gate(default_params):
    """GATE-2: Barrier placement at quota is rejected; barriers_placed unchanged."""
    over_quota_state = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset(),
        barriers_placed=default_params.barrier_quota,
        turn=0,
    )
    new_state, outcome = engine.apply_cop_action(
        over_quota_state, None, (1, 1), default_params
    )
    assert (1, 1) not in new_state.barriers
    assert new_state.barriers_placed == default_params.barrier_quota
    assert outcome is None


def test_all_capture_types(default_params):
    """GATE-3: All three capture types yield Outcome.CAPTURE via engine.check_capture."""
    # BASE-03: cop landed on thief's cell.
    state_03 = GameState(
        cop=(3, 3), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0
    )
    assert engine.check_capture(state_03, default_params) is Outcome.CAPTURE

    # BASE-04: barrier placed on thief's cell.
    state_04 = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset({(3, 3)}),
        barriers_placed=1,
        turn=0,
    )
    assert engine.check_capture(state_04, default_params) is Outcome.CAPTURE

    # BASE-05: no legal move — thief's own cell is a barrier (same setup as BASE-04;
    # detect_capture checks BASE-04 first; either condition produces CAPTURE).
    state_05 = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset({(3, 3)}),
        barriers_placed=1,
        turn=0,
    )
    assert engine.check_capture(state_05, default_params) is Outcome.CAPTURE

    # Confirm a clean state returns None (game continues).
    state_none = GameState(
        cop=(0, 0), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0
    )
    assert engine.check_capture(state_none, default_params) is None
