"""The whole Final-Reveal/mutual-audit send-receive-verdict sequence -- the
sibling that keeps agent_entrypoint.py a thin caller (pre-authorized,
must_haves: Step-0 collect/sign/declare AND the whole Final-Reveal audit
wiring landing in the SAME plan). Wire mechanics (push/receive
FINAL_REVEAL, observed-history extraction, verdict recording) live in the
sibling agent_audit_exchange.py, split at the SAME 150-code-line gate --
this module keeps only the public entry point and its verdict policy.

Step-0 declaration collect/sign/declare and its D-61 on-disk persistence
moved to the sibling `agent_step0_wiring.py` when 05-13's receive-leg
policy took this file to exactly 150/150 (05-10's `security/audit.py`
precedent: split at exactly the gate, never at the breach). Both names are
RE-EXPORTED below, so `agent_entrypoint`, `late_peer_harness`, the gate
scripts and the test suite all resolve through this module unchanged.
"""

from __future__ import annotations

import time

from pursuit.constants import Outcome
from pursuit.network.agent_audit_exchange import (
    OWN_RECEIVE_FAILED,
    observed,
    push_final_reveal,
    receive_final_reveal,
    record_audit_incomplete,
    record_audit_verdict,
    record_technical_loss,
)
from pursuit.network.agent_context import AgentContext
from pursuit.network.agent_step0_wiring import declare_step0, write_declaration
from pursuit.network.orchestrator import opponent_role
from pursuit.network.turn_commit_ledger import ledger_path
from pursuit.security.audit import audit_peer_records
from pursuit.security.ledger import CommitLedger

__all__ = ["declare_step0", "run_final_audit", "write_declaration"]


async def run_final_audit(
    ctx: AgentContext, *, board_outcome: Outcome | None = None,
) -> Outcome | None:
    """Game-end mutual audit (D-67, SEC-05/08): send this side's own
    ledger as FINAL_REVEAL, receive the opponent's, and audit BOTH
    directions -- the opponent's claims against what we observed on the
    wire, AND our own ledger against what we ourselves actually sent
    (CONTEXT, locked: symmetric honesty). Called only when
    `ctx.security.commit_reveal` is True, AFTER `run_turn_loop` returns --
    `ctx.machine` is already terminal; this function never calls
    `ctx.machine.attempt` again.

    *board_outcome* is the turn loop's own result, supplied by
    `agent_entrypoint.run_agent` (05-04). It decides ONLY what a failed
    OUTBOUND push means, and nothing else:

    - a push failure with a board outcome standing is evidence about US, so
      it records a non-accusatory `audit_incomplete` and FALLS THROUGH to
      the receive + audit steps (05-UAT.md G1: our own send failing is not
      proof the peer was silent, and aborting here is what left machine B
      with no verdict at all);
    - a push failure with NO board outcome still returns TECHNICAL_LOSS --
      the turn loop never resolved, so nothing else stands;
    - a failed RECEIVE after a push that SUCCEEDED still returns
      TECHNICAL_LOSS -- our envelope reached the peer's tool, so the channel
      demonstrably worked and a peer that then never publishes its own
      nonces performed an act of its own (rule 36);
    - a failed RECEIVE when our OWN push had ALREADY failed and a board
      outcome stands is the mirror of the first case (05-13, G6): our own
      transport is demonstrably broken on this leg, the peer may well have
      answered into a socket we could not reach, and accusing it is exactly
      the false declaration 05-04 removed from the send leg. It records a
      second non-accusatory `audit_incomplete` -- reason naming OUR OWN
      receive -- and RETURNS, leaving the board outcome standing. Returning
      is load-bearing: falling through with `peer_records == []` would fail
      every honest turn at `audit_state` and re-enter TECHNICAL_LOSS through
      the AUDIT_HASH_MISMATCH door;
    - a genuine AUDIT_HASH_MISMATCH still returns TECHNICAL_LOSS (D-67)."""
    own_records = CommitLedger(ledger_path(ctx)).read_all()

    send_verdict = await push_final_reveal(ctx, own_records)
    if send_verdict is not None:
        if board_outcome is None:
            return record_technical_loss(ctx, send_verdict)
        record_audit_incomplete(ctx, send_verdict)

    peer_records, recv_verdict = await receive_final_reveal(ctx)
    if recv_verdict is not None:
        # `send_verdict is not None` is the whole discrimination, and it is
        # what keeps rule 36's sanction intact: a push that LANDED proves
        # the peer's server accepted our envelope, so silence afterwards is
        # the peer's own act. Only when BOTH of our own legs failed is the
        # evidence about us rather than about them.
        if board_outcome is not None and send_verdict is not None:
            record_audit_incomplete(ctx, recv_verdict, reason=OWN_RECEIVE_FAILED)
            return None
        return record_technical_loss(ctx, recv_verdict)

    sent_commits, sent_reveals = observed(ctx, direction="message_sent")
    received_commits, received_reveals = observed(ctx, direction="message_received")

    # 05-05: the SAME candidate set serves both directions, passed THROUGH
    # from `adopt_negotiated_game_id` (which built it before its rebind) and
    # never reconstructed here -- post-adoption `ctx.game_uid` and
    # `ctx.negotiated_game_id` are the SAME string on the thief, so a set
    # rebuilt here would hold one element and degenerate to equality. Our own
    # records always carry `ctx.game_uid`, which is in the set on both roles
    # by construction, so the self direction cannot mis-fire. `forbidden_role`
    # is the only per-direction difference: a PEER record claiming to have
    # been written by US is a replay of our own commits (every FINAL_REVEAL
    # makes them available), and symmetrically for our own ledger.
    started = time.monotonic()
    peer_audit = audit_peer_records(
        received_commits, received_reveals, peer_records,
        candidate_game_ids=ctx.candidate_game_ids, forbidden_role=ctx.role,
    )
    self_audit = audit_peer_records(
        sent_commits, sent_reveals, own_records,
        candidate_game_ids=ctx.candidate_game_ids, forbidden_role=opponent_role(ctx.role),
    )
    elapsed_seconds = time.monotonic() - started

    return record_audit_verdict(
        ctx, peer_audit=peer_audit, self_audit=self_audit, elapsed_seconds=elapsed_seconds,
    )
