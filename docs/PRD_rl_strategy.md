# PRD — RL Strategy Module (Q-Learning Policy)

**Version:** 1.00 · **Status:** ⛔ SUPERSEDED 2026-08-08 — see the banner below · **Updated:** 2026-07-31

> # ⛔ SUPERSEDED — 2026-08-08 — DO NOT IMPLEMENT
>
> **Replaced by [docs/PRD_matrix_mover.md](PRD_matrix_mover.md)**, the per-mechanism PRD for the
> matrix-game mover that actually ships.
>
> **Why.** The mechanism described below — a per-role tabular Q-table trained by self-play, with
> moves chosen by `argmax` over a Q-row — was **withdrawn as unsound under the book's turn
> order**. Book §5.3.2 p.35 makes the turn *simultaneous*: the Acknowledge phase
> *"guarantees that the reveal will occur only when both sides have already fixed their moves"*.
> That makes the game a two-player zero-sum **matrix game**, not an MDP, so `max_a' Q(s',a')` has
> no meaning, and an `argmax` policy is deterministic by construction and therefore readable by
> any searching opponent. The full argument, with the measurements that settled it, is in
> [docs/phases/phase-3/PRD.md](phases/phase-3/PRD.md) §2, with the narrative in
> [ENGINEERING-LOG.md](phases/phase-3/ENGINEERING-LOG.md) and
> [RUN-1-POSTMORTEM.md](phases/phase-3/RUN-1-POSTMORTEM.md).
>
> **Nothing below is implemented.** No file under `src/pursuit/strategy/` implements this
> mechanism: there is no `QLearningBrain`, no `HeuristicBrain`, no Q-table artefact and no
> `qtable_<role>.json`. `strategy/registry.py` registers exactly three brains — `value_search`
> (the shipped mover), `chaser_cop` and `greedy_evader` (the sparring anchors). Treat every
> section below as a record of a design that was tried and dropped, never as a contract on the
> code.
>
> **Kept, not deleted**, deliberately — the same discipline commit `da345dd` applied to the twelve
> superseded plans `03-14..03-25`: the record of what was planned, and why it was dropped,
> is part of the engineering evidence.
>
> Superseded in the run-2 rebuild landed 2026-08-08 (`8b30328`, `f3d9847`, `2606efa`, `7040d7a`;
> planning state reconciled in `da345dd`).

> Per-mechanism PRD required by CLAUDE.md and [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §2.3,
> written before the code it describes (§2.5 step 5) — no file under `src/pursuit/strategy/`
> exists yet. Covers the Q-learning policy's *mechanism*: state encoding, reward, update rule,
> exploration, fallback, training regime, evaluation bar. Framework rationale, failure modes and
> the evaluation rubric are locked in
> [03-AI-SPEC.md](../.planning/phases/03-blind-strategy-module-rl-policy/03-AI-SPEC.md); this
> document cites that contract rather than duplicating it. Every number below is either traced to
> [PARAMETERS.md](PARAMETERS.md) or explicitly labelled an engineering default in §9 — nothing
> here is invented.

## 1. Mechanism and scope

Each turn, both the cop and the thief process convert a local observation — own cell, a
*believed* target cell, agent-relative blocked-direction bitmask, barriers-used count, and a
bucketed turn phase — into one of 5 movement actions via a per-role Q-table trained offline by
self-play. States the table has not learned enough about fall back to a Bayes motion-model prior
combined with a BFS distance oracle on the barrier-aware grid. The cop additionally runs a
separate, non-Q barrier sub-policy after choosing its movement. This is the mechanism AI-SPEC §1
classifies and §2 selects the (framework-free, stdlib) implementation approach for; this PRD is
the encoding/reward/update/fallback/training contract the code in 03-04…03-08 must match exactly.

**Requirements covered:**

| REQ-ID | Description |
|--------|-------------|
| STRAT-01 | Move selection uses a trained tabular Q-learning policy via `BrainBase._pick_move` |
| STRAT-02 | A fallback handles states the Q-table has never (sufficiently) visited |
| STRAT-03 | The strategy module is pluggable via config `[strategy]`, separate from networking |
| STRAT-04 | Given a known target, the agent walks the shortest path with no manual intervention |
| STRAT-05 | The cop selects barrier placement via `_decide_move` |
| STRAT-06 | Training is offline; a trained Q-table ships; learning curves instrumented from run 1 |
| STRAT-07 | The algorithm chooses the move — the language model never does (rule 25) |
| DOC-02 | This document — the per-mechanism PRD for the Q-learning policy |

**In scope:** state encoding, action space, reward function, Q-update rule, ε/α schedules, the
fallback trigger and its distance metric, the barrier sub-policy's place in the decision order,
the offline training regime, the sparring pool, checkpointing, and the evaluation success bar.

**Out of scope (future phases, not a Phase-3 deliverable):** scent and pheromone evidence, hint
parsing, the Bayes belief map's evidence-update step, and any LLM text — all Phase 4. Cloud
tunneling — Phase 5. Commit-reveal and Step-0 — Phase 6. None of these appear in the code this
PRD governs; Phase 3 plays **blind**, with a known target cell standing in for the belief map
Phase 4 will supply through the same input contract (§10).

## 2. State encoding (D-04, D-05, D-06)

The Q-table key is a canonical string built from five fields, in this fixed order:

```
own_row,own_col|target_row,target_col|blocked_mask|barriers_used|turn_bucket
```

| Field | Composition | Cardinality |
|---|---|---|
| `own_row,own_col` | Absolute own-cell coordinate | 7×7 = 49 |
| `target_row,target_col` | Absolute **believed** target-cell coordinate (D-11, §10) | 7×7 = 49 |
| `blocked_mask` | Agent-relative bitmask of which of the 4 orthogonal directions are currently blocked (barrier or board edge), integer 0–15 | 16 |
| `barriers_used` | Count of barriers placed so far this game, 0 through `barrier_quota` | 15 |
| `turn_bucket` | Bucketed turn phase (early=0 / mid=1 / late=2), boundaries from `strategy.turn_bucket_fractions` | 3 |

**Worked example.** Own cell `(2,3)`, believed target `(5,5)`, blocked directions {N, W}
(bitmask `1001` = `9`), 6 barriers placed, turn 14 of a game whose `move_ceiling` is 35 (minimum,
PARAMETERS.md Table 15 row 3). `turn_bucket_fractions = [0.34, 0.69]` (config `[strategy]`) place
the boundaries at turns `0.34×35 ≈ 11.9` and `0.69×35 ≈ 24.15`; turn 14 falls between them, so
`turn_bucket = 1` (mid). Encoded key:

```
2,3|5,5|9|6|1
```

**Why the full barrier bitmap is excluded.** A full 7×7 barrier bitmap is 2^49 ≈ 5.6×10^14
combinations per positional pair — the table would never converge; nearly every state would be
visited at most once, which is failure mode 4 in AI-SPEC §1 (state-space explosion). The
agent-relative blocked-direction bitmask captures the only barrier information that changes which
of the 5 actions are legal or attractive *from this cell*, at a fixed cost of 16 values.

**Why the raw turn index is excluded.** Using the raw turn number (0..34, one value per turn up
to `move_ceiling = 35`) instead of 3 buckets multiplies the turn dimension by up to **35×**,
diluting visits per state without adding any strategic distinction most individual turns need —
the thief's end-game stalling choice only depends on *which phase* of the game it is in, not the
exact turn count.

**State-space size arithmetic.** Full theoretical cross product:
`49 × 49 × 16 × 15 × 3 = 1,728,720` distinct keys. This is an upper bound, not the expected
populated size — many combinations are unreachable or vanishingly unlikely in practice (e.g. a
given `barriers_used` count correlates strongly with `turn_bucket`, and several `blocked_mask`
values require board geometry that only some `(own, target)` pairs permit). `eval.max_table_keys`
(§9.2) is a health ceiling on the *actually populated* table after training, checked against this
bound, not equal to it.

## 3. Action space

Exactly **5** movement actions: `N`, `E`, `S`, `W`, `STAY` — the fixed "4 orthogonal + stay, no
diagonals" movement range (PARAMETERS.md Table 15 row 1, **fixed**).

**The barrier decision is deliberately not an action (D-12).** Folding "place a barrier in
direction X" into the action set would multiply the action space (5 moves × up to 4 barrier
directions × "no barrier"), fragmenting visits across a much larger table for a decision that is
cop-only and structurally different from movement. Instead the cop runs a **two-stage decision**:
`_pick_move` selects one of the 5 movement actions from the Q-policy (or the fallback), then a
separate heuristic barrier sub-policy (`_decide_move`, STRAT-05, 03-07) decides whether and where
to place a barrier that same turn. The Q action space stays at exactly 5 for both roles; the
thief's `_decide_move` never places a barrier.

## 4. Reward function

| Signal | Value | When | Config key | Source |
|---|---|---|---|---|
| Capture | **1.0** | Cop's terminal reward when it captures the thief | `training.reward_capture` | engineering default |
| Survival | **1.0** | Thief's terminal reward when it survives to `survival_threshold` | `training.reward_survival` | engineering default |
| Step cost | **-0.01** | Every non-terminal turn, both roles | `training.reward_step` | engineering default |
| Barrier-gain shaping | **0.05** | Cop-only; awarded when a placed barrier strictly increases the thief's BFS distance to escape (guides the barrier sub-policy without dominating the terminal signal) | `training.reward_barrier_gain` | engineering default |

**These reward values are not the league scoring table and are not reused from it.** §1.3 of the
book states the reward function R "translates directly" from the scoring table as a general
design principle, but this mechanism's reward signal uses its **own**, independently-scaled
values (unit-magnitude terminal rewards, a small negative per-step cost, a small positive shaping
term) rather than reusing PARAMETERS.md Table 17's capture/survival/tie scores (20/5, 5/10, 2 —
all **fixed**, §9.1). Table 17 governs **league match outcomes and points**; it is read by
`pursuit.sdk.rules.score_outcome` and is never touched by the learner. Reusing it directly as a
reward would put the Q-update's numeric scale at the mercy of a table this mechanism must never
alter, and 20/5/5/10 are not designed to be a well-behaved reward signal (asymmetric magnitudes
that would bias the discounted return between roles). This separation is itself an engineering
decision (D-18): the reward signal is ours to tune, the scoring table is not.

## 5. Update rule and exploration

**Q-update** (standard off-policy tabular Q-learning), applied once per environment step:

```
Q(s,a) ← Q(s,a) + α · (r + γ · max_a' Q(s',a') − Q(s,a))
```

- `γ` (discount factor) = `training.gamma` — fixed per run, does not decay.
- `α` (learning rate) decays alongside `ε` (D-25): linear decay from `training.alpha` down to
  `training.alpha_floor`, over `training.alpha_decay_episodes` episodes, floor held thereafter:

```
α(e) = max(alpha_floor, alpha − (alpha − alpha_floor) × min(e, alpha_decay_episodes) / alpha_decay_episodes)
```

**ε-greedy exploration schedule** — linear decay from `training.epsilon_start` to
`training.epsilon_floor` over `training.epsilon_decay_episodes` episodes, same shape as `α`:

```
ε(e) = max(epsilon_floor, epsilon_start − (epsilon_start − epsilon_floor) × min(e, epsilon_decay_episodes) / epsilon_decay_episodes)
```

At episode `e`, with probability `ε(e)` a uniformly random legal action is taken; otherwise the
argmax action over the 5 Q-values for the current state key. **At evaluation and match time,
`ε = strategy.epsilon_eval` (0.0) — fully greedy, no exploration.** Every hyperparameter above is
named only as a config key in source; none is a literal (§9.2).

**D-19: `random`, not `secrets`, for exploration.** ε-greedy action selection and opponent
sampling use a seeded `random.Random(training.seed)` instance — never module-level `random.*`
(whose global state any library call can perturb) and never `secrets`. Reproducibility under a
fixed seed is the goal here; `secrets` is reserved for Phase 6's cryptographic nonce generation, a
different requirement with a different threat model. Conflating the two would make training runs
non-reproducible for no security benefit, since nothing in Phase 3 is adversarial input.

## 6. Fallback (D-08, D-09, D-10)

**Trigger:** the fallback is used when the current state key is **absent from the table, OR** its
recorded visit count is below `strategy.min_visits` (STRAT-02). Both conditions route to the same
fallback — a state with a handful of visits is not meaningfully different from an unvisited one;
its Q-values are noise, not a learned preference (AI-SPEC failure mode 2).

**Bayes motion-model prior.** When the target cell itself is not directly known (Phase 4's
belief map has not yet narrowed it — not exercised by Phase 3's known-target contract, but the
fallback's prior mechanism is specified here so Phase 4 needs no retrain), the prior over the
opponent's plausible cells starts uniform and is spread each turn by the opponent's legal moves —
a **prediction step only**, with no evidence incorporated (no scent, no hint). Phase 4 plugs
scent/hint evidence into this exact same update; the update rule itself does not change.

**Distance metric: BFS on the barrier-aware grid, not raw Manhattan (D-09).** STRAT-02 as worded
in REQUIREMENTS.md names the fallback "Bayes + Manhattan." The implementation here is **Bayes +
barrier-aware BFS**, and that deviation is deliberate and recorded, not a silent drift: raw
Manhattan distance ignores barriers entirely, so a fallback built on it walks straight into a
barrier pocket and stalls exactly where cornering play was designed to happen (AI-SPEC failure
mode 3, STRATEGY.md's "known risk"). BFS on the barrier-aware grid is the generalization that
degrades gracefully to the same value Manhattan would give whenever no barrier blocks the direct
path, and only diverges — correctly — once one does. The fallback picks the legal move that
strictly reduces this BFS distance to the believed target.

## 7. Training regime (D-13, D-15, D-17)

**Offline only; no training during a league match.** Episodes step `pursuit.sdk.engine` directly
and **never** the FastMCP network layer (D-17). Reasons: (1) a `training.episodes = 300000`
overnight run requires in-process speed — routing every step through two live async peer
processes would add IPC/deadline/watchdog overhead built for a different problem (Phase 2's
resilience machinery, irrelevant to a solitary training loop) and make the run orders of
magnitude slower; (2) the network layer's turn-passing model assumes two independent processes
with no shared state, which is the opposite of what a fast training loop needs.

**Sparring pool composition (D-13).** Each episode samples one opponent from three sources,
weighted by `training.sparring_mix = [0.30, 0.50, 0.20]` (heuristic / past-self / reference impl,
in that order — the RESEARCH-ruled weighting, see 03-PLAN-OUTLINE.md's conflict-resolution table;
`HeuristicBrain` is *also* the eval opponent, so weighting it much higher would train on the test
set). The sampled opponent is frozen and read-only for the whole episode — sampling happens once
per episode, never mid-episode, so the Q-target's stationarity assumption holds and no live table
object is ever shared between the learner and its opponent (project rule 2). Past-self opponents
are drawn δ-uniformly (`training.selfplay_delta = 0.5`) from a ring buffer of the newest
`training.pool_size = 10` checkpoints snapshotted every `training.pool_snapshot_every = 10000`
episodes, plus one pinned early anchor so the pool always retains a weak opponent. The reference
implementation is optional and import-guarded (`training.reference_impl_path`, empty default,
D-21); when absent, its pool weight is dropped and the remaining two are renormalized rather than
the run failing. Mechanics of the pool's snapshot/retention machinery are 03-RESEARCH.md §2's to
detail; this PRD fixes only the composition and sampling-cadence contract 03-08 must implement
against.

**Checkpoint cadence and resumability.** Two distinct cadences, not one key doing double duty:
crash-recovery checkpoints every `training.checkpoint_every = 5000` episodes, separate from the
`pool_snapshot_every = 10000`-episode cadence that admits a new past-self snapshot into the
sparring pool. A checkpoint persists the **whole run state** — episode index, current `ε`/`α`,
RNG state, seed, config hash, CSV row count, and the Q-tables — not the table alone, so a resumed
run reproduces the same curve rather than silently restarting exploration or reward accounting
(D-24). Checkpoint writes must be crash-safe (atomic write + prior-generation retention); the
exact Windows-safe write mechanics are an implementation concern of 03-08, informed by
03-RESEARCH.md §3, and are not re-derived here.

**Seed logging.** `training.seed = 1337` is recorded in every checkpoint/manifest and every CSV
header, so a curve can be reproduced from its own artifacts alone (D-15).

## 8. Evaluation (D-14, D-16)

**Success bar.** `QLearningBrain` must beat `HeuristicBrain` head-to-head, per role, over the
fixed eval scenario set (`eval.eval_scenarios = 20` scenarios × `eval.repeats_per_scenario = 10`
seeds = `eval.eval_games = 200` games per arm per role), at a win rate meeting both
`eval.win_rate_margin = 0.10` above the measured baseline rate and the absolute floor
`eval.min_win_rate_absolute = 0.55` (D-14). The full statistical rubric — paired McNemar exact
test at `eval.significance_alpha = 0.05`, why the margin is not a flat 50%, and why both roles
must pass independently — is locked in
[03-AI-SPEC.md](../.planning/phases/03-blind-strategy-module-rl-policy/03-AI-SPEC.md) §5,
dimension E5; this PRD does not restate it.

**Learning-curve instrumentation from episode 1 of run 1 (D-16, rule 42).** A CSV row is appended
every `training.curve_log_every = 500` episodes, carrying `(episode, epsilon, mean_reward,
winrate_vs_baseline, fallback_rate)`. Retrofitting curves after the fact would mean re-running an
overnight training pass, so the harness must emit these from the very first training episode of
the very first run, never added later. **README PNG obligation:** rule 42 requires the README to
carry a learning-curve section for an RL-based strategy; the CSV is rendered into PNGs by a
`matplotlib`-based script (`training/plot_curves.py`, dev-only dependency, D-20) and embedded in
the submission README (Phase 8, but the artifact pipeline exists from Phase 3).

## 9. Parameter table

Every number this mechanism uses appears in one of the two tables below. A number that is not in
either table does not belong in this mechanism.

### 9.1 Traced to PARAMETERS.md — game values, never invented, never altered here

| Parameter | Value | Source | Status |
|---|---|---|---|
| Board size | 7×7 | PARAMETERS.md Table 13 row 1 | minimum |
| Movement range (basis for the 5-action space, §3) | 4 orthogonal + stay | PARAMETERS.md Table 15 row 1 | **fixed** |
| Barrier quota | 14 | PARAMETERS.md Table 15 row 2 | minimum |
| Move ceiling (`move_ceiling`, used in the turn-bucket arithmetic, §2) | 35 | PARAMETERS.md Table 15 row 3 | minimum |
| Survival threshold | 35 | PARAMETERS.md Table 15 row 4 | minimum |
| Capture score, cop / thief | 20 / 5 | PARAMETERS.md Table 17 rows 1–2 | **fixed** — league scoring only, not the reward signal (§4) |
| Survival score, cop / thief | 5 / 10 | PARAMETERS.md Table 17 rows 3–4 | **fixed** — league scoring only |
| Tie score | 2 | PARAMETERS.md Table 17 row 5 | **fixed** — league scoring only |

These values may never be altered by this mechanism: **fixed** rows disqualify the team on any
deviation, and **minimum** rows may only ever be raised by mutual agreement, never lowered. They
arrive here via `game_params.json` (loaded through the existing Phase-1/2 config path), not via
`strategy.json`.

### 9.2 Engineering defaults — NOT PARAMETERS.md values (D-18)

**Every value below is our own choice, config-tunable, and never sourced from PARAMETERS.md.**
They are internal RL hyperparameters, not game parameters.

| Default | Value | Config key | Note |
|---|---|---|---|
| Fallback visit threshold | 20 | `strategy.min_visits` | STRAT-02 trigger, §6 |
| Turn-bucket boundaries | `[0.34, 0.69]` | `strategy.turn_bucket_fractions` | fractions of `move_ceiling`, §2 |
| Eval/match exploration | 0.0 | `strategy.epsilon_eval` | greedy, §5/§8 |
| Decision latency budget | 50 ms | `strategy.max_decision_ms` | inside the Phase-2 turn deadline |
| Oscillation breaker window / limit | 6 / 3 | `strategy.oscillation_window` / `strategy.oscillation_limit` | online guardrail, not this PRD's focus |
| Learning rate / discount | 0.15 / 0.95 | `training.alpha` / `training.gamma` | §5 |
| ε start / floor / decay length | 1.0 / 0.05 / 150000 | `training.epsilon_start` / `epsilon_floor` / `epsilon_decay_episodes` | §5 |
| α floor / decay length | 0.02 / 150000 | `training.alpha_floor` / `training.alpha_decay_episodes` | mirrors the ε decay length, D-25 |
| Episode count | 300000 | `training.episodes` | overnight run, §7 |
| Checkpoint interval | 5000 | `training.checkpoint_every` | crash recovery, §7 |
| Curve log interval | 500 | `training.curve_log_every` | rule 42, §8 |
| Sparring mix | `[0.30, 0.50, 0.20]` | `training.sparring_mix` | heuristic/past-self/reference, §7 |
| Pool snapshot interval / size | 10000 / 10 | `training.pool_snapshot_every` / `training.pool_size` | past-self pool, §7 |
| Past-self sampling shape | 0.5 | `training.selfplay_delta` | δ-uniform, §7 |
| Training seed | 1337 | `training.seed` | §7/§8 |
| Reward terms | 1.0 / 1.0 / -0.01 / 0.05 | `training.reward_capture` / `reward_survival` / `reward_step` / `reward_barrier_gain` | §4 |
| Eval set size | 20 × 10 = 200 | `eval.eval_scenarios` / `eval.repeats_per_scenario` / `eval.eval_games` | §8 |
| Eval win-rate bar | 0.10 / 0.55 / 0.05 | `eval.win_rate_margin` / `eval.min_win_rate_absolute` / `eval.significance_alpha` | §8, AI-SPEC §5 E5 |
| State-space health ceiling | 250000 | `eval.max_table_keys` | §2 |

The first table (§9.1) may never be altered by this mechanism except by raising a **minimum** row
upward through mutual agreement with the opponent team; the second (§9.2) is entirely ours to
tune, and every future change to a value in it belongs in `config/{police,thief}/strategy.json`,
never as a literal in `src/`.

## 10. Boundaries and honesty

- **Input contract: a believed target cell (D-11).** `_pick_move` and the fallback both consume
  a `target_cell` that Phase 3 populates with the *known* target (the Stage-3 gate condition) and
  Phase 4 will populate with the belief map's argmax cell instead. The state-key format, the
  Q-table, and every trained checkpoint are unaffected by this swap — **no retraining is required
  when Phase 4's belief map arrives.**
- **The algorithm chooses the move; the language model never does (rule 25 / STRAT-07).** Every
  move is traceable to `_pick_move` (Q-table lookup or fallback); no LLM, script, or human input
  sits anywhere on that path in this phase, and Phase 4's LLM is confined to hint decoding and
  bluff text around this boundary, never inside it.
- **Cop and thief hold separate Q-tables in separate processes (D-03, project rule 2).** Each
  role's `QLearningBrain` loads its own `qtable_<role>.json` at construction and holds it only in
  that process; there is no shared live table object, module-level cache, or shared game-state
  object between the two roles at any point — sharing one would be an information-leakage
  disqualification, not a design smell.
- **Barrier declarations are truthful and within quota (rules 16, 22).** The cop's barrier
  sub-policy (§3, STRAT-05) never declares a placement it did not make, and never exceeds
  `barrier_quota` (§9.1); the thief's `_decide_move` never places a barrier at all.

---

*Every number in this document appears in §9.1 (a PARAMETERS.md game value) or §9.2 (a labelled
engineering default) or is a section/table number. None is invented.*
