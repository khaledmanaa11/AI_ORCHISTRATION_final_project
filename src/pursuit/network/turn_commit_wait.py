"""D-58 wire mechanics: the jitter-tolerant wait primitives -- split from
`turn_commit.py` at the 150-code-line gate (Segal Table 5,
pre-authorized), mirroring `handshake.py`/`handshake_wire.py`'s
policy-vs-mechanism split. `next_protocol_message` generalizes
`turn_buffer.await_move`'s own shape (tolerant of an interleaved HINT,
bounded per-pull by `call_with_retry`'s existing NetworkParams ladder --
no new timeout/retry/backoff number) to any expected type; the four
`wait_for_*` functions built on top of it are each one named leg of the
D-58 exchange (opponent COMMIT, ACK+opponent-COMMIT together, REVEAL
capturing an early ACK, a still-outstanding ACK).

The commit+ledger mechanics (`build_action_payload`/`commit_own_action`/
`ledger_path`) moved to the sibling `turn_commit_ledger.py` when 06-05's
turn-binding fix pushed this file to 156 code lines; they are re-exported
here so existing importers are unaffected.

Every inbound COMMIT logged from this module is stamped with THIS side's
own turn (`local_turn`), never the peer's declared `envelope.turn` -- see
`turn_commit_send.log_received` for why that distinction is
security-critical (06-UAT.md Gap 1).
"""

from __future__ import annotations

from collections.abc import Callable

from pursuit.network import turn_buffer
from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_ledger import (
    build_action_payload,
    commit_own_action,
    ledger_path,
)
from pursuit.network.turn_commit_send import log_received, send_and_log
from pursuit.network.verdict import TechnicalWin

H_COMMIT_KEY = "h_commit"

# Re-exported for the callers that already import them from here
# (turn_commit.py, the gate6 scripts, the test suite); the definitions
# moved to turn_commit_ledger.py at the 150-line gate, see 06-05.
__all__ = [
    "H_COMMIT_KEY",
    "build_action_payload",
    "commit_own_action",
    "ledger_path",
    "next_protocol_message",
    "wait_for_ack_and_commit",
    "wait_for_matching_ack",
    "wait_for_opponent_commit",
    "wait_for_reveal_capturing_early_ack",
]


async def next_protocol_message(
    ctx: AgentContext, *, on_attempt: Callable[[], None] | None = None,
) -> tuple[Envelope | None, TechnicalWin | None]:
    """Pull one non-HINT envelope off the wire, tolerant of an interleaved
    HINT (buffered via `turn_buffer.record_hint`, never blocking) -- the
    same primitive `turn_buffer.await_move` uses, generalized to any type
    (D-58). Bounded per-pull by `call_with_retry`'s existing NetworkParams
    ladder; a silent opponent eventually returns a `TechnicalWin` verdict
    here (never raises). Duplicate/unexpected types are the caller's own
    concern to drop."""
    # `on_attempt` runs once at the START of each BOUNDED attempt.
    # Introduced by 05-13 (05-UAT.md G6) for the audit path and defaulted to
    # None so the turn loop stayed byte-identical; 05-16 (deferred item #10)
    # is what makes EVERY caller pass `ctx.watchdog.touch` -- the four
    # `wait_for_*` legs below and `agent_audit_exchange.receive_final_reveal`
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
        return envelope, None


async def wait_for_ack_and_commit(
    ctx: AgentContext, h_commit: str, turn: int, current: State,
) -> tuple[str | None, TechnicalWin | None]:
    """The initiator's D-58 dual wait: block until BOTH an ACK naming our
    own h_commit AND the opponent's own COMMIT have arrived -- ACKing the
    opponent's COMMIT the instant it arrives, regardless of whether our
    own ACK has arrived yet. A duplicate ACK/COMMIT arriving here is
    tolerated jitter, dropped. Returns `(opponent_h_commit, verdict)`."""
    ack_received, opponent_h_commit = False, None
    while not (ack_received and opponent_h_commit is not None):
        envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.ACK and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            ack_received = True
        elif envelope.type is MessageType.COMMIT and opponent_h_commit is None:
            opponent_h_commit = envelope.payload.get(H_COMMIT_KEY)
            log_received(
                ctx, envelope, state_from=current, state_to=State.WAIT_OPPONENT, local_turn=turn,
            )
            ack_verdict = await send_and_log(
                ctx, MessageType.ACK, turn, {H_COMMIT_KEY: opponent_h_commit},
                state_from=current, state_to=State.WAIT_OPPONENT,
            )
            if ack_verdict is not None:
                return None, ack_verdict
    return opponent_h_commit, None


async def wait_for_reveal_capturing_early_ack(
    ctx: AgentContext, h_commit: str,
) -> tuple[Envelope | None, TechnicalWin | None]:
    """The responder's own tail wait (D-58): block until the opponent's
    REVEAL arrives. An ACK matching our own h_commit arriving FIRST is
    captured onto `ctx.commit_state.own_ack_received` (it cannot arrive a
    second time), so this side's own later `reveal_pending` never blocks
    on a message that already came. A duplicate/unexpected arrival is
    tolerated jitter, dropped."""
    while True:
        envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.REVEAL:
            return envelope, None
        if envelope.type is MessageType.ACK and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            ctx.commit_state.own_ack_received = True


async def wait_for_opponent_commit(
    ctx: AgentContext, current: State, turn: int,
) -> tuple[str | None, TechnicalWin | None]:
    """The responder's first wait (D-58): block until the initiator's own
    COMMIT arrives -- logged on receipt, since the D-58 both-locked-gate
    proof needs this record to appear before this side's own later
    REVEAL. Returns `(opponent_h_commit, verdict)`.

    *turn* is THIS side's own pre-resolve turn, used as the log record's
    join key instead of the peer's declared `envelope.turn` (Gap 1)."""
    while True:
        envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.COMMIT:
            log_received(ctx, envelope, state_from=current, state_to=current, local_turn=turn)
            return envelope.payload.get(H_COMMIT_KEY), None
        # a duplicate/unexpected arrival here is tolerated jitter -- dropped.


async def wait_for_matching_ack(ctx: AgentContext, h_commit: str) -> TechnicalWin | None:
    """`reveal_pending`'s own ack-wait: block until an ACK matching
    *h_commit* arrives (skipped entirely when
    `ctx.commit_state.own_ack_received` is already True -- it arrived
    early, during the tail wait above). Returns None once found, or the
    TechnicalWin verdict on exhaustion."""
    while True:
        envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
        if verdict is not None:
            return verdict
        if envelope.type is MessageType.ACK and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            return None
