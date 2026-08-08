"""Action spaces for one simultaneous turn (RULES-RESOLUTION.md Sec2).

Both agents choose from the SAME pre-turn state, so both action sets are generated
from that one snapshot. Nothing here knows what the opponent picked -- that is the
whole point of the joint turn and of the Commit-Reveal protocol that enforces it.

Book Sec3.4 p.21: the thief moves one orthogonal cell or stays; the cop either moves
the same way XOR places one barrier on the cell it stands on or one of its four
orthogonal neighbours. Table 15 marks the movement set *fixed* -- a diagonal is a
technical loss (rules 13/14), so no generator here may ever emit one.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]


@dataclass(frozen=True)
class CopAction:
    """A single cop action: exactly one of move XOR barrier is set.

    Constructing one with both or neither set is a programming error, not a game
    event, so it raises rather than being silently coerced -- the sequential engine
    signalled a rejected barrier by returning the same object, and that made an
    invalid placement indistinguishable from a deliberately wasted turn.
    """

    move: Coord | None = None
    barrier: Coord | None = None

    def __post_init__(self) -> None:
        """Reject the two malformed shapes at construction time."""
        if (self.move is None) == (self.barrier is None):
            raise ValueError(
                f"CopAction is move XOR barrier; got move={self.move}, barrier={self.barrier}"
            )

    @property
    def is_barrier(self) -> bool:
        """True when this action places a barrier instead of moving."""
        return self.barrier is not None

    def destination(self, cop_cell: Coord) -> Coord:
        """Where the cop stands after this action: unchanged when placing."""
        return cop_cell if self.barrier is not None else self.move


def thief_actions(state: GameState, params: GameParams) -> list:
    """Return every legal thief destination from the pre-turn state.

    STAY is always present: an agent standing on a cell may remain there even if
    that cell was barriered underneath it. Rule 47 (trapped thief) no longer
    depends on this list being empty -- it tests the four neighbours directly --
    so STAY being unconditional is now correct rather than the bug that made
    rule 47 unreachable dead code.
    """
    return get_legal_moves(state, "thief", params)


def barrier_cells(state: GameState, params: GameParams) -> list:
    """Return every legal barrier target: the cop's own cell plus its 4 neighbours.

    The cop's own cell IS legal -- book Sec3.4 p.21 names it explicitly. The old
    engine rejected it (barrier.py case 2), which removed a real denial move: the
    cop seals the corridor cell it occupies and steps off next turn.
    """
    if state.barriers_placed >= params.barrier_quota:
        return []
    size = params.board_size
    row, col = state.cop
    candidates = [(row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
    return [
        cell
        for cell in candidates
        if 0 <= cell[0] < size and 0 <= cell[1] < size and cell not in state.barriers
    ]


def cop_actions(state: GameState, params: GameParams) -> list:
    """Return every legal cop action: moves first, then barrier placements.

    Move order is stable and deterministic so a replay reproduces the same matrix
    row ordering, and so a tie-break by index is reproducible across processes.
    """
    moves = [CopAction(move=cell) for cell in get_legal_moves(state, "cop", params)]
    return moves + [CopAction(barrier=cell) for cell in barrier_cells(state, params)]
