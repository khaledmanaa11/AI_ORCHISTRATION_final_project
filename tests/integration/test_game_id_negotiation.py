"""05-05 Task 2 (D-61, 05-UAT.md G2): one match, one id, across BOTH sides'
logs, ledgers and declarations.

Why this is a NEW file rather than an assertion added to
test_step0_and_audit.py: that harness takes a SINGLE `game_uid` for both
sides, hardcodes its log stems as "a"/"b" rather than deriving them from the
uid, and never runs `run_agent` (where adoption lives). "All four artifacts
share one stem" is literally unassertable there.

THE PITFALL this file is shaped to avoid: that harness's `_handshake`
closure passes the one shared `game_uid` as `local_game_id`. Copy that and
both sides publish the SAME id, `peer_game_id` matches on both, nothing is
actually adopted, and the test passes while proving nothing. Here EACH SIDE
passes ITS OWN uid as `local_game_id` to BOTH `default_context` and
`perform_handshake`, and the assertions below fail against pre-Task-2 code
(two different stems).
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
from pursuit.network.game_identity import adopt_negotiated_game_id
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.network.turn_commit_ledger import ledger_path
from pursuit.shared.scent_config import scent_digest

UID_A = "aaaa1111aaaa1111"
UID_B = "bbbb2222bbbb2222"


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


async def _play_with_different_uids(cfg_a, cfg_b, log_dir):
    """run_agent's own sequence, both directions, with DELIBERATELY DIFFERENT
    per-side uids -- and log paths DERIVED from them, so a stem that did not
    move is visible as a missing file rather than a passing assertion."""
    step0_a, decl_a = await declare_step0(cfg_a)
    step0_b, decl_b = await declare_step0(cfg_b)

    ctx_a = agent_lifecycle.default_context(
        cfg_a, game_uid=UID_A, log_path=log_dir / "police" / f"{UID_A}.jsonl",
        local_step0_digest=step0_a, local_game_id=UID_A, local_step0_declaration=decl_a,
    )
    ctx_b = agent_lifecycle.default_context(
        cfg_b, game_uid=UID_B, log_path=log_dir / "thief" / f"{UID_B}.jsonl",
        local_step0_digest=step0_b, local_game_id=UID_B, local_step0_declaration=decl_b,
    )
    ctx_a.runtime.client = lambda: Client(ctx_b.runtime.server)
    ctx_b.runtime.client = lambda: Client(ctx_a.runtime.server)

    local_digest = config_digest(cfg_a.config_dir / "game_params.json")
    local_scent_digest = scent_digest(cfg_a.scent)

    async def _handshake(ctx, step0_digest, declaration, own_uid):
        async with ctx.runtime.client() as client:
            return await perform_handshake(
                machine=ctx.machine, reporter=ctx.reporter, local_digest=local_digest,
                local_role=ctx.role, call_peer=make_client_caller(client),
                local_scent_digest=local_scent_digest, local_step0_digest=step0_digest,
                local_game_id=own_uid, local_step0_declaration=declaration,
            )

    result_a = await _handshake(ctx_a, step0_a, decl_a, UID_A)
    result_b = await _handshake(ctx_b, step0_b, decl_b, UID_B)
    assert result_a.agreed and result_b.agreed, f"{result_a}; {result_b}"
    assert result_a.peer_game_id == UID_B and result_b.peer_game_id == UID_A

    pre_adoption_b = ctx_b.log_path.read_text(encoding="utf-8")
    adopt_negotiated_game_id(ctx_a, result_a)
    adopt_negotiated_game_id(ctx_b, result_b)
    write_declaration(ctx_a, cfg_a, result_a, decl_a)
    write_declaration(ctx_b, cfg_b, result_b, decl_b)

    outcome_a, outcome_b = await asyncio.gather(run_turn_loop(ctx_a), run_turn_loop(ctx_b))
    return ctx_a, ctx_b, outcome_a, outcome_b, pre_adoption_b


async def test_all_four_artifacts_join_on_one_negotiated_id(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")

    ctx_a, ctx_b, outcome_a, outcome_b, pre_adoption_b = await _play_with_different_uids(
        cfg_a, cfg_b, tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b

    # 1. All FOUR artifacts share ONE stem across the two sides.
    stems = {p.stem for p in (ctx_a.log_path, ctx_b.log_path)}
    stems |= {ledger_path(ctx_a).stem.removesuffix(".ledger"),
              ledger_path(ctx_b).stem.removesuffix(".ledger")}
    assert stems == {UID_A}, f"the four artifacts do not join: {stems}"
    for path in (ctx_a.log_path, ctx_b.log_path, ledger_path(ctx_a), ledger_path(ctx_b)):
        assert path.exists(), path

    # 2. Both sides COMMITTED the same game_id -- the half that lives inside
    #    the hash, and the half the 2026-08-13 round got wrong.
    committed = {
        json.loads(line)["payload"]["state"]["game_id"]
        for path in (ledger_path(ctx_a), ledger_path(ctx_b))
        for line in path.read_text(encoding="utf-8").splitlines()
    }
    assert committed == {UID_A}, committed

    # 3. The rename lost nothing: every pre-handshake line is still there,
    #    under the negotiated name.
    assert "illegal_transition" in pre_adoption_b
    assert ctx_b.log_path.read_text(encoding="utf-8").startswith(pre_adoption_b)

    # 4. Both declarations name the negotiated id too (unchanged from 06-03,
    #    re-asserted here because it is the artifact that ALREADY joined).
    for ctx in (ctx_a, ctx_b):
        assert (ctx.log_path.parent / f"declaration_{UID_A}.json").exists()


async def test_the_candidate_set_has_two_elements_on_both_roles(tmp_path, monkeypatch):
    """The WIRING assertion, driven through the real production path.

    A `candidate_game_ids` rebuilt from `{game_uid, negotiated_game_id}`
    AFTER adoption yields `{UID_A}` on the thief -- `negotiated_game_id(
    'thief', O, P)` is `P` and `game_uid` has just become `P` -- so the
    audit's membership check degenerates to equality on that role and
    accuses a convention-swapping honest peer. Only a set captured BEFORE
    the rebind passes this on BOTH sides."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")

    ctx_a, ctx_b, _outcome_a, _outcome_b, _pre = await _play_with_different_uids(
        cfg_a, cfg_b, tmp_path,
    )

    assert ctx_a.candidate_game_ids == {UID_A, UID_B}
    assert ctx_b.candidate_game_ids == {UID_A, UID_B}
    assert ctx_a.negotiated_game_id == UID_B and ctx_b.negotiated_game_id == UID_A
    # After adoption the thief's own two "ids" are the SAME string -- the
    # precise reason the set may not be rebuilt from them.
    assert ctx_b.game_uid == ctx_b.negotiated_game_id == UID_A


async def test_the_negotiated_game_ids_survive_the_mutual_audit(tmp_path, monkeypatch):
    """An honest game whose two sides started from different uids must still
    audit clean on BOTH directions once Task 3's state checks are live."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")

    ctx_a, ctx_b, outcome_a, outcome_b, _pre = await _play_with_different_uids(
        cfg_a, cfg_b, tmp_path,
    )
    audit_a, audit_b = await asyncio.gather(
        run_final_audit(ctx_a, board_outcome=outcome_a),
        run_final_audit(ctx_b, board_outcome=outcome_b),
    )
    assert audit_a is not Outcome.TECHNICAL_LOSS and audit_b is not Outcome.TECHNICAL_LOSS

    for ctx in (ctx_a, ctx_b):
        verdicts = [e for e in _read_jsonl(ctx.log_path) if e["event"] == "audit_verdict"]
        assert verdicts and all(v["matched"] for v in verdicts), verdicts
