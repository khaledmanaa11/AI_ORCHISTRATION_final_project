---
phase: 08-submission-and-league-operations
plan: 01
subsystem: testing
tags: [audit-gate, segal-section-17, table-5, exit-contract, mutation-probes, anti-vacuity]

requires:
  - phase: 07-reporting-and-visualization-shell
    provides: "`scripts/measure_gate7.py` + `gate7_report.GateExit` -- the 0/1/2 exit contract this gate inherits, and the `gate7_*.py` split-by-hand pattern for files that escape both the 150-line gate and coverage"
  - phase: 03-blind-strategy-module-rl-policy
    provides: "the SUPERSEDED banner on `docs/PRD_rl_strategy.md`, which the README honesty row derives its search terms from"
provides:
  - "`scripts/check_submission.py` + 12 siblings -- the Sec17 + Table-5 audit as a runnable gate, 86 rows, exit 0/1/2"
  - "`docs/SUBMISSION-CHECKLIST.md` -- the gap register, 32 GAPs each with the exact path its fix lands in and the plan that owns it"
  - "`docs/mechanism-prd-map.json` -- the Sec2.3 coverage register the package walk is answered from"
  - "`docs/credential-scan-allowlist.json` -- per-path, per-reason exemptions for the generic credential shape that cannot suppress a provider key and cannot go stale"
  - "`docs/phases/phase-8/submission_audit_evidence.json` -- the full 86-row evidence JSON"
affects: [08-03, 08-04, 08-06, 08-07, 08-08, 08-09, 08-10, 08-11]

tech-stack:
  added: []
  patterns:
    - "Three-verdict audit rows: PASS / GAP / UNJUDGED, where UNJUDGED is counted apart and never folded into the pass count"
    - "Inventory derived from the tree, answered from a committed register -- a new package becomes a new GAP row by itself"
    - "Table-5 rows CITE the Sec17 rows that measure them and take the worst verdict; a cited row that a run does not produce is a GAP, never a shrug"
    - "Row identity is the thing judged (`G1-M[src/pursuit/gui]`), never a position in a walk"

key-files:
  created:
    - scripts/check_submission.py
    - scripts/submission_common.py
    - scripts/submission_report.py
    - scripts/submission_readme.py
    - scripts/submission_readme_honesty.py
    - scripts/submission_mechanisms.py
    - scripts/submission_docs.py
    - scripts/submission_code.py
    - scripts/submission_testing.py
    - scripts/submission_security.py
    - scripts/submission_scan.py
    - scripts/submission_research.py
    - scripts/submission_table5.py
    - docs/SUBMISSION-CHECKLIST.md
    - docs/mechanism-prd-map.json
    - docs/credential-scan-allowlist.json
    - docs/phases/phase-8/submission_audit_evidence.json
    - tests/unit/submission_gate_helpers.py
    - tests/unit/test_submission_exit_contract.py
    - tests/unit/test_submission_judges.py
  modified:
    - docs/phases/phase-8/TODO.md

key-decisions:
  - "D-82 implemented: Sec17 is a script with the measure_gate7 exit contract -- 0 all-pass, 1 any GAP, 2 on an evidence set that judged nothing -- not a prose checklist, because a prose checklist cannot fail"
  - "UNJUDGED is a first-class verdict, never a pass. Table 5's own `Enforced by` column marks OOP, TDD and hardcoded values `Code review`/`Work process`; 13 rows carry it"
  - "The Sec2.3 mechanism inventory is walked from `git ls-files` and answered from `docs/mechanism-prd-map.json`, never from a `docs/PRD_*.md` glob -- the glob answers a question nobody asked"
  - "A SUPERSEDED PRD is refused as coverage by name, so `docs/PRD_rl_strategy.md` cannot close the strategy row"
  - "The credential scan splits into provider shapes (unconditional, unexemptable) and a generic assignment shape (exemptable per path, with a reason, and stale entries fail the row)"
  - "Row identity is the path judged, not the walk index -- probe 11 proved positional ids renumber unrelated rows"

patterns-established:
  - "Anti-vacuity by construction: four independently-named emptiness reasons, each pinned by its own test, and EMPTY_EVIDENCE outranks GAPS_FOUND"
  - "Every counter-control asserts the mutation LANDED before the verdict is read"
  - "A derived check whose derivation can empty (superseded terms, verification files, ISO characteristics) reports UNJUDGED, never PASS"

duration: 145min
completed: 2026-08-17
---

# Phase 8 Plan 01: The §17 + Table-5 Audit Summary

**Segal §17's six-group final checklist and §19.1 Table 5 built as a 13-file runnable gate over 86 tree-derived rows with a real exit-2 state, mutation-proven by 13 probes, plus `docs/SUBMISSION-CHECKLIST.md` registering all 32 gaps with the exact path each fix lands in.**

## Performance

- **Duration:** ~145 min
- **Tasks:** 3 (the gate, the register, the tests) — committed as one atomic feature commit
- **Files created:** 20 · **modified:** 1

## Plan provenance — no `08-01-PLAN.md` exists

`.planning/phases/08-submission-and-league-operations/` contains only `08-CONTEXT.md` and
`08-PLAN-OUTLINE.md`; the per-plan files were never written. This plan was executed from
**`08-PLAN-OUTLINE.md` §9's "08-01 — The §17 audit, as a gate that can fail"** entry (objective,
acceptance, trap) plus §3's **D-82** and §5's expected findings, all of which were
**re-derived against the tree rather than inherited**.

## What the gate measures

`uv run python scripts/check_submission.py` — **86 rows, 41 PASS / 32 GAP / 13 UNJUDGED,
73 judged, exit 1** at HEAD.

| Group | PASS | GAP | UNJUDGED |
|---|---:|---:|---:|
| 1. Structure & documentation | 12 | 16 | 0 |
| 2. Architecture & code | 5 | 2 | 3 |
| 3. Testing & quality | 3 | 1 | 3 |
| 4. Configuration & security | 12 | 3 | 0 |
| 5. Research & visualization | 1 | 4 | 0 |
| 6. Extensibility & standards | 1 | 5 | 2 |
| T5. Table 5 (§19.1) | 7 | 1 | 5 |

## The exit-2 state is real, and it outranks exit 1

Four independently-named emptiness reasons, each proven:

| Probe | Input | Result |
|---|---|---|
| 1 | `--empty-probe`, end to end | **exit 2**, all four reasons printed |
| 2 | the full 86-row set with `mechanism_count = 0` | **exit 2** — `EMPTY_EVIDENCE` over 32 real GAPs |
| 3 | the full row set with `readme_count = 0` | **exit 2** |
| 4 | rows present, every one UNJUDGED | **exit 2**, `judged = 0` |

Probes 2 and 3 are the load-bearing ones: a run that judged nothing cannot know whether it
has gaps, so an empty inventory must not be reported as "32 gaps found".

## Mutation proofs — one counter-control per group

Every probe asserted the mutation landed before the verdict was read, and every probe was
reverted with the tree verified clean.

| # | Probe | Rows changed |
|---|---|---|
| 5 | group 1 — unstage `docs/PLAN.md` | **1** — G1-11 PASS → GAP |
| 6 | group 2 — plant a `src/` module with no docstring | **1** — G2-07 PASS → GAP (196 modules parsed, offender named) |
| 7 | group 3 — unstage `.github/workflows/quality-gate.yml` | **1** — G3-02 PASS → GAP |
| 8 | group 4 — unstage `.env-example` | **2** — G4-01 PASS → GAP **and** T5-12 followed its citation |
| 9 | group 5 — unstage 3 of 4 curve artifacts | **1** — G5-01 PASS → GAP |
| 10 | group 6 — plant a real ISO-25010 map (positive control) | **1** — G6-05 GAP → **PASS**, back to GAP on removal |
| 11 | plant an empty `src/pursuit/probe_pkg/` | **1 new row** — `G1-M[src/pursuit/probe_pkg]` = GAP |
| 12 | plant a 161-code-line `src/` file | **2** — G2-03 PASS → GAP **and** T5-08 followed its citation |
| 13a | add a **stale** allowlist entry | G4-02 PASS → GAP, `STALE allowlist entries: 1` |
| 13b | plant a provider key **inside an allowlisted file** | G4-02 PASS → GAP, `provider-shape hits: 1` |

Probes 8 and 12 changing two rows is the Table-5 citation working as designed, not leakage:
each Table-5 row takes the worst verdict of the §17 rows it cites.

## The gate found two defects in its own work

**1. Positional row identity (found by probe 11).** The mechanism rows were first numbered
`G1-M01`, `G1-M02`, … in walk order. Planting one package renumbered every row after it, so
the probe's diff showed `G1-M04: PASS → GAP` and `G1-M11: <absent> → PASS` — two changes for
one insertion, and a stable register row silently changing its own id. Rows are now
identified by the path they judge; the re-run produces **exactly one** new row.

**2. A vacuous test of my own (found by test-mutation A).** `test_a_quoted_mermaid_string_is_not_a_rendered_block` asserted only
`_FENCE.match(quoted) is None`. `.match` anchors at position 0 whatever the pattern says, so
the test **passed** when `_FENCE` was deliberately weakened to the bare substring
`` ```mermaid ``. It now also asserts `.search`, and a third test runs `mermaid_blocks()`
end to end against `docs/phases/phase-8/TODO.md` — first asserting the trap file still
contains the literal fence string, so the test cannot pass by losing its subject. Re-run under
the same weakening: **1 failed**.

## Findings the outline predicted, re-derived here

Each was confirmed mechanically rather than inherited:

- **README describes a system this repo does not ship (G1-08, G1-09).** 3 unqualified
  mentions of `Q-Learning`, derived from the H1 of the SUPERSEDED `docs/PRD_rl_strategy.md`;
  Phase 3 verified `passed` yet still shown "in progress". Registered only — **08-06 rewrites**.
- **All seven §2.1 items fail (G1-01…G1-07 + G1-03b).** The outline said six of seven; the
  gate measures **seven**, because the examples/screenshots item is split into a code-sample
  half (present) and a non-curve-image half (**0 of 3 images**), and the composite row fails.
- **Three mechanisms without a PRD:** `sdk/` (11 modules), `gui/` (7 modules),
  and the tunnel — `docs/PRD_mcp_transport.md:28` puts tunneling out of scope in as many words.
- **Zero rendered diagrams.** `grep -rl '```mermaid' docs/` no longer returns nothing — it
  returns `docs/phases/phase-8/TODO.md`, where the string is a **quoted grep command inside a
  table cell**. The gate counts 0.
- **ISO/IEC 25010** — the eight names parsed out of §13; no tracked doc names all eight and
  cites eight repo paths.
- **No LICENSE, CONTRIBUTING.md, PROMPT_LOG.md, notebook, token-cost analysis,
  sensitivity analysis, extension-points doc, deployment doc, screenshots, git tag.**
- **`RULES.md:97`** (not `:83` — line numbers have shifted) writes rule 48 as "survival
  **10/5**" against Table 17's cop 5 / thief 10. Both halves are parsed from the documents;
  no number is written into the gate and no fixed value was touched.
- **The declaration artifact has zero production callers**, re-derived at HEAD. Registered
  outside the gate's reach — a dead-code row needs call-graph reachability. **08-04 owns it.**

## Findings the outline did **not** predict

| Finding | Evidence | Owner |
|---|---|---|
| Root-level `graph.json` / `graph.html` are **not** gitignored | `git check-ignore -q` exit 1 for both; `.gitignore:151-152` covers only `.planning/graphs/…`, while CLAUDE.md states they are gitignored build artifacts | 08-03 |
| 4 of 26 tracked config JSONs carry no `version` field | `config/{police,thief}/{resolution,role}.json` | 08-03 |
| `__all__` missing from 7 of 11 packages; `__version__` in **0** | §14 professional packaging | 08-03 |
| No automated test-report artifact | no `coverage.xml`/JUnit/`htmlcov`, and no CI directive that would produce one | 08-03 |
| `version.py` `1.00` vs `pyproject.toml` `1.00.0` | D-79 derives the tag name from the reconciled value | 08-11 |

## Standing gates

| Gate | Result | Baseline |
|---|---|---|
| `uv run pytest --cov` | **2174 passed, 0 failed**, coverage **97.37%** | 2153 / 97.37% — **+21 tests, coverage unchanged** |
| `uv run ruff check .` | 0 violations | 0 |
| `sh scripts/check_line_limit.sh` | exit 0 (488 files enumerated) | exit 0 |
| line limit, all 16 new files **explicitly by path** | exit 0 | — |
| `check_local_truth.py` | `OK: 7 module(s) scanned`, exit 0 | 7 modules |
| `check_no_llm_in_strategy.py` | OK, exit 0 | OK |
| **Rule-38 counters, full suite** | police **1922 → 1922**, thief **1915 → 1915** — **delta 0/0** | — |
| `git diff config/` | **empty** | empty |
| every new file **not** gitignored | 16/16 confirmed by `git check-ignore` | D7-10's guard |

`scripts/` is enumerated by neither `check_line_limit.sh` (`src/** tests/** training/**`) nor
coverage (`source = ["src", "training"]`), so all 13 script files were **split by hand** —
`submission_readme.py` hit 168 code lines and was **split**, never compressed — and are checked
explicitly by path. The 21 new tests load them **by path**, so the suite and the CLI a grader
runs are proven to be the same code.

## Decisions Made

- **D-82 implemented as written.** Exit 0/1/2, with 2 outranking 1.
- **`UNJUDGED` is a verdict, not an excuse.** 13 rows carry it, each with the reason written
  into the row itself. Table 5's own *Enforced by* column is the authority.
- **The mechanism register is committed, the inventory is not.** The walk cannot invent a
  package and the register cannot hide one.
- **A superseded PRD is refused as coverage by name**, so the strategy row cannot be closed
  with `docs/PRD_rl_strategy.md`.
- **The credential allowlist is two-tier.** Provider shapes are unexemptable; the generic
  shape is exemptable per path with a reason, and stale entries fail the row.

## Deviations from Plan

No `08-01-PLAN.md` existed, so there is no task list to deviate from. Three departures from
the **outline's** §9 acceptance text, each deliberate:

**1. [Rule 2 — Missing critical] The credential scan needed a two-tier pattern set.**
- **Found during:** the first gate run — G4-02 reported 5 hits, all synthetic HMAC fixtures.
- **Issue:** a single generic pattern makes the row permanently red for a non-defect, which
  destroys the signal; weakening the pattern would have destroyed the check.
- **Fix:** provider shapes stay unconditional; the generic shape gained a committed,
  per-reason allowlist whose stale entries fail the row. Both properties probe-proven (13a/13b).
- **Committed in:** `4b63ee7`.

**2. [Rule 1 — Bug] Mechanism row ids were positional.** See "defects in its own work" above.

**3. [Rule 1 — Bug] A test of mine measured nothing.** See test-mutation A above.

**Total deviations:** 3 (1 missing-critical, 2 bugs in this plan's own work).
**Impact:** none on scope. All three strengthen the gate.

## Issues Encountered

- **A probe revert failed silently.** After `git add`-ing a mutated `tests/unit/test_step0_sign.py`,
  `git checkout -- <file>` restored it **from the index**, which held the mutation — the
  post-revert grep still found the planted key. Corrected with `git checkout HEAD -- <file>`
  and re-verified: `sk-ant` count 0, `git status` clean. This is the same hazard the phase-7
  record already carries; it is written down again because the first check caught it and a
  post-revert assertion is the only reason it did.
- `git status` after all 13 probes shows **only** the 08-01 additions — no `M` entries.

## User Setup Required

None.

## Next Phase Readiness

- `docs/SUBMISSION-CHECKLIST.md` is the input to waves 2–3; every gap names its owner plan.
- 08-06/07/08/09 can close their gaps and re-run the gate to watch rows go green.
- 08-11 must re-run this gate at HEAD with every remaining GAP closed or carrying a dated
  recorded reason.

**Nothing was pushed. No tag was created. No remote was touched.** The gate's only git calls
are `ls-files`, `log`, `tag -l` and `check-ignore` — all local reads.

## Self-Check: PASSED

Run 2026-08-17, after both commits landed.

- **20 of 20 claimed paths present**, all tracked, **none gitignored** (D7-10's guard).
- **Commit `4b63ee7` reachable** in `git log --all`.
- **Evidence JSON re-read from disk:** 41 PASS / 32 GAP / 13 UNJUDGED over 86 rows, exit 1,
  10 mechanisms discovered -- matching every count claimed above.
- **Three numbers in the register were CORRECTED, not left as written**, after re-reading the
  evidence JSON: `.env-example` key lines 24 -> **12**; line-limit enumerated files 489 -> **488**;
  `src/` modules parsed 196 -> **195** (489 and 196 were the values *under probe 12 and probe 6*,
  not at HEAD, and the probe rows now say so).
- **`git tag -l` is empty and 125 commits sit ahead of `origin/main`** -- nothing was pushed, no
  tag was created, no remote was touched.

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*
