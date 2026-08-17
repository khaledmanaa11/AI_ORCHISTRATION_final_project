---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 07-07 is fully committed and closed, tree clean. NEXT IS 07-08 (the replay
  viewer), then 07-09 (GATE-7 evidence) and 07-10 (the one autonomous:false plan -- OAuth consent,
  one live send, screenshots, and the games-played VALUE decision, OQ-5). WHAT 07-07 LEAVES FOR THE
  PLANS THAT OWN IT, AND IT IS SIX THINGS: (1) THE FOUR ARTIFACTS ARE AT `<artifact_dir>/<role>/`,
  not at `<artifact_dir>/` -- a real dev_launch game proved that two seats sharing one repository
  share one configured directory, and the second seat's rewrite ATE the first seat's report, which
  is rule 35's zero-for-both-teams shape exactly; (2) `agreement.audit_verdict` in `result_` is
  BYTE-IDENTICAL to the `log_` artifact's, by construction, so 07-08's verdict screen may quote
  either without a second extraction; (3) THE COP'S `agreed` IS LEGITIMATELY `null` ON A CAPTURE IT
  WON -- rule 21 gives the Capture Claim to the cop, so only the THIEF ever receives one, and the
  artifact carries a stated reason; a viewer must not render that as a failure; (4)
  `games_played_declared` is an absent MARKER carrying its own reason, never a number -- 07-10 sets
  the VALUE from docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md before any live send; (5)
  `build_reporting_chain` REFUSES to build a live transport, so 07-10 constructs GmailSink itself
  and injects it; (6) a production series contains ONE sub-game today (D7-17) -- the two-sub-game
  arithmetic is proven, but `game_id` is minted per game while PARAMETERS reads it as the series id.
  Eighteen deferred items now sit in the phase's deferred-items.md: D7-1 RESOLVED, D7-2, D7-3,
  D7-4, D7-5, D7-6 RESOLVED, D7-7 RESOLVED, D7-8, D7-9 RESOLVED, D7-10 RESOLVED, D7-11, D7-12,
  D7-13 (RESOLVED for log_), D7-14 RESOLVED by this plan's production call site, D7-15, D7-16, plus
  D7-17 and D7-18 from this plan. Still open and NOT fixed per the scope boundary:
  check_no_llm_in_strategy.sh has been absent from quality-gate.yml since 03-10, and D7-5's
  recoverable handshake -> handshake transition still fires once per run. OQ-1/OQ-2/OQ-3 are CLOSED
  in code with citations; OQ-4 is CLOSED by this plan as a recorded INTERPRETATION with both
  citations (one result_ per SERIES, rewritten with .prev rotation and emailed after every
  sub-game); OQ-6 is CLOSED structurally by 07-06. OQ-5 -- the games-played VALUE -- remains the
  human's at 07-10, before any live send. NOTHING IN THIS REPO TRANSMITS: both shipped
  reporting.json files still read mode dry_run (git diff on both is empty), no test anywhere can
  reach the network, and the only thing the game-end hook produces is files on this machine's disk.
stopped_at: PHASE 7 PLAN 07 EXECUTED (2026-08-17) -- THE MANDATORY REPORT IS ONE DURABLE FILE PER
  SERIES WHOSE TOKEN TOTAL IS ACCUMULATED IN THE FILE, AND ONE MEASUREMENT IS THE WHOLE PLAN: the
  same mutation that drops the accumulation fails 2 tests over two sub-games and PASSES 9/9 when
  only single-sub-game tests run, because with one game played the per-game and per-series figures
  are equal. Rule 54 needs both, and the series one CANNOT come from budget.report() -- the outline
  said it could -- since Gatekeeper.__init__:81 builds a fresh TokenBudget, the gatekeeper is built
  once per PROCESS, and budget.py:44-52 says "a fresh instance per series only". Two sub-games of
  140 and 10 tokens give a series total of 150: strictly greater than either and EQUAL to their sum,
  asserted strictly rather than with >=. `agreed` IS THREE-VALUED and defaulting it is a false
  declaration under the one rule whose sanction is ZERO FOR BOTH TEAMS: capture_declaration sends
  GAME_OVER only when the outcome is a capture AND this side is the cop, so a survival game has no
  peer claim on either side and even a capture leaves the COP with none -- measured on the real game
  a5dd2a98827f4df5, police agreed=null with NO_PEER_CLAIM and thief agreed=true; the naive
  own==peer with peer defaulted to own fails 6 of 9. A malformed peer claim is a NAMED
  non-agreement, never a ValueError (security/audit.py's boundary rule, six Phase-5 defects deep).
  THE WATCHDOG CONTAINMENT WAS CHOSEN AND RECORDED WITH ITS ARITHMETIC: the mail ladder is
  30x4 + 30x3 = 210 s against a 60 s watchdog_threshold, so a touch per bounded attempt (entry and
  finally, wrapping the sink) rather than a total bound -- a bound short enough to fit would be an
  INVENTED number and would also give up before rule 32 wants. Driven on an injected clock with
  ZERO real sleeps: 4 attempts, armed.clock.now exactly 210.0, fired == [], and two paired controls
  -- the same ladder unwrapped IS killed (freeze then exit, in that order) and a genuinely frozen
  agent is still killed while one touch inside the window still saves it. A REPORTING FAILURE
  CANNOT REACH THE EXIT CODE, which since 06-05 MEANS an audit mismatch: contained at its own
  boundary with except Exception (never BaseException -- CancelledError must still propagate), and
  driven with REAL causes because the failing-SINK path never reaches that branch at all. AND THEN
  ONE REAL GAME FOUND A RULE-35 DISQUALIFIER NO UNIT TEST COULD HAVE POSED: at commit 4d68886,
  dev_launch produced log_<uid>_g01 AND log_<uid>_g02 for a SINGLE game plus one
  result_<uid>.json carrying role:police, BOTH seats' entries and games_measured:2 -- the thief
  reported first, the police read that file as "the previous generation of this series", appended
  its own entry and rewrote it, and THE THIEF'S REPORT WAS GONE. Fixed to <artifact_dir>/<role>/
  without editing reporting.json (its value is the artifact ROOT); the re-run gives two separate
  reports, one sub-game each, both logs _g01, each carrying its own role, and probe 15 fails 2.
  test_end_of_game_wiring.py exists because every other test drives report_game_end directly, so
  deleting the ONE line in agent_entrypoint.py would have left the suite green while no league game
  ever reported -- and its position assertion was WRONG-SHAPED on the first draft, comparing source
  offsets and passing against a mutation that moved the call to the top of the very finally it
  forbids; rewritten on the AST, probe 14 now fails 2. Three more of my own assertions measured
  nothing and were replaced: `tokens != 0` (a dict never equals an int -- and the SECOND draft,
  `0 not in tokens.values()`, failed too because present:False IS 0 under ==), an artifact-path
  check that could never exist once artifacts moved per-role, and a chain test that asserted only a
  filename's suffix and now SENDS and looks for the file. Eighteen revert probes, every count real,
  anchor asserted present and mutation asserted landed before each run. Games-played is emitted as
  an absent MARKER naming GAMES-PLAYED-RECONSTRUCTION.md and declaration_<game_id>.json; nothing
  here sets, defaults or reads around the value.
---

Last session: 2026-08-17T23:55:00+03:00
Stopped at: Completed 07-07-PLAN.md (end-of-game reporting + `result_`) in full. Three tasks, each
  committed atomically: Task 1 the rule-35 agreement record, three-valued and never inferred
  (`e61b46c`); Task 2 `result_<game_id>.json` as one durable file per series with both token totals
  (`8377916`); Task 3 the game-end hook, contained, watchdog-touching, and wired at ONE call site
  beside `record_completed_game` (`4d68886`). Two further commits closed findings in my own work:
  the per-role artifact directory that a real game proved was a rule-35 disqualifier (`5aa9ec1`),
  and three assertions of mine that measured nothing (`7081515`). Gates: `ruff check .` 0
  violations; 2090 passed / 0 failed against the 2047 baseline; coverage 97.29% (baseline 97.19%);
  `check_line_limit.sh` exit 0 with all nineteen new `.py` files ALSO checked explicitly by path;
  `check_no_llm_in_strategy.py` OK; `check_local_truth.py` -> `OK: 5 module(s) scanned`, exit 0;
  every new `.py` and both new PRDs confirmed NOT ignored by git (D7-10's guard);
  `git diff config/{police,thief}/reporting.json` EMPTY and both still `dry_run`;
  `scripts/dev_launch.py` exit 0, game `a5dd2a98827f4df5`, both seats `matched=true` at turn 5,
  ZERO `technical_win` and ZERO `watchdog_incident`, and both seats wrote their OWN `log_` and
  `result_` under `game_artifacts/<role>/`. Rule-38 counters, all four: the full suite moved police
  1920->1920 and thief 1913->1913 (delta 0/0); one real game moved 1919->1920 and 1912->1913
  (delta 1/1). All six new source modules at 100% coverage -- `result_agreement.py`,
  `result_agreement_fields.py`, `artifact_result.py`, `result_artifact_fields.py`,
  `end_of_game.py`, `end_of_game_chain.py` -- and so is every other module in
  `services/reporting/`. `agent_entrypoint.py` measured 103 -> 107 of its 150 permitted code lines.
  AST scan over all thirteen of this plan's test/fixture files: 0 parametrize sites, 4
  assert-bearing loops, every one floored. Production-caller grep over all 25 new public names:
  every one referenced in `src/` outside its defining module, and `report_game_end` reaches
  `network/agent_entrypoint.py` -- D7-14 closed, and `test_log_artifact_reachability.py` now NAMES
  the `log_` builder's five reachers so its empty-list assertion cannot be green because the
  builder is dead code. Two per-mechanism PRDs written per CLAUDE.md Sec2.3:
  `docs/PRD_result_artifact.md` and `docs/PRD_end_of_game.md`. Graphify refreshed -- 10027 nodes /
  17957 edges / 575 communities; `graphify explain report_game_end` resolves to
  `end_of_game.py:89` (degree 16, `--> _report()`) and `record_sub_game` to
  `artifact_result.py:147` (degree 9). `07-07-SUMMARY.md` written with every number from a run in
  this session, self-check PASSED (26 paths verified present AND tracked, 5 task commits verified
  reachable, and five file-size numbers CORRECTED rather than left as written).
  `docs/phases/phase-7/TODO.md` gains a ticked 07-07 row and a refreshed 07-96; D7-14 closed, and
  D7-17 (`game_id` is minted per GAME while PARAMETERS reads it as the SERIES id) and D7-18 (a
  QuotaManager path is unguarded against the shipped `config/` tree) filed in the phase's
  `deferred-items.md`.
Resume file: None -- the tree is clean and 07-07 is closed. Next is `/gsd:execute-phase 7`
  continuing into 07-08 (the replay viewer), which must floor `verify_log_turns` on
  `committed > 0`, inherits D7-8 and the 07-06 quantisation rule, and now also reads `result_`
  from `game_artifacts/<role>/`; then 07-09 and the human-in-the-loop 07-10.
---

Last session: 2026-08-17T22:40:00+03:00
Stopped at: Completed 07-06-PLAN.md (the live GUI -- a separate process over a published
  LocalView snapshot) in full. Three tasks, each committed atomically: Task 1 the best-effort
  publisher plus its read half, the one call site in `maybe_resolve`, and the leak scan run over
  the WRITTEN FILE with its five-variant counter-control (`56e4d96`); Task 2 the five thin `gui/`
  files over `sdk/view_render.py` + `sdk/view_text.py`, and the runtime recovery test that found
  the quantisation channel (`840636b`); Task 3 the local-truth gate turned green BY CODE with
  D7-9's three blind spots measured open then closed, split at 198 lines into
  `scripts/local_truth_ast.py` (`ad46940`). A fourth commit closed four findings in my own work
  (`dea2a60`): `lit_cells`'s test-only reachability wired into `view_text._support`, one unguarded
  assert-bearing loop rewritten as a set comparison, both inline parametrize tables named and
  floored, and the last uncovered branch (a scent-free view) covered. Gates: `ruff check .` 0
  violations; 2047 passed / 0 failed against the 1974 baseline; coverage 97.19% (baseline 97.12%);
  `check_line_limit.sh` exit 0 with all twenty-one new/touched files ALSO checked explicitly by
  path; `check_local_truth.py` -> `OK: 5 module(s) scanned`, exit 0, and the `.sh` wrapper the same;
  `check_no_llm_in_strategy.py` OK; every new `.py` confirmed NOT ignored by git (D7-10's guard);
  grep of `gui/` for the four forbidden spellings -> no hits, prose included;
  `python -m pursuit.gui.live_app --help` exit 0 with `--refresh-ms` shown as required and exit 2
  when it is omitted; `--once` scripted launch exit 0 against a synthetic snapshot AND against both
  seats of the real game; `scripts/dev_launch.py` exit 0, game `2db6cc8b039c82e7`, both seats
  matched=true, outcome capture, zero `technical_win`, zero `watchdog_incident`. Rule-38
  counters, all four: the full suite moved police 1918->1918 and thief 1911->1911 (delta 0/0); one
  real game moved 1917->1918 and 1910->1911 (delta 1/1). All four new sdk modules at 100% coverage:
  view_publish.py, view_snapshot.py, view_render.py, view_text.py; `gui/` is coverage-omitted and
  holds 200 of the 579 new `src/` code lines (34.5%), every one of them widget construction, which
  `test_gui_structural.py` enforces structurally. AST parametrize/loop scan over all six of this
  plan's test files: 2 parametrize sites, both now NAMED and floored; 4 assert-bearing loops, three
  already guarded and one found UNGUARDED and rewritten. Graphify refreshed -- 9734 nodes / 17412
  edges / 579 communities; `graphify explain publish_view` resolves to `view_publish.py:90`
  (degree 17, edge in from `maybe_resolve`) and `LiveDashboard` to `live_app.py:47`.
  `07-06-SUMMARY.md` written with every number from a run in this session, self-check PASSED (25
  paths and 4 task commits verified, every new source/test file additionally verified TRACKED by
  git, and the `gui/` line share recomputed independently at 200/579 = 34.5%).
  `docs/phases/phase-7/TODO.md` gains a ticked 07-06 row and a refreshed 07-96; D7-6, D7-7 and D7-9
  marked RESOLVED and D7-15/D7-16 filed in the phase's `deferred-items.md`.
Resume file: None -- the tree is clean and 07-06 is closed. Wave 2 of phase 7 is COMPLETE. Next is
  `/gsd:execute-phase 7` continuing into 07-07 (end-of-game reporting + `result_`), which owns
  D7-13/D7-14 and the D7-3/D7-12 wiring; then 07-08, 07-09 and the human-in-the-loop 07-10.
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
