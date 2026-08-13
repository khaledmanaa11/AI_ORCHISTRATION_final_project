# Phase 5 TODO — Cloud Exposure and Tunneling

**Owner:** Khaled (solo) · **Updated:** 2026-08-13 (verify-work: 8/9 UAT tests pass, criterion 2 human-pending)

> Phase task list. Row IDs and plan IDs are deliberately the same (the Phase-4 convention).
> `/gsd:verify-work 5` marks every row `[x]` and ticks the matching rows in the root
> [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 05-01 Tunnel lifecycle — pyngrok dep, tunnel.json + loader, TunnelManager (DI, reconnect via Table 19 reuse), lifecycle wiring, exchange printout | P0 | ☑ | Khaled | Unit tests all faked; gates green; no secret/number in config (CLOUD-01) |
| 05-02 Shared-secret channel — ASGI middleware, explicit client transport headers, env plumbing, .env-example | P0 | ☑ | Khaled | 403 without header through loopback integration; secret-off default leaves all existing tests untouched (CLOUD-01) |
| 05-03 Gate 5 — smoke script, GATE-5-MEASUREMENT.md (remote round procedure, PENDING item), LOCALTONET-FALLBACK.md, graph refresh | P1 | ☑ | Khaled | Smoke script env-gated + evidence JSON; both §10.4 criteria quoted with evidence paths (CLOUD-02, rule 10) |
| 05-96 Refresh the graphify graph at plan-phase and after execute | P2 | ☑ | Khaled | GRAPH_REPORT.md current with tunnel modules (plan-phase refresh done at 04-13/14; post-execute refresh in 05-03) |
| 05-97 Create/refresh docs/phases/phase-5/{PRD,PLAN,TODO}.md at plan-phase | P1 | ☑ | Khaled | This triplet exists and matches the plan set (created at plan-phase 2026-08-09) |
| 05-99 On verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ◐ | Khaled | Phase gate met incl. the human remote round; all TODOs checked (DOC-01) — **open solely on the criterion-2 remote round** (REMOTE-ROUND-RUNBOOK.md, after Phase 6); every code/doc row above is measured done (05-UAT.md, 2026-08-13) |

## Phase gate (§10.4)
- [x] Each peer is reachable on the public internet through ngrok/Localtonet
      (real run 2026-08-09T09:41:20Z, `verdict: PASS` — gate5_smoke_evidence.json)
- [ ] An agent on a remote machine connects through the tunnel and plays a full round
      against the local agent (human-run; evidence retained per GATE-5-MEASUREMENT.md;
      procedure in REMOTE-ROUND-RUNBOOK.md — the phase's one open item)
