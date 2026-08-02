# 03-10 Summary — §10.4 gate tests, evaluation CLI, and the run-1 GATE-4 measurement

**Plan:** `03-10-PLAN.md` · **Status:** Tasks 1–4 all executed · **GATE-4: FAIL (both roles)**
**Run 1 measured:** 2026-08-02

---

## What landed

| Task | Outcome |
|---|---|
| 1 — GATE-1/2/3 integration tests | Done (commit `1dea409`). `tests/integration/test_{shortest_path,policy_fallback,strategy_pluggable}.py` plus `scripts/check_no_llm_in_strategy.{py,sh}` as a standalone CI gate, verified to exit nonzero on a planted forbidden import |
| 2 — Evaluation CLI + fixed eval scenario set | Done (commit `8c8471f`). `training/evaluate.py` (3 arms, `--smoke`/`--full`/`--assert-gate`) + `eval_{scenarios,arms,stats,report}.py` + committed `artifacts/eval_scenarios.json` (20 scenarios, held-out seeds asserted in code) |
| 3 — STRAT coverage audit + TODO reconciliation | Done (commit `b15d033`) |
| 4 — Training run, GATE-4 measurement, table promotion | **Ran. Gate failed. Table deliberately NOT promoted.** |

## Task 4 — the run and the result

300,000 episodes (150,000 cop / 150,000 thief), `seed=1337`, config hash `5fa4d554…`,
completed uninterrupted — `run_state.json` shows `episode=300000` and all 600 curve rows are
present, so no resume gap. Artifacts landed in `%LOCALAPPDATA%\pursuit\training\` as designed
(D-22, outside OneDrive): `qtable_police.json` 39,483 keys / 3,525,039 visits,
`qtable_thief.json` 29,703 keys / 1,355,252 visits. The three operator steps from
`03-RESEARCH.md` §3 evidently held — the run neither stalled nor slept.

### GATE-4, measured on the 20 held-out eval scenarios

| Role | Learner | Baseline | Margin | Margin ≥0.10 | Floor ≥0.55 | Verdict |
|---|---|---|---|---|---|---|
| Cop | 0.250 | 0.100 | +0.150 | yes | **no** | **FAIL** (floor) |
| Thief | 0.800 | 0.900 | −0.100 | **no** | yes | **FAIL** (margin — worse than the heuristic it replaces) |

### E6 convergence — neither role converged

- **Cop:** `decile_gain=+0.848` (passes; it learned a great deal — training win rate vs the
  heuristic went 0.00 → 0.90), but `final_slope=+0.094` over the trailing 20,000 episodes.
  It was **still climbing when ε hit its floor**. The run was stopped early, not at
  convergence.
- **Thief:** `decile_gain=−0.068` — the final decile is *worse* than the first. The curve
  rises to ≈0.13 near episode 100,000, then declines to ≈0. Mean reward falls +0.283 → −0.040.

## Two findings worth carrying forward

**1. The thief regressed, and the run's own data suggests why.** Its `fallback_rate`
collapsed from 0.76 to 0.009 across training: as visit counts crossed `min_visits` (20), the
thief stopped consulting the BFS fallback and began trusting Q-values that never became
better than the fallback they displaced. Compounding it, `sparring_mix` draws a past-self
opponent 50% of the time, so the thief faced an ever-stronger cop (0.00 → 0.90) and an
increasingly all-loss training signal. Stated as a hypothesis, not a conclusion — it is
consistent with the curves but was not isolated experimentally. Config levers exist for both
halves (`min_visits`, `sparring_mix`), so the follow-up stays config-only as the plan requires.

**2. The evaluation CLI pseudo-replicates, inflating its own significance.**
`repeats_per_scenario=10` replays each scenario **identically**, because both brains are
deterministic at `epsilon_eval=0.0` — verified directly: 0 of 20 scenarios produced a
differing outcome across their 10 repeats. So `eval_games=200` carries an effective **n=20**,
and the CLI's reported `mcnemar_p≈0.0000` / `z=3.95` are wrong. Recomputed honestly on the 20
paired scenarios: **cop *p*=0.250, thief *p*=0.500 — neither significant at α=0.05.** This is
a defect in Task 2's machinery, and fixing it makes the gate **stricter**; the negative result
holds under both accountings.

## What was deliberately not done

Per `03-10-PLAN.md` Task 4 ("If the gate fails, that is a real result, not a blocker to work
around… Do not lower the bar to make it pass, and do not write an unmeasured number into the
README"):

- **No bar was lowered.** `min_win_rate_absolute` (0.55), `win_rate_margin` (0.10) and
  `significance_alpha` (0.05) are untouched.
- **No table was promoted.** `artifacts/qtable_{police,thief}.json` do not exist, so
  `test_beats_baseline_smoke_subset` still skips for want of a *blessed* table — an honest
  skip, distinct from the earlier "never trained" skip. The trained tables remain in
  `%LOCALAPPDATA%\pursuit\training\` for the retrain to resume from.
- **Every README number is measured.** The rule-42 section now embeds the three real figures
  and carries the failing numbers, including the corrected n=20 statistics.

## Phase status

Phase 3 is **not** complete. GATE-1/2/3 are met; GATE-4 is measured and failed. Three
follow-up rows are recorded in `docs/phases/phase-3/TODO.md` (T4-followup-1: retrain the cop
to convergence; T4-followup-2: diagnose the thief regression; T4-followup-3: fix the eval
pseudo-replication). The first two are config-only; the third is a correctness fix to
`training/evaluate.py`.

Repo gates at the time of writing: `ruff check .` → 0, `scripts/check_line_limit.sh` → clean,
`pytest --cov=pursuit --cov=training` → green at ≥85%.
