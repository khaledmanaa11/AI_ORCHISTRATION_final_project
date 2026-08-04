"""Tests for pursuit.strategy.graph.cycles (03-11 Task 2).

Pins the cited identities from docs/research/PURSUIT-AND-EVASION-STRATEGY.md
Sec3.2-3.3: cycle rank = E - V + 1, deleting a degree-d cell reduces rank by
d - 1, and the empty 7x7 grid (V=49, E=84) has cycle rank 36.
"""

from __future__ import annotations

from pursuit.shared.state import GameState
from pursuit.strategy.graph.components import component_of, degree, edge_count, free_cells
from pursuit.strategy.graph.cycles import cycle_rank, is_forest, reduction_value


def _state(barriers: frozenset = frozenset()) -> GameState:
    return GameState(
        cop=(0, 0), thief=(6, 6), barriers=barriers, barriers_placed=len(barriers), turn=0
    )


def test_empty_7x7_board_has_cycle_rank_36_and_is_not_a_forest(default_params):
    cells = free_cells(_state(), default_params)
    assert cycle_rank(cells) == 36
    assert is_forest(cells) is False


def test_empty_cell_set_has_cycle_rank_zero_and_is_a_forest():
    assert cycle_rank(frozenset()) == 0
    assert is_forest(frozenset()) is True


def test_single_cell_and_straight_corridor_are_forests_with_rank_zero():
    assert cycle_rank(frozenset({(0, 0)})) == 0
    assert is_forest(frozenset({(0, 0)})) is True

    corridor = frozenset({(0, col) for col in range(5)})
    assert cycle_rank(corridor) == 0
    assert is_forest(corridor) is True


def test_removing_a_degree_4_cell_drops_rank_by_exactly_3(default_params):
    cells = free_cells(_state(), default_params)
    cell = (3, 3)
    assert degree(cells, cell) == 4
    assert reduction_value(cells, cell) == 3
    reduced = cells - {cell}
    assert cycle_rank(reduced) == cycle_rank(cells) - 3


def test_removing_a_degree_2_cell_drops_rank_by_exactly_1(default_params):
    cells = free_cells(_state(), default_params)
    cell = (0, 0)
    assert degree(cells, cell) == 2
    assert reduction_value(cells, cell) == 1
    reduced = cells - {cell}
    assert cycle_rank(reduced) == cycle_rank(cells) - 1


def test_barrier_split_board_cycle_rank_counts_only_the_queried_side(default_params):
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((mid, col) for col in range(size))
    cells = free_cells(_state(barriers=wall), default_params)
    thief_side = component_of(cells, (size - 1, 0))
    assert cycle_rank(thief_side) == 12
    assert is_forest(thief_side) is False


def test_spanning_tree_of_n_cells_has_edge_count_n_minus_one():
    cells = frozenset({(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)})
    assert is_forest(cells)
    assert edge_count(cells) == len(cells) - 1
