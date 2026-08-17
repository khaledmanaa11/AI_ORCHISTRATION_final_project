"""The two INBOUND QUEUE READERS, split out of `turn_buffer.py` (08-05).

THE SEAM IS THE ONE THE RECORD ALREADY NAMED. Phase-5 deferred item #20 wrote
it down three plans ago -- "`await_move`/`drain_trailing_hint` (the queue
readers) away from `reject_peer_payload`/`log_illegal`/`send_hint`" -- against
`turn_buffer.py` sitting at the 150-code-line gate with nowhere to put #19's
repair. This is that split, taken along that line. Split, never compressed: no
assertion, guard or comment was shortened to make room, and `turn_buffer`
re-exports all three names below so every caller, and every monkeypatch of
`turn_buffer.await_move`, resolves exactly where it did before.

WHY `await_move` NEEDED THE ROOM: DEFERRED ITEM #19, and it is closed here.
This is the `commit_reveal=False` wait (`turn_commit.await_and_respond`'s first
branch, its ONE production caller). It buffered a HINT and returned EVERYTHING
ELSE to `turn_actions.await_opponent_turn`, which handed it straight to
`decode_revealed_action`. The other four `wait_for_*` legs each test the type;
this one did not. MEASURED by 07-18's source-enumerated boundary guard on its
first run -- police, all nine `MessageType` members, one well-formed envelope
each:

    commit_reveal ON   0 of 9 unnamed reasons     <- 05-18 Task 2's fix
    commit_reveal OFF  8 of 9 unnamed reasons, every one
                       'payload has neither direction nor x/y keys'

Eight false declarations against a peer that sent a perfectly legal envelope of
a type we were not waiting for (rules 16/22). Only HINT survived, because HINT
is the one type that branch tested for.

A FINAL_REVEAL IS BUFFERED BEFORE IT IS SKIPPED, and that is not decoration.
This function pulls through `wait_for_opponent` directly rather than through
`turn_commit_pull.next_protocol_message`, so it does not inherit 05-17's
buffering. Adding a type test WITHOUT the buffer would have converted #19 into
05-17's defect on the same path: the peer's published ledger consumed and
destroyed, after which our own audit waits out its whole ladder and declares an
honest peer OPPONENT_UNRESPONSIVE. `test_envelope_boundary_invariant.py`
asserts exactly that ("the peer's published ledger was destroyed"), so the
omission would have failed rather than shipped.
"""

from __future__ import annotations

import asyncio

from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.final_reveal_buffer import record_final_reveal
from pursuit.network.turn_hint_buffer import record_hint
from pursuit.network.verdict import TechnicalWin

__all__ = ["HintProtocolError", "await_move", "drain_trailing_hint"]

#: How many hints this side tolerates while the peer still owes it a move.
#: Unchanged in value from the `for _ in range(2)` bound it replaces -- one
#: hint is tolerated, the second is a protocol violation. Named because the
#: loop is no longer bounded by the same construct that expresses the rule.
MAX_CONSECUTIVE_HINTS = 1


class HintProtocolError(ValueError):
    """A hint violated the Task-3 buffering rules (duplicate/late/an
    unexpected non-hint trailer). The caller turns this into a technical
    loss for the sender, same as any rules-13/14 violation -- never a crash."""


async def await_move(ctx: AgentContext) -> tuple[Envelope | None, TechnicalWin | None]:
    """Bounded wait for the opponent's MOVE envelope, recording (never
    blocking on) any HINT seen first -- a peer that never sends hints must
    still be playable. Raises HintProtocolError on a buffering violation.

    Returns ONLY a MOVE (08-05, deferred #19). Any other type is buffered
    where a later layer wants it and then skipped, and the wait continues --
    the same shape the four `wait_for_*` legs have had since 05-18."""

    # 05-16 (deferred item #10): the touch moved INSIDE the per-attempt
    # closure, exactly as `turn_commit_wait.next_protocol_message`'s
    # `on_attempt` hook does. The post-ladder touch below is kept. The
    # anonymous lambda became a named closure only because a lambda cannot
    # hold two statements -- the awaited call is byte-identical.
    async def _pull() -> object:
        ctx.watchdog.touch()
        return await wait_for_opponent(ctx.runtime.queue, timeout=ctx.net.response_timeout)

    # UNBOUNDED BY CONSTRUCT, BOUNDED IN FACT -- and this is the same trade the
    # other four legs already make. Every iteration costs a full
    # `(retry_count + 1) x response_timeout` ladder, so a peer that stops
    # speaking exhausts it and returns D-13's own MEASURED
    # `opponent_unresponsive` verdict; a peer that keeps sending junk keeps the
    # watchdog touched per bounded attempt, and a wedged loop stops producing
    # attempts so NET-07 still kills us. What is NOT acceptable is the previous
    # behaviour, which terminated promptly by treating the junk as a move.
    hints_since_move = 0
    while True:
        call_outcome = await call_with_retry(
            _pull, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
            backoff=ctx.net.backoff_seconds,
        )
        ctx.watchdog.touch()
        if not call_outcome.succeeded:
            return None, call_outcome.verdict
        queued = call_outcome.value
        envelope = queued if isinstance(queued, Envelope) else Envelope.from_dict(queued)
        if envelope.type is MessageType.MOVE:
            return envelope, None
        if envelope.type is MessageType.HINT:
            record_hint(ctx, envelope.sender, envelope.turn, envelope.payload)
            hints_since_move += 1
            if hints_since_move > MAX_CONSECUTIVE_HINTS:
                raise HintProtocolError("opponent sent two consecutive hints with no move")
            continue
        # The counter is deliberately NOT reset by a skipped foreign type. The
        # rule the message states is "two hints with NO MOVE", not "two hints
        # with nothing in between"; resetting would hand an adversarial peer an
        # unbounded hint channel for the price of one junk envelope per hint.
        if envelope.type is MessageType.FINAL_REVEAL:
            record_final_reveal(ctx, envelope)


def drain_trailing_hint(ctx: AgentContext) -> None:
    """Non-blocking: record a hint ALREADY sitting on the queue right
    behind the move just received; never waits for one that has not
    arrived (Task 3 rule). A non-hint item found here (e.g. a future
    turn's move arriving early) is put straight back untouched -- this
    function only ever consumes an actual HINT."""
    try:
        raw = ctx.runtime.queue.get_nowait()
    except asyncio.QueueEmpty:
        return
    envelope = raw if isinstance(raw, Envelope) else Envelope.from_dict(raw)
    if envelope.type is not MessageType.HINT:
        ctx.runtime.queue.put_nowait(raw)
        return
    record_hint(ctx, envelope.sender, envelope.turn, envelope.payload)
