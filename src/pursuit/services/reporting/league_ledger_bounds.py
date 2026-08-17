"""What the BOOK forbids a league ledger to record, and the grade floor it
asks about.

Split out of `league_ledger.py` at the 150-code-line gate (Segal Table 5 -- the
combined module measured 162) along the seam that module's own docstring
already named: "TWO REFUSALS, BOTH FROM THE BOOK" were one subject and
read/append/derive were another. `league_ledger.py` re-exports every public
name below, so callers keep ONE import path (the `end_of_game_chain.py`
precedent). Split, never compressed: no body or docstring was shortened.

RULE 52 -- `docs/PARAMETERS.md:86`, `docs/RULES.md:101`. "Against each opponent
there is ONE SCORING GAME ONLY -- no rematches for points; unscored warm-up
games are permitted." So the refusal is scoped to `scored=True`, and a warm-up
against an already-scored opponent must still be recordable. A refusal that
also blocked the warm-up would be over-broad, not safe: the warm-up happened,
and a ledger that will not record a game that happened is not an audit trail.

TABLE 18 ROW 5 -- `docs/PARAMETERS.md:84`, "[max games per team]" = 10, status
**fixed**. CLAUDE.md's first prohibition makes any deviation from a fixed value
a disqualification, so this is a refusal rather than a warning. It counts EVERY
recorded game, warm-ups included: the row bounds "max games any one team may
play" and says nothing about scoring, and counting only scored games would be
the looser reading of a bound the book fixed.

TABLE 18 ROW 3 -- "[minimum games]" = 2, **fixed**, the floor for a project
grade. Reported by `league_ready`, never enforced: a mid-league ledger is
legitimately short, and refusing to record the FIRST game because it is not yet
the second would be absurd.
"""

from __future__ import annotations

from pursuit.services.reporting.league_ledger_fields import (
    MAX_GAMES_PER_TEAM,
    MINIMUM_GAMES,
    count_reading,
    scored_opponents,
)

__all__ = ("LedgerRefusalError", "league_ready", "refuse_if_bounded")


class LedgerRefusalError(ValueError):
    """A league game the book does not permit this team to record.

    A distinct TYPE, not a bare `ValueError`: rule 52 and Table 18 row 5 are
    refusals a league-day operator must be able to catch and read, and a caller
    that confused one with a malformed-argument error would retry it.
    """


def refuse_if_bounded(ledger: dict, *, opponent: str, scored: bool) -> None:
    """Both book refusals, checked BEFORE anything is written.

    Before, so a refused game leaves the ledger byte-identical -- a partially
    applied refusal would corrupt the very record it protects.
    """
    played = count_reading(ledger, scored_only=False)
    if played >= MAX_GAMES_PER_TEAM:
        raise LedgerRefusalError(
            f"{played} league games already recorded and docs/PARAMETERS.md:84 Table 18 "
            f"row 5 fixes max games per team at {MAX_GAMES_PER_TEAM}"
        )
    if scored and opponent in scored_opponents(ledger):
        raise LedgerRefusalError(
            f"a scoring game against {opponent!r} is already on the ledger; rule 52 "
            "(docs/PARAMETERS.md:86) allows one scoring game per opponent -- record a "
            "warm-up with scored=False instead"
        )


def league_ready(ledger: dict) -> bool:
    """Does the ledger meet Table 18 row 3's floor of two scored games against
    DIFFERENT opponents (SUB-07)? Rule 52 makes "two scored games" and "two
    opponents" the same requirement, so this counts opponents, not rows."""
    return len(scored_opponents(ledger)) >= MINIMUM_GAMES
