---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 07-05 is fully committed and closed, tree clean. WAVE 2 CONTINUES: 07-06
  (live GUI) is the remaining wave-2 plan, and 07-07 (end-of-game) now has EVERYTHING it needs
  from waves 1-2 -- 07-05 was its last missing input. Running two in parallel needs WORKTREES:
  the shared git index mixes commits and the whole-tree pre-commit hook blocks everyone. WHAT
  07-05 LEAVES FOR THE PLANS THAT OWN IT, AND IT IS FOUR THINGS: (1) 07-07 MUST PASS THE
  NEGOTIATED game_uid (ctx.game_uid), not the process-local one -- D7-13, found on a real thief
  log that carries TWO game_uids because adopt_negotiated_game_id renames the log mid-stream;
  prior_game_uids will be [] on one seat and one entry on the other, and that is correct; (2)
  07-07 must call write_log_artifact from the GAME-END path only -- D-64 and SEC-04, and
  tests/unit/test_log_artifact_reachability.py FAILS the moment anything under network/turn_* or
  orchestrator.py reaches it, in EITHER import form (the module path or the package's re-exported
  name; the name form is the one 07-07 is most likely to write); (3) 07-08 must check
  committed > 0 before displaying any ratio -- verify_log_turns returns (0, 0) on an empty
  artifact and 0 == 0 is True; it needs NEITHER source file, proven by deleting both; and there
  is no belief_argmax in the artifact at all, so D7-8's constraint is satisfied by ABSENCE rather
  than by discipline at render time; (4) log_join.py sits at 147/150 -- the next plan to open it
  SPLITS, never compresses. Fourteen deferred items now sit in the phase's deferred-items.md:
  D7-1 RESOLVED, D7-2, D7-3, D7-4, D7-5, D7-6, D7-7, D7-8, D7-9, D7-10 RESOLVED, D7-11, D7-12,
  plus D7-13 (RESOLVED for log_) and D7-14 from this plan. Still open and NOT fixed per the scope
  boundary: the local-truth CI job is RED until 07-06 creates src/pursuit/gui/ (D7-6, by
  construction -- 07-06 turns it green by writing modules that pass, and must not soften the
  gate), check_no_llm_in_strategy.sh has been absent from quality-gate.yml since 03-10, and
  D7-5's recoverable handshake -> handshake transition still fires once per run (it is the very
  record carrying the pre-negotiation uid in D7-13). OQ-1/OQ-2/OQ-3 are CLOSED in code with
  citations. OQ-4 is resolved in the outline and half-implemented; 07-07 owns the rest. OQ-5 --
  the games-played VALUE -- remains the human's at 07-10, before any live send. NOTHING IN THIS
  REPO TRANSMITS: both shipped reporting.json files still read mode dry_run, and no test anywhere
  can reach the network.
stopped_at: PHASE 7 PLAN 05 EXECUTED (2026-08-17) -- log_<game_id>_g<NN>.json IS BUILT, AND ON A
  REAL dev_launch GAME IT RE-HASHES 5/5 COMMITTED TURNS TO 100% ON BOTH SEATS WITH THE .jsonl AND
  THE .ledger.jsonl DELETED FROM DISK. Rule 20 makes a VERIFYING replay viewer a threshold
  condition for approving the project, so self-containment was proven by REMOVING the sources,
  not by asserting it. THE JOIN KEYS ON LOCAL TURN TRUTH, reusing 06-05's discipline rather than
  re-deriving it, and the peer's envelope turn is carried into peer_claimed_turns as EVIDENCE and
  is never a key. THE COUNTER-CONTROL IS THE POINT AND IT HAS REAL COUNTS: the adversarial fixture
  has the peer stamp COMMIT turn 99 and REVEAL turn 7 on one local turn 3 -- keyed on local truth
  the artifact has 5 turn entries and 4 peer COMMIT+REVEAL pairs, keyed on envelope.turn it has 7
  entries and 3 pairs, keys [0,1,2,3,4,7,99] -- it LOSES A PAIR AND INVENTS TWO TURNS THE PEER
  NAMED OUT OF THIN AIR, while the HONEST fixture is identical under both keys, which is exactly
  why a happy path alone proves nothing. AND IT IS NOT ONLY AN ADVERSARY: scanning all 20 recorded
  games in logs/, EVERY ONE carries 5-6 message_received records whose local turn differs from the
  peer's stamp -- every incoming HINT, because a hint arrives one turn late -- so a builder keyed
  on the peer's number would misfile every hint of every honest game. RULES 8-9: ZERO INTERNAL
  STATE, BY ALLOW-LIST. D7-8 records that the cop's true argmax is STILL written into every
  language_turn JSONL record, correctly, because that log is the rule-38 audit record -- but this
  artifact is emailed off the machine, so outgoing_hint copies exactly ("intent","text") and never
  the whole record minus a deny-list, because an allow-list stays correct when a future plan adds
  a field. All six LANGUAGE_INTERNAL_FIELDS scanned absent from BOTH real artifacts, with a
  counter-control proving the scan finds a planted belief_argmax. A TRUNCATED TAIL IS TOLERATED
  AND MID-FILE CORRUPTION IS NOT, without weakening read_all or _read_log: log_read.py is a
  SECOND reader, because an audit that cannot read its own evidence must stop while a replay
  artifact that cannot be produced from a crashed game is useless exactly when it is needed;
  CorruptLogError is a distinct CLASS, asserted with an exact type check, because
  json.JSONDecodeError is itself a ValueError and a looser assertion would have passed on the
  tail case too. TWENTY-ONE REVERT PROBES, every count real, anchor asserted present and mutation
  asserted landed before each run: re-key on envelope.turn 3 failed; peer_claimed_turn neutered
  3; partial tail raises 3; mid-file corruption dropped 4; _is_turn bool guard removed 1;
  language record copied wholesale 11; verify_log_turns counts uncommitted turns 8; re-hash
  always True 2; truncated_tail out of the seal 1; seal from a fresh build not the FILE 1;
  game_uid check removed 2; post-write re-hash check removed 1; outgoing hint never populated 3;
  audit verdict never carried 2; prior_game_uids dropped 1; turn-loop imports the builder by
  module path 2, by re-exported NAME 2, from the orchestrator 2; the join reaches for
  CommitLedger 1; a new src/ module imports security.ledger 1; the reachability scanner blinded
  2. THREE HOLES THE SELF-AUDIT FOUND IN MY OWN WORK, and the third is the one worth remembering:
  (i) the _is_turn bool guard had NO test and probe 5 returned 18 passed / 0 failed -- it is not
  cosmetic, because True == 1 and hash(True) == hash(1), so a ledger line stamped "turn": true
  lands on TURN 1's dict key and silently replaces its nonce and hash; (ii) the post-write
  re-hash check had no test and probe 12 returned 16 passed / 0 failed, fixed by giving it a real
  cause -- a ledger whose h_commit disagrees with its own payload; (iii) THE REACHABILITY GATE
  WAS GREEN BECAUSE IT WAS BLIND -- it watched module PATHS only, so a probe adding an import of
  artifact_log FROM THE PACKAGE into network/turn_actions.py, a turn-loop module importing the
  builder, PASSED 6/6. The package re-exports, so the name form is precisely the one 07-07 will
  write. Same class as 07-11's vacuous fixtures. Coverage then found four more untested defensive
  branches; all four new modules now sit at 100%. D-61 FOUND ON A REAL GAME BY A CHECK WRITTEN TO
  CATCH THE OPPOSITE MISTAKE: logs/thief/521519a78f96c255.jsonl holds 42 records and TWO game_uids
  -- the one pre-negotiation illegal_transition carries 3c0c5fd8f6705a3b, the other 41 and the
  filename carry the negotiated 521519a78f96c255 -- because agent_lifecycle opens the log before
  the handshake and adopt_negotiated_game_id renames it after. A builder reading "the log's
  game_uid" off the first record would have REFUSED THE THIEF AN ARTIFACT IN EVERY GAME. Fixed by
  requiring the negotiated id to appear somewhere and carrying every other id in prior_game_uids
  INSIDE THE SEAL, because dropping it would hide the very fact 05-UAT G2 exists to make visible;
  the strict half is kept and tested. Zero numbers invented: turn indices come from the records,
  the filename and the sub-game index from 07-02's namer.
---

Last session: 2026-08-17T16:10:00+03:00
Stopped at: Completed 07-05-PLAN.md (the log_ artifact -- wire JSONL x nonce ledger, joined on
  local turn truth) in full. Three tasks, each committed atomically: Task 1 the join, the
  crash-tolerant reader and the adversarial disjoint-turn fixture (`3f503b2`), Task 2 the
  artifact, its seal and the deleted-sources integration proof (`e6ea7f0`), Task 3 the nonce
  boundary pinned as a SCAN rather than recorded as a grep, plus `docs/PRD_log_artifact.md`
  (`1d0a47d`). Three further commits closed findings in my own work: the four defensive branches
  coverage exposed and the last unguarded assert-bearing loop (`fdb95eb`), the D-61 two-game_uid
  fix (`4787e11`), and trimming log_join.py off the exact 150/150 limit (`34169fd`). Gates:
  `ruff check .` 0 violations; 1974 passed / 0 failed against the 1919 baseline; coverage 97.12%
  (baseline 97.02%); `check_line_limit.sh` exit 0 with all twelve new files ALSO checked
  explicitly by path (the no-arg form enumerates via git ls-files and passes VACUOUSLY on an
  untracked file); `check_no_llm_in_strategy.py` OK; every new `.py` confirmed NOT ignored by git
  (D7-10's guard); `scripts/dev_launch.py` exit 0, game `521519a78f96c255`, both seats
  `"matched":true`, outcome capture at turn 5. Rule-38 counters, all four: the full suite moved
  police 1916->1916 and thief 1909->1909 (delta 0/0); one real game moved 1916->1917 and
  1909->1910 (delta 1/1). All five new modules at 100% coverage: log_join.py, log_read.py,
  log_turn_fields.py, log_artifact_fields.py, artifact_log.py. AST parametrize scan over all
  seven of this plan's test/fixture files: 3 sites, two named sources both length-guarded and one
  inline 5-element literal with a positive control; 2 assert-bearing loops, one already guarded
  and one -- over LOG_ARTIFACT_MODULES -- found UNGUARDED and now floored at 4. Graphify refreshed
  -- 9449 nodes / 16882 edges; `graphify explain write_log_artifact` resolves to
  `artifact_log.py:129` (degree 14) and `join_game` to `log_join.py:119` (degree 25); graph.html
  skipped by the tool at 9449 nodes against its 5000 viz limit, and it is a gitignored local-only
  artifact anyway. `07-05-SUMMARY.md` written with every number from a run in this session,
  self-check PASSED (19 paths and 5 task commits verified, and every new source/test file
  additionally verified TRACKED by git). `docs/phases/phase-7/TODO.md` gains a ticked 07-05 row
  with its measured evidence; D7-13 and D7-14 filed in the phase's `deferred-items.md`.
Resume file: None -- the tree is clean and 07-05 is closed. Wave 2 of phase 7 continues
  (`/gsd:execute-phase 7`): 07-06 (live GUI) is the last wave-2 plan. 07-07 is now fully
  unblocked and owns D7-13/D7-14; 07-08 consumes `verify_log_turns` and must floor it on
  `committed > 0`.
---

Last session: 2026-08-17T11:40:00+03:00
Stopped at: Completed 07-04-PLAN.md (the mail transport -- attached JSON, send-only scope, 429
  handled by the ONE gatekeeper) in full. Three tasks, each committed atomically: Task 1 the
  MIME shape asserted by re-parsing the rendered bytes (`86d9547` -- 17 tests, with the body
  and header leak checks each paired with a control that plants the distinctive value and
  requires the check to FAIL), Task 2 the MailSink protocol and DryRunSink plus the
  durable_write_bytes / write_artifact_bytes extractions (`c196535` -- 9 tests that claim only
  what a disk write can claim), Task 3 GmailSink against an injected fake transport
  (`6b686cd` -- 47 tests across three files, none satisfiable by DryRunSink). Gates:
  `ruff check .` 0 violations; 1919 passed / 0 failed against the 1846 baseline; coverage
  97.02% (baseline 96.95%); `check_line_limit.sh` exit 0 with all twelve new/touched files
  ALSO checked explicitly by path; `check_no_llm_in_strategy.py` OK; `uv lock --check` current
  and no requirements.txt exists; `git diff config/` EMPTY; `scripts/dev_launch.py` exit 0
  with outcome capture and 11 `"matched":true` audit verdicts per side, zero STEP0_MISMATCH,
  zero technical_win. Rule-38 counters, all four: the full suite moved police 1915->1915 and
  thief 1908->1908 (delta 0/0); one real game moved 1915->1916 and 1908->1909 (delta 1/1).
  Every new or touched module at 100% coverage: message.py, sink.py, gmail_sink.py,
  artifacts.py, durable_write.py. Collected test counts re-read from pytest rather than
  counted by hand -- 17 / 9 / 12 / 15 / 20 = 73, exactly the suite delta. Every parametrize
  site in this plan's five test files is length-guarded (4 sites, 4 guards), because an
  emptied table SKIPS silently. Graphify refreshed -- 9250 nodes / 16532 edges,
  `graphify explain GmailSink` resolves to `gmail_sink.py:153`. `07-04-SUMMARY.md` written
  with every number from a run in this session, self-check PASSED (18 paths and 3 commits
  verified, and the nine new source/test files additionally verified TRACKED by git -- the
  check that would have caught D7-10 on its own). `docs/phases/phase-7/TODO.md` gains a ticked
  07-04 row and moves 07-96 to in-progress; D7-10 (RESOLVED), D7-11 and D7-12 filed in the
  phase's `deferred-items.md`.
Resume file: None -- the tree is clean and 07-04 is closed. Wave 2 of phase 7 continues
  (`/gsd:execute-phase 7`): 07-05 (log_ builder) and 07-06 (live GUI). 07-07 consumes this
  plan's ReportingChain + sink wiring and owns D7-12.
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
