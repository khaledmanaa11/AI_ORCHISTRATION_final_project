# GATE-8 measurement — Phase 8, the submission gate

**Status: GATE-8 IS NOT MET, AND NOTHING BELOW READS PASS.** All three criteria are
**structurally human-completed**: publishing two repositories, filling and submitting a form
PDF, and playing scored games against real opponent teams. Each criterion below is therefore
reported as **two named halves** — the half measured on this machine, and the half a human
closes — and the criterion-level verdict is the string that joins them, so that a search for
`PASS` cannot land on a criterion nobody has finished.

| Criterion | Measured half | Human half | Whose |
|---|---|---|---|
| 1 — two cross-linked public repos + tag | **BUILT + TAGGED PASS** | **PUBLISHED PENDING** | 08-12 |
| 2 — academic README, screenshots, form PDF, per member | **README PASS** | **SCREENSHOTS PENDING** · **FORM + SUBMISSION PENDING** | 07-10 · 08-14 |
| 3 — ≥ 2 scored games vs different teams, reported with the commit hash | **MACHINERY PASS** | **GAMES PENDING** | 08-13 (needs 07-10) |

The three criterion verdicts, quoted verbatim from
[`gate8_measurement_evidence.json`](gate8_measurement_evidence.json) so this record cannot
drift from the run that produced it (`tests/unit/test_gate8_record.py` re-reads them):

```
criterion_1: BUILT+TAGGED PASS; PUBLISHED PENDING (08-12)
criterion_2: README PASS; SCREENSHOTS PENDING (07-10); FORM+SUBMISSION PENDING (08-14)
criterion_3: MACHINERY PASS; GAMES PENDING (08-13, needs 07-10)
```

**Date:** 2026-08-17 · **Plan:** 08-11 · **Method:** `scripts/measure_gate8.py`, plus
`scripts/build_split_repos.py --gates` for criterion 1's inside-the-output gates and
`scripts/check_submission.py` for criterion 2's row verdicts.

This is the `GATE-7-MEASUREMENT.md` criterion-1 precedent and the `GATE-5-MEASUREMENT.md`
criterion-2 precedent applied to a whole gate: **a gate that reports PASS on the strength of
preparation is worthless**, and this project has twice held a criterion at PENDING across days
rather than soften it. Three of the six halves here are PENDING and stay PENDING until someone
has actually done them.

**The exit code says less than this document does.** `measure_gate8.py` exits **0** when the
three *measurable* halves pass — it is a preparation check, not a verdict on GATE-8. Exit 1 is
a real failure and exit 2 is an evidence set that judged nothing, which outranks a run that
found real failures (`scripts/gate8_report.py::GateExit`).

---

## The three criteria — quoted verbatim from `.planning/ROADMAP.md` Phase 8

> **Success Criteria** (submission gate):
>
> 1. Two cross-linked public repos (cop, thief), each carrying README/config/PRD/PLAN/TODO,
>    with a Git tag on the submitted version
> 2. Academic README with its six mandatory sections (incl. learning curves and `Verified OK`
>    screenshots); submission form filled and saved as PDF, submitted per team member
> 3. At least 2 scored league games played against different teams and reported, each game
>    emailing the commit hash it ran on

---

## Criterion 1 — two cross-linked public repositories, each with a Git tag

**Method.** Two commands. The first rebuilds both outputs from `git ls-files` into a
destination **outside** this tree (D-76) and runs `uv sync`, `ruff check .`, `pytest --cov` and
the line-limit scan **inside each output**; the second measures what was built.

```bash
uv run python scripts/build_split_repos.py --dest C:/Users/Hp/pursuit-split-repos --replace --gates \
    --json docs/phases/phase-8/split_build_evidence.json
uv run python scripts/measure_gate8.py
```

**What a PASS looks like — the measured half.** Every field below must hold, per output, for
`built_and_tagged_verdict: PASS`:

| Field | Must be |
|---|---|
| `exists`, `commit_count`, `clean_worktree` | present, exactly one commit, nothing uncommitted |
| `tracked_file_count` | **> 0** — a count, because an empty tree passes every structural check trivially |
| `remote_count` | **0** — the evidence that nothing has been published from here |
| `rule50` | README / config / PRD / PLAN / TODO all **> 0**, counted not asserted |
| `cross_link.banner_present`, `.names_the_other_repository`, `.repo_split_doc_tracked` | all true (rule 49) |
| `cross_link.urls_in_banner` | **empty** — both rule-49 links are stated-absent markers until 08-12, never guessed URLs |
| `tag.exists`, `.annotated`, `.points_at_head` | true — an annotated tag on that output's own `HEAD` |
| `tag.tree_file_count` | **equal to `tracked_file_count`** — a tag on the wrong commit is what this row exists to catch |
| `tag.pushed` | **false** |

**Measured — 2026-08-17.** `built_and_tagged_verdict: PASS`, `published_verdict: PENDING`.

| Field | `pursuit-police` | `pursuit-thief` |
|---|---|---|
| Root | `C:\Users\Hp\pursuit-split-repos\pursuit-police` | `...\pursuit-thief` |
| HEAD | `4897b48` | `18d904c` |
| Commits · clean worktree | 1 · yes | 1 · yes |
| Tracked files | **1043** | **1043** |
| **Remotes** | **0** | **0** |
| rule 50 | README 1 · config 28 · PRD 16 · PLAN 103 · TODO 10 | identical |
| Cross-link banner | present, 25 lines, names the other repository, **0 URLs** | identical |
| **Tag** | **`v1.00`**, annotated, at `4897b48205caf16fb4e223e29dbfc0b102706f85` | **`v1.00`**, annotated, at `18d904cf4978b6ba43071cca837cfc859c2ea5f6` |
| Tag tree file count | **1043** — equal to `git ls-files` | **1043** — equal |
| **Pushed** | **no** | **no** |

Gates **inside each output** (`split_build_evidence.json`): `uv sync` exit 0 · `ruff check .`
exit 0 · line-limit **544 tracked `.py` files scanned, 0 violations** · forbidden paths **7
names checked, 0 present, 0 tracked** · both seats' config present (14 files each) with **0
counters carried** · history disjoint from this repository · `pytest --cov` **2574 passed,
coverage 97.44%** against `fail_under = 85`.

**The tag name is derived, not chosen (D-79).** `v` + `src/pursuit/shared/version.py`'s
`VERSION`. Until this plan, `pyproject.toml` disagreed with that file (`1.00.0` against
`1.00`), which is why D-79 required the reconciliation to land first — a tag derived from the
wrong one of two literals names a version half the repository denies. T5-06 is now PASS and
`tests/unit/test_version_single_source.py` holds the two together, comparing **raw strings**
because `1.00` and `1.0` are the same PEP-440 version and two different tag names.

### What was deliberately NOT done, and why

**No tag was cut in this repository, and none will be by an agent.** `git tag -l` here returns
nothing; `development_repo_is_deliberately_untagged: true` in the evidence. Two reasons:

1. **D-79.** The tag belongs on the submitted artifact. This repository's `main` is well over a
   hundred commits ahead of a remote that is not the submission target, and its history is
   private working history.
2. **A measured hazard.** This repository's `origin/main` has moved **with no agent pushing
   it** — observed 2026-08-14 and 2026-08-16, with no pushing git hook in the tree. A local tag
   here could therefore be carried outward by a process nobody in this session controls. The
   two outputs have **zero remotes** and live outside this tree, so a tag in them cannot leave
   the machine by accident.

**No remote command of any kind was issued.** `scripts/measure_gate8.py` reports
`no_remote_command_was_issued.network_verb_hits_in_this_package: {}` — a scan of its own source
for `push`/`fetch`/`pull`/`clone`/`remote add`/`gh`, fired on a planted `push` line first
(`tests/unit/test_gate8_measure.py`) so that an all-clear means something.

**The row the two gates disagree about, and why that is correct.** Run inside
`pursuit-police`, `scripts/check_submission.py` reports **71 PASS / 2 GAP** with **G6-08 PASS**
(group 6: 6 PASS / 0 GAP). Run here it reports **70 PASS / 3 GAP** with **G6-08 GAP**. Both are
right: the tag exists in the tree that will be submitted and does not exist in the tree that
will not be.

**Published — PENDING (08-12).** Creating a GitHub repository, adding a remote and pushing are
outward, irreversible acts behind a person's account and consent screen. Procedure:
[`PUBLISH-RUNBOOK.md`](PUBLISH-RUNBOOK.md).

---

## Criterion 2 — academic README, screenshots, submission form as PDF, per member

**Method.** `scripts/measure_gate8.py` reads each **built output's** `README.md` and asks
`tests/unit/readme_contract_checks.py` — the module the README contract itself uses, imported
rather than retyped — for the §9.4.2 six sections and §2.1's seven items. The screenshot and
form halves are counted and reported, never judged PASS.

**What a PASS looks like — the measured half.** For `readme_sections_verdict: PASS`, in **both**
outputs: `readme_bytes > 0`, `missing_academic_942_headings == []`,
`missing_segal_21_headings == []`, and `academic_sections_expected > 0`.

**Measured — 2026-08-17.** `readme_sections_verdict: PASS`.

| Field | `pursuit-police` | `pursuit-thief` |
|---|---|---|
| README bytes | 31347 | 31346 |
| Missing §9.4.2 sections (of 6) | **none** | **none** |
| Missing §2.1 items (of 7) | **none** | **none** |

**Screenshots — PENDING (07-10).** Tracked images: **5**, of which **0** are not a training
curve. Audit rows **G1-03b** and **G5-04** are open and are written as **marked-absent slots**;
08-06 refused to relabel a learning curve as a screenshot of the running system. They need one
live run with a human at the keyboard.

**Submission form — PENDING (08-14), and its location is not known.** Rule 43 says "download
the submission form"; **OQ8-3** records that neither `docs/RULES.md` nor `docs/PARAMETERS.md`
gives a URL, a Moodle location or a file name, and **no location was guessed**. Fill-in notes:
[`SUBMISSION-RUNBOOK.md`](SUBMISSION-RUNBOOK.md).

**Per-member submission — PENDING (08-14).** Team code `khm-mn17`, one member.

**Self-assessment score — PENDING (08-14), OQ8-4.**
[`../../SELF-ASSESSMENT.md`](../../SELF-ASSESSMENT.md) is drafted with the score field **blank**
and an evidence table that is deliberately all Table-5 and §17 rows, so a number taken from it
cannot be a league-performance claim by accident (rule 55).
`tests/unit/test_self_assessment.py` fails the moment a digit appears in that field.

---

## Criterion 3 — at least two scored league games against different teams

**Method.** `scripts/measure_gate8.py` reads the per-role league ledger through the shipped
`read_ledger`/`count_reading` API, compares it against Table 18's two **fixed** bounds as the
code holds them, and checks that the mechanism which carries the commit hash onto the wire has
a **production caller** — 08-04's finding, kept as a verdict.

**What a PASS looks like — the measured half.** For `machinery_verdict: PASS`: a production
call site for `write_declaration_artifact` outside its defining module; at least one retained
declaration artifact; **every** retained artifact carrying a commit hash; `minimum_games > 0`;
`max_games_per_team >= minimum_games`; and no role's scored count above the maximum.

**Measured — 2026-08-17.** `machinery_verdict: PASS`, `games_played_verdict: PENDING`.

| Field | Measured |
|---|---|
| Production call site | `src/pursuit/services/reporting/end_of_game_declaration.py` |
| Retained declaration artifacts | 2 — `police_declaration_397b3503b1bfa996.json`, `thief_declaration_397b3503b1bfa996.json` |
| Carrying a commit hash | **2 of 2**, at `declarations.own.declaration.commit_hash` |
| The hash both carry | `e67283841ac23e0f32bad7b7d63f99c56dc7a3f1` |
| Bounds | minimum **2** (Table 18 row 3, fixed) · maximum **10** per team (row 5, fixed) |
| Ledger, police / thief | **0 scored, 0 total, 0 distinct opponents** — no ledger file exists yet |

**Scored games — PENDING (08-13, and blocked on 07-10).** Arranging real opponent teams is not
something an agent can do, and **rule 35 zeroes both teams** when either fails to report or the
two reports contradict each other — so no game was played here to demonstrate a delta.
Procedure: [`LEAGUE-RUNBOOK.md`](LEAGUE-RUNBOOK.md).

**Games-played declaration — PENDING (08-14), OQ8-2.** The rule-38 value is not an agent's to
pick, and none of the four plans in this wave set, defaulted or inferred one.

---

## The rule-38 counter, across this measurement

`games_played` before and after every command in this record:

| Counter | Before | After |
|---|---|---|
| `config/police/games_played.json` (gitignored, local) | **1927** | **1927** |
| `config/thief/games_played.json` (gitignored, local) | **1920** | **1920** |

`unchanged_by_this_measurement: true`, and `git diff config/` is empty. A **full**
`uv run pytest --cov` in this repository moved them **0 / 0**, and **no real game was played by
08-11** — this plan delivers a tag, three runbooks and two documents, none of which needs one.
The +1/+1 per real game contract is **inherited** from 07-09/08-07/08-08 and recorded as
inherited, never re-claimed here.

---

## Why none of the three criteria can be closed from this repository alone

Criterion 1 needs a GitHub account and an outward push; criterion 2 needs a form nobody has
located and a personal submission; criterion 3 needs a second team. These are not testing gaps
to be closed with more mocking — they are the literal content of the criteria, exactly as
`GATE-5-MEASUREMENT.md` §"Why criterion 2 cannot be scripted from this repository alone"
argued for the remote round. What **can** be true before a human acts is true and measured
above; what cannot, says PENDING and names who closes it.

---

*Phase: 08-submission-and-league-operations · Plan: 08-11*
*Evidence: [`gate8_measurement_evidence.json`](gate8_measurement_evidence.json) ·
[`split_build_evidence.json`](split_build_evidence.json) ·
[`submission_audit_evidence.json`](submission_audit_evidence.json)*
