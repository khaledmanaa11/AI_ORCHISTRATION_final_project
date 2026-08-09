"""Task 4's own proof: Step-0 declared+verified before move 1, the shared
game_id naming the declaration file (D-61 CORROBORATION ONLY -- the
load-bearing D-61 proof is test_handshake_step0.py's own unit test, which
uses deliberately different local_game_id values; this harness, like
play_two_peer_game, hands both sides the SAME game_uid by construction),
and a clean game's mutual audit passing silently. Both D-67 tamper cases
live in the sibling test_step0_and_audit_tamper.py, which imports
`_play_full_game` from here (mirrors test_handshake_scent.py importing
shared fakes from test_handshake.py).

Hand-rolls the two-peer wiring (test_commit_reveal_protocol_jitter.py's
own precedent) since perform_handshake here needs local_step0_digest/
local_game_id, which play_two_peer_game's own call does not pass.
"""

from __future__ import annotations

import asyncio
import json

from fastmcp import Client

from pursuit.constants import Outcome
from pursuit.network import agent_lifecycle
from pursuit.network.agent_audit_wiring import declare_step0, run_final_audit, write_declaration
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.shared.scent_config import scent_digest


def _has_no_move_content_yet(log_path) -> bool:
    """True before any game-content envelope (move/commit/hint) has been
    logged -- a RECOVERABLE illegal_transition record from BOTH sides
    calling perform_handshake (real symmetric two-process behavior: each
    side's own outbound call ALSO drives the other's inbound responder,
    which then also attempts HANDSHAKE on an already-HANDSHAKE machine) is
    harmless noise, not game content."""
    if not log_path.exists():
        return True
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    return not any(e["event"] in ("message_sent", "message_received") for e in events)


async def _play_to_turn_loop_end(cfg_a, cfg_b, *, game_uid, log_dir):
    """Build two REAL AgentContexts, declare+sign Step-0 on both, handshake
    BOTH directions (each side's own outbound perform_handshake call --
    real deployment is fully symmetric, not just one client leg), write
    both declarations, then play to completion -- WITHOUT running the
    audit, so test_step0_and_audit_tamper.py can inject ledger/log
    corruption between run_turn_loop and run_final_audit."""
    step0_digest_a, decl_a = await declare_step0(cfg_a)
    step0_digest_b, decl_b = await declare_step0(cfg_b)

    ctx_a = agent_lifecycle.default_context(
        cfg_a, game_uid=game_uid, log_path=log_dir / "police" / "a.jsonl",
        local_step0_digest=step0_digest_a, local_game_id=game_uid,
    )
    ctx_b = agent_lifecycle.default_context(
        cfg_b, game_uid=game_uid, log_path=log_dir / "thief" / "b.jsonl",
        local_step0_digest=step0_digest_b, local_game_id=game_uid,
    )
    ctx_a.runtime.client = lambda: Client(ctx_b.runtime.server)
    ctx_b.runtime.client = lambda: Client(ctx_a.runtime.server)

    local_digest = config_digest(cfg_a.config_dir / "game_params.json")
    local_scent_digest = scent_digest(cfg_a.scent)

    async def _handshake(ctx, step0_digest):
        async with ctx.runtime.client() as client:
            return await perform_handshake(
                machine=ctx.machine, reporter=ctx.reporter, local_digest=local_digest,
                local_role=ctx.role, call_peer=make_client_caller(client),
                local_scent_digest=local_scent_digest,
                local_step0_digest=step0_digest, local_game_id=game_uid,
            )

    result_a = await _handshake(ctx_a, step0_digest_a)
    result_b = await _handshake(ctx_b, step0_digest_b)
    assert result_a.agreed and result_b.agreed, f"{result_a}; {result_b}"

    for log_path in (ctx_a.log_path, ctx_b.log_path):
        assert _has_no_move_content_yet(log_path)

    write_declaration(ctx_a, cfg_a, result_a, decl_a)
    write_declaration(ctx_b, cfg_b, result_b, decl_b)

    for log_path in (ctx_a.log_path, ctx_b.log_path):
        assert _has_no_move_content_yet(log_path)

    outcome_a, outcome_b = await asyncio.gather(run_turn_loop(ctx_a), run_turn_loop(ctx_b))
    assert outcome_a is not None and outcome_a == outcome_b
    return outcome_a, outcome_b, ctx_a, ctx_b


async def _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b):
    """The audit half of a full game, split out so a tamper test can run
    it AFTER corrupting ledger/log state."""
    audit_a, audit_b = await asyncio.gather(run_final_audit(ctx_a), run_final_audit(ctx_b))
    final_a = audit_a if audit_a is not None else outcome_a
    final_b = audit_b if audit_b is not None else outcome_b
    return final_a, final_b


async def _play_full_game(cfg_a, cfg_b, *, game_uid, log_dir):
    """`_play_to_turn_loop_end` + the audit, undisturbed -- the clean-game
    shape this file's own tests exercise."""
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
        cfg_a, cfg_b, game_uid=game_uid, log_dir=log_dir,
    )
    final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)
    return final_a, final_b, ctx_a, ctx_b


async def test_declaration_files_share_the_game_id_before_any_move(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    game_uid = "step0-audit-declare"

    _final_a, _final_b, ctx_a, ctx_b = await _play_full_game(
        cfg_a, cfg_b, game_uid=game_uid, log_dir=tmp_path,
    )

    decl_a_path = ctx_a.log_path.parent / f"declaration_{game_uid}.json"
    decl_b_path = ctx_b.log_path.parent / f"declaration_{game_uid}.json"
    assert decl_a_path.exists() and decl_b_path.exists()

    police_decl = json.loads(decl_a_path.read_text(encoding="utf-8"))
    thief_decl = json.loads(decl_b_path.read_text(encoding="utf-8"))
    assert police_decl["declaration"]["team_code"] == thief_decl["declaration"]["team_code"]
    assert police_decl["declaration"]["role"] == "police"
    assert thief_decl["declaration"]["role"] == "thief"


async def test_a_clean_game_audits_with_no_mismatch(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")

    final_a, final_b, ctx_a, ctx_b = await _play_full_game(
        cfg_a, cfg_b, game_uid="step0-audit-clean", log_dir=tmp_path,
    )
    assert final_a == final_b
    assert final_a is not Outcome.TECHNICAL_LOSS

    for log_path in (ctx_a.log_path, ctx_b.log_path):
        events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        verdicts = [e for e in events if e["event"] == "audit_verdict"]
        assert verdicts and all(v["matched"] for v in verdicts)
