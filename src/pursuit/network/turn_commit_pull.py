"""`next_protocol_message` -- the D-58 pull primitive, split out of
`turn_commit_wait.py` at the 150-code-line gate (Segal Table 5).

Deferred item #11 named this exact seam three plans ago: "the four
`wait_for_*` legs (policy) away from `next_protocol_message` (the
primitive) -- the same policy-vs-mechanism split `handshake.py`/
`handshake_wire.py` already uses". 05-17 is the change that needed the
room. That file sat at 145/150 and this plan adds both the FINAL_REVEAL
routing below and the docstring corrections that routing forces on three
of the legs; neither fits in place. Split, never compressed --
`turn_commit_wait` re-exports this name, so `turn_commit.py`,
`agent_audit_exchange.py`, the gate scripts and the test suite all resolve
it exactly where they did before.

TWO message types are special-cased here, and they are special-cased
DIFFERENTLY on purpose:

- a HINT is buffered and SKIPPED. No caller of this primitive ever wants
  one; `turn_language` collects it later out of `ctx.pending_hints` /
  `ctx.incoming_hints`, and a peer that sends none must still be playable.
- a FINAL_REVEAL is buffered and STILL RETURNED. Exactly one caller wants
  it -- `agent_audit_exchange.receive_final_reveal` -- so skipping it here
  would starve that caller of the very envelope it is waiting for, cost it
  a whole `(retry_count + 1) x response_timeout` ladder, and end in the
  same false accusation through a different door. Buffering is what makes
  the four `wait_for_*` legs' tolerated-jitter DROP harmless again: a leg
  may still discard the arrival, because the ledger it carried is already
  safe in `ctx.commit_state.early_final_reveal` and the audit consults
  that buffer BEFORE it waits (05-17).

That asymmetry is the whole fix, and it is ROUTING, not timing: no
timeout, retry count or backoff moves, and none may (CLAUDE.md rule 1 --
every number lives in `docs/PARAMETERS.md`). A peer's published ledger is
now never lost, whichever layer it lands in, which is the invariant 05-15
established one layer further in (`receive_final_reveal` checking WHICH
envelope it got) and this file completes.
"""

from __future__ import annotations

from collections.abc import Callable

from pursuit.network import turn_buffer
from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.verdict import TechnicalWin

__all__ = ["next_protocol_message"]


async def next_protocol_message(
    ctx: AgentContext, *, on_attempt: Callable[[], None] | None = None,
) -> tuple[Envelope | None, TechnicalWin | None]:
    """Pull one non-HINT envelope off the wire, tolerant of an interleaved
    HINT (buffered via `turn_buffer.record_hint`, never blocking) -- the
    same primitive `turn_buffer.await_move` uses, generalized to any type
    (D-58). Bounded per-pull by `call_with_retry`'s existing NetworkParams
    ladder; a silent opponent eventually returns a `TechnicalWin` verdict
    here (never raises).

    A FINAL_REVEAL is RECORDED into `ctx.commit_state.early_final_reveal`
    on the way past and then returned like anything else (05-17). Callers
    keep their own drop policy: what changed is that a caller dropping this
    particular type no longer destroys the peer's published ledger, so
    `agent_audit_wiring`'s "a push that landed proves the silence is
    theirs" premise is true again instead of being a silence we
    manufactured. Every OTHER duplicate/unexpected type is still the
    caller's own concern to drop, and nothing about that policy moved."""
    # `on_attempt` runs once at the START of each BOUNDED attempt.
    # Introduced by 05-13 (05-UAT.md G6) for the audit path and defaulted to
    # None so the turn loop stayed byte-identical; 05-16 (deferred item #10)
    # is what makes EVERY caller pass `ctx.watchdog.touch` -- the four
    # `wait_for_*` legs and `agent_audit_exchange.receive_final_reveal`
    # alike. The default survives only as the signature's neutral element;
    # there is no caller that wants an unmarked ladder.
    #
    # Without it the WHOLE ladder (retry_count+1 attempts x response_timeout
    # plus backoffs = 135 s at the shipped Table-19 values) runs unmarked
    # against a 60 s `watchdog_threshold`, because the only touch is the
    # post-ladder one below. MEASURED on this leg before the fix
    # (tests/unit/test_turn_loop_watchdog.py, injected clock): the freeze
    # fired at attempt 2 of 4, t=70 s, touches=0 -- so `os._exit(1)` ran
    # MID-GAME and the D-13 verdict due at t=140 s was never recorded.
    #
    # It marks a real attempt STARTING, never a heartbeat on a dead loop:
    # each attempt is itself bounded by response_timeout, so a wedged event
    # loop stops producing attempts and NET-07 still kills us. That is why
    # this is not closed by widening `watchdog_threshold` (a Table-19 config
    # value) or by disarming the watchdog across the turn loop -- both are
    # refuted by named revert probes in that same test module.
    async def _pull() -> object:
        if on_attempt is not None:
            on_attempt()
        return await wait_for_opponent(ctx.runtime.queue, timeout=ctx.net.response_timeout)

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
        if envelope.type is MessageType.HINT:
            turn_buffer.record_hint(ctx, envelope.sender, envelope.turn, envelope.payload)
            continue
        if envelope.type is MessageType.FINAL_REVEAL:
            turn_buffer.record_final_reveal(ctx, envelope)
        return envelope, None
