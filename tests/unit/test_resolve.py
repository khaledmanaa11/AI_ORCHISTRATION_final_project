"""resolve_turn: joint application, validation, and the three fixed engine defects.

The six terminal predicates get their own file (test_terminal.py) -- this one
covers that both actions are applied at once, that illegal actions are rejected
rather than absorbed, and that the turn advances exactly once per joint turn.
"""

import pytest

from pursuit.constants import Outcome
from pursuit.sdk.actions import CopAction
from pursuit.sdk.resolve import make_state, resolve_turn
from pursuit.shared.resolution import BOOK_ONLY, PREFERRED
from pursuit.shared.state import GameState


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    """Build a GameState with only the fields a test cares about."""
    return GameState(
        cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn
    )


def test_both_moves_apply_in_one_call(default_params):
    """The joint turn moves both agents from the same pre-turn snapshot."""
    pre = _state(cop=(0, 0), thief=(3, 3))
    post, outcome = resolve_turn(
        pre, CopAction(move=(0, 1)), (3, 4), default_params, PREFERRED
    )
    assert (post.cop, post.thief) == ((0, 1), (3, 4))
    assert outcome is None


def test_turn_advances_exactly_once_per_joint_turn(default_params):
    """One joint turn is one increment -- not one per agent."""
    pre = _state(cop=(0, 0), thief=(3, 3), turn=7)
    post, _ = resolve_turn(pre, CopAction(move=(0, 0)), (3, 3), default_params, PREFERRED)
    assert post.turn == 8


def test_barrier_action_leaves_the_cop_in_place(default_params):
    """Move XOR barrier: placing forgoes movement (book Sec3.4)."""
    pre = _state(cop=(2, 2), thief=(0, 0))
    post, _ = resolve_turn(
        pre, CopAction(barrier=(2, 3)), (0, 1), default_params, PREFERRED
    )
    assert post.cop == (2, 2)
    assert (2, 3) in post.barriers
    assert post.barriers_placed == 1


def test_cop_may_barrier_its_own_cell(default_params):
    """Book Sec3.4 p.21 names the cop's own cell as a legal target explicitly.

    The sequential engine rejected it (barrier.py case 2), removing a real denial
    move: seal the corridor cell you occupy, then step off next turn.
    """
    pre = _state(cop=(2, 2), thief=(0, 0))
    post, _ = resolve_turn(
        pre, CopAction(barrier=(2, 2)), (0, 1), default_params, PREFERRED
    )
    assert (2, 2) in post.barriers
    assert post.cop == (2, 2)


def test_thief_onto_vacated_cop_cell_is_not_a_capture(default_params):
    """Deliberately not a capture: the cop left, and an empty cell is harmless.

    This is the live bug from the sequential engine, where the thief could step
    onto the cop, be spared, and escape -- inverted here into a defined rule.
    """
    pre = _state(cop=(2, 2), thief=(2, 3))
    post, outcome = resolve_turn(
        pre, CopAction(move=(2, 1)), (2, 2), default_params, PREFERRED
    )
    assert outcome is None
    assert post.thief == (2, 2)


def test_illegal_thief_move_is_rejected(default_params):
    """Diagonals are a technical loss (rules 13/14), so they must raise."""
    pre = _state(cop=(0, 0), thief=(3, 3))
    with pytest.raises(ValueError, match="illegal thief move"):
        resolve_turn(pre, CopAction(move=(0, 1)), (4, 4), default_params, PREFERRED)


def test_thief_move_onto_existing_barrier_is_rejected(default_params):
    """apply_move validated nothing; the resolver does. Regression guard."""
    pre = _state(cop=(0, 0), thief=(2, 3), barriers=frozenset({(2, 2)}), placed=1)
    with pytest.raises(ValueError, match="illegal thief move"):
        resolve_turn(pre, CopAction(move=(0, 1)), (2, 2), default_params, PREFERRED)


def test_illegal_cop_move_is_rejected(default_params):
    """An out-of-bounds cop move raises rather than being silently applied."""
    pre = _state(cop=(0, 0), thief=(3, 3))
    with pytest.raises(ValueError, match="illegal cop move"):
        resolve_turn(pre, CopAction(move=(-1, 0)), (3, 4), default_params, PREFERRED)


def test_barrier_beyond_one_step_is_rejected(default_params):
    """Book Sec3.4 bounds placement to the cop's own cell or a 4-neighbour."""
    pre = _state(cop=(0, 0), thief=(3, 3))
    with pytest.raises(ValueError, match="illegal barrier"):
        resolve_turn(pre, CopAction(barrier=(2, 2)), (3, 4), default_params, PREFERRED)


def test_barrier_over_quota_is_rejected(default_params):
    """A spent quota makes every placement illegal, not a silently wasted turn."""
    pre = _state(cop=(0, 0), thief=(3, 3), placed=default_params.barrier_quota)
    with pytest.raises(ValueError, match="illegal barrier"):
        resolve_turn(pre, CopAction(barrier=(0, 1)), (3, 4), default_params, PREFERRED)


def test_cop_action_rejects_both_and_neither(default_params):
    """CopAction is move XOR barrier; the malformed shapes raise at construction."""
    with pytest.raises(ValueError, match="move XOR barrier"):
        CopAction(move=(0, 1), barrier=(0, 1))
    with pytest.raises(ValueError, match="move XOR barrier"):
        CopAction()


def test_make_state_uses_negotiated_start_positions(default_params):
    """Start cells come from config -- book Sec3.3 marks them negotiated."""
    state = make_state(default_params)
    assert (state.cop, state.thief) == (default_params.cop_start, default_params.thief_start)
    assert (state.turn, state.barriers_placed, state.barriers) == (0, 0, frozenset())


def test_book_only_and_preferred_agree_on_a_plain_capture(default_params):
    """The negotiated flags must not change any BOOK predicate."""
    pre = _state(cop=(2, 1), thief=(2, 3))
    for rules in (BOOK_ONLY, PREFERRED):
        _, outcome = resolve_turn(
            pre, CopAction(move=(2, 2)), (2, 2), default_params, rules
        )
        assert outcome is Outcome.CAPTURE
