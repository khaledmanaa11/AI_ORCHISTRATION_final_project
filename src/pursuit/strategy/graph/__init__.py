"""Graph measurement layer for run 2 (D-26, D-09 superseded, QUAL-02).

Barriers keep the board triangle-free, so cop-win is equivalent to the
thief's free component being a forest -- the cop destroys cycles, the thief
preserves one. This package is a pure library with no role knowledge and no
shared runtime state (D-03): `03-16` (features), `03-17` (barrier objective)
and `03-18` (alpha-beta search) are all built against this one API.

Re-exports the public names of `components`, `cycles` and `territory` so
consumers import from `pursuit.strategy.graph`, never a submodule. Filled in
as each module lands (components: Task 1; cycles/territory: Tasks 2-3).
"""

from pursuit.strategy.graph.components import (
    articulation_points,
    component_of,
    degree,
    edge_count,
    free_cells,
    neighbors,
)
from pursuit.strategy.graph.cycles import cycle_rank, is_forest, reduction_value

__all__ = [
    "articulation_points",
    "component_of",
    "cycle_rank",
    "degree",
    "edge_count",
    "free_cells",
    "is_forest",
    "neighbors",
    "reduction_value",
]
