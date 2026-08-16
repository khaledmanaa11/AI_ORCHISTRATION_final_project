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

_STEP0 = "step0"
_DIGEST_ONLY_DETAIL = "step0 digest present (declaration content not sent, digest-only)"
_UNREADABLE_DETAIL = (
    "step0 digest present (declaration container is not an object -- unreadable, "
    "treated as digest-only)"
)
_UNREADABLE_DIGEST_DETAIL = (
    "step0 digest present but not a string -- unreadable, nothing to verify content "
    "against, treated as digest-only"
)
_UNREADABLE_HMAC_NOTE = " (declaration hmac unreadable -- treated as unsigned)"


def _step0_verified(shared_secret: str | None, envelope: Envelope) -> tuple[bool, str]:
    """Digest presence is required; content verification runs only when
    the peer ALSO sent `STEP0_DECLARATION` (opt-in on their side).

    Reads PEER-SUPPLIED data and must never raise -- `security/audit.py`'s
    boundary rule, INSTANCE 6. Until 05-10 a `step0_declaration` that was a
    str/list/number hit `remote_envelope.get(...)` and raised `AttributeError`,
    which `evaluate`'s try/except does not cover (it wraps the DECODE block
    only) and which `respond_to_handshake`'s own "never raises" docstring flatly
    contradicted. On the outbound half it escaped `perform_handshake` into
    `run_agent` and killed the process AT THE HANDSHAKE, so a foreign
    implementation with an odd container shape would cost us the league game
    before move 1.

    An unreadable container resolves to the EXISTING digest-only case rather
    than a STEP0_MISMATCH abort, named distinctly in the detail so the log still
    says what happened. Deliberate on both sides: there is no content to verify,
    so nothing is waved through; a peer wanting that outcome can already have it
    by sending no declaration at all, so this opens no evasion; and a hard abort
    would be a NEW false-accusation path against an honest foreign shape (rules
    16/22), the exact class of defect this phase has corrected repeatedly.

    05-12 closes TWO MORE escapes of the same shape, found by probe against
    this very function while containing G9 -- both peer-controlled strings
    handed straight to `digests_match` inside `verify_declaration`, which
    raises `TypeError` on any non-str. Both are reached ONLY when the peer
    sent a declaration, which is why 05-10's sweep -- it stopped at the
    declaration CONTAINER -- could not see either.

    BOTH are downgraded, NEITHER is a new abort, and the reasoning is this
    module's own, applied unchanged: an unreadable value leaves NOTHING TO
    VERIFY, and a peer wanting that outcome can already have it by sending no
    declaration at all -- so no evasion is opened, and inventing an abort here
    would be a NEW false-accusation path (rules 16/22) bought for nothing.

      - a non-str DIGEST joins `_UNREADABLE_DETAIL`'s digest-only branch. The
        minimum bar rule 24 cares about is that Step-0 RAN and the key was
        SENT, and `remote_digest is None` still enforces exactly that. Note
        the containment must NOT be `unusable_peer_digest`'s absent-or-not-str
        answer: that gate is right where the digest is COMPARED (config,
        scent), and wrong here, where presence alone is the test -- a non-str
        digest that arrives with no declaration was AGREED before 05-12 and
        still agrees, because the value is never used on that path;
      - a non-str HMAC is treated as unsigned, named in the detail. Its
        ABSENCE already agrees, so this changes nothing a peer cannot do by
        omitting the field.
    """
    remote_digest = envelope.payload.get(HandshakeKey.STEP0_DIGEST)
    if remote_digest is None:
        return False, f"{_STEP0} digest absent from peer payload"

    remote_envelope = envelope.payload.get(HandshakeKey.STEP0_DECLARATION)
    if remote_envelope is not None and not isinstance(remote_envelope, dict):
        return True, _UNREADABLE_DETAIL
    declaration = remote_envelope.get("declaration") if remote_envelope is not None else None
    if declaration is None:
        return True, _DIGEST_ONLY_DETAIL
    if not isinstance(remote_digest, str):
        return True, _UNREADABLE_DIGEST_DETAIL

    hmac_value = remote_envelope.get(step0_sign.SignKey.HMAC)
    hmac_note = ""
    if hmac_value is not None and not isinstance(hmac_value, str):
        hmac_value, hmac_note = None, _UNREADABLE_HMAC_NOTE
    verified = step0_sign.verify_declaration(
        declaration, digest=remote_digest, hmac_value=hmac_value, secret=shared_secret,
    )
    if not verified:
        return False, "step0 declaration content does not hash to its own claimed digest"
    return True, f"step0 declaration content verified against its digest{hmac_note}"
