"""D-67's own two-tamper-class proof, at the real two-peer integration
level -- imports the harness from test_step0_and_audit.py (mirrors
test_handshake_scent.py importing shared fakes from test_handshake.py).

(a) a corrupted ledger PAYLOAD fails the hash re-verify (check 2) -- the
    OTHER side's audit catches it, its outcome becomes TECHNICAL_LOSS.
(b) THE D-67 case: hash/payload left untouched (still verifies) but what
    the other side actually observed in-game differs from the claim -- the
    hash-only bypass D-67's own rationale describes, genuinely closed.
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
