---
status: diagnosed
phase: 06-security-and-cryptography
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md]
started: 2026-08-09T16:58:43Z
updated: 2026-08-09T17:35:00Z
---

## Current Test

[testing complete — 9 pass, 2 issues, both diagnosed]

## Tests

> Every result below was re-measured during this UAT session against `HEAD = b3655348`,
> not copied from the plan SUMMARY files.
>
> **All three §10.4 gate criteria measured PASS.** The two issues below were found by an
> adversarial audit run *in addition to* the gate: they are cases the gate's own harnesses
> do not construct, because every existing harness stamps envelope turns honestly.

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
result: issue
reported: "Holds for the two tamper classes actually measured, but both are defeated by a peer that skews its own envelope `turn` stamps, and the resulting TECHNICAL_LOSS is not durable."
severity: blocker
measured: the *measured* tamper classes do pass — tamper (a) `thief_outcome_is_technical_loss: true`, `mismatch_names_h_commit: true`, `police_self_audit_also_caught_it: true`; tamper (b) `hash_alone_still_verified_before_corruption: true`, `mismatch_names_d67: true`, `police_self_audit_stayed_clean: true`. **But both harnesses stamp turns honestly.** Reproduced against the shipped `audit_peer_records` with a paired control: commit to action A, play action B, stamp that REVEAL envelope `turn=1001` instead of `1` → `all_matched = True`, detail *"turn 1: trailing commit, no in-game reveal observed -- hash verified"*. The identical data honestly stamped correctly returns *"revealed action does not match what was actually played (D-67)"*. See Gaps 1. Separately, even when a mismatch IS caught, the verdict is not durable — see Gaps 2.

### 9. A peer that publishes no nonces fails the audit (rule 36)
expected: a peer sending FINAL_REVEAL {"records": []}, or silently dropping one fully-exchanged turn, is caught with one named mismatch per omitted turn — not vacuously passed; an honest trailing commit-without-reveal is still matched
result: issue
reported: "The coverage check is keyed on the peer's own declared turn stamps, so the empty-records evasion reopens against a peer that skews them."
severity: blocker
measured: all 3 `tests/unit/test_audit_coverage.py` cases and `test_tamper_d_*` PASSED — but every one hard-codes matching keys in both observed dicts. Reproduced with a paired control: 3 fully-exchanged turns, peer sends `{"records": []}` → honest stamping gives 3 *"committed and revealed in-game but absent from final reveal"* mismatches (`all_matched = False`); the same game with every COMMIT stamped `turn=0` and every REVEAL stamped `turn=99` gives `all_matched = True`, **0 records** — the exact hole (i) evasion, reopened. See Gaps 1.

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
passed: 9
issues: 2
pending: 0
skipped: 0

## Gaps

<!-- Found by a 5-lens adversarial audit run during this verify-work session.
     All five lenses converged independently on Gap 1; all five skeptics failed
     to refute it. Both gaps were then reproduced by hand against the shipped
     code with paired controls before being recorded here. -->

- truth: "A forged reveal, or a withheld set of nonces, is caught by the mutual audit and becomes a technical loss"
  status: failed
  reason: "The audit's join key is attacker-controlled. `observed()` builds BOTH observed_commits and observed_reveals keyed on `envelope.get(EnvelopeKey.TURN)` — the peer's own declared turn number, taken verbatim off the wire. Nothing in src/ ever compares an inbound envelope's turn to ctx.state.turn (grep for `.turn ==` / `envelope.turn` returns only sites that CONSUME it as a key). So a peer that stamps its COMMIT and REVEAL envelopes with disjoint turn numbers makes `set(observed_commits) & set(observed_reveals)` empty, which (a) makes _missing_turns' rule-36 coverage check yield nothing, re-opening the empty-`{\"records\": []}` evasion, and (b) sends every entry down _audit_one's `turn not in observed_reveals` branch, which returns matched=True as a 'trailing commit'. The cheapest variant stamps every envelope turn=0, collapsing a whole game to one key: a single valid record then satisfies the audit of an N-turn game and N-1 nonces stay secret forever."
  severity: blocker
  test: 8, 9
  root_cause: "`agent_audit_exchange.observed()` keys the audit's two evidence dicts on untrusted peer-declared `envelope.turn`; `audit.py`'s trailing-commit exemption and coverage check both trust those keys as local truth."
  artifacts:
    - path: "src/pursuit/network/agent_audit_exchange.py:78"
      issue: "turn = envelope.get(EnvelopeKey.TURN) — attacker-supplied value used as the audit's join key for both dicts (:81, :83)"
    - path: "src/pursuit/security/audit.py:62"
      issue: "`if turn not in observed_reveals` returns matched=True (trailing-commit exemption) — reachable for EVERY turn once the keys are skewed"
    - path: "src/pursuit/security/audit.py:82"
      issue: "`fully_exchanged = set(observed_commits) & set(observed_reveals)` — empties out under skew, so the rule-36 coverage check yields nothing"
    - path: "src/pursuit/network/turn_commit_wait.py:107-170"
      issue: "all four D-58 waits match on MessageType + payload h_commit only; none validates envelope.turn against ctx.state.turn"
    - path: "tests/unit/test_audit_coverage.py"
      issue: "every case hard-codes matching keys in both observed dicts, so the suite cannot see this class of bypass"
  missing:
    - "Validate an inbound COMMIT/REVEAL envelope's turn against local turn state on the receive path, and reject/technical-loss on mismatch (the honest peer always knows the true turn number)"
    - "OR key observed_commits/observed_reveals on locally-authoritative turn state rather than the peer's declared value"
    - "A regression test whose observed_commits and observed_reveals keys DISAGREE, asserting the audit still reports a mismatch"

- truth: "Any mismatch is a technical loss (§10.4 criterion 2)"
  status: failed
  reason: "When the audit DOES catch a cheat, the verdict never reaches anything durable. `turn_events.game_over_record` has exactly one call site (orchestrator.py:105), inside run_turn_loop — so the JSONL's only outcome-bearing line is written with the BOARD outcome BEFORE run_final_audit runs (agent_entrypoint.py:73-77). run_final_audit's Outcome.TECHNICAL_LOSS is returned up to run_agent, and main.py then discards it: `asyncio.run(agent_lifecycle.run_agent(args.config_dir))` followed by an unconditional `return 0`. The result is an audit_verdict line appended after a game_over line that still records the cheater's win, and a zero exit code. Any Phase-7 reporter reading the outcome field reads the cheater's result."
  severity: major
  test: 8
  root_cause: "game_over is recorded before the audit runs and is never corrected; run_agent's overridden outcome is discarded by main.py."
  artifacts:
    - path: "src/pursuit/network/orchestrator.py:105"
      issue: "the only game_over_record call site — runs before run_final_audit"
    - path: "src/pursuit/main.py:51"
      issue: "asyncio.run(run_agent(...)) discards the returned outcome; `return 0` unconditionally"
  missing:
    - "Write a corrected game_over (or an explicit outcome-superseding record) after the audit overrides the outcome"
    - "Propagate the final outcome to main.py's exit code"

## Standing notes carried forward (not gaps)

## Standing notes carried forward (not gaps)

Logged honestly in `deferred-items.md`, neither affecting any §10.4 criterion:

1. FINAL_REVEAL is not itself written as a `message_sent`/`message_received` envelope
   record; the Final-Reveal/Audit phase is evidenced by the `audit_verdict` record instead.
2. Measurement and test runs advance the real, gitignored `config/{police,thief}/games_played.json`
   counter — the shipped counter's correct rule-37 behaviour, flagged so a future reader is
   not surprised.
