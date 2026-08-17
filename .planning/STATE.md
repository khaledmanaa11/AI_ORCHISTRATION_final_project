---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
Resume file: None -- 08-09 is committed and closed; the tree is clean apart from untracked
  throwaway `game_artifacts/`, which must NEVER be committed (D7-19). **WAVE 2 IS COMPLETE.**
  Next is wave 3's **08-10** (the two-repo split, built LOCALLY, nothing pushed).
  WHAT 08-10 INHERITS, WRITTEN DOWN RATHER THAN REMEMBERED: `check_submission.py` now exits 1 at
  **69 PASS / 4 GAP / 13 UNJUDGED** (was 65/8/13). All four remaining GAPs are somebody else's:
  G1-03b and G5-04 (the screenshots -- 08-06 with 07-10's material, still MARKED-ABSENT SLOTS
  and not to be faked), G6-08 (the tag, 08-11/08-12) and T5-06 (the `version.py` 1.00 vs
  `pyproject.toml` 1.00.0 reconciliation, 08-11, and D-79 derives the tag name from it).
  **`notebooks/` IS A NEW TOP-LEVEL DIRECTORY** and must survive the split. `analysis.ipynb`
  reads FOUR tracked artifacts under `artifacts/`; a split that drops `artifacts/` leaves it
  unable to execute, and `tests/unit/test_notebook_offline.py` FAILS inside that tree rather
  than passing quietly. **THREE NEW DEV DEPENDENCIES** (nbconvert, ipykernel, nbformat) are in
  `pyproject.toml`, so `uv sync` inside each split output must still resolve them.
  ONE TEST SKIPS BY DESIGN IN A SPLIT TREE:
  `test_research_docs.py::test_every_cited_commit_hash_resolves` skips when
  `git rev-list --count HEAD` is under 50, because 08-10's outputs have ONE initial commit and a
  hash from this repo cannot exist there. The skip NAMES its reason; every other test in that
  file runs there and must pass.
  THE STANDING CITATION CONSTRAINT NOW GOVERNS NINE DOCUMENTS: a backticked repository path in
  `ARCHITECTURE.md`, `QUALITY-25010.md`, `EXTENSION-POINTS.md`, `PRD_sdk.md`, `PRD_tunnel.md`,
  `PRD_gui.md`, `SENSITIVITY.md`, `TOKEN-COST.md` or `PROMPT_LOG.md` is a CLAIM THAT THE PATH
  EXISTS NOW. `tests/unit/doc_citation_helpers.py` enforces the first six against `git ls-files`;
  `tests/unit/test_research_docs.py` enforces the last three against the filesystem AND resolves
  every cited 7-hex commit hash. Reference a deleted file UNBACKTICKED. FIVE fabricated or
  unresolvable citations have now been caught this phase, one of them in 08-09's own first draft.
  A NEW OPEN CORRECTION, AND IT IS NOT 08-09'S TO MAKE: the sweep contradicts
  `docs/phases/phase-3/ENGINEERING-LOG.md` Act 4.3. The log records thief survival against a
  barrier-blind chaser as **89% -> 1%** across the swap decision, and `phase-3/PRD.md`,
  `phase-3/PLAN.md` and `src/pursuit/shared/resolution.py`'s `PREFERRED` docstring all quote it.
  Measured at HEAD: **32.0% -> 7.5%**. `scripts/sensitivity_reconcile.py` parses the old pair OUT
  OF THE LOG and re-measures all eight weights x rules x opening arms at n=200; the highest is
  52.5% and none approaches 1%. **The DIRECTION of the shipped decision is confirmed and needs no
  change** (the swap still costs the thief ~25pp and the cop seat is 100% under all four rule
  combinations) -- but "89% to 1%" MUST NOT be quoted as a current measurement. The CAUSE WAS NOT
  ESTABLISHED and no document pretends otherwise. Recorded in `docs/SUBMISSION-CHECKLIST.md`.
  STILL OPEN AND STILL A HUMAN'S: OQ8-1 (D7-17, DRAFTED and UNSENT), OQ8-2 (the games-played
  VALUE), OQ8-3 (where the form lives), OQ8-4 (the self-assessment SCORE), OQ8-5 (THE LICENCE --
  still PREPARED, NOT ADOPTED), OQ8-6 (the two repo URLs), OQ8-7 (the token ceiling), OQ8-8
  (README language, recorded as an ASSUMPTION), OQ8-9 (is `origin` public?).
  **OQ8-9 REMAINS URGENT AND UNANSWERED.** THIS AGENT PUSHED NOTHING and issued NO remote command
  of any kind, but the ref has moved on its own before (19:04 on 08-14, 13:35 and 17:14 on 08-16,
  and `acc5913` six minutes after it was committed). No corrective remote action was taken -- a
  force-push is itself touching the remote. `git tag -l` is still EMPTY.
stopped_at: 08-09 CLOSED (2026-08-17) -- THE REPOSITORY HAD NO SENSITIVITY ANALYSIS, NO
  NOTEBOOK, NO TOKEN-COST ANALYSIS AND NO PROMPT LOG. No plan file existed; executed from
  `08-PLAN-OUTLINE.md` Sec9, the same way 08-07 and 08-08 were. SEVEN ATOMIC COMMITS:
  `32440b4` the three dev deps, `486a01a` the sweep + its refusals + both artifacts, `a8931b7`
  the token-cost readers, `bcce41b` the executed notebook, `32535b7` the three documents,
  `112bd6f` the register and trackers, `aac4cf8` the self-audit fixes.
  GAP MOVEMENT: 65/8/13 -> **69/4/13**. FOUR rows, EXACTLY the four 08-09 owned (G1-14, G5-02,
  G5-03, G5-05); NO other row moved in either direction, which is the counter-control. The gate's
  own empty state re-observed at exit **2**.
  EVERY PUBLISHED NUMBER IS RENDERED FROM A COMMITTED ARTIFACT, and
  `tests/unit/test_research_docs.py` re-renders all FOUR generated blocks and compares them
  against the committed documents -- so a figure edited in by hand fails the suite instead of
  reaching a grader. Verified at HEAD: 5008 / 1014 / 2093 / 930 characters, all four present
  verbatim; `artifacts/token_cost/token_cost.json` rebuilds BYTE-IDENTICAL (sha256 693efe19...);
  the sweep's baseline cell reproduces exactly on a fresh 200-game run (116/200, 65/200,
  200/200).
  THE SWEEP CANNOT TOUCH A FIXED PARAMETER, AND THAT IS A PARSE RATHER THAN A PROMISE.
  `scripts/sensitivity_status.py` reads `docs/PARAMETERS.md`'s Status column (32 rows, 14 fixed);
  `refuse_fixed` fails on a fixed row, an unknown row, or a status the extract contradicts, and
  `refuse_downward` fails a `minimum` swept below the shipped value. The fixed list the document
  PRINTS comes from that same parse. 13 configurations x 3 matchups x 200 games, 755.6s, fully
  offline through `training/arena.run_match`.
  SEPARABLE FINDINGS (non-overlapping 95% Wilson, `arena.compare`'s conservative rule): board 11
  **+35.0pp** thief survival, horizon 70/70 **-29.0pp**, swap-as-capture **-25.0pp**, the prior
  instead of the fitted vector **-18.0pp**. Search depth (50 vs 200 vs 800 iterations) and extra
  barriers (21, 28) move NOTHING separably. The cop matchup is 200/200 at baseline and is flagged
  **SATURATED** in the document, the notebook and the renderer -- the effect ranking refuses to
  rank a knob on it at all.
  TOKEN COST, FROM THE ONE LIVE GAME AND LABELLED n=1 EVERYWHERE: input is **96.4%** of spend;
  the system prompts are **91-96%** of each call's input CHARACTERS and are re-sent every call;
  `_estimate_tokens` **over-reserves 1.35x** and the cause is located (the `max_tokens=300`
  ceiling is 42.5% of the reservation while real output averaged 19.1 tokens/call); and a
  **10-game series -- the FIXED maximum, Table 18 row 5 -- projects to 301,800 tokens against a
  200,000 budget and DOES NOT FIT**, so the ladder reaches TEMPLATE_ONLY at ~6.0 games and the
  language layer goes dark for the last four of a maximal series. Nobody had written that down.
  The mocked run transfers on CALLS (1.643 vs 1.662) and is **9.83x** away on TOKENS; pooling
  them would have corrupted every projection.
  THE PROMPT LOG CARRIES A MEASURED REVISION, not an anecdote: `bluff_prompt.py` said "phrasing a
  claim FOR a player" and produced "The player is currently positioned near the eastern edge of
  the grid." on 2026-08-13; `50ac2fe` put the model in the seat; the tracked wire logs show
  **1 third-person sentence in the 10 hints before and 0 in the 69 after**. The 10-hint
  before-sample is stated as a limit IN the entry, and the third-person rule is labelled a narrow
  mechanical proxy where it prints.
  THREE VACUITIES FOUND IN 08-09'S OWN TESTS, all by probing rather than reading, all fixed:
  (1) `test_every_cited_commit_hash_resolves` was parametrized over three documents and only ONE
  cites a commit, so two of three parametrizations iterated an EMPTY SET and passed having
  checked nothing; (2) `test_no_document_claims_a_league_result`'s disjunct had a TRIVIAL branch
  that `PROMPT_LOG.md` takes, so deleting the disclaimer from all three documents AND every
  mention of the league with it would have passed; (3) the token-cost empty-evidence fixture
  zeroed BOTH totals, so removing the guard failed on `ZeroDivisionError` rather than the
  assertion -- it would have kept passing if anyone had guarded the division instead of the
  evidence. All three probed RED after the fix and reverted.
  SIX MUTATIONS PROVEN TO LAND BEFORE BEING TRUSTED (the odd-quote lesson from 08-07): the FIXED
  refusal -> `pass` (2 failed/12 passed), the empty-spend guard deleted (1 failed, DID NOT RAISE),
  a notebook input repointed at `logs/` (2 failed/3 passed plus the notebook's own in-cell
  assertion), `50ac2fe` -> `dead1ee` (1 failed), both league disclaimers removed (1 failed), and
  a `96.4%` -> `99.9%` tamper asserted in-test. Every one reverted and the suite re-run green.
  WHAT THESE DOCUMENTS DELIBERATELY DO NOT CLAIM: **NO league game has been played** and all three
  say so in their own limits sections; mail is `dry_run` and NOTHING HAS EVER BEEN DELIVERED;
  phase 4 is `human_needed`; phases 7 AND 8 are NOT verified; the games-played VALUE is
  deliberately unset and nothing here sets or infers one; every token figure is n=1 and every
  per-game projection is labelled an EXTRAPOLATION from a game that ended at turn 14 of 35;
  `TOKEN-COST.md`'s S2 is recorded as BLOCKED on a named missing measurement rather than given an
  invented number; and the Phase-4 belief on/off comparison (3 seeds per arm) is deliberately NOT
  plotted, with the reason written into the notebook.
  GATES: **2455 passed / 0 failed** (baseline 2413; +46 new, -4 from de-parametrising two tests
  during the self-audit), coverage **97.44% UNCHANGED** (the new code is in `scripts/`, outside
  the coverage source list, and is measured by tests loaded BY PATH), ruff **0** tree-wide (it
  lints the notebook too -- one SIM300 was found there and the notebook re-executed after the
  fix), line-limit **0** with all nine new `scripts/*.py` ALSO checked explicitly by path,
  local-truth OK (7), no-LLM OK, `check_submission` exit 1 at 69/4/13, `--empty-probe` exit 2,
  `jupyter nbconvert --execute` exit 0 in 4.6s with 3 embedded figures.
  RULE-38 COUNTERS: suite **1927->1927 / 1920->1920 (0/0)**. **NO REAL GAME WAS PLAYED BY 08-09**
  -- it delivers documents, nothing in it needs a game, and advancing the shipped counter to
  demonstrate a delta would be a state change with no deliverable behind it. The +1/+1 contract
  is INHERITED from 08-07/08-08's measurement (1926->1927 / 1919->1920, `game_id`
  `2582a94c8a5ec618`) and was NOT re-measured here; it is recorded as inherited, never claimed as
  measured. `git diff config/` EMPTY -- the counters are gitignored at `.gitignore:90`.
  SELF-CHECK PASSED: 25 of 25 `key-files` paths exist, 7 of 7 commit hashes resolve via
  `git cat-file -e`, 37 of 37 repository paths cited across the three new documents resolve, and
  all 5 published commands run to exit 0.
  NOTHING WAS PUSHED BY THIS AGENT, NO TAG WAS CREATED, NO REMOTE COMMAND OF ANY KIND WAS
  ISSUED.
---

Last session: 2026-08-17T23:59:00+03:00
Stopped at: Completed 08-09 in full -- the four Sec17 research artifacts the repository had
  none of. Seven atomic commits (`32440b4`, `486a01a`, `a8931b7`, `bcce41b`, `32535b7`,
  `112bd6f`, `aac4cf8`). `docs/SENSITIVITY.md`, `docs/TOKEN-COST.md`, `docs/PROMPT_LOG.md` and
  `notebooks/analysis.ipynb` -- the repository's FIRST tracked notebook, executing offline with
  three committed figures. `check_submission.py` 65/8/13 -> **69 PASS / 4 GAP / 13 UNJUDGED**,
  exactly the four rows this plan owns, no other row moving in either direction.
  EVERY PUBLISHED NUMBER IS RENDERED FROM A COMMITTED ARTIFACT and re-rendered by
  `tests/unit/test_research_docs.py` for comparison, so a hand-edited figure fails the suite.
  The sweep varies ONLY parameters `docs/PARAMETERS.md` marks `minimum` (upward) or
  `negotiable`, plus three labelled engineering defaults -- and that is a PARSE of the Status
  column, not a promise. Separable at 95% Wilson: board 11 +35.0pp, horizon 70 -29.0pp,
  swap-as-capture -25.0pp, the fitted vector +18.0pp; search depth and extra barriers move
  nothing separably, and the saturated cop matchup is flagged rather than read as evidence.
  TWO HONEST FINDINGS KEPT RATHER THAN SMOOTHED: the sweep contradicts ENGINEERING-LOG Act
  4.3's 89%/1% pair (measured 32.0%/7.5%, eight arms re-measured, CAUSE NOT ESTABLISHED, the
  shipped decision's direction unchanged), and three vacuities were found in this plan's OWN
  tests by probing -- two parametrizations that iterated an empty set, a disjunct whose trivial
  branch was the one being taken, and a fixture that failed on ZeroDivisionError rather than its
  assertion. All fixed, all probed RED, all reverted.
  Counters: suite 1927->1927 / 1920->1920 (0/0). NO real game was played -- 08-09 delivers
  documents, and the +1/+1 contract is recorded as INHERITED from 08-07/08-08, never claimed as
  measured here. Suite 2455 passed, coverage 97.44% unchanged, ruff 0, line-limit 0. Nothing
  pushed, no tag, no remote command of any kind. **Wave 2 is complete; next is 08-10.**


Last session: 2026-08-17T19:45:00+03:00
Stopped at: Completed 08-07 and 08-08 in full. Four atomic commits (`acc5913`, `072d61d`,
  `5687c39`, `f176923`). The repository's FIRST six rendered mermaid diagrams -- C4 x4, a
  deployment view and the four-phase commit-reveal sequence -- with symmetric peers, rule-2
  process separation and D-76's separate GUI process asserted about the DRAWN GRAPH rather than
  captioned. Plus `docs/QUALITY-25010.md` (eight characteristics, each with its own repo
  evidence, against a repo that held ONE line on 25010), `docs/EXTENSION-POINTS.md` (five real
  seams), `docs/PRD_sdk.md` and `docs/PRD_tunnel.md`. `check_submission.py` 58/15/13 ->
  **65 PASS / 8 GAP / 13 UNJUDGED**, exactly the seven rows these two plans own, no other row
  moving in either direction. New assertions proven RED on the pre-change documents: 16 failed /
  4 passed, then 5 failed / 6 passed. Rendering proven with the REAL renderer out of tree, and
  the two mutations the unit tests use were rejected by it. Six deviations, five of them defects
  in this session's own work found before commit -- including TWO cited script names that do not
  exist, one of them the 08 outline's PREDICTED filename rather than the tree's. Counters: suite
  0/0, one real game +1/+1, `game_id` `2582a94c8a5ec618`, both seats matched=true.
  NOTHING PUSHED BY THIS AGENT -- but `origin/main` moved to `acc5913` SIX MINUTES after that
  commit, with no pushing hook in this repository and `codex.exe` running. Investigate.
Resume file: None -- the tree is clean and both plans are closed. Next is `/gsd:execute-phase 8`
  finishing wave 2 with 08-09 (sensitivity analysis, offline notebook, token-cost analysis,
  prompt log -- the last four GAPs Claude can close), then wave 3's 08-10. Any document 08-09
  writes under `docs/` is subject to the backticked-path rule if it is one of the six
  contract-covered files, and any mermaid it adds must carry an `<!-- diagram: NAME -->` marker
  and pass `scripts/check_diagrams.py`.
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
