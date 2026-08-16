"""D-58 wire mechanics: the jitter-tolerant wait legs -- split from
`turn_commit.py` at the 150-code-line gate (Segal Table 5,
pre-authorized), mirroring `handshake.py`/`handshake_wire.py`'s
policy-vs-mechanism split. The three `wait_for_*` functions here are each
one named leg of the D-58 exchange, and each is ROLE-SPECIFIC: the
responder's first wait for the initiator's COMMIT, the initiator's dual
ACK+opponent-COMMIT wait, the responder's still-outstanding-ACK wait.

The fourth leg, the tail wait for the opponent's REVEAL, moved to the
sibling `turn_commit_wait_reveal.py` when 05-18 took this file to 151 code
lines -- and along that exact division, because 05-18 is what made it the
one leg BOTH roles run (deferred item #18: the police branch of
`turn_commit.await_and_respond` had been pulling bare, with no type test at
all). It is NOT re-exported here, unlike every other split this module has
been through: that leg imports `H_COMMIT_KEY` from this file, so exporting
it back would be an import cycle. Its three importers name it directly.

The pull primitive they are all built on, `next_protocol_message`, moved
to the sibling `turn_commit_pull.py` when 05-17 needed room here for the
FINAL_REVEAL routing and for the docstring corrections that routing forces
on three of these legs (this file was at 145/150 -- deferred item #11
named this exact seam). It is re-exported below, unchanged for every
importer.

WHAT "DROPPED AS TOLERATED JITTER" NOW MEANS, because it changed. Each leg
below still discards an arrival it was not waiting for. Until 05-17 that
DESTROYED the envelope, which for a peer's FINAL_REVEAL meant our own
audit later waited for a ledger we had already eaten, exhausted its
ladder, and declared an honest peer OPPONENT_UNRESPONSIVE (rules 16/22 --
`agent_audit_wiring.py:97`). `next_protocol_message` now RECORDS a
FINAL_REVEAL into `ctx.commit_state.early_final_reveal` before returning
it, so a leg's drop costs nothing: the audit reads that buffer before it
waits. The legs' drop policy itself is byte-unchanged -- nothing here
started keeping envelopes -- and every drop below is now safe rather than
merely tolerated.

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

from pursuit.network.agent_context import AgentContext
from pursuit.network.envelope import MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_ledger import (
    build_action_payload,
    commit_own_action,
    ledger_path,
)
from pursuit.network.turn_commit_pull import next_protocol_message
from pursuit.network.turn_commit_send import log_received, send_and_log
from pursuit.network.verdict import TechnicalWin

H_COMMIT_KEY = "h_commit"

# Re-exported for the callers that already import them from here
# (turn_commit.py, agent_audit_exchange.py, agent_audit_observed.py, the
# gate6 scripts, the test suite); the definitions moved to
# turn_commit_ledger.py at the 150-line gate (06-05) and to
# turn_commit_pull.py at the same gate (05-17).
__all__ = [
    "H_COMMIT_KEY",
    "build_action_payload",
    "commit_own_action",
    "ledger_path",
    "next_protocol_message",
    "wait_for_ack_and_commit",
    "wait_for_matching_ack",
    "wait_for_opponent_commit",
]


async def wait_for_ack_and_commit(
    ctx: AgentContext, h_commit: str, turn: int, current: State,
) -> tuple[str | None, TechnicalWin | None]:
    """The initiator's D-58 dual wait: block until BOTH an ACK naming our
    own h_commit AND the opponent's own COMMIT have arrived -- ACKing the
    opponent's COMMIT the instant it arrives, regardless of whether our
    own ACK has arrived yet. A duplicate ACK/COMMIT arriving here is
    tolerated jitter, dropped -- and so is a peer FINAL_REVEAL, which is
    SAFE to drop only because `next_protocol_message` buffered it on the
    way past (05-17); dropping it outright is what made our own audit
    accuse an honest peer. Returns `(opponent_h_commit, verdict)`."""
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
        # A duplicate/unexpected arrival here is tolerated jitter -- dropped.
        # That sentence was FALSE for one type until 05-17, and it is the
        # sentence this plan was written about: a peer FINAL_REVEAL landing
        # in this window was consumed and destroyed, after which our own
        # audit waited out its whole ladder and declared the peer
        # OPPONENT_UNRESPONSIVE. `next_protocol_message` buffers it before
        # returning it, so the drop below is now genuinely free.


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
