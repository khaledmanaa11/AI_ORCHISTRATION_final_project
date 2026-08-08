"""payoff_matrix: one-ply expansion of the joint turn into a bounded [-1, 1] matrix.

Terminals must dominate estimates without a magic large constant (module doc),
so a capture is exactly +1.0, a survival exactly -1.0, and every non-terminal
leaf is strictly inside the open interval. The kill-range test is the anchor:
rule 46 seals the thief's PRE-move cell, so that row must be all-capture no
matter which of the thief's replies is checked against it.
"""

from __future__ import annotations

from pursuit.sdk.actions import CopAction, cop_actions, thief_actions
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.state import GameState
from pursuit.strategy.matrix import payoff_matrix
from pursuit.strategy.weights import PRIOR


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn)


def test_rows_and_columns_match_the_action_generators_in_order(default_params):
    state = _state((2, 2), (4, 4))
    rows, columns, matrix = payoff_matrix(state, PRIOR, default_params, PREFERRED)
    assert rows == cop_actions(state, default_params)
    assert columns == thief_actions(state, default_params)
    assert len(matrix) == len(rows)
    assert all(len(row) == len(columns) for row in matrix)


def test_capture_entry_is_exactly_plus_one(default_params):
    """cop steps onto the thief's cell while the thief stays -- Sec3.5 same-cell
    capture, worth exactly the bound, not a squashed estimate near it."""
    state = _state((2, 2), (2, 3))
    rows, columns, matrix = payoff_matrix(state, PRIOR, default_params, PREFERRED)
    row_index = rows.index(CopAction(move=(2, 3)))
    col_index = columns.index((2, 3))
    assert matrix[row_index][col_index] == 1.0


def test_survival_entry_is_exactly_minus_one(default_params):
    state = _state((0, 0), (6, 6), turn=default_params.survival_threshold - 1)
    rows, columns, matrix = payoff_matrix(state, PRIOR, default_params, PREFERRED)
    row_index = rows.index(CopAction(move=(0, 1)))
    col_index = columns.index((6, 5))
    assert matrix[row_index][col_index] == -1.0


def test_non_terminal_entries_are_strictly_inside_the_bound(default_params):
    """Far apart and early: no single joint move can trigger any of the six
    predicates, so every entry is the squashed estimate -- never at the bound
    that would let it outrank a real win."""
    state = _state((0, 0), (6, 6))
    _, _, matrix = payoff_matrix(state, PRIOR, default_params, PREFERRED)
    for row in matrix:
        for entry in row:
            assert -1.0 < entry < 1.0


def test_kill_range_row_is_all_plus_one_regardless_of_the_thiefs_reply(default_params):
    """The single most important test in this file. Rule 46: a barrier landing
    on the thief's PRE-move cell captures it no matter what it does this turn --
    so the whole row for that barrier action must read +1.0."""
    state = _state((3, 3), (3, 4))
    rows, columns, matrix = payoff_matrix(state, PRIOR, default_params, PREFERRED)
    row_index = rows.index(CopAction(barrier=(3, 4)))
    assert matrix[row_index] == [1.0] * len(columns)
