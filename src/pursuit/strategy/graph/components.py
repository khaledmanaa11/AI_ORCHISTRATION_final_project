"""Free-cell graph: adjacency, components, degree, iterative cut vertices.

The base module of `pursuit.strategy.graph` -- `cycles.py` and `territory.py`
both import this and define no adjacency of their own (QUAL-02). `bfs()` in
`strategy.pathfind` reaches adjacency through `get_legal_moves`, which builds
a probe `GameState` per cell -- fine for one distance query, far too heavy
inside alpha-beta's inner loop (D-26). This module keeps exactly one other
copy, set-membership adjacency over a precomputed cell set, pinned equal to
the engine's own `get_legal_moves` by `test_components.py`'s equivalence
test: a justified second implementation with a proof, not a silent
duplicate.

Every function is pure and takes no role: agents' own cells count as free
cells, and callers subtract whatever they want excluded (D-03). A cell
outside the given set has an empty component and degree 0 -- the cop can
legally wall a cell off, so this is an ordinary outcome, never an error
(mirrors `pathfind.UNREACHABLE`'s never-raise contract).
"""

from __future__ import annotations

from collections import deque

from pursuit.constants import Direction
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]

_DELTAS: tuple[Coord, ...] = tuple(
    direction.value for direction in Direction if direction is not Direction.STAY
)


def free_cells(state: GameState, params: GameParams) -> frozenset[Coord]:
    """In-bounds cells minus `state.barriers` -- the only function here taking
    `(GameState, GameParams)`; every other function takes the derived set, so
    03-18 pays this derivation once per search node, not once per call."""
    size = params.board_size
    return frozenset(
        (row, col)
        for row in range(size)
        for col in range(size)
        if (row, col) not in state.barriers
    )


def neighbors(cells: frozenset[Coord], cell: Coord) -> frozenset[Coord]:
    """The one adjacency implementation. Orthogonal only -- `Direction.STAY`
    is excluded so a self-loop can never corrupt `degree`/`edge_count` and,
    through them, cycle rank."""
    return frozenset(
        (cell[0] + row_delta, cell[1] + col_delta)
        for row_delta, col_delta in _DELTAS
        if (cell[0] + row_delta, cell[1] + col_delta) in cells
    )


def component_of(cells: frozenset[Coord], start: Coord) -> frozenset[Coord]:
    """Cells reachable from `start` within `cells`. Empty if `start` is not
    itself a member of `cells` -- never raises."""
    if start not in cells:
        return frozenset()
    visited = {start}
    frontier: deque[Coord] = deque([start])
    while frontier:
        current = frontier.popleft()
        for neighbor in neighbors(cells, current):
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append(neighbor)
    return frozenset(visited)


def degree(cells: frozenset[Coord], cell: Coord) -> int:
    """Number of in-set neighbours of `cell`; 0 if `cell` is not in `cells`."""
    if cell not in cells:
        return 0
    return len(neighbors(cells, cell))


def edge_count(cells: frozenset[Coord]) -> int:
    """Undirected edge count over `cells`, each edge counted once."""
    return sum(degree(cells, cell) for cell in cells) // 2


def articulation_points(cells: frozenset[Coord]) -> frozenset[Coord]:
    """Cut vertices of the (possibly disconnected) graph over `cells`.

    Iterative Hopcroft-Tarjan -- an explicit stack of
    `(node, sorted_neighbors, next_index)` frames, no recursion anywhere.
    A non-root node is a cut vertex when some child's low-link cannot reach
    back above the node's own discovery time; a root is a cut vertex iff it
    has >= 2 DFS children. Each component of `cells` is walked independently.
    """
    discovered: dict[Coord, int] = {}
    low: dict[Coord, int] = {}
    parent: dict[Coord, Coord | None] = {}
    root_child_count: dict[Coord, int] = {}
    cut_vertices: set[Coord] = set()
    clock = 0

    for root in sorted(cells):
        if root in discovered:
            continue
        parent[root] = None
        root_child_count[root] = 0
        discovered[root] = low[root] = clock
        clock += 1
        stack: list[tuple[Coord, list[Coord], int]] = [
            (root, sorted(neighbors(cells, root)), 0)
        ]

        while stack:
            node, ordered_neighbors, next_idx = stack[-1]
            if next_idx == len(ordered_neighbors):
                stack.pop()
                if not stack:
                    continue
                caller = stack[-1][0]
                low[caller] = min(low[caller], low[node])
                if caller != root and low[node] >= discovered[caller]:
                    cut_vertices.add(caller)
                continue

            stack[-1] = (node, ordered_neighbors, next_idx + 1)
            neighbor = ordered_neighbors[next_idx]
            if neighbor not in discovered:
                parent[neighbor] = node
                if node == root:
                    root_child_count[root] += 1
                discovered[neighbor] = low[neighbor] = clock
                clock += 1
                stack.append((neighbor, sorted(neighbors(cells, neighbor)), 0))
            elif neighbor != parent[node]:
                low[node] = min(low[node], discovered[neighbor])

        if root_child_count[root] >= 2:
            cut_vertices.add(root)

    return frozenset(cut_vertices)
