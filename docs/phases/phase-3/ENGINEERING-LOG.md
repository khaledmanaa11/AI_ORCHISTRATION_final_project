# Phase 3 engineering log — how the strategy module was actually built

**Audience:** the grader, and whoever maintains this next.
**Purpose:** the PRD says what the module does. This says what went wrong on the way there,
what we measured, what we got wrong, and what we threw away. Every number below was measured
in this repository; none is estimated.

Companion document: [RUN-1-POSTMORTEM.md](RUN-1-POSTMORTEM.md), the forensic analysis of the
first training run.

---

## Act 1 — a training run that looked fine and wasn't

The first attempt was textbook: tabular Q-learning, ε-greedy, a state key over
(cop cell × thief cell × blocked mask × barriers used × turns remaining × action) inducing
**103,723,200 Q-values**, trained for **300,000 episodes** overnight.

The learning curve looked healthy. The cop's win rate against the heuristic thief climbed
decile by decile — 0.006, 0.024, 0.055 … 0.854 — peaking at **0.9435**. The last curve rows
sat at **0.900**.

Then GATE-4 measured it at **0.250**.

The recorded diagnosis was "still climbing when ε hit its floor → train longer." The
post-mortem showed that was wrong. Every one of the 300,000 episodes started from the same
board — cop (0,0), thief (3,3) — and the gate measured it somewhere it had never been. The
thief's reward function was separately degenerate and had never been capable of learning.

That much we knew going into this phase. What we did not know was that fixing both would not
have been enough.

## Act 2 — the real defect: the game is simultaneous

The engine resolved a turn in two halves: `apply_cop_action`, check capture, then
`apply_thief_move`. So the thief chose its move while already looking at the cop's *new*
cell.

Reading the book directly settled it in one sentence. §5.3.2 p.35, on the Acknowledge phase:

> *"This acknowledgement prevents the sender from retreating from its commitment, and at the
> same time guarantees that the reveal will occur only when both sides have already fixed
> their moves."*

And §5.2 p.33 lists the three frauds the protocol exists to prevent. The second is
*"changing a move after the opponent's move has been revealed."*

**This reframed the problem completely.** It is not that the agent had an unfair advantage in
training. It is that the entire mandatory Commit-Reveal chapter — four cryptographic phases,
every turn, SHA-256, nonces, the mutual audit — has *no purpose whatsoever* under sequential
play. We had implemented the protocol and then built a game that did not need it.

It also explains the training failure at a level the post-mortem could not reach. Under
simultaneous moves this is a **two-player zero-sum Markov game**, not an MDP:

- there is no "best action" independent of the opponent's simultaneous choice;
- at contact squares the only unexploitable play is a **mixed** strategy;
- Q-learning's target `max_a' Q(s', a')` is a single-agent quantity with no meaning here;
- and `argmax` over a Q-row is deterministic by construction.

The repo had already measured what determinism costs, in a scratch file nobody had acted on:
a search cop captures a **deterministic** evader 96% of the time and a **mixing** one 36%.
We play the thief seat in half of every league match.

**Lesson:** the run-1 post-mortem was rigorous and still reached the wrong root cause,
because it only questioned the learner. It never questioned the environment.

## Act 3 — what else was broken, found by running the engine rather than reading it

Auditing the old engine by *executing* it turned up three defects that had been live through
all of run 1:

1. **The thief could walk onto the cop and not be captured.** `get_legal_moves` never
   excluded the opponent's cell, and capture was only ever tested on the cop's half-turn.
   The thief steps onto the cop → `outcome=None` → next turn the cop steps away and the
   capture is simply gone. Whether it counted depended on the cop's *next* decision, which is
   not a rule the book contains.
2. **`apply_move` validated nothing.** It was a bare `dataclasses.replace`. A thief was
   successfully placed on top of a barrier.
3. **Rule 47 was unreachable dead code.** `if not get_legal_moves(...)` can never fire,
   because `get_legal_moves` appends STAY unconditionally. The book's condition is about the
   four *adjacent* cells and says nothing about staying put — so the cop's entire
   barrier-sealing win condition did not exist.

None of these were caught by a green test suite, because the tests encoded the same
assumptions the code did.

Fixing them could not be done by reordering calls. `apply_cop_action`/`apply_thief_move`
never accepted both actions, and every turn passed through an intermediate one-agent-moved
state that destroys the pre-turn positions a swap detector needs. A joint turn was literally
inexpressible. One `resolve_turn` replaced both.

## Act 4 — three measurements that changed the design

### 4.1 The evaluation was 5× too slow, and the fix was not the obvious one

First benchmark of the feature vector: **194 µs warm**. At ~50 leaves per decision that is
~10 ms of pure evaluation, and it would have dominated every training run.

The obvious response is to delete expensive features. The actual cause was the two-source
Voronoi split, recomputed from scratch per leaf at ~120 µs. Memoising the **BFS distance
maps** on `(cells, source)` fixed it without losing anything: the 25 move-only successors of
a decision put the cop on at most 5 distinct cells and the thief on at most 5, so 50 BFS
calls collapse to 10.

| | before | after |
|---|---|---|
| decision, caches cold | ~9.7 ms | **3.62 ms** |
| self-play throughput | — | **~14,200 games/hour/core** |

**Lesson:** benchmark the thing you will actually run. The first benchmark measured 300
*unrelated* random states, where nothing can be shared. It reported a number that was true
and useless.

### 4.2 Rule 46 makes distance 1 a forced loss — and a one-ply search cannot see it

The thief seat was losing badly. The diagnostic was to break down *which predicate* was
ending games. Against a naive chaser with barriers, **82 of 100** games ended by rule 46 — a
barrier placed on the thief's cell.

Reading the rule again explained why. The cop's legal barrier targets are its own cell **plus
its four orthogonal neighbours**, and rule 46 captures the thief when the seal lands on the
cell it occupied *at that moment* — its **pre**-move cell. So:

> A thief at Manhattan distance 1 from a cop with quota remaining is captured next turn no
> matter where it runs. The seal lands on the cell it is leaving. There is no escaping move.

A depth-1 search cannot discover this, because the loss is two plies away. Rather than pay
for a depth-2 search, we named it as a feature. Measured effect on thief survival against a
sealing chaser: **15% → 64%**.

But the first attempt over-corrected. With the feature weighted at 3.00, survival against a
*barrier-blind* chaser collapsed from 89% to 10% — the thief became so proximity-averse it
cornered itself. An ablation across all four rule sets showed the feature helping enormously
in one regime and hurting enormously in the other. We stopped hand-tuning at that point and
let training set the weight; it settled on **1.84**.

**Lesson:** a feature can encode a *conditional* truth. "Distance 1 is death" is only true if
the opponent actually places barriers.

### 4.3 One negotiable rule was worth more than the whole learning run

Two of the six terminal predicates are undefined by the book. §3.2 p.18 says the contract is
*negotiated between each pair of teams* and is *"a floor, not a ceiling"*, so they are agreed
data rather than engine assumptions.

We had initially chosen the capture-favouring reading on the theory that the cop seat is
worth more (20 points vs 10). Measuring it said otherwise:

| our thief vs a barrier-blind chaser | survival |
|---|---|
| swap counts as a capture | **1%** |
| swap does not (book-only) | **89%** |

The cop seat was at 100% either way. So the swap predicate was worth ~88 points of thief
survival and bought nothing. **We reversed the decision** and now propose the barrier race
while declining the swap. The engine still implements both, because an opponent may propose
it and the search adapts — it expands through the live rules, so only positional judgement is
baked into the weights.

**Lesson:** we picked that rule before we had data, on a plausible argument about scoring.
The plausible argument was backwards.

## Act 5 — two optimisers, one shipped

Rather than argue about the objective, both were built and run to completion:

- **Outcome regression** (Texel-style) on `tanh(w·φ)` against the game's actual result, with
  Adagrad, batch-synchronous generations, an anchored opponent pool, and randomised starts.
  40 generations × 600 games = **24,000 games**, about an hour.
- **(1+λ)-ES on league points directly**, with common random numbers so that a difference in
  fitness is a difference in weights and not a difference in luck.

Held-out at n=200 with 95% Wilson intervals, on the negotiated opening:

| | thief vs sealing cop | thief vs blind cop | cop vs evader |
|---|---|---|---|
| hand-set prior | 43.5% | 14.5% | 100% |
| **outcome regression** | **58.0%** | **32.5%** | **100%** |
| (1+λ)-ES | 20.0% | 85.5% | 93.5% |

Total points were near-identical. The **distribution** was not: the ES vector is a specialist
that collapses against the stronger, more likely archetype. A competent opponent uses its
barrier quota — rule 46 makes it decisive — so the balanced vector ships and the ES run is
kept as a documented negative result.

Training also **flipped the sign** on two features the hand-set prior had backwards:
`chokepoint_density` (+0.40 → −0.49) and `thief_on_chokepoint` (+0.30 → −0.39). The prior
assumed chokepoints in the thief's region help the cop. The data disagreed.

## Act 6 — the gates were not running

While enabling the pre-commit hook we found that **`ruff` and `pytest --cov` had been
commented out of both the hook and CI** since before the `uv` project existed. Only the
150-line check was actually enforced. Both are now live, and the first thing the restored
suite caught was a genuine bug: `load_weights("")` resolved to the current *directory* and
raised `PermissionError` instead of falling back to the prior.

## What we got wrong, in order

1. Believed the run-1 post-mortem's root cause. It was rigorous and still incomplete, because
   it only interrogated the learner and never the environment.
2. Trusted a green test suite. The tests encoded the same sequential assumption the code did,
   so they could not fail.
3. Benchmarked the wrong workload first, and got a number that was true and useless.
4. Chose a negotiable rule from a plausible scoring argument instead of a measurement, and had
   to reverse it.
5. Hand-tuned the kill-range weight to 3.00 and made a whole regime worse before letting
   training decide.
6. Assumed the enforced quality gates were enforced.

## What is still open, honestly

- **Depth 1.** The mover expands one joint ply. A multi-turn barrier seal is visible only as a
  gradient through the structure features, not as a plan.
- **The thief seat is the weak one**, and it is bounded by the rules rather than by the
  algorithm: with quota in hand, a cop that reaches distance 1 wins outright.
- **Untested negotiation lever.** Board size is a *minimum* in Appendix ו, so it may be agreed
  upward, and a larger board should favour the thief without costing the cop much. Not
  measured.
- **Warm-up games are legal and unscored** (rule 52), and code may change between games
  (Appendix ו §2 rule 5). Scouting an opponent and refitting offline is permitted and not yet
  built.
