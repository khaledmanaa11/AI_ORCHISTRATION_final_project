"""D-08 game-start handshake: connectivity proof + config-digest exchange (NET-03, NET-09).

D-15 / rule 11: any digest mismatch aborts BEFORE move 1 -- never a warning or soft-fail,
because a game played on divergent rules produces a result neither side can defend. An
unreachable peer is a DISTINCT, transient outcome the caller retries; this module makes
exactly one attempt per call and owns no timeout, retry count or backoff (those are 02-07's
deadline module, sourced from NetworkParams, wired in by 02-09). Hashing, canonical JSON,
envelope validation and the transition table come from 02-02/02-03 and are never
re-implemented here (QUAL-02). Phase 6 later adds a Step-0 declaration to this same
handshake by extending the envelope payload -- the shape does not change, and Step-0 is
NOT implemented now.

The wire adapter (HANDSHAKE_TOOL/HANDSHAKE_TURN/HandshakeKey/build_offer/make_client_caller)
lives in handshake_wire.py, split out at the 150-code-line gate; its own docstring explains
why the constants moved there too (avoids a circular import back to this module).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from mcp import McpError

from pursuit.network.config_hash import digests_match
from pursuit.network.envelope import Envelope, MessageType

# HANDSHAKE_TOOL/HANDSHAKE_TURN/make_client_caller are re-exported verbatim for callers of
# THIS module -- unused below except via that re-export (noqa: F401), because they are
# consumed only by handshake_wire.py's own build_offer/make_client_caller internals.
from pursuit.network.handshake_wire import (
    HANDSHAKE_TOOL,  # noqa: F401
    HANDSHAKE_TURN,  # noqa: F401
    HandshakeKey,
    build_offer,
    make_client_caller,  # noqa: F401
)
from pursuit.network.state_machine import (
    State,
    TransitionReporter,
    TransitionSeverity,
    TurnStateMachine,
)


class HandshakeOutcome(Enum):
    """The four ways one handshake attempt can resolve."""

    AGREED = "agreed"
    CONFIG_MISMATCH = "config_mismatch"
    UNREACHABLE = "unreachable"
    MALFORMED_REPLY = "malformed_reply"


@dataclass(frozen=True)
class HandshakeResult:
    """Outcome of one perform_handshake / respond_to_handshake attempt."""

    outcome: HandshakeOutcome
    state: State
    local_digest: str
    remote_digest: str | None
    peer_role: str | None
    detail: str

    @property
    def agreed(self) -> bool:
        """True only when the outcome is AGREED."""
        return self.outcome is HandshakeOutcome.AGREED

    @property
    def aborted(self) -> bool:
        """True when this attempt escalated the machine to State.ERROR."""
        return self.state is State.ERROR


class HandshakeCaller(Protocol):
    """One outbound attempt. Raises McpError when the peer is unreachable."""

    async def __call__(self, envelope: Envelope) -> dict: ...


def _result(
    outcome: HandshakeOutcome, machine: TurnStateMachine, local_digest: str, *,
    remote_digest: str | None = None, peer_role: str | None = None, detail: str = "",
) -> HandshakeResult:
    """Shared HandshakeResult constructor -- one shape, reused by every return path (QUAL-02)."""
    return HandshakeResult(
        outcome=outcome, state=machine.state, local_digest=local_digest,
        remote_digest=remote_digest, peer_role=peer_role, detail=detail,
    )


def _mismatch_detail(local_digest: str, remote_digest: str) -> str:
    """The design-note-6 evidence line: both digests, no accusation -- built ONCE here and
    reused by both directions so they cannot diverge (QUAL-02)."""
    return (
        f"config digest mismatch: local={local_digest} remote={remote_digest}; "
        "aborting before move 1 (rule 11, D-15)"
    )


def _not_attempted(machine: TurnStateMachine, local_digest: str) -> HandshakeResult:
    """The machine already left State.HANDSHAKE elsewhere in the protocol (a rejected
    duplicate, already reported by 02-03's own machinery) -- no peer contact is made here."""
    return _result(
        HandshakeOutcome.UNREACHABLE, machine, local_digest,
        detail=f"handshake not attempted: machine is in {machine.state.value}",
    )


def _abort(
    machine: TurnStateMachine, reporter: TransitionReporter, *, outcome: HandshakeOutcome,
    local_digest: str, remote_digest: str | None, peer_role: str | None, detail: str,
) -> HandshakeResult:
    """Escalate to State.ERROR and emit the D-15 evidence report. A legal HANDSHAKE -> ERROR
    transition is silent in 02-03 (its design note 4) -- this is the one place the abort
    evidence is written; without this call the abort would leave no trace at all."""
    reporter(current=machine.state, target=State.ERROR,
              severity=TransitionSeverity.PROTOCOL_VIOLATION, reason=detail)
    machine.attempt(State.ERROR)
    return _result(outcome, machine, local_digest, remote_digest=remote_digest,
                    peer_role=peer_role, detail=detail)


def _evaluate(
    machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str, raw: dict,
) -> HandshakeResult:
    """Shared decode-then-compare step for BOTH directions (QUAL-02): decode the
    counterpart's envelope via 02-02's Envelope.from_dict (never a hand-rolled key check),
    then AGREE or _abort on mismatch/garbage. One call site, so the two directions cannot
    diverge in evidence or escalation policy."""
    try:
        envelope = Envelope.from_dict(raw)
        if envelope.type is not MessageType.HANDSHAKE:
            raise ValueError(f"expected a handshake message, got {envelope.type.value}")
        remote_digest = envelope.payload[HandshakeKey.DIGEST]
    except (KeyError, TypeError, ValueError) as exc:
        return _abort(machine, reporter, outcome=HandshakeOutcome.MALFORMED_REPLY,
                       local_digest=local_digest, remote_digest=None, peer_role=None,
                       detail=f"malformed handshake reply: {exc}")
    if digests_match(local_digest, remote_digest):
        return _result(HandshakeOutcome.AGREED, machine, local_digest,
                        remote_digest=remote_digest, peer_role=envelope.sender,
                        detail="config digests agree")
    return _abort(machine, reporter, outcome=HandshakeOutcome.CONFIG_MISMATCH,
                  local_digest=local_digest, remote_digest=remote_digest, peer_role=envelope.sender,
                  detail=_mismatch_detail(local_digest, remote_digest))


async def perform_handshake(
    *, machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str,
    local_role: str, call_peer: HandshakeCaller,
) -> HandshakeResult:
    """OUTBOUND handshake half. Exactly one attempt -- no retry, no timeout, no sleep."""
    machine.attempt(State.HANDSHAKE)
    if machine.state is not State.HANDSHAKE:
        return _not_attempted(machine, local_digest)

    try:
        raw = await call_peer(build_offer(local_digest, local_role))
    except McpError as exc:
        detail = f"peer unreachable during handshake: {exc}"
        reporter(current=machine.state, target=State.HANDSHAKE,
                  severity=TransitionSeverity.RECOVERABLE, reason=detail)
        return _result(HandshakeOutcome.UNREACHABLE, machine, local_digest, detail=detail)

    return _evaluate(machine, reporter, local_digest, raw)


def respond_to_handshake(
    *, machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str,
    local_role: str, incoming: dict,
) -> tuple[dict, HandshakeResult]:
    """INBOUND handshake half (NET-03 symmetry). Pure, synchronous, never raises."""
    reply = build_offer(local_digest, local_role).to_dict()

    machine.attempt(State.HANDSHAKE)
    if machine.state is not State.HANDSHAKE:
        return reply, _not_attempted(machine, local_digest)

    return reply, _evaluate(machine, reporter, local_digest, incoming)
