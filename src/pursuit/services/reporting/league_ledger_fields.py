"""The league ledger's key names, its two FIXED bounds, and the derivation
`league_ledger.py` reads a games-played count out of.

Split from that module at the 150-code-line gate (Segal Table 5) on the
`result_artifact_fields.py` precedent and along the same seam: the SCHEMA plus
the arithmetic here, read/append/refuse there. `league_ledger.py` re-exports
every public name, so callers keep ONE import path.

WHAT THIS FILE MUST NOT DO, AND THE REASON IS NOT STYLE. It must not choose a
games-played VALUE. `docs/RULES.md:79` (rule 38) makes a false games-played
declaration an ABSOLUTE disqualification; 07-00 fixed the counter MECHANISM and
recorded that the two shipped counters read 1922 and 1915 for two agents that
have only ever played each other, because one `pytest` run used to advance both
by +14 for zero games. Which of those readings is "a game played" is OQ8-2, a
human's decision from `docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md`. So
`games_played_reading` returns BOTH candidate counts and an explicit UNSET
marker for the declared figure -- it never collapses them into one number, and
the marker is what a declaration carries until the human fills it in.
"""

from __future__ import annotations

from pursuit.shared.absent import stated_absent

__all__ = (
    "LEAGUE_LEDGER_UNSET",
    "LEDGER_FILENAME",
    "LEDGER_VERSION",
    "MAX_GAMES_PER_TEAM",
    "MINIMUM_GAMES",
    "LeagueGameField",
    "LedgerField",
    "count_reading",
    "empty_ledger",
    "entries",
    "games_played_reading",
    "scored_opponents",
)

#: Beside this role's run output, never under the shipped `config/` tree --
#: `tests/_shipped_config_guard.py` makes that structural, and the same reason
#: `end_of_game_chain.QUOTA_FILENAME` is not an artifact applies here.
LEDGER_FILENAME = "league_ledger.json"

LEDGER_VERSION = "1.00"

#: docs/PARAMETERS.md:84, Table 18 row 5 -- "[max games per team]", 10, FIXED.
#: FIXED means any deviation disqualifies (CLAUDE.md prohibition 1), so this is
#: a refusal and not a warning. It is checked against EVERY recorded league
#: game, warm-ups included: the row bounds "max games any one team may play"
#: and says nothing about scoring, so counting only scored games would be the
#: looser reading of a fixed bound.
MAX_GAMES_PER_TEAM = 10

#: docs/PARAMETERS.md:82, Table 18 row 3 -- "[minimum games]", 2, FIXED. Not
#: enforced as a refusal (a ledger is legitimately short mid-league); carried
#: so `league_ready` can answer whether the grade floor is met yet.
MINIMUM_GAMES = 2


class LedgerField:
    """Top-level key names -- structural, avoids magic strings."""

    VERSION = "version"
    ENTRIES = "entries"


class LeagueGameField:
    """One recorded league game.

    `scored` is the rule-52 discriminator: "against each opponent there is one
    scoring game only -- no rematches for points", while unscored warm-ups are
    permitted and encouraged. Both kinds are recorded, because both were
    played; only the scored one is bounded per opponent.
    """

    OPPONENT = "opponent"
    GAME_ID = "game_id"
    SCORED = "scored"
    OUTCOME = "outcome"
    COMMIT_HASH = "commit_hash"
    RECORDED_AT = "recorded_at"


#: The declared games-played figure, unset for exactly the reason above.
_UNSET_DETAIL = (
    "deliberately unset. The ledger below DERIVES two candidate counts "
    "(`scored` and `all_recorded`), but which reading rule 37/38 asks a team to "
    "declare is OQ8-2 -- a human's decision from docs/phases/phase-7/"
    "GAMES-PLAYED-RECONSTRUCTION.md, taken at 08-14. docs/RULES.md:79 makes a "
    "false games-played declaration an ABSOLUTE disqualification, so nothing "
    "automated may choose between them"
)
LEAGUE_LEDGER_UNSET = stated_absent(_UNSET_DETAIL)


def empty_ledger() -> dict:
    """A ledger with no games in it.

    IT STARTS EMPTY AND IS NEVER SEEDED FROM `games_played.json`. Those two
    files read 1922 and 1915 and 07-00's own docstring records why: a `pytest`
    run, not a game. Seeding from them would import the exact defect this
    ledger exists to replace (D-80).
    """
    return {LedgerField.VERSION: LEDGER_VERSION, LedgerField.ENTRIES: []}


def entries(ledger: dict) -> list:
    """This ledger's games, or `[]` for a shape that carries none."""
    recorded = ledger.get(LedgerField.ENTRIES)
    return list(recorded) if isinstance(recorded, list) else []


def scored_opponents(ledger: dict) -> tuple[str, ...]:
    """Every opponent already holding a SCORED game, in insertion order."""
    seen: dict[str, None] = {}
    for entry in entries(ledger):
        if entry.get(LeagueGameField.SCORED) is True:
            seen.setdefault(str(entry.get(LeagueGameField.OPPONENT)), None)
    return tuple(seen)


def count_reading(ledger: dict, *, scored_only: bool) -> int:
    """One of the two candidate counts. `scored_only` names which."""
    recorded = entries(ledger)
    if not scored_only:
        return len(recorded)
    return sum(1 for entry in recorded if entry.get(LeagueGameField.SCORED) is True)


def games_played_reading(ledger: dict) -> dict:
    """BOTH candidate counts, the distinct-opponent count rule 49/SUB-07 asks
    about, and the UNSET marker for the declared figure. Never one number."""
    return {
        "scored": count_reading(ledger, scored_only=True),
        "all_recorded": count_reading(ledger, scored_only=False),
        "distinct_scored_opponents": len(scored_opponents(ledger)),
        "declared": dict(LEAGUE_LEDGER_UNSET),
    }
