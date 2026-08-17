"""The artifact spine: the `game_uid` join, the ONE canonical-signing entry
point every artifact writer goes through, and the one place artifacts may be
written (REPORT-06).

THE PUBLIC IMPORT PATH. The four filename builders and the `<NN>` index live
in `artifact_names.py` -- the dependency-free half, split out at the
150-code-line gate -- and are re-exported here, so `artifacts.<name>` resolves
every public name in the spine and no caller has to know which half holds it.

ONE SERIALIZER, NOT TWO. `canonical_json`/`digests_match` are imported from
`pursuit.network.config_hash` -- the same narrow, documented package-boundary
exception `security/commit_pack.py` and `security/step0_sign.py` already take.
(`07-CONTEXT.md` points at `pursuit.security` for these; it is wrong, see
`07-PLAN-OUTLINE.md` Sec11 item 2.) A second `json.dumps(sort_keys=True, ...)`
anywhere in the artifact package would be a second canonicalisation and is
forbidden (QUAL-02, D-46).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pursuit.network.config_hash import canonical_json, digests_match
from pursuit.services.reporting.artifact_names import (
    ARTIFACT_SUFFIX,
    FIRST_SUB_GAME_INDEX,
    SUB_GAME_INDEX_WIDTH,
    ArtifactField,
    ArtifactPrefix,
    config_filename,
    declaration_filename,
    log_filename,
    next_sub_game_index,
    result_filename,
    sub_game_suffix,
)
from pursuit.shared.durable_write import (
    DURABLE_WRITE_BACKOFF_SECONDS,
    DURABLE_WRITE_RETRIES,
    durable_write_json,
)

__all__ = (
    "ARTIFACT_SUFFIX",
    "FIRST_SUB_GAME_INDEX",
    "IGNORED_RUN_DIR",
    "SUB_GAME_INDEX_WIDTH",
    "ArtifactField",
    "ArtifactPrefix",
    "artifact_digest",
    "artifact_digest_matches",
    "artifact_header",
    "config_filename",
    "declaration_filename",
    "log_filename",
    "next_sub_game_index",
    "result_filename",
    "sub_game_suffix",
    "write_artifact",
)

# `agent_lifecycle.py:86` fixes the per-run output tree and `.gitignore`
# ignores it wholesale; see write_artifact below for the D7-1 decision.
IGNORED_RUN_DIR = "logs"


def artifact_header(*, game_uid: str, game_id: str, sub_game_index: int | None = None) -> dict:
    """The join block every artifact opens with. `sub_game_index` is carried
    only by the two artifacts whose NAME carries it, so a file's contents and
    its filename can never disagree about which sub-game it is."""
    header = {ArtifactField.GAME_UID: game_uid, ArtifactField.GAME_ID: game_id}
    if sub_game_index is not None:
        sub_game_suffix(sub_game_index)
        header[ArtifactField.SUB_GAME_INDEX] = sub_game_index
    return header


def artifact_digest(payload: object) -> str:
    """THE artifact seal: SHA-256 over `canonical_json(payload)`.

    Identical in construction to `config_hash.config_digest` and
    `step0_sign.digest_declaration`, and deliberately so -- a digest this
    function takes over `json.loads(game_params.json)` equals the digest the
    handshake put on the wire, byte for byte.
    """
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def artifact_digest_matches(payload: object, digest: str) -> bool:
    """Recompute and compare through `digests_match` -- D-46 fixes
    `secrets.compare_digest` as this project's one digest comparison, so no
    artifact check opens a second, weaker `==`."""
    return digests_match(artifact_digest(payload), digest)


def write_artifact(artifact_dir: Path | str, filename: str, payload: object) -> Path:
    """Durably write one artifact into the configured artifact directory.

    D7-1, DECIDED HERE. `.gitignore` ignores `logs/` wholesale, immediately
    beneath its own comment claiming the four required artifacts are kept out
    of the ignore list -- and `agent_step0_wiring.write_declaration` writes
    its handshake-time declaration PRECURSOR into `logs/<role>/`. The four
    DELIVERABLE artifacts (rule 50, Appendix F rule 4) therefore go to the
    configured artifact directory, which 07-01's `reporting.json` sets to
    `game_artifacts` and verified is not ignored.

    The `logs/` ignore rule is NOT narrowed, deliberately. Git cannot
    re-include a file whose parent directory is excluded, so narrowing means
    restructuring the rule into `logs/**` plus negations that the next editor
    can silently break -- returning us to exactly this bug, unnoticed. And
    `logs/` legitimately holds the bulky per-run wire logs (`<uid>.jsonl`) and
    nonce ledgers (`<uid>.ledger.jsonl`) that must stay out of git.

    So the refusal below is the enforcement, at the one write site, rather
    than a convention every caller has to remember: an artifact path under
    `logs/` is a programming error, not a preference.
    """
    path = Path(artifact_dir) / filename
    if IGNORED_RUN_DIR in path.parts:
        raise ValueError(
            f"artifact path {path} is under {IGNORED_RUN_DIR}/, which .gitignore "
            "ignores wholesale; the four required artifacts must be committable (D7-1)"
        )
    durable_write_json(
        path, payload, retries=DURABLE_WRITE_RETRIES, backoff=DURABLE_WRITE_BACKOFF_SECONDS,
    )
    return path
