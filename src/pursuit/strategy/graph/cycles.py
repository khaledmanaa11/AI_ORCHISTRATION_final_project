"""Cycle rank, per-cell reduction value, and the forest predicate.

Barriers keep the board triangle-free, so cop-win is equivalent to the
thief's free component being a forest -- the cop destroys cycles, the thief
preserves one (D-09 superseded: distance was the wrong objective for both
roles). Cycle rank of a connected component is the measurable form of that
equivalence.

Cited identities (docs/research/PURSUIT-AND-EVASION-STRATEGY.md Sec3.2-3.3):
cycle rank of a component = E - V + 1; deleting a degree-d cell reduces it
by exactly d - 1. The empty 7x7 grid (V=49, E=84) has cycle rank 36 -- the
test oracle this module is pinned against.

Defines no adjacency of its own; every quantity here is derived through
`components.edge_count`/`components.degree` (QUAL-02).
"""

from __future__ import annotations

from pursuit.strategy.graph.components import Coord, degree, edge_count


def cycle_rank(cells: frozenset[Coord]) -> int:
    """E - V + 1 for a connected cell set. Empty input is 0.

    `cells` is assumed connected -- the intended producer is
    `components.component_of`. The precondition is not defended at runtime:
    a component-count guard costs a traversal 03-18's inner loop cannot
    afford (D-26). Passing a disconnected set silently measures a rank that
    does not correspond to any single component; the barrier-split test in
    `test_cycles.py` exercises the correct, connected-only usage instead.
    """
    if not cells:
        return 0
    return edge_count(cells) - len(cells) + 1


def is_forest(cells: frozenset[Coord]) -> bool:
    """True iff `cycle_rank(cells) == 0` -- the thief's win condition."""
    return cycle_rank(cells) == 0


def reduction_value(cells: frozenset[Coord], cell: Coord) -> int:
    """`degree(cells, cell) - 1` -- the acyclicity gained by barriering `cell`.

    03-17's greedy candidate ranking: a degree-4 cell buys 3 units toward a
    forest, a degree-2 cell buys 1. A cell outside `cells` scores -1 via
    `degree == 0`; 03-17 filters those candidates out, this module does not.
    """
    return degree(cells, cell) - 1
