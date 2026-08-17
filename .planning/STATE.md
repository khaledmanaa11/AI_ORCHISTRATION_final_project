---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 07-06 is fully committed and closed, tree clean. WAVE 2 IS DONE: 07-06 was
  the last wave-2 plan. NEXT IS 07-07 (end-of-game reporting + result_), which has had everything
  it needs since 07-05 and owns D7-13/D7-14 and the D7-3/D7-12 wiring; then 07-08 (replay viewer),
  07-09 (gate evidence) and 07-10 (the one autonomous:false plan -- OAuth consent, one live send,
  screenshots, and the games-played VALUE decision, OQ-5). WHAT 07-06 LEAVES FOR THE PLANS THAT OWN
  IT, AND IT IS FOUR THINGS: (1) 07-10 MUST STATE A --refresh-ms VALUE for the screenshot and record
  it -- OQ-6 is resolved STRUCTURALLY, the repository holds no interval number anywhere in src/ and
  --refresh-ms is required=True with no default, so a launcher that omits it exits 2; (2) 07-08's
  replay viewer inherits the QUANTISATION rule as well as D7-8 -- a heat ramp whose background
  swallows small probabilities draws a support SMALLER than display.min_support_cells guards, and a
  five-cell drawn plus names its centre off numbers that were themselves compliant, so
  view_render.shade reserves the background for exactly zero and the drawn support is asserted
  EQUAL to the published one; (3) NOTHING may move from sdk/view_render.py or sdk/view_text.py into
  gui/ -- pyproject.toml:38 omits */gui/* from coverage, the 100% figures exist because the logic is
  outside it, and tests/unit/test_gui_structural.py FAILS the moment a gui/ module performs
  arithmetic, builds a string, or imports outside pursuit.sdk/pursuit.gui; (4) 07-09 records the
  scripted-launch evidence -- --once exits 0 on this machine (Tk 8.6) against a synthetic snapshot
  AND against both seats of a real game. Sixteen deferred items now sit in the phase's
  deferred-items.md: D7-1 RESOLVED, D7-2, D7-3, D7-4, D7-5, D7-6 RESOLVED, D7-7 RESOLVED, D7-8,
  D7-9 RESOLVED, D7-10 RESOLVED, D7-11, D7-12, D7-13 (RESOLVED for log_), D7-14, plus D7-15 and
  D7-16 from this plan. Still open and NOT fixed per the scope boundary:
  check_no_llm_in_strategy.sh has been absent from quality-gate.yml since 03-10, and D7-5's
  recoverable handshake -> handshake transition still fires once per run. OQ-1/OQ-2/OQ-3 are CLOSED
  in code with citations; OQ-4 is 07-07's remainder; OQ-6 is CLOSED structurally by this plan.
  OQ-5 -- the games-played VALUE -- remains the human's at 07-10, before any live send. NOTHING IN
  THIS REPO TRANSMITS: both shipped reporting.json files still read mode dry_run, no test anywhere
  can reach the network, and the live GUI's only output is a JSON file inside the agent's own
  gitignored logs/<role>/ directory.
stopped_at: PHASE 7 PLAN 06 EXECUTED (2026-08-17) -- THE LIVE GUI IS A SEPARATE PROCESS (D-76) FED
  BY A PUBLISHED LocalView SNAPSHOT, AND IT FOUND A LEAK CHANNEL 07-11 STRUCTURALLY COULD NOT:
  QUANTISATION. display.min_support_cells = 6 keeps the geometric inversion empty by guarding the
  PUBLISHED support; a heat ramp that rounded small probabilities down to the background would paint
  a SMALLER support than the grid carries, and a five-cell drawn plus names its centre exactly as
  loudly as a printed coordinate. So shade reserves BACKGROUND_COLOUR for exactly zero and the
  load-bearing assertion is an EQUALITY between the drawn support and the published one, asserted
  BEFORE any inversion. IT IS NOT HYPOTHETICAL: measured on the production view, scent.own spans
  0.08-1.8 (ratio 22.50) and scent.opponent 0.058-0.154 (2.66) against the belief's 1.57 -- the
  near-uniform belief would have HIDDEN the defect behind the very panel it endangers, so both
  halves are asserted; probe 1 gives 4 failed. D-76 DECIDED FROM THREE MEASUREMENTS, not preference:
  tk.mainloop() blocks its calling thread and Watchdog os._exits at the configured 60 s threshold,
  killing the agent mid-game; Tk is not thread-safe, and a polling thread could sample the pure
  1.0/0.0 delta window inside decide(); and a separate process CANNOT HOLD the true joint position
  at all, turning D-74's type-level firewall into a PROCESS-level one. The agent's whole
  contribution is one contained call at the single point a joint turn resolves -- publish_view never
  raises, never returns a verdict and never touches ctx.state, because since 06-05 a non-zero exit
  code MEANS an audit mismatch and a failed cosmetic write must not forge a technical loss.
  dev_launch (2db6cc8b039c82e7) exit 0, both seats matched=true, outcome capture, ZERO
  technical_win and ZERO watchdog_incident. THE RUNTIME RECOVERY TEST RUNS THE WHOLE CHAIN -- real
  decide(known_cell=ctx.state.thief) -> publish -> THE FILE ON DISK -> read_snapshot -> the exact
  view_render/view_text calls gui/ makes -- and BOTH counter-controls fire: a leaky panel inverts to
  [(5,3)] and its scent brightest set is [(5,3)]; the peak-cell-line-deleted sidebar earns a CLEAN
  coordinate verdict while the heatmap still inverts, which is the argmax-only trap re-run at the
  render layer. VERIFIED ON THE LIVE GAME, not only on fixtures: thief true cell (2,3), police
  published argmax (1,1), entropy 5.5587, drawn support 49/49 == published, inversion [], scent peak
  (2,2), and NO forward pair [2,3] and NO flat index 17/23 anywhere in the file -- the single scan
  hit was own_cell pair [3,2], the REVERSED encoding colliding with our own rule-8-legal cell,
  confirmed a false positive rather than assumed and filed as D7-16. ONE OF MY OWN ASSERTIONS WAS
  WRONG-SHAPED AND FAILED FIRST: "the brightest stop must not CONTAIN the true cell" is false on a
  near-uniform map, where ceil(v/peak*6) puts 20-odd of 49 cells in the last bucket; what is a leak
  is the top stop NAMING a cell, so it is now a geometric inversion over the brightest set with a
  non-empty guard. D7-6 CLOSED BY CODE AND THE GATE HARDENED IN THE SAME COMMIT, with all three of
  D7-9's blind spots MEASURED OPEN FIRST: a bare __init__.py printed "OK: 1 module(s) scanned" exit
  0 -> now exit 2; a panel.pyw reading ctx.state.thief was NEVER SCANNED -> now reported; and an
  aliased s = ctx.state then s.thief, plus getattr(ctx.state,"thief") and asdict(s)["cop"], returned
  violations=[] exit 0 -> now 3 violations. The dynamic-key check is on the KEY rather than on what
  it is applied to, which makes it total over indirections nobody has thought of yet. The gate hit
  198 code lines and was SPLIT into scripts/local_truth_ast.py, loaded by file path so 07-03's
  standalone property survives; both halves checked explicitly at 140 and 102. What is STILL open is
  written into the gate's own docstring rather than papered over -- a parameter named state is
  beyond a single-module AST walk, and the gate still cannot see a coordinate that is DRAWN, so it
  is nowhere cited as evidence about these panels. gui/ IS 200 CODE LINES OF PURE CONSTRUCTION
  across five files, 34.5% of the 579 new src/ lines, and the coverage omission is made safe rather
  than tolerated: zero arithmetic BinOps (annotation BitOr excluded), zero f-strings/.join/.format,
  every pursuit import under pursuit.sdk or pursuit.gui, each scan paired with a control proving it
  can fail -- and the plan's grep is clean AS PROSE too, the four forbidden spellings absent from
  docstrings as well. All four new sdk modules at 100%. OQ-6 RESOLVED WITH ZERO NUMBERS IN src/:
  --refresh-ms is required=True with no default and LiveDashboard takes it keyword-only with no
  default (the Watchdog/TokenBucket precedent); --help exits 0 showing it required, and omitting it
  exits 2. EIGHTEEN REVERT PROBES, every count real, anchor asserted present and mutation asserted
  landed before each run: quantisation 4; lit_cells inert 6; publisher re-raises 2; published before
  both slots 1; view_history shared 1; strategy map republished 14; fabricated uniform panel 1; idle
  0.00 instead of unknown 1; half-written file raises 2; package-marker guard neutered 2; .pyw
  dropped 1; state_aliases emptied 1; accessor_key None 1; direct .state chain dropped 5; belief
  panel blanked 1; shared scent scale 3; outgoing hint never recorded 2; raw scent republished 4.
  FOUR HOLES THE SELF-AUDIT FOUND IN MY OWN WORK: (i) lit_cells() had TEST-ONLY reachability -- the
  D7-3 finding in my own code, found by grepping production callers for all 33 new public names, and
  WIRED rather than excused (view_text._support now counts what the panel actually lights, so the
  caption and the picture are one fact); (ii) one unguarded assert-bearing loop over fx.BARRIERS,
  rewritten as a set comparison which FAILS on an empty source instead of passing; (iii) both
  parametrize tables were inline literals -- named and floored, because a thinned table skips
  silently; (iv) coverage exposed the one uncovered branch, a scent-free view that
  view_builder._scent_view genuinely produces. D7-7 also CLOSED: HintHistory.record_outgoing had no
  caller AT ALL and is now called from turn_language_io after the hint goes out, so the sidebar
  shows a whole conversation. Zero numbers invented: every constant is presentation (CELL_PIXELS,
  PANEL_PAD, DECIMALS...), the bucket count is len(HEAT_RAMP) everywhere, and the one number a live
  GUI genuinely needs is deliberately not in the repository.
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
