"""D-67 wire mechanics for the Final-Reveal mutual audit -- split from
agent_audit_wiring.py at the 150-code-line gate (pre-authorized: this
plan's own must_haves anticipated agent_audit_wiring.py needing further
splitting, mirroring the handshake.py/turn_commit.py precedent). Holds
"how to push/receive one FINAL_REVEAL envelope" and "how to read this
side's own observed commit/reveal history from its wire log" --
agent_audit_wiring.py keeps only the two public entry points and policy
(declare_step0/write_declaration/run_final_audit).

"How to record an audit verdict" moved to the sibling
`agent_audit_verdict.py` when 06-05's Gap-2 fix took this file to 159 code
lines; both of its public names are re-exported below, so importers that
already reach for them here are unaffected.

"How to read this side's own observed history back off its wire log"
(`observed`) moved to the sibling `agent_audit_observed.py` when 05-15's
receive-leg envelope-type loop took this file to 153 -- split at the gate
along the seam this docstring already named, never compressed to fit, and
re-exported below so no importer changed.
"""

from __future__ import annotations

from pursuit.network import capture_declaration, turn_buffer
from pursuit.network.agent_audit_observed import observed
from pursuit.network.agent_audit_verdict import (
    OWN_RECEIVE_FAILED,
    record_audit_incomplete,
    record_audit_verdict,
    record_technical_loss,
)
from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.turn_commit_wait import next_protocol_message
from pursuit.network.verdict import TechnicalWin

_FINAL_REVEAL_TOOL = "receive_final_reveal"
_RECORDS_KEY = "records"

__all__ = [
    "OWN_RECEIVE_FAILED",
    "observed",
    "push_final_reveal",
    "receive_final_reveal",
    "record_audit_incomplete",
    "record_audit_verdict",
    "record_technical_loss",
]


async def push_final_reveal(ctx: AgentContext, records: list[dict]) -> TechnicalWin | None:
    """Send THIS side's own ledger as one FINAL_REVEAL envelope, via the
    SAME call_with_retry ladder every other push uses (D-17, no new number).

    05-13 (05-UAT.md G6) -- the audit now touches the freeze watchdog once
    at the START of each BOUNDED attempt. Before this, `Watchdog.touch()`
    was called NOWHERE in the audit path: all five call sites were in the
    turn loop, and `agent_entrypoint.run_agent` arms the watchdog before
    `start_server` and stops it only in the teardown `finally`, so this
    ladder -- (retry_count+1) x response_timeout plus backoffs, 135 s at
    the shipped Table-19 values -- ran entirely unmarked against a 60 s
    `watchdog_threshold` whose freeze action is `os._exit(1)`. Against a
    peer whose socket accepts TCP but never answers (a stalled tunnel edge,
    exactly the drop 05-11 exists for) the process died at t=60 s, so
    `run_final_audit`'s non-accusatory `record_audit_incomplete` at
    t~135 s NEVER RAN: our log ended on `watchdog_incident` with no
    `audit_verdict`, and the peer then declared US `opponent_unresponsive`.

    NET-07 is PRESERVED, not traded away, and the placement is the whole
    reason. The touch marks a real attempt STARTING -- the shape
    `turn_commit_send.push` already uses around this same ladder -- never a
    heartbeat on a dead loop. Every attempt is itself bounded by
    `response_timeout`, so the widest possible gap between two touches is
    response_timeout + backoff_seconds (35 s) < watchdog_threshold (60 s),
    while a genuinely wedged event loop stops producing attempts at all and
    is still killed. Stopping the watchdog across the audit would have made
    the same test pass by deleting the requirement.
    """
    envelope = Envelope(
        type=MessageType.FINAL_REVEAL, turn=ctx.state.turn, sender=ctx.role,
        payload={_RECORDS_KEY: records},
    )
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _call() -> object:
        ctx.watchdog.touch()
        async with ctx.runtime.client() as client:
            return await client.call_tool(_FINAL_REVEAL_TOOL, args)

    call_outcome = await call_with_retry(
        _call, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    return None if call_outcome.succeeded else call_outcome.verdict


async def receive_final_reveal(ctx: AgentContext) -> tuple[list[dict], TechnicalWin | None]:
    """Block for the opponent's own FINAL_REVEAL -- the SAME bounded-wait
    primitive turn_commit.py's own waits use (tolerant of a stray HINT).

    The receive leg carries the IDENTICAL 135 s-against-60 s exposure the
    push leg does -- `next_protocol_message`'s only touch is AFTER its whole
    ladder -- and it is the leg that runs LAST, so a freeze here kills the
    process with the peer's records already in hand and no `audit_verdict`
    written. `on_attempt` is therefore passed here and nowhere else: the
    turn-loop callers keep the pre-05-13 behaviour byte for byte.

    05-15 (G10): this leg now LOOPS until an actual FINAL_REVEAL arrives,
    the same shape `turn_commit_wait`'s four `wait_for_*` legs have always
    had. It used to accept whatever `next_protocol_message` returned first
    and read `records` off it -- so ANY other envelope arriving ahead of the
    peer's FINAL_REVEAL yielded `records=[]` with `verdict=None`, which is
    byte-identical to the `{"records": []}` rule-36 evasion and drives an
    honest peer straight into AUDIT_HASH_MISMATCH / TECHNICAL_LOSS. That is
    a FALSE ACCUSATION (rules 16/22), and it was reachable BEFORE this plan
    added a sender: `game_over` is a registered tool on our published league
    surface, so any peer implementation using it triggered it. Measured
    pre-fix on a queue of [GAME_OVER, FINAL_REVEAL]: `records=[]`,
    `verdict=None`, the peer's real ledger discarded. A capture declaration
    seen on the way past is recorded as evidence; anything else is dropped
    as tolerated jitter. Termination is unchanged -- the ladder underneath
    still returns a verdict against a genuinely silent peer, and it still
    touches the watchdog once per bounded attempt.

    05-17: the BUFFER is consulted at the top of every iteration, before
    the wait. 05-15 hardened this leg against an envelope arriving ahead of
    the peer's ledger IN THIS LEG; the same ledger arriving one layer
    earlier -- while the turn loop still owned the queue -- was consumed
    and destroyed by whichever `wait_for_*` leg was running, and no amount
    of waiting here brings it back. `turn_commit_pull.next_protocol_message`
    now records every FINAL_REVEAL it sees into
    `ctx.commit_state.early_final_reveal`, so the type test that used to
    live inline here happens there instead and this leg reads the result.
    Two consequences worth stating: a ledger that arrived early
    SHORT-CIRCUITS the ladder entirely rather than timing out behind it,
    and a rule-36 silent peer is UNCHANGED -- the buffer is empty, the
    ladder runs, the verdict is returned, and `run_final_audit` still
    accuses. A duplicate cannot double-count: the buffer keeps the first
    arrival and `take_final_reveal` consumes it."""
    while True:
        buffered = turn_buffer.take_final_reveal(ctx)
        if buffered is not None:
            return buffered.payload.get(_RECORDS_KEY, []), None
        envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
        if verdict is not None:
            return [], verdict
        capture_declaration.record_received_declaration(ctx, envelope)
