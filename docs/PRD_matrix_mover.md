# PRD — the matrix-game mover

**Mechanism:** how the agent chooses its action on a simultaneous turn.
**Status:** implemented (run 2) · **Supersedes:** `docs/PRD_rl_strategy.md` (tabular Q-learning, run 1)
**Segal §2.3:** every algorithm or central mechanism carries its own PRD. This is that document.

---

## 1. The problem this mechanism solves

Both agents choose an action from the same pre-turn board without seeing the other's
choice. Book §5.3.2 p.35 makes this explicit — the Acknowledge phase *"guarantees that
the reveal will occur only when both sides have already fixed their moves"* — and the
whole mandatory Commit-Reveal protocol exists to enforce it.

That is a **two-player zero-sum Markov game**, not a Markov decision process. The
distinction is not academic:

- In an MDP there is a best action per state. In a matrix game there is not: the best
  action depends on what the opponent simultaneously does, and at contact squares the
  only unexploitable play is a **mixed** strategy.
- Q-learning's bootstrap target `max_a' Q(s', a')` is a single-agent quantity. It has no
  meaning here, and `argmax` over a Q-row is deterministic by construction.

Run 1 implemented independent tabular Q-learning over a 103.7-million-value key. It was
not under-trained; it was solving the wrong problem.

## 2. What it does

Per turn:

```
1. enumerate both action sets from the SAME pre-turn state      (sdk/actions.py)
2. build the |A_c| x |A_t| payoff matrix by one-ply expansion   (strategy/matrix.py)
      M[i][j] = value of resolve_turn(state, cop_action_i, thief_move_j)
3. solve the matrix game                                        (strategy/equilibrium.py)
      pure saddle if one exists, else regret matching
4. sample this seat's strategy from a seeded, logged RNG        (strategy/valuebrain.py)
```

**Inputs:** `GameState`, `GameParams`, `ResolutionRules`, a 15-float weight vector, a seeded `Random`.
**Output:** a `Decision` (move, provenance, optional barrier).
**No language model is involved at any point** (rule 25 — recommended by the book, treated as hard here).

### Why the matrix can be derived rather than learned

Transitions are deterministic, so `M[i][j]` is exactly the value of the resolved
successor. Nothing joint is ever stored or sampled. This kills the standard objection to
minimax-Q — that a joint table needs `|A_c| x |A_t|` times the samples — because the
joint object is rebuilt at the point of use and only a 15-weight evaluation is learned.

### Leaf values

Bounded to `[-1, 1]` so terminals and estimates share one scale:

| leaf | value |
|---|---|
| CAPTURE | `+1.0` exactly |
| SURVIVAL | `-1.0` exactly |
| non-terminal | `tanh(w · φ(s))`, strictly inside `(-1, 1)` |

Squashing is not cosmetic. An unbounded leaf could outrank a real capture and make the
search prefer a position it merely likes to a win it can actually take.

## 3. The evaluation φ(s) — 15 features

Cop-perspective, each scaled to roughly `[-1, 1]` by a divisor derived from `GameParams`.
The game is zero-sum, so **one vector serves both seats by negation** — there is no
second artefact and no second training run.

| group | features |
|---|---|
| contact | bias, −distance, thief-unreachable, −thief-degree, parity, cop-degree |
| territory | Voronoi cell difference, −thief region size |
| structure | −cycle rank, region-is-forest, chokepoint density, thief-on-chokepoint |
| resources | barriers remaining, turns remaining |
| tactical | **thief-in-kill-range** |

**Why structure and not distance.** A single cop cannot corner a perfect evader on an
open 7×7 grid: the free graph has cycle rank `(n−1)² = 36` and the thief simply runs
loops. Capture requires first driving that cycle rank toward zero with barriers. Distance
is a symptom; structure is the objective. Measured: a greedy max-distance thief and a
max-room thief both survive **0%** against this mover, while the mover's own thief
survives far more — distance-only policies are not merely weaker, they are wrong.

**`thief_in_kill_range` is the highest-value single feature and deserves its own note.**
Rule 46 captures the thief when a barrier lands on the cell it occupied *at that moment* —
its **pre**-move cell — and the cop's legal barrier targets are its own cell plus its four
orthogonal neighbours. So **a thief at Manhattan distance 1 from a cop with quota
remaining is captured next turn no matter where it runs**: the seal lands on the cell it
is leaving. There is no escaping move. A depth-1 search cannot discover this, because the
loss is two plies away. Naming it as a feature gives a one-ply searcher a two-ply fact for
free, and is far cheaper than the depth-2 search that would otherwise be required.
Measured effect on thief survival against a sealing chaser: **15% → 64%**.

## 4. The solver

Two stages, because most positions do not need mixing:

1. **`pure_saddle`** — exact, deterministic, `O(rows × cols)`. Where `max_i min_j M = min_j max_i M`,
   the pure maximin pair *is* the equilibrium, and playing it keeps the turn fully
   deterministic and byte-reproducible in the replay viewer.
2. **Regret matching** (Hart & Mas-Colell 2000) — only when no saddle exists, which is
   exactly where mixing is genuinely required. The **average** strategies converge to Nash;
   returning the current iterate instead is the classic implementation error and yields a
   policy that oscillates rather than mixes.

**Why mixing matters commercially.** This repo's own measurement: a search cop captures a
deterministic evader **96%** of the time and a uniformly mixing one **36%**. We play the
thief seat in half of every league match, and rule 52 gives each opponent exactly one
counted game — there is no adaptation window in which to recover from being read.

Sampling takes the random draw as an argument rather than calling a module RNG, so the
caller owns reproducibility: the live agent draws from a per-game seed that is logged
(rule 20), and the replay reproduces the game exactly.

## 5. Cost — measured, not estimated

On the development laptop, CPython under `uv`, no numpy:

| quantity | measured |
|---|---|
| joint successors per decision | 31.5 average |
| decision, caches cold | **3.62 ms** |
| decision, caches warm | **2.14 ms** |
| implied self-play throughput | **~14,200 games/hour/core** |

The negotiated response timeout is 30 s (Table 19) and the watchdog 60 s, so a 3.6 ms
decision uses about 0.01% of budget. Book §5.5 p.39 normalises the league score so that
raw hardware cannot decide the race — *"a light, fast solution on a modest machine that
beats a heavy opponent is a victory of development over computational muscle"* — which is
an argument for a shallow search with a good evaluation, and against a deep one.

**What makes it affordable:** memoising the BFS distance maps on `(cells, source)`. The 25
move-only successors of a decision put the cop on at most 5 distinct cells and the thief on
at most 5, so 50 BFS calls collapse to 10. Before that change the per-leaf cost was 194 µs
and dominated everything; the two-source Voronoi alone was ~120 µs per leaf.

## 6. Alternatives considered and rejected

| alternative | why not |
|---|---|
| Keep tabular Q-learning, train longer | Unsound under simultaneity (§1). Run 1's cop finished training at 90% and gated at 25%. |
| Depth-4 simultaneous alpha-beta | Simultaneous-move αβ prunes far more weakly than sequential αβ — a bound on one entry rarely eliminates a row or column. Depth 4 measured ~4.3 s full-width. Also cuts against §5.5's computational-fairness normalisation. |
| Tabular value over a graph-invariant abstraction | ~400k keys and a multi-hour run, and its own throughput analysis depended on an unvalidated cache hit rate. The 15-weight linear model reaches usable play in minutes and is inspectable by eye. |
| Exact LP for the matrix game | Correct, but a tableau simplex returns a **vertex** — a pure strategy — on the constant matrices that are routine in the open early game. That reintroduces the determinism the mechanism exists to remove. Regret matching returns uniform there. |
| Deep search over a neural evaluation | No dependency budget for it (the project has one runtime dependency), no wall-clock budget on a laptop, and unauditable against rule 42's requirement to describe the model. |

## 7. Risks and what is done about them

| risk | mitigation |
|---|---|
| Depth 1 cannot see a multi-turn barrier seal | Structure features (cycle rank, forest, chokepoints) give the gradient; `thief_in_kill_range` supplies the one two-ply fact that mattered most. Honest limitation: a gradient is not a plan. |
| The evaluation is fitted against one rule set but played under another | The search expands through the **live** `ResolutionRules`, so tactics adapt to whatever was negotiated. Only positional judgement is baked into the weights. |
| A learned weight is worse than the prior | The prior is shippable on its own (§6.3 makes learning optional), and `training/run_eval.py` measures trained-vs-prior on held-out anchors with 95% Wilson intervals. A trained vector ships only if it wins that comparison. |
| Self-play learns only to beat its past selves | The opponent pool is anchored by three FIXED, non-drifting members (the prior and both naive archetypes) which together outweigh the self-play share. |
| Mixing makes replay non-reproducible | The draw is a pure function of a logged seed. |

## 8. Compliance

- **Rule 2** — no shared runtime state; the two seats are separate processes and the only
  shared thing is a pure library and a read-only weight file.
- **Rule 25** — the algorithm chooses the move; no LLM is on the decision path. Enforced by
  `scripts/check_no_llm_in_strategy.py`.
- **Segal Table 5** — every file ≤ 150 code lines; no hardcoded values (scaling divisors
  derive from `GameParams`, solver constants are named module constants).
- **Rule 42** — the learning curve is written to `artifacts/*/curve.json` for the report,
  and `weights.describe()` renders the model as a named table.

---

## Run 3 — adaptive rule-46 terminal leaf (2026-08-18)

Rule 46 makes Manhattan distance 1 with quota remaining a **forced capture one
turn later**: the seal lands on the cell the thief is leaving, so no reply
escapes. Run 2 encoded that fact as the learned `thief_in_kill_range` feature;
run 3 promotes it to a **terminal leaf value** (`FORCED_CAPTURE_VALUE = 0.98`,
a named module constant kept strictly below `CAPTURE_VALUE`), giving the
one-ply mover exact two-ply trap vision.

The leaf is **gated on evidence**, per seat, via two new validated
`strategy.json` keys (engineering defaults, not PARAMETERS.md values):
`leaf_mode` (`stock` | `adaptive` | `cautious`) and `relax_turn`. `adaptive`
arms the leaf iff `barriers_placed > 0 or turn < relax_turn` — every barrier
on the board is the cop''s, so one placed barrier is proof of a sealing
opponent; a pure function of the visible state, no memory, replay-exact.

Measurements (Wilson 95%, league opening). Always-cautious: sealing-chaser
survival 59.3% but no-seal 72.0% (n=300) — the phantom-threat cost. Adaptive
gate at n=1000/cell: sealing **57.4%** [54.3, 60.4] vs incumbent 51.1%
[48.6, 53.7]; no-seal **90.4%** [88.4, 92.1] vs 30.0%; unchanged vs the
strong search cop. The thief ships `leaf_mode=adaptive` with the promoted
thief-only ES vector (`config/thief/weights.json` metadata carries the
evidence); the cop ships `leaf_mode=stock`, byte-identical behaviour to run 2.

A depth-2 backup (solved one-ply matrix value as the leaf) was tried first and
**degraded** the thief 46% → 23% vs the sealing chaser (n=100, separated) —
the classic pathology of deepening on a leaf fitted at depth 1; recorded as a
negative result.
