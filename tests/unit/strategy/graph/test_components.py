"""Tests for pursuit.strategy.graph.components (03-11 Task 1).

Pins the package's one adjacency implementation equal to the engine's own
get_legal_moves (QUAL-02), and proves the never-raise contract for
out-of-set cells (the pathfind.UNREACHABLE precedent).
"""

from __future__ import annotations

import dataclasses

from pursuit.shared.board import get_legal_moves
from pursuit.shared.state import GameState
from pursuit.strategy.graph.components import (
    articulation_points,
    component_of,
    degree,
    edge_count,
    free_cells,
    neighbors,
)


def _state(barriers: frozenset = frozenset()) -> GameState:
    return GameState(
        cop=(0, 0), thief=(6, 6), barriers=barriers, barriers_placed=len(barriers), turn=0
    )


def test_empty_board_is_one_component_with_84_edges_and_no_cut_vertices(default_params):
    cells = free_cells(_state(), default_params)
    assert len(cells) == default_params.board_size**2
    assert component_of(cells, (0, 0)) == cells
    assert edge_count(cells) == 84
    assert articulation_points(cells) == frozenset()


def test_barrier_wall_splits_board_into_two_components_summing_to_the_free_total(
    default_params,
):
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((mid, col) for col in range(size))
    cells = free_cells(_state(barriers=wall), default_params)
    left = component_of(cells, (0, 0))
    right = component_of(cells, (size - 1, 0))
    assert left.isdisjoint(right)
    assert len(left) + len(right) == len(cells)


def test_degree_by_position_corner_edge_interior(default_params):
    cells = free_cells(_state(), default_params)
    size = default_params.board_size
    assert degree(cells, (0, 0)) == 2
    assert degree(cells, (0, 1)) == 3
    assert degree(cells, (size // 2, size // 2)) == 4


def test_barrier_corridor_produces_cut_vertex_at_the_choke_cell(default_params):
    size = default_params.board_size
    mid = size // 2
    gap_col = size // 2
    wall = frozenset((mid, col) for col in range(size) if col != gap_col)
    cells = free_cells(_state(barriers=wall), default_params)
    assert (mid, gap_col) in articulation_points(cells)


def test_out_of_set_cell_returns_empty_component_and_zero_degree(default_params):
    cells = free_cells(_state(barriers=frozenset({(3, 3)})), default_params)
    assert component_of(cells, (3, 3)) == frozenset()
    assert degree(cells, (3, 3)) == 0


def test_neighbors_equals_engine_legal_moves_minus_stay_for_every_free_cell(default_params):
    cells = free_cells(_state(), default_params)
    for cell in cells:
        probe = dataclasses.replace(_state(), cop=cell)
        engine_neighbors = set(get_legal_moves(probe, "cop", default_params)) - {cell}
        assert neighbors(cells, cell) == engine_neighbors
