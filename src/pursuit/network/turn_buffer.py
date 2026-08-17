"""Per-turn helpers split out of turn_actions.py at the 150-code-line gate
(Segal Table 5): the D-11 illegal-transition log line, plus (Phase 4, D-47)
the hint buffer and the bounded wait that tells a MOVE envelope apart from
an optional HINT envelope on the same wire. The joint-turn ACTION buffer
(`record_action`/`maybe_resolve`) is a sibling split, `turn_resolve.py`
(same gate, deviation, 04-12).

Deviation (Rule 3 - blocking, 04-12): `record_hint` now also populates
`ctx.incoming_hints` (a cache that survives `pending_hints`' own
resolve-time clear, so `take_my_turn` can still decode a hint one call
later -- see `network/turn_language.py`). `send_hint` drops 04-04's
`PLACEHOLDER_HINT_TEXT` in favour of the real composed text/intent (D-33's
placeholder-must-be-gone requirement).

05-06 (G3): `record_hint` itself moved to the sibling
`turn_hint_buffer.py` -- this file had no room left (146/150) for the
inbound receipt-logging it gained. It is re-exported below, so
`turn_buffer.record_hint` still resolves for every caller and every
monkeypatch, exactly as `turn_resolve.py`'s own split left this file's
API unchanged.

08-05: the two INBOUND QUEUE READERS -- `await_move` and
`drain_trailing_hint`, plus the `HintProtocolError` the first of them
raises -- moved to the sibling `turn_buffer_queue.py`, along the seam
deferred item #20 named three plans ago. Deferred item #19's repair
(a type test on `await_move`, so the toggle-off wait stops handing a
HANDSHAKE or a GAME_OVER to the move decoder) needed room this file did
not have at 142/150. Re-exported below on the same rule as every split
before it. What is left here is what the name still describes: the
illegal-transition log line, the shared rules-13/14 rejection path, and
the outbound hint push.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import hint_payload, turn_events
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import EnvelopeKey
from pursuit.network.event_log import append_event
from pursuit.network.final_reveal_buffer import record_final_reveal, take_final_reveal
from pursuit.network.hint_payload import Intent
from pursuit.network.orchestrator import AgentContext
from pursuit.network.state_machine import State, TransitionResult
from pursuit.network.turn_buffer_queue import (
    HintProtocolError,
    await_move,
    drain_trailing_hint,
)
from pursuit.network.turn_hint_buffer import record_hint

# Re-exported (05-06): `record_hint` moved to turn_hint_buffer.py at the
# 150-line gate. Named here so `turn_buffer.record_hint` keeps resolving
# for turn_commit_pull's own `turn_buffer.record_hint(...)` reference and
# for every test that monkeypatches it at this module's namespace.
#
# `record_final_reveal`/`take_final_reveal` (05-17) are re-exported for the
# SAME reason and reach this file the same way -- they live in
# `final_reveal_buffer.py` because this one had 11 lines of headroom and
# because their buffer, unlike every other buffer here, is per-GAME rather
# than per-turn. Named here so the pull primitive's two special cases read
# as one rule at its own call site (`turn_buffer.record_hint(...)` beside
# `turn_buffer.record_final_reveal(...)`) rather than as two unrelated
# mechanisms, and so both are monkeypatchable at one namespace.
__all__ = [
    "HintProtocolError",
    "await_move",
    "drain_trailing_hint",
    "log_illegal",
    "record_final_reveal",
    "record_hint",
    "reject_peer_payload",
    "send_hint",
    "take_final_reveal",
]


def log_illegal(ctx: AgentContext, current: State, target: State, result: TransitionResult) -> None:
    """Persist the D-11 illegal-transition evidence. The reporter callback
    already fired synchronously inside ctx.machine.attempt() (NET-05)."""
    append_event(
        ctx.log_path,
        turn_events.illegal_transition_record(
            game_uid=ctx.game_uid,
            turn=ctx.state.turn,
            sender=ctx.role,
            current=current,
            target=target,
            severity=result.severity,
            reason=f"illegal transition {current.value} -> {target.value}",
        ),
    )


def reject_peer_payload(ctx: AgentContext, reason: str) -> Outcome:
    """Shared rules-13/14 rejection path for an illegal or unparseable
    payload from the peer: log evidence, end the game, return
    Outcome.TECHNICAL_LOSS -- never raise out of the caller's handler.
    retries_attempted/timeout_seconds are genuinely 0 here: this is an
    immediate protocol rejection, not a NET-06 retry-ladder exhaustion."""
    append_event(
        ctx.log_path,
        turn_events.technical_win_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role,
            retries_attempted=0, timeout_seconds=0.0, reason=reason,
        ),
    )
    ctx.machine.attempt(State.GAME_OVER)
    return Outcome.TECHNICAL_LOSS


async def send_hint(ctx: AgentContext, turn: int, *, text: str, intent: Intent) -> None:
    """Best-effort hint push for *turn* (D-47). `text`/`intent` are the
    REAL composed deception channel (04-12, replacing 04-04's
    `PLACEHOLDER_HINT_TEXT` outright) -- this function only owns the
    push-and-log mechanics, never the content. A failed push never ends the
    game: the move is the authoritative, required channel (rules 13/14); a
    hint is optional even on our OWN send side, mirroring "a peer that
    sends no hints must still be playable"."""
    hint_envelope = hint_payload.build_hint(text, intent, turn, ctx.role)
    args = {k: v for k, v in hint_envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _push() -> object:
        ctx.watchdog.touch()
        async with ctx.runtime.client() as client:
            return await client.call_tool("receive_hint", args)

    call_outcome = await call_with_retry(
        _push, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    ctx.watchdog.touch()
    if call_outcome.succeeded:
        append_event(
            ctx.log_path,
            turn_events.turn_record(
                game_uid=ctx.game_uid, turn=turn, event="message_sent", sender=ctx.role,
                state_from=State.MY_TURN, state_to=State.WAIT_OPPONENT,
                envelope=hint_envelope.to_dict(),
            ),
        )
