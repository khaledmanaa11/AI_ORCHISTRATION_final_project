"""The early-FINAL_REVEAL buffer (05-17): a peer's published ledger is
never lost, whichever layer it lands in.

WHY IT EXISTS. `run_final_audit` pushes our own ledger and then waits for
the peer's. But the peer's FINAL_REVEAL can reach our queue BEFORE our
audit does -- whenever that side exits its turn loop first and pushes
immediately -- and until this module the envelope was consumed by whichever
`wait_for_*` leg happened to be running and dropped as tolerated jitter.
The audit then waited for a message that had already been delivered and
destroyed, exhausted its ladder, and (our own push having landed) declared
the peer OPPONENT_UNRESPONSIVE at `agent_audit_wiring.py:97`. A false
declaration, rules 16/22, against a peer that DEMONSTRABLY DID PUSH.

WHY A BUFFER AND NOT A LONGER WAIT. The envelope was already consumed;
no amount of extra waiting brings it back, so widening the ladder cannot
fix this and would only move a Table-19 number (CLAUDE.md rule 1) to make
a symptom quieter. This is a ROUTING fix. It contains no numeric value at
all, and the tempting timing "fix" is refuted by a named revert probe in
`tests/unit/test_early_final_reveal.py`.

WHY THE FIRST ARRIVAL WINS. A second FINAL_REVEAL is either a transport
retry of the first -- identical, nothing to gain by preferring it -- or a
DIFFERENT ledger, which is a peer revising what it published after seeing
ours. Rule 36 is about what a peer publishes; the first thing it published
is what it published. Keeping the first also makes the buffer idempotent,
so a duplicate can neither double-count nor re-drive the audit.

WHERE THE SLOT LIVES. `ctx.commit_state`, beside `own_ack_received` --
which exists for exactly this shape one protocol step earlier (an ACK that
arrived EARLY, captured so a later leg never blocks on a message that
already came). Per-context, never a module global (NET-02).
"""

from __future__ import annotations

from pursuit.network.agent_context import AgentContext
from pursuit.network.envelope import Envelope

__all__ = ["record_final_reveal", "take_final_reveal"]


def record_final_reveal(ctx: AgentContext, envelope: Envelope) -> None:
    """Buffer *envelope* as the peer's Final Reveal, first arrival wins.

    The caller has already established `envelope.type is
    MessageType.FINAL_REVEAL` -- `turn_commit_pull.next_protocol_message` is
    the only one, and it tests the type before calling, exactly as it does
    before `turn_buffer.record_hint`. The type is deliberately NOT re-tested
    here: a second gate would let the two disagree about which envelopes
    reach the audit, and that disagreement is what a false accusation is
    made of."""
    if ctx.commit_state.early_final_reveal is None:
        ctx.commit_state.early_final_reveal = envelope


def take_final_reveal(ctx: AgentContext) -> Envelope | None:
    """Pop the buffered Final Reveal, or None if none arrived early.

    Consuming rather than peeking is what keeps the audit driven exactly
    once per published ledger: `receive_final_reveal` checks this buffer at
    the top of every iteration, so a peek would spin on the same envelope
    forever instead of terminating."""
    envelope = ctx.commit_state.early_final_reveal
    ctx.commit_state.early_final_reveal = None
    return envelope
