"""Verify a `log_` artifact and reach ONE of three verdicts (REPORT-09).

Rule 20 (`docs/RULES.md:51`) makes a **verifying** replay viewer "a threshold
condition for approving and submitting the project", and Sec10.4 criterion 3
names the words on the screen. This module earns them; `gui/replay_app.py`
only renders what it returns.

THE HASH IS RECOMPUTED THROUGH `commit_pack.verify_reveal` AND NOWHERE ELSE
(D-59). `commit_pack.py:10-18` forbids a second `json.dumps(sort_keys=True,
...)` in this repository in as many words, and `network/config_hash.
canonical_json` is the one canonicalisation. A second serializer here would
not produce a missed forgery -- it would produce FALSE `FAILED` verdicts on an
honest artifact, which is the worst possible failure of this screen: it
accuses the opponent of our own formatting.

A TAMPERED ARTIFACT IS MALFORMED INPUT BY CONSTRUCTION, so the three types
`security/audit.py:159-165` catches are caught here too. That module's
boundary-rule block (`:56-124`) lists SIX production defects from this one
pattern, including instance 5 -- a `ValueError` from `build_commit_payload`
escaping a narrower `(TypeError, KeyError)` clause. A viewer that dies on a
tampered file shows no verdict at all, which is strictly worse than showing
`FAILED`.

THE IN-PROGRESS-GAME QUESTION IS DECIDED, and it lives in the sibling
`replay_source.py` with the refusal that enforces it: the artifact does not
exist until the game is over, and the two live files are refused BY NAME.

`mainloop()` IS CORRECT FOR THIS APP, unlike the live dashboard -- see
`gui/replay_app.py`, which owns that note.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.security.audit_shape import NO_USABLE_TURN
from pursuit.security.commit_pack import verify_reveal
from pursuit.services.reporting.artifacts import artifact_digest_matches
from pursuit.services.reporting.log_artifact_fields import LogArtifactField, sealed_body
from pursuit.services.reporting.log_turn_fields import TurnField
from pursuit.services.reporting.replay_board import board_colour_frames
from pursuit.services.reporting.replay_session import (
    SECTION_TITLES,
    WINDOW_TITLE,
    ReplaySession,
)
from pursuit.services.reporting.replay_source import ReplayExit, load_artifact
from pursuit.services.reporting.replay_verdict import (
    BANNER_COLOURS,
    NOTHING_TO_VERIFY,
    VERIFIED_OK,
    ReplayVerdict,
    TurnCheck,
    VerdictState,
    banner_colour,
    failed_banner,
    ratio_detail,
    seal_failed_banner,
)

__all__ = (
    "BANNER_COLOURS",
    "NOTHING_TO_VERIFY",
    "SECTION_TITLES",
    "VERIFIED_OK",
    "WINDOW_TITLE",
    "ReplayExit",
    "ReplaySession",
    "ReplayVerdict",
    "TurnCheck",
    "VerdictState",
    "banner_colour",
    "board_colour_frames",
    "check_turn",
    "check_turns",
    "load_artifact",
    "open_replay",
    "seal_matches",
    "verdict_from",
)

NO_COMMITMENT = "no commitment ledgered for this turn"
REHASHED = "re-hashed against h_commit"
MISMATCH = "re-hash does not match h_commit"
MALFORMED = "malformed commit payload"
UNUSABLE_TURN = "turn record is not an object"


def check_turn(turn: object) -> TurnCheck:
    """Re-hash ONE turn from the artifact alone."""
    if not isinstance(turn, dict):
        return TurnCheck(turn=NO_USABLE_TURN, committed=True, ok=False, detail=UNUSABLE_TURN)
    number = turn.get(TurnField.TURN, NO_USABLE_TURN)
    if turn.get(TurnField.HASH) is None:
        return TurnCheck(turn=number, committed=False, ok=False, detail=NO_COMMITMENT)
    try:
        matched = verify_reveal(
            turn[TurnField.HASH],
            state=turn[TurnField.STATE],
            move=turn[TurnField.MOVE],
            intent=turn[TurnField.INTENT],
            nonce=turn[TurnField.NONCE],
        )
    except (TypeError, KeyError, ValueError) as exc:
        return TurnCheck(turn=number, committed=True, ok=False, detail=f"{MALFORMED} -- {exc}")
    return TurnCheck(
        turn=number, committed=True, ok=matched, detail=REHASHED if matched else MISMATCH
    )


def check_turns(artifact: dict) -> tuple[TurnCheck, ...]:
    """Every turn, in the artifact's own order, so the cursor can index it."""
    turns = artifact.get(LogArtifactField.TURNS)
    return tuple(check_turn(turn) for turn in turns) if isinstance(turns, list) else ()


def seal_matches(artifact: dict) -> bool:
    """The artifact's own seal, recomputed off the object in hand.

    Additive rather than redundant: the seal covers `outcome`,
    `audit_verdict`, `prior_game_uids` and `truncated_tail`, none of which
    any per-turn commit hash can see. Contained on the same boundary rule --
    a tampered artifact must reach a verdict, never an exception.
    """
    try:
        digest = artifact[LogArtifactField.LOG_DIGEST]
        return artifact_digest_matches(sealed_body(artifact), digest)
    except (TypeError, KeyError, ValueError):
        return False


def verdict_from(artifact: dict, checks: tuple[TurnCheck, ...]) -> ReplayVerdict:
    """The whole-file verdict, from checks already made.

    THE NON-ZERO GUARD RUNS BEFORE ANY AGGREGATE, and that ordering is the
    load-bearing line of this module: `all(...)` over an empty sequence is
    True, `audit_record.all_matched([])` is this repository's canonical
    instance of it, and a zero-turn artifact reading `Verified OK` on a
    grader's screen would be the same bug with an audience.
    """
    committed = tuple(check for check in checks if check.committed)
    verified = len(tuple(check for check in committed if check.ok))
    detail = ratio_detail(verified, len(committed))
    if not committed:
        return ReplayVerdict(VerdictState.NOTHING_TO_VERIFY, NOTHING_TO_VERIFY, detail, 0, 0)
    failure = next((check for check in committed if not check.ok), None)
    if failure is not None:
        banner = failed_banner(failure)
    elif not seal_matches(artifact):
        banner = seal_failed_banner()
    else:
        return ReplayVerdict(VerdictState.OK, VERIFIED_OK, detail, verified, len(committed))
    return ReplayVerdict(VerdictState.FAILED, banner, detail, verified, len(committed))


#: THERE IS DELIBERATELY NO ONE-CALL `verdict_for(artifact)` CONVENIENCE
#: WRAPPER. It was written, and the production-caller grep found it reachable
#: from tests only -- D7-3's finding, in this plan's own work. Rather than ship
#: a second entry point that nothing on the screen's path uses, callers who
#: want a whole-file answer use `open_replay(path).verdict`, which is the
#: EXACT value the banner renders. A measurement taken through a parallel
#: helper would be evidence about the helper.


def open_replay(path: Path | str) -> ReplaySession:
    """Load, verify, and hand back a session positioned on the first turn.

    THE PRODUCTION ENTRY POINT: `gui/replay_app.main` calls exactly this, so
    the verdict on the screen and the verdict a test asserts are one value
    computed once, never two parallel derivations.
    """
    artifact = load_artifact(path)
    checks = check_turns(artifact)
    return ReplaySession(
        artifact, checks, verdict_from(artifact, checks), source=Path(path).name
    )
