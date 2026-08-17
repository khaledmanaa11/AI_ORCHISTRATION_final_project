---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 07-03 is fully committed and closed, tree clean. **WAVE 1 IS COMPLETE**
  (07-01, 07-02, 07-03 all executed and summarised). Next is WAVE 2: 07-04 (mail transport,
  depends_on 07-01 + 07-02), 07-05 (log_ builder) and 07-06 (live GUI, the consumer side of
  D-74). Running any two in parallel needs WORKTREES -- the shared git index mixes commits and
  the whole-tree pre-commit hook blocks everyone. WHAT 07-03 LEAVES FOR 07-06, AND IT IS TWO
  THINGS NOT ONE: (1) the whole 07-03 surface -- build_local_view, HintHistory, LocalView -- has
  no PRODUCTION caller yet and HintHistory.record_outgoing has none at all, structurally rather
  than by omission since this plan's non-goals exclude every line of Tkinter (D7-7, the third
  occurrence of D7-3); and (2) THE local-truth CI JOB IS RED UNTIL 07-06 CREATES
  src/pursuit/gui/, by construction -- 07-06 turns it green by writing modules that pass the
  check, and must not be tempted to soften the gate instead (D7-6). Seven deferred items now sit
  in the phase's deferred-items.md: D7-1 RESOLVED, D7-2, D7-3, D7-4, D7-5, and the two new ones.
  Also recorded in D7-6 and NOT fixed per the scope boundary: check_no_llm_in_strategy.sh has
  been absent from quality-gate.yml since 03-10 and still is -- pre-existing and unrelated,
  so not slipped into a commit about a different gate. OQ-1/OQ-2/OQ-3 are CLOSED in code with
  citations; OQ-4 is resolved in the outline but not implemented; OQ-5 -- the games-played
  VALUE -- remains the human's at 07-10, before any live send. Nothing in this repo transmits:
  every shipped config carries reporting.mode dry_run.
stopped_at: PHASE 7 PLAN 11 EXECUTED (2026-08-17) -- THE COP WAS PUBLISHING THE THIEF'S EXACT
  CELL, AND 07-03'S FIREWALL WAS GREEN BECAUSE ITS FIXTURES WERE VACUOUS. Rules 8-9 are an
  ABSOLUTE DISQUALIFICATION (docs/RULES.md:30). TWO INDEPENDENT FIXTURE DEFECTS made every
  assertion in that area worthless: local_view_fixtures.scent_field never called emit_opponent,
  so view.scent.opponent was an ALL-ZERO grid in all thirty of 07-03's revert probes -- the one
  field carrying the true cell at full strength was empty in every test written to protect it --
  and honest_context seeded belief with observe_exact((6,6)), a cell production never supplies.
  Corrected to run ONE real decide(known_cell=ctx.state.thief), 07-03's own load-bearing absence
  test FAILED at '$.belief.argmax: pair [5, 3]'. THE MEASURED LEAK, through the shipped path with
  the real config/police/*.json: belief argmax (5,3) == ctx.state.thief; entropy 1.8799649487271113;
  support [(4,3),(5,2),(5,3),(5,4),(6,3)], 5 of 49, P(true) 0.5556; scent.opponent argmax (5,3) at
  0.9, which is EXACTLY scent.json's "source" -- the unmixed kernel centre, not a decayed trace.
  THE OBVIOUS FIX IS A TRAP AND IT WAS RUN: publishing the strategy maps again and deleting
  BeliefView.argmax makes 07-03's coordinate scanner PASS 2/2 -- a clean verdict -- while the
  geometric, scent and floor tests all FAIL, because observe_exact gives a delta, spread disperses
  it only over that cell's legal destinations and update multiplies pointwise so a zeroed cell
  never reopens: the published support IS the legal-move plus centred on the true pre-move cell,
  and the centre of a plus inverts uniquely. A fix validated by a coordinate-absence test would
  have looked successful and shipped the disqualification. THE SEALED-THIEF ENDGAME IS WORSE AND
  IS THE COP'S WIN CONDITION, not a corner case: thief walled at (0,0) behind 2 barriers against a
  quota of 14 published argmax (0,0), entropy -0.0, lit cells [(0,0,1.0)] -- a one-pixel heatmap on
  the truth. IT WAS REAL IN A REAL GAME, not only in a fixture: logs/police/29dec44e0ab71785.jsonl
  records cop belief_entropy 5.6108 at turn 0 then 1.8800/1.8800/1.8800/1.7159, while the thief's
  stayed 5.6131/5.6100/5.5183/5.4697. OPTION (a) CHOSEN AND WRITTEN DOWN (source + the new
  docs/PRD_display_belief.md, which CLAUDE.md Sec2.3 requires anyway): a display-only BeliefMap
  never fed ctx.state.thief, driven by the legal-motion model and the opponent's own broadcast
  hints, published in place of the strategy map. Option (b) -- publish only when observe_exact did
  not fire -- is for the COP a PERMANENTLY BLANK PANEL, since turn_language.py:57 returns the true
  cell on every turn but turn 0; it hides the leak by deleting the feature. NOBODY OWNED RULE 9
  BEFORE THIS: beliefadapter.py:120-123 said in its own docstring that local truth was "a
  display-layer concern, not this one's" and view_builder published the value unredacted -- both
  delegated, neither owned. strategy/display_belief.py owns it now. THE STRATEGY BELIEF IS
  UNCHANGED and still receives known_cell (argmax still (5,3), entropy still 1.88): provenance is
  the opponent's own honest Reveal and rule 9 governs the DISPLAY, not play. scent.opponent IS
  FIXED TOO because it leaks independently -- uniform scalar decay lets two published snapshots
  subtract to recover the fresh deposit, so even an animate-only GUI leaked every turn; scent.own
  is passed through untouched at 1.8, local truth by definition. AFTER: published argmax (1,3),
  entropy 5.5469, support 47/49, P(truth) 0.0223, inversion [], scent peak (4,4) at 0.154; sealed
  case argmax (1,2), entropy 5.5472, support 47. COP SEAT ONLY BY PROVENANCE, NEVER BY ROLE NAME:
  the substitution fires on a contamination flag, so the thief's published belief is BYTE-IDENTICAL
  before and after -- sha256 0b046a9430b79af3d1b7f3a58a4bf91ffdce383d739d3d5267f3e03e1ba0e3b0,
  2565 bytes, argmax (4,5), entropy 5.5328, support 47 -- and a future path that contaminated a
  different seat is covered without an edit. FLOORS ARE DERIVED, NEVER INVENTED (CLAUDE.md rule 1,
  D-18): belief.json gains display.min_support_cells 6 (one cell's legal destination set is STAY
  plus four orthogonal moves = len(DIRECTION_WORDS) = 5, so a support of 6+ cannot fit inside any
  cell's neighbourhood and the inversion is structurally empty) and display.min_entropy_bits 1.0
  (a fair coin between two cells); validate_display_floors REFUSES a floor at or below
  MAX_STEP_NEIGHBOURHOOD, because a floor that admits the measured leak is not a floor. TWELVE
  REVERT PROBES, every count real: strategy belief republished 9; raw scent republished 3; the
  argmax-only fix 3 failed / 2 PASSED (the scanner); publishable() hard-wired True 2; contamination
  never recorded 14; display map fed the truth 9; the SYMMETRIC fix (thief redacted too) 3; advance
  made inert 3; geometric_inversion always [] 2; grid_argmax always (0,0) 2; min_support_cells
  lowered to 5 22 failed + 12 errors; published_scent leaking the raw grid 3. Probe 3's first
  attempt reported "anchor not found" (a trailing \n against a CRLF tree) and was NOT counted as a
  pass -- it was rewritten to report per-test outcomes. Probes 8/9/10 exist because this
  mechanism's likeliest failure is an inert display map or an attack that never fires, either of
  which would make every assertion pass vacuously. AST scan of all eight touched test files: one
  parametrize site and one module-level literal looped in an assert, BOTH already length-guarded,
  zero unguarded. Production callers grepped for all 13 new names: ten external; publishable,
  contaminated and MAX_STEP_NEIGHBOURHOOD are reached only from inside their own module, by
  published_belief/published_scent and validate_display_floors, all of which are on the production
  path -- proven live by probes 4 and 11. THREE FALSE DOCSTRINGS IN local_view.py CORRECTED, each
  now saying what it used to claim: "cannot express an opponent's true cell" (a dense grid
  expresses one without any coordinate in it), "argmax ... is routinely wrong; that is exactly why
  it is legal to draw" (observe_exact made it RIGHT every turn by construction) and "our own
  RECONSTRUCTION ... not a live reading of where it is now" (the kernel was stamped on the true
  CURRENT cell at source strength). FOUR FILES SPLIT AT THE 150-LINE GATE, never compressed:
  BeliefKey to shared/belief_keys.py (which also removed a real cycle -- every group module is
  imported BY belief_config.py, so the newest group could not name its fields canonically),
  scent_likelihood checks to shared/scent_likelihood_config.py, 07-03's scanner to
  tests/unit/local_view_scanner.py, and the display rationale to docs/PRD_display_belief.md.
  D7-8 FILED AND DELIBERATELY NOT FIXED: turn_language.belief_snapshot still writes the true argmax
  to the JSONL, which is CORRECT -- the log is the audit record (rule 38) and rules 8-9 govern the
  LIVE interface -- but 07-08's replay viewer may not render it live. D7-9 restates that
  check_local_truth.py CANNOT see a coordinate that is drawn rather than named and was not cited as
  evidence anywhere in this plan. 07-06 AND 07-08 WERE BLOCKED ON THIS AND ARE NOW UNBLOCKED;
  07-06 must also render belief=None gracefully, which is now a LIVE case (the floor guard), not
  only the belief-disabled one.
---

Last session: 2026-08-17T09:20:00+03:00
Stopped at: Completed 07-11-PLAN.md (the display belief -- rules 8-9 recovery, not absence)
  in full. Three tasks, each committed atomically: Task 1 the RED reproduction on fixtures
  rebuilt to model production (`4c4c03d` -- 9 failed / 45 passed, including 07-03's OWN
  load-bearing absence test failing at `$.belief.argmax: pair [5, 3]`, with both anti-vacuity
  controls passing so the attack was proven to fire before being used as evidence), Task 2 the
  root-cause fix at the strategy layer with option (a) reasoned in source and in the new
  `docs/PRD_display_belief.md` (`19aa946`), Task 3 the three false docstrings corrected and the
  byte-level thief control added (`df041a0`). Gates: `ruff check .` 0 violations; 1846 passed /
  0 failed against the 1826 baseline; coverage 96.95% (baseline 96.95%); `check_line_limit.sh`
  exit 0 with all nine new files ALSO checked explicitly by path; `check_no_llm_in_strategy.py`
  OK; `dev_launch.py` exit 0 with both sides `"matched":true`. Rule-38 counters, all four:
  the full suite moved police 1914->1914 and thief 1907->1907 (delta 0/0); one real game moved
  1914->1915 and 1907->1908 (delta 1/1). Graphify refreshed -- `DisplayBelief` at
  `display_belief.py:50`, degree 25, edges to BeliefMap/ScentField/DisplayFloors and from
  BeliefAdapter. `07-11-SUMMARY.md` written with every number from a run in this session,
  self-check PASSED (23 files and 3 commits verified). `docs/phases/phase-7/TODO.md` gains a
  ticked 07-11 row; D7-8 and D7-9 filed in the phase's `deferred-items.md`.
Resume file: None -- the tree is clean and 07-11 is closed. Wave 2 of phase 7 is next
  (`/gsd:execute-phase 7`): 07-04, 07-05, and 07-06, which was BLOCKED on this plan and is
  now unblocked. 07-08 is likewise unblocked but inherits D7-8.
---

Last session: 2026-08-17T05:40:00+03:00
Stopped at: Completed 07-03-PLAN.md (the rules 8-9 local-truth firewall) in full. Three
  tasks, each committed atomically: Task 1 the RED tests taken BEFORE the fix (`70df24a`
  -- two collection ERRORs naming the missing modules and 8 failures naming the missing
  script, quoted verbatim in the commit message), Task 2 `LocalView` + `view_builder`
  outside `gui/` (`f7d21c6`), Task 3 the CI gate wired and loud on an empty scan
  (`1ccd4ea`). Two further commits closed self-audit findings in my own work: the
  unpinned entropy value plus the 150-line test split (`094eb12`), and the two unguarded
  literal sets plus an unreachable `None` annotation (`7c69f81`). `07-03-SUMMARY.md`
  written with the three pre-fix failures verbatim, the production-caller grep, the
  thirty probe counts and the noted absence of `check_no_llm_in_strategy.sh` from CI.
  `docs/phases/phase-7/TODO.md` row 07-03 ticked with its measured evidence; D7-6 and
  D7-7 filed in the phase's `deferred-items.md`.
Resume file: None -- wave 1 of phase 7 is complete and the tree is clean. Next is
  `/gsd:execute-phase 7` continuing into wave 2 (07-04, 07-05, 07-06).
---

Last session: 2026-08-04T12:31:00+03:00
Stopped at: Completed 03-11-PLAN.md (graph primitives, run-2 wave 1's first plan) in
  full. All 3 tasks executed TDD (tests written and confirmed red before each
  implementation went green), each committed atomically: Task 1 `components.py`
  (`12be2e4`), Task 2 `cycles.py` (`52c85f2`), Task 3 `territory.py` (`b4b06fa`). A
  4th commit (`af5f0de`) closed a Rule-2 coverage gap found during final verification
  (two documented contract branches -- the DFS-root cut-vertex case and
  `cycle_rank(frozenset())==0` -- had no direct test; 2 tests added, package coverage
  98%->100%). `03-11-SUMMARY.md` written. Full repo gates green: `ruff check .` 0
  violations, line-limit clean (new files 100/37/55/32 code lines), 456 passed / 2
  skipped (the pre-existing GATE-4 skip, untouched), coverage 97.05% (>=85% floor).
  Graphify rebuilt and `GRAPH_REPORT.md` refreshed (3457 nodes/6273 edges/234
  communities). `docs/phases/phase-3/TODO.md` deliberately not touched -- its
  03-11..03-16 row numbering predates the 15-plan wave breakdown and reconciling it is
  03-24's ("triplet refresh") explicit job.
Resume file: None -- 07-00 is fully committed and closed. **Next step is the phase-7 plan
  set**: `07-PLAN-OUTLINE.md` defines 10 plans across 5 waves (07-01..07-10), of which only
  07-10 is `autonomous: false` (OAuth consent, one live send, presentation screenshots, and
  the games-played value decision). Plans 07-01..07-09 are not written yet. Wave 1 is a
  genuine three-way fan-out (07-01/07-02/07-03, no shared files) and would need WORKTREES to
  run in parallel -- the shared git index otherwise mixes commits. Four open questions from
  the outline still need deciding from the book/PARAMETERS rather than invented: OQ-1 daily
  send ceiling, OQ-2 DOS trip threshold, OQ-3 backoff 'stricter value' ambiguity, OQ-4
  result_ per-series vs per-game. OQ-5 was this plan.
---

Last session: 2026-08-04T13:00:00+03:00
Stopped at: Completed 03-12-PLAN.md (thief safety rule -- never step into N[cop], run-2
  wave 1's second plan) in full. Both tasks committed atomically: Task 1 `safety.py`
  (`71b201d`, test-first: `test_safety.py` confirmed red against a `ModuleNotFoundError`
  before the module existed, green after -- 7 unit tests), Task 2 wiring + regression
  guard (`20d87f6`). `src/pursuit/strategy/safety.py` -- `closed_neighbourhood`/
  `safe_moves`, pure (D-03), never-empty guarantee, docstring carries the full D-31
  296/300=0.987 vs 283/300=0.943 provenance plus the unsoftened "did not fully
  reproduce, lost 3/20, flawed control" caveat. `fallback.py::_evade` filters legal
  moves through `safe_moves` before ranking with the UNCHANGED
  `(unreachable?, distance, onward)` key -- filter-then-rank, `_pursue` byte-identical.
  `tests/unit/strategy/test_fallback.py` needed zero changes (verified before/after,
  all 6 cases hold under the filtered behaviour). New
  `tests/integration/test_thief_safety.py`: non-vacuous 160-game regression guard, two
  arms differing ONLY by `monkeypatch.context()`-scoped patches of `fallback.safe_moves`
  (real spy vs no-op) against the same 20 committed GATE-4 scenarios + 60 seeded random
  starts (`n=60`, `REGRESSION_TOLERANCE=0.05`, `seed=314159`, named test-local
  constants, D-19); asserts grid filtered-survival >= unfiltered, random-start rate
  within one noise band, filter-bound counter > 0 (non-vacuous), and the per-turn
  N[cop] invariant across all 160 games via a spy wrapper. Does not reproduce D-31's
  own flawed disabled-barrier control. `03-12-SUMMARY.md` written (self-check PASSED).
  One deviation, a documentation correction (not a code fix): the plan's own
  ~100ms/game timing estimate did not reproduce -- measured ~34-38s for the 160-game
  suite, `cProfile`-traced to 03-07's pre-existing `choose_barrier` (out of this plan's
  scope), not this plan's own code. Recorded honestly in the test module's own
  docstring; `n=60` was NOT reduced and barrier placement was NOT disabled to chase the
  stale target. Full repo gates green: `ruff check .` 0 violations, line-limit clean
  (new files 50/76/157 code lines, `fallback.py` still well inside its own ceiling),
  464 passed / 2 skipped (same 2 pre-existing skips as 03-11), coverage 97.95%
  (>=85% floor), `safety.py`/`fallback.py` both individually 100% covered. Full-repo
  `--cov` run took 7m47s on this Windows machine, confirmed genuinely CPU-bound
  throughout (`Get-Process ... CPU`), not the known Windows stdio-hang pattern.
  Graphify rebuilt (3523 nodes/6406 edges/233 communities) and `GRAPH_REPORT.md`
  refreshed and committed. `docs/phases/phase-3/TODO.md` deliberately not touched --
  same rationale as 03-11 (03-24's "triplet refresh" job).
Resume file: None -- 07-00 is fully committed and closed. **Next step is the phase-7 plan
  set**: `07-PLAN-OUTLINE.md` defines 10 plans across 5 waves (07-01..07-10), of which only
  07-10 is `autonomous: false` (OAuth consent, one live send, presentation screenshots, and
  the games-played value decision). Plans 07-01..07-09 are not written yet. Wave 1 is a
  genuine three-way fan-out (07-01/07-02/07-03, no shared files) and would need WORKTREES to
  run in parallel -- the shared git index otherwise mixes commits. Four open questions from
  the outline still need deciding from the book/PARAMETERS rather than invented: OQ-1 daily
  send ceiling, OQ-2 DOS trip threshold, OQ-3 backoff 'stricter value' ambiguity, OQ-4
  result_ per-series vs per-game. OQ-5 was this plan.
