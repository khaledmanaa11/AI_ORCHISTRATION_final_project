"""Assembles the GATE-6 evidence JSON from the three criterion
measurements (06-04 Task 1) -- mirrors gate4_report.py's own "one place
the Sec10.4 verdicts are computed FROM the numbers" precedent. No numeric
threshold is invented here: every field is either a measured count/
boolean or a verdict that follows directly and honestly from one.
"""

from __future__ import annotations

from datetime import datetime, timezone

_PHASE_KINDS = ("commit", "ack", "reveal")


def _criterion_1_verdict(c1: dict) -> str:
    counts = c1["envelope_counts"]
    has_all_phases = all(
        counts[side].get(kind, 0) > 0
        for side in ("police_sent", "thief_sent")
        for kind in _PHASE_KINDS
    )
    final_reveal_ok = all(c1["final_reveal_audit_confirmed"].values())
    nonce_absent = all(c1["nonce_absent_from_wire_log"].values())
    ledger_ok = (
        c1["ledger_nonce_bearing_records"]["police_all_carry_nonce"]
        and c1["ledger_nonce_bearing_records"]["thief_all_carry_nonce"]
        and c1["ledger_nonce_bearing_records"]["police_count"] > 0
        and c1["ledger_nonce_bearing_records"]["thief_count"] > 0
    )
    decl_ok = all(
        c1["declarations"][side][field]
        for side in ("police", "thief")
        for field in ("own_declaration_exists", "peer_declaration_exists", "predates_first_move_content")
    )
    gate_ok = c1["both_locked_gate_ordering"]["police_ok"] and c1["both_locked_gate_ordering"]["thief_ok"]
    checks = (has_all_phases, final_reveal_ok, nonce_absent, ledger_ok, decl_ok, gate_ok, c1["outcomes_agree"])
    return "PASS" if all(checks) else "FAIL"


def _criterion_2_verdict(c1: dict, c2: dict) -> str:
    a = c2["tamper_a_corrupted_ledger_payload"]
    b = c2["tamper_b_hash_verifies_but_action_differs"]
    checks = (
        a["thief_outcome_is_technical_loss"], a["thief_audit_verdict_matched"] is False,
        a["mismatch_names_h_commit"], a["police_self_audit_also_caught_it"],
        b["hash_alone_still_verified_before_corruption"], b["thief_outcome_is_technical_loss"],
        b["mismatch_names_d67"], b["police_self_audit_stayed_clean"],
        all(c1["nonce_absent_from_wire_log"].values()),
    )
    return "PASS" if all(checks) else "FAIL"


def _criterion_3_verdict(c3: dict) -> str:
    checks = (
        c3["is_step0_mismatch"], c3["aborted_to_error_state"],
        c3["move_1_unreachable_after_abort"], not c3["run_turn_loop_ever_called"],
    )
    return "PASS" if all(checks) else "FAIL"


def build_report(criterion_1: dict, criterion_2: dict, criterion_3: dict) -> dict:
    return {
        "gate": "GATE-6 (book Sec10.4 milestone 6)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "env_vars_required": [],
        "criterion_1_four_phases_commit_reveal": {
            **criterion_1, "verdict": _criterion_1_verdict(criterion_1),
        },
        "criterion_2_hash_nonce_mismatch_technical_loss": {
            **criterion_2,
            "nonce_absent_from_wire_log": criterion_1["nonce_absent_from_wire_log"],
            "verdict": _criterion_2_verdict(criterion_1, criterion_2),
        },
        "criterion_3_step0_verified_before_move_1": {
            **criterion_3, "verdict": _criterion_3_verdict(criterion_3),
        },
    }
