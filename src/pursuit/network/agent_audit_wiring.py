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
    observed,
    push_final_reveal,
    receive_final_reveal,
    record_audit_incomplete,
    record_audit_verdict,
    record_technical_loss,
)
from pursuit.network.agent_context import AgentContext
from pursuit.network.agent_wiring import AgentConfig
from pursuit.network.handshake_evaluate import HandshakeResult
from pursuit.network.secret_wiring import resolve_shared_secret
from pursuit.network.turn_commit_ledger import ledger_path
from pursuit.security import step0_collect, step0_sign
from pursuit.security.audit import audit_peer_records
from pursuit.security.ledger import CommitLedger
from pursuit.shared.durable_write import durable_write_json
from pursuit.shared.version import VERSION

_COUNTER_FILENAME = "games_played.json"
_LLM_NAME_UNKNOWN = "unspecified"
# Structural, matching QTable.save()'s own local durable-write precedent
# (03-05-SUMMARY.md) -- not a PARAMETERS.md value.
_DECLARE_RETRIES = 3
_DECLARE_BACKOFF_SECONDS = 0.1


async def declare_step0(cfg: AgentConfig) -> tuple[str, dict]:
    """Collect + sign THIS side's Step-0 declaration BEFORE the handshake
    (D-62/D-63) so its digest is ready to ride the handshake payload.
    Returns `(step0_digest, declaration_envelope)` -- the envelope is the
    exact dict `write_declaration` persists once the handshake agrees."""
    games_played = step0_collect.read_games_played(cfg.config_dir / _COUNTER_FILENAME)
    llm_name = cfg.language.model.get("model_id", _LLM_NAME_UNKNOWN)
    declaration = step0_collect.collect_declaration(
        role=cfg.role, team_code=cfg.security.team_code, llm_name=llm_name,
        code_version=VERSION, games_played=games_played,
    )
    secret = resolve_shared_secret(cfg.config_dir)
    secret_value = secret[1] if secret is not None else None
    signature = step0_sign.sign_declaration(declaration, secret=secret_value)
    return signature[step0_sign.SignKey.DIGEST], {"declaration": declaration, **signature}


def _declared_game_id(ctx: AgentContext, result: HandshakeResult) -> str:
    """D-61, scoped ONLY to the declaration filename: police keeps its own
    game_uid; the thief adopts the initiator's peer_game_id (falling back
    to its own game_uid if the peer never sent one)."""
    if ctx.role == "police":
        return ctx.game_uid
    return result.peer_game_id or ctx.game_uid


def write_declaration(
    ctx: AgentContext, cfg: AgentConfig, result: HandshakeResult, declaration_envelope: dict,
) -> None:
    """Persist THIS side's own signed Step-0 declaration beside the log,
    named by the negotiated game_id (D-61) -- ONLY after a successful
    handshake -- then record this game against the per-role counter
    exactly once (rule 37/38). ALSO persists the PEER's own declaration
    (D-62 follow-up), when they sent one, so the content this side
    verified at handshake stays auditable after the fact (Phase 7);
    skipped entirely for a digest-only peer -- there is no content to save."""
    declared_game_id = _declared_game_id(ctx, result)
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
    - a failed RECEIVE still returns TECHNICAL_LOSS -- a peer that withholds
      its own nonces is the peer's own act (rule 36);
    - a genuine AUDIT_HASH_MISMATCH still returns TECHNICAL_LOSS (D-67)."""
    own_records = CommitLedger(ledger_path(ctx)).read_all()

    send_verdict = await push_final_reveal(ctx, own_records)
    if send_verdict is not None:
        if board_outcome is None:
            return record_technical_loss(ctx, send_verdict)
        record_audit_incomplete(ctx, send_verdict)

    peer_records, recv_verdict = await receive_final_reveal(ctx)
    if recv_verdict is not None:
        return record_technical_loss(ctx, recv_verdict)

    sent_commits, sent_reveals = observed(ctx, direction="message_sent")
    received_commits, received_reveals = observed(ctx, direction="message_received")

    started = time.monotonic()
    peer_audit = audit_peer_records(received_commits, received_reveals, peer_records)
    self_audit = audit_peer_records(sent_commits, sent_reveals, own_records)
    elapsed_seconds = time.monotonic() - started

    return record_audit_verdict(
        ctx, peer_audit=peer_audit, self_audit=self_audit, elapsed_seconds=elapsed_seconds,
    )
