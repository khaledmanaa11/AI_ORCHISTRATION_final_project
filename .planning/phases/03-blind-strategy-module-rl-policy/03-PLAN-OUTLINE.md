# Phase 3 Plan Outline — Blind Strategy Module (RL policy)

**Phase:** 03-blind-strategy-module-rl-policy
**Goal:** The Q-Learning decision engine, with no scent and no natural language yet.
**Requirements:** STRAT-01 … STRAT-07 (+ QUAL-02/08/09/10/11/13, DOC-02)

## OUTLINE COMPLETE

## Decision IDs

Authoritative for this phase. Derived from `03-CONTEXT.md` (locked user decisions) and
`03-AI-SPEC.md` (framework + evaluation contract). Plans cite these; do not re-derive them.

| ID | Decision | Source |
|----|----------|--------|
| D-01 | No RL framework — tabular Q-learning on a stdlib `dict`; no NumPy, no torch, no Gymnasium | AI-SPEC §2 |
| D-02 | Q-table persists as **JSON**, never pickle — human-readable, diffable, grader-openable | CONTEXT |
| D-03 | **Separate Q-table per role**, loaded per process; no shared live state between cop and thief (project rule 2) | CONTEXT |
| D-04 | Positional core of the state key is the **absolute (own cell, target cell) pair** (49×49) — edge/corner effects are learned | CONTEXT |
| D-05 | Barriers enter the key as an **agent-relative blocked-direction bitmask + barriers-used count** — never the full 7×7 bitmap | CONTEXT |
| D-06 | Turn enters as a **bucketed phase** (early/mid/late), thresholds in config | CONTEXT |
| D-07 | **Two selectable brains** behind `BrainBase`: `QLearningBrain` and `HeuristicBrain`, both fully playable, chosen via config `[strategy]` | CONTEXT, STRAT-03 |
| D-08 | **Fallback trigger**: state key absent **OR** visit count below a config threshold — low-data Q-values are noise | CONTEXT, STRAT-02 |
| D-09 | The fallback's distance metric is **BFS on the barrier-aware grid**, not raw Manhattan, so it never dead-ends in a barrier pocket | CONTEXT, STRAT-04 |
| D-10 | **Bayes motion-model prior**: uniform prior spread each turn by the opponent's legal moves (prediction step, no evidence) | CONTEXT |
| D-11 | Input contract is **"a believed target cell"** — Phase 3 feeds the known target, Phase 4 feeds the belief argmax. **No retraining when belief arrives** | CONTEXT |
| D-12 | **Two-stage cop decision**: Q-policy picks movement, then a heuristic barrier sub-policy decides whether/where to place. Q action space stays at **5** | CONTEXT, STRAT-05 |
| D-13 | **Sparring pool**: heuristic brain + past-self checkpoints + the reference implementation — bounds non-stationarity, avoids self-play collapse | CONTEXT, STRAT-06 |
| D-14 | **Success bar**: `QLearningBrain` must beat `HeuristicBrain` head-to-head over the eval set (win-rate threshold + game count from config) | CONTEXT |
| D-15 | **Big overnight training runs**; episode counts in config; runs are resumable and seed-logged | CONTEXT |
| D-16 | **Learning curves from run 1**: CSV per episode (episode, reward, win-rate vs baseline, ε) + matplotlib README PNGs (rule 42) | CONTEXT, STRAT-06 |
| D-17 | Training steps `pursuit.sdk.engine` **directly**, never the FastMCP network layer — episodes must run in-process at full speed | AI-SPEC §4, engineering decision |
| D-18 | ε/α/γ, `min_visits`, turn-bucket boundaries, episode counts and the eval bar are **engineering defaults in config — NOT PARAMETERS.md values**, and are labelled as such wherever they appear | CONTEXT, PRD §Numeric sourcing |
| D-19 | Seeded `random` for ε-greedy exploration; `secrets` stays reserved for Phase 6 nonces — reproducibility and crypto are different requirements | AI-SPEC §3 |
| D-20 | `matplotlib` is a **dev/training-only** dependency; nothing on the decision path imports it, so the shipped agent's runtime dep list stays `fastmcp` alone | AI-SPEC §2 |
| D-21 | The reference implementation is **never vendored and never a submodule** — its LICENSE is an Educational Use EULA whose §4c forbids redistribution, and Phase 8 ships two *public* repos. It is an **opt-in local clone** behind config `reference_impl_path` (empty default), reached by an import-guarded adapter that drops the opponent and **renormalizes pool weights** when absent | RESEARCH §1 |
| D-22 | Training artifacts default to a path **outside OneDrive** (`%LOCALAPPDATA%`-derived, config-overridable, never hardcoded in `src/`). Only the final blessed Q-tables, curve CSV and PNGs are copied into the repo at run end | RESEARCH §3 |
| D-23 | The eval scenario set uses **held-out start-position seeds disjoint from training**. `HeuristicBrain` is both a sparring partner and the eval opponent, so without disjoint seeds "beats the baseline" is training on the test set | RESEARCH §2 |
| D-24 | Checkpoints persist the **whole run** (episode, ε, α, RNG state via `getstate`, seed, config hash, CSV row count) — not just the Q-table. Writes rotate a `.prev` generation and validate-with-fallback on load, because `os.replace` is **not guaranteed atomic on Windows** | RESEARCH §3 |
| D-25 | **α decays alongside ε**, and the two roles are tracked with **separate curves and win-rates** — a fixed learning rate oscillates under a non-stationary opponent, and one shared threshold marks one role done while the other is still random | RESEARCH §2 |

## Conflict resolutions

Where `03-AI-SPEC.md` and `03-RESEARCH.md` disagree, these rulings are authoritative and the
plans implement them:

| Topic | AI-SPEC said | RESEARCH said | Ruling |
|---|---|---|---|
| Sparring mix | heuristic 0.5 / past-self 0.35 / reference 0.15 | heuristic 0.30 / past-self 0.50 / reference 0.20 | **RESEARCH.** Weighting the heuristic above ~1/3 trains against the eval opponent. Config key name stays `sparring_mix` (AI-SPEC's), values become 0.30/0.50/0.20 |
| Checkpoint cadence | `checkpoint_every = 5000` | snapshot every 10 000 for the *pool* | **Both — they are different things.** `checkpoint_every = 5000` is crash-recovery; `pool_snapshot_every = 10000` is past-self pool admission. Two keys, not one |
| Q-table save | "atomic via `os.replace`" | `os.replace` is not atomic on Windows | **RESEARCH.** Rotate `.prev`, validate on load with fallback, bounded retry on `PermissionError` (WinError 32) |
| Artifacts location | `artifacts/` in-repo | outside OneDrive | **RESEARCH.** In-repo `artifacts/` holds only the final blessed outputs |

## Plans

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|-----------|-------------|
| 03-00 | Phase-3 scaffold: `[strategy]`/`[training]` config, `matplotlib` dev dep, config loader reusing `loader_helpers`, test stubs | 1 | none | QUAL-02, QUAL-11, QUAL-13 |
| 03-01 | `docs/PRD_rl_strategy.md` v1.00 — the per-mechanism PRD, written **before** the policy code (SEGAL §2.5 step 5) | 1 | none | DOC-02 |
| 03-02 | `BrainBase` + `Observation`/`Decision` contracts + config-driven brain registry | 2 | 03-00 | STRAT-03, STRAT-07 |
| 03-03 | BFS pathfinding + distance oracle on the barrier-aware grid | 2 | 03-00 | STRAT-04, QUAL-02 |
| 03-04 | Bayes motion prior + fallback policy + `HeuristicBrain` baseline | 3 | 03-02, 03-03 | STRAT-02 |
| 03-05 | State encoding + JSON Q-table with per-key visit counts | 3 | 03-00, 03-02 | STRAT-01 |
| 03-06 | `QLearningBrain` — ε-greedy selection, `min_visits` fallback trigger, Q-update rule | 4 | 03-04, 03-05 | STRAT-01, STRAT-07 |
| 03-07 | Cop barrier sub-policy (two-stage decision, quota-respecting, truthful) | 4 | 03-02, 03-03 | STRAT-05 |
| 03-08 | Offline training harness + sparring pool + resumable atomic checkpoints | 5 | 03-06, 03-04 | STRAT-06 |
| 03-09 | Learning-curve CSV + matplotlib plotting + README section | 6 | 03-08 | STRAT-06 |
| 03-10 | §10.4 gate tests (GATE-1…4) + STRAT coverage audit | 7 | all | STRAT-01…07 |

## Notes for the executor

- **Plan size discipline (deliberate for this phase):** plans state *what* to build, the
  contract, and the non-obvious constraints — they do not transcribe the file contents.
  Phase 2's plans averaged ~850 lines each and re-wrote in prose what the code then said in
  Python. Phase 3 plans target ~150–220 lines. If a plan needs the exact wording of a rule,
  it cites the file rather than quoting it.
- **Every plan is subject to the standing gates** (`ruff` 0, coverage ≥85%, ≤150 lines per
  file, `uv` only, zero hardcoded values, zero secrets) — these are not restated per plan.
- **Numeric discipline:** game values (7×7 board, 14 barriers, 35 turns) come from
  `docs/PARAMETERS.md` and may never be altered. RL hyperparameters are chosen by us and
  live in config, labelled as engineering defaults per D-18.
