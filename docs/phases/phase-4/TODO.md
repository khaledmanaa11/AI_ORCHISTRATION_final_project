# Phase 4 TODO — Language and Scent

**Owner:** Khaled (solo) · **Updated:** 2026-08-09

> Phase task list. Mirrors the `.planning/` plan for Phase 4. `/gsd:verify-work 4` marks every
> row `[x]` (☑) and ticks the matching rows in the root [docs/TODO.md](../../TODO.md) — **not
> before 04-14 has measured GATE-4** (see [`PRD.md`](PRD.md) §2, §8).
> **Status:** ☐ not started · ◐ in progress / executed-not-verified · ☑ done (verify-work only)
> · **Priority:** P0/P1/P2

**Namespace note, stated plainly so no future reader has to wonder (Phase 3's own TODO.md hit
this same question and answered it differently — see its own file for that phase's shape):**
**in this file the row IDs and the `.planning/` execution-plan IDs are deliberately the same
number.** Row `04-05` below is plan `04-05-PLAN.md`, not an aggregated milestone the way Phase
3's `03-01`…`03-04` rows each summarised several `03-1N`/`03-2N` execution plans. Phase 4 has
exactly fourteen numbered execution plans and this table has exactly fourteen matching rows
plus the three roadmap tasks (`04-96`/`97`/`99`) — a 1:1 mapping, by design.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 04-01 Locked scent model — kernel table, decay law, `ScentField`, digest helper | P0 | ◐ | Khaled | Table 16 values + Figure-4 kernel exact; digest stable and shipped (LANG-04, LANG-07) |
| 04-02 Handshake carries the scent digest (rule 23) | P0 | ◐ | Khaled | `SCENT_MISMATCH` distinct from `CONFIG_MISMATCH`, `secrets.compare_digest` |
| 04-03 LLM gatekeeper — token bucket, FIFO queue, budget ladder | P0 | ◐ | Khaled | Overflow queues, never crashes (QUAL-03, QUAL-05) |
| 04-04 Transport — `MessageType.HINT`, direction-token move codec | P0 | ◐ | Khaled | Coordinates off the outgoing wire; legacy `{x,y}` still decoded (LANG-01, LANG-02) |
| 04-05 Belief map core — grid, motion model, scent likelihood | P0 | ◐ | Khaled | Regime A/B both exercised on one `BeliefMap` object (LANG-05) |
| 04-06 Provider layer — registry, `template`, `claude_api` (Haiku 4.5) | P0 | ◐ | Khaled | No key → degrades to `NO_KEY`, never crashes (LANG-06) |
| 04-07 Hint decoder — constrained JSON, EN + HE, total | P0 | ◐ | Khaled | Every failure path → `NO_EVIDENCE`, never raises (LANG-06) |
| 04-08 Deception planner — intent + claim, both role policies | P0 | ◐ | Khaled | A lying capture/barrier claim is unconstructable (LANG-03, STRAT-07) |
| 04-09 Belief fusion — hint likelihood, adaptive reliability, lie detector | P0 | ◐ | Khaled | Sec4.4's 0.9→0.81 worked example reproduced exactly (LANG-05) |
| 04-10 Bluff generator — word limit, retry, truncate, template bank | P0 | ◐ | Khaled | `compose()` never empty, never over-limit, never raises (LANG-01, LANG-02) |
| 04-11 `BeliefAdapter` — sample from belief, believed-state substitution | P0 | ◐ | Khaled | Option A proven exact in Regime A, coordinate-only diff in Regime B (LANG-05, STRAT-07) |
| 04-12 Turn-pipeline integration — Figure 7 wired into the live loop | P0 | ◐ | Khaled | Real two-peer game completes; `PLACEHOLDER_HINT_TEXT` gone (LANG-01…06) |
| 04-13 Three per-mechanism PRDs, rules-resolution note, phase triplet | P1 | ◐ | Khaled | This triplet + `docs/PRD_{scent_map,belief_map,deception}.md` + `RULES-RESOLUTION-LANG.md` committed (DOC-01, DOC-02) |
| 04-14 GATE-4 measurement against the live API | P0 | ☐ | Khaled | All three §10.4 gate behaviours measured against a real game; robustness paths reconfirmed live |
| 04-96 Refresh the knowledge graph after new code lands | P1 | ◐ | Khaled | `GRAPH_REPORT.md` reflects the wave-6/7 tree; `services/llm/` has no edge into `strategy/` |
| 04-97 Create/refresh `docs/phases/phase-4/{PRD,PLAN,TODO}.md` | P1 | ◐ | Khaled | This triplet exists and describes what was actually built (not what was planned) |
| 04-99 On verify-work, mark all Phase 4 TODOs `[x]` in the phase triplet + root `docs/TODO.md` | P1 | ☐ | Khaled | Runs only after 04-14 measures GATE-4; not this plan's job |

## Phase gate (§10.4)

- [ ] A hint becomes an inference (belief map updates via Bayes from a decoded hint; a
      schema-invalid hint changes nothing) — mechanism proven in unit/integration tests
      (`docs/PRD_belief_map.md` §4), **live-game measurement pending 04-14**.
- [ ] The scent map updates and decays (0.9/0.10/5×5, decay law asserted over ≥10 turns, digests
      matched at handshake) — mechanism proven, **live-game reconfirmation pending 04-14**.
- [ ] The LLM emits a ≤15-word hint every turn, true and false, `intent` fixed before the text —
      mechanism proven against mocked/template providers, **live-API measurement pending 04-14**.

This gate is unticked because it is unmeasured against the real API, not because the mechanisms
are unbuilt. See [`PRD.md`](PRD.md) §2 for the exact bar 04-14 measures against.
