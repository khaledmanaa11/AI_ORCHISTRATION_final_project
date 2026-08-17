"""`log_<game_id>_g<NN>.json` -- "turn-by-turn journal: commitments, moves,
hints, verdicts, nonce and hash. Enables full cryptographic verification in the
replay simulator" (docs/PARAMETERS.md:167, and rule 20 makes that verifying
replay a threshold condition for approving the project).

THE FULL RATIONALE IS `docs/PRD_log_artifact.md` -- the per-mechanism PRD
CLAUDE.md Sec2.3 requires for a central mechanism, and where this module's
reasoning moved when the docstring took this file to 151/150 (split, never
compressed; the `strategy/display_belief.py` precedent). What follows is the
contract; the PRD carries the measurements and the rejected alternatives.

GAME END ONLY -- D-64 AND SEC-04, AND THIS IS NOT A CONVENTION BUT A RULE.
`security/ledger.py` states its file "is never read or written by anything on
the wire path (D-64)"; rule 18 keeps every nonce secret while the game is live,
and only SEC-04's end-of-game publication makes the ledger readable. So this
builder is reachable ONLY from a game-end path (07-07 wires it), never from the
turn loop -- enforced as a scan on every suite run by
`tests/unit/test_log_artifact_reachability.py`, not recorded as a grep.

SELF-CONTAINED, OR IT IS NOT AN ARTIFACT. The viewer never opens the `.jsonl`
or the `.ledger.jsonl`: every turn carries the five `commit_pack.verify_reveal`
inputs at its top level. `tests/integration/test_log_artifact_roundtrip.py`
proves it by DELETING both sources before verifying.

RE-HASHING GOES THROUGH `commit_pack`, NEVER A FRESH `json.dumps` (D-59), and
the seal goes through `artifacts.artifact_digest`, which is `config_hash`'s one
`canonical_json`. WIRE TRUTH ONLY -- no belief, no scent, nothing derived from
`ctx.state`; `log_turn_fields.py` owns that boundary.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.security.commit_pack import verify_reveal
from pursuit.services.reporting.artifacts import (
    artifact_digest,
    artifact_digest_matches,
    artifact_header,
    log_filename,
    write_artifact,
)
from pursuit.services.reporting.log_join import join_game
from pursuit.services.reporting.log_turn_fields import TurnField

__all__ = (
    "SEALED_FIELDS",
    "LogArtifactField",
    "build_log_artifact",
    "verify_log_artifact",
    "verify_log_turns",
    "write_log_artifact",
)


class LogArtifactField:
    """Key names for the log artifact -- structural, avoids magic strings."""

    ROLE = "role"
    TURNS = "turns"
    OUTCOME = "outcome"
    AUDIT_VERDICT = "audit_verdict"
    TRUNCATED_TAIL = "truncated_tail"
    LOG_DIGEST = "log_digest"


# What the seal covers. `truncated_tail` is INSIDE it deliberately: whether a
# game's tail was lost is part of the record's provenance, and a marker outside
# the seal could be flipped without breaking it.
SEALED_FIELDS = (
    LogArtifactField.TURNS,
    LogArtifactField.OUTCOME,
    LogArtifactField.AUDIT_VERDICT,
    LogArtifactField.TRUNCATED_TAIL,
)


def _sealed_body(artifact: dict) -> dict:
    """The sealed sub-object, named ONCE so the builder and the verifier can
    never drift apart on what the digest covers."""
    return {name: artifact[name] for name in SEALED_FIELDS}


def build_log_artifact(
    log_path: Path | str, *, game_uid: str, game_id: str, sub_game_index: int
) -> dict:
    """Join one finished game's wire log to its ledger and seal the result.

    The log's own `game_uid` must agree with the caller's: an artifact named
    for one game and filled from another's log is the failure this check
    exists for, and it is cheap because both sources are already open.
    """
    joined = join_game(log_path)
    if joined.game_uid is not None and joined.game_uid != game_uid:
        raise ValueError(
            f"log at {log_path} carries game_uid {joined.game_uid!r}, "
            f"not the requested {game_uid!r}"
        )
    artifact = artifact_header(game_uid=game_uid, game_id=game_id, sub_game_index=sub_game_index)
    artifact[LogArtifactField.ROLE] = joined.role
    artifact[LogArtifactField.TURNS] = joined.turns
    artifact[LogArtifactField.OUTCOME] = joined.outcome
    artifact[LogArtifactField.AUDIT_VERDICT] = joined.audit_verdict
    artifact[LogArtifactField.TRUNCATED_TAIL] = joined.truncated_tail
    artifact[LogArtifactField.LOG_DIGEST] = artifact_digest(_sealed_body(artifact))
    return artifact


def verify_log_artifact(path: Path | str) -> bool:
    """Read a written log artifact back and check its own seal.

    Reads the FILE, so it is the round trip through `durable_write_json` and
    back through `json.loads` being checked -- the same promise
    `verify_config_artifact` makes, for the same reason.
    """
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    return artifact_digest_matches(_sealed_body(artifact), artifact[LogArtifactField.LOG_DIGEST])


def verify_log_turns(artifact: dict) -> tuple[int, int]:
    """Re-hash every committed turn FROM THE ARTIFACT ALONE (07-08's entry).

    Returns `(verified, committed)`. `committed` counts only turns carrying an
    `h_commit`; a trailing game-over turn has wire records but never a ledger
    entry, and counting it would make the ratio a lie. A caller must check
    `committed > 0` before treating `verified == committed` as evidence --
    `audit_record.all_matched([])` returning True is this repository's own
    canonical instance of that trap.
    """
    verified = committed = 0
    for turn in artifact[LogArtifactField.TURNS]:
        if turn[TurnField.HASH] is None:
            continue
        committed += 1
        verified += verify_reveal(
            turn[TurnField.HASH],
            state=turn[TurnField.STATE],
            move=turn[TurnField.MOVE],
            intent=turn[TurnField.INTENT],
            nonce=turn[TurnField.NONCE],
        )
    return verified, committed


def write_log_artifact(
    artifact_dir: Path | str,
    log_path: Path | str,
    *,
    game_uid: str,
    game_id: str,
    sub_game_index: int,
) -> Path:
    """Build, durably write, then re-read and re-check BOTH promises.

    The seal check catches a broken write. The re-hash check catches a broken
    BUILDER: `commit_own_action` computed each `h_commit` from the very payload
    copied here, so a turn that fails to re-hash means this module corrupted it
    in transit -- an internal inconsistency, never evidence about the game.
    Shipping such a file would put a FAILED verdict on the grader's screen and
    blame the opponent for our own bug.
    """
    artifact = build_log_artifact(
        log_path, game_uid=game_uid, game_id=game_id, sub_game_index=sub_game_index
    )
    path = write_artifact(artifact_dir, log_filename(game_id, sub_game_index), artifact)
    if not verify_log_artifact(path):
        raise ValueError(f"log artifact failed seal re-verification after write: {path}")
    verified, committed = verify_log_turns(json.loads(path.read_text(encoding="utf-8")))
    if verified != committed:
        raise ValueError(
            f"log artifact re-hashes {verified}/{committed} committed turns: {path}"
        )
    return path
