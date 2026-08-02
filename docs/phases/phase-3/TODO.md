# Phase 3 TODO — Blind Strategy Module (RL policy)

**Owner:** Khaled (solo) · **Updated:** 2026-08-01

> Phase task list. Mirrors the `.planning/` plans for Phase 3. `/gsd:verify-work 3` marks
> every row `[x]` and ticks the matching rows in the root [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 03-00 Phase-3 scaffold + config sections + test stubs | P0 | ☑ | Khaled | `uv add --dev matplotlib`; `[strategy]` + `[training]` sections in `config/{police,thief}/`; `StrategyKey`/`TrainingKey` enums; hyperparameters loaded through the existing `loader_helpers` (QUAL-02/11/13); test stubs collect and exit 0 |
| 03-01 `docs/PRD_rl_strategy.md` | P0 | ☑ | Khaled | v1.00; state encoding, reward function, update rule, fallback trigger and sparring pool all specified; every number carries a Source column marking it PARAMETERS.md vs engineering default. Written **before** the policy code it describes (DOC-02, SEGAL §2.5 step 5) |
| 03-02 `BrainBase` + contracts + config pluggability | P0 | ☑ | Khaled | ABC with `_pick_move`/`_decide_move`; frozen `Observation`/`Decision`; brain resolved from config `[strategy]` `police_class`/`thief_class` with zero networking imports; unknown class name fails loud (STRAT-03) |
| 03-03 BFS pathfinding + distance oracle | P0 | ☑ | Khaled | BFS over the barrier-aware grid; returns optimal distance **and** next step; extracted once and consumed by both the fallback and the barrier sub-policy (QUAL-02); barrier-pocket case proven not to dead-end (STRAT-04) |
| 03-04 Bayes motion prior + fallback + `HeuristicBrain` | P0 | ☑ | Khaled | Uniform prior spread each turn by the opponent's legal moves (prediction step, no evidence — Phase 4 plugs evidence into this same update); fallback chooses by BFS distance, never raw Manhattan; `HeuristicBrain` fully playable and usable as the baseline opponent (STRAT-02) |
| 03-05 State encoding + Q-table JSON persistence | P0 | ☑ | Khaled | Canonical string key from (own cell, believed target cell, blocked bitmask, barriers used, turn bucket) — **never** the full barrier bitmap; per-key visit counts; save→load round-trip preserves values and visits exactly; corrupt/partial table fails loud rather than loading empty |
| 03-06 `QLearningBrain` — ε-greedy + fallback trigger | P0 | ☑ | Khaled | Q-update applied per step; argmax over the 5 actions when visits ≥ `min_visits`, fallback below it, boundary itself tested; no file I/O inside `_pick_move`; seeded RNG makes selection deterministic under test (STRAT-01) |
| 03-07 Cop barrier sub-policy | P0 | ☑ | Khaled | Runs after `_pick_move`, keeping the Q action space at 5; blocks the thief's best escape corridor; never exceeds the 14-barrier quota; declaration is truthful (rules 16/22); thief never places one (STRAT-05) |
| 03-08 Offline training harness + sparring pool | P0 | ☑ | Khaled | Episode loop steps the Phase-1 SDK engine; opponent sampled from {heuristic, past-self checkpoints, reference impl}; resumable — atomic checkpoint write, logged seed, interrupted run loses at most one interval (STRAT-06) |
| 03-09 Learning curves + plotting + README section | P0 | ☑ | Khaled | CSV appended from episode 1 of run 1 (episode, reward, win-rate vs baseline, ε); matplotlib script renders the README PNGs; README learning-curve section present (rule 42) |
| 03-10 §10.4 gate tests + coverage audit | P0 | ◐ | Khaled | GATE-1/2/3/4 each map to named runnable tests; STRAT-01…STRAT-07 coverage audit closes; trained table beats `HeuristicBrain` at the configured win-rate over the configured game count. **Tasks 1–4 all executed.** Tasks 1–3 landed the GATE-1/2/3 tests, `training/evaluate.py` + `artifacts/eval_scenarios.json`, and this coverage audit. **Task 4 ran on 2026-08-02** (300,000 episodes, seed 1337, completed uninterrupted) and **GATE-4 FAILED for both roles** — see the measured-result block below. Per the plan, the bar was not lowered and no table was promoted; the row stays ◐ until a retrained table clears the gate |
| 03-10 op-1: redirect training output to a file (Windows QuickEdit) | P0 | ☑ | Khaled | `uv run python -m training.loop 2>&1 \| tee run.log` before the overnight run — console QuickEdit silently suspends the process the moment the window is clicked, the single most common "the run just stopped" cause (03-RESEARCH.md §3). Note: the entry point is `training.loop` (`main()`/`_load_run_config()`), not `training.harness` — `harness.py` only has the per-episode loop, no `__main__`; this was a real gap found and fixed post-03-08 (see STATE.md). **Evidence:** the run reached the full configured 300,000 episodes with no resume gap (`run_state.json` `episode=300000`, 600 curve rows = every 500-episode interval accounted for) |
| 03-10 op-2: disable sleep for the training machine | P0 | ☑ | Khaled | `powercfg /change standby-timeout-ac 0` before starting the overnight run — `training/loop_setup.py`'s `SetThreadExecutionState` guard covers sleep only while the process itself is running, not the machine-level power policy (03-RESEARCH.md §3). **Evidence:** overnight run completed without interruption |
| 03-10 op-3: exclude the artifacts directory from Defender real-time scanning | P0 | ☑ | Khaled | Add `training.artifacts_dir` (LOCALAPPDATA-based, outside OneDrive by default, D-22) to Windows Defender exclusions before starting — real-time scanning on every checkpoint rewrite adds latency (03-RESEARCH.md §3). **Evidence:** artifacts resolved to `%LOCALAPPDATA%\pursuit\training\` (outside OneDrive as designed); all checkpoint writes completed |
| 03-10 T4-followup-1: retrain the cop to convergence (config-only) | P0 | ☐ | Khaled | The cop was **still climbing** when ε hit its floor (`final_slope=+0.094`, decile_gain `+0.848`). Raise `training.episodes` and `epsilon_decay_episodes` together so the schedule ends at a flat curve, then re-measure. No code change — `config/{police,thief}/strategy.json` only |
| 03-10 T4-followup-2: diagnose and fix the thief's regression (config-first) | P0 | ☐ | Khaled | Thief `decile_gain=−0.068` — the final decile is worse than the first, and it lost to the heuristic it replaces (0.800 vs 0.900). Leading hypothesis, from the run's own data: `fallback_rate` collapsed 0.76 → 0.009, so the thief abandoned the BFS fallback for Q-values that never became better than it, while `sparring_mix` past-self 0.50 fed it an ever-stronger cop and an almost all-loss training signal. Config levers first: raise `min_visits` (currently 20) to keep the fallback in play longer, and rebalance `sparring_mix` toward `heuristic`. Confirm the hypothesis before tuning |
| 03-10 T4-followup-3: fix the eval CLI's pseudo-replication | P1 | ☐ | Khaled | `repeats_per_scenario=10` replays each scenario **identically** (both brains deterministic at `epsilon_eval=0.0`; verified — 0 of 20 scenarios varied across repeats). `eval_games=200` therefore has effective **n=20**, and `training/evaluate.py`'s reported `mcnemar_p≈0.0000` / `z=3.95` are inflated by pseudo-replication. Either vary the replays or report n=20. **This makes the gate stricter, not weaker** — it is a correctness fix, not a bar change (honest n=20: cop *p*=0.250, thief *p*=0.500, neither significant) |
| 03-96 Build the graphify graph | P1 | ☑ | Khaled | `.planning/graphs/` built (first build, 03-09) and refreshed after this plan's Tasks 1–2 landed real code (3190 nodes / 5849 edges / 201 communities, CLAUDE.md) |
| 03-97 Phase doc triplet at plan-phase | P1 | ☑ | Khaled | `docs/phases/phase-3/{PRD,PLAN,TODO}.md` created and filled (CLAUDE.md) |
| 03-99 Verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ☐ | Khaled | Phase gate met; all TODOs checked; root docs/TODO.md Phase 3 section all ☑ (DOC-01) |

## STRAT-01…STRAT-07 coverage audit (03-10 Task 3)

Every requirement below maps to at least one named, currently-passing test. Where a clause of
the requirement is not yet demonstrated (GATE-4's "a trained Q-table ships"), that gap is
recorded explicitly rather than the row being marked done.

| REQ-ID | Named test(s) | Status |
|--------|---------------|--------|
| STRAT-01 (Q-policy via `_pick_move`) | `tests/unit/strategy/test_qlearning.py`, `test_qlearning_learning.py`; `tests/integration/test_policy_fallback.py` (GATE-2) | ☑ met |
| STRAT-02 (Bayes+BFS fallback for unvisited states) | `tests/unit/strategy/test_fallback.py`, `test_prior.py`; `tests/integration/test_policy_fallback.py` (E4), `test_shortest_path.py` | ☑ met |
| STRAT-03 (pluggable via config `[strategy]`) | `tests/unit/strategy/test_registry.py`, `test_heuristic.py`, `test_qlearning.py`; `tests/integration/test_strategy_pluggable.py` (GATE-3) | ☑ met |
| STRAT-04 (known-target shortest path, unaided) | `tests/unit/strategy/test_pathfind.py`; `tests/integration/test_shortest_path.py` (GATE-1) | ☑ met |
| STRAT-05 (cop barrier placement via `_decide_move`) | `tests/unit/strategy/test_barriers.py`, `test_barriers_integration.py` | ☑ met |
| STRAT-06 (offline training; **a trained Q-table ships**; curves from run 1) | Harness/curves: `tests/unit/training/test_harness.py`, `test_loop.py`, `test_curves.py`, `test_checkpoint.py`, `test_sparring.py`, `test_plot_curves.py`. Eval machinery: `test_eval_scenarios.py`, `test_eval_arms.py`, `test_eval_stats.py`, `test_evaluate.py`. GATE-4 itself: `tests/integration/test_beats_baseline.py` | ◐ **open gap, now measured rather than untested**: the harness ran a full 300,000-episode training run (2026-08-02) and the curves from run 1 ship, so "offline training" and "curves from run 1" are met. The **"a trained Q-table ships"** clause is *not* met: the resulting tables failed GATE-4 for both roles and were therefore **not promoted** into `artifacts/`, so `test_beats_baseline_smoke_subset` still skips for want of a *blessed* table. Closed by the T4-followup rows above, not by another gate test |
| STRAT-07 (algorithm decides, never the LLM) | `tests/unit/strategy/test_registry.py` (structural import scan, 03-02); `tests/integration/test_strategy_pluggable.py`; `scripts/check_no_llm_in_strategy.sh` (standalone CI gate, verified to exit nonzero when a forbidden import is introduced) | ☑ met |

### QUAL-08/09/10/11/13 + DOC-02 gate commands

| REQ-ID | Gate command | Status |
|--------|--------------|--------|
| QUAL-08 (≤150 code lines/file) | `bash scripts/check_line_limit.sh` | ☑ clean |
| QUAL-09 (ruff 0 violations) | `uv run ruff check .` | ☑ clean |
| QUAL-10 (`pytest --cov` ≥ 85%) | `uv run pytest --cov=pursuit --cov=training` | ☑ met (96.45%, 425 passed / 2 skipped) |
| QUAL-11 (zero hardcoded values in `src/`) | No single command — enforced by the config/`constants.py`/`Enum` design plus targeted `ast`-walk tests, e.g. `test_barriers.py`'s quota scan and `test_registry.py`'s eval/exec scan | ☑ enforced |
| QUAL-13 (`uv` only) | `uv sync` / `uv run ...` (`pyproject.toml` + `uv.lock`, no `requirements.txt`) | ☑ met |
| DOC-02 (per-mechanism PRD) | `docs/PRD_rl_strategy.md` committed at v1.00 (03-01), before the policy code it describes | ☑ met |

## Phase gate (§10.4)

- [x] Shortest path to a known target walked unaided, barrier-free **and** through a barrier pocket (GATE-1, STRAT-04)
- [x] Q-policy serves visited states, fallback serves unvisited ones, trigger boundary tested (GATE-2, STRAT-01/02)
- [x] Brain swapped via config `[strategy]` alone, networking untouched, no LLM reachable from the decision path (GATE-3, STRAT-03/07)
- [ ] Trained `QLearningBrain` beats `HeuristicBrain` head-to-head at the configured win-rate and game count (GATE-4, STRAT-01/06) — **measured 2026-08-02 and FAILED for both roles** (cop 0.250 vs 0.100 baseline: clears the margin, misses the 0.55 floor; thief 0.800 vs 0.900 baseline: below the baseline). No longer "blocked on Task 4" — Task 4 ran; this is a real negative result awaiting the config-only retrain in T4-followup-1/2
- [x] Learning-curve CSV present from run 1; README PNGs rendered (rule 42, STRAT-06) — `artifacts/curves/curves.csv` (600 rows, from episode 1 of run 1) plus `winrate_cop.png`, `winrate_thief.png`, `mean_reward.png`, all three embedded in the README's rule-42 section with measured numbers

### GATE-4 measured result — run 1, 300,000 episodes (2026-08-02)

Run: 300,000 episodes (150,000 cop / 150,000 thief), `seed=1337`, config hash `5fa4d554…`,
completed uninterrupted. Tables written to `%LOCALAPPDATA%\pursuit\training\`
(`qtable_police.json` 39,483 keys / 3,525,039 visits; `qtable_thief.json` 29,703 keys /
1,355,252 visits) and **deliberately not promoted** into `artifacts/`.

| Role | Learner win rate | Measured baseline | Margin | Margin ok (≥0.10) | Floor ok (≥0.55) | E6 convergence | GATE-4 |
|---|---|---|---|---|---|---|---|
| Cop | 0.250 | 0.100 | +0.150 | ☑ | ☐ | not converged — `decile_gain=+0.848`, `final_slope=+0.094` (still climbing at the ε floor) | **FAIL** |
| Thief | 0.800 | 0.900 | −0.100 | ☐ | ☑ | not converged — `decile_gain=−0.068` (final decile worse than first) | **FAIL** |

Honest significance at the true effective sample size (n=20 paired scenarios, not 200
replays — see T4-followup-3): cop McNemar exact *p*=0.250, thief *p*=0.500. **Neither role
is significant at α=0.05.** The bar was not lowered and no unmeasured number was written
anywhere; per 03-10-PLAN Task 4, tuning is the follow-up.
- [x] `uv run pytest --cov=pursuit --cov=training` ≥ 85% (QUAL-10)
- [x] `uv run ruff check .` → 0 violations (QUAL-09)
- [x] `bash scripts/check_line_limit.sh` passes all src/ and tests/ files (QUAL-08)
- [x] `docs/PRD_rl_strategy.md` committed at v1.00 (DOC-02)
- [x] `docs/phases/phase-3/{PRD,PLAN,TODO}.md` committed and filled (CLAUDE.md)
