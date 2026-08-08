"""Pure board functions: legal-move generation (D-08, D-13).

Stateless and side-effect-free — only computes new values from its inputs.
No global state, no I/O. The former `apply_move` state-transition helper is
gone: it validated nothing (a bare `dataclasses.replace`), so a thief could
be placed on a barrier. `pursuit.sdk.resolve.resolve_turn` is now the sole
place a GameState is advanced, and it validates both actions before doing so
(docs/phases/phase-3/RULES-RESOLUTION.md).

Move convention (orthogonal-only, Table 15):
  - Four cardinal steps (NORTH/SOUTH/EAST/WEST) plus STAY in place.
  - Diagonal moves are never generated.
  - Out-of-bounds and barriered cells are excluded from the result.
  - STAY (current position) is always included (D-13: the agent's own cell
    is never a barrier in a valid game state).
"""

from pursuit.constants import Direction
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

# Local type alias for clarity.
Coord = tuple[int, int]


def get_legal_moves(state: GameState, agent: str, params: GameParams) -> list:
    """Return all legal destination cells for *agent* in the current state.

    Parameters
    ----------
    state:
        Current immutable game snapshot.
    agent:
        Either ``"cop"`` or ``"thief"``.
    params:
        Game configuration (provides board_size; no hardcoded grid size).

    Returns
    -------
    list[Coord]
        Unordered list of legal (row, col) destinations.
        Always contains at least the current position (STAY).
    """
    pos: Coord = state.cop if agent == "cop" else state.thief
    size: int = params.board_size

    result: list[Coord] = []
    for direction in Direction:
        dr, dc = direction.value
        candidate: Coord = (pos[0] + dr, pos[1] + dc)
        # STAY is pos itself; always include it (D-13 — agent's own cell is valid).
        if candidate == pos:
            result.append(candidate)
            continue
        # Exclude out-of-bounds cells.
        if not (0 <= candidate[0] < size and 0 <= candidate[1] < size):
            continue
        # Exclude barriered cells (D-08).
        if candidate in state.barriers:
            continue
        result.append(candidate)

    return result
