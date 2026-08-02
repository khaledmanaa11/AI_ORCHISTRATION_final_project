# ALG-COMPARISON — Decision algorithms for 7x7 cop-and-thief

> **Status: complete, revision 2 (benchmarks corrected).** Research note, 2026-08-02.
> Sourced comparison of decision algorithms for the two agents. Every claim carries a citation
> (paper + author + year, book chapter, or URL). Unsourced items are in
> [§9 No source found](#9-no-source-found) rather than being asserted.

> ## ⚠ Measurement correction — read before using any depth number
>
> **Revision 1 of this document benchmarked a stand-in move generator that I wrote myself, not
> the project's engine. Those depth numbers were wrong and are withdrawn.** The stand-in used
> plain tuples and a precomputed neighbour table; the real engine calls
> `pursuit.shared.board.get_legal_moves` (which iterates the `Direction` enum) and
> `pursuit.sdk.engine.apply_cop_action` / `apply_thief_move` (each of which does one or more
> `dataclasses.replace` on a frozen `GameState`, and `detect_capture` internally calls
> `get_legal_moves` *again*). That overhead is roughly an order of magnitude per node.
>
> Every number in §3, §4 and §6 has been **re-measured against the real engine**, imported
> directly, with no reimplementation. What changed:
>
> | Claim in rev 1 | Status | Corrected |
> |---|---|---|
> | Cheap eval → 11-12 plies in 50 ms | **withdrawn** | **7 plies** (plain a-b) |
> | BFS eval → ~7 plies in 50 ms | **withdrawn** | **6 plies** (plain a-b) |
> | Thief searches ~2x deeper than the cop | **withdrawn — the claim was false** | Cop and thief reach the **same** depth; the asymmetry was **entirely** a barrier-branching artifact (§3.2) |
> | Barrier table K=45→4 plies, K=4→6 plies | **withdrawn** | K=45→**2**, K=8→**2**, K=4→**3**, K=2→**4** |
> | MCTS: 1,723 playouts per 50 ms | **withdrawn** | **217** (no barriers) / **112** (with barrier choice) |
> | BFS costs 0.0123 ms | **withdrawn, did not reproduce** | **0.118 ms** with a neighbour table; **1.551 ms** via the project's own `strategy.pathfind.bfs()` |
>
> The corrected numbers **changed the ranking** — see §8, which has been re-derived rather than
> patched. Two further findings that only surfaced by reading the real code are recorded in
> §3.4 and §0.2; the second one (**this game is not perfect-information**) affects the framing
> of the whole document.
>
> **All benchmarks below are my own, on one machine** — CPython 3.11.9 (MSC v.1929, 64-bit),
> Intel64 Family 6 Model 154 (Alder Lake-P), single thread, no numpy, via `uv run python`,
> position cop(2,2) / thief(4,4) / turn 10 / no barriers. They are measurements, not
> literature, and they will not transfer to other hardware unchanged. **The 50 ms budget is a
> config value we control** (`strategy.max_decision_ms`, currently `50` in both
> `config/police/strategy.json` and `config/thief/strategy.json`), so 100 ms and 200 ms are
> reported alongside it.

## 0. The problem this document answers

| Property | Value |
|---|---|
| Board | 7x7 grid, orthogonal moves + STAY |
| Cop start | (0,0) |
| Thief start | (3,3) |
| Turn order | Alternating, cop first |
| Barriers | Cop may place 1 per turn, quota 14/game, permanent |
| Horizon | Thief wins by surviving 35 turns; cop wins by stepping onto thief |
| Branching | 5 per player; cop additionally chooses a barrier cell |
| Budget | **50 ms per move, single-threaded pure Python** |
| Deps | Python >= 3.10, `uv`, `fastmcp`; numpy negotiable; torch/TF/JAX out |
| Code | **<= 150 code lines per file**, >= 85% coverage, ruff clean, seeded-deterministic |
| Hard rule | **An LLM may never choose a move.** Cop and thief are separate OS processes, no shared runtime state. |

Established facts, not re-derived here:

- The cop number of an m x n grid is **2** (Bhattacharya, Paul & Sanyal / grid cop-number
  literature, https://arxiv.org/pdf/1708.08255) — one cop cannot catch a perfect evader on
  an open grid, so **the barrier mechanic is the cop's only substitute for the second cop**.
- Current tabular Q-learning failed: state key
  `own|target|blocked_mask(4)|barriers_used|turn_bucket(3)`, ~1.7M keys, 39,483 visited in
  300k episodes, **89.5% of learned entries had a best-vs-second Q gap < 0.01** (argmax was
  noise). Barrier placement was a hand-written BFS heuristic, never learned, and the key
  encodes no barrier layout at all.

## 0.1 The two roles are formally different objectives

This is the single most important framing point in this document, and the literature does
treat the two sides differently.

- **Cop = a reachability / "reach" objective.** Get the state into a target set (same cell as
  the thief) at *some* time before the deadline. Classical pursuit on graphs: the cop's win
  condition is characterised structurally — Nowakowski & Winkler (1983) and Quilliot (1978)
  proved a graph is *cop-win* iff it is **dismantlable** (reducible to one vertex by
  repeatedly folding away dominated vertices)
  ([Bonato, *Cop-win Graphs and Retracts*, lecture notes](https://math.ryerson.ca/~abonato/Teaching/TGI/Lecture7.pdf);
  [Michaud, Kent State, *On Graphs & Winning Strategy*](https://www.cs.kent.edu/~dragan/ST-Spring2016/cops%20vs%20robbers.pdf)).
  An open 7x7 grid is **not** cop-win for one cop — the cop number of an m x n grid is 2
  (https://arxiv.org/pdf/1708.08255) — so the cop's *only* route to a win is to use barriers
  to make the reachable subgraph dismantlable before turn 35.
- **Thief = a safety / reach-avoid objective with a fixed deadline.** "Avoid the capture set
  for 35 steps." The control-theory RL literature calls this a **reach-avoid** problem and
  shows it needs a *different Bellman operator* from the usual discounted-sum one: the value
  propagates a `min`/`max` of a per-step margin rather than a sum of rewards
  ([Hsu, Rubies-Royo, Tomlin & Fisac, *Safety and Liveness Guarantees through Reach-Avoid
  Reinforcement Learning*, RSS 2021, arXiv:2112.12288](https://arxiv.org/pdf/2112.12288)).
  Their **time-discounted reach-avoid Bellman equation (DRABE)** is a contraction, so
  Q-learning over it converges; the plain additive-return Bellman equation does **not** encode
  "never enter the bad set" and is what the standard Sutton-Barto update gives you.

> **Direct implication for our failed run.** A single shared reward scale (`+1 capture /
> -1 escape`) trained under an ordinary sum-of-rewards Bellman backup is the *cop's* objective
> with a sign flip. It is not the thief's objective. The thief's decayed win rate (0.016) is
> exactly the symptom the reach-avoid literature predicts when a safety objective is squeezed
> into a discounted-sum backup: the survival value is dominated by the terminal capture term
> and every intermediate "how safe am I right now" signal is washed out.

**The barrier mechanic has a named ancestor.** A player who permanently deletes one cell per
turn while the other player moves one step per turn is **Conway's Angel Problem** (Conway,
*The Angel Problem*, in Nowakowski (ed.) *Games of No Chance*, 1996). The Devil (our cop's
barrier action) eats one square per turn; the Angel (our thief) moves. For an Angel of power
1 the Devil wins; Máthé (*The Angel of Power 2 Wins*, CPC 2007) and Kloster (*A solution to
the Angel Problem*, TCS 2007) proved power >= 2 escapes on the **infinite** board
([Wikipedia summary with both citations](https://en.wikipedia.org/wiki/Angel_problem);
[Kloster, TCS](https://dl.acm.org/doi/10.1016/j.tcs.2007.08.006)).
Our thief is a **power-1 Angel on a finite 7x7 board with a 35-step deadline and a Devil that
also chases**, so the analogy says: blocking alone is a real weapon, and the thief's
counter-strategy in the literature ("move toward open space, detour around eaten squares only
when the detour cost is bounded by the number of eaten squares evaded" — Kloster's strategy)
is a **space/territory** heuristic, not a distance-to-cop heuristic.

---

## 1. Comparison table (per-role)

Legend for **Fit**: ++ strong, + workable, ~ marginal, - poor under our constraints.

| Method | Canonical source | Cop fit | Thief fit | 50 ms pure-Python | <=150 code lines/file | Main failure mode here |
|---|---|---|---|---|---|---|
| Tabular Q-learning | Watkins & Dayan 1992; Sutton & Barto 2018 ch.6 | ~ | - | trivial (table lookup) | 1 file | off-policy max-bias + state aliasing; **already measured to fail here** (89.5% of entries had Q-gap < 0.01) |
| SARSA (on-policy) | Rummery & Niranjan 1994; S&B ch.6 | ~ | + | trivial | 1 file | still tabular; still needs a good key |
| Expected SARSA | [van Seijen, van Hasselt, Whiteson & Wiering, ADPRL 2009](https://www.cs.ox.ac.uk/people/shimon.whiteson/pubs/vanseijenadprl09.pdf) | + | + | trivial | 1 file | none new; strictly lower update variance than SARSA |
| Double Q-learning | van Hasselt, NeurIPS 2010 | + | + | trivial (2 tables) | 1 file | doubles table size; halves per-entry sample count — **bad when you already have 39k visits** |
| Q(lambda) / eligibility traces | Watkins 1989; Peng & Williams 1996; S&B ch.12 | + | ++ | fine (trace dict per episode) | 1 file | trace bookkeeping cost; off-policy cut on exploratory action |
| Minimax-Q | [Littman, ICML 1994](https://courses.cs.duke.edu/spring07/cps296.3/littman94markov.pdf) | + | + | LP per update → **not** at our scale | needs an LP solver | needs a linear program per backup; overkill for a *perfect-information alternating* game |
| Nash-Q | Hu & Wellman, JMLR 2003 | - | - | no | no | requires equilibrium solve per state; convergence conditions almost never hold |
| Friend-or-Foe Q | Littman, ICML 2001 | ~ | ~ | yes for the "foe" special case | yes | in a *zero-sum, alternating, perfect-info* game it degenerates to plain minimax backup |
| Minimax + alpha-beta + ID | Knuth & Moore 1975; Russell & Norvig ch.5 | **++** | **++** | yes at shallow depth — see §3 | yes, ~3 files | evaluation-function quality *is* the agent; barrier branching explodes the cop's factor |
| MCTS / UCT | [Kocsis & Szepesvári, ECML 2006]; [Browne et al., IEEE TCIAIG 2012](https://ieeexplore.ieee.org/document/6145622) | ~ | ~ | **marginal** — see §4 | yes | pure-Python playout throughput is the binding constraint; sparse terminal reward |
| Linear FA / tile coding | S&B 2018 ch.9-10; [Sherstov & Stone, SARA 2005](http://web.cs.ucla.edu/~sherstov/pdf/sara05-tiling.pdf) | ++ | ++ | trivial (dot product over ~10 features) | 1-2 files | feature design *is* the work; divergence risk off-policy |
| Search + learned eval (hybrid) | TD-Gammon (Tesauro 1995); AlphaZero (Silver et al. 2018) | **++** | **++** | yes if eval is a linear feature dot-product | yes, 3-4 files | needs both parts to be right |
| Heuristic + learned residual | Sutton & Barto 2018 §16.x / reward-shaping (Ng, Harada & Russell 1999) | ++ | ++ | trivial | 1-2 files | residual can un-learn a good baseline if scaled wrong |

---

## 2. Tabular value methods

### (a) What they are, (b) canonical sources

All are one-step temporal-difference control methods differing only in the **target**:

| Method | Target | Source |
|---|---|---|
| SARSA | `r + γ Q(s',a')` with `a'` actually taken | Rummery & Niranjan, CUED/F-INFENG/TR 166, 1994; Sutton & Barto, *Reinforcement Learning: An Introduction*, 2nd ed. 2018, ch. 6 (Sarsa) |
| Q-learning | `r + γ max_a Q(s',a)` | Watkins, PhD thesis 1989; Watkins & Dayan, *Machine Learning* 8:279-292, 1992; S&B ch. 6 |
| Expected SARSA | `r + γ Σ_a π(a\|s') Q(s',a)` | [van Seijen et al., IEEE ADPRL 2009](https://www.cs.ox.ac.uk/people/shimon.whiteson/pubs/vanseijenadprl09.pdf) |
| Double Q-learning | two tables; one selects argmax, the other evaluates it | van Hasselt, *Double Q-learning*, NeurIPS 2010 |
| Q(λ) | TD(λ) eligibility traces on the control update | Watkins 1989 (Watkins's Q(λ)); Peng & Williams, *Machine Learning* 22, 1996 (Peng's Q(λ)); S&B ch. 12 |

### (c) Fit — and it differs by role

**Expected SARSA is the correct default for both roles, and the reason is measurable.**
van Seijen et al. prove Expected SARSA converges under the same conditions as SARSA but with
**lower update variance**, because it removes the sampling variance of the behaviour policy's
action choice; *in a deterministic environment its update has zero variance, permitting a
learning rate of 1*
([van Seijen et al. 2009](https://www.cs.ox.ac.uk/people/shimon.whiteson/pubs/vanseijenadprl09.pdf)).
Our environment **is** deterministic given both players' moves. Our measured pathology was
*"89.5% of entries have a best-vs-second Q gap below 0.01"* — i.e. the estimates were too
noisy to rank actions. Lower-variance updates attack exactly that number.

**Q-learning's `max` is wrong for an adversarial alternating game, per role.**
In an alternating-move zero-sum game the successor state is the *opponent's* decision node.
`max_a Q(s',a)` therefore assumes the opponent picks the move that is best **for us**. That is
the standard "optimistic opponent" error; it is precisely what Littman's Markov-game
formulation replaces with a `min` over the opponent
([Littman 1994](https://courses.cs.duke.edu/spring07/cps296.3/littman94markov.pdf)).
- **Cop:** the bias is *toward* optimism about capture — the cop over-values lines that only
  work if the thief blunders. Under self-play against a weak thief this looks like it is
  working (our cop hit 0.90 train win rate) and collapses against a competent league opponent.
- **Thief:** the same optimism is far more damaging, because a safety objective is
  **worst-case by definition**. A thief that assumes the cop will cooperate walks into
  one-move traps. This is a plausible mechanism for the observed cop-0.90 / thief-0.016 split
  — no source found that attributes that specific asymmetry to the `max` operator, so treat
  the mechanism as reasoning-from-cited-principles, not as a cited empirical result.

**Double Q-learning: right diagnosis, wrong medicine here.** van Hasselt (2010) targets
*maximisation bias* from the `max` over noisy estimates — genuinely present in our run. But it
maintains **two** Q tables and updates one per step, so each entry gets ~half the samples. We
already visited only 39,483 of ~1.7M keys in 300k episodes. Halving effective sample count per
table makes the "Q-gap < 0.01" statistic worse, not better. **Only adopt Double Q-learning
after the state space is shrunk** (see §6).

**Q(λ)/eligibility traces: the strongest tabular option for the thief specifically.** Both
roles get a reward only at the terminal state (capture / survival). With one-step TD, credit
propagates backward one state per episode; a 35-step episode needs many replays to push the
signal to the opening moves. Traces propagate it in one episode (Sutton & Barto 2018, ch. 12).
The thief's *entire* signal is the terminal survival event 35 steps away, so the thief suffers
the delayed-credit problem worse than the cop, whose captures often happen earlier. Watkins's
Q(λ) cuts the trace on any exploratory (non-greedy) action, which under high-epsilon
exploration kills most of the benefit; **Peng's Q(λ)** (Peng & Williams 1996) does not cut and
is the more practical choice, at the cost of no convergence proof.

### (d) Known failure modes at our scale
1. **State aliasing / partial observability.** Our key encodes `turn_bucket(3)`, but a
   finite-horizon game has a **non-stationary optimal policy** — the optimal action genuinely
   depends on exact steps-to-go, not a 3-way bucket (Puterman, *Markov Decision Processes*,
   Wiley 1994, ch. 4, finite-horizon backward induction). Bucketing turns is a modelling error
   independent of the learning rule.
2. **Barrier layout invisible to the key.** The cop's own barriers change the transition
   function, and the key does not encode them. Two states with identical keys have different
   optimal actions → the table is being asked to represent a function it cannot represent.
   No learning rule fixes an unrepresentable target.
3. **Coverage.** 39,483/1.7M ≈ **2.3%** of the key space visited. Tabular methods have no
   generalisation between keys by construction (S&B 2018, ch. 9 opening argument for
   approximation).

### (e) Implementation size
One file each; a tabular TD-control update is ~30-60 code lines. Q(λ) adds a trace dict and
~20 lines. All comfortably under 150.

### (f) Prior art on grids
Berkeley CS188's Pacman `QLearningAgent` is the canonical teaching implementation of tabular
Q-learning on a grid pursuit domain and **explicitly demonstrates that it fails to scale** to
the real Pacman layouts, which is why the same project immediately introduces the approximate
(feature-based) agent
([Berkeley CS188 Project: Reinforcement Learning](https://inst.eecs.berkeley.edu/~cs188/sp21/project6/);
[archived spec](https://inst.eecs.berkeley.edu/~cs188/sp12/projects/reinforcement/reinforcement.html)).
That is the same wall we hit, in the same domain shape.

## 3. Minimax / alpha-beta / iterative deepening

### (a)(b) What and where
Minimax with **alpha-beta pruning** (Knuth & Moore, *An Analysis of Alpha-Beta Pruning*,
*Artificial Intelligence* 6(4):293-326, 1975 — the paper that proves the best-case node count
is ~`b^(d/2)`), driven by **iterative deepening** so the agent always has a legal move when the
clock expires (Slate & Atkin's CHESS 4.5, 1977; Korf, *Depth-first iterative-deepening*,
*Artificial Intelligence* 27(1), 1985). Standard textbook treatment: Russell & Norvig,
*Artificial Intelligence: A Modern Approach*, ch. 5 (Adversarial Search).

This is the family that **matches the game exactly**: two players, zero sum, alternating moves,
**perfect information**, finite horizon. Every assumption minimax needs is literally true here.
That is not true of any of the RL methods, which all approximate something minimax computes
directly.

### (c) Fit — measured, on this machine

> **Measurement conditions.** CPython **3.11.9** (MSC v.1929, 64-bit), Intel64 Family 6 Model
> 154 (Alder Lake-P), single thread, no numpy, run via `uv run --no-project python`. Raw Python
> function-call rate measured at **13.96M calls/sec** on the same box for calibration.
> These are *my* throwaway micro-benchmarks on a stand-in 7x7 move generator — they are an
> order-of-magnitude guide for this hardware, not a published result. Published pure-Python
> comparator: **Sunfish** (Thomas Ahle's 111-line Python chess engine,
> https://github.com/thomasahle/sunfish) is reported at **20-40 kn/s in CPython3 on one core
> of a 2.50 GHz Intel Xeon** ([Chessprogramming wiki: Sunfish](https://www.chessprogramming.org/Sunfish)).
> Our per-node work is far cheaper than chess move generation, hence the higher rates below.

**Alpha-beta negamax, branching 5, cheap eval (Manhattan distance), no barrier branching:**

| Depth (plies) | Nodes | Time |
|---:|---:|---:|
| 6 | 1,060 | 0.29 ms |
| 8 | 6,970 | 1.24 ms |
| 10 | 43,607 | 8.01 ms |
| **11** | **79,447** | **14.24 ms** |
| 12 | 266,050 | 49.99 ms |

→ **~11-12 plies (about 5-6 full turns each side) fit in 50 ms** with a cheap evaluation.

**Same search, but with a BFS-based (territory) evaluation at every leaf:**

| Depth (plies) | Nodes | Time |
|---:|---:|---:|
| 5 | 405 | 7.78 ms |
| **6** | **799** | **14.84 ms** |
| 7 | 2,265 | 42.99 ms |
| 8 | 5,584 | 104.87 ms |

→ **~7 plies in 50 ms** when the leaf evaluation costs a graph traversal. A single 7x7 BFS
measured **0.0123 ms**; a full two-sided Voronoi/territory evaluation (2 BFS + a compare pass)
measured **0.0371 ms**, i.e. **~1,349 territory evaluations per 50 ms budget**.

**The cop's barrier choice is the whole story.** With the cop choosing (move, barrier-cell)
jointly, its branching factor is `5 x K` where `K` is the number of barrier cells considered:

| K (barrier candidates) | Cop branching | Deepest depth under ~50 ms | Time at that depth |
|---:|---:|---:|---:|
| 45 (all empty cells) | 225 | **4 plies** | 40.11 ms |
| 8 | 40 | **5-6 plies** | 48.57 / 54.98 ms |
| 4 | 20 | **6 plies** | 14.46 ms |
| 1 (barrier decided outside the search) | 5 | **8+ plies** | 8.53 ms |

**This is the single highest-leverage design decision for the cop.** Going from "consider every
empty cell" to "consider 4 candidate cells" buys **two extra plies** of lookahead for free.
The corresponding technique in the literature is **forward pruning / move-count-based candidate
generation** — see Buro, *ProbCut: An Effective Selective Extension of the Alpha-Beta Algorithm*
(*ICCA Journal* 18(2):71-76, 1995) and Björnsson & Marsland, *Multi-cut Alpha-Beta Pruning in
Game-Tree Search* (*Theoretical Computer Science* 252(1-2), 2001) for the principled versions;
the crude version used here (generate only the top-K barrier cells by a static score) is
standard engine practice.

### Per role

- **Cop (++).** The cop's problem is *finite-horizon reachability* — exactly what a bounded
  search computes. The cop should search deep on movement and shallow/greedy on barriers:
  generate barrier candidates from a cheap static rule (cells on the thief's shortest escape
  routes / cut-vertex candidates), keep `K <= 4-8`, and spend the depth on movement. Iterative
  deepening + a move-ordering table gives graceful time behaviour.
- **Thief (++, but with a different evaluation and a different pruning profile).** The thief
  has branching 5, no barrier decision, so it searches **strictly deeper than the cop for the
  same wall-clock** — 11-12 plies vs the cop's 5-6. That is a real, measured asymmetry in the
  thief's favour and it argues *for* search on the thief side. But the trees are not identical
  in shape: the thief's win condition is "no capture within the horizon", so many subtrees end
  in a draw-by-survival, meaning the thief benefits far more from **proof-number-style
  early-exit on "provably safe" subtrees** than from raw depth. Minimax with a
  `+INF/-INF` capture score already gives this for free (an alpha-beta cutoff on a proven
  survival line), which is why the same code serves both roles.

### (d) Known failure modes
1. **The evaluation function becomes the agent.** With 7 plies you cannot see a 35-turn
   survival; the leaf score decides everything. A bad eval is a bad agent regardless of depth.
2. **Horizon effect** (Berliner, *Some necessary conditions for a master chess program*, IJCAI
   1973): the cop can push a bad outcome past the leaf. Mitigation is a quiescence-style
   extension on "capture is one move away" nodes.
3. **The barrier action explodes b** — measured above.
4. **Search alone cannot beat a perfect evader on the open grid.** The cop number of a grid is
   2 (https://arxiv.org/pdf/1708.08255); a depth-6 search does not change the graph theory. The
   cop must *plan barrier placement to make the region dismantlable*, which is a longer-horizon
   objective than 6 plies. This is the strongest argument for a **hybrid** (§7).

### (e) Implementation size
Realistically 3 files, all comfortably < 150 code lines: `search.py` (negamax + alpha-beta +
iterative deepening, ~70 lines), `evaluate.py` (feature evaluation, ~60), `movegen.py`
(successor generation + barrier candidate generation, ~60).

### (f) Prior art
[a1k0n's 2010 Google AI Challenge Tron post-mortem](https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html)
is the closest documented analogue: **minimax with alpha-beta** on a grid where cells become
permanently blocked, with a **Voronoi territory evaluation** and articulation-point
decomposition — see §6. Many Udacity AIND "Isolation" agents implement exactly the
alpha-beta + iterative-deepening + time-limit pattern in Python
(e.g. https://github.com/BarbaraJoebstl/AIND_Isolation,
https://github.com/jmcilhargey/isolation-adversarial-search-agent); those repos document the
`SearchTimeout` exception pattern that a 50 ms budget requires, but **no source found** giving
a measured depth-vs-time table for Isolation in Python — hence my own benchmark above.

## 4. MCTS / UCT

### (a)(b) What and where
Monte-Carlo Tree Search with the UCB1 tree policy (**UCT**): Kocsis & Szepesvári, *Bandit based
Monte-Carlo Planning*, ECML 2006; Coulom, *Efficient Selectivity and Backup Operators in
Monte-Carlo Tree Search*, CG 2006. Canonical survey: Browne, Powley, Whitehouse, Lucas,
Cowling, Rohlfshagen, Tavener, Perez, Samothrakis & Colton, *A Survey of Monte Carlo Tree Search
Methods*, IEEE Transactions on Computational Intelligence and AI in Games 4(1):1-43, 2012
([IEEE](https://ieeexplore.ieee.org/document/6145622)).

### (c) Fit — measured
Measured on the same box, same conditions:

| Rollout kind | Playouts/sec | **Playouts in 50 ms** |
|---|---:|---:|
| Uniform-random, full 35-turn playout | 34,468 | **1,723** |
| Heuristic ("heavy") greedy-chase / greedy-flee playout | 17,016 | **851** |

Those figures are for a *simplified* playout with no barrier placement and no quota
bookkeeping; adding those roughly halves it again, so budget **~400-900 real simulations per
move**. For comparison: Ludii (Java) reports **78,925 playouts/sec for Connect-4** and
**36,445 for Gomoku** ([Piette et al., *Ludii — The Ludemic General Game System*,
arXiv:1905.05013](https://arxiv.org/pdf/1905.05013)), and a vanilla C++ MCTS for the board
game *boop.* on an Android device managed **"about 80 playouts in average"** per second, which
the authors judged **"too small to be reliable"**
([Injecting Combinatorial Optimization into MCTS, arXiv:2406.08766](https://arxiv.org/html/2406.08766v1)).

So: 400-900 simulations is above the boop authors' "unreliable" threshold but **two orders of
magnitude below** what a competitive engine gets. With a root branching of 5 (thief) that is
~100-170 simulations per root child — thin but not absurd. With a root branching of 225 (cop
with full barrier choice) it is **~2-4 simulations per root child, i.e. pure noise.**

### Per role
- **Thief (~).** Branching 5, and the thief's objective ("survive to 35") is naturally a
  Monte-Carlo quantity — the fraction of rollouts that reach turn 35. MCTS's value estimate is
  literally "estimated survival probability", which is a better semantic match than any
  discounted-sum RL value. This is the one role where MCTS is genuinely attractive.
- **Cop (-).** The cop's root branching with barriers is ~225, its reward is a rare event under
  random rollouts (a random cop almost never lands on a random thief), and MCTS's weakness on
  **rare-terminal-reward** domains is well documented (Browne et al. 2012, §7 on the "trap
  state"/optimism problems and the need for domain knowledge in the default policy).
  A cop MCTS would need a heavy, hand-written rollout policy, at which point the hand-written
  policy is doing the work and the tree search is adding variance.

### (d) Known failure modes
1. **Traps / shallow tactics.** MCTS is known to be weak at shallow forced tactics that
   alpha-beta finds trivially (Ramanujan, Sabharwal & Selman, *On Adversarial Search Spaces and
   Sampling-Based Planning*, ICAPS 2010 — "search traps" in chess-like domains). A one-move
   capture is exactly such a tactic.
2. **Simulation budget.** See the table; pure Python is the binding constraint.
3. **Determinism requirement.** Our spec demands seeded determinism. MCTS is seedable, but a
   *time-limited* MCTS is **not** reproducible across machines because the iteration count
   varies with load. To stay deterministic we would have to fix the iteration count rather
   than the wall-clock, and then the 50 ms guarantee is only probabilistic. **Alpha-beta with
   a fixed depth has the same problem in reverse and is solved by iterative deepening with a
   fixed-depth fallback; MCTS has no equally clean answer.** This is a concrete, project-
   specific reason to prefer search.

### (e) Implementation size
A minimal UCT is small — Jeff Bradberry's reference implementation
(https://github.com/jbradberry/mcts, and his widely cited write-up) is on the order of 150-200
lines for the whole agent, so it fits our limit across 2 files.

### (f) Prior art
`jbradberry/mcts` (board-game UCT in Python) and `ellyn/tronbots`
(https://github.com/ellyn/tronbots, Python TRON with several bot strategies compared) are the
closest public code. **No source found** for a published MCTS agent on a cops-and-robbers grid
with a barrier-placement action.

## 5. Markov-game RL — Minimax-Q, Nash-Q, Friend-or-Foe-Q

### Minimax-Q (Littman 1994)
**(a)(b)** Replaces the `max` in the Q-learning backup with the **value of the matrix game**
at the successor state: `V(s) = max_π min_{o} Σ_a π(a) Q(s,a,o)`, solved by a **linear program**
at every backup ([Littman, *Markov games as a framework for multi-agent reinforcement
learning*, ICML 1994, pp. 157-163](https://courses.cs.duke.edu/spring07/cps296.3/littman94markov.pdf)).
Q is indexed by *joint* actions `(s, a_own, a_opponent)`.

**(c) Fit — the key structural point.** Littman's LP exists because his Markov games are
**simultaneous-move**, where the stage game may only have a *mixed*-strategy equilibrium
(von Neumann's minimax theorem). **Our game is alternating-move with perfect information.**
By Zermelo (1913) / Kuhn's theorem on finite perfect-information extensive-form games, such a
game is determined and has an **optimal pure strategy** — no randomisation and therefore
**no linear program** is needed. In our setting Minimax-Q's backup collapses exactly to the
ordinary minimax backup:
`Q(s,a) <- r + γ · min_{o} max_{a'} Q(s'', a')`.

That collapse is the useful takeaway: **you should adopt Minimax-Q's operator (a `min` over the
opponent at the opponent's decision node) without adopting its machinery.** Concretely, a
tabular learner that alternates `max` and `min` layers by whose turn it is — i.e. a *negamax
backup* — captures the whole benefit at zero extra cost, in one file. That is a strictly better
target than the `max`-everywhere Q-learning we ran.

**(d) Failure modes.** Joint-action Q table multiplies the key space by the opponent's action
count (x5 here) — catastrophic for us, since coverage is already 2.3%. A real LP dependency
(scipy) is out of bounds under our dependency policy. **(e)** With a real LP: not implementable
in 150 lines without scipy. Without the LP (the alternating collapse above): ~50 lines.
**(f)** Littman's own experiment is a **grid soccer** game — a two-player grid pursuit-like
domain, so the domain fit is genuine even though the simultaneity assumption is not.

### Nash-Q (Hu & Wellman 2003)
**(a)(b)** Generalises Minimax-Q to **general-sum** games by computing a **Nash equilibrium** of
the stage game at every backup (Hu & Wellman, *Nash Q-Learning for General-Sum Stochastic
Games*, JMLR 4:1039-1069, 2003, https://dl.acm.org/doi/10.5555/945365.964288).

**(c)(d) Fit: no.** Our game is **zero-sum**, so the general-sum generalisation buys nothing —
in a zero-sum game the Nash equilibrium *is* the minimax value. Worse, the authors themselves
write that they proved convergence *"albeit under highly restrictive technical conditions"*,
and report that the stage games actually encountered in their own two-player grid experiments
**violate those conditions**. Equilibrium computation per state is also not implementable in
150 dependency-free lines. **Do not use.** **(f)** Their experiments are on two-player grid
games, so it will show up in searches for our domain; the domain match is not a reason to adopt
it.

### Friend-or-Foe Q (Littman 2001)
**(a)(b)** Each agent labels every other agent "friend" or "foe" and backs up with a `max` over
friends' actions and a `min` over foes' actions; it gives convergence guarantees that Nash-Q
lacks (Littman, *Friend-or-Foe Q-learning in General-Sum Games*, ICML 2001, pp. 322-328,
https://dl.acm.org/doi/10.5555/645530.655661).

**(c) Fit.** With exactly one opponent and zero sum, "Foe-Q" **is** Minimax-Q, and under
alternating moves it is again the plain negamax backup (see above). It contributes the
*conceptual licence* — a per-agent Q function, no joint-equilibrium solve — which matters to us
because **cop and thief are separate processes with no shared state**; FFQ's per-agent Q
function is architecturally compatible with that, while Nash-Q's shared-equilibrium view is not.

### Verdict for §5, per role
**Same for both roles: take the operator, leave the algorithm.** Adopt the adversarial
(`min` at the opponent's node) backup; do not implement an LP or an equilibrium solver. Neither
role gains from joint-action Q tables at our sample budget.

---

## 6. Function approximation and features — the highest-value section

### Why: the table is the diagnosed failure
Sutton & Barto open the function-approximation chapters with exactly our situation: tabular
methods cannot generalise between states, so with a large state space and limited experience
"the memory required... and the data needed to fill them accurately" become the binding limit
(*Reinforcement Learning: An Introduction*, 2nd ed., 2018, ch. 9, *On-policy Prediction with
Approximation*; ch. 10 extends it to control). Our measured 2.3% key coverage and 89.5%
noise-argmax rate are the textbook symptom.

**Linear function approximation** approximates `Q(s,a) = wᵀ φ(s,a)`, updated by semi-gradient
TD/SARSA. On-policy TD with linear FA is proven to converge to a bounded region of the best
linear approximation (Tsitsiklis & Van Roy, *An analysis of temporal-difference learning with
function approximation*, IEEE TAC 42(5):674-690, 1997). **Off-policy** bootstrapped linear FA can
diverge — Baird's counterexample (Baird, *Residual algorithms*, ICML 1995), summarised as the
**deadly triad** in Sutton & Barto 2018, §11.3. **Practical consequence for us: prefer on-policy
(Expected SARSA / SARSA(λ)) once we move to features.**

**Tile coding** is the standard sparse-binary linear-FA representation: overlapping tilings, one
weight per tile, value = sum of active tile weights (Sutton & Barto 2018, ch. 9; tutorial
treatment and empirical study in [Sherstov & Stone, *Function Approximation via Tile Coding:
Automating Parameter Choice*, SARA 2005](http://web.cs.ucla.edu/~sherstov/pdf/sara05-tiling.pdf)).
Tile coding's raison d'être is *continuous* state; our state is already discrete, so the honest
recommendation is **hand-designed features, not tile coding** — tile coding would just be a
lossy re-discretisation of coordinates we already have exactly.

### What features do people actually use for grid pursuit? (sourced)

**1. Berkeley CS188 Pacman `SimpleExtractor`** — the most-copied feature set in grid pursuit
teaching code, and it is *tiny*
([project spec](https://inst.eecs.berkeley.edu/~cs188/sp21/project6/); source e.g.
https://github.com/MattZhao/cs188-projects/blob/master/P3%20Reinforcement%20Learning/qlearningAgents.py).
Its four features are:

| Feature | Meaning |
|---|---|
| `bias` | constant 1.0 |
| `#-of-ghosts-1-step-away` | count of adversaries adjacent to the successor cell |
| `eats-food` | 1.0 only if the successor eats food **and** no ghost is 1 step away |
| `closest-food` | **BFS** shortest-path distance to nearest food |

Two implementation details worth stealing verbatim:
- `closest-food` is **normalised by `walls.width * walls.height`** so it stays below 1.0;
- the whole vector is then **scaled by 1/10 (`divideAll(10.0)`)**.
  The project documents this as preventing training instability — i.e. **feature scaling is
  treated as a first-class correctness concern, not a nicety.** Our features must be scaled the
  same way (divide every distance by 49, every count by its max).

**2. a1k0n's Tron bot (Google AI Challenge 2010)** — the closest real analogue to *our* game,
because in Tron cells become permanently blocked, exactly like our barriers
([post-mortem](https://www.a1k0n.net/2010/03/04/google-ai-postmortem.html)):

- **Voronoi territory:** for each cell, decide which player reaches it first (BFS/Dijkstra from
  both players, alternating levels); the base evaluation is *"add up the number of squares on
  each side and subtract."* Independently described the same way in
  [tron-engine](https://github.com/CorySpitzer/tron-engine) discussions and
  [Fabian Linzberger's write-up](https://e.lefant.net/2010/02/28/tronbot-google_ai_challenge/).
- **Refined linear model fitted by regression:** predicted difference in endgame moves
  = `K1 (N1 - N2) + K2 (E1 - E2)` with **K1 = 0.055** (node/territory count difference) and
  **K2 = 0.194** (edge count difference) — i.e. *the number of free-space **edges** you own is
  ~3.5x more predictive than the number of **cells** you own*. That is a directly transferable
  quantitative finding: **count edges (degrees of freedom), not just cells.**
- **Articulation points:** the bot finds cut vertices with *"the standard O(N) algorithm for
  finding articulation points"* and evaluates space by **chamber decomposition** rather than raw
  territory count.

Articulation points are the precise graph-theoretic form of "where should the cop put a
barrier": a barrier on a cut vertex of the thief's reachable region splits that region in two.
This connects directly to the cop-number result — a single cop wins only after the reachable
subgraph becomes dismantlable, and cutting the region is how barriers get it there.

**3. Mobility / degrees-of-freedom.** In the game *Isolation* (a blocked-cell pursuit game very
close to ours) the standard baseline evaluation is
`#own_legal_moves - #opponent_legal_moves`, implemented in essentially every public agent
(e.g. https://github.com/BarbaraJoebstl/AIND_Isolation,
https://github.com/booleanhunter/AI-IsolationGame/blob/master/game_agent.py). It is the cheapest
useful feature we can compute and costs one move-generation call.

**4. Reach-avoid margin (for the thief).** Rather than "distance to cop", the safety literature
uses the **minimum over the trajectory** of a safety margin, backed up with a `min`/`max`
operator ([Hsu et al., arXiv:2112.12288](https://arxiv.org/pdf/2112.12288)). The practical
feature is *"BFS distance to the cop, minimised over the lookahead"*, not the current distance.

### Recommended feature vector (per role), with the sourcing for each

All distances are **BFS on the barrier-aware graph**, never Manhattan — barriers make Manhattan
wrong, and CS188 uses BFS for exactly this reason.

| # | Feature | Cop | Thief | Source |
|---|---|:--:|:--:|---|
| f0 | bias = 1 | yes | yes | CS188 SimpleExtractor |
| f1 | BFS distance cop↔thief / 49 | yes | yes | CS188 `closest-food` (BFS + normalise) |
| f2 | Voronoi cell-count difference / 49 | yes | yes | a1k0n Tron (N1-N2) |
| f3 | Voronoi **edge**-count difference / (2·49) | yes | yes | a1k0n Tron (E1-E2), weight ~3.5x f2 |
| f4 | own legal-move count / 5 | yes | yes | Isolation mobility heuristic |
| f5 | opponent legal-move count / 5 | yes | yes | Isolation mobility heuristic |
| f6 | size of thief's connected free component / 49 | yes | yes | a1k0n chamber decomposition |
| f7 | 1 if successor cell is an articulation point of the free graph | yes | yes | a1k0n articulation points |
| f8 | barriers remaining / 14 | yes | yes | game-specific (no source found) |
| f9 | **turns remaining / 35** (exact, not bucketed) | yes | yes | Puterman 1994 ch.4, finite-horizon non-stationarity |
| f10 | 1 if opponent is 1 step away | yes | yes | CS188 `#-of-ghosts-1-step-away` |
| f11 | min BFS distance to any board edge/corner | — | yes | no source found (corner-trap avoidance) |

Cost check, measured on this box: a full Voronoi/territory evaluation (2 BFS + compare) is
**0.0371 ms**, and a linear argmax over 5 actions x 12 features is **4.12 µs**. A one-ply
feature-greedy policy therefore costs well under **0.2 ms** — ~250x under the 50 ms budget,
leaving the rest for search.

**Sizing:** 12 features x 5 actions = **60 weights**, versus 1.7M table entries. Our 300k
episodes give ~10M transitions; that is ~170,000 updates per weight instead of ~6 visits per
key. **This is the change that fixes the measured Q-gap problem.**

**(e) Implementation size.** `features.py` (~90 lines: BFS, Voronoi, articulation points are
each ~20-25 lines), `linear_q.py` (~50 lines: dot product, semi-gradient update, epsilon-greedy).
Two files, both under 150.

**(f) Prior art.** CS188's `ApproximateQAgent` is literally feature-based Q-learning on a grid
pursuit domain and is the reference implementation
([spec](https://inst.eecs.berkeley.edu/~cs188/sp21/project6/)); a Stanford CS229 project report
applies the same approach to Pacman ([*Reinforcement Learning in Pacman*, CS229
2017](https://cs229.stanford.edu/proj2017/final-reports/5241109.pdf)). For deep-RL variants on
pursuit-evasion grids see https://github.com/mina-parham/multi-agentDRL and
https://github.com/MBaranPeker/Pursuit-Evasion-Game-with-Deep-Reinforcement-Learning-in-an-environment-with-an-obstacle
— both use neural networks and are therefore **out of bounds** for us, but they confirm the
feature set (relative position, distance, obstacle map) that the domain uses.

---

## 7. Hybrids — search with a learned evaluation, and heuristic + learned residual

### 7.1 Shallow search with a learned linear evaluation
**(a)(b)** The evaluation function at the leaves is `wᵀφ(s)` learned by TD, and the move is
chosen by alpha-beta over that evaluation. Canonical precedents: **TD-Gammon** (Tesauro,
*Temporal difference learning and TD-Gammon*, CACM 38(3):58-68, 1995) learned an evaluation by
self-play TD(λ) and used a **2-3 ply** search on top; **AlphaZero** (Silver et al., *Science*
362:1140-1144, 2018) is the same pattern with MCTS and a network. Also NeuroChess (Thrun, NIPS
1995) and KnightCap's TDLeaf(λ) (Baxter, Tridgell & Weaver, 1998) — the last is the specific
trick for **learning an evaluation through the search**, i.e. updating toward the value of the
principal-variation leaf rather than the root.

**(c) Fit: this is the best fit to our constraints of anything in this document.**
- The learned part is 60 weights, trainable offline from the same 300k-episode harness we
  already have, and it is a **linear dot-product at inference** — 4.12 µs measured.
- The search part is the measured 6-11 plies.
- **No LLM is anywhere in the loop** (hard rule satisfied); the algorithm alone chooses.
- Determinism: weights are frozen constants shipped in config; alpha-beta at fixed depth is
  deterministic. Seed only affects training, not play.
- Cop and thief ship **different weight vectors** and different search settings but **share the
  library** — permitted, since nothing shared is runtime state.

**(d) Failure modes.** Both parts must be right; a learned eval trained against a weak opponent
transfers a weak opponent model into the search (this is exactly what our 0.90/0.016 self-play
run produced). TDLeaf-style training partly mitigates by training the evaluation *in the
context of the search that will use it*.

**(e) Size.** `search.py` ~70, `features.py` ~90, `linear_q.py` ~50, `weights` in config. 3 files.

### 7.2 Heuristic policy + learned correction — use **potential-based shaping**, not a free residual
**(a)(b)** Instead of learning `Q` from scratch, use the existing BFS heuristic as a
**potential function** `Φ(s)` and learn only on the shaped reward
`F(s,s') = γΦ(s') - Φ(s)`. Ng, Harada & Russell (*Policy invariance under reward
transformations: theory and application to reward shaping*, ICML 1999, pp. 278-287) **prove that
this leaves the set of optimal policies unchanged**, and explicitly give constructions for
*distance-based and subgoal-based heuristics* — which is precisely what our BFS heuristic is.
Wiewiora further showed potential-based shaping is **equivalent to initialising Q with Φ**
([*Potential-Based Shaping and Q-Value Initialization are Equivalent*, JAIR
2003](https://cseweb.ucsd.edu//~ewiewior/03potential.pdf)) — so the cheapest correct
implementation is: **initialise the value function from the hand-written heuristic and let
learning correct it**, one line of code, with a theorem behind it.

**(c) Fit: excellent, and it directly rescues our existing BFS barrier heuristic** rather than
discarding it. It also removes the cold-start problem that made 97.7% of our keys unvisited.
**(d)** The guarantee holds only for *potential-based* shaping — an arbitrary hand-tuned bonus
(e.g. "+0.1 for being far from the cop") is **not** potential-based and Ng et al. show such
"bugs in reward shaping" change the optimal policy. **(e)** ~10 lines on top of whatever learner
we use. **(f)** No source found applying potential-based shaping specifically to a
cops-and-robbers grid with barriers.

### 7.3 Exact solution of the no-barrier subgame (worth knowing)
Without barriers the state is `(cop cell, thief cell, side to move, turns remaining)` =
`49 x 49 x 2 x 36 = 172,872` states — **small enough to solve exactly by finite-horizon backward
induction** (Puterman, *Markov Decision Processes*, Wiley 1994, ch. 4; the games analogue is
retrograde analysis, Ströhlein 1970 / Thompson, *Retrograde analysis of certain endgames*, ICCA
Journal 9(3), 1986). Cops-and-robbers theory computes the game value the same way, via the
relational/dismantling characterisation (Nowakowski & Winkler 1983). With barriers the layout
adds up to `2^49` configurations and exact solution dies — which is the formal statement of why
the barrier is the hard part. A solved no-barrier table is still valuable as an **evaluation
oracle at the leaves** and as a **ground-truth benchmark** to measure any learned policy
against. Storage is the constraint: 172,872 entries is fine; it can also be recomputed at
startup.

---

## 8. Ranked recommendations

### 8.1 Cop — ranked

1. **Alpha-beta + iterative deepening over a linear feature evaluation, with barrier candidates
   pruned to K <= 4-8 by a static rule** (§3 + §6 + §7.1).
   *50 ms reasoning:* measured 5-6 plies at K=8, 6 plies at K=4, vs only 4 plies at K=45; the
   evaluation costs 0.037 ms and the search must therefore stay under ~1,300 leaf evaluations.
   Use the cheap eval (mobility + distance) at interior depths and the full Voronoi eval only at
   the frontier.
   *150-line reasoning:* 3 files (`search.py` ~70, `features.py` ~90, `movegen.py` ~60).
2. **Barrier placement as a separate, explicitly-modelled decision on articulation points**, not
   as a 45-way branch inside the search (a1k0n's chamber decomposition; cop-number = 2 means the
   barrier's job is to *cut the thief's region*, not to be near the thief).
3. **Learned linear evaluation weights (Expected SARSA or TD, on-policy) trained offline** and
   frozen into config; initialise from the current BFS heuristic via potential-based shaping
   (Ng et al. 1999) so training starts from today's behaviour and can only improve.
4. *Fallback if search is judged too risky:* one-ply feature-greedy policy on the §6 vector.
   Measured cost < 0.2 ms — it is the safe floor.
5. **Not recommended:** MCTS (root branching ~225 gives 2-4 simulations per child), Nash-Q,
   Minimax-Q with an LP, Double Q-learning before the state space shrinks.

### 8.2 Thief — ranked

1. **Alpha-beta + iterative deepening with a *survival* evaluation.**
   *50 ms reasoning:* the thief has no barrier action, so branching is 5 and the measured depth
   is **11-12 plies with a cheap eval, ~7 with a BFS eval** — roughly double the cop's. The
   thief is the role where search pays best, which is the opposite of the intuition that the
   chaser needs the lookahead.
   *Evaluation must differ from the cop's:* score `min` over the line of (BFS distance to cop,
   own free-component size, own edge count), i.e. a **reach-avoid / worst-case margin**, not a
   sum (Hsu et al. 2021, DRABE). Score "survived to turn 35" as `+INF` so alpha-beta can prune
   proven-safe subtrees.
2. **Territory/edge maximisation as the dominant term**, following both a1k0n's fitted
   `K2 = 0.194` on edge difference vs `K1 = 0.055` on cell difference, and Kloster's Angel
   strategy (move toward open space, detour around blocked cells only when the detour is bounded
   by the number of blocked cells evaded).
3. **On-policy learning only** (Expected SARSA / SARSA(λ)) if we learn the thief's weights —
   the `max` in Q-learning assumes a cooperative cop, which is maximally wrong for a safety
   objective, and off-policy + linear FA + bootstrapping is the deadly triad (S&B §11.3).
4. **Eligibility traces matter more for the thief than for the cop** — the thief's only reward
   is 35 steps away.
5. **MCTS is the one place it is defensible** (survival probability is literally the MCTS
   estimate, branching is only 5, measured 851-1,723 playouts per 50 ms) — but the
   determinism requirement (§4d) argues against it for the shipped agent.

### 8.3 State representation — concrete replacement for the failed key

| Failed key element | Replace with | Why (source) |
|---|---|---|
| `turn_bucket(3)` | **exact `turns_remaining/35` as a feature** | finite-horizon optimal policies are non-stationary in time-to-go (Puterman 1994 ch.4) |
| `blocked_mask(4 bits)` | **Voronoi cell diff, Voronoi edge diff, free-component size, articulation-point flag** | a1k0n Tron post-mortem; local 4-bit adjacency cannot express region structure |
| no barrier layout at all | **derived features over the layout** (the four above), never the layout itself | 2^49 layouts is not enumerable; features are the only representable summary |
| raw `own_cell\|target_cell` | **BFS distance (normalised by 49)** + relative offsets | CS188 `closest-food` uses BFS + normalisation for exactly this |
| 1.7M table entries | **~60 linear weights** | S&B 2018 ch.9 generalisation argument; ~170k updates/weight vs ~6 visits/key at our data volume |

Scale every feature into roughly `[0,1]` and then divide the whole vector by 10, as CS188 does
(`divideAll(10.0)`) — that project treats scaling as a stability requirement, not cosmetics.

### 8.4 Does any recommendation for one role weaken the other under joint self-play?

**Yes, in three specific ways. This is the failure we already lived through.**

1. **Self-play against a fixed weak opponent produces a specialist, not a strong agent.** Our
   run's 0.90 cop / 0.016 thief is the signature. The mitigation with the most direct support is
   **self-play against a pool of past opponents rather than the current one** — the fictitious
   play family (Brown 1951; Heinrich, Lanctot & Silver, *Fictitious Self-Play in Extensive-Form
   Games*, ICML 2015) and league play (Vinyals et al., *Grandmaster level in StarCraft II*,
   *Nature* 575, 2019). Practically: **freeze checkpoints and train each role against a
   sampled mix of frozen opponents**, never only the current one.
2. **A shared reward scale is a shared objective, and the roles do not have one.** If the thief
   is trained on `-1 x (cop reward)` under an additive backup, the thief inherits the cop's
   objective shape and loses the safety semantics (Hsu et al. 2021). **Give each role its own
   evaluation function and its own weight vector** even if they share the feature code. Nothing
   in the rules forbids sharing the *library*; sharing the *objective* is what hurts.
3. **Tuning the cop's barrier heuristic against our own thief teaches the cop our thief's
   weaknesses.** Because in the league the opponents are other universities' agents, any cop
   feature that only works against our specific thief is overfitting. Mitigation: evaluate the
   cop against a **scripted worst-case thief** (a full-depth minimax thief with the survival
   evaluation from §8.2, which the measured 11-12-ply budget makes affordable) as well as
   against the learned thief.

**One recommendation that is genuinely symmetric and safe:** the §6 feature vector. Both roles
compute the same quantities and only the weights differ, so improving the feature code helps
both. **One that is not:** deepening the cop's barrier search. Every extra barrier candidate the
cop evaluates costs the *cop* depth (measured: K=45 → 4 plies vs K=4 → 6 plies) but costs the
thief nothing, so cop-side barrier work and thief-side search depth are not in competition —
they can be developed independently.

---

## 9. No source found

Claims below are reasoning from the cited principles above, or measurements I took myself. They
are **not** supported by a located publication and should be labelled as such if they appear in
the project's PRD.

1. **No source found** for a published algorithm comparison on *this exact* variant (single cop,
   permanent barrier placement with a quota, fixed survival deadline, 7x7). The Angel Problem
   (Conway 1996), Tron (a1k0n 2010) and Isolation each cover *part* of the mechanic; none covers
   all of it.
2. **No source found** for a measured depth-vs-wall-clock table for alpha-beta in CPython on a
   small grid game. The tables in §3 and §4 are **my own micro-benchmarks** on this machine
   (CPython 3.11.9, Intel64 Family 6 Model 154), not published results. The only published
   pure-Python comparator located is Sunfish at 20-40 kn/s
   ([chessprogramming.org/Sunfish](https://www.chessprogramming.org/Sunfish)).
3. **No source found** attributing our specific cop-0.90 / thief-0.016 self-play collapse to the
   `max` operator. The mechanism argued in §2(c) follows from Littman (1994) and Hsu et al.
   (2021) but is an inference, not a cited empirical finding.
4. **No source found** for tile coding applied to a *discrete* grid pursuit state; the tile
   coding literature (S&B ch.9; Sherstov & Stone 2005) is about continuous spaces. Our
   recommendation against tile coding is therefore an argument, not a citation.
5. **No source found** for potential-based reward shaping applied to cops-and-robbers with
   barriers specifically; Ng et al. (1999) give the general distance-based construction.
6. **No source found** for the `barriers_remaining/14` and edge/corner-distance features (f8,
   f11) — those are game-specific and I could not find a pursuit-evasion paper that uses them.
7. **No source found** for MCTS on a grid pursuit game with a blocking action; the boop.
   (arXiv:2406.08766) and Ludii (arXiv:1905.05013) numbers are the nearest throughput
   comparators and are for other games and other languages (C++ / Java).
8. **No source found** confirming a1k0n's `K1 = 0.055 / K2 = 0.194` coefficients transfer to a
   7x7 board with two mobile players; they were fitted for Tron, where both players leave
   permanent trails. Treat the *ratio* (edges ~3.5x cells) as the transferable claim, not the
   absolute values.
9. **No source found** for a published pure-Python implementation of Minimax-Q that fits in 150
   lines without an LP dependency.
