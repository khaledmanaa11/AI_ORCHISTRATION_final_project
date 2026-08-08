# Phase 3 TODO — run 2

Definition of done for every task: code + tests landed, `uv run pytest` green,
`uv run ruff check` clean, every file ≤150 code lines, committed.

Run 1's task list is withdrawn wholesale — see [PRD §2](PRD.md). It planned a deeper
tabular Q-learner for a game that turned out to be simultaneous, which made the whole
approach unsound rather than under-trained.

---

## Wave 1 — the rules, settled from the book

- [x] **03-20a** Read the book directly (§3.4, §3.5, §5.2, §5.3, Appendix ה, Appendix ו) and
      settle every resolution predicate. → [RULES-RESOLUTION.md](RULES-RESOLUTION.md)
- [x] **03-20b** Establish that the turn is simultaneous, with the quote that proves it
      (§5.3.2 p.35) rather than by inference.
- [x] **03-20c** Record the binding parameter table and its status column
      (*fixed* / *minimum* / *negotiated*) from Appendix ו.
- [x] **03-20d** Record the league facts that shape strategy: one counted game per opponent
      (rule 52), unscored warm-ups permitted, code may change between games.

## Wave 2 — the engine becomes simultaneous

- [x] **03-21a** `resolve_turn` — one joint resolver; both actions validated; turn advances once.
- [x] **03-21b** `sdk/actions.py` — `CopAction` (move XOR barrier), both action generators.
      Cop's own cell is a legal barrier target (§3.4), which the old engine rejected.
- [x] **03-21c** `sdk/terminal.py` — the six predicates in order, BOOK rows unconditional.
- [x] **03-21d** Fix: `apply_move` validated nothing.
- [x] **03-21e** Fix: thief could step onto the cop uncaptured and escape.
- [x] **03-21f** Fix: rule 47 was unreachable dead code.
- [x] **03-21g** Negotiated resolution block, outside `game_params.json` (ADR-02).
- [x] **03-21h** Migrate the network layer to buffer both moves and resolve once.
- [x] **03-21i** Delete `shared/capture.py` — its semantics are now wrong.
- [x] **03-21j** Enable the ruff and pytest gates that were commented out of the hook and CI.

## Wave 3 — the mover

- [x] **03-22a** `graphcache.py` — memoised passability, regions, chokepoints, BFS maps.
- [x] **03-22b** `features.py` — φ(s), 15 components, all scaled from `GameParams`.
- [x] **03-22c** `equilibrium.py` — pure saddle, else regret matching; seeded sampling.
- [x] **03-22d** `matrix.py` — one-ply joint expansion, bounded leaf values.
- [x] **03-22e** `valuebrain.py` — one brain, both seats, seeded and reproducible.
- [x] **03-22f** `weights.py` — artefact I/O + the hand-set prior; fail-loud on a missing
      configured file.
- [x] **03-22g** `naive.py` — the two fixed sparring anchors.
- [x] **03-22h** Benchmark the decision cost before building on it. **3.62 ms cold** against
      a 30 s timeout; ~14,200 self-play games/hour/core.
- [x] **03-22i** Add `thief_in_kill_range` after measuring that rule 46 makes distance 1 a
      forced loss the depth-1 search could not see. Worth **15% → 64%** thief survival.

## Wave 4 — training

- [x] **03-23a** `joint_game.py` — the single game loop; both brains decide from one state.
- [x] **03-23b** `starts.py` — randomised start distribution (the fix run 1 most needed).
- [x] **03-23c** `pool.py` — anchored opponent pool.
- [x] **03-23d** `fit.py` — outcome regression with Adagrad.
- [x] **03-23e** `generation.py` / `run_selfplay.py` — batch-synchronous generations.
- [x] **03-23f** `evolve.py` / `run_evolve.py` — `(1+λ)`-ES on league points, common random
      numbers.
- [x] **03-23g** `arena.py` / `run_eval.py` — held-out evaluation, 95% Wilson intervals.
- [ ] **03-23h** Run both optimisers to completion and record the curves.
- [ ] **03-23i** Choose the shipped artefact by held-out comparison against the prior.

## Wave 5 — retire run 1

- [ ] **03-24a** Delete the tabular Q-learning stack and every module that depends on it.
- [ ] **03-24b** Relocate any test covering behaviour that survives.
- [ ] **03-24c** Registry reduced to three brains; strategy config keys pruned to what is read.

## Wave 6 — close the phase

- [ ] **03-25a** Full suite green, coverage ≥85%, ruff clean, line limit clean.
- [x] **03-25b** Per-mechanism PRD for the mover → [docs/PRD_matrix_mover.md](../../PRD_matrix_mover.md).
- [x] **03-25c** Phase triplet refreshed (this file, PRD, PLAN).
- [ ] **03-25d** Refresh the knowledge graph in `.planning/graphs/`.
- [ ] **03-25e** Tick the matching rows in the root `docs/TODO.md`.

## Withdrawn from run 1

- **T4-followup / 03-15 / 03-16 / 03-17..03-19** — deeper tabular learner, feature-vector
  bolt-on, alpha-beta over the sequential engine. All assumed a sequential turn order that
  contradicts §5.3.2. Superseded by Waves 2–4.
- **GATE-4 as specified** — measured a Q-table that no longer exists. Replaced by AC-7,
  which compares against the prior with intervals instead of against a bare threshold.
