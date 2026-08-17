---
phase: 08-submission-and-league-operations
plan: 11
subsystem: infra
tags: [git-tag, submission-gate, runbooks, versioning, measurement, graphify]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-10's two split repositories, built locally outside this tree with zero remotes"
  - phase: 08-submission-and-league-operations
    provides: "08-01's runnable Sec17 + Table-5 audit gate and its gap register"
  - phase: 08-submission-and-league-operations
    provides: "08-09's sensitivity sweep, which found the unreproducible 89%/1% pair"
provides:
  - "Annotated tag v1.00 cut in BOTH split outputs, verified, and NOT pushed"
  - "docs/phases/phase-8/GATE-8-MEASUREMENT.md -- the submission gate measured, three of six halves honestly PENDING"
  - "scripts/measure_gate8.py + four gate8_*.py siblings, exit 0/1/2, no remote verb anywhere"
  - "PUBLISH-, LEAGUE- and SUBMISSION-RUNBOOK.md -- the three human-run procedures for 08-12/08-13/08-14"
  - "docs/SELF-ASSESSMENT.md with the score field blank and pinned blank"
  - "T5-06 closed: one version, one source of truth, pinned by a test proven to fail on disagreement"
  - "The 89% -> 1% claim corrected to the reproducible 32.0% -> 7.5% in all four artifacts that quote it"
affects: [08-12, 08-13, 08-14, verify-work]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate criteria reported as two NAMED halves so a grep for PASS cannot match an unfinished criterion"
    - "Doc-to-evidence anti-drift: verdict STRINGS read out of the evidence JSON and required verbatim in the record"
    - "Named exemption lists (DELIBERATE_BUMPS, LOCAL_ONLY_PATHS) with a test that refuses an exemption for a file that does not need one"

key-files:
  created:
    - docs/phases/phase-8/GATE-8-MEASUREMENT.md
    - docs/phases/phase-8/PUBLISH-RUNBOOK.md
    - docs/phases/phase-8/LEAGUE-RUNBOOK.md
    - docs/phases/phase-8/SUBMISSION-RUNBOOK.md
    - docs/phases/phase-8/gate8_measurement_evidence.json
    - docs/SELF-ASSESSMENT.md
    - scripts/measure_gate8.py
    - scripts/gate8_common.py
    - scripts/gate8_repos.py
    - scripts/gate8_submission.py
    - scripts/gate8_report.py
    - tests/unit/test_version_single_source.py
    - tests/unit/test_sensitivity_correction.py
    - tests/unit/test_gate8_measure.py
    - tests/unit/test_gate8_record.py
    - tests/unit/test_phase8_runbooks.py
    - tests/unit/test_self_assessment.py
  modified:
    - pyproject.toml
    - src/pursuit/shared/resolution.py
    - docs/phases/phase-3/ENGINEERING-LOG.md
    - docs/phases/phase-3/PRD.md
    - docs/phases/phase-3/PLAN.md
    - docs/SENSITIVITY.md
    - docs/SUBMISSION-CHECKLIST.md
    - docs/phases/phase-8/TODO.md
    - docs/phases/phase-8/split_build_evidence.json
    - docs/phases/phase-8/submission_audit_evidence.json
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "The tag is cut ONLY in the two split outputs and never in this repository (D-79) -- reinforced by a measured hazard: an external process pushes this repo's origin/main unbidden, so a local tag here could be swept outward"
  - "pyproject.toml is reconciled DOWN to shared/version.py's 1.00, not the other way: 1.00 is the Table-5 baseline and what all 28 config JSONs already carry"
  - "The version pin compares RAW STRINGS, never PEP-440 versions -- 1.00 and 1.0 are the same version and two different tag names"
  - "Act 4.3's table body is left intact under its correction block, because scripts/sensitivity_reconcile.py PARSES it for the claim it re-measures"
  - "GATE-8 exit 0 means 'everything that could be true before a human acts is true', never 'GATE-8 is met' -- the gate DOCUMENT carries the PENDING, not the exit code"

patterns-established:
  - "Two-halves verdict strings: 'BUILT+TAGGED PASS; PUBLISHED PENDING (08-12)' is the whole verdict, so no substring search can mistake it for a pass"
  - "Runbook citation contract: every backticked repo path resolved against git ls-files, with gitignored paths exempted BY NAME and required to say 'gitignored' in the prose"

# Metrics
duration: ~3h
completed: 2026-08-17
---

# Phase 8 Plan 11: Tag prepared, GATE-8 measured, runbooks written Summary

**Annotated `v1.00` cut in both split repositories and pushed nowhere; GATE-8 measured as three
criteria in six halves with three honestly PENDING; three human-run runbooks; T5-06 closed to a
single source of truth; and the unreproducible `89% → 1%` figure corrected in all four artifacts
that ship it.**

## Performance

- **Duration:** ~3h (first commit 2026-08-17T22:23+03:00, last 2026-08-17T23:26+03:00, plus two
  full split rebuilds and two full local suites)
- **Tasks:** 8 (executed from `08-PLAN-OUTLINE.md` §9 — **no `08-11-PLAN.md` exists**, the same
  way 08-03 … 08-10 were run)
- **Commits:** 11, each atomic; 3 of them TDD RED tests committed before their fix
- **Files created/modified:** 28 tracked files against the 08-10 baseline `4466b55`

> **This run was interrupted by a server-side 529 and resumed.** What was already committed was
> **verified on disk, not redone**: 8 commits (`4bdd57e` … `99a8959`, plus the two earlier
> version commits `f34236f`/`ec55b5d` the interrupt notice did not list), the reconciled
> `version.py`/`pyproject.toml` pair, and an empty `git tag -l`. The uncommitted
> `split_build_evidence.json` was inspected before being trusted — it was **complete**, not
> half-written: both repository objects present, `verdict: pass`, `source_commit: 99a8959`,
> 12 rows each. Redone after the interrupt: the final rebuild's verification, re-cutting both
> tags (which `--replace` had wiped), the GATE-8 re-measurement, and the final suite.

## Accomplishments

- **The tag, prepared and verified — and pushed nowhere.** Annotated `v1.00` in
  `pursuit-police` (`daa16a7`) and `pursuit-thief` (`b0cb27b`), each pointing at its own
  output's `HEAD`, each listing **1046** files — equal to that output's `git ls-files` — in
  repositories with **zero remotes**. `git tag -l` in this repository is **empty**.
- **GATE-8 measured without a single blanket PASS.** Three criteria, six halves, three PENDING,
  each with a named owner.
- **Three runbooks a human can follow start to finish**, each stating in its own text that no
  agent may enter credentials, click consent, create a repository or send mail.
- **T5-06 closed**: the audit gate moved **69 PASS / 4 GAP → 70 PASS / 3 GAP**, exactly the one
  row this plan owned.
- **The 89% → 1% correction landed in all four sites**, direction unchanged, cause stated as
  never established, measuring script named.

## Task Commits

1. **Version pin, RED** — `f34236f` (test): 1 failed / 4 passed against the real disagreement
2. **T5-06 reconciled, GREEN** — `ec55b5d` (fix): `pyproject.toml` `1.00.0` → `1.00`
3. **Four-site correction, RED** — `4bdd57e` (test): 3 failed / 4 passed at HEAD
4. **Four-site correction applied** — `817ed57` (docs): 7 passed
5. **GATE-8 measurement machinery** — `65b38a2` (feat): 5 scripts, 15 contract tests
6. **Three runbooks** — `098ae91` (docs), with one deliberate RED assertion
7. **Self-assessment** — `445a007` (docs): score field blank and pinned blank
8. **Graph refresh (08-96)** — `123dff5` (chore): 12410 nodes / 21398 edges / 680 communities
9. **GATE-8 record** — `4a4317a` (docs): closes the deliberate RED from commit 6
10. **Phase-8 TODO ticked** — `99a8959` (docs): rows 08-11 and 08-96, with evidence
11. **Final rebuild, tags re-cut, GATE-8 re-measured** — `8a421a4` (chore): 12/12 in both outputs

## The tag decision, stated plainly

**What I did:** created a **local annotated tag `v1.00` in each of the two split output
repositories**, which live at `C:\Users\Hp\pursuit-split-repos\` — outside this tree — and have
**zero remotes**.

**What I did not do:** I did not push anything, did not create a repository, did not add a
remote, did not cut a tag in this repository, and issued **no remote or `gh` command of any
kind**. `git tag -l` here returns nothing, and
`gate8_measurement_evidence.json` records `development_repo_is_deliberately_untagged: true`.

**Why the outputs and not here** — two reasons, one by decision and one by measurement:

1. **D-79.** The tag belongs on the submitted artifact. This repository's `main` is far ahead of
   a remote that is not the submission target.
2. **A measured hazard.** This repository's `origin/main` moves with no agent pushing it
   (observed 2026-08-14 and 2026-08-16, no git hook responsible). A local tag *here* could be
   carried outward by a process nobody in this session controls. The two outputs have zero
   remotes and sit outside this tree, so a tag in them cannot leave the machine by accident.
   This is written into `GATE-8-MEASUREMENT.md` and the `G6-08` checklist row, not only here.

**Verification, per output:** annotated (`git cat-file -t v1.00` → `tag`), `git rev-list -n 1
v1.00` equals `git rev-parse HEAD`, `git ls-tree -r --name-only v1.00 | wc -l` = **1046** =
`git ls-files | wc -l`, `git remote` → empty. Inside the tag: `pyproject.toml` reads
`version = "1.00"`; `resolution.py` and `phase-3/PRD.md` both carry the corrected
`32.0% → 7.5%`; all five of this plan's documents are present. Each of the **seven** forbidden
names (`.env`, `police_thief_p2p.pdf`, `requirements.txt`, the four `games_played*.json`) was
checked **exactly** against the tagged tree and all seven are **absent**.

> One honest correction to my own check: a *substring* grep for those names returns **2** hits.
> Both are test **modules** named after the counter — `tests/unit/test_games_played_counter.py`
> and `test_games_played_at_game_end.py`. The exact-name check is the one that answers the
> question; the grep answers a different one.

## GATE-8 — criteria and statuses

| Criterion | Measured half | Human half | Owner |
|---|---|---|---|
| 1 — two cross-linked public repos + tag | **BUILT+TAGGED PASS** | **PUBLISHED PENDING** | 08-12 |
| 2 — academic README, screenshots, form PDF, per member | **README PASS** (0 of 6 §9.4.2 and 0 of 7 §2.1 headings missing in both outputs) | **SCREENSHOTS PENDING** · **FORM+SUBMISSION PENDING** | 07-10 · 08-14 |
| 3 — ≥2 scored games vs different teams, reported with the commit hash | **MACHINERY PASS** | **GAMES PENDING** | 08-13 (needs 07-10) |

`measure_gate8.py` exits **0**, and the record says in as many words that exit 0 means
"everything that could be true before a human acts is true", **never** "GATE-8 is met". The
document opens **"GATE-8 IS NOT MET"**. Criterion 3's machinery half is real evidence, not a
promise: `write_declaration_artifact` has a production call site
(`end_of_game_declaration.py`), both retained declaration artifacts carry a commit hash at
`declarations.own.declaration.commit_hash`, and the ledger reads **0 scored / 0 total** against
the fixed bounds min 2 / max 10.

## The version reconciliation, with its failure proof

`pyproject.toml` moved `1.00.0` → **`1.00`**, the string `src/pursuit/shared/version.py` already
carried and all 28 tracked config JSONs already agreed with (bar the two deliberate
`weights.json` `2.00` bumps). TOML cannot import, so `pyproject.toml` now **names** `version.py`
as the source it copies, and `tests/unit/test_version_single_source.py` holds them together.

**Proven to fail on disagreement, three ways, each mutation asserted landed before the run and
reverted with `git checkout` afterwards:**

| Probe | Mutation | Result |
|---|---|---|
| A | `pyproject.toml` → `1.0` — **PEP-440 EQUAL** to `1.00`, different string | **1 failed** / 4 passed |
| B | `version.py` → `VERSION = "1.10"` | **3 failed** / 2 passed |
| C | one config JSON → `"version": "9.99"` (isolated, A and B reverted) | **1 failed** / 4 passed |

Probe A is the one that matters: a packaging-aware comparison would have called the original
defect a non-issue by normalising both sides to `1.0`. The test also **parses** the Table-5
baseline out of `docs/SEGAL_GUIDELINES.md` §19.1 rather than typing it, so it cannot agree with
itself.

## The four-site correction

`ENGINEERING-LOG.md` Act 4.3's `89% → 1%` thief-survival pair does not reproduce. Re-measured by
**`scripts/sensitivity_reconcile.py`** over eight weights × rules × opening arms at n=200 each,
the like-for-like arm (shipped run-2 weights, negotiated opening) gives **32.0% → 7.5%**; the
highest arm anywhere is 52.5% and **none is near 1%**.

Corrected in all four artifacts — `docs/phases/phase-3/ENGINEERING-LOG.md`,
`docs/phases/phase-3/PRD.md`, `docs/phases/phase-3/PLAN.md`, and the `PREFERRED` comment block
in `src/pursuit/shared/resolution.py` — plus follow-up closures in `docs/SENSITIVITY.md` and
`docs/SUBMISSION-CHECKLIST.md`.

- **The direction of the shipped decision is confirmed and unchanged.** Declining the swap is
  still worth ~25 points of thief survival and the cop seat still converts 100% under all four
  rule combinations. Only the **magnitude** moves (~88 points → ~25).
- **The cause was never established** — the engine moved through Phases 4–6 between the two
  measurements and the sweep did not isolate which change is responsible. Every site says so.
- **Append-with-correction, not overwrite.** Act 4.3's table body is deliberately left intact
  beneath its correction block, because `sensitivity_reconcile.py` **parses that table** for the
  claim it re-measures — overwriting it would have broken the script that found the problem.
  Verified after the edit: `recorded_claim()` still returns `{89, 1}`.
- Act 4.2's `89% → 10%` line shares the same baseline and is flagged in the correction as
  **not re-measured** (it used a hand-tuned weight of 3.00 the sweep does not cover), rather
  than silently corrected by association.

`tests/unit/test_sensitivity_correction.py` reads **both** pairs out of
`artifacts/sensitivity/reconcile.json` rather than typing them, requires the measuring script to
be named in every site, and requires the superseded claim to **survive** in every site. It ran
**3 failed / 4 passed** against the pre-change text.

## The three runbooks

| Runbook | For | What only the human does |
|---|---|---|
| `PUBLISH-RUNBOOK.md` | 08-12 | answer OQ8-9 and OQ8-5 first; create the two repositories; `remote add` + `push`; push the tag **by name**; fill the four rule-49 links; re-scan a **fresh clone**; send the D7-17 question |
| `LEAGUE-RUNBOOK.md` | 08-13 | arrange opponents; one unscored warm-up then **one** scoring game per opponent; flip `reporting.mode` to `live` and back; confirm the report **arrived** with the commit hash in it |
| `SUBMISSION-RUNBOOK.md` | 08-14 | obtain the form (location unknown, OQ8-3); the rule-38 games-played value; the code-quality-only score; move the tag if code changed; submit per member |

Each names its own plan, states the four acts no agent may perform, and has **every backticked
repository path resolved against `git ls-files`** by `tests/unit/test_phase8_runbooks.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] The runbook citation check found three paths cited as though they shipped**
- **Found during:** Task 5 (runbooks)
- **Issue:** `config/{police,thief}/games_played.json` are **gitignored** and the league ledger
  does not exist until 08-13 — a human on a fresh clone would go looking for files that are not
  there.
- **Fix:** exempted **by name** in `LOCAL_ONLY_PATHS` with a reason each, plus
  `test_the_local_only_exemptions_are_really_untracked`, which refuses an exemption for anything
  actually tracked; and the runbooks now say "gitignored" in prose, enforced by a third test.
- **Committed in:** `098ae91`

**2. [Rule 1 — Bug] The GATE-8 banner scan read a URL out of the README body**
- **Found during:** Task 4 (GATE-8 machinery)
- **Issue:** `_cross_link` took a fixed 2000-character slice from the rule-49 banner marker, ran
  past the end of the blockquote, and reported `https://gofastmcp.com` as a rule-49 URL leak.
- **Fix:** the slice now stops at the end of the contiguous blockquote; pinned by
  `test_the_banner_block_stops_at_the_end_of_the_blockquote`.
- **Committed in:** `65b38a2`

**3. [Rule 1 — Bug] The declaration call site was looked for in the wrong module**
- **Found during:** Task 4
- **Issue:** the gate asked whether `end_of_game.py` contains `write_declaration_artifact`; the
  real production caller is `end_of_game_declaration.py`, so criterion 3 read **FAIL** for a
  mechanism that works.
- **Fix:** scan all of `src/` for call sites, **excluding the defining module** — 08-04's own
  finding (a definition is not a caller) turned into the shape of the check.
- **Committed in:** `65b38a2`

**4. [Rule 1 — Bug] The commit hash was read from the wrong depth**
- **Found during:** Task 4
- **Issue:** the artifact has no top-level `commit_hash`; it lives at
  `declarations.own.declaration.commit_hash`, so 2 of 2 retained artifacts reported as carrying
  no hash.
- **Fix:** nested read, with the field path published in the evidence JSON.
- **Committed in:** `65b38a2`

**5. [Rule 1 — Bug] The screenshot scan globbed a directory that does not exist**
- **Found during:** Task 6 (GATE-8 record)
- **Issue:** `_screenshot_slots` globbed `docs/assets/` and reported `tracked_images: 0` while
  the audit gate, asking the same question of `git ls-files`, reports **5**. A count taken over
  the wrong set is not a smaller count; it is a different question.
- **Fix:** ask `git ls-files` across the whole tree.
- **Committed in:** `4a4317a`

**6. [Rule 1 — Bug] The no-remote-verb scanner flagged its own constant, and the overall-PASS
regex flagged the record's own honest header**
- **Found during:** Tasks 4 and 6
- **Issue:** `network_verb_hits` matched the `NETWORK_VERBS = (...)` definition line, so `clean`
  could never be true; and `_OVERALL_PASS` matched
  `"**Status: GATE-8 IS NOT MET**, and nothing reads PASS"` — a check impossible to satisfy
  honestly, which is the mirror image of a check impossible to fail.
- **Fix:** skip **one named line** (never the whole file, which would blind the scan to the file
  that runs every git call); narrow the regex to a status line that *opens* with a pass, with
  controls in both directions.
- **Committed in:** `65b38a2`, `4a4317a`

---

**Total deviations:** 6 auto-fixed (all Rule 1), **every one a defect in this plan's own work,
found by running it rather than reading it.**
**Impact on plan:** none on scope. Four of the six were making a gate report the wrong verdict.

## Self-audit — the vacuity hunt

Twenty-two consecutive executors have found a vacuous test in their own work. Mine had several,
listed above. The probes that found or confirmed them:

| Probe | What it did | Result |
|---|---|---|
| A/B/C | version pin: `1.0`, drifted `VERSION`, drifted config JSON | 1 / 3 / 1 failures |
| D | planted `git_out(root, "push")` into the **real** `gate8_repos.py` | 1 failed / 14 passed, reverted |
| E | wrote `Score: 88 / 100` and a league phrase into `SELF-ASSESSMENT.md` | 2 failed / 4 passed, reverted |
| F | softened criterion 3 in the GATE-8 record to `GAMES PASS` | 1 failed / 6 passed, reverted |
| — | counter-control: the relaxed "cause was never established" regex re-run against all four **pre-change** texts | `False` on all four — the relaxation did not make it vacuous |

Every assertion added in this plan reports a **count**, not only an exit code: the version test
floors the config sweep at 28 files, the runbook test floors each runbook's citation count at 6,
the GATE-8 report exits **2** (never 0) on an empty counter snapshot, an unbuilt destination, or
an empty README.

## Gates

| Gate | Result |
|---|---|
| `uv run pytest --cov` | **2583 passed, 0 failed**, coverage **97.44%**, 203s |
| Inside each split output | **2582 passed, 0 failed**, 97.44% — the one-test difference is `test_research_docs.py::test_every_cited_commit_hash_resolves`, which **skips by design** in a split tree (verified: 12 passed / 1 skipped there), exactly as 08-09 predicted |
| `ruff check .` | 0 violations |
| `check_line_limit.sh` | exit 0; **545** tracked `.py` files scanned in each output, 0 violations |
| `check_submission.py` | **70 PASS / 3 GAP / 13 UNJUDGED**, exit 1 |
| `measure_gate8.py` | exit 0, run twice, three two-half verdicts |
| Split build | **12/12 rows in each output**, driver exit 0 |
| `uv lock --check` | exit 0 |

## `check_submission.py` movement, row by row

**69 PASS / 4 GAP → 70 PASS / 3 GAP.** One row moved, and it is exactly the one this plan owned.
No other row changed verdict in either direction — the counter-control every pass in this phase
has used.

| Row | Was | Now | Why |
|---|---|---|---|
| **T5-06** | GAP | **PASS** | the two version sources now carry the same string; Table 5 went 7 PASS / 1 GAP → **8 PASS / 0 GAP** |
| **G1-03b** | GAP | GAP | a non-curve screenshot. **Marked-absent slot**; needs one live run. **Owner: 07-10 (human)** |
| **G5-04** | GAP | GAP | screenshots of the running system: 5 tracked images, **0** not a training curve. **Owner: 07-10 (human)** |
| **G6-08** | GAP | GAP | **deliberate, and dated in the register.** `git tag -l` is empty *here* by decision (D-79). The tag exists in both split outputs, where **this same gate reports the row PASS** — run inside `pursuit-police` it returns **71 PASS / 2 GAP** with group 6 at 6 PASS / 0 GAP. **Owner: 08-11 (cut) · 08-12 (pushed, by a human)** |

The two gates disagreeing about G6-08 is the correct result: the tag exists in the tree that
will be submitted and does not exist in the tree that will not be.

## Counter delta

| Counter | Before | After |
|---|---|---|
| `config/police/games_played.json` | **1927** | **1927** |
| `config/thief/games_played.json` | **1920** | **1920** |

**Suite delta 0 / 0**, measured across a full `uv run pytest --cov`; `git diff config/` empty.
**No real game was played by 08-11.** This plan delivers a tag, three runbooks and two
documents, none of which needs one, and advancing the shipped counter to demonstrate a delta
would be a state change with no deliverable behind it. The **+1/+1 per real game** contract is
**inherited** from 07-09/08-07/08-08 and recorded as inherited, never claimed as measured here —
the same refusal 08-09 and 08-10 made.

## Issues Encountered

- **A server-side 529 interrupted the run.** Resumed by re-reading the tree rather than trusting
  memory: committed work verified on disk, the uncommitted evidence JSON inspected for
  half-writes before being trusted (it was complete).
- **`--replace` wipes the tags.** The first rebuild produced tags at `4897b48`/`18d904c`; the
  final rebuild recreated both `.git` directories and the tags had to be re-cut on the new
  HEADs. Both figures are recorded in `GATE-8-MEASUREMENT.md` rather than one silently
  overwriting the other, and `PUBLISH-RUNBOOK.md` step 2 now tells the human to re-cut after any
  rebuild — a step nobody would have known to write without hitting it.
- **The first rebuild reported 11/12** because of this plan's **own** deliberate RED test, which
  was red precisely because `GATE-8-MEASUREMENT.md` did not exist yet. Writing it closed the
  assertion and the rebuild then passed 12/12.
- **`uv.lock` still records the project version as the PEP-440-normalised `1.0.0`** and `uv lock`
  does not rewrite it; `uv lock --check` exits 0. Recorded rather than forced — and it is a
  second reason the pin compares `pyproject.toml` against `version.py` rather than dragging in a
  file whose value a tool normalises.

## Next Phase Readiness

**This is the last unattended plan of the project. Everything remaining is a human's.**

- **08-12 (publish)** is unblocked: two repositories on disk at `daa16a7` / `b0cb27b`, 12/12
  rows each, tagged `v1.00`, zero remotes. **Blocked on two answers only the owner can give:**
  OQ8-9 (is `origin` public?) and **OQ8-5 (the licence — still `AWAITING_OWNER_CONFIRMATION`;
  do not publish until it is confirmed)**.
- **08-13 (league)** additionally needs **07-10** — the authorised mail credential and the two
  screenshots that close G1-03b and G5-04.
- **08-14 (submit)** needs the form (OQ8-3), the games-played value (OQ8-2) and the score
  (OQ8-4). None of the three is an agent's.
- The two outputs are **stale by exactly this summary and the STATE update**, by construction —
  08-12 step 1 rebuilds them with one idempotent command and step 2 re-cuts the tag.

**Nothing was pushed. No repository was created. No remote was added. No tag was cut in this
repository. No remote or `gh` command of any kind was issued.**

## Self-Check: PASSED

- **28 of 28** `key-files` paths verified present **and tracked** by `git ls-files`.
- **12 of 12** commit hashes belonging to this repository resolve — the 11 task commits plus the
  08-10 baseline `4466b55`.
- **The 4 remaining hashes deliberately do NOT resolve here**, and that is the property being
  claimed: `daa16a7` resolves in `pursuit-police` and `b0cb27b` in `pursuit-thief`, and neither
  is an object in this repository — the disjoint-history row. The two superseded build commits
  (`4897b48`, `18d904c`) resolve **nowhere**, because `--replace` destroyed the repositories
  that held them; they are cited only as the superseded measurement they were, and the record
  says so.
- Both tags re-verified after the summary was written: annotated, on their own output's `HEAD`,
  tree file count **1046** = `git ls-files`, **zero remotes**, **not pushed**.
- `git tag -l` in this repository: **empty**.

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*
