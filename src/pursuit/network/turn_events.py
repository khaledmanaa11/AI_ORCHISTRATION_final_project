"""Pure D-11 JSONL record builders -- no I/O, no numbers baked in (QUAL-11).

Every builder is dict-in/dict-out: it accepts the evidence as ARGUMENTS and
returns a plain, json.dumps-able dict. Persisting the result (write, flush,
fsync) is 02-04's `append_event` -- never duplicated here.

Two builders (`turn_record`, `illegal_transition_record`) fit 02-04's
`build_event` exactly and reuse it verbatim (QUAL-02): the D-11 stable fields
plus the `details` forward-compat hook already cover their shape. The other
three (`technical_win_record`, `watchdog_incident_record`, `game_over_record`)
need evidence fields at the TOP level of the record (retries_attempted,
idle_seconds, outcome, ...), which `build_event` has no parameter for, so they
add those fields directly onto the dict `build_event` returns -- one call,
zero re-derivation of the timestamp/required-field assembly it already does.

`game_over_record` is the one exception: 02-04's `EventType` (that module is
owned by 02-04 and is not edited by this plan) has no GAME_OVER member, so its
four common fields plus the default ISO-8601 UTC timestamp are assembled
directly here, using `EventField`'s own key names (never a bare string).
"""

from __future__ import annotations

from datetime import datetime, timezone

from pursuit.constants import Outcome
from pursuit.network.event_log import EventField, EventType, build_event
from pursuit.network.state_machine import State, TransitionSeverity


def turn_record(
    *,
    game_uid: str,
    turn: int,
    event: str,
    sender: str,
    state_from: State,
    state_to: State,
    envelope: dict,
) -> dict:
    """A message_sent/message_received turn record (D-11, D-14)."""
    return build_event(
        game_uid=game_uid,
        turn=turn,
        event=EventType(event),
        sender=sender,
        state_from=state_from.value,
        state_to=state_to.value,
        envelope=envelope,
    )


def illegal_transition_record(
    *,
    game_uid: str,
    turn: int,
    sender: str,
    current: State,
    target: State,
    severity: TransitionSeverity,
    reason: str,
) -> dict:
    """The NET-05 sink record: severity and reason land in `details`, 02-04's
    forward-compatibility hook, so the stable fields never reshape."""
    return build_event(
        game_uid=game_uid,
        turn=turn,
        event=EventType.ILLEGAL_TRANSITION,
        sender=sender,
        state_from=current.value,
        state_to=target.value,
        details={"severity": severity.value, "reason": reason},
    )


def technical_win_record(
    *,
    game_uid: str,
    turn: int,
    sender: str,
    retries_attempted: int,
    timeout_seconds: float,
    reason: str,
) -> dict:
    """D-13, rules 16/22: retries_attempted is what actually ran, never a
    constant or the configured maximum."""
    record = build_event(game_uid=game_uid, turn=turn, event=EventType.TECHNICAL_WIN, sender=sender)
    record.update(
        retries_attempted=retries_attempted, timeout_seconds=timeout_seconds, reason=reason
    )
    return record


def watchdog_incident_record(
    *, game_uid: str, turn: int, sender: str, idle_seconds: float, threshold_seconds: float
) -> dict:
    """NET-07: a freeze incident, self-contained -- no external lookup needed."""
    record = build_event(
        game_uid=game_uid, turn=turn, event=EventType.WATCHDOG_INCIDENT, sender=sender
    )
    record.update(idle_seconds=idle_seconds, threshold_seconds=threshold_seconds)
    return record


def game_over_record(*, game_uid: str, turn: int, sender: str, outcome: Outcome) -> dict:
    """The terminal D-11 record. See module docstring for why this one
    builder cannot reuse `build_event` (no matching EventType member)."""
    return {
        EventField.GAME_UID: game_uid,
        EventField.TURN: turn,
        EventField.EVENT: "game_over",
        EventField.SENDER: sender,
        EventField.TIMESTAMP: datetime.now(timezone.utc).isoformat(),
        "outcome": outcome.value,
    }


def language_turn_record(
    *,
    game_uid: str,
    turn: int,
    sender: str,
    regime: str,
    belief_entropy: float | None,
    belief_argmax: tuple | None,
    reliability: float | None,
    token_spend: dict,
    incoming: dict,
    outgoing: dict,
) -> dict:
    """The Task-3 per-turn language snapshot: the whole language channel,
    once per turn, in one record (rules 8-9: every field is what THIS peer
    believed or observed -- never a ground-truth board). No matching
    `EventType` member exists either (same reason as `game_over_record`
    above -- that module is owned by 02-04 and not edited by this plan), so
    the four common fields are assembled directly here.

    `belief_entropy`/`belief_argmax`/`reliability` are None when
    `belief.enabled` is false this game -- an honest "not run", never a
    fabricated number. `incoming`/`outgoing` are plain dicts (text, decode
    outcome/reason, or text+intent) built by `turn_language.py`."""
    return {
        EventField.GAME_UID: game_uid,
        EventField.TURN: turn,
        EventField.EVENT: "language_turn",
        EventField.SENDER: sender,
        EventField.TIMESTAMP: datetime.now(timezone.utc).isoformat(),
        "regime": regime,
        "belief_entropy": belief_entropy,
        "belief_argmax": list(belief_argmax) if belief_argmax is not None else None,
        "reliability": reliability,
        "token_spend": token_spend,
        "incoming_hint": incoming,
        "outgoing_hint": outgoing,
    }
