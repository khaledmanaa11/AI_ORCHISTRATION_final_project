---
phase: 03-blind-strategy-module-rl-policy
verified: 2026-08-16T18:38:20Z
status: passed
score: 3/3 §10.4 criteria verified — but criterion 1 carried ZERO automated evidence until this pass
retroactive_authorship:
  written: 2026-08-16
  phase_closed: 2026-08-08
  closed_by: "chore commit da345dd (`chore(gsd): reconcile planning state -- phase 3 closed,
    12 plans superseded`), NOT by /gsd:verify-work 3. No verifier ran at closure time. This
    document is written eight days late and says so; every claim below was measured against
    live HEAD on 2026-08-16, never carried over from a SUMMARY."
  why_it_matters: "Phase 3 was the only build phase with neither an NN-VERIFICATION.md nor a
    GATE-N-MEASUREMENT.md. Phases 01, 02, 04, 05 and 06 all carry a VERIFICATION; phases 4, 5
    and 6 additionally carry a GATE-N-MEASUREMENT. That absence is what let §10.4 criterion 1
    lose its only test without anything noticing."
descoped_plans:
  count: 12
  ids: "03-14 .. 03-25"
  by: da345dd
  citation: "book §5.3.2 p.35 — the Acknowledge phase 'guarantees that the reveal will occur
    only when both sides have already fixed their moves', so the turn is SIMULTANEOUS"
  reason: "All twelve specified alpha-beta search bolted onto the sequential engine with the
    Q-policy demoted to an evaluation. Alpha-beta is meaningless under simultaneous moves.
    Each file carries a `⛔ SUPERSEDED — DO NOT EXECUTE` banner and is kept unmodified below
    it as the record. This is why the phase directory holds 26 PLANs and only 14 SUMMARYs:
    14 + 12 = 26, and the 12 with no SUMMARY are exactly the 12 with a banner. Measured."
  completion_mark_is_honest: true
criterion_text_edited:
  which: "§10.4 criterion 2, at .planning/ROADMAP.md:96"
  by: da345dd
  before: "Move selection comes from a tabular Q-learning policy, with a Bayes+Manhattan
    fallback for unvisited states"
  after: "Move selection comes from the algorithm — a solved matrix game per turn, sampled
    from its equilibrium"
  judgement: correction_not_softening
open_deferred_items: []
human_verification: []
---

# Phase 3: Blind Strategy Module — Verification Report (retroactive)

**Phase Goal:** The decision engine, with no scent and no natural language yet.
**Delivered as:** a simultaneous-move matrix-game mover over a learned weight vector.
**Verified:** 2026-08-16 — **written retroactively**, eight days after the phase was closed.
**Status:** passed.

## 0. Why this document is late, and what that cost

Phase 3 was closed on 2026-08-08 by `da345dd`, a **chore commit that reconciled planning
state** — not by `/gsd:verify-work 3`. No verifier ran. The phase went straight from
`f3d9847` (the code) to a ticked `[x]` on `.planning/ROADMAP.md:23`.

That tick is **honest and stays**. The work was done: the turn became simultaneous, the mover
shipped, the trained weights shipped, the run-1 stack was retired, and
`docs/phases/phase-3/TODO.md` is complete and checked. Un-ticking a genuinely complete phase
would itself be a misreport (rule 38).

But skipping the verifier cost one concrete thing, found by audit on 2026-08-16 and closed in
this pass: **§10.4 criterion 1 had no evidence of any kind.** `tests/integration/test_shortest_path.py`
was deleted in `f3d9847` along with the `HeuristicBrain` it drove, with no replacement.
`grep -rln shortest tests/ --include=*.py` returned nothing at HEAD, and the phase PRD's
AC-1..AC-9 (`docs/phases/phase-3/PRD.md` §3) does not cover it either. A verify-work pass in
August would have caught that in its first hour.

## 1. §10.4 milestone gate — criterion by criterion

### Criterion 1 — "Given a known target location, the agent computes and walks the shortest path with no manual intervention"

**Status: ✓ PASS — evidence created in this pass, not found in it.**

| | |
|---|---|
| Evidence | `tests/integration/test_shortest_path.py` + `tests/integration/shortest_path_harness.py`, landed 2026-08-16 |
| Evidence before this pass | **none.** Deleted in `f3d9847`, never replaced |
| Result | **9 passed** (7 parametrized scenarios + 1 anti-vacuity guard + 1 revert probe) |

The test drives the brain that actually ships — `value_search`, built through
`registry.build_brain` from real config, never instantiated directly — against a **frozen**
thief, so the target is a genuinely fixed known location. Three assertions, because no one of
them is sufficient:

1. the run ends in a real `Outcome.CAPTURE`;
2. on every turn the cop **moves**, its barrier-aware BFS distance to the target
   (`graphcache.distances(passable(barriers, board_size), target).get(cop_cell)`) drops by
   **exactly 1** — a shortest walk, not merely a non-increasing one;
3. `move_turns + barrier_turns == the initial BFS distance`.

(3) is the clause that matters. Exempting barrier turns from (2) and stopping there is a
loophole in which a cop that placed barriers forever passes trivially; bounding the **total**
turn count by the BFS distance closes it and catches dawdling at the same time.

Measured walk, all seven scenarios, cop `value_search` vs a frozen thief:

| Scenario | cop → target | initial BFS | move turns | barrier turns | total | outcome |
|---|---|---|---|---|---|---|
| `canonical_opening` | (0,0) → (3,3) | 6 | 5 | 1 | 6 | CAPTURE |
| `far_corner_cop` | (6,6) → (3,3) | 6 | 5 | 1 | 6 | CAPTURE |
| `long_diagonal` | (0,6) → (6,0) | 12 | 10 | 2 | 12 | CAPTURE |
| `same_row_short` | (3,0) → (3,3) | 3 | 2 | 1 | 3 | CAPTURE |
| `already_in_seal_range` | (3,2) → (3,3) | 1 | 0 | 1 | 1 | CAPTURE |
| `barrier_pocket` | (3,1) → (3,5), wall | 10 | 9 | 1 | 10 | CAPTURE |
| `edge_to_edge` | (0,3) → (6,3) | 6 | 5 | 1 | 6 | CAPTURE |

Every move turn dropped the distance by exactly 1 — **zero strict-decrease violations across
all seven**. The final turn is a seal rather than a step in six of the seven (rule 46: sealing
the thief's own cell is a capture); `long_diagonal` ends in a two-seal corner trap (rule 47,
walled-in thief), which is why the assertion bounds `move + barrier` rather than assuming a
single seal.

**Non-vacuity is proven, not asserted.** `shortest_path_harness.DistanceIgnoringCop` steps to
whichever legal cell is *furthest* from the target. Driving the real gate assertions with that
stub monkeypatched over `registry.build_brain`: **7/7 scenarios FAIL**, each on
`AssertionError: <scenario>: never captured the frozen target / assert Outcome.SURVIVAL is
Outcome.CAPTURE`. The committed suite keeps this as
`test_the_gate_fails_a_cop_that_ignores_distance`. An empty-parametrize guard
(`test_the_scenario_set_is_not_empty`) is included because pytest **skips** an empty set in
silence — the trap plan 05-12 hit.

*Recorded because it is a real measurement, not a defect:* the same revert harness run against
`naive.ChaserCop` fails only **1 of 7** (`barrier_pocket`). That is the expected result, not a
weakness in the gate — `ChaserCop` genuinely descends the BFS gradient, so it walks shortest
paths on open boards; it trips the gate in the pocket by sealing the cell it is standing on
(book §3.4 permits this), which puts it off the passable graph and makes its distance to the
target undefined. The gate names that case explicitly rather than raising a `TypeError`.

### Criterion 2 — "Move selection comes from the algorithm — a solved matrix game per turn, sampled from its equilibrium"

**Status: ✓ PASS.**

| Claim | Evidence (measured/source-read at HEAD) |
|---|---|
| A matrix game is built per turn | `strategy/matrix.py::payoff_matrix` — one-ply joint expansion through `resolve_turn`; `tests/unit/strategy/test_matrix.py` |
| It is solved, mixing where mixing is required | `strategy/equilibrium.py::solve` — pure saddle, else regret matching. `tests/unit/strategy/test_equilibrium.py::test_matching_pennies_converges_to_half_half` pins 0.5/0.5 on the canonical no-saddle game; 11 test functions in that module |
| The move is sampled from the equilibrium, reproducibly | `strategy/valuebrain.py::_decide_move` → `equilibrium.sample`, seeded `random.Random`. `tests/unit/strategy/test_valuebrain.py::test_same_seed_reproduces_the_same_decision` and `test_epsilon_zero_reports_equilibrium` (provenance is a data field, never inferred) |
| The **algorithm** decides, never the LLM (rule 25 / STRAT-07) | `scripts/check_no_llm_in_strategy.py` — an `ast` walk over every module in `src/pursuit/strategy/`; `tests/integration/test_strategy_pluggable.py` loads that exact file and calls `find_violations()` directly, so CI and the suite run one implementation, not two |

#### The criterion text itself was edited — stated plainly

`da345dd` **rewrote §10.4 criterion 2** at `.planning/ROADMAP.md:96`. Verbatim diff:

```diff
-  2. Move selection comes from a tabular Q-learning policy, with a Bayes+Manhattan fallback for unvisited states
+  2. Move selection comes from the algorithm — a solved matrix game per turn, sampled from its equilibrium
```

Editing a milestone criterion and then passing it is exactly the move rule 38 exists to catch,
so it is recorded here rather than left in a chore commit's diff. **The judgement, with its
reasoning, verbatim from the audit that produced this document:**

> This is a **correction, not a softening**, because the original text baked a specific
> implementation choice (tabular Q-learning) into what is supposed to be a book criterion, and
> the book makes RL **optional** — it requires that the ALGORITHM, never the LLM, chooses the
> move. The reword moved the criterion CLOSER to the book.

Two facts support that and are checkable independently of the judgement:

- criterion 3, which carries the book's actual requirement ("the algorithm — never the LLM —
  chooses the move"), was **not touched** by `da345dd`. The edit narrowed nothing;
- the mechanism the old text named is gone from the codebase, not hidden: no `QLearningBrain`,
  no `HeuristicBrain`, no Q-table artefact tracked in git. `strategy/registry.py` registers
  exactly `value_search`, `chaser_cop`, `greedy_evader`.

What the reword does **not** do is repair the requirement register: `.planning/REQUIREMENTS.md`
still words **STRAT-01** as "a trained tabular Q-learning policy" and **STRAT-02** as "a Bayes +
Manhattan heuristic fallback". Left as found — that file is unmaintained project-wide (4 of 77
requirements ticked), so correcting only the Phase-3 rows would misrepresent its state. Flagged,
not fixed.

### Criterion 3 — "The strategy module is pluggable via config `[strategy]`, separate from networking; the algorithm — never the LLM — chooses the move"

**Status: ✓ PASS.** Text unchanged since the roadmap was written.

| Claim | Evidence |
|---|---|
| A brain named in real config alone builds and plays to a terminal outcome | `tests/integration/test_strategy_pluggable.py::test_both_brain_classes_build_from_config_alone_and_play_to_terminal` — `value_search` in either seat, `chaser_cop`/`greedy_evader` as the role-specific anchors |
| Swapping brains touches nothing in the network layer | `test_brain_swap_leaves_network_layer_byte_for_byte_unchanged` — a real `git diff -- src/pursuit/network` snapshot before and after, with the git-work-tree dependency declared via `skipif` rather than crashing (`c5a7eae`) |
| Config cannot name an arbitrary importable | `strategy/registry.py` resolves through an explicit dict — never `eval`, `exec`, or an unguarded `importlib` call; unknown names raise and name every known class, never falling back to a default brain |
| The guard can actually fail | `test_check_script_flags_a_synthetic_forbidden_import` and two `pursuit.services` cases, against a synthetic poisoned tree — never by poisoning real source |

## 2. What was descoped, and why the phase tick is still honest

`.planning/phases/03-blind-strategy-module-rl-policy/` holds **26 PLAN files and 14 SUMMARYs**.
That gap is not 12 unfinished plans. Measured: exactly **12 PLAN files carry a
`⛔ SUPERSEDED — DO NOT EXECUTE` banner** — `03-14-PLAN.md` through `03-25-PLAN.md` — and they
are exactly the 12 with no SUMMARY. `14 + 12 = 26`.

`da345dd` put those banners there deliberately, citing **book §5.3.2 p.35**: the Acknowledge
phase *"guarantees that the reveal will occur only when both sides have already fixed their
moves"*, so the turn is simultaneous. All twelve plans specified alpha-beta search over the
sequential engine, which is meaningless under simultaneous moves. Its own commit message states
the risk it was closing: *"Left alone, the next session would run `/gsd:execute-phase 3` and
rebuild the exact defect this phase removed."* Each plan is kept unmodified below its banner as
the record of what was planned and why it was dropped.

The fragments those plans still owed shipped under different names — `training/starts.py`,
`strategy/weights.py`, `training/pool.py` — and `docs/phases/phase-3/TODO.md` tracks the work
that actually happened, wave by wave, fully checked.

**Conclusion: the `[x]` on `.planning/ROADMAP.md:23` is accurate.** The descope is documented,
book-cited, and reversible-by-reading; the deliverables landed.

## 3. Deferred items

`.planning/phases/03-blind-strategy-module-rl-policy/deferred-items.md` logs two, both from
03-13. Both re-checked at HEAD this pass:

| # | Item | Status now |
|---|---|---|
| 1 | `docs/PRD_rl_strategy.md` §2 still documents the deleted `turn_bucket` key format; owner named as **03-22**, which was itself superseded | **CLOSED 2026-08-16.** The whole document is now marked superseded (commit `f2a7940`), which supersedes its §2 with it. The stale key format no longer describes anything anyone should implement |
| 2 | `training/harness.py`'s `EpisodeConfig` docstring still says `turn_bucket_fractions` | **MOOT.** `training/harness.py` does not exist at HEAD — deleted with the run-1 stack (Wave 5, 03-24a). Verified: `training/` holds 11 modules, none of them `harness.py` |

`grep -rn turn_bucket training/ src/` at HEAD matches nothing tracked — the only hit is a stale
`__pycache__/qtable.cpython-311.pyc`, an untracked build artifact.

## 4. Gaps found by this pass

| # | Gap | Severity | Status |
|---|---|---|---|
| 1 | §10.4 criterion 1 had **zero** evidence — the only test was deleted in `f3d9847` with no replacement, and AC-1..AC-9 does not cover it | 🛑 Blocker for the gate, not for the code | **CLOSED** by `tests/integration/test_shortest_path.py` (commit `ee167b0`). The shipped code satisfies the criterion; this was an evidence gap, not a behavioural defect |
| 2 | `docs/TODO.md` row 03-04 was ☑ with the DoD "PRD_matrix_mover.md … PRD_rl_strategy.md superseded", but `PRD_rl_strategy.md` still read a bare `Status: approved` and carried no supersede notice — a **verifiably false tick** (rule 38) | ⚠️ Warning | **CLOSED** by `f2a7940`. The fix writes the banner, making the existing tick true; the tick was not removed, because the replacement PRD really was written |
| 3 | Phase 3 was the only build phase with no VERIFICATION and no GATE-N-MEASUREMENT | ⚠️ Warning | **CLOSED** by this document |
| 4 | `.planning/REQUIREMENTS.md` STRAT-01/02 still describe the withdrawn Q-learning mechanism | ℹ️ Info | **OPEN, flagged not fixed** — see criterion 2 above. That file is unmaintained project-wide (4/77 ticked); a Phase-3-only correction would misrepresent it |

Nothing found in this pass contradicts the phase's own claims about what it built.

## 5. Standing gates — re-run fresh at HEAD (2026-08-16)

| Gate | Result | Baseline before this pass |
|---|---|---|
| `uv run pytest tests/ --cov` | **1516 passed, 0 failed, 96.62% coverage**, 179.55 s | 1507 passed / 0 failed / 96.62% |
| `uv run ruff check .` | **All checks passed!** (0 violations) | 0 violations |
| `bash scripts/check_line_limit.sh` | exit **0**, no output | exit 0 |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports under …/src/pursuit/strategy` | same |
| `uv run pytest tests/integration/test_shortest_path.py` | **9 passed** in 0.18 s | the file did not exist |

**+9 tests, coverage flat at 96.62%.** The delta is exactly this pass's nine new cases
(7 parametrized + guard + revert probe) — no test was deleted, weakened, or relaxed to get
there, and the known pre-existing `test_late_peer_teardown` load flake (deferred item #4 of
Phase 5) did not reproduce on this run.

## 6. What is NOT claimed

- **No new §10.4 measurement was manufactured for criteria 2 and 3.** Both were already
  covered by tests that existed before this pass; this document locates and names that
  evidence, it does not create it.
- **No tracker row was ticked that the evidence does not support**, and no criterion was
  softened. The one criterion edit in the phase's history is `da345dd`'s, recorded in §1 with
  its diff and the reasoning for calling it a correction.
- **This report is retroactive.** It was written on 2026-08-16 by an audit pass, not by
  `/gsd:verify-work 3` at closure time on 2026-08-08. Everything in it was measured against
  live HEAD; nothing was carried over from a SUMMARY on trust.

---

*Verified: 2026-08-16 — retroactive; phase closed 2026-08-08 by `da345dd`*
*Verifier: Claude (audit pass, three-deliverable remediation)*
