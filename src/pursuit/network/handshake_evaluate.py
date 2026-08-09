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

D-61/D-62 (06-03): unlike CONFIG/SCENT (digests of files kept byte-identical across both
config dirs -- equality is correct there), a Step-0 declaration is inherently PER-AGENT;
two roles' digests are NEVER expected to match. `_step0_present` checks PRESENCE only, not
equality (see its own docstring) -- a literal equality check would abort every real game.
`peer_game_id` is read UNCONDITIONALLY so an abort report still names the peer's proposal.
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
    """The six ways one handshake attempt can resolve (D-46 adds SCENT_MISMATCH,
    D-62 adds STEP0_MISMATCH)."""

    AGREED = "agreed"
    CONFIG_MISMATCH = "config_mismatch"
    SCENT_MISMATCH = "scent_mismatch"
    STEP0_MISMATCH = "step0_mismatch"
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
    peer_game_id: str | None = None
    """D-61: the game_id the PEER proposed, read unconditionally from the
    envelope (present even on a mismatch -- evidence, not just success)."""

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
    remote_digest: str | None = None, peer_role: str | None = None,
    peer_game_id: str | None = None, detail: str = "",
) -> HandshakeResult:
    """Shared HandshakeResult constructor -- one shape, reused by every return path (QUAL-02),
    including handshake.py's own UNREACHABLE branch."""
    return HandshakeResult(
        outcome=outcome, state=machine.state, local_digest=local_digest,
        remote_digest=remote_digest, peer_role=peer_role, peer_game_id=peer_game_id,
        detail=detail,
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
    local_digest: str, remote_digest: str | None, peer_role: str | None,
    peer_game_id: str | None = None, detail: str,
) -> HandshakeResult:
    """Escalate to State.ERROR and emit the D-15 evidence report. A legal HANDSHAKE -> ERROR
    transition is silent in 02-03 (its design note 4) -- this is the one place the abort
    evidence is written; without this call the abort would leave no trace at all."""
    reporter(current=machine.state, target=State.ERROR,
              severity=TransitionSeverity.PROTOCOL_VIOLATION, reason=detail)
    machine.attempt(State.ERROR)
    return build_result(outcome, machine, local_digest, remote_digest=remote_digest,
                         peer_role=peer_role, peer_game_id=peer_game_id, detail=detail)


def _step0_present(envelope: Envelope) -> tuple[bool, str]:
    """D-62, presence-only (see module docstring)."""
    if envelope.payload.get(HandshakeKey.STEP0_DIGEST) is None:
        return False, "step0 digest absent from peer payload"
    return True, "step0 digest present"


def _compare_offer(
    local_digest: str, local_scent_digest: str | None, local_step0_digest: str | None,
    envelope: Envelope, remote_digest: str,
) -> tuple[HandshakeOutcome, bool, str]:
    """Compare config, then -- only for each lock THIS call site opted into -- scent (D-46,
    equality) and step0 (D-62, presence). `local_*_digest is None` skips that check entirely;
    a REMOTE peer can never opt itself out this way, only skip its OWN local check."""
    config_ok, config_detail = compare_named_digest("config", local_digest, remote_digest)
    if not config_ok:
        return HandshakeOutcome.CONFIG_MISMATCH, False, config_detail
    detail = config_detail

    if local_scent_digest is not None:
        remote_scent = envelope.payload.get(HandshakeKey.SCENT_DIGEST)
        scent_ok, scent_detail = compare_named_digest("scent", local_scent_digest, remote_scent)
        if not scent_ok:
            return HandshakeOutcome.SCENT_MISMATCH, False, scent_detail
        detail = f"{detail}; {scent_detail}"

    if local_step0_digest is not None:
        step0_ok, step0_detail = _step0_present(envelope)
        if not step0_ok:
            return HandshakeOutcome.STEP0_MISMATCH, False, step0_detail
        detail = f"{detail}; {step0_detail}"

    return HandshakeOutcome.AGREED, True, detail


def evaluate(
    machine: TurnStateMachine, reporter: TransitionReporter, local_digest: str,
    local_scent_digest: str | None, local_step0_digest: str | None, raw: dict,
) -> HandshakeResult:
    """Shared decode-then-compare step for BOTH directions (QUAL-02): decode the
    counterpart's envelope via 02-02's Envelope.from_dict (never a hand-rolled key check),
    then AGREE or abort via _compare_offer. One call site, so the two directions cannot
    diverge in evidence or escalation policy. `peer_game_id` (D-61) is read UNCONDITIONALLY,
    best-effort, whenever the envelope decoded far enough to have a payload at all."""
    envelope: Envelope | None = None
    try:
        envelope = Envelope.from_dict(raw)
        if envelope.type is not MessageType.HANDSHAKE:
            raise ValueError(f"expected a handshake message, got {envelope.type.value}")
        remote_digest = envelope.payload[HandshakeKey.DIGEST]
    except (KeyError, TypeError, ValueError) as exc:
        peer_game_id = envelope.payload.get(HandshakeKey.GAME_ID) if envelope is not None else None
        return _abort(machine, reporter, outcome=HandshakeOutcome.MALFORMED_REPLY,
                       local_digest=local_digest, remote_digest=None, peer_role=None,
                       peer_game_id=peer_game_id, detail=f"malformed handshake reply: {exc}")

    peer_game_id = envelope.payload.get(HandshakeKey.GAME_ID)
    outcome, ok, detail = _compare_offer(
        local_digest, local_scent_digest, local_step0_digest, envelope, remote_digest,
    )
    if ok:
        return build_result(HandshakeOutcome.AGREED, machine, local_digest,
                             remote_digest=remote_digest, peer_role=envelope.sender,
                             peer_game_id=peer_game_id, detail=detail)
    return _abort(machine, reporter, outcome=outcome, local_digest=local_digest,
                  remote_digest=remote_digest, peer_role=envelope.sender,
                  peer_game_id=peer_game_id,
                  detail=f"{detail}; aborting before move 1 (rule 11/23, D-15/D-46/D-61/D-62)")
