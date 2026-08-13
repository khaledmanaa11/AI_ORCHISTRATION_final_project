# Phase 5 TODO — Cloud Exposure and Tunneling

**Owner:** Khaled (solo) · **Updated:** 2026-08-13 (plan-phase --gaps: 05-04..05-08 planned to close the five gaps the 2026-08-13 remote round exposed; criterion 2 still open)

> Phase task list. Row IDs and plan IDs are deliberately the same (the Phase-4 convention).
> `/gsd:verify-work 5` marks every row `[x]` and ticks the matching rows in the root
> [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 05-01 Tunnel lifecycle — pyngrok dep, tunnel.json + loader, TunnelManager (DI, reconnect via Table 19 reuse), lifecycle wiring, exchange printout | P0 | ☑ | Khaled | Unit tests all faked; gates green; no secret/number in config (CLOUD-01) |
| 05-02 Shared-secret channel — ASGI middleware, explicit client transport headers, env plumbing, .env-example | P0 | ☑ | Khaled | 403 without header through loopback integration; secret-off default leaves all existing tests untouched (CLOUD-01) |
| 05-03 Gate 5 — smoke script, GATE-5-MEASUREMENT.md (remote round procedure, PENDING item), LOCALTONET-FALLBACK.md, graph refresh | P1 | ☑ | Khaled | Smoke script env-gated + evidence JSON; both §10.4 criteria quoted with evidence paths (CLOUD-02, rule 10) |
| 05-04 G1 — verdict honesty + bounded teardown grace: a failed OWN final-reveal send stops accusing the peer; technical losses get a corrected `game_over`; `linger_for_peer` (Table 19 `response_timeout` cap / `backoff_seconds` quiet interval, zero new numbers) | P0 | ☐ | Khaled | Send-failure matrix + 3 paired fairness controls green; GATE-6 re-run all three criteria PASS (rules 16/22) |
| 05-05 G2 — the negotiated game id governs log, ledger, declaration AND committed `state.game_id`; audit validates the peer's committed role/turn, and game_id when one was negotiated | P0 | ☐ | Khaled | Four artifacts share one stem across two machines; forged-record probe no longer matched; honest peer publishing no game_id still matched; GATE-6 PASS (D-61, SEC-05/08) |
| 05-06 G3+G4 — inbound HINTs written to the wire log (D-11/D-14, rule 20); relaxed receive window AND responder `pending.turn` stamp landing together; no hint composed for an already-resolved turn | P0 | ☐ | Khaled | Two-peer test: both sides stamp the turn played, both sides decode ≥1 non-`no_hint` hint; the 3 tests that froze the bugs re-specified, none deleted (LANG-01/03) |
| 05-07 G5 — keyless LLM made legible: startup WARNING, honest declared `llm_name`, first-person compose prompt | P1 | ☐ | Khaled | Fallback BEHAVIOUR unchanged (Phase-4 sanctioned); 10 declaration keys unchanged; PRD_deception.md STYLE_GUIDE in sync (rule 38) |
| 05-08 Remote round attempt 2 — HUMAN-RUN on two machines/networks; runbook amended with attempt-1's missing evidence (machine B console, ngrok agent log, clock skew) | P0 | ☐ | Khaled | Two AGREEING verdicts + one shared game UID across all four artifacts, or criterion 2 stays PENDING with the new gaps stated (CLOUD-02) |
| 05-96 Refresh the graphify graph at plan-phase and after execute | P2 | ☑ | Khaled | GRAPH_REPORT.md current with tunnel modules (plan-phase refresh done at 04-13/14; post-execute refresh in 05-03) |
| 05-97 Create/refresh docs/phases/phase-5/{PRD,PLAN,TODO}.md at plan-phase | P1 | ◐ | Khaled | Triplet exists and matches the plan set — refreshed 2026-08-13 for the 05-04..05-08 gap-closure set |
| 05-99 On verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ◐ | Khaled | Phase gate met incl. the human remote round; all TODOs checked (DOC-01) — **open on the criterion-2 remote round AND the five gaps attempt 1 exposed** (05-UAT.md, 2026-08-13) — closed by plans 05-04..05-08 |

## Phase gate (§10.4)
- [x] Each peer is reachable on the public internet through ngrok/Localtonet
      (real run 2026-08-09T09:41:20Z, `verdict: PASS` — gate5_smoke_evidence.json)
- [ ] An agent on a remote machine connects through the tunnel and plays a full round
      against the local agent (human-run; procedure in REMOTE-ROUND-RUNBOOK.md).
      **Attempt 1, 2026-08-13: a full 5-turn game to a real capture across two machines
      on two networks — but the two sides' verdicts disagreed and the two logs carried
      different game UIDs, so the criterion did not close.** Five gaps diagnosed
      (05-UAT.md), planned as 05-04..05-08; attempt 2 runs after they land.
