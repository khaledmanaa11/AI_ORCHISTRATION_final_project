"""Step-0 declaration collect/sign/declare, and the whole Final-Reveal/
mutual-audit send-receive-verdict sequence -- the sibling that keeps
agent_entrypoint.py a thin caller (pre-authorized, must_haves: Step-0
collect/sign/declare AND the whole Final-Reveal audit wiring landing in
the SAME plan). Wire mechanics (push/receive FINAL_REVEAL, observed-history
extraction, verdict recording) live in the sibling agent_audit_exchange.py,
split at the SAME 150-code-line gate -- this module keeps only the two
public entry points and D-61's game_id resolution policy.
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
from pursuit.network.agent_wiring import AgentConfig
from pursuit.network.game_identity import negotiated_game_id
from pursuit.network.handshake_evaluate import HandshakeResult
from pursuit.network.language_wiring import declared_llm_name
from pursuit.network.orchestrator import opponent_role
from pursuit.network.secret_wiring import resolve_shared_secret
from pursuit.network.turn_commit_ledger import ledger_path
from pursuit.security import step0_collect, step0_sign
from pursuit.security.audit import audit_peer_records
from pursuit.security.ledger import CommitLedger
from pursuit.shared.durable_write import durable_write_json
from pursuit.shared.version import VERSION

_COUNTER_FILENAME = "games_played.json"
# Structural, matching QTable.save()'s own local durable-write precedent
# (03-05-SUMMARY.md) -- not a PARAMETERS.md value.
_DECLARE_RETRIES = 3
_DECLARE_BACKOFF_SECONDS = 0.1


async def declare_step0(cfg: AgentConfig) -> tuple[str, dict]:
    """Collect + sign THIS side's Step-0 declaration BEFORE the handshake
    (D-62/D-63) so its digest is ready to ride the handshake payload.
    Returns `(step0_digest, declaration_envelope)` -- the envelope is the
    exact dict `write_declaration` persists once the handshake agrees.

    `llm_name` is `declared_llm_name`'s answer, NOT a config echo (rule 38,
    05-UAT G5): only the VALUE of that one field moved, never the field
    set. The declaration's ten Sec5.5 keys are what `sign_declaration`
    HMACs and what `handshake_step0` verifies before move 1 (Sec10.4
    criterion 3), so a shape change here would break Step-0 against a
    peer."""
    games_played = step0_collect.read_games_played(cfg.config_dir / _COUNTER_FILENAME)
    llm_name = declared_llm_name(cfg.language.model)
    declaration = step0_collect.collect_declaration(
        role=cfg.role, team_code=cfg.security.team_code, llm_name=llm_name,
        code_version=VERSION, games_played=games_played,
    )
    secret = resolve_shared_secret(cfg.config_dir)
    secret_value = secret[1] if secret is not None else None
    signature = step0_sign.sign_declaration(declaration, secret=secret_value)
    return signature[step0_sign.SignKey.DIGEST], {"declaration": declaration, **signature}


def write_declaration(
    ctx: AgentContext, cfg: AgentConfig, result: HandshakeResult, declaration_envelope: dict,
) -> None:
    """Persist THIS side's own signed Step-0 declaration beside the log,
    named by the negotiated game_id (D-61) -- ONLY after a successful
    handshake -- then record this game against the per-role counter
    exactly once (rule 37/38). ALSO persists the PEER's own declaration
    (D-62 follow-up), when they sent one, so the content this side
    verified at handshake stays auditable after the fact (Phase 7);
    skipped entirely for a digest-only peer -- there is no content to save.

    05-05: the D-61 policy is no longer duplicated here -- the ONE definition
    lives in `game_identity.negotiated_game_id`, which `run_agent` has
    already applied to `ctx.game_uid` itself by the time this runs (so this
    call is idempotent on the live path: `negotiated_game_id(role, P, P)` is
    `P` for both roles). Calling it rather than reading `ctx.game_uid` keeps
    a caller that has NOT adopted -- the integration harnesses -- on exactly
    the pre-05-05 filename."""
    declared_game_id = negotiated_game_id(ctx.role, ctx.game_uid, result.peer_game_id)
    path = ctx.log_path.parent / f"declaration_{declared_game_id}.json"
    durable_write_json(
        path, declaration_envelope, retries=_DECLARE_RETRIES, backoff=_DECLARE_BACKOFF_SECONDS,
    )
    if result.peer_step0_declaration is not None:
        peer_path = ctx.log_path.parent / f"declaration_{declared_game_id}_peer.json"
        durable_write_json(
            peer_path, result.peer_step0_declaration,
            retries=_DECLARE_RETRIES, backoff=_DECLARE_BACKOFF_SECONDS,
        )
    step0_collect.record_game_played(cfg.config_dir / _COUNTER_FILENAME)


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
