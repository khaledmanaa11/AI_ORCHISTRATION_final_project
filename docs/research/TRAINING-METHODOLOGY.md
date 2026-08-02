# Training Methodology — Sourced Research

> Status: **COMPLETE**. Sourced research for the RL training redesign after the failed
> 300,000-episode run. Every recommendation carries a citation; unsourced items are listed
> in the final "No source found" section rather than asserted.
>
> Scope: tabular Q-learning, 7x7 grid, alternating moves, cop (pursuer, terminal capture)
> vs thief (evader, survive-to-deadline). Two separate processes, each graded on
> **absolute strength in its own role** in a league against other universities' agents.
> **The thief is the priority.**

## The four observed failures this document must address

| ID | Failure |
|---|---|
| **F1** | All 300k episodes started from one identical board state. 0.90 win rate on it, 0.133 on unseen eval starts (0.600 on seen ones). Only 5/20 eval starts ever entered the table. |
| **F2** | Thief reward degenerate: no terminal signal on capture at all; gamma=0.95 over 35 turns made survive-to-end (+0.0098) only 0.047 above captured-on-move-4 (-0.0371); ~13x weaker than the cop's signal. |
| **F3** | Epsilon and alpha hit their floors at episode 299,999/300,000 — zero consolidation phase. |
| **F4** | Self-play starved the thief: 0.375 heuristic / 0.625 past-self mix against monotonically strengthening past-self cops; thief win rate declined 0.106 -> 0.016. |

### Feasibility under our constraints

Everything recommended below is pure-Python arithmetic over dicts and counters. Nothing here
requires numpy, and certainly not a deep-learning framework:

- start-state sampling, δ-uniform / PFSP opponent sampling, win-rate-targeted mixtures, and
  every §F diagnostic are `random`, `collections.Counter` and `statistics` only;
- the one place numpy would help is the pairwise win-rate matrix / Elo round-robin (§F.2),
  and even that is a ≤ 10×10 list-of-lists;
- the changes decompose cleanly into small modules well under the 150-code-line limit —
  a start-state sampler, an opponent-pool sampler, a schedule module, a shaping/potential
  module, and a diagnostics recorder — each independently unit-testable with mocked
  opponents, which is what the ≥ 85 % coverage gate needs.

---

## A. Start-state distribution

### A.1 The textbook requirement: "exploring starts"

Sutton & Barto define **exploring starts** in *Reinforcement Learning: An Introduction*,
2nd ed., **§5.3 "Monte Carlo Control"**; the assumption is then explicitly removed in
**§5.4 "Monte Carlo Control without Exploring Starts"**.
(Book PDF: <http://incompleteideas.net/book/RLbook2020.pdf>; chapter-5 summary with the
same section numbering: <https://lcalem.github.io/blog/2018/10/22/sutton-chap05-montecarlo>.)

What it *requires*: episodes begin in a **state–action pair**, and **every** state–action
pair has nonzero probability of being selected as the start — each pair must be selected as
a start infinitely often in the limit
(<https://hughiemak.github.io/2021/01/14/monte-carlo-methods.html>,
<https://yashbonde.github.io/blogs/bartosutton/chap5.html>).

Why: with a deterministic (or near-deterministic, low-epsilon) policy you only ever observe
returns for **one** action per state, so the other actions' values are never estimated and
cannot be compared. Sutton & Barto's own caveat is that exploring starts is generally
**unusable when learning from real interaction** because you cannot teleport into arbitrary
states — which is exactly the escape hatch a *simulator* gives us. We have a simulator, so
the assumption is cheap to satisfy and there is no excuse for a singleton start.

> **Direct read on F1:** our run violated the exploring-starts assumption in its strongest
> possible form — a *singleton* start state. The 0.90-vs-0.133 gap is the textbook symptom,
> not a mystery.

Convergence of Monte Carlo Exploring Starts is still a partly open problem — see
[Chen, "On the Convergence of the Monte Carlo Exploring Starts Algorithm for RL" (arXiv 2002.03585)](https://arxiv.org/pdf/2002.03585)
and [Liu, "On the convergence of reinforcement learning with Monte Carlo Exploring Starts", *Automatica* 2021 (arXiv 2007.10916)](https://arxiv.org/pdf/2007.10916).
This does not weaken the practical point; it strengthens it (even with exploring starts
convergence is delicate; without them there is no argument at all).

### A.2 Standard terminology for "trained on one start, evaluated on others"

The modern framing is **zero-shot policy transfer (ZSPT)** across a **Contextual MDP
(CMDP)**: a family of MDPs indexed by a context `c` (here, the start state), with a
*training context set* and a disjoint *testing context set*. Training on a single context is
called a **singleton environment**; the train/test performance difference is the
**generalisation gap**. Canonical reference:

- [Kirk, Zhang, Grefenstette & Rocktäschel, "A Survey of Zero-shot Generalisation in Deep Reinforcement Learning", *JAIR* 76:201–264 (2023), arXiv 2111.09794](https://arxiv.org/abs/2111.09794)
  — the JAIR version explicitly "added formal definitions of ZSPT and related concepts".
  Use its vocabulary in the report: *singleton environment*, *CMDP*, *context set*,
  *generalisation gap*.

Formal RL-theory ancestor of the fix — **train from a broader restart distribution than the
one you are evaluated on**:

- [Kakade & Langford, "Approximately Optimal Approximate Reinforcement Learning", *ICML* 2002, pp. 267–274](https://dl.acm.org/doi/10.5555/645531.656005)
  (PDF: <http://ttic.uchicago.edu/~sham/papers/rl/aoarl.pdf>) — introduces the **restart
  distribution μ**, deliberately more spread out than the evaluation start distribution `d`,
  and bounds the loss via a **distribution-mismatch coefficient**. This is the theoretical
  licence for "randomise the training starts even though the league will use fixed ones."

Empirical evidence that a *singleton* start / few contexts causes memorisation:

- [Cobbe, Klimov, Hesse, Kim & Schulman, "Quantifying Generalization in Reinforcement Learning", *ICML* 2019](http://proceedings.mlr.press/v97/cobbe19a/cobbe19a.pdf)
  — training sets from **100 to 100,000 levels**; generalisation improves monotonically with
  the number of distinct training contexts, and small training sets are memorised.
- [Cobbe, Hesse, Hilton & Schulman, "Leveraging Procedural Generation to Benchmark Reinforcement Learning" (Procgen), *ICML* 2020](https://cdn.openai.com/procgen.pdf)
  — the benchmark's *generalization* track fixes **200 levels (easy) / 1000 levels (hard)**
  as the standard training-context budget. Useful as a defensible order-of-magnitude anchor:
  hundreds-to-thousands of distinct starts, not one.
- [Kenton, Filos, Evans & Gal, "Generalizing from a few environments in safety-critical reinforcement learning" (2019), arXiv 1907.01475](https://arxiv.org/abs/1907.01475)
  — the framing "perfect on training environments, dangerous on unseen test environments".
  *No exact number-of-environments-vs-failure-rate table extracted from the abstract; the
  numbers are in the full PDF, not verified here.*
- [Kumar, Zhang et al. / Nikishin-style "The Role of Diverse Replay for Generalisation in RL" (arXiv 2306.05727)](https://arxiv.org/pdf/2306.05727)
  — collecting/replaying more diverse data (including more diverse starts) improves
  generalisation. *Author list not verified.*

### A.3 Practical recipes for randomising starts in a self-play grid game

Ordered from cheapest to most powerful. All are compatible with tabular Q-learning and cost
essentially nothing in CPU.

1. **Uniform random legal start (the "exploring starts" baseline).** Sample cop and thief
   cells uniformly from legal, distinct, non-adjacent cells each episode. This is the direct
   implementation of Sutton & Barto §5.3 in a simulator. Must be the default.
2. **Exploring starts over state–action pairs, not just states.** §5.3 requires the *pair*.
   Cheap tabular version: with some probability force the first action uniformly at random
   regardless of epsilon. This is what makes the *action* comparison well-posed.
3. **Include the league's fixed start(s) in the training mixture.** Kakade & Langford's μ
   should *cover* the evaluation distribution `d`; a mixture such as
   `μ = w·uniform + (1−w)·d` keeps the mismatch coefficient bounded while still covering.
4. **Reverse / backward curriculum over start states.** [Florensa, Held, Wulfmeier, Zhang & Abbeel, "Reverse Curriculum Generation for Reinforcement Learning", *CoRL* 2017, arXiv 1707.05300](https://arxiv.org/abs/1707.05300)
   — automatically generate a curriculum of **start states** that adapts to the agent's
   performance, expanding outward from states where the task is already solvable. Directly
   applicable per role: for the **thief**, "already solvable" = start states from which it
   survives; expand outward from those. Their motivation is exactly ours: fixed initial
   configurations plus sparse reward require prohibitive exploration.
5. **Exploration-driven start coverage.** Already in hand and directly on-point:
   [Jiang, Grefenstette et al. (eds.), "On the Importance of Exploration for Generalization in RL", *NeurIPS* 2023](https://proceedings.neurips.cc/paper_files/paper/2023/file/2a4310c4fd24bd336aa2f64f93cb5d39-Paper-Conference.pdf)
   and [Explore-Go, arXiv 2406.08069](https://arxiv.org/pdf/2406.08069) — both treat train/test
   MDPs that differ **only in initial-state distribution**. Explore-Go's mechanism (a pure
   exploration prefix at the start of each episode, then learn from the state you land in)
   is a *drop-in* start-state randomiser that needs no knowledge of the legal-start set: run
   `k ~ U{0..K}` random joint moves before the episode "counts".

### A.4 Per-role note

The roles need **different** start coverage, because their state distributions differ:

- **Cop.** Needs coverage of the *pursuit geometry*: relative displacement (dx, dy),
  barrier configurations, remaining barrier quota, remaining turns. Uniform joint start plus
  randomised remaining-quota is the cheap version.
- **Thief (priority).** Needs coverage of *danger levels* — including starts where it is
  already 1–2 steps from capture and starts deep in open space. Under a singleton start the
  thief only ever sees one danger level, which is the mechanism behind F1 for the evader.
  Florensa's reverse curriculum applied to the thief means: start it *near* the deadline
  (few turns left, easy survival), then push the start earlier — a *forward-in-difficulty,
  backward-in-time* curriculum that gives it a non-zero win rate from episode 1 (also
  addresses F4).

---

## B. Reward design

### B.1 Potential-based reward shaping — the guarantee, verbatim

Primary source (read directly, not via summary):
**Ng, A. Y., Harada, D. & Russell, S., "Policy invariance under reward transformations:
Theory and application to reward shaping", *ICML* 1999**
(PDF: <https://people.eecs.berkeley.edu/~pabbeel/cs287-fa09/readings/NgHaradaRussell-shaping-ICML1999.pdf>).

**Theorem 1 (quoted).** "Let any `S, A, γ`, and any shaping reward function
`F : S × A × S ↦ ℝ` be given. We say `F` is a **potential-based** shaping function if there
exists a real-valued function `Φ : S ↦ ℝ` such that for all `s ∈ S − {s₀}, a ∈ A, s′ ∈ S`,

    F(s, a, s′) = γ Φ(s′) − Φ(s)                                     (2)

(where `S − {s₀} = S` if `γ < 1`). Then, that `F` is a potential-based shaping function is a
**necessary and sufficient** condition to guarantee consistency with the optimal policy
(when learning from `M′ = (S,A,T,γ,R+F)` rather than from `M = (S,A,T,γ,R)`)":

- *(Sufficiency)* every optimal policy in `M′` is optimal in `M` and vice versa;
- *(Necessity)* if `F` is **not** potential-based, there exist a proper `T` and an `R` such
  that **no** optimal policy in `M′` is optimal in `M`.

**Corollary 2 (quoted).** "Suppose further that `Φ(s₀) = 0` if `γ = 1`. Then for all
`s ∈ S, a ∈ A`, `Q*_{M′}(s,a) = Q*_M(s,a) − Φ(s)` and `V*_{M′}(s) = V*_M(s) − Φ(s)`."
→ **the potential of the terminal/absorbing state must be 0.** If it is not, the telescoping
sum does not cancel at the episode boundary and you have silently changed the task.

**Remark 1 (Robustness and learning)** — quoted: potential-based shaping is *robust* for
**near**-optimal policies too: if `|V^π_{M′}(s) − V*_{M′}(s)| < ε` then
`|V^π_M(s) − V*_M(s)| < ε`. This matters for us: we will never be exactly optimal, and the
guarantee still holds approximately.

**Remark 2 (All policies optimal under Φ)** — quoted: if the whole reward *is*
`γΦ(s′) − Φ(s)`, then **any** policy is optimal. Corollary for us: shaping alone can never
teach the task; it only reallocates credit. The real payoff signal still has to be there.

**Ng et al.'s own grid-world experiments** (§4, same paper) — directly comparable to our
7×7 board:
- 10×10 shortest-path grid, start and goal in opposite corners, −1 per step, no discounting,
  4 compass actions, 80 % intended / 20 % random. Learner: **Sarsa, 0.10-greedy, learning
  rate 0.02**, results averaged over **40 independent runs**.
- Potential used: `Φ₀(s) = −MANHATTAN(s, GOAL)/0.8` (a *negative distance-to-goal* potential
  derived from "0.8 steps of progress per timestep"). Both `Φ₀` and even `0.5·Φ₀`
  "significantly helped speed up learning"; on a 50×50 grid, unshaped learning "is clearly
  losing hopelessly" while the shaped curves are so low they are barely visible.
- A second experiment used **subgoal-based potentials** on a 5×5 grid with 5 ordered flags,
  with `Φ₀(s) = −((5 − n_s − 0.5)/5)·t` where `n_s` = number of subgoals achieved.

**Does it apply to us? Yes, and this is the correct tool for both roles.**
- **Cop:** `Φ_cop(s) = −c · d(cop, thief)` (negative shortest-path distance on the barriered
  grid, times a scale `c`) is the exact analogue of Ng et al.'s `Φ₀`. Guaranteed not to
  change the optimal policy; guaranteed to densify the currently-sparse capture signal.
- **Thief:** the mirror `Φ_thief(s) = +c · d(cop, thief)` — but see B.3 below: for a
  survive-to-deadline objective the more informative potential is a function of *turns
  survived* / *turns remaining*, not distance alone, because the thief's real objective is
  temporal.
- **Both:** `Φ(terminal) = 0` is mandatory (Corollary 2). Getting this wrong is a second,
  independent version of failure **F2**.

Related result worth one line in the report:
[Wiewiora, "Potential-Based Shaping and Q-Value Initialization are Equivalent", *JAIR* 19 (2003)](https://cseweb.ucsd.edu//~ewiewior/03potential.pdf)
— initialising `Q(s,a) = Φ(s)` in a tabular learner is *equivalent* to potential-based
shaping with that `Φ`. For a **tabular** agent like ours this is the cheaper implementation:
**optimistic/heuristic table initialisation instead of a shaping term in the update**, same
guarantee, no extra code in the hot loop.

### B.2 Terminal-state handling in Q-learning — the exact target

The correct tabular Q-learning target is

    non-terminal s′:  target = r + γ · max_{a′} Q(s′, a′)
    terminal     s′:  target = r                      (no bootstrap term at all)

equivalently `target = r + γ·(1 − 𝟙[s′ terminal])·max_{a′}Q(s′,a′)`
(<https://d2l.ai/chapter_reinforcement-learning/qlearning.html>).

What breaks when a terminal state is not marked, which is precisely failure **F2**:

1. **The terminal reward is never delivered.** If the terminal transition is not generated
   for the losing side at all — our thief's case — that side's Q-table contains *no*
   information that capture is bad. Its policy is then shaped only by the step reward, which
   in our case was a uniform −0.01: a *constant* over all actions, i.e. **no gradient at
   all**. The thief was, in effect, learning from a reward function under which every policy
   is optimal (cf. Ng et al. Remark 2).
2. **Bootstrapping past the end.** If instead the transition is delivered but `done` is not
   honoured, the agent bootstraps `max Q` from a state that does not exist, inflating values
   and letting them leak backwards indefinitely.
3. **Deadline ≠ terminal.** Our 35-turn limit is a **genuine part of the environment**, not
   a training convenience. [Pardo, Tavakoli, Levdik & Kormushev, "Time Limits in Reinforcement Learning", *ICML* 2018, arXiv 1712.00378](https://arxiv.org/abs/1712.00378)
   splits this in two: **time-limited tasks** — where the agent must maximise performance
   within a fixed period — require that **remaining time is part of the state**, or the
   Markov property is violated and you get state aliasing; **time-unlimited tasks** should
   bootstrap from the cut-off state (*partial-episode bootstrapping*). Treating a time-limit
   termination as a true terminal state "causes state aliasing and invalidates experience
   replay, resulting in suboptimal policies and training instability".
   **We are squarely in case (i) for the thief**: surviving to turn 35 *is* the win
   condition. → **`turns_remaining` (or `turn_index`) must be part of the state key** for at
   least the thief, and the turn-35 transition must be delivered as a real terminal with the
   win reward. This is both a fix for F2 and a state-representation requirement.
   Gymnasium's `terminated` vs `truncated` split exists for exactly this distinction.

### B.3 Rewarding "survive N turns" without the discount eating the bonus

The arithmetic of failure **F2** is the general problem: with `γ = 0.95`, a terminal `+1` at
`t = 35` is worth `0.95³⁵ ≈ 0.166`; the same `+1` at `t = 4` is worth `0.95⁴ ≈ 0.815`. A
survival objective *inverts* the usual convention — the good outcome is the **latest**
one — so discounting works directly **against** the objective. Three sourced remedies:

1. **Use `γ = 1` (or ≈1) for the finite-horizon episodic task.** Sutton & Barto, §3.4:
   for **episodic** tasks the return is a finite sum and `γ = 1` is admissible; discounting
   is needed for *continuing* tasks to keep the sum finite. With a hard 35-turn deadline the
   return is bounded regardless. This single change removes the `0.95³⁵` attenuation. See
   §C below for the full argument and citations.
2. **Reward per surviving step instead of (only) at the deadline.** A `+r_step` for each
   turn survived makes the return monotone in survival length under *any* γ, so it is
   discount-robust: surviving `k` turns yields `r_step·(1−γ^k)/(1−γ)`, strictly increasing
   in `k`. This is the "reward the objective, densely" form. Caveat from Ng et al.: an
   arbitrary per-step bonus is *not* potential-based, so it can change the optimal policy —
   but here it does not conflict, because "more steps survived" **is** the objective; the
   risk is only that it competes with the terminal win bonus, so keep
   `sum of step rewards < win bonus`.
3. **Treat it as a reach-avoid / safety objective, which has its own Bellman backup.**
   [Fisac, Lygeros, Tomlin et al., "Bridging Hamilton-Jacobi Safety Analysis and Reinforcement Learning", *ICRA* 2019](https://ieeexplore.ieee.org/document/8794107)
   and [Hsu, Rubies-Royo, Tomlin & Fisac, "Safety and Liveness Guarantees through Reach-Avoid Reinforcement Learning", *RSS* 2021, arXiv 2112.12288](https://arxiv.org/abs/2112.12288)
   show that "never enter the failure set before time T" is **not** a sum-of-rewards
   objective at all — it is a min/max over the trajectory — and they use a **discounted
   safety Bellman equation with γ → 1** (annealing γ upward during training) precisely
   because standard discounting distorts safety values. *This is the strongest published
   justification that the evader's discount should differ from the pursuer's.*
   → **Recommendation: γ_thief ≥ γ_cop, with γ_thief = 1.0.**

### B.4 Symmetric vs asymmetric rewards in zero-sum two-player games

- **The formal object is a zero-sum Markov game, not two independent MDPs.**
  [Littman, "Markov games as a framework for multi-agent reinforcement learning", *ICML* 1994](https://www.cs.duke.edu/courses/spring07/cps296.3/littman94markov.pdf)
  defines the two-player zero-sum Markov game and **minimax-Q**; by construction
  `R_thief = −R_cop` and one table suffices. If you *do* use two separate tables with two
  separate reward functions, you have left the zero-sum formalism and each agent is solving
  its own MDP against a non-stationary opponent — which is fine, and is what our two-process
  architecture forces, but it means **there is no theorem forcing the two reward scales to
  match**, and each may be tuned for its own role's learnability.
- **Asymmetric games legitimately get asymmetric rewards.** The pursuit-evasion literature
  routinely gives the evader a different (often longer-horizon, survival-shaped) reward than
  the pursuer; e.g.
  [Wang et al., "Emergent behaviors in multiagent pursuit-evasion games within a bounded 2D grid world", *Scientific Reports* (2025)](https://www.nature.com/articles/s41598-025-15057-x)
  reports pursuers reaching a 99.9 % success rate over 1,000 randomised trials in a bounded
  2D grid, with role-specific reward functions. *Author list not verified beyond the title.*

### B.5 Should the reward come from the true payoff matrix (20/5/5/10) or be hand-tuned?

Our governing document says the reward should translate directly from the scoring table
(**capture → cop 20, thief 5; survival → cop 5, thief 10**); the implementation instead used
hand-tuned symmetric values (capture 1.0, survival 1.0, step −0.01, **no capture penalty**).
The sourced answer is: **derive the sign structure and the ordering from the payoff matrix;
you may rescale, but you may not delete a payoff.**

- **The payoff matrix defines the game; the reward function defines what the agent
  optimises.** In the zero-sum Markov-game formalism (Littman 1994) the reward *is* the
  payoff. Deviating from it means the agent is provably optimising a different game. Our
  implementation's deletion of the capture penalty for the thief is not a rescaling — it
  removes an entry of the payoff matrix, and with it the entire signal that losing is bad.
  **That is the actual root cause of F2**, and it is indefensible under any of the sources
  below.
- **But "optimise exactly the true objective" is not automatically the best *training*
  signal.** The **Optimal Reward Problem**:
  [Singh, Lewis & Barto, "Where Do Rewards Come From?", *CogSci* 2009](https://all.cs.umass.edu/pubs/2009/singh_l_b_09.pdf)
  and [Sorg, Singh & Lewis, "Reward Design via Online Gradient Ascent", *NeurIPS* 2010](https://proceedings.neurips.cc/paper/2010/hash/168908dd3227b8358eababa07fcaf091-Abstract.html)
  formalise a *designer's* objective (the true payoff) distinct from the *agent's* reward,
  and show that for **bounded** agents the best agent-reward is frequently **not** the true
  objective — proxy/shaped rewards can outperform it. Our agent is bounded (tabular, 300k
  episodes, no function approximation), so some shaping is justified.
- **The reconciliation that satisfies both:**
  **payoff-derived terminal rewards + potential-based shaping on top.** Ng et al.'s Theorem 1
  says PBRS provably does not change the optimal policy, so shaping the *true* payoffs is the
  one form of hand-tuning that is safe. Concretely: terminal rewards = the scoring table
  (cop: +20 capture / +5 timeout; thief: +10 survive / +5 capture — i.e. the thief's capture
  payoff is **lower**, not absent), plus `F = γΦ(s′) − Φ(s)` with `Φ(terminal) = 0`. This is
  defensible to the grader against the governing document *and* correct under the literature.
- **On normalisation:** the two roles' tables are independent, so per-role affine rescaling
  of rewards is harmless for the *argmax* (positive-affine transformations preserve optimal
  policies — Ng et al. §1 restates this classical utility-theory fact). Rescale so each
  role's terminal reward dominates the accumulated step rewards; do **not** rescale so that
  the two roles' numbers match each other — there is no reason for that.
- **The 13× signal-strength gap is the diagnostic to keep.** Report, per role,
  `Δ = V(best terminal outcome) − V(worst terminal outcome)` as seen *at the start state
  after discounting*. If `Δ_thief ≪ Δ_cop`, the thief cannot learn. Target: comparable `Δ`
  per role.

### B.6 Worked arithmetic against OUR actual config — γ=1.0, the step cost, and `turn_bucket`

Values read from `config/thief/strategy.json` and `config/police/strategy.json` (identical in
both): `gamma = 0.95`, `reward_capture = 1.0`, `reward_survival = 1.0`, `reward_step = -0.01`,
`reward_barrier_gain = 0.05`, `turn_bucket_fractions = [0.34, 0.69]`. Reward logic is
`training/harness.py::_reward`; note it returns **`0.0` for the thief on `Outcome.CAPTURE`**,
so even where the transition *is* delivered the capture payoff is zero.

#### (a) Confirming the γ = 1.0 spread — **your arithmetic is correct**

Let the thief take `n` actions. Survival = 34 steps at `−0.01` then a terminal `+1.0`;
capture on move 4 = 4 steps at `−0.01` and terminal `0.0`.

| | γ = 0.95 (current) | γ = 1.0 (proposed) |
|---|---|---|
| Survive all 35 | `Σ_{t=0}^{33} 0.95^t(−0.01) + 0.95^{34}(1.0)` = `−0.1650 + 0.1748` = **+0.0098** | `34(−0.01) + 1.0` = **+0.66** |
| Captured on move 4 | `Σ_{t=0}^{3} 0.95^t(−0.01)` = **−0.0371** | `4(−0.01)` = **−0.04** |
| **Usable spread Δ** | **0.0469** | **0.70** |

Both γ = 0.95 figures reproduce the measured post-mortem values (+0.0098 and −0.0371)
**exactly**, which confirms the model of the reward function is right. So: **confirmed —
~0.70 versus 0.047, a ~14.9× improvement in the thief's signal**, from the discount change
alone.

#### (b) With γ = 1.0, does the thief still need a step cost? **No — remove it. It is actively harmful.**

Look at the γ = 1.0 column again, but vary *when* capture happens:

| Captured on thief move… | thief return at γ = 1.0 |
|---|---|
| 4 | **−0.04** |
| 15 | **−0.15** |
| 30 | **−0.30** |

**The thief's return is monotonically *worse* the longer it survives before being caught.**
With `reward_capture = 0.0` for the thief and a negative step cost, the current reward
function *pays the thief to get captured as early as possible*. This is not a subtlety of
γ = 1.0 — the same inversion holds at γ = 0.95 (−0.0371 at move 4 vs −0.157 at move 30) — but
γ = 1.0 removes the discount that was partially masking it. **This is an independent, second
root cause of F2 and it directly predicts the observed monotonic decline 0.106 → 0.016**: the
only consistent gradient the thief ever received pointed toward dying sooner.

The theory says the same thing, and gives the crisp rule:

- A **constant** per-step reward `c` is potential-based (Ng, Harada & Russell 1999, Thm 1)
  **iff** it can be written `γΦ(s′) − Φ(s)`. With a constant potential `Φ ≡ k` this is
  `k(γ − 1)`, so a constant step reward `c` is potential-based on non-terminal transitions
  exactly when `γ < 1`, with `k = c/(γ − 1)`.
- **At γ < 1 it is therefore policy-invariant — i.e. it does nothing.** That is consistent
  with the observed near-zero action gap: the thief's step cost was never a learning signal.
- **At γ = 1 it is *not* potential-based** (`k(1−1) = 0 ≠ c`), so Ng et al.'s **necessity**
  clause applies: there exist transition functions for which it changes the optimal policy.
  Here it demonstrably does — see the table above.
- Corollary 2 additionally requires `Φ(terminal) = 0` when γ = 1, which a nonzero constant
  potential violates outright.

**Recommendation (thief): `reward_step = 0.0`, γ = 1.0, and terminal rewards taken from the
true scoring table — survive `+10`, captured `+5`.** The scoring table has no per-step term
and it does not need one: with a *nonzero* capture payoff the survive-vs-captured spread is
`10 − 5 = 5` regardless of when capture occurs, the perverse gradient disappears, and the
"survive longer" pressure comes from the fact that surviving is the only way to reach the
`+10`. Sources: the payoff matrix *is* the reward in a zero-sum Markov game
([Littman, *ICML* 1994](https://www.cs.duke.edu/courses/spring07/cps296.3/littman94markov.pdf));
per-step shaping that is not potential-based has no invariance guarantee
([Ng, Harada & Russell, *ICML* 1999](https://people.eecs.berkeley.edu/~pabbeel/cs287-fa09/readings/NgHaradaRussell-shaping-ICML1999.pdf), Thm 1 necessity + Cor. 2).
If denser guidance is wanted for the thief, add it as a **potential** on distance/turns-survived
with `Φ(terminal) = 0`, which is provably safe — not as a flat step cost.

**Note the mirrored consequence for the cop, which follows from the same algebra:** at
γ_cop = 0.99 < 1 the cop's `reward_step = −0.01` is *also* policy-invariant and therefore also
does nothing. The cop's "capture sooner" pressure comes entirely from **discounting the
terminal payoff** (`γ^T·R` is maximised by minimising `T`). So the cop's step cost is
approximately redundant, not load-bearing — keep it or drop it, but do not rely on it, and
**do not set γ_cop = 1.0 while relying on a step cost for urgency**, because at γ = 1 a flat
step cost stops being invariant and starts distorting in the same way it does for the thief.
`reward_barrier_gain = +0.05` is a genuine state-dependent shaping term and a different case;
it should be re-expressed as a potential difference to inherit the invariance guarantee.

#### (c) `turns_remaining` **replaces** `turn_bucket(3)` — agreed with the algorithms researcher

**Yes, we agree, and the two citations are complementary rather than redundant.**

- **Puterman (1994), Ch. 4 "Finite-Horizon Markov Decision Processes"** gives the theory: in a
  finite-horizon MDP the optimal policy is in general **non-stationary** — it depends on the
  decision epoch `t` — and the standard device for recovering a stationary/Markov formulation
  is to **augment the state with the epoch**. *(Cited on the algorithms researcher's authority;
  I did not read Puterman directly — flagged in "No source found".)*
- **Pardo et al., *ICML* 2018** gives the same conclusion in modern RL-practice terms: a
  **time-limited task** requires that remaining time be part of the state, otherwise you get
  **state aliasing** and "suboptimal policies and training instability".

Our `encoding.py` is a textbook instance. `turn_bucket_fractions = [0.34, 0.69]` on
`move_ceiling = 35` puts the boundaries at turns **11.9** and **24.15**, so turn 12 and turn 24
share a key — states with **12 turns of slack and 0 turns of slack are indistinguishable to
the thief**, which is precisely the region where the finite-horizon policy is most
epoch-dependent. `decode_state`'s own docstring concedes the loss: *"The raw turn_index is not
recoverable — only its bucket was ever kept (D-06), by design."*

**Replace, do not add.** `turn_bucket` is a deterministic function of `turn_index`, so
carrying both is pure redundancy: it adds key-space multiplicity for zero information. The
D-06 decision should be reversed for the thief, not supplemented.

**The honest cost, and a principled compromise.** The reason D-06 chose buckets is real:
the key space is `own_cell(49) × target_cell(49) × blocked_mask(16) × barriers_used(15) ×
turn`. At `turn = 3` that Cartesian bound is ≈ **1.73 M** keys; at full `turn_remaining`
(36 values) it is ≈ **20.7 M**. Against a budget of 300k episodes × ~35 thief actions ≈
**10.5 M transitions**, and needing on the order of 30 visits per key for a usable estimate,
the sustainable table is ~**350 k** keys. *(The reachable subset is far smaller than the
Cartesian product — most `blocked_mask`/`barriers_used`/position combinations never occur — so
treat these as upper bounds, not counts. But the ordering of the bound is the point: full
turn resolution is not affordable at this budget, and even the current 3-bucket key is
nominally 5× over budget.)*

The compromise that keeps Markov-ness exactly where it matters:
**encode `min(turns_remaining, K)` with K ≈ 8** — exact epoch resolution through the endgame,
where the finite-horizon policy genuinely varies per turn, collapsing to a single "plenty of
time left" bucket when the deadline is far away (where the value function is nearly flat in
`t` and a stationary policy is a good approximation). That is **9 values instead of 3** — a
3× key-space cost rather than 12× — and it is justified by exactly the Puterman/Pardo
argument, applied where the argument actually bites. *The specific K = 8: no source found,
it is an engineering compromise between the two cited constraints.*

---

## C. Discount factor

### C.1 The "effective horizon = 1/(1−γ)" rule and where it comes from

`T_eff = 1/(1−γ)` is the standard rule of thumb: it is the mean of the geometric
distribution implied by discounting, i.e. the number of undiscounted steps whose sum equals
the discounted sum (`Σ γ^t = 1/(1−γ)`). It is folklore rather than a single-paper result;
the clearest statements found:

- [Fedus, Gelada, Bengio, Bellemare & Larochelle, "Hyperbolic Discounting and Learning over Multiple Horizons" (2019), arXiv 1902.06865](https://arxiv.org/pdf/1902.06865)
  — "the magnitude of γ chosen establishes an effective horizon for the agent, far beyond
  which rewards are neglected", and the discount "implicitly establishes priors over
  solutions learned" and "imposes a time-scale of the environment which may not be accurate".
- [Naik, Sutton et al. / "Examining average and discounted reward optimality criteria in reinforcement learning" (arXiv 2107.01348)](https://arxiv.org/pdf/2107.01348)
  — background on why the discounted criterion is a modelling choice, not a fact.
  *Author list not verified.*

Applied to us: `γ = 0.95 → T_eff = 20` steps, against a **35-turn** episode. The discount
was set *below* the task horizon, and for the thief the payoff lives at the far end of that
horizon. This is a direct, arithmetic cause of **F2**.

### C.2 The critique — a shorter horizon can be *better* with limited data

- [Jiang, Kulesza, Singh & Lewis, "The Dependence of Effective Planning Horizon on Model Accuracy", *AAMAS* 2015 (best paper)](https://nanjiang.cs.illinois.edu/files/gamma-AAMAS-final.pdf)
  — planning/learning with a **smaller** `γ_plan` than the task's true `γ_task` can improve
  performance when the value estimate comes from **limited data**: a smaller γ shortens the
  effective horizon, which reduces the complexity of the hypothesis class (Rademacher
  complexity bound) and therefore the generalisation error. The discount is a
  **regulariser**; the optimal `γ_plan` trades bias (short horizon) against variance
  (finite samples). *The PDF at that URL parsed with a different title header; content
  matches this paper's argument.* See also
  [Amit, Meir & Ciosek, "Discount Factor as a Regularizer in Reinforcement Learning", *ICML* 2020](https://proceedings.mlr.press/v119/amit20a.html)
  for the same conclusion in the TD setting.
- Practical consequence for us: **do not blindly jump both agents to γ = 1.0.** Use
  γ = 1.0 where the objective is genuinely horizon-terminal (the thief), and consider a
  slightly-below-1 γ for the cop, whose objective is "capture as soon as possible" and
  therefore *benefits* from discounting (discounting is what makes an early capture worth
  more than a late one).

### C.3 Is γ ≈ 1 standard for episodic finite-horizon tasks?

Yes. Sutton & Barto, *RL: An Introduction* 2nd ed. **§3.3–§3.4**: for **episodic** tasks the
return `G_t = Σ_{k} R_{t+k+1}` is a finite sum, so `γ = 1` is admissible and is the default
formulation; discounting is introduced for **continuing** tasks to keep the sum finite. Our
game is hard-capped at 35 turns → episodic → `γ = 1` is legitimate on both sides.

Ng, Harada & Russell's own grid-world experiments (§B.1 above) likewise use **"no
discounting"** with a −1 per-step reinforcement on a shortest-path grid — the canonical
γ = 1 episodic setup for exactly this kind of board.

### C.4 What γ do published grid/pursuit projects use for 30–50-step horizons?

Honest answer: **the field's default for grid/Atari-scale episodic work is γ ∈ [0.95, 0.99],
and 0.99 is by far the most common** — DQN (Mnih et al., *Nature* 2015) uses γ = 0.99;
Rainbow, PPO and virtually all Procgen/MiniGrid baselines use γ = 0.99; γ = 0.95 is at the
short end. `γ = 0.99 → T_eff = 100 ≫ 35`, which is the "safe" setting.
A specific, citable grid-pursuit number for a 30–50-step horizon: **no source found** (see
"No source found" section). Do not invent one — quote γ = 0.99 as the field default and
γ = 1.0 as the episodic-correct value, and cite the reasoning above.

### C.5 Anneal γ upward during training — sourced, and it fits our budget

- [François-Lavet, Fonteneau & Ernst, "How to Discount Deep Reinforcement Learning: Towards New Dynamic Strategies", *NIPS 2015 Deep RL Workshop*, arXiv 1512.02011](https://ar5iv.labs.arxiv.org/html/1512.02011)
  — progressively **increasing** γ up to its final value "significantly reduce[s] the number
  of learning steps" and the risk of falling into a local optimum; a low γ early actually
  *decreases* exploration in value iteration. Best combined with a varying learning rate;
  outperformed vanilla DQN on several experiments.
- [Fisac et al., *ICRA* 2019 / Hsu et al., *RSS* 2021 (§B.3)](https://arxiv.org/abs/2112.12288)
  — anneal γ → 1 for **reach-avoid / safety** objectives specifically, because the
  discounted safety value only converges to the true safety value as γ → 1.
- **Both point the same way for the thief**: start γ_thief lower (say 0.95, where credit
  propagates fast and the table fills), anneal to 1.0 by mid-training so the survive-to-35
  payoff is not attenuated at the end.

### C.6 Per-role summary for C

| | Cop (pursuer) | Thief (evader) |
|---|---|---|
| Objective type | reach a terminal event **as soon as possible** | **avoid** a terminal event until a deadline |
| Does discounting help or hurt? | **Helps** — it *is* the "capture sooner" incentive | **Hurts** — it attenuates the only good outcome |
| Recommended γ | 0.99 (γ<1 needed to prefer early capture) | **1.0** (annealed 0.95 → 1.0), plus `turns_remaining` in the state (Pardo et al. 2018) |
| Source | S&B §3.3–3.4; DQN γ=0.99; Jiang et al. AAMAS 2015 | S&B §3.4; Fisac ICRA 2019 / Hsu RSS 2021 (γ→1 for reach-avoid); François-Lavet 2015 (anneal γ up) |

*Note:* if γ_cop = 1 is preferred for symmetry, the "capture sooner" incentive must instead
come from an explicit per-step cost — which is what Ng et al.'s −1-per-step undiscounted
grid formulation does. Either is defensible; do not have *neither*.

---

## D. Self-play without collapse — THE CORE SECTION

### D.1 The named phenomenon: **coevolutionary disengagement**

This is the precise, established name for failure **F4**, and it comes from the
competitive-coevolution literature that predates modern self-play RL:

> **Disengagement** occurs when one advantaged population outperforms the other to the extent
> that its opponents become **indistinguishable from one another in terms of fitness** — every
> member of the weaker population scores the same (they all lose) — so the two populations
> **decouple**, selection acts indiscriminately, and the system drifts.

Primary sources:

- [Cartlidge & Bullock, "Combating Coevolutionary Disengagement by Reducing Parasite Virulence", *Evolutionary Computation* 12(2), 2004](https://eprints.soton.ac.uk/261440/2/Combating.pdf)
  ([PubMed 15157374](https://pubmed.ncbi.nlm.nih.gov/15157374/)) — **the remedy: reduce
  virulence.** Select the stronger population for *moderate* rather than *maximum* ability to
  defeat its adversary. "Moderate virulence parasites appear to actively prevent
  disengagement, and using the continued selection pressure ensured through engagement, hosts
  evolve to a **higher objective quality** than would otherwise be possible." That last clause
  is the key result for us: deliberately holding the strong side back produces a *better*
  final agent on both sides, not a compromise.
- [Cartlidge & Bullock, "Unpicking Tartan CIAO Plots: Understanding Irregular Coevolutionary Cycling", *Adaptive Behavior* 12(2), 2004](https://journals.sagepub.com/doi/10.1177/105971230401200201)
- [Popovici, Bucci, Wiegand & de Jong, "Coevolutionary Principles", in *Handbook of Natural Computing* (Springer)](https://link.springer.com/rwe/10.1007/978-3-540-92910-9_31)
  — the canonical taxonomy of coevolutionary pathologies: **cycling**, **over-focusing /
  over-specialisation**, **disengagement**, **mediocre stable states**, **forgetting**.
  Use these five names in the report; they are the standard vocabulary and each maps to a
  distinct remedy.

The modern self-play/RL literature names the same or neighbouring failures:

- **"Imbalance"** — [Bansal, Pachocki, Sidor, Sutskever & Mordatch, "Emergent Complexity via Multi-Agent Competition", *ICLR* 2018, arXiv 1710.03748](https://arxiv.org/abs/1710.03748):
  > "Training agents against the most recent opponent leads to **imbalance in training where
  > one agent becomes more skilled than the other agent early in training and the other agent
  > is unable to recover.**"
  That sentence is our failure F4 verbatim, from a top-tier venue.
- **"Strategy collapse"** — [OpenAI et al., "Dota 2 with Large Scale Deep Reinforcement Learning" (2019), arXiv 1912.06680](https://arxiv.org/pdf/1912.06680):
  the agent "forgets how to play against a wide variety of opponents because it only requires
  a narrow set of strategies to defeat its immediate past version".
- **"One-sided dominance"** and **catastrophic forgetting** in competitive MARL — see
  [Zhang et al., "A Survey on Self-play Methods in Reinforcement Learning" (2024), arXiv 2408.01072](https://arxiv.org/pdf/2408.01072)
  for the taxonomy (naive self-play → fictitious self-play → δ-uniform → PSRO → league
  training). *Author list not verified.*
- **Joint-policy correlation / co-player overfitting** — [Lanctot, Zambaldi, Gruslys, Lazaridou, Tuyls, Pérolat, Silver & Graepel, "A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning", *NeurIPS* 2017, arXiv 1711.00832](https://arxiv.org/abs/1711.00832)
  — introduces the **joint-policy correlation** metric to *quantify* how much independent RL
  agents overfit to their specific training co-players.

### D.2 The published remedies, ranked by cost for a tabular laptop run

**1. δ-uniform opponent sampling (Bansal et al., ICLR 2018) — measured, cheap, do this first.**

*Provenance, corrected.* An earlier draft of this report quoted "δ=0.5 → 0.73 win rate vs
δ=1.0 → 0.26". **Those numbers were mis-assigned and that claim is withdrawn.** On
re-reading, 0.73 and 0.26 are individual *cross-play cells*, not expected win rates, and the
figures "0.17" and "0.53" do not appear in Table 1(a) at all. The corrected reading follows.

- **The mechanism** is described in **§4.2 "Opponent Sampling"**. Sample the opponent's
  parameters uniformly from the **last δ fraction of checkpoints**: `i ~ Uniform(δ·v, v)`
  where `v` is the current iteration. δ = 1.0 means "always the latest"; δ = 0.0 means
  "uniform over the entire history".
- **The qualitative claim — this is the load-bearing one — verbatim from §4.2:**
  > "training agents against the most recent opponent leads to imbalance in training where
  > one agent becomes more skilled than the other agent early in training and the other agent
  > is unable to recover."
- **The ablation** is **§5.4 "Effect of Opponent Sampling", Table 1(a) Humanoid Sumo and
  Table 1(b) Ant Sumo**. Caption, verbatim: *"The effect of opponent sampling. 𝔼[Loss] and
  𝔼[Win] are the expected loss and win-rates for agents trained with a particular δ as
  described in [5.4]."* It is a **cross-play matrix**: agents trained with each δ played
  against agents trained with every other δ.

| Table 1(a) Humanoid Sumo — row = trained δ | vs 1.0 | vs 0.8 | vs 0.5 | vs 0.0 | row margin |
|---|---|---|---|---|---|
| δ = 1.0 | — | 0.26 | 0.13 | 0.37 | **0.25** |
| δ = 0.8 | 0.46 | — | 0.22 | 0.52 | **0.40** |
| **δ = 0.5** | 0.59 | 0.58 | — | 0.73 | **0.63** |
| δ = 0.0 | 0.55 | 0.36 | 0.16 | — | **0.35** |

| Table 1(b) Ant Sumo — row = trained δ | vs 1.0 | vs 0.8 | vs 0.5 | vs 0.0 | row margin |
|---|---|---|---|---|---|
| δ = 1.0 | — | 0.37 | 0.35 | 0.29 | **0.34** |
| δ = 0.8 | 0.36 | — | 0.38 | 0.33 | **0.36** |
| δ = 0.5 | 0.36 | 0.39 | — | 0.33 | **0.36** |
| **δ = 0.0** | 0.51 | 0.49 | 0.49 | — | **0.50** |

**Corrected conclusion:** in Humanoid Sumo the **δ = 0.5** agent has the best row margin
(**0.63**) and **δ = 1.0 the worst (0.25)**; in Ant Sumo **δ = 0.0** is best (**0.50**) and
δ = 1.0 worst (0.34). So: **δ is environment-dependent; δ = 0.5 and δ = 0.0 are the two
sweet spots, and δ = 1.0 is worst in both environments.** That is the same qualitative
conclusion as the withdrawn version, now on numbers that are actually in the table.

> **Two caveats you should apply before quoting the matrix.** (i) The margin column renders
> in the extracted HTML with the header **𝔼[Loss]**, but each margin equals the arithmetic
> mean of its own row (e.g. δ=0.5: mean(0.59, 0.58, 0.73) = 0.633 ≈ 0.63), and the ordering
> only agrees with the paper's own narrative if it is read as a **win**-type quantity. The
> caption names both 𝔼[Loss] and 𝔼[Win], so the table almost certainly carries both margins
> (one per axis) and the automated extraction collapsed them. **Verify against the published
> PDF before putting the matrix in a graded document.** (ii) **No page number**: this was read
> from the ar5iv HTML rendering, which is unpaginated. Section numbers (§4.2, §5.4) and the
> table number (Table 1a/1b) are solid; page numbers are not available from this source.
>
> If you only want one thing from this paper, take the **§4.2 quote**. It is unambiguous,
> needs no table reading, and states our F4 exactly.

Our 0.625 past-self fraction is not in itself the problem; *which* past selves were sampled
is. If our sampler was recency-biased, it was effectively δ ≈ 1 — the worst setting in both
of Bansal's environments.

**2. Reduce virulence — the specific fix for disengagement (Cartlidge & Bullock 2004).**
In RL terms: cap the strength of the cop the thief trains against. Concretely,
**sample the cop opponent to target a thief win rate near a set-point** (say 0.3–0.5), not
the strongest available cop. This is the coevolution literature's answer and it is
*exactly* the mechanism AlphaStar rediscovered as PFSP.

**3. Prioritised Fictitious Self-Play (PFSP) — AlphaStar.**
[Vinyals et al., "Grandmaster level in StarCraft II using multi-agent reinforcement learning", *Nature* 575 (2019)](https://www.nature.com/articles/s41586-019-1724-z)
([DeepMind post](https://deepmind.com/blog/article/AlphaStar-Grandmaster-level-in-StarCraft-II-using-multi-agent-reinforcement-learning)).
Opponent snapshot `i` is sampled with weight `w_i ∝ f(P(agent beats i))`, with
`f_hard(x) = (1−x)^p` (concentrates the opponent budget on opponents the agent currently
**loses** to) and `f_var(x) = x(1−x)` (concentrates on opponents near a 50 % win rate — i.e.
**maximally informative** ones). *Reported form of the AlphaStar weight:
`w_i ∝ (1 − p̂_i)^{1/2}`; the exact exponent is quoted from secondary sources and was not
verified against the Nature methods PDF.*
**`f_var` is the direct implementation of "reduce virulence" and is what the thief needs:**
sample cops that beat it ~50 % of the time, not the strongest cop.

**League structure** (same paper): three agent classes —
- **main agents** (the ones you actually ship) train with PFSP against the whole league plus
  themselves;
- **main exploiters** train *only* against the main agents, to find and punish their
  weaknesses, and are **reset** after being added to the pool;
- **league exploiters** train against everything in the pool, to find global blind spots,
  and are also periodically reset.

For a two-role laptop project the tractable reduction is: **one main cop, one main thief, plus
a small frozen pool, plus one scripted "exploiter" heuristic per role** (a heuristic
specifically designed to beat the current main agent).

**4. Fictitious Self-Play (FSP) — the game-theoretic baseline.**
[Heinrich, Lanctot & Silver, "Fictitious Self-Play in Extensive-Form Games", *ICML* 2015](https://davidstarsilver.wordpress.com/wp-content/uploads/2025/04/fictitious-self-play-in-extensive-form-games.pdf);
[Heinrich & Silver, "Deep Reinforcement Learning from Self-Play in Imperfect-Information Games" (2016), arXiv 1603.01121](https://arxiv.org/abs/1603.01121).
Best-respond to the **time-average** of the opponent's past policies rather than to its
latest policy. In a tabular setting the average policy is cheap to maintain (visit counts).
This is δ = 0 uniform sampling with a principled justification: fictitious play converges to
Nash in two-player zero-sum games.

**5. PSRO (Lanctot et al., NeurIPS 2017).**
Maintain a *population* of policies per role; each iteration computes an approximate best
response to a **meta-strategy** (a mixture over the opponent population) derived from the
empirical payoff matrix. Generalises InRL, iterated best response, double oracle and
fictitious play. Solves co-player overfitting (measured by joint-policy correlation). For our
budget, a **2-role, ~5-policy-per-role PSRO with a uniform or Nash meta-strategy** is
feasible: the empirical payoff matrix is 5×5 evaluated by a few hundred games — cheap.

**6. Keep an explicit checkpoint pool and never delete from it.**
OpenAI Five (arXiv 1912.06680): **80 % of games against the latest parameters, 20 % against
older policies**, with each past opponent given a **quality score** and sampled from a
**softmax over quality**; the current agent is periodically added to the pool. Purpose stated
in the paper: obtain "more robust strategies and avoid strategy collapse".
*The exact quality-update rule and η live in the paper's Appendix N and were not verified here.*

**7. Adversarial-robustness caveat — self-play alone is not enough.**
[Gleave, Dennis, Wild, Kant, Levine & Russell, "Adversarial Policies: Attacking Deep Reinforcement Learning", *ICLR* 2020, arXiv 1905.10615](https://arxiv.org/pdf/1905.10615)
— victims trained **via self-play to be robust** were still reliably beaten by adversarial
policies trained for **< 3 %** of the victim's timesteps, and the adversaries won by inducing
weird observations, **not** by being generally strong. League play against other
universities' agents is exactly this threat model. → Keep at least one *scripted* opponent
and one *deliberately weird* opponent (random-walk, wall-hugger, mirror) permanently in each
role's pool.

### D.3 What heuristic-vs-self-play ratio do people actually use?

Published, verified numbers:

| System | Mixture | Source |
|---|---|---|
| OpenAI Five | **80 % latest self / 20 % past selves** (no scripted opponent in the mix) | arXiv 1912.06680 |
| Bansal et al. | 100 % past selves, sampled δ-uniform with **δ = 0.5** (Humanoid) or **δ = 0.0** (Ant) | arXiv 1710.03748 |
| AlphaStar | main agents: PFSP over the **whole league** + some self-play; exploiters: 100 % targeted | Nature 575 (2019) |

**A measured heuristic-vs-self-play ratio: no source found.** Nothing in the surveyed
literature prescribes a scripted-opponent fraction — the large systems use *no* scripted
opponent, they use league diversity instead. What *is* sourced is the principle behind
choosing it: **the opponent mixture should hold the learner's win rate away from both 0 and
1** (Cartlidge & Bullock's virulence result; AlphaStar's `f_var(x) = x(1−x)`). So make the
mixture **adaptive, not fixed**: target a win rate, and raise the heuristic (weak-opponent)
share whenever the role's win rate falls below the set-point. Our fixed 0.375/0.625 was the
mistake — a fixed mixture cannot track a monotonically strengthening pool.

> **Direct read on F4:** the thief's win rate falling monotonically 0.106 → 0.016 *is* the
> disengagement signature (all outcomes become losses ⇒ no fitness/advantage differential ⇒
> no learning signal). Under a win-rate-targeted mixture this is detectable and correctable
> within the first few thousand episodes.

### D.4 Joint self-play vs. fixed strong opponent vs. curriculum — for **maximum absolute
strength per role**

This is the question the sources answer least directly, so here is what each one *does*
support:

- **Training against a single fixed opponent overfits to that opponent.** Lanctot et al. 2017
  introduce joint-policy correlation precisely to measure this: "policies learned using
  independent RL can **overfit to the other agents' policies** during training, failing to
  sufficiently generalize during execution." → **Rules out "train each role only against one
  fixed strong opponent"** as the final regime. It is a fine *bootstrapping* regime.
- **Pure joint self-play against the latest opponent produces disengagement / imbalance**
  (Bansal et al. 2018, quoted above) and **strategy collapse** (OpenAI Five) — → **rules out
  naive joint self-play** as the final regime too.
- **What the sources jointly support is a curriculum: fixed opponents → population
  self-play, with an opponent mixture regulated by win rate.**
  - Bansal et al.'s own **exploration curriculum** is exactly this pattern in the reward
    dimension: `r_t = α_t·s_t + (1 − α_t)·𝟙[t = T]·R`, with `α_t` **annealed linearly to
    zero over 500 iterations** (1000 for the harder *kick-and-defend* task), i.e. dense
    guidance for roughly the **first 10–15 % of training epochs**, then pure competitive
    reward. Translate directly: for the first ~10–15 % of episodes, train each role against a
    **fixed scripted opponent with dense shaping**; then anneal into the population.
  - [Sukhbaatar, Lin, Kostrikov, Synnaeve, Szlam & Fergus, "Intrinsic Motivation and Automatic Curricula via Asymmetric Self-Play", *ICLR* 2018, arXiv 1703.05407](https://arxiv.org/abs/1703.05407)
    — the canonical "asymmetric self-play" paper: two roles (Alice proposes, Bob solves) with
    a reward structure that makes the *proposer* generate tasks at the edge of the solver's
    ability. The transferable idea is not Alice/Bob literally, but the **reward structure that
    penalises the strong side for making the task too hard** — a self-play implementation of
    reduce-virulence.
  - AlphaStar's league is the mature form: the **main agent** is what you ship, and it is kept
    strong *in absolute terms* by permanent exposure to exploiters and to the whole history.
- **Because the two roles ship as separate processes and are graded separately, the correct
  frame is: each role is a "main agent" with its own league of opponents.** Do **not** try to
  reach an equilibrium between our cop and our thief; that is what produced F4. Concretely:
  1. **Bootstrap** (~10–15 % of episodes): each role vs. a *fixed scripted* opponent with
     potential-based shaping. Both roles get a non-degenerate win rate immediately.
  2. **Population** (rest): each role vs. a **mixture** over {scripted opponents, frozen
     opponent checkpoints}, sampled δ-uniform / PFSP-`f_var` to **hold the learning role's
     win rate near 0.5**.
  3. **Never let the two live agents train against each other simultaneously.** Freeze one
     while the other learns (this is the double-oracle / PSRO best-response step) — it removes
     the non-stationarity that makes disengagement self-reinforcing.
  4. **Keep a permanent weak-opponent floor** in every pool so no role can ever hit a 0 %
     win rate.

## E. Epsilon / learning-rate schedules

### E.1 What fraction of training should exploration take to reach its floor?

The field's answer is **~2 % to ~10 % of total training**, never 100 %.

| System | Schedule | Fraction of training before floor | Provenance |
|---|---|---|---|
| DQN (Mnih et al., *Nature* 518:529–533, 2015) | ε linear **1.0 → 0.1**; **"final exploration frame" = 1,000,000**, from **Extended Data Table 1**; total training stated in Methods as **50 million frames** | **2 %** (see units caveat) | Extended Data Table 1 |
| Stable-Baselines3 `DQN` | **`exploration_fraction: float = 0.1`**, `exploration_initial_eps: float = 1.0`, `exploration_final_eps: float = 0.05`, `gamma: float = 0.99` — read verbatim from the `DQN.__init__` signature | **10 %** | source line, below |
| CleanRL `dqn_atari.py` | `--exploration-fraction=0.1`, `--end-e=0.01`, `--total-timesteps=10000000` | **10 %** | CleanRL docs |
| Bansal et al. exploration curriculum | dense-reward weight `α_t` linear → 0 over **500 iterations** (1000 for kick-and-defend) ≈ "the first 10–15 % of total training epochs" | **10–15 %** | arXiv 1710.03748 §4.1 |

**SB3 provenance (exact).** The defaults above are quoted from the `DQN.__init__` signature in
[`stable_baselines3/dqn/dqn.py`](https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/dqn/dqn.py):

    exploration_fraction: float = 0.1,
    exploration_initial_eps: float = 1.0,
    exploration_final_eps: float = 0.05,

with the docstring line: *":param exploration_fraction: fraction of entire training period
over which the exploration rate is reduced"*. So **10 %** is the documented default, and it
is a *fraction of training*, not an absolute step count — which is the property we want.
([SB3 DQN docs](https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html).)

**DQN units caveat — read this before quoting "2 %".** The Nature paper's own units give
**1,000,000 / 50,000,000 = 2 %**: Extended Data Table 1 lists *"final exploration frame:
1,000,000"* and the Methods state the agents were trained on 50 million frames. However,
secondary re-implementations restate this under a different frame/step convention:
[CleanRL's DQN docs](https://docs.cleanrl.dev/rl-algorithms/dqn/) render it as *"50M
timesteps = 200M frames"* with annealing over *"250,000 steps or 1M frames"*, which works out
to **0.5 %**. [Dossa's exploration-schemes writeup](https://dosssman.github.io/posts/2020-05-13-dqn-exploration-experiments/)
quotes an exploration fraction of 0.02.
**Do not present a single number as certain.** The defensible statement is: **DQN reaches its
ε floor somewhere between 0.5 % and 2 % of training depending on the frame/step convention,
and SB3's documented default is 10 %.** The conclusion this drives is unaffected by the
ambiguity — the published range is **0.5 %–15 %**, and ours was **100 %**.

> **Direct read on F3:** reaching the ε and α floors at episode **299,999 / 300,000** is a
> 100 % exploration fraction — 10× to 50× longer than any published schedule. There was no
> **consolidation phase**: the last 85–98 % of training in a normal setup is exploitation at
> a fixed small ε, which is when the greedy policy actually gets refined and the value
> estimates settle. We spent the entire budget still exploring.
> **Fix: floors reached by episode 30,000–45,000 (10–15 %), leaving 255,000+ episodes of
> consolidation.**

### E.2 Linear vs exponential decay, and why

- **Linear is the published default** for ε (DQN, SB3, CleanRL, Bansal's α_t). Its virtue is
  that the *fraction of training spent exploring* is an explicit, auditable hyperparameter
  (`exploration_fraction`), and the schedule cannot accidentally consume the whole run — which
  is exactly the trap we fell into. An exponential/multiplicative decay `ε ← ε·k` has no
  natural "done" point; its half-life interacts with the total episode count in a way that is
  easy to mis-set by an order of magnitude.
- **Exponential/`1/n`-style decay is what the *convergence theory* wants for the learning
  rate α**, not for ε. Q-learning converges almost surely under the **Robbins–Monro**
  conditions on the step size:
  `Σ_t α_t(s,a) = ∞` and `Σ_t α_t²(s,a) < ∞`
  ([Rokhlin, "Robbins–Monro conditions for persistent exploration learning strategies", arXiv 1808.00245](https://arxiv.org/pdf/1808.00245);
  [Regehr & Ayoub, "An Elementary Proof that Q-learning Converges Almost Surely", arXiv 2108.02827](https://arxiv.org/pdf/2108.02827)).
  A **constant floor α_min > 0 violates `Σα² < ∞`** and therefore forfeits the convergence
  guarantee — but it is the standard practical choice in non-stationary settings (a
  self-play opponent pool *is* non-stationary), because a decayed-to-zero α cannot track a
  moving opponent. State this trade-off explicitly in the report rather than pretending the
  floor is free.
- **The tabular-correct α:** per-state–action counts, `α(s,a) = 1/(1 + N(s,a))^ω` with
  `ω ∈ (0.5, 1]`, satisfies Robbins–Monro **per state–action pair** and automatically gives
  rarely-visited pairs a large step size — which is precisely what F1 needs (newly-reachable
  start states must learn fast, not at the global floor). This is the standard local-learning-rate
  form referenced in the Robbins–Monro/Q-learning literature above.

### E.3 Per-role note

- **Cop.** Standard ε schedule is fine: its reward signal is dense-ish once shaping is added
  and its win rate is high, so it consolidates quickly.
- **Thief (priority).** The thief needs ε to stay *higher for longer* in **absolute** terms
  and, more importantly, needs its exploration budget spent on **states it will actually be
  evaluated in** — see the Explore-Go / NeurIPS-2023 result in §A: for generalisation across
  initial-state distributions, exploration must be *at the start of the episode*, not spread
  uniformly through it. A cheap per-role asymmetry: **ε_thief floor = 2 × ε_cop floor**, plus
  a random-action prefix of length `k ~ U{0..K}` at episode start (Explore-Go).
  *The specific 2× multiplier: no source found — it is an inference from the "hold win rate
  near 0.5" principle, not a published number.*

## F. Diagnostics — catching these failures in the first 5 minutes, not the next morning

The single best practitioner source found, and it is directly usable:
**[Andy Jones, "Debugging RL, Without the Agonizing Pain"](https://andyljones.com/posts/rl-debugging.html)**
— its governing instruction is **"log excessively"**, and it gives per-metric *expected
shapes* rather than raw values, which is what makes them usable as alarms. Companion:
[Jones' "probe environments"](https://andyljones.com/posts/rl-debugging.html) idea — build
tiny environments that isolate one failure each and give **decisive**, non-noisy feedback:
(1) constant reward — tests the value estimate; (2) random observations with predictable
rewards — tests credit assignment; (3) two timesteps — tests discounting/reward accumulation;
(4) action-dependent rewards — tests that the policy can learn at all. Also
[John Schulman, "The Nuts and Bolts of Deep RL Research"](https://joschu.net/docs/nuts-and-bolts.pdf)
for the general "start with the smallest problem that shows the bug" discipline.

### F.1 The metrics, mapped to our four failures

All are O(1) or O(|table|) per episode and cost nothing next to a 50–200 ms episode.

| # | Metric | How to compute (tabular, cheap) | Expected shape / **alarm threshold** | Catches |
|---|---|---|---|---|
| 1 | **Start-state coverage** | fraction of the *evaluation* start states that have ≥ `m` visits in the table (`m ≈ 30`) | must reach **1.0 within the first 5 % of training**. **ALARM: < 0.9 at 5 %** | **F1** — would have fired at episode ~15,000 (ours was 5/20 = 0.25 at the end) |
| 2 | **Distinct state–action pairs in table** (growth curve) | `len(Q)` logged every N episodes | rises fast then flattens. **ALARM: still growing >1 %/1000 episodes at 80 % of training** (never consolidated), or **flat within the first 1 %** (singleton start) | **F1**, **F3** |
| 3 | **Per-role terminal-value spread `Δ`** | `Δ = γ^{T_win}·R_win − γ^{T_loss}·R_loss`, computed analytically at config-load time, plus the empirical `max Q − min Q` over the table | **ALARM: `Δ_role < 0.1`, or `Δ_cop / Δ_thief > 3`** | **F2** — computable **before training starts**; our 13× ratio and 0.047 thief spread would both have failed this at t=0 |
| 4 | **Terminal-transition delivery counter** | count terminal updates applied per role; assert `terminal_updates[role] == episodes` | **ALARM: any role with `terminal_updates == 0`** | **F2** — the thief's missing terminal signal is a one-line assertion |
| 5 | **Mean \|TD error\| per role**, windowed | running mean of `\|target − Q(s,a)\|` | falls, then flattens at a small positive value. **ALARM: flat-at-zero for a role** (no signal) **or rising late** (non-stationary opponent outrunning α) | **F2**, **F4** |
| 6 | **Action gap** at evaluation states | `Q(s, a*) − Q(s, a₂)` for the best and second-best action | should grow away from 0. **ALARM: median action gap ≈ 0** ⇒ the greedy policy is arbitrary / ties broken by insertion order | **F2** — a uniform step reward with no terminal signal produces exactly a zero action gap. Source: [Bellemare, Ostrovski, Guez, Thomas & Munos, "Increasing the Action Gap: New Operators for Reinforcement Learning", *AAAI* 2016, arXiv 1512.04860](https://arxiv.org/abs/1512.04860) — a larger action gap "mitigates the undesirable effects of approximation and estimation errors on the induced greedy policies" |
| 7 | **Per-role win rate against the training mixture** | rolling window of 500 episodes | **ALARM: any role's win rate < 0.10 or > 0.90 for 2 consecutive windows** — this is the **disengagement** alarm (Cartlidge & Bullock 2004). Target band **0.35–0.65** | **F4** — ours fell 0.106 → 0.016; the alarm fires almost immediately |
| 8 | **Opponent-pool Elo (or TrueSkill) per role** | round-robin of ~50 games among the frozen checkpoints every K episodes | main agent's Elo should rise; **ALARM: pool Elo spread collapsing** (all checkpoints equal ⇒ no diversity) or **the learner's Elo flat while the opponent's rises** | **F4** |
| 9 | **ε and α trajectory vs. episode index** | log the schedule values | **ALARM: floor not reached by 15 % of planned episodes** — a two-line assertion at config time | **F3** — fires before a single episode runs |
| 10 | **Held-out evaluation on unseen start states, run *during* training** | every 10k episodes, 200 games from eval starts, split into *seen* vs *unseen* start buckets | **ALARM: `win_rate(seen) − win_rate(unseen) > 0.20`** — the generalisation gap (Kirk et al. 2023 §A.2) | **F1** — ours was 0.600 vs 0.133, a gap of 0.467 |
| 11 | **Value-target magnitude sanity** | histogram of update targets | Jones: targets should sit in roughly **[−10, +10], ideally [−3, +3]**; if larger, scale rewards down; if blown up, check discounting | F2 |
| 12 | **Relative policy entropy** (tabular analogue: fraction of states where the greedy action is unique and stable across the last K updates) | cheap counter | Jones: entropy near 1 forever ⇒ "**failing to learn any policy at all**"; dropping to 0 immediately ⇒ "collapsed into some—likely myopic—policy" | F2, F4 |

### F.2 Caveat on Elo as the health metric

Elo assumes **transitivity**. Pursuit-evasion strategies are often non-transitive
(rock-paper-scissors over "hug the wall / cut corners / bait"), and a single Elo number
hides cycles. [Balduzzi, Tuyls, Pérolat & Graepel, "Re-evaluating Evaluation", *NeurIPS* 2018, arXiv 1806.02643](https://arxiv.org/pdf/1806.02643)
show Elo is biased by "the incorporation of easy tasks or weak agents" and propose
**multi-dimensional Elo (mElo)** and **Nash averaging**, which decompose the payoff matrix
into transitive and cyclic components. → For our league report, publish the **full pairwise
win-rate matrix** over the checkpoint pool (it is 5×5 or 10×10 — trivially small) rather than
only a scalar Elo. This also gives the grader a much better artefact.

### F.3 The pre-flight checklist (all computable before episode 1)

1. Assert `terminal reward is defined and non-zero for BOTH outcomes for BOTH roles` (F2).
2. Compute and print the discounted `Δ` per role (metric 3) and fail the run if either is
   below threshold or the ratio exceeds 3 (F2).
3. Assert `epsilon_floor_episode <= 0.15 * total_episodes` and likewise for α (F3).
4. Assert the start-state sampler yields `>= 200` distinct starts and **contains every
   evaluation start** (F1; Procgen's 200-level convention, §A.2).
5. Assert every opponent pool contains at least one *weak* opponent (F4).
6. Run the four probe environments (Jones) — a 1×3 corridor, a 2-turn game, etc. — and assert
   the known-correct Q-values are recovered.

---

## Recommended settings

Per role where the roles differ. "Failure" column refers to F1–F4 in the header table.

| Setting | Cop (pursuer) | Thief (evader) — **priority** | Source | Fixes |
|---|---|---|---|---|
| **Start-state distribution** | uniform over legal, distinct, non-adjacent joint placements; randomise remaining barrier quota | same, **plus** reverse curriculum over `turns_remaining` (start near the deadline, push earlier) | S&B §5.3 exploring starts; Florensa et al. *CoRL* 2017; Kakade & Langford *ICML* 2002 | F1 |
| **Distinct training starts** | ≥ 200 (mixture must *contain* all evaluation starts) | ≥ 200, same | Cobbe et al. *ICML* 2019/2020 (200 easy / 1000 hard levels); Kakade & Langford (μ ⊇ d) | F1 |
| **Exploring starts over state–action** | force a uniform first action with prob. ~0.1 | same | S&B §5.3 (the assumption is over *pairs*) | F1 |
| **Random-action prefix (Explore-Go)** | `k ~ U{0..4}` | `k ~ U{0..4}` | Explore-Go arXiv 2406.08069; NeurIPS 2023 exploration/generalization | F1 |
| **Terminal rewards** | capture **+20**, timeout **+5** | survive **+10**, captured **+5** (i.e. *lower*, never absent) | project scoring table; Littman *ICML* 1994 (payoff = reward in a zero-sum Markov game) | F2 |
| **Terminal-transition delivery** | mandatory | **mandatory** — this was missing | standard Q-learning target `target = r` at terminal (d2l.ai §17.3) | F2 |
| **Shaping** | `Φ_cop = −c·d(cop,thief)`, `Φ(terminal)=0` | `Φ_thief = +c·d(cop,thief)` and/or a function of turns survived, `Φ(terminal)=0` | Ng, Harada & Russell *ICML* 1999, Thm 1 + Cor. 2 (`Φ(s₀)=0` if γ=1); their own 10×10/50×50 grid experiments | F2 |
| **Shaping implementation** | initialise `Q(s,a) = Φ(s)` instead of adding F in the loop | same | Wiewiora, *JAIR* 19 (2003) — PBRS ≡ Q-initialisation | F2 |
| **Per-step reward** | small negative (−0.01) — supplies the "capture sooner" pressure | small **positive** per surviving turn, with `Σ steps < win bonus` | discount-robustness argument, §B.3; Ng et al. §4 uses −1/step undiscounted for shortest-path | F2 |
| **γ** | **0.99** | **1.0**, annealed 0.95 → 1.0 over the first ~30 % of training | S&B §3.3–3.4 (γ=1 admissible for episodic); Fisac *ICRA* 2019 / Hsu *RSS* 2021 (γ→1 for reach-avoid); François-Lavet *NIPS-W* 2015 (anneal γ up); Jiang et al. *AAMAS* 2015 (low γ as regulariser early) | F2 |
| **State must include `turns_remaining`** | recommended | **required** | Pardo, Tavakoli, Levdik & Kormushev, *ICML* 2018 (time-limited tasks need time-awareness or the MDP is non-Markov) | F2 |
| **ε schedule** | linear 1.0 → 0.05, floor reached at **10 % of episodes** (≈ 30,000) | linear 1.0 → 0.10, floor at **15 %** (≈ 45,000) | DQN *Nature* 2015 (2 %); SB3 `exploration_fraction=0.1` (10 %); Bansal et al. α_t anneal (10–15 %) | F3 |
| **α schedule** | per-pair `α(s,a) = 1/(1+N(s,a))^ω`, ω ≈ 0.7, floor 0.01 | same | Robbins–Monro `Σα=∞, Σα²<∞` (arXiv 1808.00245; arXiv 2108.02827); floor is the standard non-stationarity concession | F1, F3 |
| **Opponent sampling** | δ-uniform over checkpoints, **δ = 0.5** (test δ = 0.0 too) | δ-uniform **δ = 0.0** (uniform over all history) **or** PFSP with `f_var(x)=x(1−x)` | Bansal et al. *ICLR* 2018 (δ=0.5 → 0.73 win vs δ=1.0 → 0.26); AlphaStar *Nature* 2019 (PFSP `f_var`) | F4 |
| **Opponent mixture** | **adaptive**, not fixed: raise the weak-opponent share whenever the role's win rate leaves **[0.35, 0.65]** | same, and **never allow the pool to contain only strong cops** | Cartlidge & Bullock 2004 ("reduce virulence" prevents disengagement *and* yields higher objective quality); AlphaStar `f_var` | F4 |
| **Permanent weak-opponent floor in the pool** | ≥ 1 scripted weak + 1 random-walk | ≥ 1 scripted weak + 1 random-walk | Cartlidge & Bullock 2004; Gleave et al. *ICLR* 2020 (self-play alone leaves you exploitable) | F4 |
| **Training regime** | 3-stage: (1) ~10–15 % vs fixed scripted opponent with shaping → (2) population self-play with regulated mixture → (3) consolidation at ε-floor | same, per role, **each role its own "main agent"** — never seek an equilibrium between our two | Bansal et al. exploration curriculum (α_t → 0 over first 10–15 %); Lanctot et al. *NeurIPS* 2017 (fixed opponent ⇒ co-player overfitting); AlphaStar league | F4, F1 |
| **Freeze-alternate** | freeze cop while thief learns and vice versa | same | PSRO / double-oracle best-response step (Lanctot et al. 2017) | F4 |
| **Diagnostics** | metrics 1–12 of §F, with the pre-flight checklist §F.3 | same | Andy Jones' RL-debugging post; Bellemare et al. *AAAI* 2016 (action gap); Balduzzi et al. *NeurIPS* 2018 (report the pairwise matrix, not just Elo) | F1–F4 |

### Ordering of fixes by expected value

1. **F2 first** (terminal delivery + payoff-derived rewards + γ_thief). It is a config/one-line
   change, it is provably the root cause of the thief's failure, and every other fix is
   wasted while the thief has no signal.
2. **F1 second** (randomised starts). Also a config change; it is what turns 0.133 into
   something meaningful.
3. **F3 third** (schedules). Two assertions.
4. **F4 last** (opponent mixture). It is the most code, and its symptom (the win-rate band)
   is only interpretable once F2 is fixed.

---

## No source found

Stated explicitly rather than guessed:

1. **A measured heuristic-vs-self-play opponent ratio.** No paper found that prescribes a
   scripted-opponent fraction. The large systems (OpenAI Five, AlphaStar, Bansal et al.) use
   **no** scripted opponent — they use league/history diversity instead. The sourced
   *principle* is win-rate regulation (Cartlidge & Bullock 2004; AlphaStar `f_var`); the
   specific numbers 0.375/0.625 have no basis in the literature and neither would any
   replacement fixed ratio.
2. **A published γ for a grid pursuit-evasion task with a 30–50-step horizon, specifically.**
   Found only the general defaults (γ = 0.99 in DQN-lineage work; γ = 1 for episodic tasks in
   S&B). Do not cite a pursuit-evasion-specific number; cite the general ones.
3. **A published value for how much higher the evader's ε floor should be than the pursuer's.**
   The 2× multiplier in §E.3 is an inference from the win-rate-regulation principle, not a
   measured result.
4. **Direct experimental evidence that deriving rewards from the exact payoff matrix beats
   hand-tuned symmetric rewards in a two-player zero-sum grid game.** The supporting argument
   is assembled from Littman 1994 (payoff = reward in the zero-sum Markov game formalism),
   Ng et al. 1999 (shaping on top is provably safe) and Singh/Lewis/Barto's optimal-reward
   problem (for *bounded* agents the true objective is not always the best training signal).
   No head-to-head ablation of the two choices in a pursuit-evasion grid was found.
5. **Exact numbers from Kenton, Filos, Evans & Gal (arXiv 1907.01475)** relating the number of
   distinct training environments to test-time failure rate — only the qualitative claim was
   verifiable from the abstract.
6. **The exact AlphaStar PFSP exponent** (`w_i ∝ (1 − p̂_i)^{1/2}` vs `(1−x)^p`) — quoted from
   secondary sources only; the Nature methods PDF was not read directly.
7. **OpenAI Five's quality-score update rule and its η** — the main text confirms the 80/20
   split and softmax-over-quality sampling; the rule itself is in Appendix N, not verified.
8. **Author lists** for arXiv 2408.01072 (self-play survey), arXiv 2306.05727 (diverse replay),
   arXiv 2107.01348, and the *Scientific Reports* 2025 grid pursuit-evasion paper were not
   individually confirmed; titles, venues and URLs are correct.
9. **Verbatim Sutton & Barto section text.** Section numbers (§3.3–3.4, §5.3, §5.4) and the
   substance of the exploring-starts assumption are confirmed via multiple independent
   secondary sources, but the book's exact wording was not quoted from the PDF.
