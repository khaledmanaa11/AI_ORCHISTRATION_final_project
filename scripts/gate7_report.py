"""Assembles the GATE-7 evidence JSON from the three criterion measurements.

`gate6_report.py`'s precedent: ONE place the Sec10.4 verdicts are computed
FROM the numbers, and no numeric threshold invented here -- every field is a
measured count/boolean or a verdict that follows directly from one.

TWO RULES THIS FILE EXISTS TO ENFORCE.

1. CRITERION 1 IS NEVER A BLANKET PASS. It carries `dry_run_verdict` and
   `live_send_verdict` as two named fields; the criterion-level `verdict` is
   the STRING that joins them, so a grep for `"verdict": "PASS"` cannot match
   a criterion whose live half has never run.
2. AN EMPTY EVIDENCE SET IS NEVER A PASS. Every criterion's checks include a
   non-zero COUNT, and `EMPTY_EVIDENCE` (exit 2) is reported separately from
   `FAILED` (exit 1) -- `scripts/check_local_truth.py`'s own convention, and
   07-03's rule that a gate which judged nothing must be loud about it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import IntEnum

DRY_RUN_PASS = "PASS"
LIVE_PENDING = "PENDING"
PASS = "PASS"
FAIL = "FAIL"


class GateExit(IntEnum):
    """Process exit codes -- structural, not game parameters."""

    OK = 0
    FAILED = 1
    EMPTY_EVIDENCE = 2


def _criterion_1_counts(c1: dict) -> tuple[int, ...]:
    """The counts that must all be non-zero for criterion 1 to mean anything."""
    return (
        c1["dry_run_end_to_end"]["attachment"]["attachment_count"],
        len(c1["dry_run_end_to_end"]["files_written"]),
        c1["backoff_ladder"]["attempts"],
        len(c1["scope_gate"]["guard_call_sites"]),
        c1["queue_and_drain"]["attempts_before_recovery"],
    )


def _criterion_1_dry_run_verdict(c1: dict) -> str:
    dry, ladder, scope, queue = (
        c1["dry_run_end_to_end"], c1["backoff_ladder"], c1["scope_gate"], c1["queue_and_drain"],
    )
    checks = (
        c1["recipient_is_the_mandatory_address"],
        set(c1["shipped_modes"].values()) == {"dry_run"},
        dry["sent"], dry["refusal"] is None, dry["pending_after_send"] == 0,
        dry["watchdog_touches"] > 0, dry["quota_counter_written_beside_the_run"],
        dry["from_header_absent"], dry["to_header"] == c1["recipient"],
        dry["attachment"]["is_attachment"], dry["attachment"]["reparses_to_the_report"],
        dry["attachment"]["content_type"] == "application/json",
        dry["body"]["is_the_fixed_boilerplate"], dry["body"]["carries_no_report_content"],
        dry["body"]["line_ending_is_crlf"],
        ladder["backoffs_match_config"], ladder["sent"],
        scope["exact_send_scope_accepted"], scope["extra_scope_rejected"],
        scope["empty_scope_rejected"], scope["scope_checked_before_any_credential_is_read"],
        scope["unset_credential_env_var_refuses_loudly"],
        len(scope["guard_call_sites"]) == 2,
        queue["queued"], queue["attempts_equal_one_full_ladder"],
        queue["drained_outcomes_sent"] == [True], queue["pending_after_drain"] == 0,
        all(count > 0 for count in _criterion_1_counts(c1)),
    )
    return DRY_RUN_PASS if all(checks) else FAIL


def _criterion_2_verdict(c2: dict) -> str:
    gate, empty, snapshots, launches = (
        c2["structural_gate"], c2["empty_scan_control"],
        c2["published_snapshot"], c2["live_app_launch"],
    )
    checks = (
        gate["modules_scanned"] > 0, gate["violation_count"] == 0, gate["exit_code"] == 0,
        len(gate["allowed_service_modules"]) > 0,
        empty["missing_root_exit_code"] == empty["expected_exit_code"],
        empty["package_marker_only_exit_code"] == empty["expected_exit_code"],
        *(snapshots[side]["published"] for side in ("police", "thief")),
        *(len(snapshots[side]["top_level_keys"]) > 0 for side in ("police", "thief")),
        *(not snapshots[side]["true_position_fields_present"] for side in ("police", "thief")),
        *(launches[side]["returncode"] == 0 for side in ("police", "thief")),
    )
    return PASS if all(checks) else FAIL


def _criterion_3_verdict(c3: dict) -> str:
    ok, failed, empty = c3["verified_ok"], c3["failed"], c3["nothing_to_verify"]
    checks = (
        c3["outcomes_agree"], c3["sources_existed_before_deletion"],
        all(c3["sources_deleted_before_verifying"].values()),
        ok["state"] == "ok", ok["banner"] == "Verified OK",
        ok["committed"] > 0, ok["verified"] == ok["committed"],
        ok["turn_count"] > ok["committed"],
        failed["state"] == "failed", failed["banner_names_the_tampered_turn"],
        failed["banner_does_not_name_turn_zero"],
        failed["verified"] == failed["committed"] - 1,
        empty["state"] == "nothing_to_verify", empty["banner"] == "Nothing to verify",
        empty["committed"] == 0,
        c3["app_launch"]["returncode"] == c3["app_launch"]["expected_returncode"],
        c3["live_log_refused_by_name"]["returncode"]
        == c3["live_log_refused_by_name"]["expected_returncode"],
        c3["live_log_refused_by_name"]["message_names_rule_18"],
    )
    return PASS if all(checks) else FAIL


def build_report(criterion_1: dict, criterion_2: dict, criterion_3: dict, counters: dict) -> dict:
    dry_run_verdict = _criterion_1_dry_run_verdict(criterion_1)
    return {
        "gate": "GATE-7 (book Sec10.4 milestone 7)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "env_vars_required": [],
        "games_played_counter": counters,
        "criterion_1_game_summary_sent_by_mail": {
            **criterion_1,
            "dry_run_verdict": dry_run_verdict,
            "live_send_verdict": LIVE_PENDING,
            "verdict": f"DRY_RUN {dry_run_verdict}; LIVE {LIVE_PENDING} (07-10)",
        },
        "criterion_2_live_gui_local_truth_only": {
            **criterion_2, "verdict": _criterion_2_verdict(criterion_2),
        },
        "criterion_3_replay_shows_verified_ok": {
            **criterion_3, "verdict": _criterion_3_verdict(criterion_3),
        },
    }


def exit_code(report: dict) -> int:
    """0 only when both machine-closable criteria PASS and criterion 1's
    dry-run half PASSes. The live half is PENDING by design and does not make
    this non-zero -- the GATE DOCUMENT carries that, not this exit code."""
    if not report["criterion_2_live_gui_local_truth_only"]["structural_gate"]["modules_scanned"]:
        return int(GateExit.EMPTY_EVIDENCE)
    verdicts = (
        report["criterion_1_game_summary_sent_by_mail"]["dry_run_verdict"],
        report["criterion_2_live_gui_local_truth_only"]["verdict"],
        report["criterion_3_replay_shows_verified_ok"]["verdict"],
    )
    return int(GateExit.OK) if all(v == PASS for v in verdicts) else int(GateExit.FAILED)
