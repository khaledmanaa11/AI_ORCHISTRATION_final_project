"""Criterion-2 evidence: the SAME two D-67 tamper-harness proofs 06-03
already tests (tests/integration/test_step0_and_audit_tamper.py's
`test_tamper_a_*`/`test_tamper_b_*`), re-run here end to end through
`measure_gate6.py` itself and captured as evidence -- never a third,
parallel tamper harness. Reuses the SAME `_play_to_turn_loop_end`/
`_run_audit_and_merge` pair `gate6_clean_game.py` uses.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from gate6_common import events, ledger_path, load_configs

from pursuit.constants import Outcome
from pursuit.security import commit_pack
from tests.integration.test_step0_and_audit import _play_to_turn_loop_end, _run_audit_and_merge


def _write_events(log_path: Path, records: list[dict]) -> None:
    log_path.write_text("\n".join(json.dumps(e) for e in records) + "\n", encoding="utf-8")


def _last_audit_verdict(records: list[dict]) -> dict:
    return [r for r in records if r.get("event") == "audit_verdict"][-1]


async def _tamper_a_corrupted_ledger_payload() -> dict:
    """(a): corrupt one entry's PAYLOAD in police's own ledger -- thief's
    audit of police's claims must fail the re-hash check (check 2), and
    police's own self-audit must independently catch its own corrupted
    ledger too (symmetric honesty)."""
    cfg_a, cfg_b = load_configs()
    with tempfile.TemporaryDirectory() as tmp:
        outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
            cfg_a, cfg_b, game_uid="gate6-tamper-a", log_dir=Path(tmp),
        )
        path = ledger_path(ctx_a)
        lines = path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[0])
        record["payload"]["intent"] = "lie" if record["payload"]["intent"] == "truth" else "truth"
        lines[0] = json.dumps(record)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)
        verdict_b = _last_audit_verdict(events(ctx_b.log_path))
        mismatches = [r for r in verdict_b["peer_audit"] if not r["matched"]]
        return {
            "thief_outcome_is_technical_loss": final_b is Outcome.TECHNICAL_LOSS,
            "thief_audit_verdict_matched": verdict_b["matched"],
            "mismatch_names_h_commit": any("H_commit" in r["detail"] for r in mismatches),
            "police_self_audit_also_caught_it": final_a is Outcome.TECHNICAL_LOSS,
        }


async def _tamper_b_hash_verifies_action_differs() -> dict:
    """(b) THE D-67 case: ledger/hash left completely untouched
    (independently re-verified via commit_pack.verify_reveal before any
    corruption), but what thief actually observed played in-game is
    corrupted for one turn -- must still fail, proving the hash-only
    check ALONE would have missed the forgery."""
    cfg_a, cfg_b = load_configs()
    with tempfile.TemporaryDirectory() as tmp:
        outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
            cfg_a, cfg_b, game_uid="gate6-tamper-b", log_dir=Path(tmp),
        )
        genuine = json.loads(ledger_path(ctx_a).read_text(encoding="utf-8").splitlines()[0])
        hash_alone_still_verifies = commit_pack.verify_reveal(genuine["h_commit"], **genuine["payload"])

        b_events = events(ctx_b.log_path)
        reveal_index = next(
            i for i, e in enumerate(b_events)
            if e.get("event") == "message_received"
            and e.get("envelope", {}).get("type") == "reveal"
            and e["envelope"]["turn"] == genuine["turn"]
        )
        move = b_events[reveal_index]["envelope"]["payload"]["move"]
        other = "south" if move["direction"] != "south" else "north"
        b_events[reveal_index]["envelope"]["payload"] = {
            **b_events[reveal_index]["envelope"]["payload"],
            "move": {**move, "direction": other},
        }
        _write_events(ctx_b.log_path, b_events)

        final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)
        verdict_b = _last_audit_verdict(events(ctx_b.log_path))
        mismatches = [r for r in verdict_b["peer_audit"] if not r["matched"]]
        return {
            "hash_alone_still_verified_before_corruption": hash_alone_still_verifies,
            "thief_outcome_is_technical_loss": final_b is Outcome.TECHNICAL_LOSS,
            "mismatch_names_d67": bool(mismatches) and all("D-67" in r["detail"] for r in mismatches),
            "police_self_audit_stayed_clean": final_a is not Outcome.TECHNICAL_LOSS,
        }


async def measure_tamper() -> dict:
    return {
        "tamper_a_corrupted_ledger_payload": await _tamper_a_corrupted_ledger_payload(),
        "tamper_b_hash_verifies_but_action_differs": await _tamper_b_hash_verifies_action_differs(),
    }
