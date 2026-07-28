"""Immutable game-state snapshot for the pursuit engine (D-12).

GameState is a frozen dataclass — constructing a new state for every turn
guarantees no shared mutable state can leak between the cop and thief processes
(project rule 2). Use dataclasses.replace(...) to derive successor states.
"""

from dataclasses import dataclass

# Type alias used by both state and board modules.
Coord = tuple[int, int]


@dataclass(frozen=True)
class GameState:
    """Snapshot of the full board state at a single point in time.

    Fields
    ------
    cop : Coord
        Current (row, col) position of the cop agent.
    thief : Coord
        Current (row, col) position of the thief agent.
    barriers : frozenset[Coord]
        Set of cells that have been barriered; immutable per snapshot.
    barriers_placed : int
        Running count of barriers placed by the cop this game; used to enforce
        the barrier quota without mutating this snapshot.
    turn : int
        Zero-based turn counter.  Incremented by the orchestrator (Phase 2),
        not by board.py pure functions.
    """

    cop: Coord
    thief: Coord
    barriers: frozenset  # frozenset[Coord]
    barriers_placed: int
    turn: int


def increment_turn(state: "GameState") -> "GameState":
    """Return a new GameState with the turn counter advanced by one step."""
    import dataclasses  # noqa: PLC0415 — local import avoids circular dep risk

    return dataclasses.replace(state, turn=state.turn + 1)
