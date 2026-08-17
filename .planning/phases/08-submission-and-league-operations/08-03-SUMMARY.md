---
phase: 08-submission-and-league-operations
plan: 03
subsystem: infra
tags: [packaging, gitignore, ci, licence, coverage-report, submission-audit, sec17]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-01's `scripts/check_submission.py` gate and `docs/SUBMISSION-CHECKLIST.md` gap register — the seven rows this plan inherited"
  - phase: 08-submission-and-league-operations
    provides: "08-04's `config/{police,thief}/league.json`, which moved the tracked-config denominator from 26 to 28"
provides:
  - "`__all__` on all 11 packages and `__version__` on the root package, both guarded by tests that derive their expectations from `git ls-files`"
  - "root `graph.json` / `graph.html` genuinely gitignored — CLAUDE.md's own claim now true, and held true by a test that parses that claim"
  - "`version` on all 28 tracked config JSONs, asserted by VALUE against `shared/version.py`, not merely by presence"
  - "CI produces and stores `coverage.xml` + `reports/junit.xml` (§17 automated test reports)"
  - "`CONTRIBUTING.md`, `pyproject.toml` `license`/`authors`, and a `LICENSE` drafted under an explicit PREPARED-NOT-ADOPTED flag"
  - "`docs/RULES.md` rule 48's survival pair corrected to cop-first `5/10`, recorded in a new Corrections section with both citations"
  - "`local_truth_ast.is_package_marker` widened by SHAPE, with eight refusal cases and a leaky-`__init__.py` control"
affects: [08-06, 08-07, 08-10, 08-11, 08-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Parse the claim out of the document that makes it, then hold the tree to it (CLAUDE.md's gitignore sentence; PARAMETERS Table 17; the workflow's run lines)"
    - "Biconditional guards across two files, so a flag cannot be dropped by tidying one of them"
    - "Widen a structural gate by SHAPE, never by filename, and pay for the widening with refusal cases"

key-files:
  created:
    - LICENSE
    - CONTRIBUTING.md
    - tests/unit/test_publication_ignore_rules.py
    - tests/unit/test_package_exports.py
    - tests/unit/test_package_version.py
    - tests/unit/test_package_marker_admission.py
    - tests/unit/test_config_versioning.py
    - tests/unit/test_test_report_artifacts.py
    - tests/unit/test_packaging_metadata.py
    - tests/unit/test_extract_consistency.py
  modified:
    - .gitignore
    - .github/workflows/quality-gate.yml
    - pyproject.toml
    - docs/RULES.md
    - docs/SUBMISSION-CHECKLIST.md
    - scripts/local_truth_ast.py
    - src/pursuit/__init__.py
    - src/pursuit/{gui,network,sdk,security,services,shared}/__init__.py
    - config/{police,thief}/{resolution,role}.json

key-decisions:
  - "The seven import-free packages declare their SUBMODULE INVENTORY rather than a curated re-export — `network/` is 54 mutually-importing modules and a package-level re-export is how a circular import lands before a deadline"
  - "`__version__` is RE-EXPORTED from `shared/version.py`, never re-typed; the repo already carries one version-drift defect (T5-06) and a second literal would be a second one"
  - "`local_truth_ast.is_package_marker` admits a literal `__dunder__` assignment by SHAPE, never by the filename `__init__.py` — a leaky `__init__.py` must still be a violation"
  - "`pyproject.toml` uses `license = { file = \"LICENSE\" }`, not the SPDX string `\"MIT\"`, because the SPDX string would assert an adoption that has not happened"
  - "`docs/RULES.md` yielded to `docs/PARAMETERS.md` on the survival pair because RULES.md's own header says all numeric values live in PARAMETERS.md; the book was NOT re-read and the summary says so"
  - "G1-05/G1-06 and T5-06 were deliberately left GAP — they are 08-06's and 08-11's, even though this plan was editing the files involved"

patterns-established:
  - "Anti-vacuity floor on every derived list: a walk that finds nothing must fail, not agree"
  - "Every probe asserts the mutation LANDED before its verdict is read, and reverts by rewriting the file"
  - "A test's expected value is parsed from the governing document, never copied from the code under test"

# Metrics
duration: 195min
completed: 2026-08-17
---

# Phase 8 Plan 03: Publication Hygiene Summary

**Eight §17 gap rows closed and made machine-checkable — packaging exports and version, the
root graph artifacts genuinely ignored, all 28 config files versioned, CI storing real test
reports, `CONTRIBUTING.md` + packaging metadata, a `LICENSE` visibly flagged as the owner's to
confirm, and rule 48's survival pair corrected against Table 17 with both citations recorded.**

> **No `08-03-PLAN.md` exists.** The phase directory holds only `08-CONTEXT.md` and
> `08-PLAN-OUTLINE.md`, so this plan was executed from the outline's §9 `08-03` entry plus the
> seven rows `docs/SUBMISSION-CHECKLIST.md` assigns to 08-03. Every finding was **re-derived at
> HEAD** rather than inherited.

## Performance

- **Started:** 2026-08-17T12:19:34Z
- **Tasks:** 7, each committed atomically
- **Files created:** 10 · **Files modified:** 15

## Gate run, against the orchestrator's baseline

| Gate | Baseline (08-04) | This plan | Verdict |
|---|---|---|---|
| `uv run pytest --cov` | 2293 passed / 0 failed | **2331 passed / 0 failed** | +38, exactly this plan's new tests (3+5+4+5+4+7+6+4) |
| Coverage | 97.43% | **97.44%** | floor 85% |
| `uv run ruff check .` | 0 | **0** | — |
| `sh scripts/check_line_limit.sh` | 0 violations | **0 violations**, exit 0 | all 9 new/touched files also checked **by path** |
| `check_local_truth.py` | OK, 7 modules | **OK, 7 modules**, exit 0 | unchanged after `gui/__init__.py` gained `__all__` |
| `check_no_llm_in_strategy.py` | OK | **OK**, exit 0 | — |
| `check_submission.py` | exit 1 · 41/32/13 | **exit 1 · 49 PASS / 24 GAP / 13 UNJUDGED** | 8 rows closed |
| `uv sync` / `uv lock --check` | — | exit 0 / exit 0 | after the `pyproject.toml` metadata edit |

### Rule-38 counters — all four numbers

| Run | police | thief | Delta |
|---|---|---|---|
| Full `uv run pytest --cov` | 1923 → 1923 | 1916 → 1916 | **0 / 0** |
| One real `scripts/dev_launch.py` game | 1923 → 1924 | 1916 → 1917 | **+1 / +1** |

The real game: `game_id` `117041920a949129`, exit 0, all four rule-50 artifacts written on
both seats, `audit_verdict {"matched": true, "turn": 5}`, **zero** `technical_win`, **zero**
`watchdog_incident`, and the `result_` artifact recording `commit_hash ae281de…` — this plan's
own HEAD, so rule 53's wiring is intact after the config edit. **Nothing sets the games-played
VALUE**; the counter moved by exactly the number of games actually played.

## The GAP movement, row by row

**32 → 24. Eight rows, and exactly the eight this plan owned.** No other row changed verdict in
either direction — the counter-control for a hygiene plan.

| Row | Group | What changed |
|---|---|---|
| **G4-06** | 4 | `git check-ignore -q graph.json` **1 → 0** |
| **G4-07** | 4 | `git check-ignore -q graph.html` **1 → 0** |
| **G4-21** | 4 | tracked config JSONs carrying `version`: **24/28 → 28/28** |
| **G2-05** | 2 | packages declaring `__all__`: **4/11 → 11/11** |
| **G2-06** | 2 | `__init__.py` files declaring `__version__`: **0 → 1** |
| **G3-03** | 3 | CI emits `--cov-report=xml` + `--junitxml` and uploads both |
| **G6-03** | 6 | `LICENSE` exists; `pyproject.toml` declares `license` + `authors` |
| **G1-15** | 1 | `RULES.md` rule 48 survival pair now agrees with PARAMETERS Table 17 |

Group totals: 1 → 13/15/0 · 2 → **7/0**/3 · 3 → **4/0**/3 · 4 → **15/0**/0 · 5 → 1/4/0 ·
6 → 2/4/2 · T5 → 7/1/5.

**Two rows deliberately NOT closed, and recorded as such.** G1-05/G1-06 judge the *README's*
headings, not the existence of `CONTRIBUTING.md` and `LICENSE` — closing them means editing a
README whose opening paragraph is still factually wrong about the shipped strategy, which is
08-06's rewrite. T5-06 (`version.py` `1.00` vs `pyproject.toml` `1.00.0`) stays 08-11's,
because D-79 derives the tag name from the reconciled value — even though this plan had
`pyproject.toml` open.

## Task Commits

1. **Root graph artifacts genuinely ignored** — `6c44e5c` (fix)
2. **§14 packaging: `__all__` ×11, `__version__`, marker admission** — `589b094` (feat)
3. **Version the four unversioned config files** — `fbad2a7` (chore)
4. **CI produces and stores the automated test reports** — `2fd8a2a` (feat)
5. **`CONTRIBUTING.md`, packaging metadata, flagged `LICENSE`** — `43da1ea` (docs)
6. **Rule 48's survival pair corrected, with both citations** — `d257b8d` (docs)
7. **Gap register re-measured, 32 → 24, explained row by row** — `ae281de` (docs)

## The two corrections the orchestrator named

### 1. `graph.json` / `graph.html` were not ignored, though CLAUDE.md said they were

Re-derived at HEAD before the fix: `git check-ignore -q graph.json` → **exit 1**, same for
`graph.html`. `.gitignore` covered `graphify-out/` and the two `.planning/graphs/` copies only,
while `CLAUDE.md:178` states in as many words that both are "gitignored build artifacts".

Fixed with **anchored** rules `/graph.json` and `/graph.html`, so they cover exactly the two
root artifacts `graphify update .` drops and cannot hide a `graph.json` some future
subdirectory legitimately tracks. Verified three ways: `check-ignore` exit 0; real files
created at the root and absent from `git status --porcelain`; `git ls-files -i -c` empty, so
nothing tracked became ignored. **Neither file was committed.**

`tests/unit/test_publication_ignore_rules.py` **parses the claim out of CLAUDE.md** — bounded
by `;` and the phrase itself, floored at three names — and holds git to it, with a
discrimination control over three certainly-tracked files. The claim and the ignore file can
no longer disagree silently.

### 2. `RULES.md:97` wrote survival `10/5` against Table 17's cop 5 / thief 10

Corrected to `5/10`. **No fixed value changed**: both numbers were already on the line and
still are. Only the *order* was wrong — and the order is what says whose number it is. Under
the old ordering rule 48 awarded the **cop** 10 points for failing to capture and the
**thief** 5 for surviving, inverting Table 17's incentive on a page a grader reads.

Recorded rather than re-derived: `docs/RULES.md` gains a **"Corrections to this extract"**
section whose entry **C1** carries

- **citation 1** — `PARAMETERS.md` Table 17 rows 3–4, `[survival score – cop]` **5** and
  `[survival score – thief]` **10**, both **fixed**;
- **citation 2** — rule 48's own *capture* pair `20/5`, which is cop-first against Table 17
  rows 1–2, so its survival pair must be cop-first too;

and states the honest limit: **the book itself was not re-read.** `police_thief_p2p.pdf` is
untracked and in Hebrew, and CLAUDE.md's instruction is to work from the extracts and
*surface* a contradiction. This extract yielded because its own header says it must — *"All
numeric values referenced here live in PARAMETERS.md"* — and a role-labelled fixed table
outranks an unlabelled compression of it. If the book's Appendix F is ever checked and
disagrees, both documents move together and C1 is superseded, never deleted.

## The licence — prepared, and visibly not adopted

`LICENSE` is MIT, the conventional academic default, **under a `PREPARED, NOT ADOPTED` block**
naming the three things the owner must confirm: the licence choice, the copyright-holder line,
and the year. `pyproject.toml` declares `license = { file = "LICENSE" }` rather than the SPDX
string `"MIT"`, because the SPDX string would be an assertion that MIT *is* the licence.

The flag is **registered, not merely written**: `docs/SUBMISSION-CHECKLIST.md` carries a
`**LICENCE STATUS:** AWAITING_OWNER_CONFIRMATION` field plus a section stating that **08-12
must not create a public repository until the owner confirms**, in the same class as the repo
URLs (OQ8-6) and the games-played value (OQ8-2). `tests/unit/test_packaging_metadata.py` binds
the two files as a **biconditional** — caveat present ⇔ field pending, caveat deleted ⇔ field
confirmed — so the flag cannot be dropped by tidying either file. Both directions were probed
and both failed correctly.

It is trivially reversible today because **nothing has been pushed.**

## Probes — thirteen, each asserting the mutation landed first

| # | Probe | Result |
|---|---|---|
| 1 | remove `/graph.json` + `/graph.html` | `check-ignore` exit 1; 1 failure naming both |
| 2 | drop `"turn_buffer"` from `network.__all__` | 1 failure, the missing name printed |
| 3 | plant a **tracked** `src/pursuit/sdk/probe_module.py` | 1 failure, "missing" |
| 4 | `__version__ = "1.00"` instead of the re-export | 1 failure, the literal quoted |
| 5 | `_is_literal_dunder` forced `True` | 2 failures, incl. the leaky `__init__.py` |
| 6 | strip `version` from `config/thief/role.json` | 2 failures |
| 7 | drift `config/police/resolution.json` to `9.99` | 1 failure |
| 8 | delete the report flags from the workflow `run:` line | **first attempt: 0 failures — see below** |
| 8b | same probe against the corrected test | 2 failures |
| 9 | delete `LICENSE`'s caveat while the register said pending | 1 failure |
| 10 | flip the register to confirmed while the caveat stood | 1 failure |
| 11 | put rule 48's survival pair back as `10/5` | 1 failure, parsed `('20','5','10','5')` |

Every probe was reverted **by rewriting the file**, never with `git checkout --`, which
restores from the index.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `is_package_marker` correctly started judging `gui/__init__.py`**
- **Found during:** Task 2. Adding `__all__` turned a docstring-only file into a module with a
  statement, and `test_gui_structural.py` failed with `__init__.py binds no pursuit name at all`.
- **Fix:** widened `local_truth_ast.is_package_marker` **by shape** — one `__dunder__` target
  whose value `ast.literal_eval` accepts. Special-casing the filename `__init__.py` was the
  cheap alternative and was rejected: it would blind the rules 8–9 firewall to a real
  `__init__.py` that imported `GameState`.
- **Paid for:** `tests/unit/test_package_marker_admission.py` — 6 admitted shapes, **8 refused**
  (a Name-valued dunder, a Call-valued one, an Attribute-valued one, a non-dunder assignment,
  a single-underscore one, a real import, a function, and a dunder followed by an import), a
  leaky `__init__.py` that must still be reported, and the `EMPTY_SCAN` property re-proven.
- **Committed in:** `589b094`

**2. [Rule 1 — Bug] `docs/SUBMISSION-CHECKLIST.md` prose contradicted its own status check**
- **Found during:** Task 5. The first biconditional grepped the register for two marker
  strings; the register necessarily *quotes* both while explaining them, so it read as
  "confirmed" while saying "pending".
- **Fix:** one anchored `**LICENCE STATUS:**` field, parsed by regex; the prose may say
  anything.
- **Committed in:** `43da1ea`

### Self-inflicted defects this plan found in its **own** work

**A. The workflow test measured its own documentation.** Probe 8 deleted `--cov-report=xml`
and `--junitxml` from the `run:` line and **all 7 tests still passed** — because the
explanatory comment block above the job quotes those flags, and the test grepped the whole
file. Fixed by reading only non-comment lines, with a control proving the stripper strips; the
re-probe produced 2 failures. *A test that greps a file containing its own explanation is
measuring the explanation.*

**B. A Windows separator bug reported an ignored file as trackable.**
`str(Path("reports/junit.xml"))` is `reports\junit.xml` here, so comparing it against the
forward-slash name failed even though git had said "ignored". Fixed with `PurePosixPath` and
separator normalisation. Same class as the CRLF note `gitignore_probe.git_ignored` already
carries on its stdin side — and it failed *loudly*, which is the safe direction.

**C. A probe's own landing check was wrong.** Probe 1 printed `MUTATION LANDED: False` because
`"/graph.json" not in text` also matches inside `.planning/graphs/graph.json`. The authoritative
landing evidence was `git check-ignore` exit 1, which is what was used.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug) + 3 self-inflicted defects found and
closed before commit.
**Impact:** no scope creep. The gate widening is the only change to an existing guard, it is
narrower than a filename exemption, and it is paid for with 8 refusal cases.

## Issues Encountered

- A heredoc containing em-dashes and apostrophes failed under Git Bash; the checklist edit was
  applied from a scratchpad script instead. No content was lost.
- `dev_launch.py` prints a Windows `WinError 995` / `CancelledError` at uvicorn teardown. Known
  shutdown noise (phase-5 deferred item #1's neighbourhood); the process exit code is **0**
  and all four artifacts were written.

## Next Phase Readiness

- **08-06** inherits G1-01…G1-07, G1-03b, G1-08, G1-09. `CONTRIBUTING.md` and `LICENSE` now
  exist, so the README's *Contributing* and *License* sections have real targets to link to.
- **08-11** still owns **T5-06**: `version.py` `1.00` vs `pyproject.toml` `1.00.0`. D-79
  derives the tag name from the reconciled value.
- **08-12** must not publish until the owner confirms the licence — registered under
  `**LICENCE STATUS:** AWAITING_OWNER_CONFIRMATION` and guarded by a biconditional test.
- Any plan adding a module under `src/pursuit/` must now add it to that package's `__all__`,
  or `tests/unit/test_package_exports.py` fails. That is the guard working.

**NOTHING WAS PUSHED. NO TAG WAS CREATED. NO REMOTE WAS TOUCHED.**

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*

## Self-Check: PASSED

- 10 created paths verified **present AND tracked by git AND not gitignored**.
- 7 task commits verified reachable: `6c44e5c` `589b094` `fbad2a7` `2fd8a2a` `43da1ea`
  `d257b8d` `ae281de`.
- Every number above was read from a command run in this session; the GAP counts come from
  `check_submission.py` output, not from the register's prose.
