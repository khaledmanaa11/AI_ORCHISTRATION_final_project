"""D-08 game-start handshake: connectivity proof + digest exchange (NET-03, NET-09, D-46).

D-15 / rule 11: any config-digest mismatch aborts BEFORE move 1 -- never a warning or
soft-fail, because a game played on divergent rules produces a result neither side can
defend. D-46 / rule 23: the scent-emission model is locked the SAME way, as a second digest
riding the SAME payload -- this is the first user of the extension point this module always
reserved ("Phase 6 later adds a Step-0 declaration to this same handshake by extending the
envelope payload -- the shape does not change"); Step-0 is Phase 6's next user of it, still
NOT implemented now. An unreachable peer is a DISTINCT, transient outcome the caller retries;
this module makes exactly one attempt per call and owns no timeout, retry count or backoff
(those are 02-07's deadline module, sourced from NetworkParams, wired in by 02-09). Hashing,
canonical JSON, envelope validation and the transition table come from 02-02/02-03 and are
never re-implemented here (QUAL-02).

The wire adapter (HANDSHAKE_TOOL/HANDSHAKE_TURN/HandshakeKey/build_offer/make_client_caller)
lives in handshake_wire.py; the decode/compare/abort internals (HandshakeOutcome/
HandshakeResult/evaluate) live in handshake_evaluate.py -- both split out at the
150-code-line gate and imported back here, so this module stays the single public seam
(perform_handshake, respond_to_handshake) every existing caller already uses unchanged.
"""

from __future__ import annotations

from typing import Protocol

from mcp import McpError

from pursuit.network.envelope import Envelope
from pursuit.network.handshake_evaluate import (
    HandshakeOutcome,  # noqa: F401  (re-exported for callers of THIS module)
    HandshakeResult,
    build_result,
    evaluate,
    not_attempted,
)

# HANDSHAKE_TOOL/HANDSHAKE_TURN/HandshakeKey/make_client_caller are re-exported verbatim for
# callers of THIS module -- unused below except via that re-export (noqa: F401).
from pursuit.network.handshake_wire import (
    HANDSHAKE_TOOL,  # noqa: F401
    HANDSHAKE_TURN,  # noqa: F401
    HandshakeKey,  # noqa: F401
    build_offer,
    make_client_caller,  # noqa: F401
)
from pursuit.network.state_machine import (
    State,
    TransitionReporter,
    TransitionSeverity,
    TurnStateMachine,
)


class HandshakeCaller(Protocol):
    """One outbound attempt. Raises McpError when the peer is unreachable."""

    async def __call__(self, envelope: Envelope) -> dict: ...


async def perform_handshake(
    *, machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str,
    local_role: str, call_peer: HandshakeCaller, local_scent_digest: str | None = None,
) -> HandshakeResult:
    """OUTBOUND handshake half. Exactly one attempt -- no retry, no timeout, no sleep."""
    machine.attempt(State.HANDSHAKE)
    if machine.state is not State.HANDSHAKE:
        return not_attempted(machine, local_digest)

    try:
        offer = build_offer(local_digest, local_role, local_scent_digest=local_scent_digest)
        raw = await call_peer(offer)
    except McpError as exc:
        detail = f"peer unreachable during handshake: {exc}"
        reporter(current=machine.state, target=State.HANDSHAKE,
                  severity=TransitionSeverity.RECOVERABLE, reason=detail)
        return build_result(HandshakeOutcome.UNREACHABLE, machine, local_digest, detail=detail)

    return evaluate(machine, reporter, local_digest, local_scent_digest, raw)


def respond_to_handshake(
    *, machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str,
    local_role: str, incoming: dict, local_scent_digest: str | None = None,
) -> tuple[dict, HandshakeResult]:
    """INBOUND handshake half (NET-03 symmetry). Pure, synchronous, never raises."""
    reply = build_offer(local_digest, local_role, local_scent_digest=local_scent_digest).to_dict()

    machine.attempt(State.HANDSHAKE)
    if machine.state is not State.HANDSHAKE:
        return reply, not_attempted(machine, local_digest)

    return reply, evaluate(machine, reporter, local_digest, local_scent_digest, incoming)
