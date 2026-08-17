# Submission runbook — the form, the score, and the final push

**Owner:** 08-11 (written) · **Run by:** a human, at **08-14** · **Blocked on:** 08-12
(published) and 08-13 (games played).

> **What Claude cannot do.** No agent may **obtain or fill the submission form**, **sign a
> declaration about games played**, **set a self-assessment score**, **submit on a person's
> behalf**, **enter credentials**, **click consent**, or **send mail**. Every step below is
> **HUMAN** unless it is marked **CHECK**. This is the last runbook; nothing after it is an
> agent's.

---

## 1. Obtain the form — HUMAN

**Its location is not recorded anywhere in this repository, and no agent guessed one (OQ8-3).**
Rule 43 says "download the submission form"; neither `docs/RULES.md` nor `docs/PARAMETERS.md`
gives a URL, a Moodle location or a file name. The two addresses the project does know are
`rmisegal@gmail.com` (the lecturer) and `rmisegal+uoh26finalgame@gmail.com` (game reports) —
neither is a form location.

Find it on the course page or ask the lecturer. Then:

- fill it,
- **save as PDF**,
- **alter no field and forge nothing** (rule 43 — a bureaucratic condition for a grade, and
  forging a field is not a formatting question).

## 2. What goes in the form

| Field | Value | Source |
|---|---|---|
| Repository links (**two**) | the cop and thief URLs from 08-12 | rule 49 |
| Team identification code | **`khm-mn17`** — 8 characters, no spaces | rule 45; shipped in `config/*/security.json` |
| Games played | see step 3 — **not** a number to copy from a counter file | rule 38 |
| Self-assessment score | see step 4 — **code quality only** | rule 55 |
| Submitted by | **once per team member**; this is a solo team, so one submission | rule 44 |

`config/police/security.json` and `config/thief/security.json` both carry `khm-mn17` today, and
08-10's split verification confirms it survives into both published repositories. Read it from
there rather than retyping it.

## 3. The games-played value — HUMAN, and rule 38 is absolute

**This is the single most dangerous field on the form.** Rule 38 makes a misreported
games-played count an **absolute disqualification**, and no agent in this project has ever set,
defaulted or inferred the value.

What exists, and what it is worth:

All three are **gitignored and local to the machine that played** — none of them ships in either
published repository, so the number cannot be read off a clone.

| Source | Reading | Caveat |
|---|---|---|
| `config/police/games_played.json` | a raw counter | it counts **process runs**, not league games — one full `pytest` once advanced it by +14 |
| `config/thief/games_played.json` | a second raw counter | it **disagrees** with the police one, for two agents that have only ever played each other |
| `config/police/league_ledger.json` / `config/thief/league_ledger.json` | the derived count | D-80: the ledger is the single source of the declaration, and `games_played.json` is never read back into it |

Work through [`../phase-7/GAMES-PLAYED-RECONSTRUCTION.md`](../phase-7/GAMES-PLAYED-RECONSTRUCTION.md)
§6 (the Option A/B/C reading) and its §8 five-box checklist. Under Option A the value must lie in
**[0, 10]** to be consistent with Table 18 row 5 (max games per team = 10, **fixed**).

**The figure written on the form, the figure in the ledger, and the figure declared on the wire
in `declaration_<game_id>.json` must be the same figure.** Check all three; do not reconcile them
by editing the artifact after the fact.

## 4. The self-assessment score — HUMAN

Rule 55: the score is for **code quality only**, and explicitly **not** for league results.

[`../../SELF-ASSESSMENT.md`](../../SELF-ASSESSMENT.md) is drafted with the **score field blank**
and its evidence table is deliberately all Table-5 and §17 rows — nothing about wins, points or
opponents appears in it, so a number taken from that table cannot be a league-performance claim
by accident. Refresh its numbers first:

```bash
uv run pytest --cov
uv run python scripts/check_submission.py
```

Then write the number into the blank field, and into the form. **An agent may not write it**: it
is a numeric claim about the owner's own work.

## 5. If the code changed after 08-12 — HUMAN

Rule 41 wants the tag on the **submitted** version. If anything was committed to either
published repository after the tag was pushed:

```bash
cd C:/Users/Hp/pursuit-split-repos/pursuit-police
git tag -d v1.00                       # local
git push origin :refs/tags/v1.00       # delete the remote tag  -- HUMAN
git tag -a v1.00 -m "Submission version 1.00 -- police (cop) repository, team khm-mn17"
git push origin v1.00                  # HUMAN
```

…and the same in `pursuit-thief`. If the **version itself** changes rather than just the commit,
change it in `src/pursuit/shared/version.py` **first** — `pyproject.toml` and every config
`"version"` key are checked against that one file by
`tests/unit/test_version_single_source.py`, and the tag name is derived from it, so a hand-typed
tag that does not match will not survive the suite.

## 6. Submit — HUMAN

- One submission **per team member** (rule 44). A team of one submits once; a missing personal
  submission earns that member no grade regardless of the work.
- Keep the PDF exactly as saved.

---

## Done when

| | Evidence |
|---|---|
| The form is filled and saved as an unaltered PDF | rule 43 |
| Two repository links and `khm-mn17` are in it | rules 49, 45 |
| The games-played figure matches the ledger **and** the wire declaration | rule 38 |
| The self-assessment score is set, on code quality only | rule 55 |
| The tag points at the submitted commit in both repositories | rule 41 |
| Submitted once per team member | rule 44 |

Then Phase 8 is closed, and [`GATE-8-MEASUREMENT.md`](GATE-8-MEASUREMENT.md)'s three criteria can
be moved off PENDING — **by recording what happened, not by declaring it done.**
