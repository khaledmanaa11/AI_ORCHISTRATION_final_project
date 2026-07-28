"""Per-agent turn state machine (NET-04/NET-05, D-09/D-10/D-12).

State is one of six D-09 members (INIT, HANDSHAKE, MY_TURN, WAIT_OPPONENT,
GAME_OVER, ERROR). Phase 6 adds commit-reveal sub-states additively — new
State members plus new rows/edges in ALLOWED_TRANSITIONS, never a signature
change here.

Legality is decided by ALLOWED_TRANSITIONS, an explicit module-level dict
(D-12) — no FSM library is imported anywhere in this module.

Rule 5 / NET-05 / D-10: every illegal transition attempt is reported to the
injected `reporter`, never silently dropped. A RECOVERABLE attempt (duplicate
message, out-of-order retry) leaves the machine on its previous state so the
game keeps running; a PROTOCOL_VIOLATION escalates to State.ERROR and ends
the game.

`reporter` is injected as a parameter, not imported, so this module has no
dependency on 02-04's reporting/audit-trail module — that keeps 02-03 and
02-04 safe to build in the same wave, and makes the NET-05 report path
trivial to test with a fake reporter instead of filesystem inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class State(Enum):
    """The six D-09 states. Phase 6 inserts commit-reveal sub-states additively."""

    INIT = "init"
    HANDSHAKE = "handshake"
    MY_TURN = "my_turn"
    WAIT_OPPONENT = "wait_opponent"
    GAME_OVER = "game_over"
    ERROR = "error"


ALLOWED_TRANSITIONS: dict[State, frozenset[State]] = {
    State.INIT: frozenset({State.HANDSHAKE, State.ERROR}),
    State.HANDSHAKE: frozenset({State.MY_TURN, State.WAIT_OPPONENT, State.ERROR}),
    State.MY_TURN: frozenset({State.WAIT_OPPONENT, State.GAME_OVER, State.ERROR}),
    State.WAIT_OPPONENT: frozenset({State.MY_TURN, State.GAME_OVER, State.ERROR}),
    State.GAME_OVER: frozenset(),
    State.ERROR: frozenset(),
}
"""Explicit legal-transition table (D-12). Every State member is a key, so no
lookup in transition() can raise KeyError. GAME_OVER and ERROR are terminal —
both map to the empty frozenset."""

TERMINAL_STATES: frozenset[State] = frozenset({State.GAME_OVER, State.ERROR})
"""States with no outgoing edges. TransitionResult.continues is derived from
this set, not from a hand-repeated pair of comparisons (QUAL-02)."""


class TransitionSeverity(Enum):
    """Classification of an illegal transition attempt (D-10)."""

    RECOVERABLE = "recoverable"
    """Duplicate message / out-of-order retry — the game continues."""

    PROTOCOL_VIOLATION = "protocol_violation"
    """A real protocol violation — escalates the machine to State.ERROR."""


RECOVERABLE_ATTEMPTS: frozenset[tuple[State, State]] = frozenset(
    {
        # Self-transitions: the peer re-delivered a message we already applied.
        (State.HANDSHAKE, State.HANDSHAKE),
        (State.MY_TURN, State.MY_TURN),
        (State.WAIT_OPPONENT, State.WAIT_OPPONENT),
        (State.GAME_OVER, State.GAME_OVER),
        # A late/duplicate handshake arriving after we already advanced.
        (State.MY_TURN, State.HANDSHAKE),
        (State.WAIT_OPPONENT, State.HANDSHAKE),
    }
)
"""Explicit allow-list of *illegal but benign* (current, target) pairs
(D-10). Everything illegal and not in this set is a PROTOCOL_VIOLATION —
including any attempt out of ERROR and any backwards jump to INIT."""


class TransitionReporter(Protocol):
    """Injected reporting sink. 02-04's audit-trail module adapts to this
    shape; 02-09 wires the two together when it constructs a
    TurnStateMachine."""

    def __call__(
        self,
        *,
        current: State,
        target: State,
        severity: TransitionSeverity,
        reason: str,
    ) -> None:
        """Record one illegal transition attempt. Called on every rejection,
        never on an accepted transition."""
        ...


@dataclass(frozen=True)
class TransitionResult:
    """Outcome of a single transition() call."""

    state: State
    """The state the machine is in AFTER the attempt."""

    accepted: bool
    """True only when the requested transition applied."""

    severity: TransitionSeverity | None
    """None when accepted; set on every rejection."""

    @property
    def continues(self) -> bool:
        """True when the caller may keep playing (state is not terminal)."""
        return self.state not in TERMINAL_STATES


def classify_severity(current: State, target: State) -> TransitionSeverity:
    """Classify an illegal (current, target) attempt by table lookup.

    RECOVERABLE if the pair is in RECOVERABLE_ATTEMPTS, else
    PROTOCOL_VIOLATION. Never called for a legal transition.
    """
    if (current, target) in RECOVERABLE_ATTEMPTS:
        return TransitionSeverity.RECOVERABLE
    return TransitionSeverity.PROTOCOL_VIOLATION


def transition(
    current: State, target: State, *, reporter: TransitionReporter
) -> TransitionResult:
    """Attempt to move from `current` to `target`.

    Legal transitions apply silently (severity-based logging of legal moves
    is 02-09's job via the event log, not this module's). Every illegal
    attempt is reported to `reporter` before the outcome is computed, so no
    return path can skip the report (NET-05, rule 5). A RECOVERABLE illegal
    attempt leaves the machine on `current`; a PROTOCOL_VIOLATION escalates
    it to State.ERROR.
    """
    if target in ALLOWED_TRANSITIONS[current]:
        return TransitionResult(state=target, accepted=True, severity=None)

    severity = classify_severity(current, target)
    reporter(
        current=current,
        target=target,
        severity=severity,
        reason=f"illegal transition {current.value} -> {target.value}",
    )
    resulting = State.ERROR if severity is TransitionSeverity.PROTOCOL_VIOLATION else current
    return TransitionResult(state=resulting, accepted=False, severity=severity)


class TurnStateMachine:
    """Per-agent instance. Holds THIS agent's state only (NET-02) — no
    module-level mutable current-state variable, so two machines in one
    interpreter never observe each other's state."""

    def __init__(self, reporter: TransitionReporter, *, initial: State = State.INIT) -> None:
        """Store the injected reporter and set the starting state on this
        instance."""
        self._reporter = reporter
        self._state = initial

    @property
    def state(self) -> State:
        """This agent's current state."""
        return self._state

    def attempt(self, target: State) -> TransitionResult:
        """Attempt to move this machine to `target`, updating instance state
        to match the result (a PROTOCOL_VIOLATION escalation sticks; a
        RECOVERABLE rejection leaves the state unchanged)."""
        result = transition(self._state, target, reporter=self._reporter)
        self._state = result.state
        return result
