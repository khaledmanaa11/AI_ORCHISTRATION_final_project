"""ScentField: one peer's own trail and its local reconstruction of the
opponent's (D-49).

Two independent dict-backed grids on ONE object -- `own` and `opponent`.
Both describe THIS peer's own beliefs about a single process's local state;
nothing here crosses the process boundary (rule 2, CLAUDE.md: never share
runtime state between the cop and the thief). `board_size` comes from
GameParams via the caller -- this module reads no config itself, matching
emission()/decay()'s own board_size-as-int signature.

Which regime feeds `opponent` -- an exact revealed cell (Regime A) or an
emission weighted by the belief posterior (Regime B) -- is the belief map's
decision, not this module's: `emit_opponent` takes one cell at a time with an
optional weight, so a caller running Regime B simply calls it once per
(cell, probability) pair in its posterior. Keeping that decision out of here
is what lets the belief-map module own it without a circular import.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pursuit.shared.scent_config import ScentModel
from pursuit.strategy.scent import Coord, decay, emission

_GRID_NAMES = ("own", "opponent")


@dataclass
class ScentField:
    """Two independent per-peer scent grids: own trail and reconstructed
    opponent trail. Mutable by design -- `emit_*`/`advance` update state in
    place across a live game, unlike the frozen GameState snapshot (D-12)."""

    model: ScentModel
    board_size: int
    own: dict[Coord, float] = field(default_factory=dict)
    opponent: dict[Coord, float] = field(default_factory=dict)

    def emit_own(self, cell: Coord) -> None:
        """Add one full-strength emission centred on cell to the own-trail grid."""
        self.own = _merged(self.own, emission(self.model, cell, self.board_size))

    def emit_opponent(self, cell: Coord, weight: float = 1.0) -> None:
        """Add one (optionally weighted) emission to the opponent-trail grid.

        `weight` defaults to 1.0 for Regime A (an exactly revealed cell).
        Regime B calls this once per (cell, probability) pair in the belief
        posterior, so the accumulated opponent grid becomes a probability-
        weighted composite rather than a single full-strength deposit.
        """
        contribution = {
            c: v * weight for c, v in emission(self.model, cell, self.board_size).items()
        }
        self.opponent = _merged(self.opponent, contribution)

    def advance(self) -> None:
        """Apply one joint-turn decay to BOTH grids.

        RULES-RESOLUTION.md Sec4 fixes one joint turn = one increment: call
        this exactly once per joint turn, after both actions are known --
        never once per half-turn.
        """
        self.own = decay(self.own, self.model)
        self.opponent = decay(self.opponent, self.model)

    def strength(self, grid: str, cell: Coord) -> float:
        """Return the current strength at cell in the named grid ('own'/'opponent')."""
        return self._grid(grid).get(cell, 0.0)

    def freshest(self, grid: str) -> Coord | None:
        """Return the strongest cell in the named grid, or None if it is empty."""
        values = self._grid(grid)
        return max(values, key=values.get) if values else None

    def snapshot(self) -> ScentField:
        """Return a copy decoupled from this field: mutating either one (the
        original or the copy) never affects the other. For the belief map
        and, later, the replay log."""
        return ScentField(
            model=self.model,
            board_size=self.board_size,
            own=dict(self.own),
            opponent=dict(self.opponent),
        )

    def _grid(self, name: str) -> dict[Coord, float]:
        if name not in _GRID_NAMES:
            raise ValueError(f"ScentField: unknown grid {name!r}, expected 'own' or 'opponent'")
        return self.own if name == "own" else self.opponent


def _merged(base: dict[Coord, float], delta: dict[Coord, float]) -> dict[Coord, float]:
    """Return base + delta, cell-wise, as a NEW dict -- neither input is mutated."""
    merged = dict(base)
    for cell, value in delta.items():
        merged[cell] = merged.get(cell, 0.0) + value
    return merged
