"""The per-opponent league ledger (D-80): the durable record of which teams
this agent has played, which of those games were SCORED, and the two candidate
games-played counts derived from it.

THE SCHEMA and the arithmetic are `league_ledger_fields.py`, re-exported here.

WHY A SECOND COUNTER EXISTS AT ALL, when the shipped per-role counter file
`games_played.json` already holds a number. Because that number is not
evidence of anything.
07-00 measured one `uv run pytest tests/` advancing both files by +14 for zero
games, and the two shipped counters still disagree by seven for two agents that
have only ever played each other. Rule 37 makes the counter's value part of
every Step-0 declaration and rule 38 (`docs/RULES.md:79`) makes declaring it
falsely an ABSOLUTE disqualification, so what a declaration needs is a count
with a per-game AUDIT TRAIL behind it -- an opponent, a game_id, a commit hash
and a timestamp per row -- not an integer whose history is gone.

THE LEDGER STARTS EMPTY AND IS NEVER SEEDED FROM THAT FILE. Seeding is the
tempting shortcut and it imports the exact defect (D-80). Only a completed
league game appends a row.

THE TWO BOOK REFUSALS -- rule 52's one-scoring-game-per-opponent and Table 18
row 5's fixed max of ten -- live in `league_ledger_bounds.py` with their
citations, and are applied by `record_league_game` before it writes.

NOTHING HERE DECLARES A NUMBER. `games_played_reading` returns both candidate
counts and an UNSET marker for the declared figure; `declared_count_matches` is
the counter-control a human's chosen figure is checked against at 08-14. An
inflated claim fails it, which is the point.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pursuit.services.reporting.league_ledger_bounds import (
    LedgerRefusalError,
    league_ready,
    refuse_if_bounded,
)
from pursuit.services.reporting.league_ledger_fields import (
    LEAGUE_LEDGER_UNSET,
    LEDGER_FILENAME,
    LEDGER_VERSION,
    MAX_GAMES_PER_TEAM,
    MINIMUM_GAMES,
    LeagueGameField,
    LedgerField,
    count_reading,
    empty_ledger,
    entries,
    games_played_reading,
    scored_opponents,
)
from pursuit.shared.durable_write import durable_write_json, load_json_with_fallback

__all__ = (
    "LEAGUE_LEDGER_UNSET",
    "LEDGER_FILENAME",
    "LEDGER_VERSION",
    "MAX_GAMES_PER_TEAM",
    "MINIMUM_GAMES",
    "LeagueGameField",
    "LedgerField",
    "LedgerRefusalError",
    "count_reading",
    "declared_count_matches",
    "empty_ledger",
    "entries",
    "games_played_reading",
    "league_ready",
    "ledger_path",
    "read_ledger",
    "record_league_game",
    "scored_opponents",
)

_WRITE_RETRIES = 3
_WRITE_BACKOFF_SECONDS = 0.1


def ledger_path(directory: Path | str) -> Path:
    """THE ledger file for one role. One definition, so a reader and a writer
    cannot drift onto two different files (the `counter_path` precedent)."""
    return Path(directory) / LEDGER_FILENAME


def read_ledger(directory: Path | str) -> dict:
    """This role's ledger, or an empty one when no game has been recorded.

    An unreadable file is NOT silently replaced with an empty ledger: that
    would turn a corrupt audit trail into a clean-looking zero, which is the
    rule-38 failure mode. It raises.
    """
    path = ledger_path(directory)
    if not path.exists():
        return empty_ledger()
    data = load_json_with_fallback(path)
    if not isinstance(data, dict) or not isinstance(data.get(LedgerField.ENTRIES), list):
        raise ValueError(f"league ledger is malformed and was not replaced: {path}")
    return data


def record_league_game(
    directory: Path | str,
    *,
    opponent: str,
    game_id: str,
    scored: bool,
    outcome: str,
    commit_hash: str,
    now: str | None = None,
) -> dict:
    """Append one COMPLETED league game and durably rewrite the ledger.

    `scored` is the caller's honest statement about what the game was, and it
    is REQUIRED -- defaulting it either way would let rule 52's bound be
    dodged by omission. `commit_hash` is the one the game actually ran under
    (rule 53, PARAMETERS mandatory rule 5); it is reused, never re-derived.
    """
    for name, value in (("opponent", opponent), ("game_id", game_id), ("outcome", outcome)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
    if not isinstance(scored, bool):
        raise TypeError("scored must be an explicit bool")
    ledger = read_ledger(directory)
    refuse_if_bounded(ledger, opponent=opponent, scored=scored)
    ledger[LedgerField.VERSION] = LEDGER_VERSION
    ledger[LedgerField.ENTRIES] = [
        *entries(ledger),
        {
            LeagueGameField.OPPONENT: opponent,
            LeagueGameField.GAME_ID: game_id,
            LeagueGameField.SCORED: scored,
            LeagueGameField.OUTCOME: outcome,
            LeagueGameField.COMMIT_HASH: commit_hash,
            LeagueGameField.RECORDED_AT: now or datetime.now(timezone.utc).isoformat(),
        },
    ]
    durable_write_json(
        ledger_path(directory), ledger, retries=_WRITE_RETRIES, backoff=_WRITE_BACKOFF_SECONDS,
    )
    return ledger


def declared_count_matches(ledger: dict, declared: object, *, scored_only: bool) -> bool:
    """THE counter-control for rule 38: does a claimed figure match the ledger?

    `scored_only` names WHICH reading the claim is being checked against, and
    has no default -- the two readings are the open question (OQ8-2), so a
    check that silently picked one would answer it by accident. A non-integer
    or a bool is False rather than an error: this is a verdict function, and a
    malformed claim is a failed claim.
    """
    if isinstance(declared, bool) or not isinstance(declared, int):
        return False
    return declared == count_reading(ledger, scored_only=scored_only)
