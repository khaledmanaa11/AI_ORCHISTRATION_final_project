"""Decode-then-compare-then-abort machinery for the D-08 handshake (D-15, D-46, rule 11/23).

Split from handshake.py at the 150-code-line gate (Segal Table 5), the same way
handshake_wire.py already split out envelope/transport concerns: this module holds
HandshakeOutcome/HandshakeResult and every internal step that decodes a peer's reply,
compares it against what we sent, and escalates the state machine on a mismatch.
handshake.py owns only the two PUBLIC entry points (perform_handshake,
respond_to_handshake) and imports everything here back, so external callers keep doing
`from pursuit.network.handshake import HandshakeOutcome` unchanged (QUAL-02: one shape,
reused, never duplicated). No import of handshake.py itself, so handshake.py can import
from here with no circular import -- the same one-directional shape handshake_wire.py uses.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pursuit.network.config_hash import compare_named_digest
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.handshake_wire import HandshakeKey
from pursuit.network.state_machine import (
    State,
    TransitionReporter,
    TransitionSeverity,
    TurnStateMachine,
)


class HandshakeOutcome(Enum):
    """The five ways one handshake attempt can resolve (D-46 adds SCENT_MISMATCH)."""

    AGREED = "agreed"
    CONFIG_MISMATCH = "config_mismatch"
    SCENT_MISMATCH = "scent_mismatch"
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


def build_result(
    outcome: HandshakeOutcome, machine: TurnStateMachine, local_digest: str, *,
    remote_digest: str | None = None, peer_role: str | None = None, detail: str = "",
) -> HandshakeResult:
    """Shared HandshakeResult constructor -- one shape, reused by every return path (QUAL-02),
    including handshake.py's own UNREACHABLE branch."""
    return HandshakeResult(
        outcome=outcome, state=machine.state, local_digest=local_digest,
        remote_digest=remote_digest, peer_role=peer_role, detail=detail,
    )


def not_attempted(machine: TurnStateMachine, local_digest: str) -> HandshakeResult:
    """The machine already left State.HANDSHAKE elsewhere in the protocol (a rejected
    duplicate, already reported by 02-03's own machinery) -- no peer contact is made here."""
    return build_result(
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
    return build_result(outcome, machine, local_digest, remote_digest=remote_digest,
                         peer_role=peer_role, detail=detail)


def _compare_offer(
    local_digest: str, local_scent_digest: str | None, envelope: Envelope, remote_digest: str,
) -> tuple[HandshakeOutcome, bool, str]:
    """Compare config, then -- only if THIS call site has opted into the scent lock -- scent
    (D-46, rule 23). One place both directions share, so config and scent are never checked
    with diverging logic. `local_scent_digest is None` means this call has not opted in
    (pre-04-12 callers): the config check alone still runs; a REMOTE peer can never opt
    itself out this way, only skip its OWN local check."""
    config_ok, config_detail = compare_named_digest("config", local_digest, remote_digest)
    if not config_ok:
        return HandshakeOutcome.CONFIG_MISMATCH, False, config_detail
    if local_scent_digest is None:
        return HandshakeOutcome.AGREED, True, config_detail
    remote_scent = envelope.payload.get(HandshakeKey.SCENT_DIGEST)
    scent_ok, scent_detail = compare_named_digest("scent", local_scent_digest, remote_scent)
    if not scent_ok:
        return HandshakeOutcome.SCENT_MISMATCH, False, scent_detail
    return HandshakeOutcome.AGREED, True, f"{config_detail}; {scent_detail}"


def evaluate(
    machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str,
    local_scent_digest: str | None, raw: dict,
) -> HandshakeResult:
    """Shared decode-then-compare step for BOTH directions (QUAL-02): decode the
    counterpart's envelope via 02-02's Envelope.from_dict (never a hand-rolled key check),
    then AGREE or abort via _compare_offer. One call site, so the two directions cannot
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

    outcome, ok, detail = _compare_offer(local_digest, local_scent_digest, envelope, remote_digest)
    if ok:
        return build_result(HandshakeOutcome.AGREED, machine, local_digest,
                             remote_digest=remote_digest, peer_role=envelope.sender, detail=detail)
    return _abort(machine, reporter, outcome=outcome, local_digest=local_digest,
                  remote_digest=remote_digest, peer_role=envelope.sender,
                  detail=f"{detail}; aborting before move 1 (rule 11/23, D-15/D-46)")
