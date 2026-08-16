---
phase: 05-cloud-exposure-and-tunneling
plan: "08"
subsystem: infra
tags: [gate-5, remote-round, ngrok, runbook, rule-38, evidence-discipline, knowledge-graph]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "the four code fixes the round tested live (05-04 verdict honesty + linger, 05-05 the negotiated game id, 05-06 the hint channel, 05-07 the honest llm_name), plus 05-09..05-11's crash containment and the tunnel watch"
  - phase: 06-security-and-cryptography
    provides: "the commit-reveal exchange and Step-0 declarations that the remote round exercised over a real network"
provides:
  - "REMOTE-ROUND-RUNBOOK.md amended into a durable league-day procedure: both machines' consoles and both ngrok agent logs in the evidence list, a UTC-clock note, a pre-flight block, and an expected-difference table with the live signatures of the 05-04/05-05/05-06 fixes"
  - "GATE-5-MEASUREMENT.md internally consistent: criterion 2's own section no longer reads PENDING under a PASS header"
  - "the knowledge graph refreshed against the phase's shipped code (7411 nodes / 13317 edges / 470 communities)"
  - "two new deferred items: #8 the stale ROADMAP progress table, #9 the mechanism behind the belief-budget test failure"
affects: [05-12-g9-g7, 05-13-g6, phase-08-submission-league-games]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A gate record is append-only for its attempt narratives and correctable for its status lines -- the two are different kinds of statement"
    - "An operator runbook records what each failed attempt cost, not just the happy path"

key-files:
  created:
    - .planning/phases/05-cloud-exposure-and-tunneling/05-08-SUMMARY.md
  modified:
    - docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md
    - docs/phases/phase-5/GATE-5-MEASUREMENT.md
    - docs/phases/phase-5/TODO.md
    - .planning/ROADMAP.md
    - .planning/graphs/GRAPH_REPORT.md
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
    - .planning/STATE.md

key-decisions:
  - "Task 2 was NOT re-run: the human remote round closed on 2026-08-16 at attempt 4 (games b22361aa93ccf310 + d265603c116a9f99), so re-running it would have burned a second operator's time to re-prove a closed criterion -- recorded as complete-on-arrival with its evidence paths instead"
  - "The runbook was amended anyway, after the gate closed: it is a durable operator document reused on league day, and attempts 2-4 had taught more than the plan (written before them) anticipated"
  - "Attempts 1-3's 'criterion NOT yet closed' verdicts are TRUE STATEMENTS ABOUT THOSE ATTEMPTS and were left byte-identical; only the criterion's own status line -- which read PENDING under a PASS header -- was corrected, with a dated note saying what it used to read"
  - "The phase-5 TODO row for 05-08 now states plainly that it was ticked at verify-work on the ROUND alone while the runbook half it also names had not been written (rule 38 applies to our own trackers, not only to capture declarations)"
  - "The belief-budget test failure was logged, never fixed: the only quick repair is to move a threshold so a red test goes green, and the measurement is what is wrong (15.625 ms Windows tick quantization against a 3.571 ms mean)"
  - "GRAPH_REPORT.md is a community/hub summary and names no individual module, so the plan's 'the three new modules appear in GRAPH_REPORT.md' check was answered against graph.json instead -- agent_teardown 32 nodes, game_identity 28, turn_hint_buffer 21"

patterns-established:
  - "Secret scans over evidence handle UTF-16: PowerShell Tee-Object writes UTF-16, which a naive grep silently fails to match -- decode first, then search, and triage every hit as placeholder-vs-real without printing a value"
  - "A tracker correction carries the sentence that says what it used to say, so the correction is itself auditable"

# Metrics
duration: 35min
completed: 2026-08-16
---

# Phase 5 Plan 08: Remote Round — Runbook, Gate Record, and the PENDING/PASS Contradiction Summary

**The remote round was already won (attempt 4, 2026-08-16), so this plan did the half that had not landed: turned the runbook into a league-day document that records what all four attempts cost, and removed a gate record that stated `PASS` in its header and `PENDING` in the section beneath it.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-16T14:45Z (approx — first file read)
- **Completed:** 2026-08-16T15:25Z
- **Tasks:** 3 (2 executed, 1 already satisfied on arrival)
- **Files modified:** 6 (+1 created)

## Accomplishments

- **The runbook now collects the evidence attempt 1 wished it had** — and attempts 2, 3 and 4 as well. Before this plan `REMOTE-ROUND-RUNBOOK.md` contained **zero** occurrences of "ngrok agent log" and no clock instruction; it now has both, plus a pre-flight block, an expected-difference table, and a pre-`git add` secret grep.
- **A gate record that contradicted itself was corrected.** `GATE-5-MEASUREMENT.md`'s header said criterion 2 **PASS**, and the "Criterion 2" section 100 lines below opened **`Status: PENDING.`** Both cannot be true. The status line is now PASS with the attempt-4 anchor and a dated note recording what it used to read.
- **Task 2 was recognised as complete-on-arrival, not re-run.** The criterion closed at attempt 4 with agreeing verdicts on both machines; re-running would have cost a second operator's evening to re-prove a closed criterion.
- **The knowledge graph knows this phase's code**: 7411 nodes / 13317 edges / 470 communities, built from `85a71710` (was 7287 / 13159 / 439).
- **Two findings logged rather than smoothed:** the ROADMAP progress table is stale for three other phases (#8), and the belief-budget test's failure mechanism is now written down (#9).

## Task Commits

1. **Task 1: amend the runbook with what attempts 1–4 taught** — `85a7171` (docs)
2. **Task 2: run the round** — **no commit; already satisfied on arrival** (see below)
3. **Task 3: record the result, fix the contradiction, refresh the graph** — `6d1565d` (docs)

**Plan metadata:** the `docs(05-08): complete the remote-round plan` commit that carries this file (a hash cannot be embedded in the object that defines it).

## Task 2 — already satisfied, and why it was not re-run

The plan was written expecting to *drive* the round. By the time it executed, the round had already happened and closed the criterion. Recording it rather than repeating it:

| Fact | Value |
|---|---|
| Attempt | 4, 2026-08-16 ≈13:29Z |
| Games | `b22361aa93ccf310` (13:29:27) and `d265603c116a9f99` (13:31:52) |
| Machines / networks | A police, Windows 12-core, **phone hotspot** ↔ B thief, Windows 11 20-core, **wired ethernet** |
| Both sides' outcome | `capture` on both machines, both games |
| Both sides' audit | `audit_verdict matched=true`, self and peer, all six turns |
| Shared UID | one stem per game across both machines' log, ledger and declarations |
| LLM | live `claude-haiku-4-5` declared and billed on **both** sides (B's `language_turn` carries real `token_spend`) |
| Cross-checks | 26/26 per game, re-derived independently over the retained files |
| Evidence | `docs/phases/phase-5/remote-round-2026-08-16-attempt4/` (both machines) |
| Narrative | `GATE-5-MEASUREMENT.md` → Attempt 4 · commit `bcc04bf` |

Two limits that round already states about itself, repeated here so this summary cannot be read as claiming more: machine B's console was never Tee'd, and the 05-11 tunnel-repair path **never fired** (no drop occurred), so attempt 4 proves a healthy tunnel completes a round — not that a dropped one is repaired.

## Files Created/Modified

- `docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md` — +134 / −2 lines, of which the only deletion is the digest table's commit reference. Adds: a status header (criterion closed, file retained for league day); a pre-flight block of five recordings (commit hash from both machines, both UTC clocks, both consoles redirected, the ngrok agent log, and a deliberate live-vs-template `llm_name` decision) plus the `ERR_NGROK_334` leftover-agent trap; an expected-difference table mapping each attempt-1 symptom to its fix and its live signature; "do not `Ctrl-C` at `game_over`" with the measured linger cost; §5 evidence items 5–7 (both consoles, both ngrok agent logs with two named ways to obtain one, the recorded clocks and any stray session logs); and a secret-grep instruction before `git add`.
- `docs/phases/phase-5/GATE-5-MEASUREMENT.md` — criterion 2's status line corrected `PENDING` → `PASS` with a dated note; "What closes this section" now names the artifacts that satisfy it and records the retrospective runbook amendment. **Three deletions in the whole diff**, none inside an attempt narrative.
- `docs/phases/phase-5/TODO.md` — row 05-08's definition-of-done now separates the round half (closed at attempt 4) from the runbook half (landed at `85a7171`), and says the row was first ticked on the round alone.
- `.planning/ROADMAP.md` — row 05-08 extended; the progress table's Phase-5 row corrected from `4/8 · criterion 2 PENDING` to `11/15 · GATE-5 MET`. The two §10.4 criteria themselves were not touched.
- `.planning/graphs/GRAPH_REPORT.md` — refreshed (249 insertions / 195 deletions).
- `.planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md` — items #8 and #9 added.

## Verification — the plan's own 6-item block

| # | Check | Result |
|---|---|---|
| 1 | `uv run ruff check .` | **`All checks passed!`** — 0 violations |
| 2 | `uv run pytest tests/ --cov` | **1373 passed, 1 failed, 96.54% coverage** — see below |
| 3 | `bash scripts/check_line_limit.sh` | **exit 0** |
| 4 | `uv run python scripts/check_no_llm_in_strategy.py` | **`OK: no forbidden imports under …/src/pursuit/strategy.`**, exit 0 |
| 5 | Secret discipline over the retained evidence | **0 credential values leaked** — detail below |
| 6 | `git ls-files docs/phases/phase-5/remote-round-2026-08-13/` | **all 9 attempt-1 files still tracked**, unchanged |

### Item 2 — the one failure, stated plainly

The plan asked for "all pass" and for the count to equal 05-07's closing figure. Neither is literally met, and both deserve the honest version:

- **Count/coverage.** 05-07's figure (1327 / 96.37%) is stale — 05-09 and 05-10 landed 47 more tests after this plan was written. The right comparison is verify-work's `1374 passed / 96.54%`, and this run collected exactly **1374 tests at exactly 96.54%**. **Zero drift.**
- **The failure.** `test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget` failed in **both** full-suite runs (137 s and 142 s) and **passed alone in 0.21 s**:

  ```
  E   AssertionError: assert 62.5 < 50
  E    +  where 62.5 = max([0.0, 0.0, 0.0, 0.0, 15.625, 0.0, ...])
  belief-enabled per-turn decision CPU time over 35 turns -- cop: max=15.625ms mean=2.232ms;
  thief: max=62.500ms mean=3.571ms (budget: cop=50ms, thief=50ms)
  ```

  Every sample is a multiple of **15.625 ms** — Windows' thread-CPU accounting tick. The decision path is fast (**mean 3.571 ms** against 50 ms); one decision straddling four ticks *reads* as 62.5 ms and `max()` over 35 turns finds it under load. Commit `330e450` re-priced this gate in CPU time to kill exactly this flake and did not succeed; the residual is measurement resolution, not algorithm speed. **Pre-existing and untouched by this plan, which changes no source.** Logged as deferred item **#9** with the two honest repairs — and explicitly *not* fixed, because the quick fix is to move a threshold until a red test goes green.

### Item 5 — secret discipline, exactly what was grepped and found

Two scans, neither of which printed a value:

1. **Evidence + consoles** — all 49 files under `docs/phases/phase-5/` (all four `remote-round-*` directories, both console captures) searched for the literal values of `ANTHROPIC_API_KEY`, `NGROK_AUTHTOKEN`, `PURSUIT_TUNNEL_SECRET` and `PURSUIT_NGROK_DOMAIN` taken from this machine's `.env`, plus shape patterns (`sk-ant-…`, an ngrok-token shape, `VAR=<value>` assignments, `X-Pursuit-Secret: <value>`). **UTF-16 was decoded first** — attempt 4's console is UTF-16 (PowerShell `Tee-Object`), and a naive `grep` matches nothing in it.
2. **Whole repo** — the three credential values against **all 675 git-tracked files**: **`RESULT: 0 credential values found in tracked files`**. `.env` is untracked and ignored (`.gitignore:11`).

Seven pattern hits were raised and every one triaged to a non-secret:

| Hit | Where | Verdict |
|---|---|---|
| `PURSUIT_TUNNEL_SECRET=<v>` ×4 | `GATE-5-MEASUREMENT.md` | placeholders: `NGROK_AUTHTOKEN=<token>`, `PURSUIT_TUNNEL_SECRET=<shared-secret>` |
| `PURSUIT_TUNNEL_SECRET=<v>` ×4 | `REMOTE-ROUND-RUNBOOK.md` | placeholders: `= "<A's …`, `= "<the …`, `= "<key …` |
| `PURSUIT_TUNNEL_SECRET=<v>` ×2 | `consoleA_attempt4.txt` | the exchange block printing the **variable name** followed by a `=====` rule — the env var NAME, never its value, exactly as designed |
| `PURSUIT_NGROK_DOMAIN` value ×4 | measurement doc, smoke evidence, both consoles | the **public reserved domain**. It is in `.env` because the code reads it from the environment, but it is an endpoint address handed to the opponent by design, not a credential. Already published in `gate5_smoke_evidence.json` since 2026-08-09. **Nothing redacted.** |

**Nothing was redacted, because nothing needed to be.** Had a real value been found in an already-committed evidence file, redaction alone would not have been the fix — the value would have had to be rotated, since it is in git history.

## Deviations from Plan

### 1. [Rule 3 — Blocking] Task 2's checkpoint was not entered: the round had already closed

- **Found during:** Task 2
- **Issue:** The plan's blocking `checkpoint:human-verify` asks a human to run the remote round. That round ran on 2026-08-16 (attempt 4) and closed criterion 2 before this plan executed. Pausing would have requested a second operator, a second network and an evening to re-prove a criterion that already carries agreeing verdicts on both machines.
- **Fix:** Recorded Task 2 as complete-on-arrival with its full evidence table (above), and executed Tasks 1 and 3 against the *four* attempts that exist rather than the two the plan anticipated.
- **Verification:** `docs/phases/phase-5/remote-round-2026-08-16-attempt4/` is committed with both machines' halves; `GATE-5-MEASUREMENT.md` → Attempt 4; commit `bcc04bf`.

### 2. [Rule 1 — Bug] The gate record stated PASS and PENDING for the same criterion

- **Found during:** Task 3
- **Issue:** `GATE-5-MEASUREMENT.md` header: "Criterion 2 **PASS** — closed 2026-08-16 by attempt 4" and, twenty lines later, "Nothing above reads PENDING". The "## Criterion 2" section opened `**Status: PENDING.**`. A record that says both is precisely the failure mode rule 38 exists to prevent.
- **Fix:** Status line → PASS with the attempt-4 anchor, plus a parenthetical recording what it previously read and when it was corrected. The per-attempt narratives were **not** touched: attempts 1–3 each state "criterion NOT yet closed", which is true of those attempts.
- **Verification:** `git diff -U0` on the file shows **three** deleted lines total — the status line, the sentence that named it, and the "What closes this section" line — none inside an attempt narrative. `grep -n PENDING` now returns only the header's discipline statement, the new dated note, and attempts 1's and 2's own verdicts.
- **Committed in:** `6d1565d`

### 3. [Rule 2 — Missing Critical] The phase TODO claimed a runbook amendment that did not exist

- **Found during:** Task 3
- **Issue:** Row 05-08 was ticked ☑ at verify-work, and its own text names "runbook amended with attempt-1's missing evidence (machine B console, ngrok agent log, clock skew)". The runbook contained none of that until Task 1 of this plan. A tick pointing at work that had not happened is the same honesty defect as a false gate status, one level down.
- **Fix:** The row's definition-of-done now separates the two halves and states that the tick was earned by the round alone, with the runbook half landing at `85a7171`.
- **Verification:** `grep -c "ngrok agent log" REMOTE-ROUND-RUNBOOK.md` returned **0** before Task 1 and **3** after.
- **Committed in:** `6d1565d`

### 4. [Rule 1 — Bug] The ROADMAP progress table still read "criterion 2 PENDING"

- **Found during:** Task 3
- **Issue:** `4/8 · In Progress (GATE-5 criterion 1 PASS; criterion 2 PENDING — …then the human remote round attempt 2)` in the summary table, while the per-phase section above it says GATE-5 MET.
- **Fix:** Corrected to `11/15 · GATE-5 MET 2026-08-16 …; 05-12..05-15 planned and pending execution`. The §10.4 criteria quoted verbatim from the book were not touched.
- **Committed in:** `6d1565d`

### 5. [Out of scope — logged, not fixed] Two findings pushed to `deferred-items.md`

- **#8:** the same ROADMAP table is stale for other phases — Phase 3 reads `0/5 Not started` while its own plan list is fully `[x]` (an internal contradiction), Phase 2 under-reports shipped work, Phase 6 says "verify-work pending" though it ran 2026-08-09. Only Phase 5's row was this plan's business.
- **#9:** the belief-budget test failure mechanism (above).

---

**Total deviations:** 4 auto-fixed (2 bug, 1 missing-critical, 1 blocking) + 2 logged out of scope.
**Impact on plan:** No scope creep. Three of the four are the same defect class the plan itself exists to police — a tracker asserting something the evidence does not support — found in the trackers rather than in the round.

## Issues Encountered

- **`GRAPH_REPORT.md` cannot satisfy the plan's own graph check.** The plan asks that "the three new modules appear in `GRAPH_REPORT.md`". They do not, and cannot: the report is a corpus/community/hub summary (1907 lines of community links and freshness metadata) that names no individual module. Answered against `graph.json` instead, which is the artifact that holds the nodes: **`agent_teardown` 32 nodes, `game_identity` 28, `turn_hint_buffer` 21** (also `deadline_status` 5, `audit_shape` 6). Report freshness now reads `Built from commit: 85a71710`.
- **`graph.html` was skipped again** — 7411 nodes against the tool's 5000-node visualisation limit, the same behaviour recorded at 04-12/05-03/06-96. `git status` before the Task-3 commit listed exactly five modified files; neither `graph.json` nor `graph.html` was staged (both gitignored).
- **The suite was run twice** because the first run's output was piped through `tail` and the failure's assertion text was lost. The second run reproduced it identically (1373/1/96.54%), which is itself the useful result: this is not a rare flake at HEAD but a reproducible full-suite failure.

## User Setup Required

None. No environment variable, service or credential was needed for this plan — the round it records was already run.

## Next Phase Readiness

- **GATE-5 stands, and now says so consistently** in the measurement document, the phase TODO and the roadmap. `/gsd:verify-work 5` has already run for the 05-01..05-11 set.
- **Next:** `/gsd:execute-phase 5` for plans **05-12..05-15** (G6–G10). Two are blocker-class for league day: until 05-12 lands, a malformed peer digest or game id can end our game before move 1.
- **Carried into league day** from this plan's runbook work: both consoles and both ngrok agent logs, both UTC clocks, both commit hashes, and an `llm_name` check before the round is trusted as a live-LLM round.
- **Open, unfixed, and written down:** deferred items #2, #3, #4, #5 (pre-existing) and #8, #9 (new).

## Self-Check: PASSED

Every claim above re-checked against disk and git rather than against this document:

- **Files** — all 7 present: `REMOTE-ROUND-RUNBOOK.md`, `GATE-5-MEASUREMENT.md`, `docs/phases/phase-5/TODO.md`, `.planning/ROADMAP.md`, `.planning/graphs/GRAPH_REPORT.md`, `deferred-items.md`, `05-08-SUMMARY.md`.
- **Commits** — `85a7171`, `6d1565d` (this plan) and `bcc04bf` (attempt 4's evidence, cited in the Task-2 table) all resolve in `git log --all`.
- **Attempt-1 evidence** — 9 files still tracked under `remote-round-2026-08-13/`, byte-unchanged.
- **Graph artifacts** — `git status` at the Task-3 commit listed exactly 5 modified files; `graph.json` and `graph.html` were not staged.
- **Secrets** — 0 credential values across 675 tracked files; `.env` untracked and ignored.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-16*
