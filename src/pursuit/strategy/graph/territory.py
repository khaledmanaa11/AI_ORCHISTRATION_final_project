"""Two-source Voronoi split and its cell-count / edge-count differences.

Imports `components` for adjacency and edge counting; defines no adjacency
of its own (QUAL-02). Positional and symmetric -- neither function names a
side (D-03); a caller passes its own cell first and reads a positive
`territory_diff` as its own advantage.
"""

from __future__ import annotations

from collections import deque

from pursuit.strategy.graph.components import Coord, edge_count, neighbors


def voronoi_split(
    cells: frozenset[Coord], first: Coord, second: Coord
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    """Split `cells` by whichever of `first`/`second` is strictly closer.

    One simultaneous two-source BFS: both frontiers advance one layer per
    round in the same loop, sharing no state with each other -- a cell's
    distance from `first` never depends on where `second` is, so the split
    is exactly "compare each source's own shortest-path distance", computed
    without re-walking the grid twice from scratch.

    Equidistant cells belong to **neither** side -- this grid is bipartite,
    so ties are common, not exotic; dropping them keeps the split
    deterministic with no tie-break rule. Cells unreachable from both
    sources also belong to neither, so `first | second` is a strict subset
    of the reachable cells: a caller assuming a partition is wrong.
    `first`/`second` (the returned sets) are always disjoint.
    """
    dist_a: dict[Coord, int] = {first: 0} if first in cells else {}
    dist_b: dict[Coord, int] = {second: 0} if second in cells else {}
    frontier_a: deque[Coord] = deque(dist_a)
    frontier_b: deque[Coord] = deque(dist_b)

    while frontier_a or frontier_b:
        frontier_a = _advance(cells, frontier_a, dist_a)
        frontier_b = _advance(cells, frontier_b, dist_b)

    side_a = frozenset(cell for cell, d in dist_a.items() if d < dist_b.get(cell, d + 1))
    side_b = frozenset(cell for cell, d in dist_b.items() if d < dist_a.get(cell, d + 1))
    return side_a, side_b


def _advance(
    cells: frozenset[Coord], frontier: deque[Coord], dist: dict[Coord, int]
) -> deque[Coord]:
    """One BFS layer out of every cell in `frontier`, recording newly
    discovered cells into `dist`. Returns the next layer's frontier."""
    next_frontier: deque[Coord] = deque()
    for cell in frontier:
        for neighbor in neighbors(cells, cell):
            if neighbor not in dist:
                dist[neighbor] = dist[cell] + 1
                next_frontier.append(neighbor)
    return next_frontier


def territory_diff(cells: frozenset[Coord], first: Coord, second: Coord) -> tuple[int, int]:
    """`(cell_diff, edge_diff)` between `first`'s and `second`'s Voronoi sides.

    `edge_diff` is computed via `components.edge_count` -- no second edge
    counter anywhere in the package (QUAL-02). Exactly antisymmetric under
    swapping `first`/`second`.
    """
    side_a, side_b = voronoi_split(cells, first, second)
    return len(side_a) - len(side_b), edge_count(side_a) - edge_count(side_b)
