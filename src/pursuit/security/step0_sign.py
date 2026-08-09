"""D-62: Step-0 declaration signing -- digest always, HMAC when a shared
secret exists.

`canonical_json` is imported from `pursuit.network.config_hash` -- the SAME
narrow, documented exception `commit_pack.py` already uses (see
`security/__init__.py`): a pure, dependency-free hashing leaf, not a
`pursuit.network`/`AgentContext` coupling.
"""

from __future__ import annotations

import hashlib
import hmac

from pursuit.network.config_hash import canonical_json, digests_match


class SignKey:
    """Payload key names -- mirrors `CommitKey`/`HandshakeKey`."""

    DIGEST = "digest"
    SIGNED = "signed"
    HMAC = "hmac"


def digest_declaration(declaration: dict) -> str:
    """SHA-256 hex digest of the canonical-JSON declaration (D-62, always run)."""
    return hashlib.sha256(canonical_json(declaration).encode("utf-8")).hexdigest()


def _hmac_hex(declaration: dict, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), canonical_json(declaration).encode("utf-8"), hashlib.sha256,
    ).hexdigest()


def sign_declaration(declaration: dict, *, secret: str | None) -> dict:
    """Digest always; HMAC-SHA256 additionally when *secret* is given.

    `signed` is explicit -- an absent secret produces `signed: False`, never
    a silently-assumed-verified declaration."""
    digest = digest_declaration(declaration)
    if secret is None:
        return {SignKey.DIGEST: digest, SignKey.SIGNED: False, SignKey.HMAC: None}
    return {
        SignKey.DIGEST: digest, SignKey.SIGNED: True,
        SignKey.HMAC: _hmac_hex(declaration, secret),
    }


def verify_declaration(
    declaration: dict, *, digest: str, hmac_value: str | None, secret: str | None,
) -> bool:
    """Recompute and compare BOTH the digest (always) and the HMAC (only
    when both `hmac_value` and `secret` are present) -- signed vs unsigned
    peers are never conflated."""
    if not digests_match(digest_declaration(declaration), digest):
        return False
    if hmac_value is None or secret is None:
        return True
    return digests_match(_hmac_hex(declaration, secret), hmac_value)
