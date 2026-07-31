# PRD — RL Strategy Module (Q-Learning Policy)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-07-31

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
