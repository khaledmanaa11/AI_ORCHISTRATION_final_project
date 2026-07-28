"""Capture detection and turn-end evaluation for the pursuit engine.

Turn-order contract (D-12):
  Step 1: Cop acts (move or place barrier).
  Step 2: detect_capture() is called — BEFORE the thief moves.
          Checks BASE-03 (coordinate overlap), BASE-04 (barrier on thief),
          BASE-05 (no legal moves for thief at start of its turn).
  Step 3: If detect_capture returns None, the thief moves.
  Step 4: evaluate_turn_end() is called — AFTER the thief moves and the
          turn counter has been incremented by the orchestrator.

Phase 1 constraint (D-15): only CAPTURE and SURVIVAL are produced here.
TIE and TECHNICAL_LOSS are unreachable in Phase 1.

No-legal-move note (D-13): STAY (thief's current position) is always legal
unless the thief's own cell is a barrier (which is BASE-04). Therefore
BASE-05 only triggers independently when get_legal_moves semantics change.
The check is included for correctness completeness and future-proofing.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]


def detect_capture(state: GameState, params: GameParams) -> Outcome | None:
    """Detect whether the thief is captured after the cop has acted.

    Called AFTER the cop acts and BEFORE the thief moves (D-12 step 2+3).
    Checks three capture conditions in order; stops at the first match.

    Parameters
    ----------
    state:
        Current immutable game snapshot (post-cop-action).
    params:
        Game configuration (provides board_size for legal-move generation).

    Returns
    -------
    Outcome.CAPTURE
        If any capture condition is satisfied (BASE-03, BASE-04, or BASE-05).
    None
        No capture condition active; thief may move.
    """
    # BASE-03: Cop moved onto the thief's cell (coordinate overlap).
    if state.cop == state.thief:
        return Outcome.CAPTURE

    # BASE-04: Cop placed a barrier on the thief's cell.
    # place_barrier accepted this placement (01-02 boundary, D-10);
    # the capture consequence is this function's sole responsibility.
    if state.thief in state.barriers:
        return Outcome.CAPTURE

    # BASE-05: Thief has no legal moves at the start of its turn (D-13).
    # STAY (thief's own cell) is always legal unless caught by BASE-04 above,
    # so this check only fires if get_legal_moves semantics evolve.
    if not get_legal_moves(state, "thief", params):
        return Outcome.CAPTURE

    return None


def evaluate_turn_end(state: GameState, params: GameParams) -> Outcome | None:
    """Evaluate whether the game has ended after the thief moves.

    Called AFTER the thief moves and the turn counter is incremented by
    the orchestrator (D-12 step 4).

    Parameters
    ----------
    state:
        Current immutable game snapshot (post-thief-move, incremented turn).
    params:
        Game configuration (provides survival_threshold; no hardcoded value).

    Returns
    -------
    Outcome.SURVIVAL
        If state.turn >= params.survival_threshold (BASE-06, D-16).
    None
        Threshold not yet reached; game continues.
    """
    if state.turn >= params.survival_threshold:
        return Outcome.SURVIVAL

    return None
