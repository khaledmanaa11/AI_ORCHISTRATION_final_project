---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: PHASE 7 PLAN 00 EXECUTED (2026-08-17) -- THE ONE NUMBER WHOSE SANCTION IS
  ABSOLUTE DISQUALIFICATION WAS FALSE, AND PHASE 7 WAS ABOUT TO TRANSMIT IT. Rule 38
  (docs/RULES.md:79) makes a false games-played declaration an absolute disqualification, and
  it ships inside declaration_<game_id>.json. Measured before any change: police 1881, thief
  1874, and ONE `uv run pytest tests/` run advanced each by exactly 14 (-> 1895/1888). So ~1881
  was on the order of 134 test runs of phantom games plus dev launches and gate measurements;
  independent proof it never counted games is that two agents which only ever played EACH OTHER
  stood 7 apart. TWO DEFECTS, the first stated by the code against itself:
  `step0_collect.record_game_played`'s docstring has always read 'increment by exactly one,
  durably, AT GAME END ONLY' while it was called from `agent_step0_wiring.py:93` inside the
  Step-0 DECLARATION path, which runs at game START -- so aborted handshakes and watchdog kills
  counted. The second is scope: the path derives from `cfg.config_dir` and the suite runs
  against the real `config/police/`, so every pytest run mutated production state.
  `record_completed_game(cfg, outcome)` is now a SEPARATE function from `declare_step0`, so rule
  38's WRITE and the declaration's READ cannot be conflated again, and `tests/_shipped_config_guard.py`
  closes the test seam STRUCTURALLY -- a test reaching for the shipped counter FAILS LOUDLY
  rather than being silently redirected, because a silent redirect would hide the next instance
  of this same bug. HEADLINE MEASUREMENTS, re-run by the orchestrator rather than inherited:
  full suite 1910/1903 -> 1910/1903, DELTA 0/0 (1557 passed, 96.65%); one real game via
  dev_launch.py 1910/1903 -> 1911/1904, DELTA 1/1, exit 0. WHAT KEPT THE BUG ALIVE:
  GATE-6-MEASUREMENT.md:178-184 certified the inflation as 'the shipped, correct behavior of the
  counter, not a bug this script introduces' -- a document asserting a bug is intentional turns
  every future reader away at the door. Withdrawn in place with a dated correction; the original
  paragraph is preserved byte-for-byte beneath it and nothing else measured there is affected.
  THE VALUE IS DELIBERATELY UNSET. Whether a 'game played' means league games only, any real
  two-machine round, or local self-play is a judgement about how the USER is represented to the
  league; being wrong in either direction is the same rule-38 breach, the file is gitignored so
  git cannot settle it, and inventing a number would BE the violation this plan prevents.
  `docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md` gives the evidence and the candidate
  readings and states 'No option is selected here.' The human sets it at 07-10, BEFORE ANY LIVE
  SEND. Commits 8e1f355 / 51b1f9b / ab50b6b. DEVIATION: the executing agent was killed by
  ECONNRESET during its final gate run, after all three task commits had landed with a clean
  tree; the orchestrator re-measured both headline numbers from scratch, confirmed the two
  document corrections on disk, and wrote the SUMMARY and this entry. No task was re-executed.
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
