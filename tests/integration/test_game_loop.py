"""Integration gate tests for Phase 1 -- Sec10.4 milestone criteria, joint-turn
edition (plan 03-14 / RULES-RESOLUTION.md).

Three tests that exercise the full joint-turn pipeline via the SDK facade
only (engine.make_state / engine.resolve_turn). All game-parameter values
come from the default_params fixture; no hardcoded game numbers appear in
this file -- the (row, col) scenario coordinates below are test-scenario
data, not game parameters, matching the convention already used throughout
test_resolve.py/test_terminal.py.
"""

import pytest

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.state import GameState


def test_legal_turn_sequence(default_params):
    """GATE-1: a legal joint turn -- both agents move at once -- runs
    without error and the game continues."""
    state = engine.make_state(default_params)

    post, outcome = engine.resolve_turn(
        state, CopAction(move=(0, 1)), (3, 4), default_params, PREFERRED
    )
    assert outcome is None  # cop at (0,1), thief at (3,4): no overlap
    assert post.turn == 1
    assert post.cop == (0, 1)
    assert post.thief == (3, 4)


def test_barrier_quota_gate(default_params):
    """GATE-2: barrier placement at quota is REJECTED (ValueError), not
    silently absorbed -- resolve_turn validates both actions before
    applying either (docs/phases/phase-3/RULES-RESOLUTION.md), unlike the
    superseded apply_cop_action/place_barrier pair, which returned the
    unchanged state on an over-quota placement."""
    over_quota_state = GameState(
        cop=(0, 0), thief=(3, 3), barriers=frozenset(),
        barriers_placed=default_params.barrier_quota, turn=0,
    )
    with pytest.raises(ValueError, match="illegal barrier"):
        engine.resolve_turn(
            over_quota_state, CopAction(barrier=(1, 0)), (3, 4), default_params, PREFERRED
        )


def test_all_capture_types(default_params):
    """GATE-3: the cop-lands-on-thief, barrier-on-thief and walled-in
    predicates each yield Outcome.CAPTURE via the joint resolver; a clean
    turn yields None."""
    # Cop steps onto the thief's pre-turn cell.
    landed = GameState(cop=(3, 2), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0)
    _, outcome = engine.resolve_turn(
        landed, CopAction(move=(3, 3)), (3, 3), default_params, PREFERRED
    )
    assert outcome is Outcome.CAPTURE

    # Barrier placed on the thief's pre-turn cell (rule 46).
    barriered = GameState(cop=(0, 0), thief=(0, 1), barriers=frozenset(), barriers_placed=0, turn=0)
    _, outcome = engine.resolve_turn(
        barriered, CopAction(barrier=(0, 1)), (0, 1), default_params, PREFERRED
    )
    assert outcome is Outcome.CAPTURE

    # Thief walled in on every orthogonal neighbour (rule 47).
    walled = GameState(
        cop=(6, 6), thief=(0, 0),
        barriers=frozenset({(0, 1), (1, 0)}), barriers_placed=2, turn=0,
    )
    _, outcome = engine.resolve_turn(
        walled, CopAction(move=(6, 6)), (0, 0), default_params, PREFERRED
    )
    assert outcome is Outcome.CAPTURE

    # A clean turn: game continues.
    clean = GameState(cop=(0, 0), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0)
    _, outcome = engine.resolve_turn(
        clean, CopAction(move=(0, 1)), (3, 4), default_params, PREFERRED
    )
    assert outcome is None
