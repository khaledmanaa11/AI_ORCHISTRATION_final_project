"""`result_<game_id>.json` -- "Final results summary across all sub-games.
**This is the mandatory report emailed to the lecturer.**"
(docs/PARAMETERS.md:168).

THE FULL RATIONALE IS `docs/PRD_result_artifact.md` -- the per-mechanism PRD
CLAUDE.md Sec2.3 requires, and where this module's reasoning moved when the
docstring took the file past 150 (split, never compressed; the
`PRD_log_artifact.md` precedent). It carries OQ-4's interpretation with both
citations, the measurement behind rule 54's two numbers, the two honest
absences and D7-15. The SCHEMA and the series arithmetic are
`result_artifact_fields.py`, re-exported here. What follows is the contract.

ONE FILE PER SERIES (OQ-4), durably rewritten with `.prev` rotation after each
sub-game and emailed each time -- PARAMETERS gets its single aggregate file
and rule 32's per-game sanction becomes unreachable.

THE SERIES TOTAL CANNOT COME FROM `budget.report()`: one budget is one process
is one game. It is this file's own previous generation plus this game's, and
`record_sub_game` is the one entry point that does both steps.

THE COMMIT HASH IS REUSED, NOT RE-DERIVED -- the caller reads it out of the
Step-0 declaration this game actually ran under (rule 53). NOTHING HERE SETS
THE GAMES-PLAYED VALUE, reads it, or reads around it.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.services.reporting.artifacts import (
    ArtifactField,
    artifact_digest,
    artifact_digest_matches,
    artifact_header,
    result_filename,
    write_artifact,
)
from pursuit.services.reporting.result_artifact_fields import (
    GAMES_PLAYED_UNSET,
    ResultArtifactField,
    SubGameField,
    TokensField,
    accumulate_series,
    game_tokens,
    sealed_body,
)
from pursuit.shared.durable_write import load_json_with_fallback

# `TOKENS_ABSENT` and `empty_series` are deliberately NOT re-exported here --
# nothing in this module's own contract uses them, and the package `__init__`
# carries them straight from `result_artifact_fields`. `SEALED_FIELDS` and
# `sealed_body` stay off the package surface entirely: `artifact_log.py`
# already owns those two names for a DIFFERENT artifact, and one package
# exporting two seals under one spelling is how a verifier checks the wrong
# body. Partial re-export, matching `artifact_log.py` rather than a blanket one.
__all__ = (
    "GAMES_PLAYED_UNSET",
    "ResultArtifactField",
    "SubGameField",
    "TokensField",
    "accumulate_series",
    "build_result_artifact",
    "game_tokens",
    "read_series",
    "record_sub_game",
    "sealed_body",
    "verify_result_artifact",
    "write_result_artifact",
)


def read_series(artifact_dir: Path | str, game_id: str) -> dict | None:
    """This series' file as it stands, or `None` when no sub-game has been
    recorded yet. Reads through `load_json_with_fallback`, and treats an
    unreadable previous generation as ABSENT rather than raising -- refusing to
    write this game's report because the last one is corrupt would hand rule 32
    the very game it sanctions (PRD Sec6)."""
    path = Path(artifact_dir) / result_filename(game_id)
    try:
        data = load_json_with_fallback(path)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def build_result_artifact(
    *,
    game_uid: str,
    game_id: str,
    role: str,
    sub_game_index: int,
    agreement: dict,
    tokens: dict,
    commit_hash: str,
    log_artifact: str | None,
    previous: dict | None = None,
) -> dict:
    """The next generation of this series' file: `previous` plus one sub-game.
    `previous` is `read_series`' answer -- its sub-game list is extended, never
    rewritten, and its series total is the base this game is added to."""
    earlier = (previous or {}).get(ResultArtifactField.SUB_GAMES)
    sub_games = list(earlier) if isinstance(earlier, list) else []
    sub_games.append(
        {
            ArtifactField.SUB_GAME_INDEX: sub_game_index,
            SubGameField.AGREEMENT: agreement,
            SubGameField.TOKENS: tokens,
            SubGameField.COMMIT_HASH: commit_hash,
            SubGameField.LOG_ARTIFACT: log_artifact,
        }
    )
    artifact = artifact_header(game_uid=game_uid, game_id=game_id)
    artifact[ResultArtifactField.ROLE] = role
    artifact[ResultArtifactField.COMMIT_HASH] = commit_hash
    artifact[ResultArtifactField.GAMES_PLAYED_DECLARED] = dict(GAMES_PLAYED_UNSET)
    artifact[ResultArtifactField.SUB_GAMES] = sub_games
    artifact[ResultArtifactField.SERIES_TOKENS] = accumulate_series(
        (previous or {}).get(ResultArtifactField.SERIES_TOKENS), tokens
    )
    artifact[ResultArtifactField.RESULT_DIGEST] = artifact_digest(sealed_body(artifact))
    return artifact


def verify_result_artifact(path: Path | str) -> bool:
    """Read a written result artifact back and check its own seal -- off the
    FILE, so the round trip through `durable_write_json` is what is checked."""
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    return artifact_digest_matches(
        sealed_body(artifact), artifact[ResultArtifactField.RESULT_DIGEST]
    )


def write_result_artifact(artifact_dir: Path | str, artifact: dict) -> Path:
    """Durably rewrite the series file, then re-read and re-check its seal --
    the same promise `write_log_artifact` makes, so a report that fails its own
    seal does so here, as our bug, rather than on a grader's screen as a
    verdict about the game (PRD Sec5)."""
    path = write_artifact(
        artifact_dir, result_filename(artifact[ArtifactField.GAME_ID]), artifact
    )
    if not verify_result_artifact(path):
        raise ValueError(f"result artifact failed seal re-verification after write: {path}")
    return path


def record_sub_game(
    artifact_dir: Path | str,
    *,
    game_uid: str,
    game_id: str,
    role: str,
    sub_game_index: int,
    agreement: dict,
    budget: object,
    commit_hash: str,
    log_artifact: str | None,
) -> tuple[dict, Path]:
    """Read the series, add this sub-game, rewrite it. THE entry point.

    It exists so that read-accumulate-write is one call: an accumulation that
    a caller can skip is an accumulation that will eventually be skipped, and
    the failure is silent -- a series total that equals the last game's.
    """
    previous = read_series(artifact_dir, game_id)
    artifact = build_result_artifact(
        game_uid=game_uid, game_id=game_id, role=role, sub_game_index=sub_game_index,
        agreement=agreement, tokens=game_tokens(budget), commit_hash=commit_hash,
        log_artifact=log_artifact, previous=previous,
    )
    return artifact, write_result_artifact(artifact_dir, artifact)
