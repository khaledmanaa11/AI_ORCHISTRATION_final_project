---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 07-04 is fully committed and closed, tree clean. WAVE 2 CONTINUES: 07-05
  (log_ builder) and 07-06 (live GUI) are next, and 07-07 (end-of-game) now has everything it
  needs from waves 1-2 except 07-05's log_ artifact. Running any two in parallel needs
  WORKTREES -- the shared git index mixes commits and the whole-tree pre-commit hook blocks
  everyone. WHAT 07-04 LEAVES FOR THE PLANS THAT OWN IT, AND IT IS THREE THINGS: (1) D7-12,
  the fourth occurrence of D7-3 -- nothing in src/ SENDS a report yet, because this plan's
  non-goals exclude deciding WHEN, which is 07-07's end_of_game.py; every importer of
  message.py / sink.py / gmail_sink.py outside the package is a test, grepped, and every name
  that COULD be wired inside the package IS; (2) build_gmail_transport's only caller is
  07-10's OAUTH-RUNBOOK, which is what it exists for, and 07-09 must write that runbook
  against the real signature (params, scopes=SEND_ONLY_SCOPES, credentials_loader=...); (3)
  gmail_sink.py sits at 149/150 code lines -- the next plan to open it SPLITS, never
  compresses. Twelve deferred items now sit in the phase's deferred-items.md: D7-1 RESOLVED,
  D7-2, D7-3, D7-4, D7-5, D7-6, D7-7, D7-8, D7-9, plus D7-10 RESOLVED, D7-11 and D7-12 from
  this plan. Still open and NOT fixed per the scope boundary: the local-truth CI job is RED
  until 07-06 creates src/pursuit/gui/ (D7-6, by construction -- 07-06 turns it green by
  writing modules that pass, and must not soften the gate), and check_no_llm_in_strategy.sh
  has been absent from quality-gate.yml since 03-10. OQ-1/OQ-2/OQ-3 are CLOSED in code with
  citations and OQ-3 is now enforced at the point of use -- one test pins the mail instance at
  30 s and the LLM instance at 5 s in the same assertion block, so neither can be harmonised
  into the other. OQ-4 is resolved in the outline and half-implemented: message.py names the
  attachment result_<game_id>.json via 07-02's namer, and DryRunSink's .prev rotation is what
  makes the per-sub-game rewrite non-destructive; 07-07 owns the rest. OQ-5 -- the games-played
  VALUE -- remains the human's at 07-10, before any live send. NOTHING IN THIS REPO TRANSMITS:
  both shipped reporting.json files still read mode dry_run, asserted per role by a test that
  reads the raw JSON rather than the loader's enum, and no test anywhere can reach the network
  -- test_gmail_sink.py fails any non-loopback connect or DNS lookup, with two control tests
  proving the guard is armed.
stopped_at: PHASE 7 PLAN 04 EXECUTED (2026-08-17) -- THE MANDATORY REPORT NOW LEAVES AS AN
  ATTACHED application/json FILE, AND THE 429 WAIT STAYS IN THE ONE GATEKEEPER. Rule 34
  (docs/RULES.md:75) makes a free-text report a ZERO SCORE and rule 30 (:66) makes a broad
  OAuth scope a DISQUALIFICATION; both are pinned before a credential exists. THE CENTRAL
  VACUITY RISK WAS NAMED IN THE PLAN AND ENFORCED IN THE TREE: DryRunSink writes a file and
  returns success, so it would make every send assertion green whether or not GmailSink works
  -- so test_mail_sink_dry_run.py asserts only what a disk write can honestly assert, and
  test_gmail_credentials.py CHECKS that absence with an AST IDENTIFIER scan rather than a text
  search, because the dry-run file's docstring legitimately NAMES 429 and scope while
  explaining that it asserts neither; paired with a control that runs the same scan over
  test_gmail_sink.py and requires it to find something. Every REPORT-04/05 assertion runs
  against GmailSink through the real 07-01 ReportingChain with a fake transport raising real
  googleapiclient HttpErrors. MEASURED: statuses [429,429,200] -> sent=True, attempts=3,
  sleeps=[30,30]; statuses [429] always -> sent=False, attempts=4 (= retries_before_failure+1
  from the shipped reporting.json), sleeps=[30,30,30], refusal=SEND_FAILED, queued=True,
  pending=1, and after statuses=[200] + drain() the SAME report comes back off the queue and
  is compared after a round trip through base64, MIME and json.loads -- recoverability, not
  "nothing raised". GmailSink RAISES GmailRetryableError on 429 and never sleeps: a second
  backoff would be a second gatekeeper (SEGAL Sec4) and would make the test pass for the wrong
  reason. THE BACKOFF ASSERTION TRANSCRIBES THE LITERAL 30 rather than reading
  params.wait_after_error_seconds back -- written the obvious way it would have stayed GREEN
  with the config lowered to Table 19's bare 5 s (probe ii: 3 failed). RULE 30 IS ENFORCED
  TWICE, and the second one is the one that matters: a token.json left over from a broader
  consent is what actually AUTHORISES the call and never appears in the list of scopes we
  asked for. Six forbidden scope sets refused (send+readonly, send+mail.google.com, modify,
  compose, mail.google.com alone, and the EMPTY set) by SET EQUALITY, so "contains gmail.send"
  cannot pass. D-70 HOLDS, GREPPED NOT ASSERTED: google.auth / google.oauth2 /
  google_auth_oauthlib / googleapiclient all resolve to exactly one file in src/,
  services/reporting/gmail_sink.py -- and GmailSink is DELIBERATELY NOT re-exported from the
  package __init__, the one departure from services/llm's convention, because that package
  must import anthropic_provider for its register_provider side effect and this one has no
  such requirement; re-exporting would load google-* (measured 0.265 s) for every dry_run
  importer. TWELVE REVERT PROBES, every count real and every mutation confirmed WIRED before
  the run: report interpolated into the body 2 failed; JSON sent inline instead of attached 4
  failed; attachment renamed off 07-02's namer 2 failed; dry run writes no .eml 3 failed;
  durable bytes write reverted to text mode 2 failed (CRCRLF observed on disk); GmailSink
  swallows 429 3 failed; backoff lowered to 5 s 3 failed; scope gate weakened to membership 4
  failed; granted-token check removed 1 failed; scope gate moved BELOW the credential read 7
  failed; asyncio.to_thread removed 1 failed; a test file named *_secret* 1 failed. THE HOLE
  THE SELF-AUDIT FOUND IN MY OWN WORK IS THE MOST COMPLETE FORM OF VACUITY THIS PHASE HAS SEEN:
  tests/unit/test_gmail_credentials.py shipped first as test_gmail_secrets.py, and
  .gitignore:26's *_secret* SWALLOWED IT SILENTLY -- eighteen passing tests, including every
  rules 39-40 assertion in the plan, that git would have refused to track, CI would never have
  run and the grader would never have seen. Caught only because git status --short before the
  commit did not list a file I had just written. Fixed by RENAMING, not by weakening the
  pattern, and the class of mistake is now a permanent gate: git check-ignore -z --stdin over
  every .py under src/ tests/ training/ scripts/, which FAILS rather than skips without git
  (D7-6's standard), carries an anti-vacuity floor of >100 files scanned and is paired with a
  control asserting the scan does find .env. Measured while fixing it: no other .py in the
  repository is ignored. That check also taught that subprocess.run(text=True) on Windows
  writes CRLF into the child's stdin, so git saw every path with a trailing carriage return
  and reported FIVE FALSE POSITIVES -- the helper passes bytes with -z and says why. TWO MORE
  MEASURED CORRECTIONS: iter_attachments() is NOT a disposition filter (probe B failed only 1
  test instead of 4 until the helper filtered on get_content_disposition()), and
  socket.connect cannot be blanket-refused on Windows (8 fixture ERRORs in asyncio's proactor
  self-pipe, so the guard is narrowed to non-loopback plus a DNS guard, both controlled).
  durable_write_bytes was EXTRACTED rather than a second write-and-rotate sequence written,
  and proven byte-neutral -- 98 IDENTICAL bytes both ways for a payload carrying a newline, a
  tab and Hebrew, because json.dumps escapes newlines and defaults to ASCII. The .eml goes
  through artifacts.write_artifact_bytes so it inherits D7-1's logs/ refusal instead of a
  hand-rolled Path.write_bytes no rule governs. THE PHASE-4 CONTROL STILL HOLDS: 07-01's
  26-test test_gatekeeper_llm_unchanged.py passes UNMODIFIED and git diff config/ is EMPTY.
  Zero numbers invented -- 429 is RFC 6585 and is what rule 28 names, v1 is Google's, and
  every limit comes from the shipped reporting.json whose _sources object cites each leaf.
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
