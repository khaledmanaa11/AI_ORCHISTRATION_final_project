"""`log_<game_id>_g<NN>.json`'s top-level key names and what the seal covers.

Split out of `artifact_log.py` at the 150-code-line gate (Segal Table 5, the
combined module measured 151) -- the `artifact_declaration_fields.py` precedent,
and along the same seam: the NAMES and the SEALED SET are a schema a reader
must know, while build/verify/write are the mechanics. `artifact_log.py`
re-exports both public names, so callers keep one import path.

Split, never compressed.
"""

from __future__ import annotations

__all__ = ("SEALED_FIELDS", "LogArtifactField", "sealed_body")


class LogArtifactField:
    """Key names for the log artifact -- structural, avoids magic strings."""

    ROLE = "role"
    PRIOR_GAME_UIDS = "prior_game_uids"
    TURNS = "turns"
    OUTCOME = "outcome"
    AUDIT_VERDICT = "audit_verdict"
    TRUNCATED_TAIL = "truncated_tail"
    LOG_DIGEST = "log_digest"


# What the seal covers. `truncated_tail` is INSIDE it deliberately: whether a
# game's tail was lost is part of the record's provenance, and a marker outside
# the seal could be flipped without breaking it. `prior_game_uids` likewise --
# it is D-61 evidence about which records belong to this game, not a note.
SEALED_FIELDS = (
    LogArtifactField.PRIOR_GAME_UIDS,
    LogArtifactField.TURNS,
    LogArtifactField.OUTCOME,
    LogArtifactField.AUDIT_VERDICT,
    LogArtifactField.TRUNCATED_TAIL,
)


def sealed_body(artifact: dict) -> dict:
    """The sealed sub-object, named ONCE so the builder and the verifier can
    never drift apart on what the digest covers."""
    return {name: artifact[name] for name in SEALED_FIELDS}
