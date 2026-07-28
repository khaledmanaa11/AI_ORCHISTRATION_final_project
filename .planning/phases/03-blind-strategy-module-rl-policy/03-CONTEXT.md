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

*Phase: 03-blind-strategy-module-rl-policy*
*Context gathered: 2026-07-28*
