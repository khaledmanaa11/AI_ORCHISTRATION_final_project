# Phase 3 TODO — Blind Strategy Module (RL policy)

**Owner:** Khaled (solo) · **Updated:** 2026-07-31

> Phase task list. Mirrors the `.planning/` plans for Phase 3. `/gsd:verify-work 3` marks
> every row `[x]` and ticks the matching rows in the root [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 03-00 Phase-3 scaffold + config sections + test stubs | P0 | ☑ | Khaled | `uv add --dev matplotlib`; `[strategy]` + `[training]` sections in `config/{police,thief}/`; `StrategyKey`/`TrainingKey` enums; hyperparameters loaded through the existing `loader_helpers` (QUAL-02/11/13); test stubs collect and exit 0 |
| 03-01 `docs/PRD_rl_strategy.md` | P0 | ☑ | Khaled | v1.00; state encoding, reward function, update rule, fallback trigger and sparring pool all specified; every number carries a Source column marking it PARAMETERS.md vs engineering default. Written **before** the policy code it describes (DOC-02, SEGAL §2.5 step 5) |
| 03-02 `BrainBase` + contracts + config pluggability | P0 | ☑ | Khaled | ABC with `_pick_move`/`_decide_move`; frozen `Observation`/`Decision`; brain resolved from config `[strategy]` `police_class`/`thief_class` with zero networking imports; unknown class name fails loud (STRAT-03) |
| 03-03 BFS pathfinding + distance oracle | P0 | ☑ | Khaled | BFS over the barrier-aware grid; returns optimal distance **and** next step; extracted once and consumed by both the fallback and the barrier sub-policy (QUAL-02); barrier-pocket case proven not to dead-end (STRAT-04) |
| 03-04 Bayes motion prior + fallback + `HeuristicBrain` | P0 | ☐ | Khaled | Uniform prior spread each turn by the opponent's legal moves (prediction step, no evidence — Phase 4 plugs evidence into this same update); fallback chooses by BFS distance, never raw Manhattan; `HeuristicBrain` fully playable and usable as the baseline opponent (STRAT-02) |
| 03-05 State encoding + Q-table JSON persistence | P0 | ☐ | Khaled | Canonical string key from (own cell, believed target cell, blocked bitmask, barriers used, turn bucket) — **never** the full barrier bitmap; per-key visit counts; save→load round-trip preserves values and visits exactly; corrupt/partial table fails loud rather than loading empty |
| 03-06 `QLearningBrain` — ε-greedy + fallback trigger | P0 | ☐ | Khaled | Q-update applied per step; argmax over the 5 actions when visits ≥ `min_visits`, fallback below it, boundary itself tested; no file I/O inside `_pick_move`; seeded RNG makes selection deterministic under test (STRAT-01) |
| 03-07 Cop barrier sub-policy | P0 | ☐ | Khaled | Runs after `_pick_move`, keeping the Q action space at 5; blocks the thief's best escape corridor; never exceeds the 14-barrier quota; declaration is truthful (rules 16/22); thief never places one (STRAT-05) |
| 03-08 Offline training harness + sparring pool | P0 | ☐ | Khaled | Episode loop steps the Phase-1 SDK engine; opponent sampled from {heuristic, past-self checkpoints, reference impl}; resumable — atomic checkpoint write, logged seed, interrupted run loses at most one interval (STRAT-06) |
| 03-09 Learning curves + plotting + README section | P0 | ☐ | Khaled | CSV appended from episode 1 of run 1 (episode, reward, win-rate vs baseline, ε); matplotlib script renders the README PNGs; README learning-curve section present (rule 42) |
| 03-10 §10.4 gate tests + coverage audit | P0 | ☐ | Khaled | GATE-1/2/3/4 each map to named runnable tests; STRAT-01…STRAT-07 coverage audit closes; trained table beats `HeuristicBrain` at the configured win-rate over the configured game count |
| 03-96 Build the graphify graph | P1 | ☐ | Khaled | `.planning/graphs/` built (first build — `src/` now substantial) and refreshed after execute (CLAUDE.md) |
| 03-97 Phase doc triplet at plan-phase | P1 | ☑ | Khaled | `docs/phases/phase-3/{PRD,PLAN,TODO}.md` created and filled (CLAUDE.md) |
| 03-99 Verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ☐ | Khaled | Phase gate met; all TODOs checked; root docs/TODO.md Phase 3 section all ☑ (DOC-01) |

## Phase gate (§10.4)

- [ ] Shortest path to a known target walked unaided, barrier-free **and** through a barrier pocket (GATE-1, STRAT-04)
- [ ] Q-policy serves visited states, fallback serves unvisited ones, trigger boundary tested (GATE-2, STRAT-01/02)
- [ ] Brain swapped via config `[strategy]` alone, networking untouched, no LLM reachable from the decision path (GATE-3, STRAT-03/07)
- [ ] Trained `QLearningBrain` beats `HeuristicBrain` head-to-head at the configured win-rate and game count (GATE-4, STRAT-01/06)
- [ ] Learning-curve CSV present from run 1; README PNGs rendered (rule 42, STRAT-06)
- [ ] `uv run pytest --cov=pursuit` ≥ 85% (QUAL-10)
- [ ] `uv run ruff check .` → 0 violations (QUAL-09)
- [ ] `bash scripts/check_line_limit.sh` passes all src/ and tests/ files (QUAL-08)
- [x] `docs/PRD_rl_strategy.md` committed at v1.00 (DOC-02)
- [ ] `docs/phases/phase-3/{PRD,PLAN,TODO}.md` committed and filled (CLAUDE.md)
