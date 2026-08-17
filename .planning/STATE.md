---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 08-01 and 08-02 are fully committed and closed, tree clean. NEXT IS THE
  REST OF PHASE 8'S WAVE 1: 08-03 (publication hygiene, `LICENSE`, `CONTRIBUTING.md`, packaging
  metadata), 08-04 (league ledger + `league.json` + the declaration artifact's FIRST production
  caller) and 08-05 (deferred #13/#19). WHAT 08-01 AND 08-02 LEAVE FOR THEM, AND IT IS WRITTEN
  DOWN RATHER THAN REMEMBERED: `docs/SUBMISSION-CHECKLIST.md` is the gap register and it names
  the owning plan for every one of its 32 GAPs. 08-03 inherits SEVEN of them -- `LICENSE`
  (blocked on OQ8-5, a human names the licence), `CONTRIBUTING.md`, `pyproject.toml`
  `license`/`authors`, `__all__` missing from 7 of 11 packages, `__version__` in ZERO
  `__init__.py`, no automated test-report artifact, and TWO the outline never predicted:
  root-level `graph.json` and `graph.html` are NOT gitignored (`git check-ignore -q` exits 1 for
  both, while `.gitignore:151-152` covers only the `.planning/graphs/` copies and CLAUDE.md
  asserts they are ignored), and 4 of 26 tracked config JSONs carry no `version` field
  (`config/{police,thief}/{resolution,role}.json`). 08-04 inherits the one finding a
  path-and-pattern gate cannot express as a row: `build_declaration_artifact` /
  `write_declaration_artifact` / `DeclarationContext` have ZERO production callers, re-derived
  at HEAD -- only their own module, a docstring mention at `artifact_config.py:151`, the
  `__init__` re-export, and tests. 08-11 inherits T5-06: `version.py` reads `1.00` and
  `pyproject.toml` reads `1.00.0`, and D-79 derives the tag name from the reconciled value.
  NOTHING IN THIS REPO HAS BEEN PUSHED: `git tag -l` is EMPTY and 125 commits sit ahead of
  `origin/main`. The two new gates make only local git reads (`ls-files`, `log`, `tag -l`,
  `check-ignore`).
stopped_at: PHASE 8 PLANS 01 AND 02 EXECUTED (2026-08-17) -- THE SEC17 AUDIT BUILT AS A GATE
  THAT CAN FAIL, AND EVERY TRACKER RECONCILED IN ONE PASS. Neither plan file existed; both were
  executed from `08-PLAN-OUTLINE.md` Sec9, with every predicted finding RE-DERIVED against the
  tree rather than inherited. 08-01: `scripts/check_submission.py` + 12 siblings, 86 rows,
  41 PASS / 32 GAP / 13 UNJUDGED, exit 0 all-pass / 1 any GAP / 2 on an evidence set that judged
  NOTHING. UNJUDGED IS NOT A PASS -- Table 5's own `Enforced by` column marks OOP, TDD and
  hardcoded values `Code review`/`Work process`, so 13 rows carry it and are counted apart. The
  mechanism inventory is WALKED from `git ls-files` (10 packages) and ANSWERED from
  `docs/mechanism-prd-map.json`, never from a `docs/PRD_*.md` glob, and a SUPERSEDED PRD is
  refused as coverage by name. The README is judged on Sec2.1's SEVEN items individually plus
  two DERIVED rule-42 honesty rows -- 3 unqualified mentions of `Q-Learning`, the term extracted
  from the superseded PRD's own H1, and Phase 3 still shown "in progress" against a `passed`
  verification. THIRTEEN PROBES, each asserting the mutation LANDED before the verdict was read
  and each reverted with the tree verified clean: `--empty-probe` exits 2; a FULL 86-row set with
  `mechanism_count=0` also exits 2, so EMPTY_EVIDENCE OUTRANKS 32 real GAPs; one counter-control
  per group flipped exactly its own row (docs/PLAN.md, a docstring-less module, the CI workflow,
  `.env-example`, 3 of 4 curve artifacts, and a POSITIVE control that turned ISO-25010 green and
  back); a planted empty package adds exactly one GAP row; a 161-line file trips G2-03 AND its
  T5-08 citation; a stale allowlist entry and a provider key planted INSIDE an allowlisted file
  both fail G4-02. THE GATE FOUND TWO DEFECTS IN ITS OWN WORK: probe 11 exposed POSITIONAL row
  ids, so inserting one package renumbered every row after it -- rows are now identified by the
  path they judge; and a test mutation exposed a VACUOUS TEST OF MINE, a mermaid check asserting
  only `.match`, which anchors regardless of the pattern and passed under a deliberately weakened
  regex -- it now asserts `.search` too and adds an end-to-end row over the real trap file which
  first asserts the trap still exists. 08-02: `.planning/REQUIREMENTS.md` header 74 -> 77
  (counted, not asserted -- the per-family breakdown always summed to 77), 6 -> 48 ticks, and
  EVERY tick cites a path plus a VERBATIM QUOTE that `scripts/check_requirements_ledger.py` reads
  back; all ten traceability rows carry an evidenced verdict and ONE surviving `Pending` that
  says why; STRAT-01/02/06 reworded from the WITHDRAWN tabular Q-learning to the matrix mover,
  honouring `03-VERIFICATION.md`'s "OPEN, flagged not fixed" hand-off; `docs/TODO.md`,
  `.planning/ROADMAP.md` Progress and `docs/phases/phase-1/TODO.md` moved in the SAME commit,
  because fixing one misdescribes the repo in the other direction. PHASES 4, 7 AND 8 ARE SHOWN
  INCOMPLETE BECAUSE THAT IS WHAT THEIR ARTIFACTS SAY: LANG-01/LANG-06 held open (no live GATE-4;
  responder side unmeasured since 05-06), ALL NINE REPORT-* held open (gate-measured is NOT
  phase-verified -- no `07-VERIFICATION.md` exists at all), all twelve SUB-* open, and four QUAL
  rows open because Table 5 itself marks them unjudgeable. THE FLIP PROBE FOUND A HOLE IN THE
  LEDGER GATE AND IT WAS CLOSED, NOT REPORTED: flipping SUB-05 first produced EXIT 0, because an
  open row legitimately cites the artifact explaining why it is open and a path-and-quote check
  cannot tell that from proof of completion -- one character produced a green ledger claiming a
  Git tag existed while `git tag -l` is empty. Closed by two independent rules: an evidence
  marker that now means SATISFIED and appears only on ticked rows while open rows carry a status
  marker, and a per-family declared tick count on every traceability row which the gate counts
  and compares, catching a flip in EITHER direction (probe 4 un-ticks SEC-04 and trips three
  rules). The header-total rule also caught an ARITHMETIC ERROR IN MY OWN SUMMARY PROSE -- 47 vs
  the real 48 ticks -- corrected before commit. Gates: 2188 passed / 0 failed against the 2153
  baseline (+35 tests); coverage 97.37% (baseline 97.37%, UNCHANGED -- `scripts/` is on neither
  the coverage source list nor `check_line_limit.sh`'s glob, which is exactly why 35 tests load
  those modules BY PATH); ruff 0 violations; `check_line_limit.sh` exit 0 with all twenty new
  `.py` files ALSO checked explicitly by path, and TWO files SPLIT rather than compressed --
  `submission_readme.py` at 168 and `requirements_ledger.py` at 149 of 150, split at 149 because
  a file one line from the gate is a trap for the next editor; `check_local_truth.py` OK 7
  modules; `check_no_llm_in_strategy` OK; `check_requirements_ledger.py` exit 0 with 48 citations
  resolved to real quotes; `check_submission.py` exit 1 with 32 GAPs, unchanged by the
  reconciliation -- which closed no Sec17 gap and claimed none. Rule-38 counters, both plans: the
  full suite moved police 1922->1922 and thief 1915->1915, DELTA 0/0; `git diff config/` EMPTY.
  Every new file confirmed NOT gitignored (D7-10's guard), and every touched file confirmed at
  CR=0. One correction worth carrying forward: `git checkout -- <file>` on a probe restores from
  the INDEX, so a mutation that was `git add`ed survives the revert -- the post-revert grep
  caught a planted provider-key shape still sitting in `tests/unit/test_step0_sign.py`, fixed
  with `git checkout HEAD -- <file>`. A post-revert ASSERTION is the only reason that was noticed.
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
