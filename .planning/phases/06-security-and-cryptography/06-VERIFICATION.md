---
phase: 06-security-and-cryptography
verified: 2026-08-09T16:52:08Z
status: passed
score: 11/11 must-haves verified
---

# Phase 6: Security and Cryptography Verification Report

**Phase Goal:** Commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware
declaration. Requirements SEC-01..SEC-08.
**Verified:** 2026-08-09T16:52:08Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (book §10.4 milestone-6 criteria, quoted from ROADMAP.md, plus the
decisions that support them)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A move is committed (SHA-256) and revealed with a valid nonce; four phases run Commit → Acknowledge → Reveal → Final Reveal/Audit | ✓ VERIFIED | `src/pursuit/security/commit_pack.py::commit` (`hashlib.sha256`); `src/pursuit/network/turn_commit.py::initiate/await_and_respond/reveal_pending` drive COMMIT→ACK→REVEAL; `agent_audit_wiring.py::run_final_audit` + `agent_audit_exchange.py` drive FINAL_REVEAL/Audit. Live-measured: `gate6_measurement_evidence.json` criterion 1 = PASS, 5/5/5 commit/ack/reveal envelopes each side, `final_reveal_audit_confirmed: true` both sides, both-locked-gate ordering `police_ok`/`thief_ok: true` with zero violations. Unit+integration tests (`tests/integration/test_commit_reveal_protocol.py`, `test_commit_reveal_protocol_jitter.py`) pass. |
| 2 | Hash covers canonical-JSON `{state, move, intent, nonce}`; nonce (`secrets.token_hex(16)`) stays secret until game end; any mismatch is a technical loss | ✓ VERIFIED | `build_commit_payload` assembles exactly those 4 keys; `canonical_json` (`pursuit.network.config_hash`) uses `sort_keys=True, separators=(",",":")`; `commit()` calls `secrets.token_hex(16)` (never `random`). Confirmed the nonce never rides `send_and_log`'s payload (only `action_payload = {"move","barrier"}`, no `nonce` key) — nonce lives solely in `CommitLedger`. `gate6_measurement_evidence.json`: `nonce_absent_from_wire_log: {police: true, thief: true}` both criteria 1 and 2; `ledger_nonce_bearing_records`: 5/5 both sides. Mismatch handling: `audit.py::audit_peer_records` + `verdict.TechnicalWinReason.AUDIT_HASH_MISMATCH` → `Outcome.TECHNICAL_LOSS` (`agent_audit_exchange.py::record_audit_verdict`). Live-measured tamper (a) (corrupted payload, caught by re-hash check) and tamper (b) (D-67 bypass case — hash verifies but revealed action differs, caught by the action cross-check) both produced `TECHNICAL_LOSS` — criterion 2 = PASS. |
| 3 | Step-0 hardware declaration (incl. exact commit hash) verified before the first move | ✓ VERIFIED | `step0_collect.collect_declaration` auto-collects OS/CPU/RAM/GPU/`git rev-parse HEAD` (never hand-typed, never a fabricated GPU). `step0_sign.sign_declaration/verify_declaration` (SHA-256 digest always, HMAC when a shared secret exists). `handshake_wire.HandshakeKey.STEP0_DIGEST/STEP0_DECLARATION` + `handshake_evaluate._compare_offer` + `handshake_step0._step0_verified` abort to `HandshakeOutcome.STEP0_MISMATCH`/`State.ERROR` before any move, reusing the existing handshake-abort pathway (no new `State` member — confirmed no diff to `state_machine.py`). Live-measured: `gate6_measurement_evidence.json` criterion 3 = PASS — a forged Step-0 digest aborts with `is_step0_mismatch: true`, `move_1_unreachable_after_abort: true`, `run_turn_loop_ever_called: false`. Both declaration files predate the first move-content record (`declarations.*.predates_first_move_content: true`). |
| 4 (supporting D-59/D-64) | The nonce ledger is durable and separate from the wire-mirroring log | ✓ VERIFIED | `CommitLedger.append` writes+flushes+`os.fsync`s BEFORE any network send (`turn_commit_wait.py::commit_own_action` runs before `send_and_log`). `ledger.py` docstring + code confirm it is never read/written on the wire path. |
| 5 (supporting D-67) | The audit closes the hash-only bypass (commit honestly, reveal a different action) and is symmetric (self-checked too) | ✓ VERIFIED | `audit.py::_audit_one` performs 3 ordered checks (commit observed → hash re-verifies → revealed action matches what was actually observed played); `agent_audit_wiring.py::run_final_audit` runs the SAME function against both the peer's claims and this side's own ledger (`self_audit`), reported with identical `AUDIT_HASH_MISMATCH` honesty either way (no suppression of a self-mismatch). Also closes the rule-36 "empty `{"records": []}`" evasion via `_missing_turns` coverage check (found and fixed during 06-03, documented in 06-03-SUMMARY.md deviation #7). |
| 6 (supporting D-66/SEC-07) | Barrier placement travels openly inside the committed/revealed action and round-trips identically on both engines | ✓ VERIFIED | `turn_commit_wait.build_action_payload` encodes `{"move":..., "barrier": ... or None}`; `turn_actions.py`'s receiver decodes+validates `barrier` through the shipped `move_payload.decode/is_legal(BARRIER)` branch (quota via `barrier_cells`), technical-loss on an illegal/forged barrier just like an illegal move. `tests/integration/test_commit_reveal_protocol_barrier.py::test_forced_cop_barrier_round_trips_identically_on_both_engines` passes; gate6 evidence reports an honest non-forced count (`barrier_placements_this_run: 1`) from the clean run. |
| 7 (SEC-01..08 requirements coverage) | All 8 SEC requirements are addressed | ✓ VERIFIED | SEC-01 (SHA-256), SEC-02 (4 phases), SEC-03 (canonical `{state,move,intent,nonce}`), SEC-04 (`secrets.token_hex(16)` + `compare_digest`), SEC-05 (mismatch → technical loss), SEC-06 (signed Step-0 before move 1), SEC-07 (barrier open on the wire + capture/barrier honesty already enforced structurally by Phase 4's `DeceptionPlan`, now doubly enforced cryptographically via D-67), SEC-08 (mutual audit every game end, both directions) — each traced to code and cited by REQ-ID in `docs/PRD_commit_reveal.md`'s requirements table. |
| 8 (no invented numbers) | Every numeric/algorithmic value in the phase traces to 06-PLAN-OUTLINE.md §2 or an explicitly-labelled structural constant | ✓ VERIFIED | SHA-256, `secrets.token_hex(16)`, `sort_keys=True, separators=(",",":")`, `NetworkParams`-reused retry/backoff, games-played-counter start 0 — all match §2's table. `_COUNTER_RETRIES=3/_COUNTER_BACKOFF_SECONDS=0.1` and `_DECLARE_RETRIES=3/_DECLARE_BACKOFF_SECONDS=0.1` are labelled structural, citing the real, pre-existing `QTable.save()` precedent (`03-05-SUMMARY.md`, confirmed by grep) — not invented. |
| 9 (package boundary) | `security/` imports `sdk`/`shared` only, with exactly the two documented `pursuit.network.config_hash` exceptions | ✓ VERIFIED | `grep "^from\|^import" src/pursuit/security/*.py` shows only `commit_pack.py` and `step0_sign.py` import `pursuit.network.config_hash` (the narrow, doc'd exception); every other file in the package imports only `sdk`/`shared`/stdlib. |
| 10 (toggle-off byte-equivalence) | `security.commit_reveal=false` reproduces the exact pre-Phase-6 wire and resolve timing | ✓ VERIFIED | `turn_commit.py`: all three entry points check `ctx.security.commit_reveal is False` first and delegate to `send_move_only`/`turn_buffer.await_move` verbatim. `tests/integration/test_commit_reveal_protocol.py::test_toggle_off_is_byte_equivalent_to_pre_phase_6` passes. |
| 11 (config symmetry, D-65) | `config/police/security.json` and `config/thief/security.json` are byte-identical | ✓ VERIFIED | `diff` confirms byte-identical; `commit_reveal: true` (league default, both files), `team_code: "khm-mn17"`. |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pursuit/security/commit_pack.py` | `build_commit_payload`/`commit`/`verify_reveal` (D-59) | ✓ VERIFIED | Present, matches spec exactly; uses `canonical_json`/`digests_match` from `config_hash` (the one documented exception); intent validated against `Intent.TRUTH.value`/`Intent.LIE.value` with bool rejection. |
| `src/pursuit/security/state_record.py` | `build_state_record` — D-60 5-field set | ✓ VERIFIED | Exactly `game_id/turn/role/position{row,col}/barriers_remaining`; zero `pursuit.network` import; non-bool-int guard present. |
| `src/pursuit/security/ledger.py` | `CommitLedger.append`/`.read_all`, fsync-durable | ✓ VERIFIED | validate→serialize→write→flush→`os.fsync` order matches `event_log.append_event`; missing file → `[]`, malformed line → `JSONDecodeError` (fail-loud). |
| `src/pursuit/security/step0_collect.py` | `collect_declaration` + games-played counter | ✓ VERIFIED | Full §5.5 field set; honest GPU not-detected fallback; `git rev-parse HEAD` raises loudly on failure; counter via `durable_write_json`. |
| `src/pursuit/security/step0_sign.py` | `digest_declaration`/`sign_declaration`/`verify_declaration` | ✓ VERIFIED | Digest always, HMAC only with a secret; `signed: False`/`hmac: None` explicit when absent. |
| `src/pursuit/security/audit.py` | `audit_peer_records`/`all_matched` — hash re-verify + D-67 revealed-vs-played cross-check | ✓ VERIFIED | 3 ordered checks + rule-36 coverage check (`_missing_turns`); pure function, no ctx/network. |
| `src/pursuit/network/turn_commit.py` + `turn_commit_wait.py` + `turn_commit_send.py` | D-58 both-locked exchange, 3 public entry points | ✓ VERIFIED | Present; split into a THIRD sibling (`turn_commit_send.py`, not originally pre-authorized in the plan) — documented and justified (deviation #3, 06-02-SUMMARY.md) once the two-file split still exceeded 150 lines. `check_line_limit.sh` clean on all three. |
| `src/pursuit/network/agent_context.py` (+ `commit_state.py`) | `AgentContext(+security,+commit_state)`, `CommitTurnState`, `PendingAction` | ✓ VERIFIED | Present; `PendingAction` split into a sibling `commit_state.py` (not in the plan's literal file list, documented) and gained 3 extra fields (`action_payload`/`h_commit`/`turn`) beyond the plan's 5-field sketch — a documented, reasoned bug-prevention fix (deviation #2, 06-02-SUMMARY.md), not scope creep. |
| `src/pursuit/network/handshake_wire.py`/`handshake_evaluate.py`/`handshake_step0.py` | `STEP0_DIGEST`/`STEP0_DECLARATION`, `STEP0_MISMATCH`, content verification | ✓ VERIFIED | Present; `handshake_step0.py` is a new sibling not in the plan's literal file list, split at the same 150-line gate (documented). Digest comparison corrected from equality (plan's literal text) to presence — a genuine, reasoned, tested correction (deviation #1, 06-03-SUMMARY.md) since a per-agent digest can never be equal across roles. |
| `src/pursuit/network/agent_audit_wiring.py` + `agent_audit_exchange.py` | Step-0 declare/write + Final-Reveal audit wiring | ✓ VERIFIED | Present; split into a sibling `agent_audit_exchange.py` (documented, mirrors the `turn_commit.py` 3-file precedent). `agent_entrypoint.py` stays thin (3 new call lines). |
| `config/police/security.json` / `config/thief/security.json` | byte-identical, `commit_reveal: true` default | ✓ VERIFIED | Confirmed via `diff`. |
| `scripts/measure_gate6.py` | localhost, 0 env vars, all 3 criteria PASS | ✓ VERIFIED | Confirmed present; ground-truth run (per task instructions) exits 0, all 3 PASS; evidence JSON matches `GATE-6-MEASUREMENT.md` claims field-for-field. |
| `docs/phases/phase-6/GATE-6-MEASUREMENT.md` + `gate6_measurement_evidence.json` | criteria verbatim + measured PASS evidence | ✓ VERIFIED | Present, quotes ROADMAP §10.4 verbatim, every PASS claim traces to an evidence-JSON field. |
| `docs/PRD_commit_reveal.md` | per-mechanism PRD, house structure | ✓ VERIFIED | Present, 292 lines, mirrors `PRD_mcp_transport.md`'s section order, every SEC-01..08 ID present. |
| `.planning/graphs/GRAPH_REPORT.md` | refreshed to reflect Phase 6 code | ✓ VERIFIED | Last touched at commit `216eec4` (06-04, the phase's final commit); contains `security/`, `turn_commit`, `agent_context`, `handshake_step0` nodes. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `commit_pack.py` | `config_hash.py` | `canonical_json`/`digests_match` reuse | ✓ WIRED | Confirmed import; `digests_match` uses `secrets.compare_digest`, never `==`. |
| `turn_actions.py` | `turn_commit.py` | `initiate`/`await_and_respond`/`reveal_pending` branch on `ctx.commit_state.pending_action` | ✓ WIRED | Confirmed live in integration tests; deadlock-freedom bug found and fixed (documented), re-measured 136s→1.15s. |
| `turn_commit_wait.py` | `security/commit_pack.py` + `ledger.py` | `commit_own_action` builds+commits+ledgers before any send | ✓ WIRED | Confirmed — ledger append precedes `send_and_log` call in both `initiate` and `await_and_respond`. |
| `handshake_evaluate.py` | `verdict.py` (via `agent_audit_exchange.py`) | Final-Reveal mismatch reuses `TechnicalWinReason`, not `HandshakeOutcome` | ✓ WIRED | `AUDIT_HASH_MISMATCH` is a `TechnicalWinReason` member, used post-hoc after `run_turn_loop` returns; Step-0 mismatch is the separate, correct `HandshakeOutcome.STEP0_MISMATCH` pre-move-1 path. Not conflated. |
| `agent_entrypoint.py` | `agent_audit_wiring.py` | Step-0 before handshake, audit after `run_turn_loop` | ✓ WIRED | Confirmed via `test_agent_entrypoint.py` fakes + live integration tests. |
| `audit.py` | `commit_pack.py` | `verify_reveal` is the only re-hash call | ✓ WIRED | Confirmed — `_audit_one` calls `commit_pack.verify_reveal` exactly once. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|---|---|---|
| SEC-01 | ✓ SATISFIED | none |
| SEC-02 | ✓ SATISFIED | none |
| SEC-03 | ✓ SATISFIED | none |
| SEC-04 | ✓ SATISFIED | none |
| SEC-05 | ✓ SATISFIED | none |
| SEC-06 | ✓ SATISFIED | none |
| SEC-07 | ✓ SATISFIED | none (barrier now open on the wire; capture/barrier verbal honesty already structurally enforced by Phase 4's `DeceptionPlan`, doubly closed by D-67's cryptographic cross-check) |
| SEC-08 | ✓ SATISFIED | none |

### Anti-Patterns Found

None. Scanned `src/pursuit/security/`, `turn_commit*.py`, `agent_audit*.py`, `handshake_step0.py`,
`scripts/measure_gate6.py` for TODO/FIXME/placeholder/stub markers and empty-implementation
patterns — zero hits. The one `return []` (in `ledger.py::read_all`) is the documented,
legitimate "no commits yet" case, not a stub.

### Honesty-Critical Properties (verified in code, not just tests)

- **Nonce never on the wire-mirroring JSONL during play:** confirmed by reading
  `turn_commit_send.send_and_log`'s payload construction — it sends `action_payload`
  (`{"move","barrier"}`), never the ledger's `payload` dict that carries `nonce`. Corroborated
  live: `gate6_measurement_evidence.json`'s `nonce_absent_from_wire_log: true` both sides, both
  criteria.
- **Audit catches hash-tamper AND played-vs-revealed divergence AND withheld/missing records:**
  `audit.py::_audit_one`'s 3 ordered checks (commit observed → hash re-verify → revealed action
  matches what was actually played) plus `_missing_turns`'s rule-36 coverage check (a fully
  witnessed turn silently dropped from `peer_records`, e.g. via `{"records": []}`, is caught, not
  vacuously passed). All three live-measured via the gate6 tamper harness and
  `tests/integration/test_step0_and_audit_tamper.py`'s three tamper cases (a/b/d).
- **Own mismatch reported symmetrically:** `agent_audit_wiring.run_final_audit` runs the SAME
  `audit_peer_records` function against `self_audit` (this side's own ledger vs. what it itself
  sent) with the identical `AUDIT_HASH_MISMATCH` label — no suppression path exists in the code.
- **No invented numeric values:** spot-checked `06-PLAN-OUTLINE.md §2`'s table against the
  shipped code — SHA-256, `secrets.token_hex(16)`, canonical-JSON separators, and the
  `NetworkParams`-reused retry/backoff all match; the two new local structural constants
  (`_COUNTER_RETRIES=3/_COUNTER_BACKOFF_SECONDS=0.1`, `_DECLARE_RETRIES=3/_DECLARE_BACKOFF_SECONDS=0.1`)
  are labelled structural and traced to the real, pre-existing `QTable.save()` precedent
  (confirmed present in `03-05-SUMMARY.md`).

### Human Verification Required

None. The phase goal is fully verifiable programmatically: a live, localhost, zero-env-var
`measure_gate6.py` run produces evidence for all three §10.4 criteria (confirmed exit 0, all
three PASS per the task's stated ground truth and corroborated by reading
`gate6_measurement_evidence.json` and re-running the phase's fast unit/integration test subset
directly). No visual, real-time, or external-service behavior is part of this phase's goal.

### Gaps Summary

No gaps. All four plans' must_haves (06-01 crypto core, 06-02 four-phase wire protocol, 06-03
Step-0 + mutual audit, 06-04 GATE-6 measurement + docs) are verified against the actual shipped
code, not just SUMMARY claims. Deviations from the plans' literal text exist (documented in each
plan's own SUMMARY.md: a measured deadlock bug fix, two additional sibling-file splits at the
150-line gate, a corrected Step-0 digest comparison, a coordinator-directed content-verification
follow-up, and a rule-36 audit-coverage-evasion fix) — every one is disclosed, reasoned, tested,
and strengthens rather than weakens the phase's security properties. `deferred-items.md` logs two
non-blocking, honestly-reported findings (FINAL_REVEAL not itself logged as an envelope record —
equivalent evidence exists via the `audit_verdict` record; measurement runs advance the real
games-played counter — correct, intended behavior) for a future polish pass, neither of which
affects any §10.4 criterion.

---

*Verified: 2026-08-09T16:52:08Z*
*Verifier: Claude (gsd-verifier)*
