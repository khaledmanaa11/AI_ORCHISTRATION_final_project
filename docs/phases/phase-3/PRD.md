# Phase 3 PRD — the strategy module (run 2, rebuilt)

**Milestone gate (book §10.4, stage 3):** two agents play a complete game blind of each
other's process, with the move decided by an algorithm — never by a language model.

**Status:** run 2. Run 1 (tabular Q-learning) is withdrawn; see §2.
**Binding rules contract:** [RULES-RESOLUTION.md](RULES-RESOLUTION.md)
**Mechanism PRD:** [docs/PRD_matrix_mover.md](../../PRD_matrix_mover.md)
**How it was actually built** — the failures, the measurements, the reversals, and what we
got wrong: [ENGINEERING-LOG.md](ENGINEERING-LOG.md) · [RUN-1-POSTMORTEM.md](RUN-1-POSTMORTEM.md)

---

## 1. What this phase delivers

| # | Deliverable | Where |
|---|---|---|
| D1 | The turn is **simultaneous**: one joint resolver, six terminal predicates | `src/pursuit/sdk/{resolve,actions,terminal}.py` |
| D2 | Negotiated resolution semantics that cannot abort the handshake | `src/pursuit/shared/resolution.py`, `config/*/resolution.json` |
| D3 | A matrix-game mover that plays an **unexploitable** (mixed) strategy | `src/pursuit/strategy/{matrix,equilibrium,valuebrain}.py` |
| D4 | A 15-feature positional evaluation over the free-cell graph | `src/pursuit/strategy/{features,graphcache}.py` |
| D5 | Two fixed sparring anchors representing a realistic opponent | `src/pursuit/strategy/naive.py` |
| D6 | Self-play training with a randomised start distribution | `training/{run_selfplay,generation,pool,fit,starts}.py` |
| D7 | A second optimiser targeting league points directly | `training/{evolve,run_evolve}.py` |
| D8 | Held-out evaluation with 95% intervals on every rate | `training/{arena,run_eval}.py` |

## 2. Why run 1 was withdrawn

Run 1 trained a tabular Q-learner for 300,000 episodes over a 103.7-million-value key. Its
cop finished training beating the heuristic thief **90%** of the time and scored **25%** at
the gate. The post-mortem attributed this to the fixed start state and a degenerate thief
reward. Both were real. Neither was the root cause.

**The root cause is that the game is simultaneous and the engine was sequential.** Book
§5.3.2 p.35 states that the Acknowledge phase *"guarantees that the reveal will occur only
when both sides have already fixed their moves"*, and §5.2 names *"changing a move after
the opponent's move has been revealed"* as one of the three frauds the mandatory
Commit-Reveal protocol exists to prevent. The engine resolved cop-then-thief, so the thief
chose while already seeing the cop's new cell — precisely the information Chapter 5 spends
eight pages making cryptographically impossible.

That makes tabular Q-learning the wrong tool, not an under-trained one. `max_a' Q(s', a')`
is a single-agent quantity with no meaning in a matrix game, and `argmax` over a Q-row is
deterministic by construction. This repo's own measurement of the cost: a search cop
captures a deterministic evader **96%** of the time and a mixing one **36%**.

Three further engine defects were found by running the old engine and are fixed in D1:
`apply_move` validated nothing (a thief could be placed on a barrier); the thief could step
onto the cop uncaptured and then escape; and rule 47 (walled-in thief) was unreachable dead
code because `get_legal_moves` appends STAY unconditionally.

## 3. Acceptance criteria

| ID | Criterion | How it is measured |
|---|---|---|
| AC-1 | Both agents decide from the **same** pre-turn state; the turn resolves once | `tests/unit/training/test_joint_game.py` asserts both brains receive an identical state object per turn |
| AC-2 | All six terminal predicates fire correctly under both rule sets | `tests/unit/test_terminal.py` |
| AC-3 | An illegal action is rejected, never absorbed | `tests/unit/test_resolve.py` |
| AC-4 | A missing negotiated block degrades to BOOK_ONLY; a malformed one raises | `tests/unit/test_resolution_config.py` |
| AC-5 | The mover plays a mixed strategy where one is required | `tests/unit/strategy/test_equilibrium.py` (matching pennies → 0.5/0.5) |
| AC-6 | A decision fits comfortably inside the 30 s negotiated timeout | measured: **3.62 ms** cold, 2.14 ms warm |
| AC-7 | The shipped weights beat the hand-set prior, or the prior ships | `training/run_eval.py`, 95% Wilson intervals, both seats |
| AC-8 | No language model on the decision path | `scripts/check_no_llm_in_strategy.py` |
| AC-9 | Segal Table 5 gates green | ruff, pytest --cov ≥85%, every file ≤150 code lines |

## 4. Requirements covered

- **STRAT-01** canonical action space — `sdk/actions.py`; movement set is *fixed* (Table 15).
- **STRAT-03** one brain seam — `BrainBase`; three registered brains, explicit registry.
- **STRAT-05** only the cop may place a barrier — enforced in `CopAction` and `naive.py`.
- **STRAT-07 / rule 25** the algorithm decides — no LLM import is reachable from `strategy/`.
- **BASE-03/04/05** capture conditions — now `sdk/terminal.py`, all three reachable.
- **Rule 46/47/48** — predicates 1, 5 and the scoring table.
- **Rule 42** — learning curves written to `artifacts/*/curve.json`.

## 5. In scope / out of scope

**In:** turn resolution, action spaces, the mover, the evaluation, training, evaluation
harness, the negotiated rules block, retirement of the run-1 stack.

**Out:** belief maps and blindness (Phase 4 — **but read §8 first**, the seam is not the
drop-in this document originally claimed); pheromones and hint text (Phase 4);
barrier placement over the wire (Phase 6 — the wire action is currently always a move);
commit-reveal itself (Phase 6); the live GUI and replay viewer (Phase 7).

## 6. Measured results

Held-out, n=200 per matchup, 95% Wilson intervals, `run_eval.py`. The prior and the
trained vector are measured in the same run, so "did training help" is a comparison and
not a number remembered from an earlier session.

**On the negotiated opening — the board a league game actually plays:**

| matchup | seat | prior | shipped | delta |
|---|---|---|---|---|
| vs chaser cop (seals) | thief | 43.5% [36.8, 50.4] | **58.0%** [51.1, 64.6] | **+14.5% — significant** |
| vs chaser cop (no seals) | thief | 14.5% [10.3, 20.0] | **32.5%** [26.4, 39.3] | **+18.0% — significant** |
| vs greedy evader | cop | 100.0% [98.1, 100] | **100.0%** [98.1, 100] | at ceiling |

On randomised starts every matchup also improved (+3.0 to +4.5%) but none separably at
n=200 — reported rather than claimed.

**Training curve** (`artifacts/run2/curve.json`, 40 generations × 600 games = 24,000 games,
≈1 h): cop 52.3% → 73.7%, thief 28.0% → 36.3% against the pool, loss 1.63 → 0.72.

**What training changed in the model.** Two features had their sign **flipped** from the
hand-set prior: `chokepoint_density` (+0.40 → −0.49) and `thief_on_chokepoint` (+0.30 →
−0.39). The prior assumed chokepoints in the thief's region help the cop; the data says the
opposite. `turns_remaining` more than tripled (0.35 → 1.14) and `thief_in_kill_range` fell
from the deliberately extreme 3.00 to 1.84 — matching the ablation which showed 3.00 made
the thief so proximity-averse it cornered itself.

**The rejected artefact.** A second optimiser — `(1+λ)`-ES on league points with common
random numbers — was run to completion and **not shipped**. It became a specialist: 85.5%
against a barrier-blind chaser (vs 32.5%) but only **20.0%** against a sealing one (vs
58.0%), and it gave up cop points (93.5% vs 100%). Total points were near-identical; the
distribution was not. A competent opponent will use its barrier quota — rule 46 makes it
decisive — so the balanced vector is the correct ship. Both runs and both curves are kept
in `artifacts/` for the report.

## 7. Known limitations, stated rather than hidden

1. **Depth 1.** The mover expands one joint ply. A multi-turn barrier seal is visible only
   as a gradient through the structure features, not as a plan. The one two-ply fact that
   mattered most — rule 46's forced capture at distance 1 — is supplied explicitly as the
   `thief_in_kill_range` feature, worth a measured **15% → 64%** on thief survival.
2. **The game is cop-favoured under the book's defaults.** With a 14-barrier quota, a cop
   that reaches Manhattan distance 1 wins outright. Our cop converts 100% against a naive
   thief; our thief's survival is where the remaining headroom is, and it is bounded by
   the rules rather than by the algorithm.
3. **The negotiated rules change the game materially.** Making the swap a capture drops
   thief survival against a barrier-blind chaser from **32.0% to 7.5%** (n=200 per arm,
   shipped run-2 weights, negotiated opening; re-measured by
   `scripts/sensitivity_reconcile.py`, artifact `artifacts/sensitivity/reconcile.json`).
   We therefore propose the barrier race and decline the swap — a measured decision,
   recorded in `resolution.py` and reversible if an opponent insists.

   **Correction, 2026-08-17 (plan 08-11).** This paragraph read **“from 89% to 1%”** until
   today, quoting `docs/phases/phase-3/ENGINEERING-LOG.md` Act 4.3. That pair does **not**
   reproduce: 08-09's sweep re-measured all eight weights × rules × opening arms and the
   highest is 52.5%, with none near 1%. The **direction is confirmed and unchanged** —
   declining the swap is still worth ~25 points of thief survival and the cop seat converts
   100% under all four rule combinations either way — but the magnitude was overstated and
   **the cause was never established**: the engine moved through Phases 4–6 between the two
   measurements and the sweep did not isolate which change is responsible.

## 8. Handoff to Phase 4 — read this before starting

**One correction to an earlier claim in this document.** Sections 5 and PLAN §2 originally
said Phase 4 would swap `Observation.target_cell` from the true cell to the belief argmax
"with no other change". That was true of run 1's Q-learning brain. It is **not** true of the
matrix-game mover.

`ValueSearchBrain._decide_move(obs, state)` **never reads `obs`**. It builds the payoff
matrix from `state`, and `GameState` carries the opponent's *true* cell. Nothing in
`src/` or `training/` reads `obs.target_cell` at all — it is currently vestigial, as is
`Observation.blocked_mask`, which `training/joint_game.py::observe` fills with 0 because the
feature vector derives everything it needs from the board.

So Phase 4's first task is a real design decision, not a field swap:

| option | what it means | cost |
|---|---|---|
| **A — believed state** | Build a `GameState` with the opponent at the belief argmax and expand the matrix over that. One line in the brain plus a caller that supplies it. | cheap; throws away the belief's uncertainty |
| **B — expectation over the belief** | Build the matrix entry as the belief-weighted expectation over candidate opponent cells. | correct under partial observability; multiplies the expansion by the number of candidate cells |

Option B is the honest one for a Dec-POMDP and is what the book's framing (§1.3) implies.
Option A is a valid first step that makes the pipeline blind immediately and can be upgraded
in place, since both only change how `payoff_matrix` obtains the opponent's position.

**Nothing else in Phases 1–3 blocks Phase 4.** The engine, the negotiated rules, the network
joint-turn path, the training and evaluation harnesses, and the shipped weights are all
independent of where the opponent's position comes from. The weights are a *positional*
evaluation over the free-cell graph and stay valid under either option.
