# Self-assessment — code quality

**Rule 55: the self-assessment score is for CODE QUALITY ONLY, and explicitly not for league
game results.** Nothing in this document mentions a win, a point, an opponent or a placing, and
that is deliberate: an evidence table that quietly credits league performance is the failure
this rule exists to prevent. The score is a claim about the software.

---

## The score

> ### Score: ______ / 100
>
> **DELIBERATELY BLANK (OQ8-4).** A numeric claim about the owner's own work is the owner's to
> make. No agent filled this in; 08-11 drafted the evidence, and the human filling the
> submission form at 08-14 writes the number. See
> [`phases/phase-8/SUBMISSION-RUNBOOK.md`](phases/phase-8/SUBMISSION-RUNBOOK.md) §4.

**Refresh the evidence before scoring** — every number below is re-derivable in two commands,
and a stale table is worse than no table:

```bash
uv run pytest --cov
uv run python scripts/check_submission.py
```

---

## 1. §19.1 Table 5 — the thirteen code-quality rows

Verdicts are `scripts/check_submission.py`'s, which re-derives each row from the tree on every
run. Twelve of the thirteen cite the §17 rows that measure them and take the **worst** verdict
among them; a cited row a run does not produce is a GAP, not a shrug.

| Row | Rule | Verdict | Evidence |
|---|---|---|---|
| T5-01 | SDK architecture — all logic through the SDK layer | **PASS** | `src/pursuit/sdk/` is the single entry point; `gui/` and the CLI are thin shells over it, enforced structurally by `tests/unit/test_gui_structural.py` |
| T5-02 | OOP / no duplication — extract at 2+ copies | UNJUDGED | a path-and-pattern gate cannot judge it; `tests/unit/doc_citation_helpers.py` and `scripts/gate7_common.py` are two real extractions made at the second copy |
| T5-03 | API gatekeeper — every external call goes through it | **PASS** | one `QuotaManager` reused as two instances; `docs/PRD_gatekeeper.md` |
| T5-04 | Rate limits in configuration, never in source | **PASS** | per-mechanism config files; no literal limit in `src/` |
| T5-05 | Overflow handling — queue, never crash | UNJUDGED (`--run-suite`) | the mail sink queues and drains; measured in `docs/phases/phase-7/gate7_measurement_evidence.json` |
| T5-06 | Version control — starts at 1.00, and the sources agree | **PASS** | closed by 08-11: `src/pursuit/shared/version.py` is the single source, `pyproject.toml` copies it, all 28 tracked config JSONs agree (bar two deliberate `weights.json` bumps), pinned by `tests/unit/test_version_single_source.py` |
| T5-07 | TDD — red → green → refactor | UNJUDGED | a work-process row. The repository's evidence is its history: RED tests committed *before* their implementation in phases 7 and 8, with the failure counts quoted in the commit messages |
| T5-08 | File size ≤ 150 code lines | **PASS** | `scripts/check_line_limit.sh` as a pre-commit hook **and** a CI job; 543 tracked `.py` files under `src/ tests/ training/` scanned, 0 violations |
| T5-09 | Linter — 0 Ruff violations | **PASS** | `ruff check .` → 0 |
| T5-10 | Test coverage ≥ 85% | UNJUDGED (`--run-suite`) | measured at **97.44%** against a `fail_under = 85` gate |
| T5-11 | Hardcoded values — 0 in source | UNJUDGED | config, `constants.py` or `Enum`; the audit cannot prove a negative by pattern |
| T5-12 | Secrets — `.env-example` + 0 in source | **PASS** | `.env-example` with dummy values, `.env` untracked and ignored, 0 credential-shaped hits in the tracked set |
| T5-13 | Package manager — everything through `uv` | **PASS** | `pyproject.toml` + `uv.lock`, no `requirements.txt` anywhere |

**Five rows are UNJUDGED and none of them is counted as a pass.** UNJUDGED means the gate
refused to judge, which outranks a green tick it could not justify.

## 2. §17 — the six audit groups

| Group | PASS | GAP | UNJUDGED | What the gaps are |
|---|---|---|---|---|
| 1 — Structure & documentation | 27 | 1 | 0 | one screenshot row, awaiting a live run (07-10) |
| 2 — Architecture & code | 7 | 0 | 3 | — |
| 3 — Testing & quality | 4 | 0 | 3 | — |
| 4 — Configuration & security | 15 | 0 | 0 | the strongest group; no gaps at any point in the audit |
| 5 — Research & visualization | 4 | 1 | 0 | the same screenshot slot |
| 6 — Extensibility & standards | 5 | 1 | 2 | the Git tag, cut in the two split outputs and pushed by a human at 08-12 |

Re-derive with `uv run python scripts/check_submission.py`; the register with the per-row
history is [`SUBMISSION-CHECKLIST.md`](SUBMISSION-CHECKLIST.md).

## 3. What the evidence does **not** cover — stated, not omitted

An honest self-assessment names the parts of the software that are unproven, because rule 42
makes an overstatement in a grader-facing document a problem in itself.

1. **Screenshots of the running system do not exist yet.** Two audit rows (G1-03b, G5-04) are
   open and are written as **marked-absent slots** rather than filled with a training curve
   dressed up as a screenshot. They need one live run at 07-10.
2. **The live mail send has been exercised once, under supervision, and every shipped config is
   `dry_run`.** The end-to-end path is measured; the day-to-day path transmits nothing.
3. **Five Table-5 rows are UNJUDGED**, above.
4. **Coverage omits `gui/`**, which is widget construction; what it renders is decided in
   `sdk/` and is covered there.
5. **One published number did not reproduce and was corrected rather than defended.** A
   thief-survival pair quoted in four artifacts read `89% → 1%`; re-measured by
   `scripts/sensitivity_reconcile.py` it is `32.0% → 7.5%`. The direction of the decision it
   supports is unchanged; the magnitude was overstated and the cause of the difference was
   never established. All four sites now say so.

## 4. Process evidence (§2.5, §8.3)

| Claim | Where a grader can check it |
|---|---|
| Documents approved before the code they describe | `docs/phases/phase-<N>/{PRD,PLAN,TODO}.md` for every phase |
| Per-mechanism PRDs | fifteen `docs/PRD_*.md` files |
| Prompt-engineering log | [`PROMPT_LOG.md`](PROMPT_LOG.md) |
| Sensitivity analysis | [`SENSITIVITY.md`](SENSITIVITY.md), rendered from `artifacts/sensitivity/` |
| Token-cost analysis | [`TOKEN-COST.md`](TOKEN-COST.md) |
| Gate measurements, per phase | `docs/phases/phase-<N>/GATE-<N>-MEASUREMENT.md` |
| Orderly Git history | conventional commits throughout; the audit measures the prefix share |

---

*Drafted by plan 08-11. The score field is filled by a human at 08-14 and by nobody else.*
