---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: PHASE 7 PLAN 02 EXECUTED (2026-08-17) -- THE ARTIFACT SPINE IS BUILT AND D7-1 IS
  RESOLVED BY MOVING THE ARTIFACT, NOT BY NARROWING THE IGNORE RULE. docs/PARAMETERS.md:165-168
  fixes four filenames a grader will diff character by character, and one of them sits a single
  field away from aborting every game at the handshake. THE NAMES ARE PINNED TO THE DOCUMENT,
  not to another copy of themselves -- `tests/unit/test_artifact_names.py` transcribes the table
  as literals, asserts it still has four rows, and carries BOTH negative halves (adding `_g01`
  to `declaration_`/`result_` and dropping it from `config_`/`log_` must each fail the same
  assertion, or the check is shape-only). `<NN>` is a per-game_id 01-based sub-game index
  derived from the artifact directory and nothing else (D-72); `games_played.json` is neither
  read nor written by the spine or anything it calls, and the width 2 and base 1 are cited to
  `<NN>` and "the match number" as structural, never invented. D7-1, THE DECISION AND ITS
  REASONING: narrowing the `logs/` rule was rejected because git CANNOT re-include a file whose
  parent directory is excluded, so a negation beneath `logs/` is a silent no-op and real
  narrowing means a `logs/**`-plus-negations restructure the next editor can break with no
  signal -- returning the repo to exactly this bug, unnoticed -- and because `logs/`
  deliberately holds the bulky per-run wire logs and nonce ledgers that must stay out of git.
  AND THE PRECURSOR COULD NEVER HAVE BEEN THE ARTIFACT: `write_declaration` runs at handshake
  time, before move 1, while PARAMETERS:165 requires `declaration_<game_id>.json` to carry the
  END TIME plus repo URLs, MCP addresses and the agreed token ceiling. So the deliverable is
  07-02's D-71 wrapper in `game_artifacts/`, a strict superset of the precursor. Made real in
  the tree, not just in prose: `artifacts.write_artifact` REFUSES any path with a `logs`
  component (ValueError naming D7-1, inherited by both artifact writers); the .gitignore
  COMMENT that asserted the opposite of the tree was corrected with ZERO patterns changed
  (verified by a comments-stripped diff reporting IDENTICAL); `game_artifacts/README.md` records
  it where a grader will look. PHASE-5 RETAINED EVIDENCE VERIFIED, NOT ASSUMED -- all 42
  remote-round files still tracked, all 19 `declaration_*.json` among them still un-ignored,
  `git status --untracked-files=all logs/` EMPTY, and after the real game
  `logs/police/declaration_4b6f019a96265cd6.json` is IGNORED as designed, being the precursor.
  CONFIG ARTIFACT MEASURED ON BOTH ROLES: embedded game_params recomputes to
  23f86a93589131ae... and scent to c0e63220b31f5b82..., each EQUAL to the digest
  `agent_entrypoint.py:80` puts on the handshake wire; both roles produce a byte-identical
  1526-byte file, proved by writing both and diffing bytes rather than trusting the builder.
  network.json is excluded (D-04 -- `config_hash.py:13-16` says hashing it would abort every
  game), as are role.json, reporting.json's SECOND Table-19 instance and every policy file,
  each exclusion reasoned in the module docstring; `handshake_digests` carries only the two
  digests actually exchanged, and language.json deliberately gets none because claiming one
  would assert an agreement never made. THE D-71 CONTROL HELD: `git diff HEAD` over
  `src/pursuit/security/` and `src/pursuit/network/` is EMPTY, every Phase-6 Step-0 test passes
  UNMODIFIED, and dev_launch logs zero STEP0_MISMATCH -- the declaration was completed without
  the signed payload being touched. EIGHTEEN REVERT PROBES with real counts, e.g. a field
  injected INSIDE the signature (the exact D-71 mistake) -> 7 failed/30 passed; the D7-1 logs
  guard removed -> 5 failed/41; an empty peer declaration fabricated instead of an honest null
  -> 6 failed/31; network.json embedded in config_ -> 5 failed/13. THREE HOLES THE SELF-AUDIT
  FOUND IN ITS OWN WORK: the regex-escaping probe first returned 0 failed because the test ran
  the hazard backwards (it must plant `config_axc_g07.json` and search for `a.c`, which
  unescaped returns 8 instead of 1) -- now fails 1; `artifact_digest_matches` had TEST-ONLY
  reachability, dead code by the exact standard 07-01 filed D7-3 for, fixed rather than excused
  by having `write_config_artifact` read the file back and re-check its own seal, raising rather
  than returning a path it could not verify; and the game_uid join test was near-tautological,
  replaced by a name-against-header cross-check that took its probe from 0 failed to 4. An AST
  scan over all 16 parametrize sites in this plan's six test files found EVERY named source
  GUARDED by a length assertion; collected counts 30/16/17/5/16/21 = 105, equal to the suite
  delta exactly. FOUR SPLITS AT THE GATE, never compressions -- `artifacts.py` measured 167/150
  and `artifact_declaration.py` 156/150, and three test files exceeded too; two test-fixture
  modules were extracted at the second consumer rather than duplicated. GATES: ruff 0,
  line-limit exit 0 including all 14 new paths checked EXPLICITLY (the no-arg form enumerates
  via `git ls-files` and passes vacuously on an untracked file), 1794 passed from a 1689
  baseline, coverage 96.90% from 96.80%, all six new modules at 100%, check_no_llm_in_strategy
  OK, dev_launch exit 0 with both sides `audit_verdict matched=true`, capture at turn 5, zero
  technical_win. SECRETS, rules 39-40: both artifacts searched against the REAL values loaded
  from .env (the first attempt searched an empty set because no key was exported), zero leaks,
  and the control finds a planted token -- no artifact sample is committed. GAMES-PLAYED, rule
  38: full suite 1912/1905 -> 1912/1905 DELTA 0/0; one real game 1912/1905 -> 1913/1906 DELTA
  1/1. The VALUE remains deliberately unset and is the human's at 07-10. Commits 9ac7fdb /
  4f90fd7 / 042c0ac / 7bd0d01 / e2bb0ee.
Resume file: None -- 07-02 is fully committed and closed, tree clean. **Next is 07-03 (LocalView
  firewall)**, the last wave-1 plan, `autonomous: true` and independent of both 07-01 and 07-02;
  after it, wave 2 is 07-04 (mail transport, depends_on 07-01 + 07-02), 07-05 (log_ builder) and
  07-06 (live GUI). Running any two in parallel needs WORKTREES -- the shared git index mixes
  commits and the whole-tree pre-commit hook blocks everyone. WHAT 07-02 LEAVES FOR ITS
  CONSUMERS: `log_filename`, `next_sub_game_index` and `result_filename` are the three public
  names with no in-package caller (07-05 and 07-07 own them), and the whole spine has no
  PRODUCTION caller yet -- structurally, not by omission, because `write_declaration_artifact`
  needs the END TIME that only exists at game end (07-07) and `write_config_artifact` needs the
  artifact directory from `load_reporting_config`, which no production path loads yet. Five
  deferred items are filed in the phase's `deferred-items.md`: **D7-1 RESOLVED** with its
  reasoning recorded; **D7-2** the durable-write retry/backoff constants still in three places,
  deliberately not folded into `step0_collect.py` (the rule-38 write path 07-00 just certified);
  **D7-3** extended to the artifact spine, owned by 07-04/07-05/07-07; **D7-4** the declaration
  envelope key is an inline literal on the signed path with no `SignKey` member, deliberately
  not folded in because the D-71 control IS the empty git diff over that file; **D7-5** a
  pre-existing recoverable illegal handshake-to-handshake transition on every dev_launch run,
  present in runs predating this plan, logged not fixed per the scope boundary. OQ-1/OQ-2/OQ-3
  are CLOSED in code with citations; OQ-4 (result_ per-series vs per-game) is resolved in the
  outline but not yet implemented; OQ-5 -- the games-played VALUE -- remains the human's at
  07-10, before any live send. Nothing in this repo transmits: every shipped config carries
  reporting.mode dry_run.
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
