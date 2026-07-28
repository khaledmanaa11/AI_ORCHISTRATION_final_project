"""Pure barrier-placement primitive for the pursuit engine (BASE-02).

place_barrier validates a proposed barrier cell and, if accepted, returns a new
frozen GameState with that cell added to barriers and barriers_placed incremented.
All four rejection cases return the original state object unchanged.

Ownership boundary with detect_capture (plan 01-03):
    Placing a barrier on the thief's current cell IS a valid placement here —
    barriers_placed is incremented and the new state is returned.  Whether that
    constitutes a capture (rule 46) is detect_capture's responsibility, not ours.
    barrier.py has no knowledge of capture semantics.

D-09 note:
    This function is a pure placement primitive.  The "one barrier per cop turn"
    constraint is enforced by the turn orchestrator (plan 01-03), which calls
    place_barrier at most once per cop turn.  barrier.py has no knowledge of turns.
"""

import dataclasses

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]


def _in_bounds(cell: Coord, board_size: int) -> bool:
    """Return True if cell is within the square board of given edge length."""
    row, col = cell
    return row in range(board_size) and col in range(board_size)


def place_barrier(state: GameState, cell: Coord, params: GameParams) -> GameState:
    """Attempt to place a barrier at *cell*; return new or original state.

    Validation order (validate FIRST, mutate SECOND — prevents spurious quota
    consumption on invalid placements):

    1. Out-of-bounds  → reject (no quota cost)
    2. Cop's own cell → reject (no quota cost)
    3. Already barriered → reject (no quota cost)
    4. Over quota    → reject
    5. Otherwise     → accept; return new frozen GameState

    Args:
        state:  Current game snapshot (frozen; never mutated).
        cell:   Proposed (row, col) placement target from the cop's strategy layer.
        params: Validated game parameters; quota read from params.barrier_quota.

    Returns:
        A new frozen GameState if the placement is accepted, or *state* unchanged
        if the placement is rejected for any of the four reasons above.

    Note:
        Placing on the thief's current cell is accepted (D-10); the capture
        consequence (rule 46 / BASE-04) is handled by detect_capture in plan 01-03.
    """
    # 1. Out-of-bounds check — no quota cost on rejection.
    if not _in_bounds(cell, params.board_size):
        return state

    # 2. Cop's own cell — no quota cost on rejection.
    if cell == state.cop:
        return state

    # 3. Already-barriered cell — no quota cost on rejection.
    if cell in state.barriers:
        return state

    # 4. Quota exhausted — reject placement.
    if state.barriers_placed >= params.barrier_quota:
        return state

    # 5. Accepted — produce a new immutable snapshot.
    new_barriers = state.barriers | frozenset({cell})
    added = len(new_barriers) - len(state.barriers)
    return dataclasses.replace(
        state,
        barriers=new_barriers,
        barriers_placed=state.barriers_placed + added,
    )
