---
phase: 08-submission-and-league-operations
plan: 06
subsystem: documentation
tags: [readme, rule-42, segal-2.1, segal-9.4.2, learning-curves, matplotlib, honesty-gate]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-01's scripts/check_submission.py -- the 86-row audit that registers the nine README rows and judges them individually rather than by an existence check"
  - phase: 08-submission-and-league-operations
    provides: "08-03's CONTRIBUTING.md and LICENSE, which G1-05/G1-06's new sections link to, and the PREPARED-NOT-ADOPTED licence discipline this README repeats"
  - phase: 08-submission-and-league-operations
    provides: "08-04's stated-absence marker discipline (shared/absent.py), reused in prose for the screenshots and the rule-49 cross-link"
  - phase: 03-blind-strategy-module-rl-policy
    provides: "the matrix-game mover and the run-2 training artefacts the academic sections describe"
provides:
  - "README.md rebuilt to Sec2.1's seven user-manual items and Sec9.4.2's six academic-report sections"
  - "zero unqualified claims about the withdrawn tabular Q-learning design (3 -> 0)"
  - "scripts/plot_run2_curves.py and two run-2 learning-curve figures drawn from tracked artefacts"
  - "tests/unit/readme_contract_checks.py -- eight derived checks over the README's text, runnable against any revision"
  - "a machine-enforced rule that a README image link resolving to nothing fails the suite, so an absent screenshot cannot become a fake asset"
affects: [08-07, 08-08, 08-09, 08-10, 08-11, 08-12, 07-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "checkers that take TEXT, not a path, so the same function runs against `git show HEAD:README.md` and proves it goes red"
    - "grader-facing absences written as marked slots naming the producing plan, never as placeholders"
key-files:
  created:
    - scripts/plot_run2_curves.py
    - tests/unit/readme_contract_checks.py
    - tests/unit/test_readme_contract.py
    - tests/unit/test_plot_run2_curves.py
    - artifacts/curves/run2_selfplay.png
    - artifacts/curves/run2_evolution.png
  modified:
    - README.md
    - docs/SUBMISSION-CHECKLIST.md
    - docs/phases/phase-8/TODO.md

key-decisions:
  - "The run-1 figures are NOT presented as the project's learning curves. New figures are drawn from artifacts/run2/curve.json and artifacts/run2_es/curve.json, the optimisers of the mechanism that ships."
  - "The two screenshots and the rule-49 cross-link ship as marked-absent SLOTS naming the producing plan, and a test fails on any README image link that resolves to nothing."
  - "No games-played number appears anywhere in the README (rule 38); the value is a human decision still open."
  - "OQ8-8 (README language) is recorded as UNCONFIRMED and English as an assumption -- the extracts carry no Sec9.4.2 language requirement and CLAUDE.md forbids re-deriving from the Hebrew book."
  - "The 08-01 gap findings in docs/SUBMISSION-CHECKLIST.md are retained rather than rewritten; a defect that was found and fixed is evidence."

patterns-established:
  - "Every documented command is executed before it is documented; a repo path quoted in a fenced block that does not exist fails the suite."
  - "Each honesty checker derives its own subject from the tree (shipped mail mode, shipped brain, which verification files exist), so it tracks the repository instead of freezing today's prose."

# Metrics
duration: ~140min
completed: 2026-08-17
---

# Phase 8 Plan 06: The root README Summary

**The README rebuilt as user manual and academic report in one file: three unqualified claims about a withdrawn tabular Q-learning design reduced to zero, Sec2.1's seven items and Sec9.4.2's six sections all present, run-2 learning curves rendered from tracked artefacts, and `check_submission.py` moved 49 PASS / 24 GAP to 58 PASS / 15 GAP -- exactly the nine rows this plan owned.**

## Interruption and resumption — stated plainly

This execution was **terminated mid-flight by a server-side 529 Overloaded**, immediately after the README write and before any verification of it. On resumption the working tree was re-read rather than assumed:

| Work | Status found on disk | What I did |
|---|---|---|
| Task 1 (curves + script + tests) | committed at `26bd9d8` | **Verified, not redone** — `git log` confirmed the commit; the figures and tests were re-run at HEAD |
| `README.md` | modified, uncommitted, 511 lines, all 17 sections present | **Verified coherent, then continued.** Every heading was listed and the file's tail read before a single further edit; the section-body parse was run through the gate's own `_sections()` to confirm nothing was truncated |
| Tasks 3 and 4 | not started | Done after resumption |

The coordinator's report that "one Q-learning mention still remains" was checked rather than acted on: the remaining mention sits on a line reading *"it was **superseded** and withdrawn"*, which is a qualified historical reference and exactly what the gate's `QUALIFIERS` list permits. The gate confirms **0 unqualified mentions**. No work was redone that had already landed, and nothing was assumed to have landed that had not.

## Performance

- **Duration:** ~140 min including the 529 interruption
- **Tasks:** 4, each committed atomically
- **Files created:** 6 · **Files modified:** 3

## Task Commits

1. **Task 1: render the run-2 learning curves** — `26bd9d8` (feat)
2. **Task 2: rebuild the README** — `129fa7f` (docs)
3. **Task 3: the README contract tests** — `a5fc8c5` (test)
4. **Task 4: record the closures in the register and the phase TODO** — `6141b61` (docs)

## The requirement-to-section map

Both standards, mapped explicitly so rows G1-01 … G1-07 can be judged rather than eyeballed.

### Segal §2.1 — the seven user-manual items

| §2.1 item | README section | Gate row | Verdict |
|---|---|---|---|
| installation: prerequisites, step-by-step, env setup, troubleshooting | `## Installation` | G1-01 | **PASS** (40 body lines; carries `prerequisit` and `troubleshoot`) |
| usage: modes, flags, CLI/GUI, typical workflow | `## Usage — running a game` | G1-02 | **PASS** (42 body lines; two flag tables) |
| examples, code samples, screenshots, use-cases | `## Examples and screenshots` | G1-03 | **PASS** (28 body lines) |
| configuration guide | `## Configuration guide` | G1-04 | **PASS** (21 body lines; all eleven config files) |
| contribution guidelines | `## Contributing` | G1-05 | **PASS** (8 body lines; links `CONTRIBUTING.md`) |
| license | `## Licence` | G1-06 | **PASS** (10 body lines; states *prepared, not adopted*) |
| credits | `## Credits and acknowledgements` | G1-07 | **PASS** (17 body lines) |
| *(examples second half)* code sample **and** non-curve screenshot | marked-absent slots | G1-03b | **GAP, deliberately** — 07-10's screenshots do not exist |

### Segal §9.4.2 — the six academic-report sections

| §9.4.2 item | README section |
|---|---|
| 1. the chosen Dec-POMDP model — state, observations, uncertainty | `## The model — a Dec-POMDP` |
| 2. orchestration dilemmas — turn management, network failure, Gatekeeper, Orchestrator | `## Orchestration dilemmas` |
| 3. the chosen strategy — how the decision mechanism works | `## The strategy that ships` |
| 4. learning curves | `## Learning curves` |
| 5. screenshots — live GUI heatmap and replay `Verified OK` | `## Examples and screenshots` (two marked-absent slots) |
| 6. link to the companion repo | `## Companion repository` (stated absence, rule 49) |

Rule 42's other named contents are present too: model description (§Dec-POMDP), **tables** (status, config, flags, troubleshooting, held-out evaluation), **strategy**, and **images** (two run-2 figures).

## The honesty defect, closed

`README.md:7` claimed each agent *"decides moves with a trained tabular **Q-learning** policy (Bayes + BFS fallback)"*. Phase 3 **withdrew** that design as unsound under the book's simultaneous turn order (§5.3.2 p.35) and shipped a matrix-game mover over a learned 15-weight evaluation. Measured movement:

- **unqualified mentions of the superseded mechanism: 3 → 0** (G1-08 GAP → PASS)
- **phase status table: phase 3 no longer "in progress"** against its `passed` verification (G1-09 GAP → PASS)
- roughly 90% of the old file was a report on the withdrawn run; it is now a report on the mechanism that ships, with the withdrawn run retained as history.

**Two further false claims the gate does not judge, found and fixed in the same pass:**

1. The README documented `uv run python training/plot_curves.py`. That file was **deleted with the rest of the run-1 stack in `f3d9847`** — a documented command a reader cannot run. Now covered by a test that fails on any repo path quoted in a fenced block that does not exist.
2. `artifacts/curves/*.png` were presented as *the* learning curves. They are the **withdrawn** run's figures. New figures for the shipped optimiser were rendered (Task 1) and the run-1 figures are retained under an explicit "withdrawn design" label.

## Proof the new assertions fail on the old README

Required, and run explicitly. `git show HEAD:README.md` (146 lines) restored in place, the test file run against it, then restored byte-identical (SHA-256 compared):

```
6 failed, 11 passed in 2.01s
```

Failing: `test_all_seven_segal_21_items_have_a_heading`, `test_all_six_academic_942_sections_have_a_heading`, `test_every_repo_path_in_a_command_block_exists`, `test_the_shipped_mail_mode_is_stated`, `test_no_unverified_phase_reads_as_verified`, `test_the_readme_names_the_brain_the_shipped_config_selects`.

Checker-level, on both revisions:

| Check | OLD README | NEW README |
|---|---|---|
| §2.1's seven items missing | **RED (7)** | green |
| §9.4.2's six sections missing | **RED (4)** | green |
| commands naming absent paths | **RED (1)** — `training/plot_curves.py` | green |
| mail honesty (`dry_run` / PENDING unstated) | **RED (2)** | green |
| unverified phase reads as verified | **RED (2)** — phases 7 and 8 | green |
| shipped brain module unnamed | **RED (1)** — `strategy/valuebrain.py` | green |
| broken relative links | green | green |
| games-played counter leaked | green | green |

**6 of 8 checkers go red on the pre-fix file. The two that do not are reported as guards, not as regressions** — the old README's links all happened to resolve and it never wrote a counter value. They are kept because they defend against *this* plan's own failure modes (a placeholder screenshot; a rule-38 number creeping in), and both are fired deliberately by anti-vacuity controls.

**Every checker has an anti-vacuity control.** `test_the_command_check_fires_on_the_deleted_run_1_plotter`, `test_the_link_check_fires_on_an_absent_image`, `test_the_phase_check_fires_on_a_row_that_omits_the_caveat`, and four more. An empty violation list proves nothing unless the same function is shown to produce a non-empty one.

## What I deliberately did NOT claim

| Temptation | What the README says instead | Evidence |
|---|---|---|
| "reports are emailed to the lecturer" | every shipped `reporting.json` is `dry_run`; **no report has ever been delivered**; the live send is PENDING | `GATE-7-MEASUREMENT.md` criterion 1 |
| "phase 4 complete" | **Executed, not verified** — `human_needed`, live-API confirmation the sole open item | `04-VERIFICATION.md` |
| "phase 7 done" | **Executed, NOT verified** — 11/12 plans, **no `07-VERIFICATION.md` exists** | ROADMAP + the absent file |
| "phase 8 in progress" (silently unverified) | **In progress, not verified** — no `08-VERIFICATION.md`. *This plan's own contract test caught this row and the README was fixed, not the check.* | the check |
| "we have played league games" | **no league game has been played**; the remote rounds are this project's own two seats | `GATE-5-MEASUREMENT.md` |
| a games-played figure | **no number anywhere**, and a test fails if either counter value appears | rule 38 |
| screenshots | two **marked-absent slots** naming the file and the producing plan (07-10) | the absence itself |
| "MIT licensed" | **prepared, not adopted**; all rights reserved until the owner confirms | `LICENSE`'s own block |
| a repo cross-link | **NOT PRESENT** — nothing pushed, no remote, `git tag -l` empty | `league.json`'s four `null`s |
| "OQ8-8 confirmed" | recorded as an **assumption**: no §9.4.2 language requirement exists in the extracts and the book is Hebrew | `docs/SUBMISSION-CHECKLIST.md` |

Understatement was avoided too, with pointers rather than restatements: 2366 passing tests, 97.44% coverage, both §10.4 criteria met for phases 1/2/3/5/6, GATE-5 closed by two rounds across two machines on two networks, and a security model with commit-reveal, `secrets.token_hex(16)` nonces and a mutual end-of-game audit.

## GAP movement

**49 PASS / 24 GAP / 13 UNJUDGED → 58 PASS / 15 GAP / 13 UNJUDGED**, exit 1 both times.

Nine rows closed — G1-01, G1-02, G1-03, G1-04, G1-05, G1-06, G1-07, G1-08, G1-09 — **exactly the nine this plan owns, and no other row moved in either direction.** That symmetry is the counter-control.

**Explained non-movement.** G1-03b (`fenced code blocks: True; images: 2, of which non-curve: 0`) and G5-04 (`tracked images: 5; not a training curve: 0`) stay GAP because 07-10's screenshots do not exist. G5-04's image count rose 3 → 5 from this plan's two curve figures **and the row did not move**, which is the judge working correctly: a learning curve satisfies rule 42 and §9.4.2 item 4, and is not a screenshot.

## Verification

| Gate | Result |
|---|---|
| `uv run pytest --cov` | **2366 passed, 0 failed** (baseline 2342; +7 curve tests, +17 contract tests) |
| coverage | **97.44%** (baseline 97.44%, unchanged — new code is in `scripts/`, outside the coverage source list, and is measured by tests loaded by path) |
| `ruff check .` | 0 violations |
| `check_line_limit.sh` | exit 0 tree-wide; all four new `.py` files also checked **by path** — `plot_run2_curves.py` 104, `test_plot_run2_curves.py` 77, `readme_contract_checks.py` 124, `test_readme_contract.py` 65 code lines, all inside 150 — and the by-path form proven to fire (`MAX_LINES=10` → VIOLATION, exit 1) rather than passing vacuously |
| `check_local_truth.py` | OK, 7 modules |
| `check_no_llm_in_strategy.py` | OK |
| `uv lock --check` | exit 0, 123 packages |
| `check_submission.py` | exit 1 at 58 / 15 / 13 |
| `test_packaging_metadata.py` | passes — the LICENCE biconditional is intact and `**LICENCE STATUS:**` untouched |

**Every documented command was executed before being documented:** `uv sync`; `--check-config` for both roles (output quoted verbatim in the README); `dev_launch.py`; both GUI processes' `--help` and `--once`; the `.jsonl` refusal (**exit 2**, as claimed); `plot_run2_curves.py`; and all seven quality-gate commands.

### Rule-38 counters, all four

| | police | thief | delta |
|---|---|---|---|
| full suite | 1925 → 1925 | 1918 → 1918 | **0 / 0** |
| one real game | 1925 → 1926 | 1918 → 1919 | **+1 / +1** |

Game `47873d48ba712222`, `dev_launch.py` exit 0, **both seats `audit_verdict matched=true`**, zero `technical_win`, zero `watchdog_incident`. `git diff config/` is empty — `config/*/games_played*.json` is gitignored (`.gitignore:90`), so no counter value can be committed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `plot_run2_curves.py` crashed on an out-of-tree `--out-dir`**
- **Found during:** Task 1, by its own test
- **Issue:** `path.relative_to(REPO_ROOT)` raises `ValueError` when `--out-dir` points outside the repository — which is exactly what the test does with `tmp_path`
- **Fix:** a `_display()` helper that falls back to the absolute path
- **Verification:** `test_main_writes_both_figures_and_neither_is_empty` went red then green
- **Committed in:** `26bd9d8`

**2. [Rule 2 - Missing Critical] The plan's stated source for the curves was the wrong run**
- **Found during:** Task 1
- **Issue:** the outline's acceptance says "the curves are the existing `artifacts/curves/*.png` with the generating command recorded". Those are the **withdrawn** run's figures, and the generating command (`training/plot_curves.py`) was deleted in `f3d9847`. Following the acceptance literally would have illustrated the academic report with the training history of a mechanism that is not in the product — the outline's own trap for this plan says so in as many words
- **Fix:** `scripts/plot_run2_curves.py` renders both run-2 optimisers from tracked artefacts; the run-1 figures are retained under an explicit "withdrawn design" label
- **Verification:** the shipped `config/{police,thief}/weights.json` were confirmed **byte-identical** to `artifacts/run2/weights.json`, so the figure labelled "the shipped 15-weight vector" is provably that
- **Committed in:** `26bd9d8`

**3. [Rule 1 - Bug] A fragile gate pass in my own README**
- **Found during:** Task 2, by inspecting the gate's parse rather than its verdict
- **Issue:** `# terminal 1` inside a bash fence is parsed as an H1 by the gate's `_sections()`, which does not track code fences. G1-02 was passing with a body of **exactly 3 lines** — the floor. One more edit and it would have silently dropped below
- **Fix:** the terminal labels moved to end-of-line comments; the section body is now 42 lines and no phantom section exists
- **Verification:** re-ran `_sections()` — `PHANTOM CODE-FENCE SECTIONS: []`
- **Committed in:** `129fa7f`

**4. [Rule 1 - Bug] My own phase-8 status row omitted the caveat**
- **Found during:** Task 3 — the contract test failed on the README I had just written
- **Issue:** the phase-8 row read "In progress" without saying the phase is unverified, while no `08-VERIFICATION.md` exists
- **Fix:** the **README** was corrected to "In progress, not verified", not the check
- **Committed in:** `129fa7f`

**5. [Rule 1 - Bug] An unverified mechanism claim I wrote and then removed**
- **Found during:** Task 2, self-check of the Usage section
- **Issue:** I wrote that "the peer that comes up first retries until the other answers". Grepping for it found only a **durable disk-write** retry (`_DECLARE_RETRIES = 3`), not a peer-reconnect loop. The claim was mine and it was unsupported
- **Fix:** replaced with the verifiable statement that an unreachable peer is a distinct recorded outcome, `HandshakeOutcome.UNREACHABLE`
- **Committed in:** `129fa7f`

**6. [Rule 1 - Bug] A rule attribution I could not support**
- **Found during:** Task 2
- **Issue:** I wrote that the four game artifacts are "required by rule 50". `docs/RULES.md:99` rule 50 lists README, `config/`, PRD, PLAN and TODO — it does **not** name the four JSONs; only `docs/KHALED_PERSONAL_PLAN.md` attributes them there
- **Fix:** re-attributed to `docs/PARAMETERS.md`, which does specify them
- **Committed in:** `129fa7f`

---

**Total deviations:** 6 auto-fixed (4 bugs, 1 missing critical, 1 attribution correction). **Four of the six are defects in this plan's own work, found by its own probes before commit.**
**Impact on plan:** No scope creep. The one addition beyond the outline — the run-2 figures — is what the outline's own trap for this plan required.

## Issues Encountered

- **Terminated by a 529 Overloaded** mid-plan. Handled by re-reading the working tree instead of trusting the interrupted state; see the table at the top. Nothing was redone that had landed and nothing was assumed that had not.
- **OQ8-8 could not be resolved.** The instruction was to confirm against the book whether §9.4.2 mandates Hebrew. `police_thief_p2p.pdf` is in Hebrew and CLAUDE.md's standing rule is to work from the extracts and *surface* a gap rather than re-derive; `SEGAL_GUIDELINES.md`, `RULES.md` and `PROJECT_GUIDE.md` contain no language requirement. Recorded as an open assumption in `docs/SUBMISSION-CHECKLIST.md`, not silently resolved.

## User Setup Required

None. But three grader-facing items remain a **human's**, and the README names all three rather than filling them:

1. **07-10** — the two screenshots (live GUI heatmap, replay `Verified OK`) and the one live mail send.
2. **OQ8-5** — confirm the licence, the copyright-holder line and the year. Until then the README states all rights reserved.
3. **OQ8-2 / 08-12** — the games-played value and the two repo URLs.

## Next Phase Readiness

- 08-07, 08-08 and 08-09 are unblocked and share no files with this plan.
- **08-07 inherits a usable seam:** the README's Documentation map links `docs/ARCHITECTURE.md`-shaped content that does not exist yet — it does **not** link the file, so no broken link ships. When 08-07 creates it, the map should gain the row.
- **08-11 should re-run `check_submission.py`** and expect 15 GAP, not 24.
- **07-10, when it runs, need only drop the two PNGs at the paths the README already names** and replace the two slot rows; `test_readme_contract.py` will then require both files to exist.

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*

## Self-Check: PASSED

- **9 paths** verified **present AND tracked AND not gitignored** — the four new `.py` files, both new PNGs, and the three modified documents.
- **4 commits** verified reachable from `HEAD`: `26bd9d8`, `129fa7f`, `a5fc8c5`, `6141b61`.
- **Two numbers CORRECTED rather than left as written:** the code-line counts for `test_plot_run2_curves.py` (67 → **77**) and `readme_contract_checks.py` (87 → **124**) were stale, taken before the `_display()` fix and the not-gitignored assertion were added. Re-measured with `check_line_limit.sh`'s own awk.
- **Nothing pushed, no tag created, no remote touched.**
