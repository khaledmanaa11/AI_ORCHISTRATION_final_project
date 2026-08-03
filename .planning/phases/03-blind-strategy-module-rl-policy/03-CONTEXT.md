# Phase 3: Blind Strategy Module (RL policy) - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers the decision engine: a `BrainBase` interface with a **trained tabular
Q-learning policy** (`_pick_move`), a **Bayes + Manhattan fallback** for unvisited states,
ε-greedy exploration, an **offline self-play training harness**, and learning-curve
instrumentation from the first run — all pluggable via config `[strategy]`
(`police_class`/`thief_class`), playing **blind** (STRAT-01…STRAT-07).

Out of scope: scent/hints/belief evidence (Phase 4), LLM anything (Phase 4 — the
algorithm, never the LLM, chooses the move), networking changes (Phase 2), crypto
(Phase 6).

**Planning-day note:** run `/gsd:ai-integration-phase 3` (optional but useful — its
eval-planner formalizes the RL evaluation rubric) *before* `/gsd:plan-phase 3 --chunked`.
Also run `/gsd:graphify` first — Phase 3 is the first graph build (task 03-96).

</domain>

<decisions>
## Implementation Decisions

### State encoding (Q-table key)
- **Barriers as local features**: agent-relative blocked-directions bitmask + barriers-used
  count — never the full 7×7 barrier bitmap (state-space explosion).
- **Absolute (own cell, target cell)** pair as the positional core (49×49) — edge and
  corner effects are learned, which is the essence of cornering play.
- **Turn as bucketed phase** (early/mid/late, thresholds in config) — the thief can learn
  end-game stalling toward the 35-turn survival threshold without a 35× table blow-up.
- **Q-table ships as JSON** — human-readable, diffable, grader-openable; no pickle.

### Policy structure
- **Separate Q-tables per role** (cop table, thief table) — independent training, clean
  Phase-8 repo split, no shared-state smell.
- **Two-stage cop decision (STRAT-05)**: `_decide_move` picks movement from the Q-policy,
  then a barrier sub-policy (heuristic in Phase 3 — e.g., block the thief's best escape
  corridor) decides whether/where to place a barrier. Q action space stays at 5.
- **Fallback trigger (STRAT-02)**: state key absent OR visit count below a config
  threshold → Bayes + Manhattan fallback (low-data Q-values are noise).
- **Two selectable brains (STRAT-03)**: `BrainBase` → `QLearningBrain` and
  `HeuristicBrain`, both fully playable, chosen via config `[strategy]`.
  `QLearningBrain` internally falls back to the heuristic. The standalone
  `HeuristicBrain` doubles as the learning-curve baseline.

### Blind-phase observability
- **Input contract is "a believed target cell"** — Phase 3 feeds the known target
  (Stage-3 gate); Phase 4 feeds the belief map's best cell. **No retraining needed when
  belief arrives.**
- **Motion-model prior when target unknown**: uniform prior spread each turn by the
  opponent's legal moves (Bayes prediction step, no evidence). Phase 4 plugs scent/hint
  evidence into this same update.
- **BFS on the barrier-aware grid** computes the shortest-path walk (STRAT-04 gate) and
  serves as the distance oracle for the "Manhattan" fallback so it never dead-ends
  behind barriers.

### Training regime
- **Sparring pool (STRAT-06)**: heuristic brain + past-self checkpoints + the reference
  implementation (`rmisegal/Game-P2P-Cop-Chase`) — bounds non-stationarity, avoids
  self-play collapse.
- **Success bar**: `QLearningBrain` must beat `HeuristicBrain` head-to-head over an eval
  set (win-rate threshold + game count from config) — answers STRATEGY.md open question 3.
- **Big overnight runs** (user's explicit choice over fast iterations): hundreds of
  thousands of episodes for convergence polish. Episode counts in config. Schedule note:
  kick off training before sleep/exam-prep blocks so wall-clock time is free.
- **Learning curves**: every run appends CSV (episode, reward, win-rate vs baseline, ε);
  a small matplotlib script renders the README PNGs (rule 42 — mandatory README section).

### Claude's Discretion
- ε schedule shape, α, γ — standard values, stored in config, tuned only if curves look
  sick. (Internal hyperparameters, not game parameters — no invented-value risk.)
- Module/file layout within the 150-line limit; test structure.
- Barrier sub-policy heuristic details.

</decisions>

<specifics>
## Specific Ideas

- All numeric knobs (thresholds, episode counts, ε/α/γ, visit-count threshold, turn
  buckets) live in config — zero hardcoded values in `src/` (QUAL gate + D-05).
- Reference implementation for sparring: `https://github.com/rmisegal/Game-P2P-Cop-Chase`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

<superseded>
## Superseded by measurement — 2026-08-02 (run-2 context)

Everything above is the **run-1** context, gathered 2026-07-28 before any training had happened.
Run 1 executed on 2026-08-02 (300,000 episodes, seed 1337) and **GATE-4 failed for both roles**
(cop 0.250 vs the 0.55 floor; thief 0.800 vs a 0.900 heuristic baseline). The post-mortem
[`docs/phases/phase-3/RUN-1-POSTMORTEM.md`](../../../docs/phases/phase-3/RUN-1-POSTMORTEM.md)
and the three-track literature review in `docs/research/` measured *why*.

**Nothing above is deleted — it is the historical record of why 03-00…03-10 look the way they
do.** The entries below override it for all planning from 03-11 onward. Where they conflict,
**these win.** Each carries the measurement or citation that overturned the original decision.

### Decisions overturned by measurement

| Was | Now | Evidence |
|---|---|---|
| **D-04** absolute `(own cell, target cell)` positional core — "edge and corner effects are learned" | **Falsified as a generalisation mechanism.** A tabular key over absolute coordinates shares nothing between positions. Trained from one start, the table covers one reachable cone. | Post-mortem Finding 1: cop scored **0.600 on trained start states vs 0.133 on unseen**; only **5/20** eval starts cleared `min_visits`; top 1% of keys hold **53.2%** of 3,525,039 visits; median best-vs-second Q margin across the whole cop table **0.00000** |
| **D-06** turn as a **bucketed phase** (early/mid/late) | **Replaced entirely by exact `turns_remaining`** — not placed alongside it. | Two independent citations: Puterman 1994 ch.4 (finite-horizon optimal policies are non-stationary in exact time-to-go); Pardo et al., *Time Limits in RL*, ICML 2018 (a deadline task is non-Markov unless `turns_remaining` is in the state). Row 03-16 |
| **D-09** BFS distance on the barrier-aware grid as the decision objective | **Distance is the wrong quantity for both roles.** Barriers keep the board triangle-free, so **cop-win ⟺ the thief's free component is a forest**: the cop destroys cycles, the thief preserves one. BFS distance stays only as a *tie-break and fallback* utility, never as the objective. | `docs/research/PURSUIT-AND-EVASION-STRATEGY.md`. The cop number of an m×n grid is **2** (Neufeld & Nowakowski, *Discrete Math* 186:253-268, 1998) — one cop chasing by distance can never catch a perfect evader; barriers are its only substitute for the missing second cop |
| **D-12** two-stage cop decision with a heuristic barrier sub-policy maximising BFS distance to a fixed corner anchor | **The corner-anchor rule has no support anywhere in the literature.** Replaced by edge/existing-barrier-adjacent placement preferring degree-4 cells inside the thief's component. Decycle **the thief's component, never the board** (decycling number of the 7×7 grid is 13 vs quota 14, but 13 placements + ~32 chase rounds = 45 > the 35-turn limit). | Guibas et al. 1999 — barriers in open space create islands the thief orbits. Row 03-14. Post-mortem Finding 4.3: barrier *layout* is invisible to the policy, so the cop's ceiling is bounded by this heuristic and no amount of training moves it |
| **D-13** sparring mix `[0.30 heuristic, 0.50 past-self, 0.20 reference]` | **Never ran as configured.** `reference_impl_path` is empty, so `_available_weights` renormalised to **0.375 / 0.625** — the thief spent 62.5% of training against past-self cops while those cops climbed to 0.90. Replaced by PFSP opponent sampling `f(x)=x(1−x)` with a weak-opponent floor in every pool. | Post-mortem Finding 4.2. Failure mode has a name: **coevolutionary disengagement**, Cartlidge & Bullock, *Evolutionary Computation* 12(2):193-222, 2004 (verified independently); remedy "reduce virulence" raises quality on **both** sides |
| **D-18** single γ for both roles | **γ must differ by role: γ_cop = 0.99, γ_thief = 1.0.** Discounting is the cop's capture-sooner incentive and actively harms the thief. Run-1's γ=0.95 gave an effective horizon of 20 against a 35-turn task. | Post-mortem Finding 2b: thief usable value range **0.047** vs the cop's 0.626 — a **13×** weaker learning signal, below the noise floor at α=0.15. `docs/research/TRAINING-METHODOLOGY.md` |

### Correctness defects found — these are code bugs, not tuning

| ID | Defect | Proof |
|---|---|---|
| **R1** | Every one of the 300,000 episodes started from the identical board (`engine.make_state`). Start states must be **randomised**, with the restart distribution μ ⊇ the eval distribution d (Kakade & Langford; reverse curriculum for the thief, Florensa et al. CoRL 2017). | Cop's key `0,0\|3,3\|9\|0\|0` has exactly **150,000 visits** — one per cop episode |
| **R2** | **The thief is never told it was caught.** `harness.py::_turn` only calls `_update_learner` when the moving role IS the learner, and capture is produced on the *cop's* turn. Terminal transitions must be delivered to the learner **whichever role's move caused them**, and the thief needs a real capture penalty. **⚠ The defect is SYMMETRIC — the post-mortem documented only half of it.** Verified in `src/pursuit/sdk/engine.py` while planning 03-14: `apply_cop_action` emits CAPTURE on the cop's turn *and* `apply_thief_move` emits SURVIVAL on the thief's turn, so a **cop** learner is blind to survival exactly as the thief is blind to capture. Both halves must be fixed and both must be tested. | Instrumented: 300/300 captured episodes delivered **exactly one update worth −0.01** (the ordinary step cost). Symmetry found 2026-08-03 by direct reading of `engine.py` |
| **R4** | **No terminal-state marking anywhere.** `update` always bootstraps `reward + γ·max Q(next_key)`, so terminal keys collide with live keys sharing the same positions/mask/count/bucket and terminal values leak into live states. | Post-mortem Finding 4.1 |
| **R5** | ε and α reach their floors at episode **299,999 of 300,000** — 100% of the way through. No consolidation phase exists. Floors belong at ~60%, and ε's floor at 10–15%, not 0. | `epsilon_decay_episodes = 150000` × 150,000 episodes per role. Produced the recorded `final_slope = +0.094` |
| **R6** | Eval **pseudo-replicates** — both brains are deterministic at `epsilon_eval=0.0`, so 10 repeats replay identically and the true sample size is **n=20, not 200**. | ✅ **Already landed** (commit `ced26d5`). Honest recomputation: cop p=0.250, thief p=0.500 — neither significant |

### New decisions for run 2 — user-confirmed 2026-08-02

- **D-26 — Alpha-beta search replaces the Q-policy as the mover.** `_pick_move` becomes an
  alpha-beta search over a cycle-based evaluation; the Q-table is demoted from a 1.7M-entry
  action table to storage for ~60 evaluation weights that RL tunes. Alpha-beta, **not MCTS**
  (Ramanujan et al. ICAPS 2010 — MCTS misses shallow traps, and barrier sealing *is* one);
  a trap closing in k thief moves needs depth ≥ 2k plies. `strategy.max_decision_ms` is ours
  to raise — test 100/200 ms early. **Measured on our real engine: depth 5 with a useful eval,
  depth 8 with Manhattan** — the algorithm researcher's 11–12-ply claim did **not** reproduce
  and its correction pass was cut off by an API limit, so treat that report's depth figures and
  its Bansal delta-uniform numbers as UNVERIFIED.
- **D-27 — STRAT-01 and STRAT-06 now require a written defence, and that defence is a
  deliverable.** STRAT-01 says "move selection uses a trained tabular Q-learning policy via
  `BrainBase._pick_move`" and STRAT-06 says "a trained Q-table ships". Under D-26 both are
  satisfied in substance but not in the literal shape the requirement text describes. A
  grader-facing document must state the deviation plainly, carry the measured evidence for it,
  and show what still ships (a trained table of tuned weights, learning curves from run 1 of
  the new regime). **This is not optional and not a footnote** — it is the single largest
  grading risk this phase carries.
- **D-28 — The GATE-4 bar stays at `min_win_rate_absolute = 0.55`.** It is not lowered for
  run 2. It originates in `docs/PRD_rl_strategy.md` §8 (D-14), **not** in `docs/PARAMETERS.md`
  (checked: 142 lines, zero matches), so it is ours to re-argue — but only *after* a second
  measurement, never because a run failed. If run 2 also misses it, the miss becomes evidence
  about the bar rather than about the run.
- **D-29 — Everything lands before run 2; there is exactly one run.** 03-11…03-16 all land,
  03-12's six pre-flight assertions gate the launch, then a single overnight run. Run 1 cost a
  whole night to four defects that were all computable at t=0.
- **D-30 — 03-12's pre-flight assertions are a hard gate on every future run.** Six checks
  computable before episode 1 (`TRAINING-METHODOLOGY.md` §F): terminal reward present for each
  role; discounted terminal-value spread per role; ε/α floor ≤ 15% of episodes; ≥200 distinct
  start states covering every eval start; weak-opponent floor in each sparring pool.
  **Run 1 failed four of these at t=0.**
- **D-31 — The thief's safety rule is a measured free win and lands regardless of search.**
  A thief that only moves to cells outside the cop's closed neighbourhood N[cop] scored
  **296/300 = 0.987** over random starts vs the current BFS thief's 283/300 = 0.943, no
  training required. **Caveat recorded, not smoothed over:** the "provably unbeatable" claim
  did **not** fully reproduce — it still lost 3/20 with new barrier placement disabled, and
  that control was itself flawed because the scenarios carry pre-placed barriers. Treat as a
  real bounded gain, not a solved thief.

### Still binding from the run-1 context

D-01 (no RL framework — stdlib only), D-02 (JSON not pickle), D-03 (separate table per role, no
shared live state — project rule 2), D-07 (two selectable brains behind `BrainBase`, config
`[strategy]`), D-08 (fallback trigger), D-10/D-11 (Bayes prior; input contract is "a believed
target cell" so Phase 4 needs no retrain), D-17 (train against the SDK engine, never the network
layer), D-19 (seeded `random`; `secrets` reserved for Phase 6), D-20 (matplotlib is dev-only),
D-21 (reference impl never vendored), D-22 (artifacts outside OneDrive), D-23 (held-out eval
seeds), D-24 (whole-run checkpoints, Windows-safe writes), D-25 (α decays with ε; per-role curves).

### Explicitly NOT in scope

The ablation pilot (4 arms × 10,000 episodes) **ran and is INCONCLUSIVE** — every pairwise
comparison insignificant (Fisher exact: cop A-vs-C p=0.407, thief A-vs-D p=0.451). It must not
be cited as support for anything. A decisive ablation needs n in the hundreds or a stochastic
eval, plus a budget near run-1's. **The case for R1–R6 rests on Findings 1–4, which are direct
measurements and do not depend on that pilot.**

</superseded>

---

*Phase: 03-blind-strategy-module-rl-policy*
*Context gathered: 2026-07-28 · Superseded section added 2026-08-02 after run-1 post-mortem*
