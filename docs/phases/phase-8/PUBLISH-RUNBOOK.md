# Publish runbook — creating and pushing the two submission repositories

**Owner:** 08-11 (written) · **Run by:** a human, at **08-12** · **Prerequisite:** 08-10's build
and 08-11's tag, both already on disk.

> **What Claude cannot do, stated once and meant throughout this file.** No agent in this
> project may **enter credentials**, **click a consent screen**, **create a GitHub repository**,
> **add a remote**, **push**, **push a tag**, or **send mail**. Every step below that does one of
> those is marked **HUMAN**. The steps marked **CHECK** are local reads a human can run, or ask an
> agent to run, at any time. 08-10 and 08-11 between them created two repositories on disk with
> **zero remotes** and one annotated tag each, and issued **no remote command of any kind**.

Rule 41 (a tag on the submitted version), rule 49 (two cross-linked public repositories) and
rule 50 (what each must contain) are closed by this runbook and by nothing else.

---

## 0. Before anything — the two blockers

**Neither is negotiable and neither is an agent's to answer.**

| Blocker | Why it comes first | Where the material is |
|---|---|---|
| **OQ8-9 — is `origin` public or private?** | If `https://github.com/khaledmanaa11/AI_ORCHISTRATION_final_project.git` is already **public**, then everything this repository has ever tracked is already published, and the secrets question stops being preventive and becomes urgent. | Open the URL while signed out of GitHub. Public if it loads. |
| **OQ8-5 — the licence** | `LICENSE` is drafted (MIT) and carries a **`PREPARED, NOT ADOPTED`** block; `docs/SUBMISSION-CHECKLIST.md` carries **`LICENCE STATUS: AWAITING_OWNER_CONFIRMATION`**. A licence is a legal declaration about the owner's own coursework. **Do not publish until the owner confirms.** | `LICENSE`, and the licence section of `docs/SUBMISSION-CHECKLIST.md` |

A biconditional test fails if either of those two markers changes without the other, so removing
one and forgetting the other breaks the suite rather than shipping quietly.

**An observation recorded rather than acted on.** During phases 7 and 8 this repository's
`origin/main` moved **without any agent pushing it** — verified on 2026-08-14 and 2026-08-16,
with no pushing git hook in the tree. Something outside this repository pushes it on a delay.
Two consequences for this runbook: (1) do not assume `origin` is under manual control when
answering OQ8-9; (2) **08-11 deliberately did not cut a tag in this repository**, only in the two
split outputs, because a local tag here could be swept outward by that process. See
`docs/phases/phase-8/GATE-8-MEASUREMENT.md` criterion 1.

---

## 1. Rebuild the two outputs — CHECK

The outputs on disk are one or more commits behind by construction: every plan's own summary
lands after the build it describes. The build is idempotent and is one command.

```bash
uv run python scripts/build_split_repos.py --dest C:/Users/Hp/pursuit-split-repos --replace --gates \
    --json docs/phases/phase-8/split_build_evidence.json
```

Exit 0 means every row of every output passed, including `uv sync`, `ruff check .`,
`pytest --cov` and the line-limit scan **inside each output**. Exit 2 means the build produced
no rows and is **not** a pass. Full detail: [`SPLIT-RUNBOOK.md`](SPLIT-RUNBOOK.md).

**`--replace` deletes and rewrites the output trees, and that deletes their tags.** Re-cut the
tag after any rebuild — step 2.

## 2. Re-cut the tag in each output — CHECK

The tag name is **derived** from `src/pursuit/shared/version.py` (`VERSION = "1.00"`), never
chosen: `v1.00`. `pyproject.toml` carries the same string, pinned by
`tests/unit/test_version_single_source.py`.

```bash
cd C:/Users/Hp/pursuit-split-repos/pursuit-police
git tag -a v1.00 -m "Submission version 1.00 -- police (cop) repository, team khm-mn17"
cd ../pursuit-thief
git tag -a v1.00 -m "Submission version 1.00 -- thief repository, team khm-mn17"
```

Then verify, from this repository:

```bash
uv run python scripts/measure_gate8.py
```

Criterion 1 must read `BUILT+TAGGED PASS; PUBLISHED PENDING (08-12)`. The gate checks that each
tag is **annotated**, points at that output's `HEAD`, and lists exactly as many files as
`git ls-files` reports — a tag on the wrong commit is the failure this row exists to catch.

## 3. Create the two public repositories — **HUMAN**

Two repositories, named to match the two outputs. Nothing else about them is prescribed by the
rules; keep the names distinguishable and stable, because they go into the submission form
(rule 49) and into `config/*/league.json`.

- `pursuit-police` — the **cop** agent
- `pursuit-thief` — the **thief** agent

Create them **empty** — no README, no `.gitignore`, no licence chosen in the GitHub UI. Each
output already contains all three, and an auto-generated file makes the first push a conflict.

## 4. Add a remote and push — **HUMAN**

```bash
cd C:/Users/Hp/pursuit-split-repos/pursuit-police
git remote add origin <the police repository URL>
git push -u origin main
git push origin v1.00

cd ../pursuit-thief
git remote add origin <the thief repository URL>
git push -u origin main
git push origin v1.00
```

**Type these in the output directories, never in the development repository.** The outputs live
outside this tree precisely so that a `git push` typed in the wrong window cannot reach a public
URL: this repository's `main` is well over a hundred commits ahead of its own remote and its
history is private working history.

Push the tag **explicitly by name**, as above. `git push --tags` in the wrong window is the
irreversible mistake this whole phase is arranged to avoid.

## 5. Fill the four real links — **HUMAN**, then CHECK

Rule 49 wants two links in the form and **four** links in both teams' JSON. Four slots are named
individually in `config/police/league.json` and `config/thief/league.json`; all four read `null`
today, which the loader renders as a stated-absent marker and **refuses** when
`reporting.mode = live`.

1. Set `league.repo_urls.own_cop` and `own_thief` in **both** roles' `league.json` to the two
   URLs from step 3. Leave `opponent_cop`/`opponent_thief` `null` until league day.
2. Replace the stated-absent markers in each output's `README.md` cross-link banner with the two
   real URLs — **both** READMEs name **both** repositories.
3. Re-run the audit and the tests:

```bash
uv run pytest tests/unit/test_league_config.py tests/unit/test_split_verify.py -q
uv run python scripts/check_submission.py
```

## 6. Re-run the publication scan against the pushed trees — CHECK

There is **no** `check_publication_safety.py` in this repository; the scan is group 4 of the
audit gate (`scripts/submission_security.py`, 15 rows, currently 15 PASS / 0 GAP) plus
`tests/unit/test_publication_ignore_rules.py`. Run both **inside a fresh clone of each pushed
repository**, not in the output directory you pushed from:

```bash
git clone <the police repository URL> /tmp/verify-police && cd /tmp/verify-police
git config core.hooksPath scripts/hooks
uv sync && uv run python scripts/check_submission.py && uv run pytest --cov
```

A fresh clone is the point. 08-10 found **four** tests that asserted the developer's untracked
files rather than the repository — including a rule-38 README leak detector that searched an
**empty** value set in every clone and therefore guarded nothing. They pass in a clone now
because that was fixed; re-running here is how it stays fixed.

Confirm by eye, in the clone: no `.env`, no `police_thief_p2p.pdf`, no `requirements.txt`, no
`config/*/games_played.json`.

## 7. Send the D7-17 question to the lecturer — **HUMAN**

The question is drafted and **unsent**:
[`D7-17-QUESTION-FOR-THE-LECTURER.md`](D7-17-QUESTION-FOR-THE-LECTURER.md). Send it to
`rmisegal@gmail.com` from the human's own mail client. **No agent may send it** — mailing the
lecturer is an outward act under a person's identity. Record the date sent at the top of that
file when it goes.

---

## Done when

| | Evidence |
|---|---|
| Both repositories reachable and public | opened while signed out |
| Each README cross-links the other, with real URLs | rule 49 |
| `v1.00` visible on both, on the pushed `main` | rule 41 |
| `league.json` holds the two own-team URLs in both roles | `check_submission.py` placeholder row |
| A fresh clone of each passes `ruff`, `pytest --cov`, the line-limit gate and the audit | Table 5, inside the published tree |
| The D7-17 question is sent and dated | OQ8-1 |

Then: [`LEAGUE-RUNBOOK.md`](LEAGUE-RUNBOOK.md) (08-13), which additionally needs **07-10**.
