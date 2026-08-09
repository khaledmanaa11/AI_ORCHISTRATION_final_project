# Phase 6 TODO — Security and Cryptography

**Owner:** Khaled (solo) · **Updated:** 2026-08-09 · **Status: all rows ☑ — closed by `/gsd:verify-work 6`**

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
| 06-99 On verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ☑ | Khaled | Phase gate met on measured evidence; all TODOs checked (DOC-01) — see [06-UAT.md](../../../.planning/phases/06-security-and-cryptography/06-UAT.md), 11/11 pass |

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
