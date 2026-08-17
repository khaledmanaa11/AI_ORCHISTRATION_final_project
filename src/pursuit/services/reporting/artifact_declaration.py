"""`declaration_<game_id>.json` -- the D-71 wrapper AROUND the signed Step-0
payloads, which it embeds verbatim and never reaches inside.

WHY THE WRAPPER EXISTS AT ALL. `docs/PARAMETERS.md:165` asks this artifact for
"both teams' identities, repo URLs, MCP server addresses, hardware spec,
language model, agreed token ceiling, start/end times". Step-0's signed
declaration already carries the identity/hardware/model half -- the ten Sec5.5
keys `step0_collect.collect_declaration` assembles -- but the rest is NOT in
it, and MUST NOT BE PUT IN IT. `agent_step0_wiring.declare_step0` signs those
ten keys with `step0_sign.sign_declaration`, and `handshake_evaluate`'s
`_step0_verified(...)` returns `HandshakeOutcome.STEP0_MISMATCH` on any
disagreement: one extra field inside the signed dict aborts every game against
a peer, and the failure presents as a broken test suite rather than as a
protocol change. So the remaining PARAMETERS content goes STRICTLY OUTSIDE the
envelopes, at the artifact's top level, where no signature covers it.
`DeclarationContext` in `artifact_declaration_fields.py` is that content.

A DIGEST-ONLY PEER GETS AN HONEST ABSENCE. `HandshakeResult.
peer_step0_declaration` is None when the peer sent a digest and no content
(`write_declaration` skips its `_peer.json` for exactly that case). This
wrapper then records `peer: null` and says why, rather than fabricating an
empty declaration -- the same honesty rule `step0_collect._collect_gpu` keeps
for an absent GPU.

NOTHING HERE WRITES INTO `logs/`: `write_declaration_artifact` goes through
`artifacts.write_artifact`, which refuses it (D7-1). The file
`agent_step0_wiring.write_declaration` leaves in `logs/<role>/` is the
handshake-time PRECURSOR, not this artifact -- it cannot be this artifact,
because it is written before move 1 and this one carries the end time.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.security.step0_sign import SignKey, verify_declaration
from pursuit.services.reporting.artifact_declaration_fields import (
    DeclarationArtifactField,
    DeclarationContext,
)
from pursuit.services.reporting.artifacts import (
    ArtifactField,
    artifact_header,
    declaration_filename,
    write_artifact,
)

__all__ = (
    "ENVELOPE_DECLARATION_KEY",
    "PEER_ABSENT_DETAIL",
    "PEER_PRESENT_DETAIL",
    "DeclarationArtifactField",
    "DeclarationContext",
    "build_declaration_artifact",
    "verify_embedded_declarations",
    "write_declaration_artifact",
)

# The key `agent_step0_wiring.declare_step0` (line 72) wraps the signed ten
# Sec5.5 keys under: `{"declaration": declaration, **signature}`. It is an
# inline literal there and `SignKey` has no member for it; naming it here
# rather than editing `step0_sign.py` keeps this plan's git diff over the
# signed path empty (D-71). Folding it onto `SignKey` is deferred to whichever
# plan next opens that file for a real reason (the D7-2 precedent).
ENVELOPE_DECLARATION_KEY = "declaration"

PEER_ABSENT_DETAIL = "peer sent a Step-0 digest only; no declaration content exists to embed"
PEER_PRESENT_DETAIL = "peer's own signed declaration embedded verbatim"

OWN_SIDE = "own"
PEER_SIDE = "peer"


def build_declaration_artifact(
    *,
    game_uid: str,
    game_id: str,
    own_envelope: dict,
    peer_envelope: dict | None,
    context: DeclarationContext,
) -> dict:
    """Wrap both signed envelopes and add the rest of PARAMETERS' content.

    The envelopes are stored BY REFERENCE, unaltered and unreordered: this
    function reads no key inside them and writes none.
    """
    artifact = artifact_header(game_uid=game_uid, game_id=game_id)
    artifact[DeclarationArtifactField.DECLARATIONS] = {
        OWN_SIDE: own_envelope,
        PEER_SIDE: peer_envelope,
    }
    artifact[DeclarationArtifactField.PEER_STATUS] = (
        PEER_ABSENT_DETAIL if peer_envelope is None else PEER_PRESENT_DETAIL
    )
    artifact[DeclarationArtifactField.REPO_URLS] = context.repo_urls
    artifact[DeclarationArtifactField.MCP_SERVER_ADDRESSES] = context.mcp_server_addresses
    artifact[DeclarationArtifactField.TOKEN_CEILING] = context.token_ceiling
    artifact[DeclarationArtifactField.START_TIME] = context.start_time
    artifact[DeclarationArtifactField.END_TIME] = context.end_time
    return artifact


def _verify_envelope(envelope: object, *, secret: str | None) -> bool:
    """Re-verify ONE embedded envelope through `step0_sign.verify_declaration`.

    Every shape check here guards a PEER-SUPPLIED value (`audit.py`'s boundary
    rule): the peer half of this artifact is whatever they sent, so an
    ill-shaped envelope must return False as evidence, never raise a TypeError
    out of `digests_match` and take the artifact writer down with it.
    """
    if not isinstance(envelope, dict):
        return False
    declaration = envelope.get(ENVELOPE_DECLARATION_KEY)
    digest = envelope.get(SignKey.DIGEST)
    hmac_value = envelope.get(SignKey.HMAC)
    if not isinstance(declaration, dict) or not isinstance(digest, str):
        return False
    if hmac_value is not None and not isinstance(hmac_value, str):
        return False
    return verify_declaration(declaration, digest=digest, hmac_value=hmac_value, secret=secret)


def verify_embedded_declarations(artifact: dict, *, secret: str | None) -> dict:
    """`{side: bool}` for every embedded envelope; an absent peer contributes
    no entry, because "not sent" and "did not verify" are different facts."""
    embedded = artifact[DeclarationArtifactField.DECLARATIONS]
    return {
        side: _verify_envelope(envelope, secret=secret)
        for side, envelope in embedded.items()
        if envelope is not None
    }


def write_declaration_artifact(
    artifact_dir: Path | str, artifact: dict, *, secret: str | None
) -> Path:
    """Self-check every embedded signature, THEN write.

    The check is the point: if wrapping perturbed one byte of a signed
    payload, that is D-71's abort arriving in an artifact instead of at a
    handshake, and it must fail here rather than ship. `secret=None` verifies
    the digest only, which is exactly the level `sign_declaration(secret=None)`
    produced -- the argument is required, never defaulted, so no caller
    silently downgrades a signed declaration to a digest-only check.
    """
    unverified = [
        side for side, ok in verify_embedded_declarations(artifact, secret=secret).items() if not ok
    ]
    if unverified:
        raise ValueError(f"embedded Step-0 declaration failed re-verification: {unverified}")
    filename = declaration_filename(artifact[ArtifactField.GAME_ID])
    return write_artifact(artifact_dir, filename, artifact)
