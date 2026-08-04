"""Tests for pursuit.strategy.graph.territory (03-11 Task 3).

Also exercises the package's public surface via `pursuit.strategy.graph`
directly, since Task 3 finishes `__init__.py`.
"""

from __future__ import annotations

from pursuit.shared.state import GameState
from pursuit.strategy.graph import component_of, free_cells, territory_diff, voronoi_split


def _state(barriers: frozenset = frozenset()) -> GameState:
    return GameState(
        cop=(0, 0), thief=(6, 6), barriers=barriers, barriers_placed=len(barriers), turn=0
    )


def test_two_sources_split_board_symmetrically_with_a_non_empty_equidistant_band(
    default_params,
):
    cells = free_cells(_state(), default_params)
    size = default_params.board_size
    first, second = voronoi_split(cells, (0, 0), (size - 1, size - 1))
    assert first.isdisjoint(second)
    assert len(first) == len(second)
    equidistant = cells - first - second
    assert len(equidistant) > 0


def test_same_source_twice_yields_two_empty_sets(default_params):
    cells = free_cells(_state(), default_params)
    first, second = voronoi_split(cells, (2, 2), (2, 2))
    assert first == frozenset()
    assert second == frozenset()


def test_territory_diff_is_exactly_antisymmetric_under_swapping_arguments(default_params):
    cells = free_cells(_state(), default_params)
    source_a, source_b = (0, 0), (6, 3)
    cell_diff, edge_diff = territory_diff(cells, source_a, source_b)
    swapped_cell_diff, swapped_edge_diff = territory_diff(cells, source_b, source_a)
    assert swapped_cell_diff == -cell_diff
    assert swapped_edge_diff == -edge_diff


def test_barrier_wall_between_sources_gives_one_side_everything_the_other_nothing(
    default_params,
):
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((mid, col) for col in range(size))
    cells = free_cells(_state(barriers=wall), default_params)
    source_a, source_b = (0, 0), (size - 1, 0)
    first, second = voronoi_split(cells, source_a, source_b)
    assert first == component_of(cells, source_a)
    assert second == component_of(cells, source_b)


def test_first_and_second_are_disjoint_in_every_case(default_params):
    cells = free_cells(_state(), default_params)
    for source_a, source_b in [((0, 0), (0, 1)), ((3, 3), (3, 3)), ((0, 0), (6, 6))]:
        first, second = voronoi_split(cells, source_a, source_b)
        assert first.isdisjoint(second)
