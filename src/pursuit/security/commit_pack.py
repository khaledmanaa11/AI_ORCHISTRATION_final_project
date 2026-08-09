"""D-59: the ONE payload-builder for the commit hash (SEC-01, SEC-03, SEC-04).

`build_commit_payload()` produces the canonical `{"state","move","intent",
"nonce"}` dict used at Commit, at ledger-write, and at Audit re-hash --
`commit()` and `verify_reveal()` both call it, neither rebuilds the dict ad
hoc (Pitfall 2: two call sites reconstructing "the same" dict from different
intermediate representations silently diverge even with sort_keys=True,
which fixes key order, not type/shape drift).

**Package-boundary exception, deliberate and narrow** (see `security/
__init__.py`): `canonical_json`/`digests_match` are imported from
`pursuit.network.config_hash` rather than reimplemented. That module is a
pure, dependency-free hashing leaf; this import adds no coupling to
`AgentContext` or the turn loop, which is the actual intent behind the
package's "never pursuit.network" framing. Never add a second
`json.dumps(sort_keys=True, ...)` call here to sidestep this import -- that
would violate D-59 (the QUAL-02 "never rebuilt ad hoc" requirement) for no
real decoupling benefit.

`move`'s INTERNAL shape is opaque to every function in this module. 06-02
populates it with the composite action dict `{"move": <direction-token
dict>, "barrier": <direction-token dict> | None}` per the revised D-59/D-66
(a cop turn that places a barrier instead of moving encodes `"move"` as a
"stay" token, mirroring `CopAction.destination()`'s own "unchanged when
placing" semantics). This module never imports `move_payload` and never
validates that internal shape beyond `isinstance(move, dict)` -- a future
reader must not add a second, narrower validation here that would silently
reject a legal barrier-only turn.
"""

from __future__ import annotations

import hashlib
import secrets
from enum import Enum

from pursuit.network.config_hash import canonical_json, digests_match
from pursuit.shared.deception_types import Intent

_VALID_INTENTS = frozenset({Intent.TRUTH.value, Intent.LIE.value})


class CommitKey(str, Enum):
    """Payload key names -- mirrors `HandshakeKey`/`HintKey`."""

    STATE = "state"
    MOVE = "move"
    INTENT = "intent"
    NONCE = "nonce"

    def __str__(self) -> str:
        return self.value


def build_commit_payload(*, state: dict, move: dict, intent: str, nonce: str) -> dict:
    """Assemble the canonical `{state, move, intent, nonce}` dict (D-59).

    Validates shape and type only -- never coerces. `move`'s internal
    structure is opaque to this function (see module docstring).

    Raises
    ------
    TypeError
        If `state`/`move` are not dicts, `intent` is not a str (a bool is
        rejected here -- Pitfall 3), or `nonce` is not a str.
    ValueError
        If `intent` is a str but not exactly `Intent.TRUTH.value` or
        `Intent.LIE.value`, or `nonce` is empty.
    """
    if not isinstance(state, dict):
        raise TypeError(f"build_commit_payload: state must be a dict, got {type(state).__name__}")
    if not isinstance(move, dict):
        raise TypeError(f"build_commit_payload: move must be a dict, got {type(move).__name__}")
    if not isinstance(intent, str):
        raise TypeError(
            f"build_commit_payload: intent must be a str, got {type(intent).__name__}"
        )
    if intent not in _VALID_INTENTS:
        raise ValueError(
            f"build_commit_payload: intent must be one of {sorted(_VALID_INTENTS)}, got {intent!r}"
        )
    if not isinstance(nonce, str):
        raise TypeError(f"build_commit_payload: nonce must be a str, got {type(nonce).__name__}")
    if not nonce:
        raise ValueError("build_commit_payload: nonce must be a non-empty str")

    return {
        CommitKey.STATE.value: state,
        CommitKey.MOVE.value: move,
        CommitKey.INTENT.value: intent,
        CommitKey.NONCE.value: nonce,
    }


def _hash_payload(payload: dict) -> str:
    """SHA-256 hex digest of the canonical-JSON payload (SEC-01)."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def commit(state: dict, move: dict, intent: str) -> tuple[str, str]:
    """Generate a fresh nonce and the commit hash (SEC-04, rule 18).

    `nonce = secrets.token_hex(16)` is always generated internally here --
    never via `random`, never accepted as a caller-supplied argument for a
    fresh commit.

    Returns
    -------
    tuple[str, str]
        `(h_commit, nonce)`.
    """
    nonce = secrets.token_hex(16)
    payload = build_commit_payload(state=state, move=move, intent=intent, nonce=nonce)
    return _hash_payload(payload), nonce


def verify_reveal(h_commit: str, *, state: dict, move: dict, intent: str, nonce: str) -> bool:
    """Rebuild the payload via `build_commit_payload` (never a second
    builder), recompute the hash, and compare via `digests_match`
    (`secrets.compare_digest`) -- never Python `==` on hex strings.
    """
    payload = build_commit_payload(state=state, move=move, intent=intent, nonce=nonce)
    return digests_match(h_commit, _hash_payload(payload))
