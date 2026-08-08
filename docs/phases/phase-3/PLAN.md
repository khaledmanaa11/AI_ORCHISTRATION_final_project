# Phase 3 PLAN — run 2

How the [PRD](PRD.md) is built. Contracts and constraints only; the code is the code.

---

## 1. Architecture

```
                  pre-turn GameState  (both seats see the SAME one)
                            |
        +-------------------+-------------------+
        |                                       |
   cop_actions()                          thief_actions()      sdk/actions.py
        |                                       |
        +------------- payoff_matrix ------------+              strategy/matrix.py
                            |    M[i][j] = leaf_value(resolve_turn(...))
                            |
                     solve(matrix)                              strategy/equilibrium.py
                     pure saddle, else regret matching
                            |
                   sample(strategy, seeded draw)                strategy/valuebrain.py
                            |
                        Decision  ->  resolve_turn once         sdk/resolve.py
```

Leaf values are bounded: CAPTURE `+1`, SURVIVAL `-1`, otherwise `tanh(w · φ(s))`.
One weight vector, cop-perspective; the thief's value is its negation.

## 2. Interfaces that other phases depend on

| Contract | Signature | Stability |
|---|---|---|
| Joint resolution | `resolve_turn(state, CopAction, thief_move, params, rules) -> (GameState, Outcome\|None)` | Frozen. Phase 6 adds commit-reveal *around* it, never inside. |
| Action spaces | `cop_actions(state, params) -> [CopAction]`, `thief_actions(state, params) -> [Coord]` | Frozen. |
| Brain seam | `BrainBase._decide_move(obs, state) -> Decision` | Unchanged from run 1 — Phase 4 swaps `Observation.target_cell` from the true cell to the belief argmax with no other change. |
| Negotiated rules | `load_resolution_rules(path) -> ResolutionRules`, `as_declaration(rules) -> dict` | The declaration dict is what Phase 6 seals into the pre-game handshake. |
| Learned artefact | `weights.json` — `{version, feature_names, weights, metadata}` | Feature names travel with the numbers so a stale vector fails loud. |

## 3. Phase-specific ADRs

**ADR-01 — the turn is resolved jointly, not reordered.**
`apply_cop_action`/`apply_thief_move` could not be made simultaneous by changing call order:
no function accepted both actions, and every turn passed through an intermediate
one-agent-moved state that destroys the pre-turn positions a swap detector needs. One
resolver replaces both. *Consequence:* `shared/capture.py` is deleted — `detect_capture`
decided capture from a single snapshot, which is now actively wrong.

**ADR-02 — negotiated predicates live outside `game_params.json`.**
Rule 11 wants that file byte-identical on both sides and the handshake aborts on a digest
mismatch, so new keys there would mean 0/0 on games that never start. Resolution semantics
go in a separate optional block that defaults to `BOOK_ONLY`. *Consequence:* we can never
diverge from a book-faithful peer at the rule-36 audit.

**ADR-03 — learn a value, never a policy.**
A policy must commit before the opponent's action is known; a value composes with a matrix
backup exactly. This is also why 15 weights suffice where 103.7M Q-values did not: the
search supplies the tactics.

**ADR-04 — mix only where mixing is required.**
`pure_saddle` first (exact, deterministic, most positions), regret matching otherwise. An
LP would return a vertex — a pure strategy — on the constant matrices that are routine in
the open early game, reintroducing the determinism the mover exists to remove.

**ADR-05 — decline the swap predicate.** Measured, not assumed: making the swap a capture
drops thief survival against a barrier-blind chaser from 89% to 1% and gains the cop seat
nothing it does not already have. We propose the barrier race only.

**ADR-06 — two optimisers, one shipped.** Outcome regression fits `P(cop wins)`, a proxy;
`(1+λ)`-ES optimises league points directly with common random numbers. Which one ships is
decided by held-out evaluation, not preference.

**ADR-07 — memoise the BFS maps, not the features.** The 25 move-only successors of a
decision put each agent on ≤5 distinct cells, so 50 BFS calls collapse to 10. This is the
single change that took a decision from ~9.7 ms to 3.6 ms and made self-play affordable.

## 4. Test plan

| Layer | File | What it pins |
|---|---|---|
| Resolution | `tests/unit/test_resolve.py` | joint application, validation, turn advances once, the three fixed defects |
| Predicates | `tests/unit/test_terminal.py` | all six, under both rule sets |
| Negotiation | `tests/unit/test_resolution_config.py` | missing → BOOK_ONLY, malformed → raise, declaration round-trips |
| Solver | `tests/unit/strategy/test_equilibrium.py` | matching pennies → (0.5, 0.5); saddle stays pure |
| Evaluation | `tests/unit/strategy/test_features.py` | bounds, sign conventions, kill-range gate, memo-invariance |
| Matrix | `tests/unit/strategy/test_matrix.py` | terminals exact; an all-`+1` row when the cop is adjacent with quota |
| Mover | `tests/unit/strategy/test_valuebrain.py` | legality, provenance, seed reproducibility |
| Training | `tests/unit/training/*` | gradient descends, samples drop opening and terminal, starts are legal |
| Integration | `tests/integration/*` | a full game plays to a terminal outcome through the network seam |

**The load-bearing test:** `test_joint_game.py` asserts both brains are handed the *same*
state object before the turn resolves. That property is this phase.

## 5. Training regime

- **Batch-synchronous generations.** Weights frozen for a whole generation, one update at
  the end — removes within-batch non-stationarity by construction.
- **Randomised starts.** Book §3.3 marks both start cells *negotiated*; 30% book opening,
  70% sampled positions with partial barriers and a spent clock.
- **Anchored pool.** Self-play 35%, past snapshots 20%, prior 15%, naive 20%, barrier-blind
  naive 10%. The three fixed anchors together outweigh self-play, so a generation that
  starts losing to them has regressed regardless of the self-play curve.
- **Seats alternate strictly**, so both rates are reported on equal sample sizes.

## 6. Risk register

| Risk | Mitigation | Residual |
|---|---|---|
| Trained weights worse than the prior | `run_eval.py` compares them on held-out anchors; the prior ships if it wins | none — §6.3 makes learning optional |
| Overfitting to our own sparring partners | fixed non-drifting anchors + a barrier-blind variant | an opponent unlike all three; rule 52 permits unscored warm-ups to scout one |
| Depth-1 myopia | structure features + the explicit kill-range feature | a deliberate multi-turn trap; stated in PRD §6 |
| Rules disagreement at the audit | BOOK_ONLY default, declaration round-trip tested | none identified |
| Feature cost on a slower machine | measured 3.62 ms against a 30 s timeout — 4 orders of margin | none |
