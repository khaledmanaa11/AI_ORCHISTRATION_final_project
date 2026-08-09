"""D-62 follow-up: Step-0 CONTENT verification -- split from
handshake_evaluate.py at the 150-code-line gate (that file was already AT
its ceiling).

The peer's FULL declaration now rides the same handshake payload as its
digest (book Sec5.5: the declaration is meant to be PUBLISHED -- OS/CPU/
RAM/GPU/model/code-version/commit-hash carry no secrecy reason to be
withheld, so sending the content is strictly more faithful to the book
than a bare digest). Presence of the digest is still the minimum bar (a
peer sending nothing at all still fails, matching rule 24's actual
failure mode); a peer that sends ONLY a digest (an opponent team's own
implementation we cannot force to publish content) still agrees, logged
as digest-only -- never a hard failure. Only a declaration whose CONTENT
does not hash to its own claimed digest is a genuine, provable mismatch.
"""

from __future__ import annotations

from pursuit.network.envelope import Envelope
from pursuit.network.handshake_wire import HandshakeKey
from pursuit.security import step0_sign

_DIGEST_ONLY_DETAIL = "step0 digest present (declaration content not sent, digest-only)"


def _step0_verified(shared_secret: str | None, envelope: Envelope) -> tuple[bool, str]:
    """Digest presence is required; content verification runs only when
    the peer ALSO sent `STEP0_DECLARATION` (opt-in on their side)."""
    remote_digest = envelope.payload.get(HandshakeKey.STEP0_DIGEST)
    if remote_digest is None:
        return False, "step0 digest absent from peer payload"

    remote_envelope = envelope.payload.get(HandshakeKey.STEP0_DECLARATION)
    declaration = remote_envelope.get("declaration") if remote_envelope is not None else None
    if declaration is None:
        return True, _DIGEST_ONLY_DETAIL

    verified = step0_sign.verify_declaration(
        declaration, digest=remote_digest, hmac_value=remote_envelope.get("hmac"),
        secret=shared_secret,
    )
    if not verified:
        return False, "step0 declaration content does not hash to its own claimed digest"
    return True, "step0 declaration content verified against its digest"
