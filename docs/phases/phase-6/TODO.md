# Phase 6 TODO — Security and Cryptography

**Owner:** Khaled (solo) · **Updated:** 2026-08-09 · **Status: all rows ☑ — §10.4 gate met,
the 2 security gaps `/gsd:verify-work 6` found were closed by plan 06-05, gate re-measured.**

> Phase task list. Row IDs and plan IDs are deliberately the same (the Phase-4 convention).
> `/gsd:verify-work 6` marks every row `[x]` and ticks the matching rows in the root
> [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 06-01 Crypto core — `security/` package (commit_pack, state_record, ledger), `security_config.py`, `security.json` pair | P0 | ☑ | Khaled | Commit→reveal→audit round-trip proven in one test; any single-field tamper disagrees; ledger durable with nonce intact; config pair byte-identical (SEC-01, SEC-03, SEC-04) |
| 06-02 Four-phase wire protocol — 4 message kinds, the both-locked Commit→Ack→Reveal exchange, barriers inside the committed action, toggle-off byte-equivalence | P0 | ☑ | Khaled | Two-peer game shows commit/ack/reveal; every REVEAL follows the opponent's COMMIT; a forced cop barrier round-trips and applies identically on both engines; no nonce in any wire log (SEC-01, SEC-02, SEC-04, SEC-07) |
| 06-03 Step-0 declaration + Final-Reveal mutual audit — collect/sign/verify, handshake third digest, negotiated `game_id`, audit verdicts | P0 | ☑ | Khaled | Declaration written and verified before move 1; a mismatch aborts like SCENT_MISMATCH; both tamper classes produce `AUDIT_HASH_MISMATCH` → `TECHNICAL_LOSS`; our own mismatch reported truthfully (SEC-05, SEC-06, SEC-07, SEC-08) |
| 06-04 Gate 6 — `measure_gate6.py`, `GATE-6-MEASUREMENT.md`, `docs/PRD_commit_reveal.md` | P1 | ☑ | Khaled | One command, zero env vars, real localhost evidence per criterion; PASS/FAIL reported honestly; per-mechanism PRD complete (SEC-01…SEC-08, DOC-02) |
| 06-96 Refresh the graphify graph at plan-phase and after execute | P2 | ☑ | Khaled | GRAPH_REPORT.md current with `security/`, `turn_commit.py`, `agent_context.py` (plan-phase refresh 2026-08-09; post-06-01 refresh 6035 nodes/10756 edges/384 communities; 06-04 refresh 6510/11909/408; final verify-work refresh 2026-08-09 → **6577 nodes / 11972 edges / 413 communities**) |
| 06-97 Create/refresh docs/phases/phase-6/{PRD,PLAN,TODO}.md at plan-phase | P1 | ☑ | Khaled | This triplet exists and matches the plan set (created at plan-phase 2026-08-09; all rows closed at verify-work) |
| 06-99 On verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ☑ | Khaled | Phase gate met on measured evidence; all TODOs checked (DOC-01) — see [06-UAT.md](../../../.planning/phases/06-security-and-cryptography/06-UAT.md), **9/11 pass, 2 gaps open** |
| 06-05 **GAP CLOSURE** — audit join key + verdict durability | P0 | ☑ | Khaled | Audit keyed on local turn truth, so turn-skew can no longer convert a forgery into a "trailing commit" nor empty the coverage set; `test_audit_turn_binding.py`'s two observed dicts DISAGREE and still mismatch (non-vacuous: 4/5 fail against pre-fix code); caught mismatch produces a corrected `game_over` + non-zero exit (SEC-05, SEC-08) |
| 06-06 **GAP CLOSURE** — peer-fault containment + sender validation | P1 | ☑ | Khaled | A peer `ToolError` ends the game through the technical-loss path instead of killing us before FINAL_REVEAL (rule 36); every game-message handler rejects a non-opponent `sender` (handshake deliberately exempt, tested); measured with both live — suite 1251/1251, GATE-6 all three PASS (SEC-05, SEC-08) |

## Phase gate (§10.4)
- [x] A move is committed (SHA-256) and then revealed with a valid nonce; the four phases run
      Commit → Acknowledge → Reveal → Final Reveal/Audit
      — **PASS**, re-measured 2026-08-09 at `HEAD=b3655348`: 5/5/5 commit/ack/reveal both sides,
      both-locked ordering 0 violations, `final_reveal_audit_confirmed` true both sides
- [x] The hash covers canonical-JSON `{state, move, intent, nonce}`; the nonce
      (`secrets.token_hex(16)`) stays secret until game end; any mismatch is a technical loss
      — **PASS**: `nonce_absent_from_wire_log` true both sides, 5/5 nonce-bearing ledger records
      each side, both tamper classes → `AUDIT_HASH_MISMATCH` / `TECHNICAL_LOSS`
- [x] The Step-0 hardware declaration (incl. exact commit hash) is verified before the first move
      — **PASS**: forged digest → `STEP0_MISMATCH`, `machine_state: error`,
      `move_1_unreachable_after_abort: true`, `run_turn_loop_ever_called: false`

Unlike GATE-4 and GATE-5, **every criterion here is machine-measurable on this one machine** —
no API key, no ngrok account, no second host. There is no human-pending item in this phase.

## The gate was not the whole security story — both gaps CLOSED by 06-05

The three criteria above are met and measured. Separately, a 5-lens adversarial audit run
during `/gsd:verify-work 6` found two real gaps, both reproduced against the shipped code
with paired controls, **both now fixed and proven fixed**:

1. **(blocker)** The mutual audit's join key is the peer's own declared `envelope.turn`
   (`agent_audit_exchange.py:78`), which nothing on the receive path validates. Skewing it
   sends every entry down `audit.py:62`'s trailing-commit exemption and empties
   `audit.py:82`'s coverage intersection — reopening BOTH the D-67 forgery bypass and the
   rule-36 empty-`{"records": []}` evasion. Every existing harness stamps turns honestly,
   so no current test can see it.
2. **(major)** A caught mismatch is not durable: `game_over` is written before the audit
   runs (`orchestrator.py:105`) and never corrected, and `main.py:51` discards the
   overridden outcome and returns 0.

Closed by plan **06-05** (`4012a18`, `e5ec5b5`, `eecd4be`, `65db6d9`): the audit is keyed on
local turn truth, and a caught mismatch appends a corrected `game_over` and exits non-zero.
`security/audit.py` was deliberately not modified — its checks were correct and were being fed
attacker-controlled keys. GATE-6 re-measured after the fix: all three criteria still PASS.
Detail, exploit paths, controls, and resolutions: `06-UAT.md` Gaps and `06-05-SUMMARY.md`.

Two further findings from the same audit — an uncaught `ToolError` killing the agent mid-game
before it publishes its nonces, and `_accept` never checking an envelope's `sender` — were
**also closed**, by plan **06-06** (`877f617`, `78ebb8c`). Measured with both fixes live: full
suite 1251/1251, GATE-6 all three criteria PASS. `deferred-items.md` #1-#2 remain open by
design (a logging-granularity gap with equivalent evidence, and the counter's correct rule-37
behaviour); neither affects a §10.4 criterion.
