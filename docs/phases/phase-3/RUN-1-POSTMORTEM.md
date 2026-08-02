# Run-1 training post-mortem — why GATE-4 failed, and what run 2 must change

**Status:** research, not yet actioned · **Date:** 2026-08-02 · **Owner:** Khaled
**Subject:** the 300,000-episode run of 2026-08-02 (seed 1337, config hash `5fa4d554…`)

Every number below was measured from run-1's own artefacts — `artifacts/curves/curves.csv`,
the checkpointed tables in `%LOCALAPPDATA%\pursuit\training\`, and instrumented replays through
the project's own `training/harness.py` and `training/eval_arms.py`. Nothing here is estimated.

**Validation anchor:** an independent re-implementation of the eval arms reproduces the official
GATE-4 result *exactly* — cop **5/20 = 0.250**, thief **16/20 = 0.800**. Every split below
decomposes those same 40 games, so the decomposition is arithmetically forced, not inferred.

---

## Verdict in one line

The cop's algorithm works and the recorded diagnosis is wrong; the thief's reward function is
mathematically degenerate and was never capable of learning. Neither failure is fixed by
training longer, and neither is config-only.

---

## Finding 1 — the cop learned fine. It was tested somewhere it had never been.

The recorded conclusion was "still climbing when ε hit its floor → train longer". The curve data
does not support that as the *primary* cause.

**The cop's training win rate against the heuristic thief, by decile:**

| decile | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| win rate | 0.006 | 0.024 | 0.055 | 0.129 | 0.194 | 0.242 | 0.303 | 0.548 | 0.506 | **0.854** |

Peak 0.9435 at episode 293,999. Final 10 curve rows: **0.900**. The cop ends training beating
the heuristic thief nine games in ten. GATE-4 then measured it at 0.250. That 0.90 → 0.25 gap is
the thing to explain, and it is not a shortage of episodes.

**Cause: every one of the 300,000 episodes started from the same board.**
`training/harness.py::run_episode` calls `engine.make_state(params.game_params)` — cop `(0,0)`,
thief `(3,3)`, turn 0, no barriers. The cop's state key for that position, `0,0|3,3|9|0|0`, has
exactly **150,000 visits** — one per cop episode. The 20 GATE-4 scenarios use **17 distinct start
pairs**, only one of which is the training start.

**Coverage of the eval start states in the trained table** (`visits >= min_visits`, i.e. whether
the brain consults the table at all rather than falling straight through to the BFS fallback):

| role | eval start states above `min_visits` |
|---|---|
| cop | **5 / 20** |
| thief | **4 / 20** |

**Split the official 0.250 by that same line:**

| role | trained start states | unseen start states | overall |
|---|---|---|---|
| cop | **3/5 = 0.600** | **2/15 = 0.133** | 5/20 = 0.250 ✔ matches GATE-4 |
| thief | 2/4 = 0.500 | 14/16 = 0.875 | 16/20 = 0.800 ✔ matches GATE-4 |

The cop wins **0.600** where it was trained and **0.133** where it was not. The gate wants 0.55.
*It is already above the bar on the states it actually saw.* What failed is generalisation, and
the reason it cannot generalise is structural: the state key is
`own_cell|target_cell|blocked_mask|barriers_used|turn_bucket` — **absolute coordinates, tabular,
no sharing between positions.** A table trained from one start covers only the reachable cone from
that start. There is no mechanism by which experience at `(0,0)` transfers to `(4,4)`.

Supporting evidence of the same concentration:

- top 1% of cop keys hold **53.2%** of all 3,525,039 visits
- 17.7% of cop keys were visited exactly once; only **35.2%** ever cleared `min_visits=20`
- median best-vs-second-action Q margin across the whole cop table: **0.00000**

---

## Finding 2 — the thief was never told it had been caught

This is the more serious defect, and it is a correctness bug, not a tuning problem.

### 2a. The capture transition is dropped entirely

Capture is produced by `engine.apply_cop_action` — during the **cop's** turn.
`training/harness.py::_turn` only calls `_update_learner` when `role == learner.role`. So when the
learner is the thief and the cop captures it, the loop breaks without ever issuing an update.

**Measured, not argued.** A thief instrumented to log every `update()` it receives, made to walk
into the cop, captured 300/300 times:

```
thief walks into cop:  CAPTURE=300/300  SURVIVAL=0/300
  thief updates per episode : mean=1.00
  final update's reward     : {-0.01: 300}
```

One update, worth **−0.01** — the ordinary step cost. The single most important event in the
thief's world produces **no signal at all**. There is no state anywhere in the thief's MDP that
carries a capture penalty, because `_reward` returns `reward_capture if role == "cop" else 0.0`.

### 2b. γ = 0.95 cancels the survival bonus against the step cost

The thief's only positive reward arrives at turn 35. With γ = 0.95 the effective horizon is
1/(1−γ) = **20 steps** — barely half the task horizon — and γ³⁴ = **0.175**.

| thief outcome | discounted value at t=0 |
|---|---|
| survives all 35 turns | **+0.0098** |
| captured on move 4 | **−0.0371** |
| **entire usable value range** | **0.047** |

The +1.0 survival reward discounts to +0.175; the accumulated step penalties sum to −0.165. They
cancel almost exactly. For comparison, the cop's reward is well-formed:

| cop outcome | discounted value at t=0 |
|---|---|
| captures on move 4 | +0.9715 |
| places all 14 barriers, never captures | +0.3455 |
| **usable value range** | **0.626** |

**The cop's learning signal is 13× stronger than the thief's.** With α starting at 0.15 against a
sparring opponent resampled every episode, a 0.047 spread is below the noise floor.

### 2c. This predicts the observed collapse, quantitatively

| decile | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| thief win rate | 0.084 | 0.072 | 0.093 | 0.106 | 0.085 | 0.063 | 0.050 | 0.046 | 0.029 | **0.016** |
| fallback rate | 0.325 | 0.241 | 0.224 | 0.190 | 0.185 | 0.176 | 0.151 | 0.101 | 0.067 | 0.041 |
| mean reward | +0.019 | +0.031 | +0.040 | +0.039 | +0.040 | +0.030 | +0.016 | +0.002 | −0.019 | **−0.029** |

Final mean reward −0.0288 ÷ step cost −0.01 = **2.9** — the thief is being captured after about
three of its own moves, essentially every episode. Its best win rate (0.506) was at episode 1,000,
when it was still almost entirely BFS fallback.

The recorded diagnosis — "`fallback_rate` collapsed 0.76 → 0.009, so it abandoned the BFS
fallback" — describes the **symptom** correctly. The cause is that as visit counts crossed
`min_visits=20`, the brain switched from a working heuristic to Q-values whose entire spread was
0.047 and therefore noise. Evidence: among thief keys that *do* clear the `min_visits` gate, the
median best-vs-second margin is **0.00033**, and **17.6%** are exact ties. The argmax those states
return is arbitrary.

---

## Finding 3 — the ε and α schedules leave no consolidation phase

`epsilon_decay_episodes = 150000` and each role receives exactly 150,000 of the 300,000 episodes,
so ε reaches its floor at episode **299,999 of 300,000 — 100% of the way through**. Same for α.
The agent never gets a stretch of near-greedy play to consolidate what it explored. This is what
produced the recorded `final_slope = +0.094`. It is real, but it is a second-order effect next to
Findings 1 and 2.

---

## Finding 4 — two further structural issues found while measuring

1. **No terminal-state marking anywhere.** `QLearningBrain.update` always computes
   `target = reward + gamma * max_a Q(next_key, a)`. At episode end `next_key` is an ordinary
   encoded key that collides with non-terminal states sharing the same positions, mask,
   `barriers_used` and `turn_bucket`. Terminal values leak into live states.
2. **The sparring mix is not what the config says.** `reference_impl_path` is empty, so the
   reference arm drops out and `_available_weights` renormalises `[0.30, 0.50, 0.20]` to
   **0.375 heuristic / 0.625 past-self**. The thief spent 62.5% of training against past-self
   cops, not the configured 50% — while those cops were climbing to a 0.90 win rate.
3. **The barrier layout is invisible to the policy.** The key carries only `blocked_mask`
   (4 local bits) and `barriers_used` (a count). Barrier *placement* is chosen by the
   hand-written `choose_barrier`, never learned. This is deliberate (D-05, to avoid a 2⁴⁹ blow-up)
   but it means the cop's ceiling is bounded by that heuristic, and no amount of training moves it.

---

## What run 2 should change, in priority order

| # | Change | Evidence it addresses | Type |
|---|---|---|---|
| **R1** | **Randomise the episode start state** — sample cop/thief cells per episode instead of always `make_state`. | cop 0.600 trained vs 0.133 unseen; 5/20 eval starts covered | **code** (`harness.py`, `loop.py`) |
| **R2** | **Deliver the terminal transition to the learner whichever role's move caused it**, and give the thief a real capture penalty (`reward_capture_penalty ≈ −1.0`). | 300/300 captures produced one −0.01 update | **code + config** |
| **R3** | **γ 0.95 → 0.99.** | effective horizon 20 < task horizon 35; thief value range 0.047 → 0.461 | config |
| **R4** | **Mark terminal states** so the final update bootstraps from 0. | terminal keys collide with live keys | code |
| **R5** | **ε and α floors at ~60% of the run**, not 100%. | floor reached at episode 299,999/300,000 | config |
| **R6** | **Land the eval-honesty fix** (n = 20, not 200) before measuring anything. | replays are deterministic — confirmed again here: 1 repeat and 10 repeats give identical results | code (already ~done, uncommitted) |

**Combined effect on the thief's reward signal** (R2 + R3), computed exactly:

| configuration | survive | captured move 4 | usable range |
|---|---|---|---|
| run-1 (γ=0.95, no penalty) | +0.0098 | −0.0371 | **0.047** |
| γ=0.99 | +0.4211 | −0.0394 | **0.461** (10×) |
| γ=0.99 + capture penalty −1.0 | +0.4211 | −1.0097 | **1.431** (30×) |

### What is *not* worth doing

- **"Train longer"** (recorded as T4-followup-1). The cop already reaches 0.90 on its training
  distribution; more episodes on one start state buys nothing measurable at eval.
- **"Raise `min_visits` to keep the fallback alive longer"** (recorded as T4-followup-2). It would
  raise the score by using the *heuristic* more — the thief's unseen-start win rate is already
  0.875 precisely because it falls back. That masks the defect rather than fixing it, and STRAT-06
  asks for a table that beats the heuristic, not one that hides behind it.
- Both were recorded as **config-only**. Neither is: R1, R2 and R4 all require code changes.

### Open question that must be settled before run 2

`min_win_rate_absolute = 0.55` for the cop, while the measured heuristic-vs-heuristic baseline on
these scenarios is **0.100**. The bar asks the learned cop to be 5.5× the hand-written one.

**Provenance, checked:** 0.55 does **not** appear anywhere in `docs/PARAMETERS.md` (142 lines,
zero matches). It originates in this project's own `docs/PRD_rl_strategy.md` §8 as decision
**D-14**, cross-referenced by AI-SPEC §5 E5. So it is *our* engineering bar, not one of Segal's
binding fixed values — which means it can legitimately be revisited on evidence, unlike a
PARAMETERS.md number. It should not be moved casually, and it must not be moved *because a run
failed*; but it is a design decision that is allowed to be re-argued.

Two data points say it is not obviously unreachable — the cop hit 0.900 in training and 0.600 on
the eval starts it had seen. Against that: on an open 7×7 grid a single pursuer cannot corner a
perfect evader at all (the grid is not cop-win for one cop), so capture depends entirely on
barrier play — which the policy cannot represent (Finding 4.3) and does not choose. **Settle
whether 0.55 is the right bar for a movement-only policy before committing another night to it.**

---

## Ablation — ran, and it is INCONCLUSIVE. Do not cite it as support.

Four arms, 10,000 episodes each (5,000 per role), same seed and machinery, each evaluated with
the project's own `eval_arms.play_game` on the same 20 held-out scenarios.

| arm | change | cop | 95% CI | thief | 95% CI |
|---|---|---|---|---|---|
| — | heuristic baseline | 0.10 | — | 0.90 | — |
| A | run-1 config exactly | 2/20 = 0.10 | [0.00, 0.23] | 14/20 = 0.70 | [0.50, 0.90] |
| B | + randomised starts (R1) | 4/20 = 0.20 | [0.02, 0.38] | 11/20 = 0.55 | [0.33, 0.77] |
| C | + γ = 0.99 (R3) | 5/20 = 0.25 | [0.06, 0.44] | 15/20 = 0.75 | [0.56, 0.94] |
| D | + capture penalty (R2, R4) | 4/20 = 0.20 | [0.02, 0.38] | 17/20 = 0.85 | [0.69, 1.00] |

**Every pairwise comparison is statistically insignificant** (Fisher exact, two-sided): cop A vs B
p=0.661, A vs C p=0.407, A vs D p=0.661; thief A vs D p=0.451, D vs baseline p=1.000. The
confidence intervals all overlap heavily.

Two reasons the pilot cannot decide anything, both structural:

1. **n = 20.** Eval replays are deterministic, so the effective sample is 20 games per arm per
   role no matter how many repeats are run. Detecting a 0.15 difference at n=20 is hopeless —
   this is the same pseudo-replication trap that inflated run-1's reported p-values (R6).
2. **Budget is 3.3% of run-1's.** 5,000 episodes per role against run-1's 150,000. Arms B/C/D
   spread those episodes over thousands of random start states, so **not one** eval start state
   cleared `min_visits`, and the learners fell through to the BFS fallback for most decisions.
   The arms largely measured the heuristic, not the learned policy.

The only defensible readings: the harness reproduces the baseline exactly (0.10 / 0.90), no arm is
catastrophically broken, and arm A's cop at this budget sits exactly on the heuristic baseline
(0.10) while the randomised-start arms sit above it (0.20–0.25) — weakly consistent with Finding 1,
and nothing more. **A decisive ablation needs a larger held-out scenario set (n in the hundreds, or
stochastic eval so replays carry information) and a budget nearer run-1's.** Until then the case
for R1–R6 rests on Findings 1–4, which are direct measurements and do not depend on this pilot.
