"""phi(s): the 14-component positional feature vector, always cop-perspective.

The game is zero-sum, so ONE vector and ONE weight set serve both seats: the
thief's value is the cop's negated. That is why the learned artefact does not
double in size for two roles, and why a self-play game yields samples for both.

Every component is scaled to roughly [-1, 1] by a board constant derived from
GameParams -- never a literal (Segal Table 5, "hardcoded values: 0 in source").
Positive means good for the cop.

Why these features and not raw coordinates: a distance-only evaluation cannot see
the cop's actual win condition. A single cop cannot corner a perfect evader on an
open 7x7 grid -- the free graph has cycle rank (n-1)^2 = 36 and the thief just
runs loops. Capture requires first driving that cycle rank toward zero with
barriers, which is a structural property of the free-cell graph, not a distance.
Features 6-9 are the ones that can see it.
"""

from __future__ import annotations

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.graph.cycles import is_forest
from pursuit.strategy.graphcache import (
    cut_vertices,
    distances,
    loops,
    passable,
    passable_for_cop,
    region,
    territory,
)

#: Orthogonal neighbours of any cell -- the movement set is *fixed* by Table 15,
#: so this is a structural constant of the game, not a tunable value.
MAX_DEGREE = 4

FEATURE_COUNT = 15

FEATURE_NAMES = (
    "bias",
    "neg_distance",
    "thief_unreachable",
    "neg_thief_degree",
    "territory_diff",
    "neg_thief_region",
    "neg_cycle_rank",
    "thief_region_is_forest",
    "chokepoint_density",
    "thief_on_chokepoint",
    "barriers_remaining",
    "turns_remaining",
    "parity",
    "cop_degree",
    "thief_in_kill_range",
)


def phi(state: GameState, params: GameParams) -> tuple:
    """Return the feature vector for *state* from the cop's point of view."""
    size = params.board_size
    total = size * size
    # Cycle rank of a fully open m x n grid: edges - vertices + 1 = (m-1)(n-1).
    max_loops = (size - 1) * (size - 1)

    free = passable(state.barriers, size)
    cop_free = passable_for_cop(state.barriers, state.cop, size)
    thief_region = region(free, state.thief) if state.thief in free else frozenset()

    from_cop = distances(cop_free, state.cop)
    hops = from_cop.get(state.thief)
    unreachable = hops is None

    cop_cells, thief_cells = territory(free, state.cop, state.thief)
    cells_diff = cop_cells - thief_cells
    region_size = len(thief_region) or 1
    chokepoints = cut_vertices(thief_region) if thief_region else frozenset()
    turns_left = max(0, params.survival_threshold - state.turn)
    barriers_left = max(0, params.barrier_quota - state.barriers_placed)

    return (
        1.0,
        -1.0 if unreachable else -hops / (2 * size),
        -1.0 if unreachable else 0.0,
        -_degree(free, state.thief) / MAX_DEGREE,
        cells_diff / total,
        -len(thief_region) / total,
        -loops(thief_region) / max_loops if thief_region else 0.0,
        1.0 if thief_region and is_forest(thief_region) else 0.0,
        len(chokepoints) / region_size,
        1.0 if state.thief in chokepoints else 0.0,
        barriers_left / params.barrier_quota,
        turns_left / params.survival_threshold,
        _parity(state),
        _degree(cop_free, state.cop) / MAX_DEGREE,
        _kill_range(state, barriers_left),
    )


def _kill_range(state: GameState, barriers_left: int) -> float:
    """1.0 when the thief stands where the cop can seal it next turn.

    This is the single most important tactical fact in the game and it is NOT
    visible one ply ahead without being named. Rule 46 captures the thief when a
    barrier lands on the cell it occupied AT THAT MOMENT -- its PRE-move cell --
    and the cop's legal barrier targets are its own cell plus its four
    orthogonal neighbours. So a thief at Manhattan distance 1 from a cop with
    quota remaining is captured next turn no matter where it runs: there is no
    escaping move, because the seal lands on the cell it is leaving.

    A depth-1 search cannot discover that, because the loss is two plies away.
    Naming it as a feature gives a one-ply searcher the two-ply fact, which is
    far cheaper than the depth-2 search that would otherwise be required.
    """
    if barriers_left <= 0:
        return 0.0
    gap = abs(state.cop[0] - state.thief[0]) + abs(state.cop[1] - state.thief[1])
    return 1.0 if gap == 1 else 0.0


def _degree(cells: frozenset, cell: tuple) -> int:
    """Number of passable orthogonal neighbours of *cell*."""
    row, col = cell
    neighbours = ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
    return sum(1 for neighbour in neighbours if neighbour in cells)


def _parity(state: GameState) -> float:
    """Bipartite tempo invariant of the grid.

    A grid graph is bipartite, so the parity of the cop-thief coordinate sum is
    conserved by any pair of ordinary moves. STAY is the only action that flips
    it, which makes parity the tempo signal in a pure pursuit -- a cop on the
    wrong parity can shadow the thief forever without ever landing on it.
    """
    total = state.cop[0] + state.cop[1] + state.thief[0] + state.thief[1]
    return 1.0 if total % 2 == 0 else 0.0


def value(weights: tuple, state: GameState, params: GameParams) -> float:
    """Linear evaluation w . phi(s), from the cop's point of view.

    The thief's evaluation is the negation; no separate weight vector exists.
    """
    vector = phi(state, params)
    return sum(weight * component for weight, component in zip(weights, vector, strict=True))
