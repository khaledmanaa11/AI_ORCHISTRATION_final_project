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


def unusable_peer_digest(name: str, remote: object) -> str | None:
    """The ONE gate every PEER-SUPPLIED digest slot passes through (05-12 G9;
    `security/audit.py`'s boundary rule, instance 7).

    Returns a NAMED non-agreement detail when *remote* cannot serve as a
    digest at all, and None when it is a `str` this side may hand to
    `digests_match`. Two unusable shapes, kept distinguishable in the detail
    because they mean different things to an operator:

      - absent: an older build that never locked this model;
      - present but not a `str`: `Envelope.from_dict` validates the payload
        only as a dict, so `payload["digest"]` is whatever JSON type the peer
        sent. Measured at `bcc04bf`: an int/list/dict/bool there reached
        `digests_match` and raised `TypeError` out of `evaluate()`, past
        `handshake_evaluate`'s try/except (which wraps the DECODE block only)
        and out of `run_agent` (whose only guard is `except ToolError`) —
        killing us AT THE HANDSHAKE with no verdict, no FINAL_REVEAL and no
        nonces published, i.e. rule 36 against US, on the opponent's say-so.

    Deliberately NOT a hex-shape or length check. This is a SAFETY gate, not
    a convention gate: a foreign league implementation is free to use a digest
    this side simply disagrees with, and that must reach the "differed"
    branch as evidence, never be pre-judged here (rules 16/22).

    The peer's VALUE is never interpolated into the detail — only its type
    name. The detail is folded into an abort message and echoed to a console
    and a JSONL log, and a peer chooses that value; a bounded type name cannot
    be used to flood either sink.
    """
    if remote is None:
        return f"{name} digest absent from peer payload"
    if not isinstance(remote, str):
        return f"{name} digest present in peer payload but not a string: {type(remote).__name__}"
    return None


def compare_named_digest(name: str, local: str, remote: object) -> tuple[bool, str]:
    """Compare one named pair of digests exchanged at handshake (D-46, rule 23).

    A `remote` that is absent, or present in a shape no digest can have,
    counts as a mismatch: a peer whose payload carries no usable digest under
    this name has not locked the corresponding model, so non-agreement is the
    same outcome as an actual value difference — only the returned detail
    distinguishes "absent" / "not a string" / "differed", so an operator can
    tell an older build from an incompatible one from a hostile one.

    `local` is OURS and is deliberately NOT guarded here: a non-str local
    digest is internal misuse and still raises out of `digests_match`, whose
    strict contract (D-46 fixes `secrets.compare_digest` as the project's one
    digest idiom) is unchanged by this function. Containment applies to the
    half a peer controls, and only to that half.

    Returns (matched, detail); detail names `name` and is ready to fold into
    an abort message. Reuses digests_match (secrets.compare_digest) so a
    second digest never opens a second, weaker '==' comparison (QUAL-02) —
    the handshake (02-08) is the one caller today, and any later digest
    exchange reuses this rather than hand-rolling its own compare.
    """
    unusable = unusable_peer_digest(name, remote)
    if unusable is not None:
        return False, unusable
    if digests_match(local, remote):
        return True, f"{name} digests agree"
    return False, f"{name} digest mismatch: local={local} remote={remote}"
