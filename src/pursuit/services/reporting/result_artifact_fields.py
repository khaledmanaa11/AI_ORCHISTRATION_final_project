"""`result_<game_id>.json`'s key names, its two honest-absence markers, the
series accumulator, and what the seal covers.

Split out of `artifact_result.py` at the 150-code-line gate (Segal Table 5) --
the `log_artifact_fields.py` / `artifact_declaration_fields.py` precedent, and
along the same seam: the SCHEMA plus the arithmetic rule 54 asks for are one
subject; read/build/write are another. `artifact_result.py` re-exports every
public name below, so callers keep ONE import path.

THE TOKEN KEY NAMES MIRROR `TokenBudget.report()` (`services/llm/budget.py`),
which writes them as an inline dict literal. They are named here for the same
reason `log_join.py` names `LedgerField`'s keys: this module has to SUM them,
and a summer that spells a key differently from its writer reports zero
forever without ever failing.

TWO ABSENCES ARE MARKED, NOT ZEROED. `step0_collect._collect_gpu` sets the
house rule -- an honest `{"present": False, "detail": ...}` rather than a
fabricated reading -- and `turn_language.py` repeats it for the belief
snapshot ("an honest 'not run', never fabricated"). A zero presented as a
measurement is a rule-38-class misstatement, so `ctx.language is None` and the
deliberately unset games-played value each get a marker that says so.

08-04: the marker's SHAPE moved to `shared/absent.py` when a third caller
needed it (rule 49's repo links). The two markers below are rebuilt from
`stated_absent` and their dict values are unchanged, byte for byte -- which is
what `tests/unit/test_absent_marker.py` asserts rather than assumes.
"""

from __future__ import annotations

from pursuit.services.reporting.artifacts import ArtifactField
from pursuit.shared.absent import ABSENT_DETAIL_KEY, ABSENT_PRESENT_KEY, stated_absent

__all__ = (
    "GAMES_PLAYED_UNSET",
    "SEALED_FIELDS",
    "TOKENS_ABSENT",
    "ResultArtifactField",
    "SubGameField",
    "TokensField",
    "accumulate_series",
    "empty_series",
    "game_tokens",
    "sealed_body",
)


class ResultArtifactField:
    """Top-level key names -- structural, avoids magic strings."""

    ROLE = "role"
    COMMIT_HASH = "commit_hash"
    GAMES_PLAYED_DECLARED = "games_played_declared"
    SUB_GAMES = "sub_games"
    SERIES_TOKENS = "series_tokens"
    RESULT_DIGEST = "result_digest"


class SubGameField:
    """One sub-game's entry. `commit_hash` is carried PER SUB-GAME because
    docs/PARAMETERS.md:152-153 permits code to change between games and
    requires each game's report to name the commit it ran on; the top-level
    `commit_hash` is the newest sub-game's, so a reader who wants only "which
    commit sent this file" does not have to walk the list."""

    AGREEMENT = "agreement"
    COMMIT_HASH = "commit_hash"
    LOG_ARTIFACT = "log_artifact"
    TOKENS = "tokens"


class TokensField:
    """`TokenBudget.report()`'s own key names, plus the two this module
    derives: `total_tokens` (rule 54's "total tokens consumed") and
    `games_measured` (how many sub-games the series total actually rests on)."""

    CALLS = "calls"
    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"
    TOTAL_TOKENS = "total_tokens"
    GAMES_MEASURED = "games_measured"
    PRESENT = ABSENT_PRESENT_KEY
    DETAIL = ABSENT_DETAIL_KEY


TOKENS_ABSENT = stated_absent(
    "the language layer was off for this game (agent_context.language is None), "
    "so no token spend exists to report -- an honest absence, never a zero "
    "presented as a measurement"
)

GAMES_PLAYED_UNSET = stated_absent(
    "deliberately unset. 07-00 fixed the rule-37/38 counter MECHANISM and left "
    "its VALUE to a human decision (docs/phases/phase-7/"
    "GAMES-PLAYED-RECONSTRUCTION.md); rule 38 makes a false games-played "
    "declaration an ABSOLUTE disqualification, so nothing here may choose it. "
    "This game's declared figure is in declaration_<game_id>.json"
)

_ACCUMULATED = (
    TokensField.CALLS,
    TokensField.INPUT_TOKENS,
    TokensField.OUTPUT_TOKENS,
    TokensField.TOTAL_TOKENS,
)

# The seal covers the header too, which is STRICTER than `log_artifact_fields.
# SEALED_FIELDS`. Deliberate: this is the emailed report, and its `game_id` is
# what files it against a game (rules 32/35). A header outside the seal could
# be swapped to re-file a real report against a different game without
# breaking the digest.
SEALED_FIELDS = (
    ArtifactField.GAME_UID,
    ArtifactField.GAME_ID,
    ResultArtifactField.ROLE,
    ResultArtifactField.COMMIT_HASH,
    ResultArtifactField.GAMES_PLAYED_DECLARED,
    ResultArtifactField.SUB_GAMES,
    ResultArtifactField.SERIES_TOKENS,
)


def sealed_body(artifact: dict) -> dict:
    """The sealed sub-object, named ONCE so the builder and the verifier can
    never drift apart on what the digest covers."""
    return {name: artifact[name] for name in SEALED_FIELDS}


def game_tokens(budget: object) -> dict:
    """THIS game's spend, or the honest absence marker.

    `budget` is `ctx.language.gatekeeper.budget` -- `None` when the language
    layer was off. `report()`'s dict is carried verbatim and only ADDED to, so
    a future field in `TokenBudget.report()` reaches the report for free.
    """
    if budget is None:
        return dict(TOKENS_ABSENT)
    report = dict(budget.report())
    report[TokensField.TOTAL_TOKENS] = (
        _count(report, TokensField.INPUT_TOKENS) + _count(report, TokensField.OUTPUT_TOKENS)
    )
    report[TokensField.PRESENT] = True
    return report


def empty_series() -> dict:
    """A series that has measured nothing yet -- all four totals at zero and
    `games_measured` at zero, which is what makes the zeros readable as "no
    game contributed" rather than as "no tokens were spent"."""
    return dict.fromkeys((*_ACCUMULATED, TokensField.GAMES_MEASURED), 0)


def _count(source: dict, name: str) -> int:
    """A non-negative-safe integer read. `bool` is excluded explicitly: it is
    an `int` subclass, so a `true` on disk would otherwise add one."""
    value = source.get(name, 0)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def accumulate_series(previous: object, tokens: dict) -> dict:
    """THE REPORT-07 ARITHMETIC: the previous file's series total PLUS this
    game's.

    It cannot come from `budget.report()`. `Gatekeeper.__init__` builds a fresh
    `TokenBudget` per instance, `language_wiring.build_language_runtime` builds
    the gatekeeper once per PROCESS, and `budget.py` states "one instance = one
    series" -- so two games are two budgets and `report()` only ever holds THIS
    game. Rule 54 requires both numbers; a per-game figure in the series slot
    is a false report, and a single-game test cannot tell the two apart.

    A game with no measured spend leaves the running total untouched and does
    not advance `games_measured`, so the series total never absorbs a zero it
    did not measure.
    """
    running = previous if isinstance(previous, dict) else empty_series()
    base = {name: _count(running, name) for name in (*_ACCUMULATED, TokensField.GAMES_MEASURED)}
    if not tokens.get(TokensField.PRESENT):
        return base
    accumulated = {name: base[name] + _count(tokens, name) for name in _ACCUMULATED}
    accumulated[TokensField.GAMES_MEASURED] = base[TokensField.GAMES_MEASURED] + 1
    return accumulated
