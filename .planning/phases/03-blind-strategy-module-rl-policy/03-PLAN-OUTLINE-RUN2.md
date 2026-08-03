# Phase 3 Plan Outline — RUN 2 (additive continuation)

**Phase:** 03-blind-strategy-module-rl-policy
**Continues:** [`03-PLAN-OUTLINE.md`](03-PLAN-OUTLINE.md) — the run-1 record. **D-01 … D-25 are
defined there and are not restated here.** That file must not be edited.
**Plans 03-00 … 03-10 are planned, executed and summarised.** They are history. This outline
plans **03-11 … 03-25** only.

**Why this block exists:** GATE-4 was measured on 2026-08-02 after a real 300,000-episode run
and **FAILED for both roles** (cop 0.250 against the 0.55 floor; thief 0.800 against a 0.900
heuristic baseline). The causes were measured, not guessed:
[`docs/phases/phase-3/RUN-1-POSTMORTEM.md`](../../../docs/phases/phase-3/RUN-1-POSTMORTEM.md)
and the `<superseded>` section of [`03-CONTEXT.md`](03-CONTEXT.md). **Where the top half of
`03-CONTEXT.md` conflicts with its `<superseded>` section, `<superseded>` wins.**

---

## 1. New decisions — D-26 … D-31

Sourced verbatim from `03-CONTEXT.md` `<superseded>` § "New decisions for run 2 —
user-confirmed 2026-08-02". Not re-derived, not extended.

| ID | Decision | Evidence / source |
|----|----------|-------------------|
| **D-26** | **Alpha-beta search replaces the Q-policy as the mover.** `_pick_move` becomes an alpha-beta search over a cycle-based evaluation; the Q-table is demoted from a 1.7M-entry action table to storage for **~60 evaluation weights** that RL tunes. Alpha-beta, **not MCTS** — MCTS misses shallow traps and barrier sealing *is* one; a trap closing in k thief moves needs depth ≥ 2k plies. `strategy.max_decision_ms` is ours to raise (test 100/200 ms early) | Ramanujan et al. ICAPS 2010. **Measured on our real engine: depth 5 with a useful eval, depth 8 with Manhattan.** ALG-COMPARISON's "11–12 plies" and its Bansal delta-uniform numbers are **UNVERIFIED** (its correction pass was cut off by an API limit) and must not be planned against |
| **D-27** | **STRAT-01 and STRAT-06 require a written defence, and that defence is a deliverable.** Under D-26 both are satisfied in substance but not in the literal shape the requirement text describes. A grader-facing document states the deviation plainly, carries the measured evidence, and shows what still ships. **Not optional, not a footnote** — the single largest grading risk this phase carries | `03-CONTEXT.md` `<superseded>` |
| **D-28** | **The GATE-4 bar stays at `min_win_rate_absolute = 0.55`.** Not lowered for run 2. It originates in `docs/PRD_rl_strategy.md` §8 (D-14), **not** `docs/PARAMETERS.md` (checked: 142 lines, zero matches), so it is ours to re-argue — but only *after* a second measurement, never because a run failed | `03-CONTEXT.md` `<superseded>`; postmortem "Open question" |
| **D-29** | **Everything lands before run 2; there is exactly one run.** 03-11…03-16 all land, the pre-flight assertions gate the launch, then a single overnight run. Run 1 cost a whole night to four defects computable at t=0 | `03-CONTEXT.md` `<superseded>` |
| **D-30** | **The pre-flight assertions are a hard gate on every future run.** Six checks computable before episode 1 (`TRAINING-METHODOLOGY.md` §F.3). **Run 1 failed four of these at t=0** | `TRAINING-METHODOLOGY.md` §F.3 |
| **D-31** | **The thief's safety rule is a measured free win and lands regardless of search.** A thief that only moves to cells outside the cop's closed neighbourhood `N[cop]` scored **296/300 = 0.987** over random starts vs the current BFS thief's 283/300 = 0.943, no training required. **Caveat recorded, not smoothed over:** the "provably unbeatable" claim did **not** fully reproduce — it still lost 3/20 with new barrier placement disabled, and that control was itself flawed (the scenarios carry pre-placed barriers). A real bounded gain, **not a solved thief** | `scratchpad/safe_thief.py`, real engine, full rules |

## 2. Run-1 decisions now superseded

From `<superseded>` § "Decisions overturned by measurement". Plans must not re-implement these.

| ID | Overturned because | Replaced by |
|----|--------------------|-------------|
| **D-04** absolute `(own, target)` positional core as a *generalisation* mechanism | cop **0.600** on trained starts vs **0.133** on unseen; only **5/20** eval starts cleared `min_visits`; top 1% of keys hold **53.2%** of 3,525,039 visits; median best-vs-second Q margin **0.00000** | Feature vector + linear weights (plan 03-16) |
| **D-06** bucketed turn phase | Puterman 1994 ch.4; Pardo et al. ICML 2018 | Exact `turns_remaining` (plan 03-13) — **replaces**, never alongside |
| **D-09** BFS distance as the *decision objective* | Barriers keep the board triangle-free ⇒ **cop-win ⟺ the thief's free component is a forest**. Cop number of an m×n grid is **2** (Neufeld & Nowakowski 1998) | Cycle-based evaluation (03-16/03-17). **BFS survives as tie-break and fallback only** |
| **D-12** heuristic barrier sub-policy maximising BFS distance to a fixed corner anchor | The corner-anchor rule has **no support anywhere in the literature**; barrier layout is invisible to the policy so the cop's ceiling is bounded by it (Finding 4.3) | Cycle-rank objective + edge/barrier-adjacent, degree-4-preferring candidate filter (plan 03-17) |
| **D-13** sparring mix `[0.30, 0.50, 0.20]` | **Never ran as configured** — empty `reference_impl_path` renormalised it to **0.375/0.625**. Failure mode: coevolutionary disengagement (Cartlidge & Bullock 2004) | PFSP `f(x)=x(1−x)` + permanent weak-opponent floor (plan 03-21) |
| **D-18** *(as labelled in `<superseded>`)* single γ for both roles | Thief usable value range **0.047** vs cop's 0.626 — a **13×** weaker signal, below the noise floor at α=0.15 | γ_cop = 0.99, γ_thief = 1.0 (plan 03-21) |

**Two label discrepancies, recorded rather than silently fixed — settle at plan-writing time:**

1. `<superseded>` overturns the **ID** `D-18` on the grounds "single γ for both roles", but
   `03-PLAN-OUTLINE.md`'s D-18 reads "ε/α/γ … are **engineering defaults in config, NOT
   PARAMETERS.md values**". These are different claims. **Read the overturn narrowly:** γ
   becomes per-role; D-18's numeric-sourcing discipline **stays in force** and every plan below
   obeys it.
2. **D-14** (the 0.55 bar), **D-15** (big overnight runs) and **D-16** (rule-42 curves) appear in
   neither the overturned table nor the "still binding" list. D-14 is explicitly reaffirmed by
   **D-28**; D-15 and D-16 are treated as still binding (rule 42 is a book requirement).

Still binding from run 1, unchanged: D-01, D-02, D-03, D-07, D-08, D-10, D-11, D-17, D-19,
D-20, D-21, D-22, D-23, D-24, D-25.

## 3. Correctness defects R1–R6 (code bugs, not tuning)

| ID | Defect | Landed by |
|----|--------|-----------|
| **R1** | All 300,000 episodes started from the identical board. Restart distribution μ must ⊇ the eval distribution d | plan **03-15** |
| **R2** | **The thief is never told it was caught** — `harness.py::_turn` only updates when the moving role IS the learner, and capture happens on the *cop's* turn. 300/300 captured episodes delivered exactly one update worth −0.01. **The worst defect in the phase** | plan **03-14** |
| **R3** | Single γ=0.95 — effective horizon 20 against a 35-turn task | plan **03-21** (config) |
| **R4** | No terminal-state marking; terminal values leak into live keys | plan **03-14** |
| **R5** | ε/α floors reached at episode 299,999 of 300,000. Floor **value** must be 0.10–0.15, not 0.05 | plan **03-21** (config) |
| **R6** | Eval pseudo-replication (true n=20, not 200) | ✅ **already landed, commit `ced26d5`** — plan **03-25** verifies only, no work |

**Withdrawn and not to be resurrected:** T4-followup-1 ("train longer") and T4-followup-2 ("raise
`min_visits`") are struck through in `docs/phases/phase-3/TODO.md` as **measured false**.

**Do not cite the ablation pilot.** 4 arms × 10,000 episodes ran and is **INCONCLUSIVE** — every
pairwise comparison insignificant (cop A-vs-C p=0.407, thief A-vs-D p=0.451). The case for R1–R6
rests on postmortem Findings 1–4, which are direct measurements.

---

## 4. Plans

**Namespace warning:** `docs/phases/phase-3/TODO.md` rows are also numbered `03-NN` and the
ranges overlap. Below, **"row NN"** means a TODO row and **"plan 03-NN"** means a plan file.
Row→plan mapping is in §6.

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|-----------|-------------|
| 03-11 | Graph primitives library — components, articulation points, cycle rank, Voronoi territory | 1 | none | D-26, D-09(superseded), QUAL-02 |
| 03-12 | Thief safety rule: never step into `N[cop]` | 1 | none | D-31, STRAT-02 |
| 03-13 | State + config surface: exact `turns_remaining` replaces `turn_bucket`; every new key declared once | 1 | none | D-06(superseded), D-18, QUAL-11 |
| 03-14 | R2 + R4: deliver the terminal transition whichever role moved; mark terminal states; PARAMETERS-sourced terminal rewards | 1 | none | R2, R4, STRAT-06 |
| 03-15 | R1: randomised episode start states, restart distribution μ ⊇ eval starts | 2 | 03-13, 03-14 | R1, STRAT-06 |
| 03-16 | Feature vector φ(s) + per-role linear evaluation `wᵀφ` (~60 weights) | 2 | 03-11, 03-13 | D-26, D-04(superseded), STRAT-01 |
| 03-17 | Cop barrier placement rewrite: cycle-rank objective + edge/barrier-adjacent degree-≥3 candidate filter | 3 | 03-11, 03-16 | D-12(superseded), STRAT-05 |
| 03-18 | Alpha-beta search core: iterative deepening, transposition table, wall-clock budget | 3 | 03-16 | D-26, STRAT-01, STRAT-07 |
| 03-19 | `SearchBrain` wiring: per-role movegen, registry + config class switch, guardrails | 4 | 03-12, 03-17, 03-18 | D-26, STRAT-01, STRAT-03, STRAT-05, STRAT-07 |
| 03-20 | Linear-weights learner + per-role weights persistence (the demoted "Q-table") | 4 | 03-14, 03-16, 03-18 | D-26, D-02, D-03, STRAT-01, STRAT-06 |
| 03-21 | Run-2 regime: PFSP `f(x)=x(1−x)` + weak-opponent floor; final per-role γ / ε / α / reward values | 5 | 03-15, 03-19, 03-20 | R3, R5, D-13(superseded), D-18, STRAT-06 |
| 03-22 | **D-27 deliverable** — grader-facing STRAT-01 / STRAT-06 deviation defence | 5 | 03-19, 03-20 | D-27, DOC-02, STRAT-01, STRAT-06 |
| 03-23 | Pre-flight gate: the six §F.3 assertions, hard-gating every run | 6 | 03-15, 03-21 | D-30, D-29, STRAT-06 |
| 03-24 | Phase triplet refresh + tracker reconciliation (roadmap task 03-97) | 6 | 03-21, 03-22 | DOC-01, CLAUDE.md triplet rule |
| 03-25 | **Run 2 + GATE-4 measurement** — human operator checkpoint, `autonomous: false` | 7 | 03-23, 03-24 | D-28, D-29, R6(verify), GATE-4, STRAT-06 |

---

## 5. Per-plan files and where the 150-line split falls

Every file below is **≤150 code lines** (blanks/comments excluded), enforced by the pre-commit
hook and CI. **Split files; never compress code to fit.** Test files obey the limit too.

> **⚠ Corrections found while writing the wave-1 plans — the plans are right, this section was
> wrong.** (1) The line counts quoted throughout §5 are **raw** lines; the gate counts **code**
> lines (blanks and `#` comments excluded), so the real headroom differs. Measured with the hook's
> own counter: `fallback.py` is **83** code lines, `harness.py` **132**, `strategy_config.py`
> **138**. (2) Consequently **03-13's "no split needed" is wrong** — 138 code lines + 15 new fields
> − 1 removed ≈ **164**, over the gate; plan 03-13 carries an explicit split contract moving
> `StrategyParams` to `src/pursuit/shared/strategy_schema.py`. (3) **R2 is symmetric** — see the
> R2 row in `03-CONTEXT.md` `<superseded>`; a cop learner is blind to SURVIVAL exactly as the thief
> is blind to CAPTURE. This widens 03-23's pre-flight check 1, which already reads "for both
> outcomes for both roles".
>
> **Line counts and the Table 17 sourcing were re-measured against the repo on 2026-08-03**, not
> taken on trust: `encoding.py` 123 ✓, `barriers.py` 124 ✓, `fallback.py` 99 ✓, `harness.py` 158 ✓,
> `sparring.py` 142 ✓, `loop.py` 158 ✓, phase triplet 113/152/93 ✓. Two paths were wrong in the
> first draft and are corrected above: `config_keys.py` is at `src/pursuit/`, and
> `strategy_config.py` at `src/pursuit/shared/` and is **169** lines, not 170.
> `docs/PARAMETERS.md` Table 17 confirmed verbatim — cop capture **20**, thief when captured **5**,
> cop when the thief survives **5**, thief survives **10**, all **fixed**, under the standing note
> that §1.3 makes the reward function translate directly from the scoring table.

**03-11 — Graph primitives.** New package `src/pursuit/strategy/graph/`. Three algorithms, three
files, because one file would be 210–280 lines: `components.py` (free-cell graph, the component
containing a cell, component size, per-cell degree within a component, **iterative** Hopcroft–Tarjan
articulation points — never recursive; ~90–120), `cycles.py` (cycle rank `E − V + 1`, per-cell
reduction value `d − 1`, `is_forest`; ~50–70), `territory.py` (two-source BFS Voronoi split →
cell-count difference and edge-count difference; ~70–90). Pure functions of `(GameState,
GameParams)`, no role knowledge, no module-level mutable state (D-03 — a shared *library* is
permitted, a shared *state object* is disqualification). Tests mirror one-to-one under
`tests/unit/strategy/graph/`.

**03-12 — Thief safety rule.** One new file `src/pursuit/strategy/safety.py` (~50–70): filter the
thief's legal moves against the cop's closed neighbourhood `N[cop]` (the cop's cell plus its legal
destinations), and **return the unfiltered legal list when the filter would empty it** — never an
empty candidate set. One edit to `fallback.py::_evade` (99 lines today, filter-then-rank keeps it
under). No split needed. Tests: `tests/unit/strategy/test_safety.py` plus a bounded head-to-head
regression at a CI-affordable n. The 0.987-vs-0.943 provenance **and** the D-31 caveat both go in
the module docstring — the caveat is not dropped because it is inconvenient.

**03-13 — State + config surface.** `encoding.py` (123 lines) *shrinks*: `turn_bucket` is deleted
and key field 5 becomes exact `turns_remaining = move_ceiling − turn_index`; `decode_state` returns
it. `src/pursuit/config_keys.py` (123) loses `TURN_BUCKET_FRACTIONS` and gains the run-2 enum
members; `src/pursuit/shared/strategy_config.py` (169 raw / under the code-line limit) loses one
field and gains the new ones;
both `config/{police,thief}/strategy.json` are edited. **This plan is one of only three config
owners** (see §7) — every new numeric knob the whole block needs is declared *here, once*, so no
later plan touches the config files in parallel. Net deletion overall; no split needed. **The key
format change invalidates every run-1 key — no table was ever promoted, so write no migration.**

**03-14 — R2 + R4, the terminal signal.** `training/harness.py` is at 158 raw lines, so the reward
function is extracted to a new `training/rewards.py` (~50) — **that is this plan's 150-line split.**
`harness.py::_turn` must deliver the terminal transition to the learner **whichever role's move
caused it**; `qlearning.py::update` gains a `terminal: bool` so the final update bootstraps from 0
(R4). **Terminal rewards are PARAMETERS.md Table 17 values, not engineering defaults** — cop 20 on
capture / 5 on survival, thief 5 on capture / 10 on survival, already loaded into
`GameParams.score_*`, and Table 17's own note records that §1.3 says the reward function
"translates directly from the scoring table". So the thief's "capture penalty" is `+5 vs +10`, a
*relative* penalty with zero invented numbers — **not** the postmortem's illustrative −1.0.
Tests: a captured thief receives exactly one terminal update carrying its capture score, and
`terminal_updates[role] == episodes`. **Tests must not assert on key format** — plan 03-13 is
changing it in the same wave.

**03-15 — R1, randomised starts.** New `training/starts.py` (~90–120): uniform over legal,
distinct, non-adjacent joint (cop, thief) placements; randomised remaining barrier quota; the
thief's reverse curriculum over `turns_remaining` (Florensa et al. CoRL 2017). Exposes
`distinct_start_count()` and `covers(eval_starts)` so 03-23 asserts against this module rather than
re-deriving μ ⊇ d (Kakade & Langford ICML 2002). `harness.py::run_episode` takes the start from the
sampler instead of `engine.make_state`; `loop.py` builds it once from config +
`artifacts/eval_scenarios.json`. **Split trigger:** if the sampler plus the curriculum schedule
exceeds 150, split `training/curriculum.py` out — do not compress.

**03-16 — Features + linear evaluation.** `src/pursuit/strategy/features.py` (~90–120): the
12-feature vector of ALG-COMPARISON §6 (f0 bias … f11 min BFS distance to edge/corner), every
distance BFS on the barrier-aware grid, every feature scaled to ~[0,1]. f9 is exact
`turns_remaining / move_ceiling` (needs 03-13); f2/f3/f6/f7 come from 03-11.
`src/pursuit/strategy/evaluate.py` (~50–70): `wᵀφ` with per-role weight vectors — **the two roles
aggregate differently and this is not cosmetic**: the cop sums, the thief takes the `min` over the
line (a reach-avoid worst-case margin), and "thief survived to the deadline" scores `+INF` so
alpha-beta can prune proven-safe subtrees. **Split trigger:** if `features.py` exceeds 150, move the
four graph-derived features to `features_graph.py`. Sizing that motivates the whole change: 12
features × 5 actions = **~60 weights** against 1.7M table entries — ~170,000 updates per weight
instead of ~6 visits per key.

**03-17 — Cop barrier placement rewrite.** `barrier_candidates.py` (~60–80): candidates must be
**in the thief's current free component ∧ touching the board edge or an existing barrier ∧ degree
≥ 3 in that component** — typically 6–12 cells, which is what makes alpha-beta affordable. The
edge/barrier-adjacency rule is Guibas et al. 1999: a barrier dropped in open space creates a hole
the thief orbits, i.e. a *new cycle*, the exact thing the objective destroys. `barriers.py` (124)
is **rewritten**: `_escape_anchor` and its `_gain` are deleted; the objective becomes primary =
cycle rank of the **thief's component** (prefer degree-4 cells — `d−1 = 3` units of progress vs 1
for degree-2), secondary = thief component size, tertiary = Voronoi share, tiebreak = BFS distance
cop→thief. **Budget invariant, asserted by test: decycle the thief's component, never the board** —
the decycling number of the 7×7 grid is 13 against a quota of 14, but 13 placements + ~32 chase
rounds = 45 > the 35-turn limit, so a decycle-the-board policy is provably a loss. **Split
trigger:** the acyclic-component endgame chase moves to `endgame.py` (~40–60) if `barriers.py`
would exceed 150.

**03-18 — Alpha-beta search core.** `src/pursuit/strategy/search.py` (~100–140): iterative-deepening
alpha-beta; transposition table keyed on `(cop, thief, barrier set, side to move, turns_remaining)`;
wall-clock budget from `strategy.max_decision_ms`; deterministic move ordering by fixed cell order
and deterministic tiebreak; and it **always returns the best move found so far when the budget
expires — it never raises**. **Split trigger:** if move ordering plus the TT push past 150, split
`transposition.py` (~40). **Plan against the measured depth, not the claimed one:** depth 5 with a
useful eval, depth 8 with Manhattan, measured on our engine. ALG-COMPARISON's 11–12-ply figure and
its Bansal delta-uniform numbers are **UNVERIFIED** and must not appear as a target anywhere.
Depth caps and the raised `max_decision_ms` (D-26: test 100/200 ms early) are **engineering
defaults declared by 03-13**, and the final value must come from a measurement on this machine.

**03-19 — `SearchBrain` wiring.** `movegen.py` (~50–70): per-role successor generation — the cop
expands (move × pruned barrier candidates from 03-17), the thief expands safety-filtered moves from
03-12, keeping branching honest (cop ~5×(6–12), thief ≤5). `searchbrain.py` (~80–110): the
`BrainBase` subclass; `_pick_move` runs the search and `_decide_move` attaches **the barrier the
same search chose**, so declared == applied (rules 16/22, AI-SPEC E9). `MoveSource` gains `SEARCH`
and the provenance guardrail widens to `{qtable, fallback, heuristic, search}`. Deadline-abort
guardrail returns the BFS-greedy move with `guard=deadline_abort`. Registry entry plus the
`police_class`/`thief_class` value switch — **the second config owner, two string values only.**
`HeuristicBrain` stays the baseline arm untouched (STRAT-03). **`scripts/check_no_llm_in_strategy.py`
must still pass over every new module — alpha-beta is an algorithm and STRAT-07 stays green.**

**03-20 — Linear-weights learner.** `linear_q.py` (~50–70): semi-gradient update `w += α·δ·φ(s)`,
with per-weight update counts replacing per-key visit counts. **On-policy (Expected SARSA) for the
thief** — Q-learning's `max` assumes a cooperative cop, which is maximally wrong for a safety
objective, and off-policy + linear FA + bootstrapping is the deadly triad (S&B §11.3); the cop's
rule is chosen in the plan **with its citation**. `weights.py` (~50–70): per-role JSON weights file
(D-02 JSON not pickle, D-03 one file per role), the same params fingerprint as the Q-table
(AI-SPEC E12), Windows-safe `.prev` rotation (D-24). Weights initialise from the existing BFS
heuristic as a potential Φ (Ng, Harada & Russell ICML 1999 Thm 1; Wiewiora JAIR 2003 — PBRS ≡
Q-initialisation), so training starts from today's behaviour and can only improve. Third and last
plan to touch `harness.py::_update_learner`, which switches to the feature-vector contract.

**03-21 — Run-2 regime.** `training/sparring.py` (142 lines): PFSP sampling `f(x) = x(1−x)`
replaces the fixed-mix renormalisation that silently produced 0.375/0.625, plus a **permanent
weak-opponent floor in every pool** (≥1 scripted weak + 1 random-walk — Cartlidge & Bullock 2004
"reduce virulence"; Gleave et al. ICLR 2020). **Split trigger:** `training/pfsp.py` (~50) if
`sparring.py` would exceed 150. Config, both role files — **the third and final config owner**:
γ cop **0.99** / thief **1.0** (R3); ε floor *value* 0.10–0.15 not 0.05 and the decay length set so
the floor is reached at **≤15% of that role's episodes** (D-30 check 3 — this also satisfies the
postmortem's "~60%, not 100%", since ≤15% is the stricter of the two and leaves the whole
consolidation phase intact); α likewise; `episodes` set as a **weight-tuning** budget, not a
table-filling one (D-26). **Number that exists nowhere and must not be invented:** if the
pre-flight Δ-ratio check (`Δ_cop/Δ_thief > 3`) or Jones' `[−10, +10]` target band cannot both be
satisfied, the only sourced remedy is a **single scale divisor applied identically to both roles**,
which preserves the PARAMETERS-sourced 20/5/5/10 ratio. If no common divisor satisfies both, the
plan **stops and asks** rather than picking a value.

**03-22 — D-27, the deviation defence.** Docs only, no code, its own plan because it is the
largest grading risk in the phase and an undocumented deviation from a book requirement reads as a
missed requirement. `docs/PRD_rl_strategy.md` → v2.00 (Segal versioning) describing
search-over-learned-evaluation. New `docs/phases/phase-3/STRAT-01-06-DEVIATION.md`: states plainly
that STRAT-01 ("move selection uses a trained tabular Q-learning policy via `BrainBase._pick_move`")
and STRAT-06 ("a trained Q-table ships") are met **in substance but not in literal shape**; carries
the measured evidence (top 1% of cop keys hold 53.2% of 3,525,039 visits; 5/20 eval starts above
`min_visits`; median best-vs-second margin 0.00000; cop 0.600 trained vs 0.133 unseen); and shows
what **still ships** — a trained per-role weights file reached from `_pick_move`, learning curves
from both runs, and run-1's curves as the historical record. README rule-42 section updated. Every
claim must be checkable against code that has already landed, which is why this waits for wave 4.

**03-23 — Pre-flight gate.** `training/preflight.py` (~100–130) plus `training/probes.py` (~60–90)
— **the split falls between the five config/sampler assertions and §F.3's sixth item**, the four
Jones probe environments (constant reward; random observations with predictable rewards; two
timesteps; action-dependent rewards), which need their own tiny environments. The six, from
`TRAINING-METHODOLOGY.md` §F.3 verbatim (**note:** D-30 says "six" and then names five — the sixth
is §F.3's probe environments, and §F.3 is what D-30 cites): (1) terminal reward defined and
non-zero for both outcomes for both roles; (2) discounted terminal-value spread Δ per role, failing
if `Δ_role < 0.1` or `Δ_cop/Δ_thief > 3`; (3) `epsilon_floor_episode ≤ 0.15 × episodes`, same for α;
(4) sampler yields ≥200 distinct starts **and contains every eval start**; (5) every opponent pool
contains at least one weak opponent; (6) the probes recover their known-correct values. Wired into
`training/loop.py::main` as a **hard gate that exits non-zero before episode 1**. **Every assertion
must be shown to fire** against a deliberately-broken config — run-1's own config is the natural
fixture for four of the six, and an assertion that cannot fire is worthless.

**03-24 — Triplet refresh.** `docs/phases/phase-3/{PRD,PLAN,TODO}.md` (113 / 152 / 93 lines)
updated to the run-2 design, with rows 03-11…03-16 mapped to the plan IDs in §6; the withdrawn
T4-followup-1/2 rows **stay struck through**. `.planning/ROADMAP.md`'s Phase 3 plan list is
refreshed (it still names the four stale placeholders 03-01…03-04). Root `docs/TODO.md` kept
consistent. **No `[x]` is ticked here** — that is `/gsd:verify-work 3` (row 03-99), and only after
the run.

**03-25 — Run 2 + GATE-4.** `autonomous: false`. Implementation and checkpoints never share a
plan, so this plan carries no code. It is the exact analogue of 03-10's Task 4. Operator sequence,
with the three run-1 operator lessons (rows op-1/2/3) repeated because they are proven:

```
powercfg /change standby-timeout-ac 0                       # op-2: machine-level sleep policy
# op-3: add %LOCALAPPDATA%\pursuit\training to Defender exclusions
uv run python -m training.preflight                          # D-30 gate — MUST exit 0
uv run python -m training.loop 2>&1 | tee run.log            # op-1: never click into the console
uv run python -m training.evaluate --scenarios artifacts/eval_scenarios.json \
    --out artifacts/eval/<run_id>.csv --full --assert-gate
```

GATE-4 is measured at the **unchanged** `min_win_rate_absolute = 0.55` (D-28). R6 is verified as
already landed in `ced26d5` — a check, not work. **Exactly one run (D-29).** If GATE-4 misses
again, the miss becomes evidence *about the bar*; re-arguing 0.55 is a separate decision this plan
does not take.

---

## 6. TODO row → plan mapping

| `docs/phases/phase-3/TODO.md` row | Plan(s) |
|---|---|
| row 03-11 thief safety rule | plan 03-12 |
| row 03-12 pre-flight assertions | plan 03-23 |
| row 03-13 cycle evaluation + alpha-beta, both roles | plans 03-11, 03-16, 03-18, 03-19 |
| row 03-14 barrier placement rewrite | plan 03-17 |
| row 03-15 run-2 training config | plans 03-20, 03-21 |
| row 03-16 `turns_remaining` | plan 03-13 |
| row 03-97 phase triplet | plan 03-24 |
| R1 / R2+R4 / R3+R5 / R6 | plans 03-15 / 03-14 / 03-21 / 03-25 (verify) |
| D-27 | plan 03-22 |
| GATE-4 (§10.4) | plan 03-25 |

## 7. Standing constraints the executor must not re-derive

- **File ownership.** `config/{police,thief}/strategy.json` has **exactly three owners, in
  different waves**: 03-13 (declare every key), 03-19 (two class-name values), 03-21 (final numeric
  values). No other plan edits them. `training/harness.py` is touched by 03-14 (w1), 03-15 (w2),
  03-20 (w4) — sequential by wave, never parallel.
- **Numeric sourcing (D-18, project rule 1).** Terminal rewards 20/5/5/10 are **PARAMETERS.md
  Table 17 fixed values** already in `GameParams`. Everything else new — search depth cap,
  `max_decision_ms`, feature scale divisor, ε/α floors, PFSP parameters, `min_distinct_starts`,
  objective weights — is an **engineering default**, declared in config and labelled as such.
- **Sourced-but-flagged.** `TRAINING-METHODOLOGY.md`'s own "No source found" section records that
  the thief-vs-cop ε-floor multiplier is an *inference*, and that the exact AlphaStar PFSP exponent
  came from secondary sources only. Plans cite these as such, never as measured results.
- **Every plan inherits the standing gates** and does not restate them: `ruff check` → 0;
  `uv run pytest --cov` ≥ 85% (currently 96.43%, 427 tests); ≤150 code lines per file including
  tests; `uv` only, never `pip` or bare `python`; zero hardcoded values in `src/`; zero secrets;
  TDD (tests before or alongside code); no shared runtime state between cop and thief — a shared
  library is fine, a shared state object is disqualification;
  `scripts/check_no_llm_in_strategy.py` stays green.
- **Plan size (house style).** Plans state **contracts and constraints** — signatures, invariants,
  file boundaries, acceptance criteria. They **never re-write the implementation in prose.** Run-1's
  Phase 3 plans totalled ~2.2k lines against Phase 2's ~9.7k; hold that line or beat it. Target
  ~140–170 lines per plan.
- **Cite decision IDs inside `must_haves`.** The downstream decision-coverage gate scans the
  `must_haves` block for `D-NN` tokens and counts nothing else — putting them only in task bodies
  fails the gate.
