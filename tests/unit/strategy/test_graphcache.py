"""graphcache: memoised, PURE graph primitives (rule 2 -- no shared game state).

passable/distances/territory take a frozenset and coordinates, never a role or
process identity, so cold and warm cache reads must agree for every seat. The
memoisation itself is only sound if clear_caches() genuinely drops it.
"""

from __future__ import annotations

import pytest

from pursuit.strategy import graphcache


@pytest.fixture(autouse=True)
def _cold_caches():
    """Every test starts from a cold memo so no test can leak state into another."""
    graphcache.clear_caches()


def test_passable_excludes_barriers(default_params):
    size = default_params.board_size
    barriers = frozenset({(0, 1)})
    cells = graphcache.passable(barriers, size)
    assert (0, 1) not in cells
    assert len(cells) == size * size - 1


def test_passable_for_cop_readds_the_cops_own_sealed_cell(default_params):
    """Book Sec3.4: the cop may seal the cell it stands on and still needs its
    own distances to mean anything."""
    size = default_params.board_size
    barriers = frozenset({(1, 1)})
    cop_view = graphcache.passable_for_cop(barriers, (1, 1), size)
    assert (1, 1) in cop_view


def test_passable_for_cop_is_unchanged_when_the_cop_is_not_sealed(default_params):
    size = default_params.board_size
    barriers = frozenset({(1, 1)})
    cop_view = graphcache.passable_for_cop(barriers, (0, 0), size)
    assert cop_view == graphcache.passable(barriers, size)


def test_distances_returns_hop_counts(default_params):
    size = default_params.board_size
    cells = graphcache.passable(frozenset(), size)
    dist = graphcache.distances(cells, (0, 0))
    assert dist[(0, 0)] == 0
    assert dist[(0, 1)] == 1
    assert dist[(size - 1, size - 1)] == 2 * (size - 1)


def test_distances_omits_unreachable_cells(default_params):
    """A full barrier column splits the board -- the far side is ABSENT from
    the map, never given some large stand-in distance."""
    size = default_params.board_size
    barriers = frozenset((row, 1) for row in range(size))
    cells = graphcache.passable(barriers, size)
    dist = graphcache.distances(cells, (0, 0))
    assert (size - 1, 0) in dist
    assert (0, size - 1) not in dist


def test_distances_from_a_source_outside_the_cell_set_is_empty(default_params):
    size = default_params.board_size
    cells = graphcache.passable(frozenset({(0, 0)}), size)
    assert graphcache.distances(cells, (0, 0)) == {}


def test_territory_splits_with_equidistant_cells_going_to_neither(default_params):
    """cop=(0,0), thief=(0,2): column 1 is equidistant from both (1 hop each)
    and must be counted for neither side."""
    size = default_params.board_size
    cells = graphcache.passable(frozenset(), size)
    cop_cells, thief_cells = graphcache.territory(cells, (0, 0), (0, 2))
    assert cop_cells == size
    assert thief_cells == size * (size - 2)
    assert cop_cells + thief_cells + size == len(cells)


def test_clear_caches_actually_resets(default_params):
    size = default_params.board_size
    graphcache.passable(frozenset(), size)
    assert graphcache.passable.cache_info().currsize >= 1
    graphcache.clear_caches()
    assert graphcache.passable.cache_info().currsize == 0
