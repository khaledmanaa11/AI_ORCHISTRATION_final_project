---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: PHASE 7 PLAN 01 EXECUTED (2026-08-17) -- ONE GATEKEEPER CLASS NOW SERVES BOTH
  CALLERS, AND PHASE 4'S LLM INSTANCE IS PROVEN BYTE-UNCHANGED. Rules 28-29 require a token
  bucket and a DOS detector on the outgoing mail path and SEGAL Sec4 forbids a second
  gatekeeper, so this plan EXTENDED shipped, tested Phase-4 code -- which is what made it
  risky. THE OUTLINE'S LINE BUDGET WAS WRONG AND IT DECIDED THE SHAPE: 07-PLAN-OUTLINE.md
  Sec5 claims `gatekeeper.py` "is at 89 counted lines with room for the GatekeeperParams
  extraction"; measured first with the gate's own awk it is 135/150, `language_config.py`
  139/150, `language_wiring.py` 129/150. Neither host had room, so `GatekeeperParams` landed
  in a new `shared/gatekeeper_params.py` -- and the edit still did not fit: D-68's optional
  budget plus D-69's `bucket_ready` seam took `gatekeeper.py` to 153/150, so `CallResult` and
  `GatekeeperOverflow` (the two types a CALLER imports) split into `gatekeeper_types.py`, the
  04-06 language_model_config.py precedent. Split, never compressed; no docstring trimmed.
  THE CONTROL THAT MATTERED MOST: OQ-3 negotiates the MAIL instance's backoff up to 30 s
  (PARAMETERS:95's 5 s minimum raised toward SEGAL:174's 30, per :182's stricter rule), and a
  silent retune of the LLM instance would have been a Phase-4 regression inside a Phase-7
  commit that no existing test could see -- the shipped gatekeeper tests build their own
  `_params()` doubles and never read `config/`. The LLM gatekeeper's effective parameters were
  dumped through the real construction path before any change and again at the end: police 22
  and thief 22 parameters, IDENTICAL = True, LLM backoff still 5 s while the mail instance
  ships 30 s, `git diff config/*/language.json` EMPTY, every pre-existing Phase-4
  gatekeeper/budget/bucket test passing UNMODIFIED. `submit()`'s statement ORDER is untouched:
  `reserve()` still above the queue-depth check and `settle()` still on the success path only,
  the D-35 contract that had no test and now has four. ZERO NUMBERS INVENTED: OQ-1 enforces
  SEGAL:173's sourced requests_per_hour 500 and writes NO daily leaf because no document gives
  one; OQ-2's DOS detector latches on a strict `>` against the INJECTED
  `retries_before_failure` so it owns no threshold at all; the five Table-19 minima are
  IMPORTED from `language_config.GATEKEEPER_MINIMA` (now public at its second consumer) rather
  than re-declared, so a floor cannot drift between the two instances; and `reporting.json`
  carries a `_sources` object citing every numeric leaf to a file and line, with a test
  asserting every numeric leaf HAS a citation. THIRTEEN REVERT PROBES, each with real counts,
  e.g. `reserve()` moved below the queue check -> 1 failed/50 passed (the only test in the repo
  that can see that move); quota counted in memory instead of durably -> 7 failed/25 passed;
  chain propagating a failed send instead of queueing -> 4 failed/28 passed. TWO HOLES THE
  SELF-AUDIT FOUND IN ITS OWN WORK: probe 9 first returned 0 failed/32 passed because
  `test_a_latched_lock_never_clears` only checked `locked` while the deleted line was a
  short-circuit, not the latch -- the latch survived but the EVIDENCE of the run was silently
  zeroed; and an AST scan over every `parametrize` in tests/ caught
  `test_gatekeeper_llm_unchanged.py` iterating two tables with nothing asserting they still had
  rows, which would have SKIPPED silently and left this plan's most important control reading
  green while asserting nothing. Both fixed and re-probed. ARTIFACT DIRECTORY decided
  deliberately: `game_artifacts/`, verified not gitignored -- NOT `logs/`, which .gitignore
  ignores wholesale immediately beneath its own comment claiming the four required artifacts
  are kept out of the list, while `write_declaration` writes into `logs/<role>/`, so the one
  artifact this project already produces is unreachable to git today (D7-1, for 07-02).
  GATES: ruff 0, line-limit exit 0 including all 16 new paths checked EXPLICITLY (the no-arg
  form enumerates via `git ls-files` and passes vacuously on an untracked file), 1689 passed
  from a 1557 baseline, coverage 96.80% from 96.65%, check_no_llm_in_strategy OK, dev_launch
  exit 0 with both sides `audit_verdict matched=true` over 5 turns and zero technical_win.
  GAMES-PLAYED, rule 38: full suite 1911/1904 -> 1911/1904 DELTA 0/0; one real game
  1911/1904 -> 1912/1905 DELTA 1/1. 07-00's guarantee holds under these changes. Commits
  c43ca63 / c6c5a98 / dfcb62a / d528517 / 8f89125. DEVIATION: the executing agent was killed by
  ECONNRESET after Task 4's verification block and before the self-audit, with three commits
  landed and the reporting package written but uncommitted; on resume the tree was READ BACK
  and verified rather than redone blind, and the production-caller grep, vacuity scan,
  collected-test counts, LLM parameter pin, full suite with counters and dev_launch were all
  re-run from scratch. Nothing was half-written.
Resume file: None -- 07-01 is fully committed and closed, tree clean. **Next is the rest of
  wave 1: 07-02 (artifact spine) and 07-03 (LocalView firewall)**, both `autonomous: true`,
  both independent of 07-01 and of each other -- a genuine three-way fan-out that needs
  WORKTREES to run in parallel, since the shared git index otherwise mixes commits and the
  whole-tree pre-commit hook blocks everyone. 07-04 and 07-07 are the plans that WIRE this
  one: `ReportingChain` and `load_reporting_config` deliberately have no production caller
  yet (D7-3), which is by design -- 07-01's non_goals exclude the wiring. Three deferred
  items are filed in the phase's `deferred-items.md`: **D7-1** .gitignore ignores `logs/`
  wholesale while rule 50 requires the four JSON artifacts committed, and
  `agent_step0_wiring.write_declaration` writes `declaration_<game_id>.json` into
  `logs/<role>/` -- 07-02 must move the writer's output OR narrow the ignore rule, not both
  and not neither; **D7-2** the durable-write retry/backoff constants now exist in three
  places, extracted to `shared/durable_write.py` but not folded into `step0_collect.py`
  (deliberately -- it is the rule-38 write path 07-00 just certified); **D7-3** above.
  OQ-1/OQ-2/OQ-3 are CLOSED in code with their citations; OQ-4 (result_ per-series vs
  per-game) is resolved in the outline but not yet implemented, and OQ-5 -- the games-played
  VALUE -- remains the human's at 07-10, before any live send. Nothing in this repo
  transmits: every shipped config carries `reporting.mode = dry_run`.
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
