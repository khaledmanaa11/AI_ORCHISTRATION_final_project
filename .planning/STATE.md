---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: PHASE 7 PLAN 03 EXECUTED (2026-08-17) -- THE RULES 8-9 FIREWALL IS BUILT, AND ITS
  COUNTER-CONTROLS ARE MEASURED RATHER THAN ASSERTED. Rule 9 (docs/RULES.md:30) makes displaying
  the objective board state in the live interface a PROJECT DISQUALIFICATION and RULES.md:115
  ranks it third among the cheapest ways to score zero. AN IMPORT BOUNDARY IS NOT THE FIREWALL:
  GameState is exactly {cop, thief, barriers, barriers_placed, turn} and turn_language.py:57
  reads ctx.state.thief on every cop turn from turn 1, so a gui/ module could import nothing
  forbidden and still read the opponent's true cell -- the leak is a FIELD READ. THE MITIGATION
  IS A CLOSED FIELD SET: sdk/local_view.py is four FROZEN dataclasses with twelve LocalView
  fields pinned by name (role, board_size, turn, own_cell, declared_barriers, barriers_placed,
  belief, scent, hints, machine_state, idle_seconds, watchdog_threshold_seconds) -- no
  GameState, no AgentContext, no free-form dict, no extras. They live in sdk/ and NOT gui/,
  because pyproject.toml:38 omits */gui/* from coverage and redaction logic there would be
  invisible to the gate; no logic was put in scripts/ either, which is scanned by NEITHER gate.
  THE DENSIFICATION IS THE NON-OBVIOUS HALF: ScentField keys its grids by coordinate, so handing
  those to a view would put EVERY cell on the board into it as a VALUE, the opponent's among
  them -- both scent grids and the belief posterior are positional row-major floats instead
  (reverting: belief 7 failed, scent 6 failed). THE VACUITY WAS DEMONSTRATED, NOT ASSUMED: with
  coordinate_hits mutated to always return clean, the absence test STILL PASSES 2/2 while
  exactly the three counter-controls fail -- which is why (b) the leaky-view control and (c) the
  anti-vacuity control exist. LeakyLocalView (an honest view with the true cell bolted on, never
  importable from pursuit) is REPORTED with the hit path naming true_opponent_cell, all five
  planted encodings are reported, and the same scanner over the HONEST payload finds all four
  cells the view may legally carry. Coordinates chosen, not arbitrary: OPPONENT_CELL (5,3)
  differs from own (0,0), both barriers and the belief argmax (6,6), and its flat indices 38/26
  differ from every other integer in the view. THE CI GATE FAILS LOUDLY ON AN EMPTY SCAN:
  check_no_llm_in_strategy.py's rglob shape returns [] for a missing root and prints OK, and
  src/pursuit/gui/ does not exist until 07-06 -- so gui_module_paths raises EmptyScanError,
  main returns ExitCode.EMPTY_SCAN (2), and the OK line prints the module count. Measured today:
  exit=2, "local-truth gate scanned nothing: <repo>/src/pursuit/gui does not exist." The
  workflow job is therefore RED until 07-06, DELIBERATELY -- skipping when the directory is
  missing is the same vacuity moved from the script into the workflow (filed D7-6 with the
  rejected alternatives). THIRTY REVERT PROBES, every count real: view carries the opponent cell
  3 failed; extras field 1; coordinate-keyed belief 7; coordinate-keyed scent 6; scanner always
  clean 3; each scanner branch 1/1/1; never descends 3; fabricated belief 1; bool stamp guard 2;
  coerced intent 3; unguarded peer payload 1; dedupe removed 1; MODULE-LEVEL GLOBAL history 5;
  gate missing-root 1; zero-module root 1; ImportFrom hole 1; field-chain check 3; allowlist
  emptied 2; module count dropped 1; log2 -> ln 1; engine_agent inverted 3; a NEW sdk module
  reading ctx.state.thief 1; dict-typed field 1; stray GUI_ROOT 1; unfrozen dataclass 1;
  import check removed 1; bare startswith 3; two thinned literal sets 1 and 2. FOUR HOLES THE
  SELF-AUDIT FOUND IN ITS OWN WORK: probe 15 first returned 0 failed because the mutation only
  DECLARED two globals and never wired them into the dataclass defaults -- the hazard ran not at
  all, the 07-02 lesson repeating on my own first probe; probe 24 ran halfway, aliasing one
  ctx.state read while ctx.state.barriers two lines below kept the AST chain alive; the entropy
  extraction had NO PINNED VALUE, the only assertions in the whole repo being >= 0.0 and is not
  None, both of which hold under ln as readily as log2 -- now pinned at exactly log2(49) with
  both consumers asserted to agree, and confirmed live (turn-0 entropy 5.6108 vs log2(49)
  5.6147, ln(49) 3.8918); and two tests were shape-only plus one loop vacuous, all three now
  pinned on values. An AST scan found ONE parametrize site in the plan's five test files
  (already guarded) but two unguarded module-level literal tuples iterated in assert-bearing
  loops -- both now counted. TWO EXTRACTIONS, each because the alternative was a second copy:
  shared/roles.py takes engine_agent/opponent_role out of network/orchestrator.py (sdk/ and the
  07-06 gui/ both need the vocabulary and NEITHER may import pursuit.network) re-exported so no
  call site changed; BeliefMap.entropy() takes the Shannon formula to the object owning the grid
  at its second consumer. PRODUCTION READERS OF THE TRUE POSITION, GREPPED EXHAUSTIVELY:
  turn_actions:184, turn_commit_ledger:66, turn_language:57/78/90/93 (all the turn loop) and
  sdk/view_builder:95/101/102 -- the only new one, asserted by an AST scan of src/pursuit/sdk/
  on every run with its own counter-control and a forward probe (a planted leaky_panel.py fails
  it). SCOPE: nine files outside tests/, git diff over src/pursuit/security/,
  agent_step0_wiring.py, handshake_evaluate.py, agent_wiring.py, turn_actions.py, turn_commit.py
  and ALL of config/ is EMPTY; the workflow edit is +18/-0. GATES: ruff 0, line-limit exit 0
  including all 12 new/edited paths checked EXPLICITLY, 1826 passed from a 1794 baseline,
  coverage 96.95% from 96.90%, local_view/view_builder/roles/belief/turn_language all 100%,
  check_no_llm_in_strategy OK, check_local_truth exit 2 as designed, dev_launch exit 0 with
  outcome capture, audit_verdict matched=true, zero technical_*, zero STEP0_MISMATCH and the one
  pre-existing D7-5 illegal transition. GAMES-PLAYED, rule 38: full suite 1913/1906 -> 1913/1906
  DELTA 0/0; one real game 1913/1906 -> 1914/1907 DELTA 1/1. Nothing here reads, writes,
  defaults or reads around the counter; the VALUE remains the human's at 07-10. Commits 70df24a
  / f7d21c6 / 1ccd4ea / 094eb12 / 7c69f81.
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
