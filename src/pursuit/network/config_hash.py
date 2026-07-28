"""NET-09 / D-08 / D-15 canonical-JSON config digest.

The SHA-256 of the shared game config, exchanged at handshake, whose
mismatch aborts the game before move 1. The digest is taken over the
CANONICALLY re-serialized JSON rather than raw file bytes (RESEARCH
Pattern 6, Pitfall 5): raw-byte hashing conflates identical formatting with
identical meaning, so an editor re-saving one side's file with different
line endings or indentation would abort a legal game on a phantom mismatch.
Canonical JSON is also this project's locked hash-input convention (SEC-03),
so reusing it here keeps exactly one canonicalisation in the repo — Phase 6's
commit-reveal hash MUST call canonical_json() rather than re-writing its own
json.dumps call (QUAL-02).

This module hashes game_params.json ONLY. It never hashes the per-agent
network configuration file, which legitimately differs per agent (different
port, different opponent URL — D-04); hashing it would abort every game.
"""

import hashlib
import json
import secrets
from pathlib import Path


def canonical_json(data: object) -> str:
    """Return the project-wide canonical JSON form (SEC-03).

    Keys are sorted recursively; separators carry no extra whitespace. Note
    that sort_keys sorts nested OBJECTS recursively but leaves ARRAY order
    untouched, which is required: scoring values are ordered [cop, thief]
    pairs, and sorting them would silently swap the two sides' scores.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def config_digest(path: "Path | str") -> str:
    """Return the SHA-256 hex digest of canonical_json(json.loads(path)).

    FileNotFoundError and json.JSONDecodeError (a ValueError subclass)
    propagate unchanged — fail loud, no silent default digest. encoding is
    explicit on both the read and the encode so the digest is identical on
    Windows and Linux regardless of locale.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def digests_match(left: str, right: str) -> bool:
    """Constant-time comparison of two digests.

    The digests are public so constant-time comparison is not strictly
    required here, but CLAUDE.md fixes secrets.compare_digest as this
    project's single digest-comparison idiom — using it here means the
    handshake (02-08) never hand-rolls `==`, and Phase 6 inherits the habit
    where it genuinely matters.
    """
    if not isinstance(left, str) or not isinstance(right, str):
        raise TypeError("digests_match requires two str arguments")
    return secrets.compare_digest(left, right)
