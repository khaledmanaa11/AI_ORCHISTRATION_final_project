"""Memoised free-cell graph measurements -- the throughput-critical layer.

The evaluation is called once per leaf of a one-ply joint expansion (up to 50
successors per decision), and the graph primitives in strategy/graph/ cost tens
to hundreds of microseconds each. Recomputing them per leaf is what would make a
search-based mover too slow to ship; memoising them makes it comfortable.

What makes this sound: the barrier set changes at most `barrier_quota` times in a
whole game, and the 25 move-only successors of any decision all share ONE barrier
set. Only the cop's barrier actions introduce new ones -- at most 5 per decision.

These caches memoise PURE functions of their arguments. They hold no game state
and leak nothing between seats (rule 2): the same inputs give the same answer no
matter which process asks. Both seats may share the interpreter during training.
"""

from __future__ import annotations

from functools import lru_cache

from pursuit.strategy.graph.components import articulation_points, component_of, free_cells
from pursuit.strategy.graph.cycles import cycle_rank

#: Bounded so a long training run cannot grow the memo without limit. Sized well
#: above the number of distinct barrier sets one game can produce.
_CACHE_SIZE = 4096


@lru_cache(maxsize=_CACHE_SIZE)
def passable(barriers: frozenset, board_size: int) -> frozenset:
    """Every in-bounds cell that is not sealed.

    Agents do not block one another -- get_legal_moves never excludes the
    opponent's cell, and nothing in book Sec3.4 says otherwise -- so occupancy
    plays no part in passability.
    """
    return frozenset(
        (row, col)
        for row in range(board_size)
        for col in range(board_size)
        if (row, col) not in barriers
    )


def passable_for_cop(barriers: frozenset, cop: tuple, board_size: int) -> frozenset:
    """Passable cells as the cop sees them, including its own sealed cell.

    Book Sec3.4 lets the cop seal the cell it stands on. It is then standing on
    an impassable cell -- legal, and a real denial move -- so its own cell must
    stay in the graph for its distances to mean anything. The thief never needs
    this: a thief on a sealed cell has already been captured (rule 46).
    """
    cells = passable(barriers, board_size)
    return cells if cop in cells else cells | {cop}


@lru_cache(maxsize=_CACHE_SIZE)
def region(cells: frozenset, start: tuple) -> frozenset:
    """The connected component containing *start*."""
    return component_of(cells, start)


@lru_cache(maxsize=_CACHE_SIZE)
def cut_vertices(cells: frozenset) -> frozenset:
    """Articulation points of *cells* -- the chokepoints of a region.

    The single most expensive primitive, and the one whose per-leaf recomputation
    the critics identified as the design's throughput risk. Memoised on the
    component rather than the whole board, so the 25 move-only successors of one
    decision share a single evaluation.
    """
    return articulation_points(cells)


@lru_cache(maxsize=_CACHE_SIZE)
def loops(cells: frozenset) -> int:
    """Cycle rank of *cells*: edges - vertices + components, floored at zero.

    Zero means the region is a forest, which is the cop's structural win
    condition -- a thief in a tree can always be cornered.
    """
    return cycle_rank(cells)


@lru_cache(maxsize=_CACHE_SIZE)
def distances(cells: frozenset, source: tuple) -> dict:
    """BFS hop counts from *source* over *cells*. Unreachable cells are absent.

    Single-source BFS from each agent replaces an all-pairs matrix, which measured
    ~1.8 ms and is pure waste when only two rows are ever read.

    Memoised on (cells, source), which is what makes a one-ply expansion cheap:
    the 25 move-only successors of a decision put the cop on at most 5 distinct
    cells and the thief on at most 5, so 50 BFS calls collapse to 10.

    The returned dict is shared with every other caller holding the same key --
    treat it as read-only. Nothing in this package mutates it.
    """
    if source not in cells:
        return {}
    seen = {source: 0}
    frontier = [source]
    while frontier:
        nxt = []
        for row, col in frontier:
            step = seen[(row, col)] + 1
            for cell in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if cell in cells and cell not in seen:
                    seen[cell] = step
                    nxt.append(cell)
        frontier = nxt
    return seen


@lru_cache(maxsize=_CACHE_SIZE)
def territory(cells: frozenset, cop: tuple, thief: tuple) -> tuple:
    """Two-source Voronoi split: (cells strictly nearer the cop, nearer the thief).

    Equidistant cells belong to neither -- they are contested, and counting them
    for either side would overstate that side's control. Computed from the two
    memoised distance maps rather than by a fresh two-source BFS, which is what
    took ~120 us per leaf and dominated the whole evaluation.
    """
    from_cop = distances(cells, cop)
    from_thief = distances(cells, thief)
    cop_cells = thief_cells = 0
    for cell in cells:
        near_cop = from_cop.get(cell)
        near_thief = from_thief.get(cell)
        if near_cop is None and near_thief is None:
            continue
        if near_thief is None or (near_cop is not None and near_cop < near_thief):
            cop_cells += 1
        elif near_cop is None or near_thief < near_cop:
            thief_cells += 1
    return cop_cells, thief_cells


def clear_caches() -> None:
    """Drop every memo. Tests call this to measure cold cost honestly."""
    for cached in (passable, region, cut_vertices, loops, distances, territory):
        cached.cache_clear()


def board_free_cells(state, params) -> frozenset:
    """Adapter onto strategy.graph.free_cells, kept so callers have one import."""
    return free_cells(state, params)
