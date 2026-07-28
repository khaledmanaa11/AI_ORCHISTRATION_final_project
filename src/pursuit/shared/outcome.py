"""Maps Outcome enum values to (cop_score, thief_score) tuples.

All score values are read exclusively from GameParams fields loaded at
startup from game_params.json (D-14).  This module contains zero numeric
literals — every score comes from a params.score_* field.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.shared.config import GameParams


def score_outcome(outcome: Outcome, params: GameParams) -> tuple[int, int]:
    """Return (cop_score, thief_score) for a completed game outcome.

    All score values come exclusively from params.score_* fields; this
    function contains no numeric literals.

    Parameters
    ----------
    outcome:
        The game outcome to score (an Outcome enum member).
    params:
        Game configuration carrying all score_* fields.

    Returns
    -------
    tuple[int, int]
        (cop_score, thief_score) pair for the given outcome.

    Raises
    ------
    ValueError
        If *outcome* is not a recognised Outcome member.
    """
    if outcome is Outcome.CAPTURE:
        return (params.score_capture_cop, params.score_capture_thief)
    elif outcome is Outcome.SURVIVAL:
        return (params.score_survival_cop, params.score_survival_thief)
    elif outcome is Outcome.TIE:
        return (params.score_tie, params.score_tie)
    elif outcome is Outcome.TECHNICAL_LOSS:
        return (params.score_technical_loss_cop, params.score_technical_loss_thief)
    else:
        raise ValueError(f"Unrecognised outcome: {outcome!r}")
