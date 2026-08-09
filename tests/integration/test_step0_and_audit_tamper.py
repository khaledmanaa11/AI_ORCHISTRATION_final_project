"""D-67's own tamper-class proof, at the real two-peer integration level --
imports the harness from test_step0_and_audit.py (mirrors
test_handshake_scent.py importing shared fakes from test_handshake.py).

(a) a corrupted ledger PAYLOAD fails the hash re-verify (check 2) -- the
    OTHER side's audit catches it, its outcome becomes TECHNICAL_LOSS.
(b) THE D-67 case: hash/payload left untouched (still verifies) but what
    the other side actually observed in-game differs from the claim -- the
    hash-only bypass D-67's own rationale describes, genuinely closed.
(d) rule-36 COVERAGE: a side's own FINAL_REVEAL records truncated (one
    genuinely committed-and-revealed turn simply missing) -- the OTHER
    side's audit catches the omission, never passes it vacuously.
"""

from __future__ import annotations

import json

from pursuit.constants import Outcome
from pursuit.network.agent_wiring import load_agent_config
from pursuit.security import commit_pack
from tests.integration.test_step0_and_audit import _play_to_turn_loop_end, _run_audit_and_merge


def _ledger_path(ctx):
    return ctx.log_path.parent / f"{ctx.log_path.stem}.ledger.jsonl"


def _events(log_path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _write_events(log_path, events: list[dict]) -> None:
    log_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


async def test_tamper_a_a_corrupted_ledger_payload_fails_the_hash_check(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
        cfg_a, cfg_b, game_uid="step0-audit-tamper-a", log_dir=tmp_path,
    )

    ledger_path = _ledger_path(ctx_a)
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    record["payload"]["intent"] = "lie" if record["payload"]["intent"] == "truth" else "truth"
    lines[0] = json.dumps(record)
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)

    # The plan's own required assertion: the OTHER side's audit catches it.
    assert final_b is Outcome.TECHNICAL_LOSS
    verdict_b = [e for e in _events(ctx_b.log_path) if e["event"] == "audit_verdict"][-1]
    assert verdict_b["matched"] is False
    assert any("H_commit" in r["detail"] for r in verdict_b["peer_audit"] if not r["matched"])

    # Bonus, not required by the plan but a genuine consequence of the same
    # function: A's OWN self-audit ALSO catches its now-corrupted ledger
    # (CONTEXT, locked: symmetric honesty is real, not suppressed).
    assert final_a is Outcome.TECHNICAL_LOSS


async def test_tamper_b_the_d67_case_hash_verifies_but_action_differs(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
        cfg_a, cfg_b, game_uid="step0-audit-tamper-b", log_dir=tmp_path,
    )

    ledger_lines = _ledger_path(ctx_a).read_text(encoding="utf-8").splitlines()
    genuine = json.loads(ledger_lines[0])
    # Prove the untouched pair genuinely verifies BEFORE corrupting anything
    # -- otherwise a failure below could not be told apart from tamper (a).
    assert commit_pack.verify_reveal(genuine["h_commit"], **genuine["payload"]) is True

    # Corrupt ONLY what B actually observed at reveal time for that turn --
    # A's own ledger/claim (still hashing correctly) is left untouched.
    b_events = _events(ctx_b.log_path)
    reveal_index = next(
        i for i, e in enumerate(b_events)
        if e["event"] == "message_received"
        and e.get("envelope", {}).get("type") == "reveal"
        and e["envelope"]["turn"] == genuine["turn"]
    )
    move = b_events[reveal_index]["envelope"]["payload"]["move"]
    other_direction = "south" if move["direction"] != "south" else "north"
    b_events[reveal_index]["envelope"]["payload"] = {
        **b_events[reveal_index]["envelope"]["payload"],
        "move": {**move, "direction": other_direction},
    }
    _write_events(ctx_b.log_path, b_events)

    final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)

    assert final_b is Outcome.TECHNICAL_LOSS
    verdict_b = [e for e in _events(ctx_b.log_path) if e["event"] == "audit_verdict"][-1]
    mismatches = [r for r in verdict_b["peer_audit"] if not r["matched"]]
    assert mismatches and all("D-67" in r["detail"] for r in mismatches)
    # A's own side never touched anything -- its audit stays clean.
    assert final_a is not Outcome.TECHNICAL_LOSS


async def test_tamper_e_a_skewed_reveal_turn_stamp_no_longer_hides_a_d67_forgery(
    tmp_path, monkeypatch,
):
    """06-05 Gap 1, at the integration level: tamper (b)'s forgery PLUS the
    turn-skew that used to hide it.

    Before 06-05 the audit keyed its evidence on the peer's own declared
    `envelope.turn`, so relabelling the REVEAL envelope sent the entry down
    audit.py's trailing-commit exemption and the D-67 check never ran. The
    record's own turn is ours, so the forgery must still be caught."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
        cfg_a, cfg_b, game_uid="step0-audit-tamper-e", log_dir=tmp_path,
    )

    genuine = json.loads(_ledger_path(ctx_a).read_text(encoding="utf-8").splitlines()[0])
    assert commit_pack.verify_reveal(genuine["h_commit"], **genuine["payload"]) is True

    b_events = _events(ctx_b.log_path)
    # Located by the RECORD's own turn -- B's local truth -- precisely
    # because the envelope's turn is about to become a lie.
    reveal_index = next(
        i for i, e in enumerate(b_events)
        if e["event"] == "message_received"
        and e.get("envelope", {}).get("type") == "reveal"
        and e["turn"] == genuine["turn"]
    )
    move = b_events[reveal_index]["envelope"]["payload"]["move"]
    other_direction = "south" if move["direction"] != "south" else "north"
    b_events[reveal_index]["envelope"]["payload"] = {
        **b_events[reveal_index]["envelope"]["payload"],
        "move": {**move, "direction": other_direction},
    }
    # The skew itself: A claims this reveal belonged to a turn far away.
    b_events[reveal_index]["envelope"]["turn"] = 1001
    _write_events(ctx_b.log_path, b_events)

    final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)

    assert final_b is Outcome.TECHNICAL_LOSS
    verdict_b = [e for e in _events(ctx_b.log_path) if e["event"] == "audit_verdict"][-1]
    mismatches = [r for r in verdict_b["peer_audit"] if not r["matched"]]
    assert mismatches and any("D-67" in r["detail"] for r in mismatches), (
        f"the skew hid the forgery: {[r['detail'] for r in verdict_b['peer_audit']]}"
    )
    assert final_a is not Outcome.TECHNICAL_LOSS


async def test_tamper_d_truncated_final_reveal_records_fail_the_coverage_check(
    tmp_path, monkeypatch,
):
    """Rule-36 coverage check (audit.py's own follow-up fix): a side whose
    FINAL_REVEAL omits a turn it genuinely committed AND revealed in-game
    -- the cheapest form being an entirely empty `{"records": []}` -- must
    not pass the mutual audit vacuously."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
        cfg_a, cfg_b, game_uid="step0-audit-tamper-d", log_dir=tmp_path,
    )

    ledger_path = _ledger_path(ctx_a)
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert lines, "the game must have committed at least one turn to prove anything"
    truncated_turn = json.loads(lines[-1])["turn"]
    ledger_path.write_text("\n".join(lines[:-1]) + ("\n" if len(lines) > 1 else ""), encoding="utf-8")

    final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)

    # THE plan's own required assertion: the OTHER side's audit catches
    # the omission and returns TECHNICAL_LOSS.
    assert final_b is Outcome.TECHNICAL_LOSS
    verdict_b = [e for e in _events(ctx_b.log_path) if e["event"] == "audit_verdict"][-1]
    mismatches = [r for r in verdict_b["peer_audit"] if not r["matched"]]
    assert any(
        r["turn"] == truncated_turn and "absent from final reveal" in r["detail"]
        for r in mismatches
    )
    # Same symmetric-honesty consequence as tamper (a): A's own self-audit
    # also catches its now-incomplete ledger.
    assert final_a is Outcome.TECHNICAL_LOSS
