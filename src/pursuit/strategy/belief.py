"""BeliefMap: a probability grid over where `role` will be when our move
lands (D-48, Task 1) -- the ONE-TURN-AHEAD predictive distribution book
Sec6.4's reliability-weighted update needs, not a posterior over a
permanently hidden position.

Three invariants hold after every operation and are defended in code, not
assumed: every cell >= 0 and the grid sums to 1; a degenerate `update`
(likelihoods that explain nothing) returns the PRIOR unchanged rather than
dividing by zero; barrier cells never carry mass. The grid itself is dense
and boring -- board_size x board_size floats, nothing cleverer -- because
7x7 is 49 numbers and clarity beats a sparse representation here.

Regime A (observe_exact then predict) and Regime B (predict/update on their
own, no exact cell ever) are ONE object exercising the SAME predict/update
loop -- see 04-PLAN-OUTLINE.md Sec1's table. Nothing here asks "which regime
am I in".
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.belief_motion import ROLES, Coord, Grid, spread
from pursuit.strategy.equilibrium import sample as _sample_index


@dataclass
class BeliefMap:
    """A live, mutable posterior over `role`'s cell.

    Mutable for the same reason ScentField (scentfield.py) is: predict/
    update/observe_exact advance state in place across a live game, unlike
    a frozen GameState snapshot (D-12).
    """

    board_size: int
    role: str

    def __post_init__(self) -> None:
        """Validate `role` and seed a uniform prior -- no information yet."""
        if self.role not in ROLES:
            raise ValueError(f"BeliefMap: role must be one of {ROLES}, got {self.role!r}")
        self._grid: Grid = _uniform(self.board_size)

    def observe_exact(self, cell: Coord) -> None:
        """Collapse the posterior to a delta at `cell` -- Regime A's entry
        point, called when the opponent's revealed action resolves to a
        known pre-turn cell."""
        n = self.board_size
        row, col = cell
        if not (0 <= row < n and 0 <= col < n):
            raise ValueError(f"observe_exact: {cell} is outside the {n}x{n} board")
        self._grid = [[1.0 if (r, c) == cell else 0.0 for c in range(n)] for r in range(n)]

    def predict(self, state: GameState, params: GameParams) -> None:
        """Advance one joint turn through the legal-motion model.

        Any cell the belief still credits that has since become a barrier
        is impossible -- `role` cannot occupy a sealed cell -- so that mass
        is cleared and the remainder renormalised BEFORE spreading: ruling
        out an impossible hypothesis is itself a Bayesian update.
        """
        cleaned = _clip_barriers(self._grid, state.barriers, self.board_size)
        self._grid = _renormalize(spread(cleaned, self.role, state, params), self.board_size)

    def update(self, likelihood: Grid) -> None:
        """Multiply pointwise by `likelihood` and renormalise.

        A likelihood that is neutral (1.0) everywhere leaves the posterior
        unchanged by construction. One whose product with the prior is zero
        everywhere would divide by zero on renormalisation; instead the
        PRIOR is returned unchanged (invariant 2) -- a reading that
        explains nothing must not zero the map.
        """
        n = self.board_size
        candidate = [[self._grid[r][c] * likelihood[r][c] for c in range(n)] for r in range(n)]
        total = sum(sum(row) for row in candidate)
        if total <= 0.0:
            return
        self._grid = [[value / total for value in row] for row in candidate]

    def posterior(self) -> tuple:
        """Return an immutable snapshot of the current grid."""
        return tuple(tuple(row) for row in self._grid)

    def argmax(self) -> Coord:
        """Return the single most likely cell, ties broken by row-major scan
        order for a reproducible result (matches actions.py's own
        deterministic-ordering convention)."""
        n = self.board_size
        best_cell: Coord = (0, 0)
        best_value = self._grid[0][0]
        for row in range(n):
            for col in range(n):
                if self._grid[row][col] > best_value:
                    best_value = self._grid[row][col]
                    best_cell = (row, col)
        return best_cell

    def sample(self, rng: random.Random) -> Coord:
        """Draw one cell proportional to the posterior, using an injected
        `random.Random` -- never the module-level RNG, never `secrets`
        (reserved for nonces, Phase 6) -- so 04-11's seeded selection
        replays exactly."""
        n = self.board_size
        flat = tuple(self._grid[r][c] for r in range(n) for c in range(n))
        index = _sample_index(flat, rng.random())
        return divmod(index, n)


def _uniform(board_size: int) -> Grid:
    """A fresh board_size x board_size grid, equal mass in every cell."""
    share = 1.0 / (board_size * board_size)
    return [[share] * board_size for _ in range(board_size)]


def _clip_barriers(grid: Grid, barriers: frozenset, board_size: int) -> Grid:
    """Zero every barrier cell's mass and renormalise -- invariant 3.

    If EVERY credited cell was just barriered, `_renormalize`'s generic
    fallback would reintroduce uniform mass at those same barrier cells --
    which `spread()` would then hypothesise `role` standing on via
    get_legal_moves' unconditional STAY branch (board.py trusts D-13's
    precondition that an agent's own cell is never a barrier, so it does
    not defend against a hypothesised position that violates it). The
    fallback here stays barrier-aware instead: uniform over the cells that
    remain legal, never the barriers themselves.
    """
    clipped = [
        [0.0 if (r, c) in barriers else grid[r][c] for c in range(board_size)]
        for r in range(board_size)
    ]
    total = sum(sum(row) for row in clipped)
    if total > 0.0:
        return [[value / total for value in row] for row in clipped]
    open_count = board_size * board_size - len(barriers)
    if open_count <= 0:
        return _uniform(board_size)
    share = 1.0 / open_count
    return [
        [0.0 if (r, c) in barriers else share for c in range(board_size)]
        for r in range(board_size)
    ]


def _renormalize(grid: Grid, board_size: int) -> Grid:
    """Scale `grid` to sum to 1; an all-zero grid falls back to uniform
    rather than dividing by zero (e.g. every credited cell just became a
    barrier at once)."""
    total = sum(sum(row) for row in grid)
    if total <= 0.0:
        return _uniform(board_size)
    return [[value / total for value in row] for row in grid]
