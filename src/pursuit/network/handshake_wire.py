"""D-06 wire adapter for the D-08 handshake: envelope shape + the fastmcp.Client bridge.

Split from handshake.py at the 150-code-line gate (Segal Table 5): this module holds only
envelope construction and transport adaptation. Every abort/comparison decision --
perform_handshake, respond_to_handshake, _abort -- stays in handshake.py (policy vs. wire,
QUAL-02). This module depends only on 02-02's envelope.py, never on handshake.py itself, so
handshake.py can import from here with no circular import.

D-46: the payload gains a SECOND key, SCENT_DIGEST, alongside the Phase-2 DIGEST -- the
scent-emission-model lock (rule 23) riding the same envelope this module's own docstring
always reserved for exactly this kind of extension (see handshake.py's module docstring).
`local_scent_digest` defaults to None so a call site not yet migrated to send one (04-12
wires the live agent path) still builds a legal, config-only offer: the key is OMITTED, not
sent as null, so that offer reads identically to an old-style peer's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType

if TYPE_CHECKING:
    from fastmcp import Client

HANDSHAKE_TOOL = "handshake"
HANDSHAKE_TURN = 0  # the ONLY numeric literal in this file: structural pre-move-1 turn index


class HandshakeKey:
    """Payload key constants -- house pattern, mirrors ConfigKey / EnvelopeKey."""

    DIGEST = "digest"
    SCENT_DIGEST = "scent_digest"


def build_offer(
    local_digest: str, local_role: str, *, local_scent_digest: str | None = None
) -> Envelope:
    """Build this agent's outbound/reply handshake envelope (D-06, D-46).

    The payload carries exactly the two documented keys when a scent digest
    is given, and only DIGEST when it is not -- never a null placeholder.
    """
    payload = {HandshakeKey.DIGEST: local_digest}
    if local_scent_digest is not None:
        payload[HandshakeKey.SCENT_DIGEST] = local_scent_digest
    return Envelope(
        type=MessageType.HANDSHAKE, turn=HANDSHAKE_TURN, sender=local_role, payload=payload,
    )


def make_client_caller(client: Client):
    """Adapt 02-06's fastmcp.Client into a HandshakeCaller (see handshake.py). Drops the
    envelope TYPE key -- the tool has no `type` parameter and HANDSHAKE_TOOL already names
    the kind. Nothing is caught here: McpError must reach perform_handshake unfiltered so it
    alone classifies unreachability.
    """

    async def _call(envelope: Envelope) -> dict:
        args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}
        result = await client.call_tool(HANDSHAKE_TOOL, args)
        return result.data

    return _call
