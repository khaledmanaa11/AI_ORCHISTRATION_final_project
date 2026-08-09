---
status: complete
phase: 06-security-and-cryptography
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md]
started: 2026-08-09T16:58:43Z
updated: 2026-08-09T17:05:00Z
---

## Current Test

[testing complete]

## Tests

> Every result below was re-measured during this UAT session against `HEAD = b3655348`,
> not copied from the plan SUMMARY files.

### 1. GATE-6 runs from one command, zero env vars
expected: measure_gate6.py exits 0 with all three §10.4 criteria PASS, zero env vars, evidence JSON written
result: pass
measured: `uv run python scripts/measure_gate6.py` → EXIT=0, criterion 1/2/3 all PASS. Re-run vs the committed evidence JSON differs in exactly 3 lines, all timestamps (`generated_at`, two `predates_detail` mtimes) — every verdict field byte-identical. Declarations collected in-run carry the real HEAD hash `b3655348e4f48196757f1f8210e078169c470852`, real psutil CPU (12 cores/1700MHz) + RAM (15.68GB), honest `gpu: {present: false, detail: "not detected"}`.

### 2. Four-phase Commit → Ack → Reveal → Final Reveal/Audit runs live between two real peers
expected: a real two-peer localhost game logs commit/ack/reveal envelopes on both sides, every REVEAL strictly after the opponent's COMMIT for that turn (D-58 both-locked gate), and an audit_verdict record at game end
result: pass
measured: police sent 5 commit / 5 ack / 5 reveal, received 5 commit / 5 reveal; thief identical. `both_locked_gate_ordering.{police,thief}_ok = true`, `_violations = []` both sides. `final_reveal_audit_confirmed` true both sides. `outcomes_agree = true` (both `capture`). Honest caveat carried forward: FINAL_REVEAL is not itself an envelope record — evidenced via the `audit_verdict` record (deferred-items.md #1).

### 3. The nonce stays secret until game end
expected: zero "nonce" occurrences in either side's wire-mirroring JSONL during play; every nonce lives only in that side's own <stem>.ledger.jsonl, published for the first time at Final Reveal
result: pass
measured: `nonce_absent_from_wire_log.{police,thief} = true` under BOTH criterion 1 and criterion 2. `ledger_nonce_bearing_records`: 5/5 records carry a nonce on each side. Source-confirmed: `commit_pack.py:112` generates via `secrets.token_hex(16)`, never `random`; comparison via `secrets.compare_digest` (`config_hash.py:59`), never `==`.

### 4. The cop's barrier travels inside the committed action (D-66 / SEC-07)
expected: a forced cop barrier is committed and revealed inside the composite {move, barrier} action, and both engines independently resolve the identical barrier cell with the quota respected
result: pass
measured: `tests/integration/test_commit_reveal_protocol_barrier.py::test_forced_cop_barrier_round_trips_identically_on_both_engines` PASSED. The clean gate run also recorded an honest, non-forced `barrier_placements_this_run: 1`.

### 5. Turning commit-reveal off reproduces the pre-Phase-6 wire exactly
expected: with security.commit_reveal=false on both sides a full game plays with only handshake/move/hint envelope types — no commit/ack/reveal — byte-equivalent to before Phase 6
result: pass
measured: `test_commit_reveal_protocol.py::test_toggle_off_is_byte_equivalent_to_pre_phase_6` PASSED.

### 6. The Step-0 declaration is machine-collected, never hand-typed
expected: role, team_code, OS, CPU cores/frequency, RAM, GPU, LLM name, code version, games played, and the exact git commit hash are gathered by code; an absent GPU reports an honest "not detected", never a fabricated figure
result: pass
measured: live declaration printed during the gate run — `{role, team_code: khm-mn17, os: Windows-10-10.0.26200-SP0, cpu: {cores: 12, freq_mhz: 1700.0}, ram_gb: 15.68…, gpu: {present: false, detail: "not detected"}, llm_name: claude-haiku-4-5, code_version: "1.00", games_played_so_far, commit_hash: b3655348…}`. Commit hash matches the real `git rev-parse HEAD`; no GPU present and none fabricated.

### 7. Step-0 is verified before move 1
expected: a declaration whose content does not hash to its own claimed digest aborts the handshake to State.ERROR with STEP0_MISMATCH; move 1 is then unreachable and the turn loop is never entered
result: pass
measured: criterion 3 — `is_step0_mismatch: true`, `outcome: "step0_mismatch"`, `machine_state: "error"`, `move_1_unreachable_after_abort: true` (explicit `machine.attempt(State.MY_TURN)` after the abort), `run_turn_loop_ever_called: false`. Detail names the fact without accusing: *"step0 declaration content does not hash to its own claimed digest; aborting before move 1"*. Unit-level: all 4 `test_handshake_step0_declaration.py` cases PASSED, including the digest-only peer still agreeing and the wrong-secret HMAC mismatch.

### 8. A forged reveal is a technical loss (D-67)
expected: both tamper classes — a corrupted ledger payload, and the D-67 case where the hash still verifies but the claimed action differs from what was actually played — produce AUDIT_HASH_MISMATCH → TECHNICAL_LOSS; the tampering side's own self-audit catches it too
result: pass
measured: tamper (a) — `thief_outcome_is_technical_loss: true`, `thief_audit_verdict_matched: false`, `mismatch_names_h_commit: true`, `police_self_audit_also_caught_it: true`. tamper (b), the D-67 case — `hash_alone_still_verified_before_corruption: true` (proving a hash-only audit would have missed it), `thief_outcome_is_technical_loss: true`, `mismatch_names_d67: true`, `police_self_audit_stayed_clean: true`. Both `test_step0_and_audit_tamper.py` cases PASSED.

### 9. A peer that publishes no nonces fails the audit (rule 36)
expected: a peer sending FINAL_REVEAL {"records": []}, or silently dropping one fully-exchanged turn, is caught with one named mismatch per omitted turn — not vacuously passed; an honest trailing commit-without-reveal is still matched
result: pass
measured: all 3 `tests/unit/test_audit_coverage.py` cases PASSED (one omitted fully-exchanged turn mismatches exactly that turn; empty records with N turns observed produces N mismatches; a genuinely turn-less game stays vacuously matched). Integration: `test_tamper_d_truncated_final_reveal_records_fail_the_coverage_check` PASSED.

### 10. The Segal §19.1 Table-5 gate is green on the whole repo
expected: ruff check → 0 violations, full pytest suite passes, coverage ≥ 85%, every file ≤ 150 code lines, no secrets in source, uv-only
result: pass
measured: `ruff check .` → *All checks passed!*. `uv run pytest tests/ --cov=src` → **1226 passed, 1 failed** — the failure is the known load-sensitive flake `test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`, re-run in isolation → **passed in 0.18s**. Coverage **99.33%**, "Required test coverage of 85.0% reached". `scripts/check_line_limit.sh` exit 0. `scripts/check_no_llm_in_strategy.py` OK. `config/{police,thief}/security.json` confirmed byte-identical via `diff`.

### 11. Phase 6's grader-facing documents exist and are complete
expected: docs/PRD_commit_reveal.md (per-mechanism PRD, SEC-01..08 traced), docs/phases/phase-6/GATE-6-MEASUREMENT.md + evidence JSON, the phase-6 PRD/PLAN/TODO triplet, and a refreshed .planning/graphs/GRAPH_REPORT.md
result: pass
measured: `docs/PRD_commit_reveal.md` 292 lines, every SEC-01…SEC-08 ID present (grep counts 3/1/2/2/2/2/2/2). `docs/phases/phase-6/` holds PRD.md, PLAN.md, TODO.md, GATE-6-MEASUREMENT.md, gate6_measurement_evidence.json. `.planning/graphs/GRAPH_REPORT.md` refreshed during this verify-work session.

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0

## Gaps

[none — all 11 tests passed on re-measured evidence]

## Standing notes carried forward (not gaps)

Logged honestly in `deferred-items.md`, neither affecting any §10.4 criterion:

1. FINAL_REVEAL is not itself written as a `message_sent`/`message_received` envelope
   record; the Final-Reveal/Audit phase is evidenced by the `audit_verdict` record instead.
2. Measurement and test runs advance the real, gitignored `config/{police,thief}/games_played.json`
   counter — the shipped counter's correct rule-37 behaviour, flagged so a future reader is
   not surprised.
