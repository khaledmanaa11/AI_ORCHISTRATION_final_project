"""D-58 wire mechanics: the jitter-tolerant wait primitives plus the
shared commit+ledger-append helper `turn_commit.py`'s three entry points
call -- split from `turn_commit.py` at the 150-code-line gate (Segal
Table 5, pre-authorized), mirroring `handshake.py`/`handshake_wire.py`'s
policy-vs-mechanism split. `next_protocol_message` generalizes
`turn_buffer.await_move`'s own shape (tolerant of an interleaved HINT,
bounded per-pull by `call_with_retry`'s existing NetworkParams ladder --
no new timeout/retry/backoff number) to any expected type; the four
`wait_for_*` functions built on top of it are each one named leg of the
D-58 exchange (opponent COMMIT, ACK+opponent-COMMIT together, REVEAL
capturing an early ACK, a still-outstanding ACK). `build_action_payload`/
`commit_own_action` build the D-59/D-66 composite action payload and
durably append the full `{state,move,intent,nonce}` record to THIS side's
own `CommitLedger` (D-64) BEFORE any network send.
"""

from __future__ import annotations

from pursuit.network import move_payload, turn_buffer
from pursuit.network.agent_context import AgentContext, Coord
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_send import log_received, send_and_log
from pursuit.network.verdict import TechnicalWin
from pursuit.security import commit_pack
from pursuit.security.ledger import CommitLedger
from pursuit.security.state_record import build_state_record

H_COMMIT_KEY = "h_commit"


def _ledger_path(ctx: AgentContext):
    """D-64's `<log-file-stem>.ledger.jsonl` sibling convention -- 06-03
    reads its own ledger by this SAME name."""
    return ctx.log_path.parent / f"{ctx.log_path.stem}.ledger.jsonl"


def build_action_payload(pre_cell: Coord, dest: Coord, barrier: Coord | None) -> dict:
    """D-59/D-66's composite action dict. `move` is always present -- a
    real step, or a "stay" token (mirroring `CopAction.destination()`'s own
    "unchanged when placing") when a barrier is placed instead; `barrier`
    is present only then. Never both `move`-as-real-step AND `barrier` --
    matches `CopAction`'s own move-XOR-barrier invariant."""
    move_dest = pre_cell if barrier is not None else dest
    payload = {"move": move_payload.encode(pre_cell, move_dest, move_payload.ActionKind.MOVE), "barrier": None}
    if barrier is not None:
        payload["barrier"] = move_payload.encode(pre_cell, barrier, move_payload.ActionKind.BARRIER)
    return payload


def commit_own_action(
    ctx: AgentContext, *, pre_cell: Coord, dest: Coord, barrier: Coord | None,
    intent: str, turn: int,
) -> tuple[str, dict]:
    """Build + commit + durably ledger-append THIS side's own action for
    *turn*, all before any send. Returns `(h_commit, action_payload)` --
    `action_payload` is the exact dict this side later reveals verbatim."""
    action_payload = build_action_payload(pre_cell, dest, barrier)
    barriers_remaining = ctx.params.barrier_quota - ctx.state.barriers_placed
    state_record = build_state_record(
        game_id=ctx.game_uid, turn=turn, role=ctx.role,
        position=pre_cell, barriers_remaining=barriers_remaining,
    )
    h_commit, nonce = commit_pack.commit(state_record, action_payload, intent)
    payload = commit_pack.build_commit_payload(
        state=state_record, move=action_payload, intent=intent, nonce=nonce,
    )
    CommitLedger(_ledger_path(ctx)).append(turn=turn, h_commit=h_commit, payload=payload)
    return h_commit, action_payload


async def next_protocol_message(ctx: AgentContext) -> tuple[Envelope | None, TechnicalWin | None]:
    """Pull one non-HINT envelope off the wire, tolerant of an interleaved
    HINT (buffered via `turn_buffer.record_hint`, never blocking) -- the
    same primitive `turn_buffer.await_move` uses, generalized to any type
    (D-58). Bounded per-pull by `call_with_retry`'s existing NetworkParams
    ladder; a silent opponent eventually returns a `TechnicalWin` verdict
    here (never raises). Duplicate/unexpected types are the caller's own
    concern to drop."""
    while True:
        call_outcome = await call_with_retry(
            lambda: wait_for_opponent(ctx.runtime.queue, timeout=ctx.net.response_timeout),
            timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
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
        envelope, verdict = await next_protocol_message(ctx)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.ACK and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            ack_received = True
        elif envelope.type is MessageType.COMMIT and opponent_h_commit is None:
            opponent_h_commit = envelope.payload.get(H_COMMIT_KEY)
            log_received(ctx, envelope, state_from=current, state_to=State.WAIT_OPPONENT)
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
        envelope, verdict = await next_protocol_message(ctx)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.REVEAL:
            return envelope, None
        if envelope.type is MessageType.ACK and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            ctx.commit_state.own_ack_received = True


async def wait_for_opponent_commit(ctx: AgentContext, current: State) -> tuple[str | None, TechnicalWin | None]:
    """The responder's first wait (D-58): block until the initiator's own
    COMMIT arrives -- logged on receipt, since the D-58 both-locked-gate
    proof needs this record to appear before this side's own later
    REVEAL. Returns `(opponent_h_commit, verdict)`."""
    while True:
        envelope, verdict = await next_protocol_message(ctx)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.COMMIT:
            log_received(ctx, envelope, state_from=current, state_to=current)
            return envelope.payload.get(H_COMMIT_KEY), None
        # a duplicate/unexpected arrival here is tolerated jitter -- dropped.


async def wait_for_matching_ack(ctx: AgentContext, h_commit: str) -> TechnicalWin | None:
    """`reveal_pending`'s own ack-wait: block until an ACK matching
    *h_commit* arrives (skipped entirely when
    `ctx.commit_state.own_ack_received` is already True -- it arrived
    early, during the tail wait above). Returns None once found, or the
    TechnicalWin verdict on exhaustion."""
    while True:
        envelope, verdict = await next_protocol_message(ctx)
        if verdict is not None:
            return verdict
        if envelope.type is MessageType.ACK and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            return None
