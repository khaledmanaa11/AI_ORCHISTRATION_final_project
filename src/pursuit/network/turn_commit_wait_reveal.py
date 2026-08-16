"""`wait_for_reveal_capturing_early_ack` -- the D-58 tail wait, split out of
`turn_commit_wait.py` at the 150-code-line gate (Segal Table 5).

THE SEAM IS THE ONE 05-18 CREATED, not an arbitrary cut to make room. The
other three legs in `turn_commit_wait.py` are each ROLE-SPECIFIC: the
responder's first wait for the initiator's COMMIT, the initiator's dual
ACK+COMMIT wait, the responder's still-outstanding-ACK wait. This one is now
the only leg BOTH roles run, because deferred item #18's repair pointed the
police branch of `turn_commit.await_and_respond` at it instead of leaving it
on a bare, type-blind pull. "Role-specific legs" / "the shared leg" is a real
division, and it is the division that file's own docstring now describes.
Split, never compressed: no assertion, guard or narrative was shortened to
fit, and the leg's body is byte-identical apart from 05-18's `h_commit is not
None` guard.

NOT RE-EXPORTED FROM `turn_commit_wait`, which breaks this file's siblings'
otherwise-universal habit, and deliberately: this module imports
`H_COMMIT_KEY` from there, so a re-export the other way would be an import
CYCLE. The three importers (`turn_commit.py` and two test modules) name this
module directly instead. The alternative -- moving `H_COMMIT_KEY` down into
`envelope.py` or `turn_commit_pull.py` to preserve the re-export habit --
would relocate a Phase-6 protocol constant into a Phase-2 module or into the
pull primitive that has no business knowing payload keys, for the sake of a
convention whose entire purpose is avoiding churn in three lines.
"""

from __future__ import annotations

from pursuit.network.agent_context import AgentContext
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.turn_commit_pull import next_protocol_message
from pursuit.network.turn_commit_wait import H_COMMIT_KEY
from pursuit.network.verdict import TechnicalWin

__all__ = ["wait_for_reveal_capturing_early_ack"]


async def wait_for_reveal_capturing_early_ack(
    ctx: AgentContext, h_commit: str | None,
) -> tuple[Envelope | None, TechnicalWin | None]:
    """BOTH roles' tail wait (D-58): block until the opponent's REVEAL
    arrives. A duplicate/unexpected arrival is tolerated jitter, dropped --
    including a peer FINAL_REVEAL, which reaches the audit through
    `ctx.commit_state.early_final_reveal` rather than through this return
    value (05-17). This is the leg 05-17's reproduction runs against: the
    peer finishes first and pushes its ledger, and the in-game REVEAL is
    still what this leg returns.

    *h_commit* names THIS side's own outstanding commit, or None when there
    is none. An ACK naming it that arrives FIRST is captured onto
    `ctx.commit_state.own_ack_received` (it cannot arrive a second time), so
    the responder's own later `reveal_pending` never blocks on a message that
    already came. **None is the INITIATOR's case and is not a sentinel**:
    `initiate` already collected this turn's ACK inside
    `wait_for_ack_and_commit`, so a further ACK here is jitter like any
    other. The `is not None` guard is what stops a payload carrying no
    `h_commit` key from matching None by accident -- without it, `.get()`
    returns None, None == None, and every ACK-shaped envelope would set the
    responder's flag on a side that has nothing outstanding.

    Serving both roles from ONE leg is deliberate. Every instance of the
    envelope-boundary class so far has been a boundary where one path had the
    type discipline and its sibling did not, so the repair removes the second
    path rather than teaching it the same lesson again.
    `turn_commit.await_and_respond`'s police branch holds the measurement and
    the rejected alternative, in one place rather than two."""
    while True:
        envelope, verdict = await next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)
        if verdict is not None:
            return None, verdict
        if envelope.type is MessageType.REVEAL:
            return envelope, None
        if h_commit is not None and envelope.type is MessageType.ACK \
                and envelope.payload.get(H_COMMIT_KEY) == h_commit:
            ctx.commit_state.own_ack_received = True
