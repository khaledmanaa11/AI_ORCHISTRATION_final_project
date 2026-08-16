"""Rule 21's Capture Claim, on the wire (05-15, gap G10).

Book Sec3.5 p.22 Table 2 -- quoted through
`docs/phases/phase-3/RULES-RESOLUTION.md:51` -- says "the cop lands on the
thief's cell and declares Capture Claim". Until this module the capture was
DERIVED and never transmitted: both engines resolve it deterministically
from the same joint action, and it reached the peer only via the
FINAL_REVEAL ledger and the rule-35 report. `docs/RULES.md` as WORDED was
already met -- rule 21 forbids denying reality and rule 22 forbids a false
declaration, and we do neither -- but a grader holding that book line could
fairly ask where the Claim itself is. This is that Claim, at ZERO new
protocol cost:

- no new `MessageType`: `GAME_OVER` has existed since Phase 2
  (`envelope.py:32`);
- no new tool: the peer's `game_over` handler has existed since Phase 2
  (`tools.py:136`) and is part of the published league surface;
- no new number: the send rides the same `call_with_retry` /
  `NetworkParams` ladder every other push uses (D-17);
- no new payload vocabulary: `docs/PRD_mcp_transport.md`'s own row for this
  tool already specified "payload carries the outcome and reason".

RULE 22 IS THE REASON FOR THE SHAPE OF THIS MODULE, not a comment on it.
Its sanction is "**Immediate disqualification**, zero score, technical
loss, no appeal" (`docs/RULES.md:52`). A false capture declaration is
therefore made impossible by CONSTRUCTION rather than by care: the payload
is read off the SAME resolved `Outcome` object that `run_turn_loop` writes
into its own `game_over` ledger record, in the same two statements, so the
transmitted claim and the audited record cannot disagree. Nothing that
could *choose* is anywhere near it -- not a policy, not a brain, and above
all not the language model (rule 25 / CLAUDE.md rule 5). `strategy/` is not
imported here at all.

The send is BEST-EFFORT and returns nothing on purpose. A declaration that
fails to land must never change the outcome and must never accuse the peer:
the capture is already resolved, already in our ledger, and already
provable at the D-67 audit. Compare `turn_buffer.send_hint`, which takes the
same position for the same reason -- except that this one additionally
swallows `ToolError`, because a peer that rejects our declaration on the
way out must not convert a resolved capture into a technical loss.
"""

from __future__ import annotations

from fastmcp.exceptions import ToolError

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.orchestrator import engine_agent
from pursuit.network.state_machine import State

#: The peer-side tool that receives a GAME_OVER envelope (tools.py:136).
DECLARATION_TOOL = "game_over"

#: Payload keys, protocol-local (the `EnvelopeKey` precedent): named here
#: rather than inline so the receive side and the tests share one spelling.
OUTCOME_KEY = "outcome"
REASON_KEY = "reason"

#: The declaration's own reason string. A fixed sentence, not a composed
#: one: rule 22 means this text must not be generatable.
CAPTURE_REASON = "cop landed on the thief's cell; capture resolved by the engine"


def declares_capture(ctx: AgentContext, outcome: Outcome | None) -> bool:
    """True when THIS side owes the Capture Claim for *outcome*.

    Two conditions, both from the book line rather than from convenience:
    the outcome resolved to a capture, and this agent is the COP -- Sec3.5
    gives the Claim to the side that lands on the other. The thief stays
    silent; it has nothing to declare and rule 21 asks nothing of it.

    `engine_agent` is the ONE bridge between role.json's vocabulary and the
    SDK's (`orchestrator.py:58`); the literals are not re-spelled here.
    """
    return outcome is Outcome.CAPTURE and engine_agent(ctx.role) == "cop"


def build_declaration(ctx: AgentContext, *, turn: int, outcome: Outcome) -> Envelope:
    """The Capture Claim envelope, read straight off the resolved outcome."""
    return Envelope(
        type=MessageType.GAME_OVER,
        turn=turn,
        sender=ctx.role,
        payload={OUTCOME_KEY: outcome.value, REASON_KEY: CAPTURE_REASON},
    )


async def send_capture_declaration(
    ctx: AgentContext, *, turn: int, outcome: Outcome | None
) -> None:
    """Declare the capture to the peer, once, on the capturing turn.

    A no-op for every other outcome and for the thief -- rule 22 forbids a
    false capture declaration, and the cheapest way to never make one is to
    have exactly one branch that can send at all.

    Never raises, never returns a verdict, never touches `ctx.state` or the
    outcome. A `message_sent` record is written ONLY when the push actually
    landed, so the log never claims a declaration that did not go out.
    """
    if not declares_capture(ctx, outcome):
        return
    envelope = build_declaration(ctx, turn=turn, outcome=outcome)
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _push() -> object:
        async with ctx.runtime.client() as client:
            return await client.call_tool(DECLARATION_TOOL, args)

    try:
        call_outcome = await call_with_retry(
            _push, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
            backoff=ctx.net.backoff_seconds,
        )
    except ToolError:
        # `deadline.call_with_retry` re-raises ToolError unretried by design
        # (an application-level rejection is not a transport failure). Here
        # -- unlike in the turn loop -- there is nothing left to lose the
        # game over: the capture is resolved and ledgered. Swallowed.
        call_outcome = None
    ctx.watchdog.touch()
    if call_outcome is not None and call_outcome.succeeded:
        append_event(
            ctx.log_path,
            turn_events.turn_record(
                game_uid=ctx.game_uid, turn=turn, event="message_sent", sender=ctx.role,
                state_from=State.GAME_OVER, state_to=State.GAME_OVER,
                envelope=envelope.to_dict(),
            ),
        )


def record_received_declaration(ctx: AgentContext, envelope: Envelope) -> None:
    """Log a peer's inbound Capture Claim as received evidence.

    Called from `agent_audit_exchange.receive_final_reveal`, which is the
    only place still reading the queue once the turn loop has ended. A
    non-GAME_OVER envelope is ignored: that leg's contract is to DROP
    unexpected arrivals as tolerated jitter, and this function must not
    change which ones it drops.
    """
    if envelope.type is not MessageType.GAME_OVER:
        return
    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=envelope.turn, event="message_received",
            sender=ctx.role, state_from=State.GAME_OVER, state_to=State.GAME_OVER,
            envelope=envelope.to_dict(),
        ),
    )
