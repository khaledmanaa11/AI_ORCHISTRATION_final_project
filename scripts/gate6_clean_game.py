"""Criterion-1 evidence (06-PLAN-OUTLINE.md Sec5 row 1): one clean game
through the REAL shipped config/police + config/thief, played via the SAME
two-peer harness 06-03's own tests already use --
`tests.integration.test_step0_and_audit._play_to_turn_loop_end` +
`_run_audit_and_merge` -- never a second, parallel game-runner.

Reports, never invents, every count: envelope-type occurrences per side,
nonce presence/absence, per-side ledger nonce-bearing records, the D-58
both-locked-gate ordering, the Step-0 declaration files, and an honest
barrier-placement count (0 is a valid outcome of a clean run -- the forced
round-trip PROOF a barrier CAN be committed/revealed lives in 06-02's own
tests/integration/test_commit_reveal_protocol_barrier.py, cited by name).

NOTE (honesty, not a bug): `agent_audit_exchange.py`'s FINAL_REVEAL
push/receive is never itself logged as a message_sent/message_received
envelope record (only `record_audit_verdict`/`record_technical_loss`
write to the JSONL) -- so Final-Reveal/Audit's own occurrence is measured
via the `audit_verdict` record's presence, not an envelope-type count.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from gate6_common import events, ledger_path, load_configs, wire_log_text
from gate6_declarations import declaration_evidence

from pursuit.constants import Outcome
from pursuit.security.commit_pack import CommitKey
from pursuit.security.ledger import CommitLedger
from tests.integration.test_step0_and_audit import _play_to_turn_loop_end, _run_audit_and_merge

GAME_UID = "gate6-clean"


def _envelope_type_counts(records: list[dict], direction: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        if r.get("event") != direction:
            continue
        kind = r.get("envelope", {}).get("type")
        if kind is not None:
            counts[kind] = counts.get(kind, 0) + 1
    return counts


def _both_locked_ordering(records: list[dict]) -> tuple[bool, list[str]]:
    """D-58: this side's own REVEAL-sent line index must exceed the
    opponent's COMMIT-received line index, for the SAME turn, every turn."""
    reveal_sent: dict[int, int] = {}
    commit_received: dict[int, int] = {}
    for i, r in enumerate(records):
        env = r.get("envelope", {})
        turn = env.get("turn")
        if r.get("event") == "message_sent" and env.get("type") == "reveal":
            reveal_sent[turn] = i
        elif r.get("event") == "message_received" and env.get("type") == "commit":
            commit_received[turn] = i
    violations = [
        f"turn {t}: reveal@{i} <= commit@{commit_received.get(t)}"
        for t, i in reveal_sent.items()
        if commit_received.get(t) is None or i <= commit_received[t]
    ]
    return not violations, violations


def _barrier_count(records: list[dict]) -> int:
    return sum(
        1
        for r in records
        if r.get("event") == "message_sent"
        and r.get("envelope", {}).get("type") == "reveal"
        and r.get("envelope", {}).get("payload", {}).get("barrier") is not None
    )


async def measure_clean_game() -> dict:
    cfg_a, cfg_b = load_configs()
    with tempfile.TemporaryDirectory() as tmp:
        log_dir = Path(tmp)
        outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
            cfg_a, cfg_b, game_uid=GAME_UID, log_dir=log_dir,
        )
        final_a, final_b = await _run_audit_and_merge(outcome_a, outcome_b, ctx_a, ctx_b)

        records_a, records_b = events(ctx_a.log_path), events(ctx_b.log_path)
        ledger_a = CommitLedger(ledger_path(ctx_a)).read_all()
        ledger_b = CommitLedger(ledger_path(ctx_b)).read_all()
        wire_text_a, wire_text_b = wire_log_text(ctx_a.log_path), wire_log_text(ctx_b.log_path)
        nonce_key = f'"{CommitKey.NONCE.value}"'

        ok_a, violations_a = _both_locked_ordering(records_a)
        ok_b, violations_b = _both_locked_ordering(records_b)

        return {
            "game_uid": GAME_UID,
            "final_outcome_police": final_a.value if isinstance(final_a, Outcome) else str(final_a),
            "final_outcome_thief": final_b.value if isinstance(final_b, Outcome) else str(final_b),
            "outcomes_agree": final_a == final_b,
            "envelope_counts": {
                "police_sent": _envelope_type_counts(records_a, "message_sent"),
                "police_received": _envelope_type_counts(records_a, "message_received"),
                "thief_sent": _envelope_type_counts(records_b, "message_sent"),
                "thief_received": _envelope_type_counts(records_b, "message_received"),
            },
            "nonce_absent_from_wire_log": {
                "police": nonce_key not in wire_text_a,
                "thief": nonce_key not in wire_text_b,
            },
            "ledger_nonce_bearing_records": {
                "police_count": len(ledger_a),
                "police_all_carry_nonce": all(CommitKey.NONCE.value in r["payload"] for r in ledger_a),
                "thief_count": len(ledger_b),
                "thief_all_carry_nonce": all(CommitKey.NONCE.value in r["payload"] for r in ledger_b),
            },
            "both_locked_gate_ordering": {
                "police_ok": ok_a, "police_violations": violations_a,
                "thief_ok": ok_b, "thief_violations": violations_b,
            },
            "declarations": {
                "police": declaration_evidence(ctx_a, GAME_UID),
                "thief": declaration_evidence(ctx_b, GAME_UID),
                "note": (
                    "both sides share GAME_UID by construction in this harness "
                    "(same caveat test_step0_and_audit.py's own docstring states); "
                    "the LOAD-BEARING D-61 negotiation proof (deliberately "
                    "DIFFERENT local_game_id per side) is "
                    "tests/unit/test_handshake_step0.py::"
                    "test_game_id_negotiation_resolves_to_the_initiators_value"
                ),
            },
            "final_reveal_audit_confirmed": {
                "police": any(r.get("event") == "audit_verdict" for r in records_a),
                "thief": any(r.get("event") == "audit_verdict" for r in records_b),
            },
            "final_reveal_note": (
                "FINAL_REVEAL push/receive (agent_audit_exchange.py) is not itself "
                "logged as a message_sent/message_received envelope record -- only "
                "record_audit_verdict()/record_technical_loss() write to the JSONL. "
                "Final-Reveal/Audit's occurrence is therefore measured via the "
                "audit_verdict record's presence, not an envelope-type count."
            ),
            "barrier_placements_this_run": _barrier_count(records_a) + _barrier_count(records_b),
            "barrier_note": (
                "an honest count from this ONE clean run -- 0 is a valid outcome if "
                "the scripted cop brain never chose to place one; the forced "
                "round-trip PROOF that a barrier CAN be committed/revealed/applied "
                "lives in tests/integration/test_commit_reveal_protocol_barrier.py "
                "(06-02), cited here by name, not re-run"
            ),
        }
