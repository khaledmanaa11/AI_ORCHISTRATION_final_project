"""D-05 tool surface: real signatures, stub bodies, later phases fill behavior.

Nine `@mcp.tool` handlers — `handshake`, `receive_move`, `receive_barrier`,
`game_over`, `receive_hint` (D-47), `receive_commit`, `receive_ack`,
`receive_reveal`, `receive_final_reveal` (D-58, Phase 6) — attach to a
server via `register_tools(mcp, queue)`. Every handler is `async def` deliberately (RESEARCH Pitfall 2): FastMCP 3.4.5
dispatches a plain `def` tool body to a worker threadpool via
`call_sync_fn_in_threadpool`, which cannot safely touch a main-loop
`asyncio.Queue`. Every handler enqueues and returns immediately (D-07): a
handler that blocked waiting on this agent's own outgoing call would
deadlock both peers.

The `handshake` tool additionally accepts an injectable `handshake_handler`
seam (NET-09). With none supplied it keeps the generic D-05 stub ack, the
behaviour 02-06's own tests and 02-08's fake-peer tests are written against.
When supplied, the handshake tool awaits the handler and returns its reply
VERBATIM instead — this is how 02-09 puts 02-08's `respond_to_handshake`
behind the real tool without editing this file. The seam is load-bearing:
the generic ack `{status, type, turn}` carries no sender/payload/digest and
cannot decode as an Envelope, so an unwired `handshake` tool would make every
real peer-to-peer handshake abort to `State.ERROR` before move 1 (NET-09,
rule 11).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType

ACK_STATUS = "ack"


class AckKey:
    """Structural key names for the generic D-05 stub ack dict."""

    STATUS = "status"
    TYPE = "type"
    TURN = "turn"


HandshakeHandler = Callable[[int, str, dict], Awaitable[dict]]


async def _accept(
    queue: asyncio.Queue, message_type: MessageType, turn: int, sender: str, payload: dict
) -> dict:
    """Decode into an Envelope, enqueue, and ack immediately (D-06, D-07).

    The try/except is a TRANSLATION, not a rescue: `Envelope.from_dict`
    raises builtin TypeError/KeyError/ValueError, and FastMCP masks
    unexpected internal exceptions before they reach the caller. Re-raising
    as `ToolError` gives the opponent a descriptive protocol error instead
    of an opaque internal error. Nothing is enqueued before the decode
    succeeds — a half-decoded message must never reach the orchestrator.
    """
    try:
        envelope = Envelope.from_dict(
            {
                EnvelopeKey.TYPE: message_type.value,
                EnvelopeKey.TURN: turn,
                EnvelopeKey.SENDER: sender,
                EnvelopeKey.PAYLOAD: payload,
            }
        )
    except (TypeError, KeyError, ValueError) as exc:
        raise ToolError(f"malformed {message_type.value} envelope: {exc}") from exc
    await queue.put(envelope)
    return {AckKey.STATUS: ACK_STATUS, AckKey.TYPE: message_type.value, AckKey.TURN: turn}


def register_tools(
    mcp: FastMCP,
    queue: asyncio.Queue,
    *,
    handshake_handler: HandshakeHandler | None = None,
) -> None:
    """Attach the four D-05 handlers to `mcp`, closing over `queue`.

    Takes the server as an argument — there is no module-level FastMCP here
    (NET-02). All four wire signatures are identical on purpose: one
    envelope shape for every message kind (D-06). Later phases fill in
    bodies; they never reshape this signature or add a second tool.
    """

    @mcp.tool
    async def handshake(turn: int, sender: str, payload: dict) -> dict:
        """Connectivity + config-hash exchange (D-08).

        No handler injected -> the generic D-05 stub body (decode, enqueue,
        ack). Handler injected -> the handler's reply is returned VERBATIM,
        and nothing is enqueued: the handshake is answered inline, not
        handed to the turn loop.
        """
        if handshake_handler is None:
            return await _accept(queue, MessageType.HANDSHAKE, turn, sender, payload)
        return await handshake_handler(turn, sender, payload)

    @mcp.tool
    async def receive_move(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's move envelope; payload carries {x, y} in Phase 2 (D-06)."""
        return await _accept(queue, MessageType.MOVE, turn, sender, payload)

    @mcp.tool
    async def receive_barrier(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's barrier declaration. Phase 2: stub."""
        return await _accept(queue, MessageType.BARRIER, turn, sender, payload)

    @mcp.tool
    async def game_over(turn: int, sender: str, payload: dict) -> dict:
        """End-of-game notification. Phase 2: stub."""
        return await _accept(queue, MessageType.GAME_OVER, turn, sender, payload)

    @mcp.tool
    async def receive_hint(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's hint envelope; payload carries {text, intent, turn}
        (D-47). Semantic judgement of the hint belongs to the strategy
        layer, never here -- decode, enqueue, ack, exactly like the other
        four, never blocking on the game loop."""
        return await _accept(queue, MessageType.HINT, turn, sender, payload)

    @mcp.tool
    async def receive_commit(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's Commit-phase hash-only envelope; payload carries
        {h_commit} (D-58, D-59). No hash/legality validation at this layer
        -- decode, enqueue, ack, exactly like every other handler."""
        return await _accept(queue, MessageType.COMMIT, turn, sender, payload)

    @mcp.tool
    async def receive_ack(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's Acknowledge-phase envelope; payload carries
        {h_commit}, naming which commit is being acknowledged (D-58)."""
        return await _accept(queue, MessageType.ACK, turn, sender, payload)

    @mcp.tool
    async def receive_reveal(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's Reveal-phase envelope; payload carries the D-59/D-66
        composite action dict {move, barrier}. The nonce never rides this
        message (SEC-04, rule 18) -- it stays local until FINAL_REVEAL."""
        return await _accept(queue, MessageType.REVEAL, turn, sender, payload)

    @mcp.tool
    async def receive_final_reveal(turn: int, sender: str, payload: dict) -> dict:
        """Opponent's end-of-game Final-Reveal/Audit envelope (D-67, 06-03's
        job to populate/consume). Registered now so the wire surface is
        complete for this phase's gate; the audit body lands in 06-03."""
        return await _accept(queue, MessageType.FINAL_REVEAL, turn, sender, payload)
