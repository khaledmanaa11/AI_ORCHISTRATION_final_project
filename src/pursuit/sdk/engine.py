"""SDK facade for the pursuit game engine (QUAL-01).

This module is the sole public entry point for callers outside src/pursuit/sdk.
It wraps shared/board and shared/outcome plus the joint-turn resolver in
sdk/resolve.py, sdk/actions.py and sdk/terminal.py -- no business logic lives
here, this is wiring only.

Joint turn (docs/phases/phase-3/RULES-RESOLUTION.md -- supersedes D-12's
cop-then-thief turn order): both agents choose their action from the SAME
pre-turn GameState, and `resolve_turn` applies both at once, advancing the
turn counter by exactly one per joint turn. See RULES-RESOLUTION.md Sec3 for
the six terminal predicates, in evaluation order, and Sec5 for how the two
negotiated predicates are agreed without breaking the config-digest handshake.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.sdk.actions import cop_actions, thief_actions  # noqa: F401
from pursuit.sdk.resolve import make_state, resolve_turn  # noqa: F401
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.outcome import score_outcome
from pursuit.shared.state import GameState


def legal_moves(
    state: GameState, agent: str, params: GameParams
) -> list[tuple[int, int]]:
    """Return legal moves for agent. Delegates to get_legal_moves."""
    return get_legal_moves(state, agent, params)


def score(outcome: Outcome, params: GameParams) -> tuple[int, int]:
    """Return (cop_score, thief_score) for an outcome. Delegates to score_outcome."""
    return score_outcome(outcome, params)
