---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 08-06 is committed and closed; the tree is clean apart from untracked
  throwaway `game_artifacts/`, which must NEVER be committed (D7-19: a grader reads those
  filenames as league evidence). WAVE 2 CONTINUES: 08-07 (architecture docs, C4 x4, ISO 25010,
  extension points), 08-08 (the three missing per-mechanism PRDs) and 08-09 (research and
  visualization). All three depend only on 08-01, share no files with each other or with 08-06,
  and need WORKTREES if run concurrently.
  WHAT 08-07/08-08/08-09 INHERIT, WRITTEN DOWN RATHER THAN REMEMBERED: `check_submission.py`
  now exits 1 at **58 PASS / 15 GAP / 13 UNJUDGED** (was 49/24/13). The 15 remaining belong to
  08-07 (4: G1-13 mermaid, G6-01, G6-02, G6-05), 08-08 (3: the sdk/gui/tunnel PRDs), 08-09
  (4: G1-14 PROMPT_LOG, G5-02, G5-03, G5-05), 08-11/08-12 (2: G6-08 the tag and T5-06's version
  reconciliation) and **08-06+07-10 jointly (2: G1-03b and G5-04, the screenshots)**.
  THE TWO SCREENSHOT ROWS ARE NOT 08-06's TO CLOSE and are left GAP on purpose. The README
  carries two MARKED-ABSENT SLOTS naming `docs/assets/live-gui-heatmap.png` and
  `docs/assets/replay-verified-ok.png` and the plan that produces them (07-10). A NEW TEST
  ENFORCES THAT DISCIPLINE: `tests/unit/test_readme_contract.py` fails the moment ANY image
  link in the README resolves to nothing, so the slot cannot quietly become a fake asset.
  A NEW STANDING CONSTRAINT FROM 08-06: the README is now judged BY THE SUITE, not only by the
  CLI. Eight derived checks in `tests/unit/readme_contract_checks.py` -- Sec2.1's seven items,
  Sec9.4.2's six sections, every relative link resolves, every repo path quoted in a fenced
  command block exists, the shipped mail mode is stated while it is dry_run, no phase without a
  `NN-VERIFICATION.md` reads as verified, the README names the brain `config/*/strategy.json`
  actually selects, and NEITHER games_played counter value appears (rule 38). A plan that edits
  the README must keep all eight green. 08-07 in particular: adding `docs/ARCHITECTURE.md` to
  the README's Documentation map is safe, but linking it BEFORE creating it goes red.
  ALSO: `scripts/plot_run2_curves.py` is the ONLY curve generator that exists.
  `training/plot_curves.py` and `training/curves.py` were DELETED in `f3d9847` with the rest of
  the run-1 stack -- the old README documented a command nobody could run. `artifacts/curves/`
  now holds FIVE images: three from the WITHDRAWN run 1 and two from run 2. The two run-2
  figures are drawn from TRACKED `artifacts/run2/curve.json` and `artifacts/run2_es/curve.json`,
  and `config/{police,thief}/weights.json` is BYTE-IDENTICAL to `artifacts/run2/weights.json`.
  STILL OPEN AND STILL A HUMAN'S: OQ8-1 (D7-17, DRAFTED and UNSENT), OQ8-2 (the games-played
  VALUE -- 08-06 put NO number in the README and a test enforces it), OQ8-5 (THE LICENCE --
  still PREPARED, NOT ADOPTED; the README's new `## Licence` section says all rights reserved
  until the owner confirms, and `**LICENCE STATUS:** AWAITING_OWNER_CONFIRMATION` plus its
  biconditional test are UNTOUCHED), OQ8-6 (the two repo URLs) and OQ8-7 (the token ceiling).
  **OQ8-8 IS NOW EXPLICITLY UNRESOLVED RATHER THAN QUIETLY ASSUMED.** The instruction was to
  confirm against the book whether Sec9.4.2 mandates Hebrew. The book is in Hebrew and CLAUDE.md
  forbids re-deriving from it; `SEGAL_GUIDELINES.md`, `RULES.md` and `PROJECT_GUIDE.md` carry NO
  language requirement. English is recorded as an ASSUMPTION in `docs/SUBMISSION-CHECKLIST.md`.
  NOTHING IN THIS REPO HAS BEEN PUSHED: `git tag -l` is EMPTY and 149 commits sit ahead of
  `origin/main`.
stopped_at: 08-06 CLOSED (2026-08-17) -- THE ROOT README REBUILT, AND ITS CENTRAL CLAIM WAS
  FALSE. `README.md:7` said each agent decides moves "with a trained tabular Q-learning policy
  (Bayes + BFS fallback)". Phase 3 WITHDREW that design as unsound under the book's simultaneous
  turn order (Sec5.3.2 p.35) and shipped a matrix-game mover over a learned 15-weight
  evaluation. UNQUALIFIED MENTIONS 3 -> 0, and phase 3 no longer reads "in progress" against a
  `passed` verification. No `08-06-PLAN.md` existed; executed from `08-PLAN-OUTLINE.md` Sec9.
  THIS RUN WAS TERMINATED MID-PLAN BY A SERVER-SIDE 529 and resumed. On resumption the tree was
  RE-READ rather than trusted: 26bd9d8 was verified committed and NOT redone; README.md was
  found uncommitted at 511 lines with all 17 sections present, verified coherent by listing
  every heading AND by running the gate's own `_sections()` parser over it, then continued.
  FOUR COMMITS, each atomic: `26bd9d8` the run-2 curves, `129fa7f` the README, `a5fc8c5` the
  contract tests, `6141b61` the register + phase TODO.
  GAP MOVEMENT: 49 PASS / 24 GAP / 13 UNJUDGED -> **58 / 15 / 13**. NINE rows, and EXACTLY the
  nine 08-06 owned (G1-01..G1-09). NO OTHER ROW MOVED IN EITHER DIRECTION -- that symmetry is
  the counter-control. G5-04's image count rose 3 -> 5 from this plan's two new curves and the
  row DID NOT MOVE, which is the judge working correctly: a learning curve is not a screenshot.
  ASSERTIONS PROVEN RED ON THE OLD FILE, not asserted to be: `git show HEAD:README.md` was
  restored in place and the test file run against it -- **6 failed / 11 passed** -- then restored
  and the restoration verified BYTE-IDENTICAL by SHA-256. 6 of the 8 checkers return violations
  on the old README; the two that do not (broken links, counter leak) are reported as GUARDS,
  not dressed up as regressions. Every checker has an anti-vacuity control that fires it.
  SIX DEVIATIONS, AND FOUR WERE DEFECTS IN THIS PLAN'S OWN WORK, found before commit:
  (1) `plot_run2_curves.py` crashed on an out-of-tree `--out-dir` (`relative_to` ValueError);
  (2) THE OUTLINE'S OWN ACCEPTANCE WAS WRONG -- it said to use the existing
  `artifacts/curves/*.png` "with the generating command recorded", but those are the WITHDRAWN
  run's figures and the command names `training/plot_curves.py`, DELETED in `f3d9847`. The
  outline's own trap for this plan says to show what the shipped fit produced, so
  `scripts/plot_run2_curves.py` was written instead;
  (3) A FRAGILE GATE PASS IN MY OWN README -- `#` comments inside a bash fence parse as H1
  headings in the gate's `_sections()` (it does not track fences), so G1-02 was passing with a
  body of EXACTLY 3 lines, the floor. Fixed to 42 lines, zero phantom sections. FOUND BY
  INSPECTING THE PARSE, NOT THE VERDICT;
  (4) my own phase-8 status row said "In progress" without saying the phase is unverified -- the
  new contract test caught it and THE README WAS FIXED, NOT THE CHECK;
  (5) I wrote that "the peer that comes up first retries until the other answers"; grepping found
  only a durable DISK-WRITE retry (`_DECLARE_RETRIES = 3`), so the unsupported claim was replaced
  with `HandshakeOutcome.UNREACHABLE`, which is real;
  (6) I attributed the four game artifacts to rule 50; `docs/RULES.md:99` does not name them, so
  the attribution moved to `docs/PARAMETERS.md`, which does.
  WHAT THE README DELIBERATELY DOES NOT CLAIM: mail `dry_run` + live PENDING (no report has ever
  been delivered), phase 4 `human_needed`, phases 7 AND 8 NOT verified, NO league game played,
  NO games-played number anywhere, screenshots as MARKED-ABSENT SLOTS, the rule-49 cross-link as
  a STATED ABSENCE naming 08-12, and the licence PREPARED, NOT ADOPTED. Understatement avoided
  too, by pointing at evidence: 2366 tests, 97.44%, Sec10.4 met for phases 1/2/3/5/6, GATE-5
  closed across two machines on two networks, commit-reveal with nonces and a mutual audit.
  EVERY DOCUMENTED COMMAND WAS RUN BEFORE IT WAS DOCUMENTED: `uv sync`, `--check-config` for both
  roles (output quoted verbatim), `dev_launch.py`, both GUI processes' `--help` and `--once`, the
  `.jsonl` refusal (exit 2, as claimed), `plot_run2_curves.py`, and all seven gate commands.
  GATES: 2366 passed / 0 failed (baseline 2342; +7 curve tests, +17 contract tests), coverage
  97.44% (unchanged -- the new code is in `scripts/`, outside the coverage source list, and is
  measured by tests loaded BY PATH), ruff 0, line-limit 0 tree-wide with all four new `.py` files
  ALSO checked by path (104/77/124/65) and the by-path form PROVEN to fire, local-truth 7
  modules, no-LLM OK, `uv lock --check` exit 0, `check_submission.py` exit 1 at 58/15/13.
  RULE-38 COUNTERS, ALL FOUR: suite 1925->1925 / 1918->1918 (0/0); one real game 1925->1926 /
  1918->1919 (+1/+1), `game_id` `47873d48ba712222`, BOTH seats `audit_verdict matched=true`,
  zero technical_win, zero watchdog_incident. `git diff config/` EMPTY -- the counters are
  gitignored at `.gitignore:90`, so no counter value can be committed.
  SELF-CHECK PASSED: 9 paths verified present AND tracked AND not gitignored, 4 commits verified
  reachable, and TWO code-line numbers CORRECTED rather than left as written (67->77, 87->124).
  NOTHING PUSHED, NO TAG CREATED, NO REMOTE TOUCHED.
---

Last session: 2026-08-17T23:20:00+03:00
Stopped at: Completed 08-06 in full -- the root README rebuilt to Sec2.1's seven items AND
  Sec9.4.2's six sections, with the rule-42 honesty defect closed. Four atomic commits
  (`26bd9d8`, `129fa7f`, `a5fc8c5`, `6141b61`). Interrupted mid-plan by a 529 and resumed by
  re-reading the tree rather than trusting it. `check_submission.py` 49/24/13 -> 58/15/13,
  exactly the nine rows this plan owns. New assertions proven RED on the pre-fix file: 6 failed
  / 11 passed against `git show HEAD:README.md`, restored byte-identically afterwards. Six
  deviations, four of them defects in this plan's own work found before commit -- including a
  GATE PASS THAT WAS FRAGILE RATHER THAN WRONG (a `#` comment inside a bash fence parses as a
  heading, leaving G1-02's body at exactly the 3-line floor). Counters: suite 0/0, one real game
  +1/+1, `game_id` `47873d48ba712222`, both seats matched=true.
Resume file: None -- the tree is clean and 08-06 is closed. Next is `/gsd:execute-phase 8`
  continuing wave 2: 08-07 (architecture docs), 08-08 (the three per-mechanism PRDs) and 08-09
  (research and visualization). None of them shares a file with 08-06, but all three must keep
  `tests/unit/test_readme_contract.py` green if they touch README.md.
---


Last session: 2026-08-17T16:40:00+03:00
Stopped at: Completed 08-03 and 08-05 in full -- WAVE 1 OF PHASE 8 IS CLOSED. Neither plan file
  existed; both executed from `08-PLAN-OUTLINE.md` Sec9. Eleven atomic commits (7 + 4).
  08-03 moved `check_submission.py` from 41 PASS / 32 GAP / 13 UNJUDGED to 49 / 24 / 13 -- eight
  rows, exactly the eight it owned, no other row moving in either direction. 08-05 CLOSED both
  phase-5 deferred items rather than accepting them, and proved the shipped commit-reveal-ON path
  byte-identical with a nonce-pinned fingerprint (same h_commit, same push turns, same ledger
  record) so the D-59 hash input and the D-64 join key are demonstrably untouched.
  THE LICENCE IS PREPARED AND NOT ADOPTED, and that is enforced rather than merely written:
  `LICENSE` carries a `PREPARED, NOT ADOPTED` block, `docs/SUBMISSION-CHECKLIST.md` carries
  `**LICENCE STATUS:** AWAITING_OWNER_CONFIRMATION`, and a biconditional test fails if either
  changes without the other. 08-12 must not publish until the owner confirms.
  Three self-inflicted test defects were found by this session's own probes and closed before
  commit, and one INHERITED bookmark (05-18's, written to fail on #19's closure) was found NOT to
  fire and was repaired. Self-check PASSED for both plans: 13 created paths verified present AND
  tracked AND not gitignored, 11 commits verified reachable.
  NOTHING PUSHED, NO TAG CREATED, NO REMOTE TOUCHED -- `git tag -l` is empty and 144 commits sit
  ahead of `origin/main`.
Resume file: None -- the tree is clean apart from untracked throwaway `game_artifacts/`, which
  must never be committed. Next is `/gsd:execute-phase 8` continuing into WAVE 2: 08-06, 08-07,
  08-08 and 08-09, a four-way fan-out over disjoint document sets (worktrees if run in parallel).
---


Last session: 2026-08-17T21:05:00+03:00
Stopped at: Completed 08-04 in full. NO `08-04-PLAN.md` EXISTED -- the phase directory holds only
  `08-CONTEXT.md` and `08-PLAN-OUTLINE.md`, so the plan was executed from the outline's Sec9
  08-04 entry, and every finding it predicted was RE-DERIVED at HEAD rather than inherited. Five
  atomic commits: `4fbd4ed` (config/{police,thief}/league.json + shared/league_config{,_fields}.py
  + shared/absent.py, D-81), `e672838` (services/reporting/league_ledger{,_fields,_bounds}.py,
  D-80), `8c6fd1e` (services/reporting/end_of_game_declaration.py -- THE first production caller),
  `daf5654` (the D7-17 draft and the checklist finding recorded CLOSED) and `b32bf9d` (graph
  refresh, 11097 nodes / 19646 edges; `graph.html` skipped, over the 5000-node viz limit).
  THE DEFECT: `build_declaration_artifact` / `write_declaration_artifact` / `DeclarationContext`
  had ZERO production callers, so `declaration_<game_id>.json` -- one of rule 50's FOUR MANDATORY
  artifacts -- had never been written by a game. CLOSED, and proven by a REAL `dev_launch` run
  (exit 0, `game_id` `397b3503b1bfa996`): both seats wrote the artifact with `repo_urls`,
  `mcp_server_addresses`, `token_ceiling` 200000, `start_time`/`end_time` taken from each seat's
  OWN wire log, and BOTH signed Step-0 envelopes embedded verbatim. Evidence committed at
  `docs/phases/phase-8/declaration-evidence/`. The call sits in `end_of_game._report` after both
  sealed artifacts and BEFORE the chain, contained SEPARATELY from the mail send -- rules 32/35
  make an unreported game cost BOTH teams everything, so a broken declaration returns None and
  logs while `EndOfGameReport.declaration_artifact` keeps the failure observable.
  RULE 38 UNMOVED: no games-played value set, defaulted or inferred. The ledger returns BOTH
  candidate counts plus an UNSET marker; the artifact's new `games_played_declared` is
  UNPARAMETERISED and names `GAMES-PLAYED-RECONSTRUCTION.md`; `league.json` carries no
  games-played leaf and a test asserts its absence. RULE 49 UNMOVED: four `null` slots rendered as
  stated-absence markers naming 08-12, with a live-mode refusal. D7-17 DRAFTED AND UNSENT.
  EIGHT PROBES, each asserted landed then reverted by rewriting the file. PROBE E FOUND A HOLE IN
  MY OWN WORK -- the max-games test moved with its own constant, so `MAX_GAMES_PER_TEAM = 11` left
  the ledger suite green on a **fixed** Table 18 row; closed by parsing the value out of
  `docs/PARAMETERS.md`. A second vacuity (a docstring stripper using `split('\"\"\"')[-1]`) was
  caught and closed before commit. Probe F removed the `declare_game` call site entirely and 7
  tests failed. Gates: 2293 passed / 0 failed (baseline 2188), coverage 97.43% (from 97.37%),
  ruff 0, line-limit 0 tree-wide with every new file also checked by path, local-truth 7 modules,
  no-LLM OK, `check_submission.py` exit 1 at 41/32/13 (unchanged -- the finding was never a row).
  Counters: suite 1923->1923 / 1916->1916 (0/0); one real game 1922->1923 / 1915->1916 (+1/+1).
  Two structural ledgers (`DURABLE_WRITE_BINDERS`, the log-artifact reacher list) and one test
  fixture correctly flagged the new modules and were updated honestly, not exempted.
  Self-check PASSED: 23 created paths verified present and tracked, five commits verified
  reachable. NOTHING PUSHED, NO TAG CREATED, NO REMOTE TOUCHED -- `git tag -l` is empty and 131
  commits sit ahead of `origin/main`.
Resume file: None -- the tree is clean and 08-04 is closed. Next is `/gsd:execute-phase 8`
  continuing wave 1: 08-03 (publication hygiene -- seven registered GAPs, `LICENSE` blocked on
  OQ8-5, and it should re-count the tracked config JSONs now that league.json added two) and
  08-05 (deferred #13/#19, where `turn_buffer.py` sits at 146/150 and needs a SPLIT).
---


Last session: 2026-08-17T18:40:00+03:00
Stopped at: Completed 08-01 and 08-02 in full. NEITHER PLAN FILE EXISTED -- the phase directory
  holds only `08-CONTEXT.md` and `08-PLAN-OUTLINE.md`, so both were executed from the outline's
  Sec9 entries, and every finding the outline predicted was RE-DERIVED against the tree rather
  than inherited. Two commits, each atomic: 08-01 the Sec17 + Table-5 audit gate (`4b63ee7`,
  21 files) and 08-02 the project-wide tracker reconciliation (`aeb7272`, 10 files, ONE commit
  by design). 08-01 delivers `scripts/check_submission.py` + 12 siblings and
  `docs/SUBMISSION-CHECKLIST.md`: 86 rows re-derived from the tree on every run, 41 PASS /
  32 GAP / 13 UNJUDGED, exit 0/1/2 with 2 meaning the evidence set judged NOTHING and OUTRANKING
  a run that found 32 real gaps. Thirteen probes, one counter-control per group, each asserting
  the mutation LANDED first; probe 11 and a test mutation each found a defect in this plan's own
  work (positional row ids, and a mermaid test that `.match`'s own anchoring made vacuous), both
  fixed rather than reported. 08-02 rebuilt `.planning/REQUIREMENTS.md` from the verification
  artifacts -- header 74 -> 77 counted, 6 -> 48 ticks each citing a verbatim quote the new
  `check_requirements_ledger.py` reads back -- and moved `docs/TODO.md`, the ROADMAP Progress
  table, `docs/phases/phase-1/TODO.md` and `docs/phases/phase-8/TODO.md` in the same commit.
  Phases 4, 7 and 8 are shown INCOMPLETE because that is what their artifacts say. The flip probe
  found a hole in the ledger gate -- an open row's own citation made a `[ ]` -> `[x]` flip pass --
  closed by an evidence/status marker split plus a per-family declared-tick-count cross-check
  that catches a flip in either direction. Gates: 2188 passed / 0 failed (baseline 2153),
  coverage 97.37% unchanged, ruff 0, line limit exit 0 including all twenty new `.py` files by
  path, local-truth 7 modules, no-LLM OK, ledger gate exit 0, audit gate exit 1 with its 32
  registered gaps. Rule-38 counters: police 1922 -> 1922, thief 1915 -> 1915, delta 0/0;
  `git diff config/` empty. Both summaries written with every number taken from a command run in
  this session; self-check PASSED for both (32 paths verified present AND tracked AND not
  gitignored, both commits verified reachable, and three numbers in `SUBMISSION-CHECKLIST.md`
  CORRECTED rather than left -- they were probe-state values, not HEAD values).
  NOTHING PUSHED, NO TAG CREATED, NO REMOTE TOUCHED: `git tag -l` is empty and 125 commits sit
  ahead of `origin/main`.
Resume file: None -- the tree is clean and both plans are closed. Next is `/gsd:execute-phase 8`
  continuing into the rest of wave 1: 08-03 (publication hygiene -- it inherits seven registered
  GAPs including two the outline never predicted, and `LICENSE` is blocked on OQ8-5), 08-04
  (the league ledger and the declaration artifact's first production caller) and 08-05.
---

Last session: 2026-08-17T13:35:00+03:00
Stopped at: Completed 07-09-PLAN.md (GATE-7 measurement + `docs/PRD_gatekeeper.md` +
  `OAUTH-RUNBOOK.md`) in full. Six commits, each atomic: Task 1 `measure_gate7.py` and its six
  siblings (`08705d9`); Task 2 the per-mechanism gatekeeper PRD (`ba72c8a`); a self-audit fix for
  the one-counter defect the gate found in its own work (`9e044d5`); the three routed findings --
  D7-18, D7-19 and the rule-25 CI job (`96495d4`); Task 3 the gate record and the runbook
  (`88d21fb`); Task 4 the graph refresh (`bb8b1da`). Gates: `ruff check .` 0 violations;
  2153 passed / 0 failed against the 2130 baseline; coverage 97.37% (baseline 97.37%, unchanged
  -- this plan adds tests, not source); `check_line_limit.sh` exit 0 with all ten new `.py` files
  ALSO checked explicitly by path (`scripts/` is NOT enumerated by the no-arg form, which is the
  point); `check_local_truth.py` -> `OK: 7 module(s) scanned`, exit 0;
  `check_no_llm_in_strategy.py` OK and now a CI job too; every new `.py` confirmed NOT ignored by
  git (D7-10's guard); `measure_gate7.py` exit 0, run twice with a byte-identical summary;
  `scripts/dev_launch.py` exit 0, game `6694ec24875b4208`, 11 matched=true audit records per
  seat, one `audit_verdict` and one `game_over` per seat, ZERO `technical_win`, ZERO
  `watchdog_incident`; `git diff config/` EMPTY and both `reporting.json` files still `dry_run`.
  Rule-38 counters, all four: the full suite moved police 1921->1921 and thief 1914->1914 (delta
  0/0); one real game moved 1921->1922 and 1914->1915 (delta 1/1) -- and the gate script now reads
  BOTH counters itself, before and after, because it plays a real game. Secret scan over every
  new doc, script and the evidence JSON: clean. Two things are NOT byte-identical across gate
  runs and both are recorded rather than smoothed -- `generated_at`, and the local-truth gate's
  own two ERROR diagnostics from the empty-scan control, which echo the throwaway temp directory;
  the replay refusal's temp path is redacted to `<tmp>` in a field whose NAME says so, which also
  keeps a local username out of a file bound for a public repo (rule 49). One correction worth
  carrying: `git checkout --` on a probe reverts the FILE, not the probe, and it wiped
  uncommitted D7-18 work once; later probes reverted by inverse edit. A first reading of probe 9
  was also wrong (a truncated pytest tail) and was re-run cleanly for an accurate record.
  `GRAPH_REPORT.md` is a COMMUNITY DIGEST, not a node listing, so grepping it for a module path
  proves nothing -- verified by querying instead: `publish_view` at `view_publish.py:90` (degree
  17), `open_replay` at `replay_verify.py:163` (degree 12), `build_reporting_chain` at
  `end_of_game_chain.py:97` (degree 16), `LiveDashboard` at `live_app.py:47` (degree 8). Graph
  refreshed: 10473 nodes / 18679 edges / 597 communities. `07-09-SUMMARY.md` written with every
  number from a command run in this session, self-check PASSED (24 paths verified present AND
  tracked AND not gitignored, 6 commits verified reachable, and two citation errors CORRECTED
  rather than left). `docs/phases/phase-7/TODO.md` gains a ticked 07-09 row and a ticked 07-96.
Resume file: None -- the tree is clean and 07-09 is closed. Next is 07-10, the phase's ONE
  `autonomous: false` plan: OAuth consent, one live send, the two README screenshots, and the
  OQ-5 games-played VALUE decision. Its procedure is `docs/phases/phase-7/OAUTH-RUNBOOK.md`,
  which states plainly that Claude must not enter credentials and must not click consent.
---

Last session: 2026-08-17T12:20:00+03:00
Stopped at: Completed 07-08-PLAN.md (the replay viewer -- load `log_`, recompute every hash,
  verdict banner, step/play/pause) in full. Three tasks, each committed atomically: Task 1 the
  verifier with its three verdicts and the non-zero-turn guard ahead of every aggregate
  (`bd1ce8d`); Task 2 the two thin Tk files that render and decide nothing (`cce667a`); Task 3 the
  round trip on a real game with both sources deleted, plus the production-caller scan (`f67e6b1`).
  A fourth commit closed two findings in my own work (`cbc6e97`): `banner_colour`'s one line, which
  was untested only because its sole caller lives in the coverage-omitted `gui/`, and two inline
  literal tables inside assert-bearing loops, now named and floored. Gates: `ruff check .` 0
  violations; 2130 passed / 0 failed against the 2090 baseline; coverage 97.37% (baseline 97.29%);
  `check_line_limit.sh` exit 0 with all fifteen new/touched files ALSO checked explicitly by path;
  `check_local_truth.py` -> `OK: 7 module(s) scanned`, exit 0 (was 5, grew by exactly two);
  `check_no_llm_in_strategy.py` OK; every new `.py` confirmed NOT ignored by git (D7-10's guard);
  `python -m pursuit.gui.replay_app --help` exit 0 and the `--once` scripted launch exit 0 against
  the REAL artifact, while a `.jsonl` path gives exit 2 with a message naming rule 18;
  `scripts/dev_launch.py` exit 0, game `55fa28cbef618a19`, both seats `"matched":true`, outcome
  capture, zero `technical_win`, zero `watchdog_incident`; `git diff config/` EMPTY. Rule-38
  counters, all four: the full suite moved police 1921->1921 and thief 1914->1914 (delta 0/0); one
  real game moved 1920->1921 and 1913->1914 (delta 1/1). All four new `services/` modules at 100%
  coverage -- `replay_verdict.py`, `replay_source.py`, `replay_session.py`, `replay_verify.py` --
  and `gui/` holds 181 of the 620 new `src/` code lines, every one of them widget construction.
  AST scan over all seven of this plan's test/fixture files: 0 parametrize sites (the four tampers
  are four tests, deliberately) and 3 assert-bearing loops, two of which carried inline tables and
  are now floored. Production-caller grep over every new public name: `open_replay` <-
  `gui/replay_app.main`, `banner_colour`/`SECTION_TITLES` <- `gui/replay_panels`, and the one name
  with test-only reachability (`verdict_for`) removed rather than excused; graphify agrees
  independently -- `open_replay` at `replay_verify.py:163`, degree 11, with an incoming
  `main() [calls]` edge. Graph refreshed: 10266 nodes / 18371 edges / 588 communities.
  `07-08-SUMMARY.md` written with every number from a command run in this session, self-check
  PASSED (17 paths verified present AND tracked AND not gitignored, 4 task commits verified
  reachable, and two file-size numbers CORRECTED rather than left as written).
  `docs/phases/phase-7/TODO.md` gains a ticked 07-08 row and a refreshed 07-96.
Resume file: None -- the tree is clean and 07-08 is closed. Next is `/gsd:execute-phase 7`
  continuing into 07-09 (GATE-7 measurement + `docs/PRD_gatekeeper.md` + `OAUTH-RUNBOOK.md`), which
  must take its criterion-3 evidence through `open_replay(path).verdict` and must report all THREE
  verdict states; then the human-in-the-loop 07-10.
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
