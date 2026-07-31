# Phase 3 PRD — Blind Strategy Module (RL policy)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-07-31

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); captures only what is
> specific to Phase 3. Game numbers come from [PARAMETERS.md](../../PARAMETERS.md); the RL
> hyperparameters are a different *category* of number and are labelled as such under
> "Numeric sourcing" below.

## Goal

Deliver the decision engine: a `BrainBase` interface behind config `[strategy]`, with a
trained tabular Q-learning policy choosing the move, a Bayes + BFS-distance fallback for
states the table has never learned, and an offline self-play training harness whose
learning curves are instrumented from the first episode. The agent plays **blind** — no
scent, no hints, no language model. Given a believed target cell it walks a shortest
barrier-aware path unaided.

## Requirements covered

| REQ-ID | Description |
|--------|-------------|
| STRAT-01 | Move selection uses a trained tabular Q-learning policy via `BrainBase._pick_move` (§B) |
| STRAT-02 | A Bayes + Manhattan heuristic fallback handles states the Q-table has never visited (§B) |
| STRAT-03 | The strategy module is pluggable — declared in config `[strategy]` as `police_class`/`thief_class`, separate from networking (§C) |
| STRAT-04 | Given a known target location, the agent computes and walks the shortest path with no manual intervention (Stage 3 gate) |
| STRAT-05 | The cop selects barrier placement via `_decide_move` (STRATEGY.md) |
| STRAT-06 | Training is offline (self-play + reference implementation); a trained Q-table ships; learning curves are instrumented from the first run (rule 42) |
| STRAT-07 | The algorithm chooses the move — the language model never does (rule 25) |
| QUAL-02 | No duplication — the BFS distance oracle is extracted once and consumed by both the fallback and the barrier sub-policy |
| QUAL-08 | Every source and test file ≤150 lines — the strategy package is split by responsibility, never compressed to fit |
| QUAL-11 | Zero hardcoded values in source — every threshold, rate and episode count in config |
| DOC-02 | `docs/PRD_rl_strategy.md` — the per-mechanism PRD for the Q-learning policy |

## Acceptance criteria (= §10.4 milestone gate)

1. **GATE-1 — Shortest path unaided:** Given a known target location, the agent computes
   and walks the shortest path with no manual intervention. Asserted on a barrier-free
   board *and* on boards where a naive Manhattan step would enter a barrier pocket — the
   walk must match BFS optimal length in both, and must terminate rather than oscillate.

2. **GATE-2 — Q-policy with fallback:** Move selection comes from the tabular Q-learning
   policy, with the Bayes + BFS-distance fallback for unvisited states. Asserted
   positively both ways: a state key with visits ≥ threshold returns the table's argmax,
   and a state key below threshold (or absent) is served by the fallback — with the
   trigger boundary itself tested, not just the two extremes.

3. **GATE-3 — Pluggable, separate, algorithm-decided:** The strategy module is swappable
   via config `[strategy]` alone, is separate from networking, and the algorithm — never
   the LLM — chooses the move. Asserted by loading each brain from config without touching
   the network layer, and by a structural test that the decision path imports nothing that
   could reach a language model (STRAT-07 is a disqualification risk, so it is tested, not
   assumed).

4. **GATE-4 — The RL actually learned something:** the shipped `QLearningBrain` beats
   `HeuristicBrain` head-to-head over the fixed eval scenario set, at the win-rate
   threshold and game count declared in config, and the learning-curve CSV + README PNGs
   exist from the first run (rule 42). A tie or a loss means the phase goal is not met —
   this criterion is what separates "a Q-table exists" from "a Q-table is worth shipping".

## Numeric sourcing

| Value | Source | Status |
|---|---|---|
| Board 7×7 | PARAMETERS.md Table 13 row 1 | minimum |
| Barrier quota 14 | PARAMETERS.md Table 15 row 2 | minimum |
| Move ceiling 35 | PARAMETERS.md Table 15 row 3 | minimum |
| Survival threshold 35 | PARAMETERS.md Table 15 row 4 | minimum |
| α (learning rate), γ (discount), ε schedule + floor | **Engineering default — NOT a PARAMETERS.md value** | config `[strategy]` |
| `min_visits` fallback threshold | **Engineering default — NOT a PARAMETERS.md value** | config `[strategy]` |
| Turn-bucket boundaries (early/mid/late) | **Engineering default — NOT a PARAMETERS.md value** | config `[strategy]` |
| Training episode count, checkpoint interval, eval game count, win-rate bar | **Engineering default — NOT a PARAMETERS.md value** | config `[training]` |

Appendix F fixes the *game*, not the *learner*. RL hyperparameters are ours to choose and
are labelled as engineering defaults wherever they appear — the same honesty convention
Phase 2 used for ports and watchdog cadence (D-16, D-18). Inventing a value in the first
table is a disqualification; choosing one in the second is engineering.

## In scope / Out of scope (this phase)

- **In:** `BrainBase` interface + `Observation`/`Decision` contracts; state encoding with
  canonical string keys; JSON Q-table with per-key visit counts; `QLearningBrain` with
  ε-greedy selection and the visit-count fallback trigger; `HeuristicBrain` as a fully
  playable baseline; Bayes motion-model prior; BFS distance oracle and walk on the
  barrier-aware grid; cop barrier sub-policy; offline training harness with sparring pool
  and resumable checkpoints; learning-curve CSV + plotting script;
  `docs/PRD_rl_strategy.md`; the §10.4 gate tests.

- **Out:** Scent, hints, pheromones, belief evidence and any LLM use (Phase 4 — the
  *input contract* is fixed now as "a believed target cell" so Phase 4 plugs in without a
  retrain); networking changes (Phase 2, done); cloud tunneling (Phase 5); commit-reveal
  cryptography (Phase 6); Gmail reporting, live GUI and replay viewer (Phase 7 — this
  phase only *emits* what Phase 7 will later visualize); submission and league operations
  (Phase 8).

## Dependencies

- Depends on: Phase 1 (`pursuit.sdk.engine` — the only route to game logic, and the
  environment the training harness steps) and Phase 2 (`config/{police,thief}/` layout and
  the loader helpers the `[strategy]` section is read through)
- External: `matplotlib` as a **dev/training-only** dependency via `uv add --dev`, imported
  solely by the plotting script. No new runtime dependency — the decision path stays pure
  standard library, so the shipped agent's runtime dep list remains `fastmcp` alone.

## Success metrics & test scenarios

- GATE-1…GATE-4 each map to named runnable tests (see [PLAN.md](PLAN.md) test plan)
- `uv run pytest --cov=pursuit` — suite green with ≥85% coverage (QUAL-10)
- `uv run ruff check .` — 0 violations (QUAL-09)
- `bash scripts/check_line_limit.sh` — all source and test files ≤150 lines (QUAL-08)
- `docs/PRD_rl_strategy.md` committed at v1.00 **before** the policy code it describes
  (DOC-02, SEGAL §2.5 step 5)
- Learning-curve CSV present from the first training run, README PNGs rendered (rule 42)
