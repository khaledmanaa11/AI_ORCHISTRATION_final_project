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


def compare_named_digest(name: str, local: str, remote: str | None) -> tuple[bool, str]:
    """Compare one named pair of digests exchanged at handshake (D-46, rule 23).

    A `remote` of None counts as a mismatch: a peer whose payload carries no
    digest under this name has not locked the corresponding model, so
    non-agreement is the same outcome as an actual value difference — only
    the returned detail distinguishes "absent" from "differed", so an
    operator can tell an older build from an incompatible one.

    Returns (matched, detail); detail names `name` and is ready to fold into
    an abort message. Reuses digests_match (secrets.compare_digest) so a
    second digest never opens a second, weaker '==' comparison (QUAL-02) —
    the handshake (02-08) is the one caller today, and any later digest
    exchange reuses this rather than hand-rolling its own compare.
    """
    if remote is None:
        return False, f"{name} digest absent from peer payload"
    if digests_match(local, remote):
        return True, f"{name} digests agree"
    return False, f"{name} digest mismatch: local={local} remote={remote}"
