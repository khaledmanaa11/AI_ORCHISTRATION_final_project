---
phase: 08-submission-and-league-operations
plan: 02
subsystem: testing
tags: [requirements-ledger, traceability, reconciliation, evidence-citation, anti-vacuity]

requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "`05-VERIFICATION.md`'s last open human item -- 'Decide the repo-wide REQUIREMENTS.md status table (do not tick Phase 5 alone) ... Fix the table as a whole or leave it alone'"
  - phase: 03-blind-strategy-module-rl-policy
    provides: "`03-VERIFICATION.md`'s flag that STRAT-01/02 still described the withdrawn Q-learning mechanism, recorded as 'OPEN, flagged not fixed'"
  - phase: 08-submission-and-league-operations
    provides: "08-01's `docs/SUBMISSION-CHECKLIST.md` and `submission_audit_evidence.json`, cited by nine QUAL/DOC/SUB rows"
provides:
  - "`.planning/REQUIREMENTS.md` reconciled: 77 counted, 48 ticked, every tick citing a verbatim quote a gate reads back"
  - "`scripts/check_requirements_ledger.py` + 3 siblings -- 0 clean / 1 any violation / 2 judged nothing"
  - "`docs/TODO.md`, `.planning/ROADMAP.md` Progress and `docs/phases/phase-1/TODO.md` brought to the artifacts"
affects: [08-10, 08-11, 07-10, verify-work]

tech-stack:
  added: []
  patterns:
    - "A ledger tick must cite `path` \"verbatim quote\"; the gate opens the file and looks for the sentence"
    - "`**evidence:**` means satisfied and appears only on ticked rows; open rows use `**status:**`"
    - "Every traceability row declares its own `**N/M ticked**` count, cross-checked against the real checkboxes -- catching a flip in EITHER direction"

key-files:
  created:
    - scripts/check_requirements_ledger.py
    - scripts/requirements_ledger.py
    - scripts/requirements_rows.py
    - scripts/requirements_trace.py
    - tests/unit/test_requirements_ledger.py
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - docs/TODO.md
    - docs/phases/phase-1/TODO.md
    - docs/phases/phase-8/TODO.md

key-decisions:
  - "Reconciled as a WHOLE in one commit -- fixing one row misdescribes the repo in the other direction, which is why this was left alone until now"
  - "Truth order enforced: NN-VERIFICATION.md verdict, then GATE-N-MEASUREMENT.md criteria, then SUMMARY counts. A tracker's own banner is never evidence for that tracker"
  - "All nine REPORT-* rows stay OPEN: gate-measured is not phase-verified, and no 07-VERIFICATION.md exists. Recording the distinction rather than erasing it"
  - "STRAT-01/02/06 reworded to the matrix mover; the withdrawn Q-learning wording is preserved verbatim in the 03-VERIFICATION.md quote the row cites"
  - "A tick cites a verbatim QUOTE, not just a path, because several verification documents carry no per-REQ-ID table and a path-only rule would let any Phase-4 row cite 04-VERIFICATION.md and be believed"

patterns-established:
  - "Bidirectional tamper detection: the declared-count cross-check fails on a flip AND on a quiet un-tick"
  - "Split a file at 149 of 150, not at 151 -- a file one line from the gate is a trap for the next editor"

duration: 95min
completed: 2026-08-17
---

# Phase 8 Plan 02: Project-Wide Tracker Reconciliation Summary

**`.planning/REQUIREMENTS.md` rebuilt from the verification artifacts — 74→77 counted, 6→48 ticked with every tick citing a verbatim quote a new gate reads back — moved in ONE commit with `docs/TODO.md`, the ROADMAP Progress table and the phase-1 triplet, and with Phases 4, 7 and 8 left honestly incomplete.**

## Performance

- **Duration:** ~95 min
- **Tasks:** 3 (the ledger, the other four trackers, the gate) — one atomic commit, as mandated
- **Files created:** 5 · **modified:** 5

## Plan provenance — no `08-02-PLAN.md` exists

Executed from **`08-PLAN-OUTLINE.md` §6 and §9's "08-02 — Project-wide tracker reconciliation,
one commit"** entry. Every figure below was re-derived from the tree and the artifacts.

## Before and after

| File | Before | After |
|---|---|---|
| `.planning/REQUIREMENTS.md` header | **"74 total"** against a breakdown summing to 77 | **77**, counted by `grep -c "^- \[[ x]\]"` |
| `.planning/REQUIREMENTS.md` ticks | **6 of 77** (BASE-01, BASE-08, CLOUD-01, CLOUD-02, QUAL-01, QUAL-06) | **48 of 77**, each citing `path` "verbatim quote" |
| Traceability rows | **10 of 10 read `Pending`** — including three phases whose verification reads `passed` | 10 evidenced verdicts; **one** `Pending` survives (DOC), and it says why |
| `docs/TODO.md` Phase 1 | no banner, **all 5 rows ☐**, against `01-VERIFICATION.md` `passed` (2026-07-28) | banner + all 5 ☑ |
| `docs/TODO.md` overall | 69 done / 6 in progress / **many stale ☐** | 69 ☑ / 6 ◐ / **6 ☐**, and all six are genuinely outstanding |
| `.planning/ROADMAP.md` Progress | Phase 7 **"Not started — not yet planned"**; Phase 8 the same | Phase 7 **11/12 executed, NOT verified**; Phase 8 **2/14 in progress** |
| `docs/phases/phase-1/TODO.md` | row `1-99` ☐ and **7 of 7 gate boxes unticked** | all closed, with the three-week lag recorded |
| Triplet table | Phase 1 `◐/◐/◐`; "All TODOs ☑" ☐ for phases 2–3 | all 8 triplets ☑ (verified tracked on disk); TODO-closure column honest per phase |

**Ticks by family:** BASE 8/8 · NET 9/9 · STRAT 7/7 · LANG **5/7** · CLOUD 2/2 · SEC 8/8 ·
REPORT **0/9** · SUB **0/12** · QUAL **9/13** · DOC **0/2**.

## What was deliberately NOT ticked, and why

| Held open | Count | Reason, written into the row |
|---|---:|---|
| LANG-01, LANG-06 | 2 | §10.4 criteria 1 and 3 read `✓ VERIFIED (mocked) / ? PENDING (live)`; no live GATE-4 run exists and the **responder** side is unmeasured since 05-06 changed responder hint composition on 2026-08-14 |
| REPORT-01 … REPORT-09 | 9 | **Gate-measured is not phase-verified.** `GATE-7-MEASUREMENT.md` reports criterion 2 PASS, criterion 3 PASS, criterion 1 dry-run PASS + live PENDING — real evidence, recorded per row — but **no `07-VERIFICATION.md` exists**. REPORT-01's live send has never happened; REPORT-06's `declaration_` artifact has zero production callers |
| SUB-01 … SUB-12 | 12 | Phase 8 is 2 of 14 plans in; three of four gate criteria are structurally human-completed |
| QUAL-02, -05, -07, -11 | 4 | Table 5's own *Enforced by* column marks these `Code review`, `Integration test` and `Work process`; 08-01's audit prints them **UNJUDGED**, and a tick would be a claim no script earned |
| DOC-01, DOC-02 | 2 | "kept current" has no terminal state; 3 of 10 mechanisms still have no PRD |

**Rule 38 cuts both ways**, so the reverse was applied too: 42 rows that had been sitting
unticked against `SATISFIED` verdicts were ticked, and probe 4 below proves the gate catches a
quiet un-tick as readily as a false tick.

## STRAT-01/02/06 reworded — a hand-off honoured

`03-VERIFICATION.md` recorded the stale wording as **"OPEN, flagged not fixed"**, explaining that
"correcting only the Phase-3 rows would misrepresent its state" while the file was unmaintained.
This pass corrects the whole file, so the rows moved with it. The withdrawn text is preserved
verbatim inside the `03-VERIFICATION.md` sentence that STRAT-01 now cites — nothing was erased.

## The gate, and the hole its own probe found

`uv run python scripts/check_requirements_ledger.py` — **0** clean, **1** any violation, **2**
judged nothing. Live result: **77 checkboxes (48 ticked, 29 open), declared total 77, 10
traceability rows, 48 citations resolved to real quotes, exit 0.**

| # | Probe | Result |
|---|---|---|
| 1 | flip `SUB-05` from `[ ]` to `[x]` | **FIRST RUN: exit 0 — the gate was wrong.** See below. **After the fix: exit 1**, "SUB: traceability declares 0 ticked, the checkboxes show 1" |
| 2 | make a tick quote text that is not in its artifact | exit 1, naming the file and the quote |
| 3 | run over an **empty** ledger | **exit 2** with all three reasons — never OK |
| 3b | run over a **missing** ledger | **exit 2** |
| 4 | quietly **un-tick** `SEC-04` | exit 1 on **three** independent rules |

### The hole, in full

The probe that was supposed to prove the gate worked is what broke it. Flipping `SUB-05` produced
**exit 0**. The cause: an open row legitimately cites the artifact explaining *why* it is open, and
a path-and-quote check cannot distinguish "evidence that this is done" from "evidence that this is
not". One character therefore produced a green ledger asserting a Git tag existed while
`git tag -l` is empty — a rule-41 claim with nothing behind it.

**Closed with two independent rules, neither of which is cosmetic alone:**

1. `**evidence:**` now means *satisfied* and appears only on ticked rows; all 29 open rows were
   converted to `**status:**`. A bare flip loses its citation.
2. **Every traceability row declares `**N/M ticked**`, and the gate counts the family and
   compares.** A flip makes declared and actual disagree, and no rewording of a marker can hide
   that. This is `05-VERIFICATION.md`'s "fix the file as a whole or leave it alone" instruction
   turned into something a machine holds.

A third rule already present — an open row must name what is outstanding — fires on the un-tick.
Probe 4 trips all three at once.

## Standing gates

| Gate | Result | Baseline |
|---|---|---|
| `uv run pytest --cov` | **2188 passed, 0 failed**, coverage **97.37%** | 2153 / 97.37% — **+35 tests across both plans, coverage unchanged** |
| `uv run ruff check .` | 0 violations | 0 |
| `sh scripts/check_line_limit.sh` | exit 0 | exit 0 |
| line limit, all 4 new files **explicitly by path** | exit 0 (116 / 71 / 63 / 56 code lines) | — |
| `check_local_truth.py` | exit 0, 7 modules | 7 modules |
| `check_no_llm_in_strategy.py` | exit 0 | OK |
| `check_requirements_ledger.py` | **exit 0** | new |
| `check_submission.py` | exit 1, **32 GAPs unchanged** — the reconciliation closed no §17 gap and claimed none | 32 |
| **Rule-38 counters, full suite** | police **1922 → 1922**, thief **1915 → 1915** — **delta 0/0** | — |
| `git diff config/` | **empty** | empty |
| every new file **not** gitignored | 4/4 confirmed | D7-10's guard |
| line endings on all 10 touched files | **CR = 0** on every one | LF required |

## Decisions Made

- **One commit, five files.** Enforced, not aspirational — the declared-count cross-check makes a
  partial edit fail the gate.
- **A tick cites a verbatim quote, not a path.** Several verification documents (Phase 4's in
  particular) carry no per-REQ-ID coverage table; a path-only rule would let any Phase-4 row cite
  `04-VERIFICATION.md` and be believed, including the two honestly open ones.
- **Phase 7's nine rows all stay open.** The outline named REPORT-02…07; the same reasoning
  applies to REPORT-08/09, which are gate-measured PASS but equally unverified. Consistency over
  a partial tick, with each row's real status recorded so nothing is understated in substance.
- **`requirements_ledger.py` was split at 149 of 150 code lines**, not compressed and not left at
  the edge.

## Deviations from Plan

No `08-02-PLAN.md` existed. Two departures from the outline's §9 text:

**1. [Rule 2 — Missing critical] The gate needed a second, semantic rule.**
- **Found during:** probe 1, which the outline itself mandates.
- **Issue:** the path-and-quote rule alone let a `[ ]` → `[x]` flip pass, because open rows carry
  citations too.
- **Fix:** marker separation (`**evidence:**` vs `**status:**`) plus the per-family declared-count
  cross-check in `scripts/requirements_trace.py`. Both probe-proven, in both directions.
- **Committed in:** `aeb7272`.

**2. [Rule 1 — Bug] My own tick arithmetic was wrong, and the gate caught it.**
- **Issue:** the summary prose read "Satisfied: 47 of 77" and "QUAL 8/13"; the real counts are
  **48** and **9/13**. The header-total rule surfaced the discrepancy on the first run.
- **Fix:** corrected in the file before commit. Recorded here because it is the gate doing the
  job it was built for, on its author.

**Total deviations:** 2 (1 missing-critical, 1 bug in this plan's own work).
**Impact:** none on scope. Both strengthen the ledger.

## Issues Encountered

- The header regex missed `**77 total**` because of the markdown emphasis and reported "no total
  declared" for a file that declared one. Relaxed to tolerate `**`, with the reason written into
  the pattern's comment.
- `check_declared_counts` was first wired to the traceability table's **phase** cell, which
  contains no REQ-ID, so no family resolved. Corrected to the requirements cell; the tests pin the
  behaviour in both dimensions (ticked count and family size).

## User Setup Required

None.

## Next Phase Readiness

- `05-VERIFICATION.md`'s last open `human_verification` item — the repo-wide status table — is
  **closed by this pass**.
- Phase 7 is now accurately described everywhere as **11 of 12 plans, not verified**. Closing it
  needs 07-10 (the live send) and then `/gsd:verify-work 7`.
- Phase 4's live GATE-4 run remains the sole blocker on LANG-01/LANG-06.
- `/gsd:verify-work 8` can rely on `check_requirements_ledger.py` rather than re-reading rows.

**Nothing was pushed. No tag was created. No remote was touched.**

## Self-Check: PASSED

Run 2026-08-17, after the reconciliation commit landed.

- **12 of 12 claimed paths present**, all tracked, **none gitignored**.
- **Commit `aeb7272` reachable** in `git log --all`.
- **Ledger re-counted from disk:** 48 ticked + 29 open = **77**, header declares **77**.
  Per family, independently recounted: BASE 8/8 · NET 9/9 · STRAT 7/7 · LANG **5/7** ·
  CLOUD 2/2 · SEC 8/8 · REPORT **0/9** · SUB **0/12** · QUAL **9/13** · DOC **0/2** -- every one
  matching the traceability row that declares it, which is what the gate cross-checks.
- **`check_requirements_ledger.py` exit 0** at HEAD; **48 citations resolved to real quotes in
  real files**, equal to the tick count.
- **Rule-38 counters unchanged by the suite:** police 1922 -> 1922, thief 1915 -> 1915.
- **`git tag -l` is empty and 125 commits sit ahead of `origin/main`** -- nothing was pushed, no
  tag was created, no remote was touched.

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*
