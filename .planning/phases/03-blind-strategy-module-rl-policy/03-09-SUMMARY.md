---
phase: 03-blind-strategy-module-rl-policy
plan: "09"
subsystem: rl-strategy-training
tags: [matplotlib, csv, learning-curves, convergence, readme, rule-42]

# Dependency graph
requires:
  - phase: 03-blind-strategy-module-rl-policy (plan 03-08)
    provides: training/curves.py's CSV writer (episode, epsilon, alpha, mean_reward,
      winrate_vs_baseline, fallback_rate, role) and the resumable run_training driver that
      calls it from episode 1
provides:
  - training/curve_analysis.py — decile_gain/final_slope/check_convergence reading that CSV,
    per-role E6 pass/fail verdicts, thresholds sourced from StrategyParams
  - training/plot_curves.py — the repo's only matplotlib importer; per-role win-rate PNGs
    (epsilon on a secondary axis) + a shared mean-reward PNG; runnable directly or via -m
  - README.md (new file) — project overview + the rule-42 learning-curves section with
    configured bar/game-count/seed and clearly marked pending placeholders
affects: [03-10 (fills the real PNGs and measured numbers into README.md after the overnight
  training run; imports training.curve_analysis.check_convergence for its GATE tests)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reader/writer split for training/ CSVs: training/curves.py only ever writes; anything
      that reads and analyzes lives in a separate sibling (curve_analysis.py), never added
      back into the writer (QUAL-02)"
    - "Direct-script sys.path bootstrap: a training/ script meant to be run both as
      `python training/<script>.py` (no -m) and imported as `training.<script>` guards a
      sys.path insert on `__package__ in (None, \"\")`, before any training.* absolute import"

key-files:
  created:
    - training/curve_analysis.py
    - training/plot_curves.py
    - tests/unit/training/test_plot_curves.py
    - README.md
  modified:
    - tests/unit/training/test_curves.py
    - docs/phases/phase-3/TODO.md

key-decisions:
  - "final_slope returns a total win-rate drift over the trailing window (regression rate x
    window span), not a raw per-episode rate — makes it directly comparable to
    convergence_tolerance (a win-rate delta, 0.02), since a 0.02-per-episode bound would be
    nonsensical over a 20000-episode window"
  - "curve_analysis.py split out of plot_curves.py at the 150-line gate (QUAL-08), the exact
    contingency the plan named ('or in a small sibling module if that file approaches 150
    lines'); plot_curves.py re-exports its public names so `training.plot_curves` still
    satisfies the plan's literal function-location spec"
  - "README.md did not exist anywhere in the repo (verified via git log) — created it now,
    borrowing .planning/PROJECT.md's heading style/opening content for the top matter, then
    added the mandatory rule-42 section; a full 'academic README' remains Phase 8 scope per
    CLAUDE.md's build order"
  - "No measured number appears in README.md's learning-curves section — every win-rate/
    game-count/seed value stated is a configured bar read from config/police/strategy.json,
    explicitly labelled as configured, not measured; every figure and verdict is marked
    'pending (03-10)' since no training run has executed yet"

patterns-established:
  - "E6 convergence verdicts are always per-role (dict[str, Verdict]), never a single
    averaged pass/fail — matches D-25's per-role curve-separation rule applied to the
    analysis layer, not just the rendering layer"

# Metrics
duration: 20min
completed: 2026-08-01
---

# Phase 3 Plan 9: Learning Curves + Plotting + README Summary

**training/curve_analysis.py's per-role E6 convergence math plus training/plot_curves.py's
matplotlib PNG renderer (the repo's only matplotlib importer), wired into a new root
README.md's rule-42 learning-curves section with configured-not-measured numbers.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-08-01T20:24:36+03:00 (immediately after 03-08's completion commit)
- **Completed:** 2026-08-01T20:44:01+03:00
- **Tasks:** 2/2
- **Files modified:** 6 (4 created, 2 modified)

## Accomplishments

- `training/curve_analysis.py`: `decile_gain`, `final_slope`, `check_convergence` reading
  `training/curves.py`'s CSV schema without touching or recreating that module (verified via
  `git diff` showing zero change across both commits)
- `training/plot_curves.py`: per-role win-rate-vs-baseline PNGs with the epsilon schedule on
  a secondary axis, plus a shared mean-reward PNG with a separately labelled line per role
  (never averaged, D-25); confirmed as the repo's sole matplotlib importer via a repo-wide
  grep, and confirmed nothing under `src/` imports it
- README.md created (did not previously exist) with the rule-42 learning-curves section:
  states the configured `win_rate_margin` (0.10), `min_win_rate_absolute` (0.55), `eval_games`
  (200 = 20 scenarios x 10 seeds), `convergence_window`/`convergence_tolerance`
  (20000/0.02), `episodes` (300000), and `seed` (1337) — every figure and measured win-rate
  explicitly marked "pending (03-10)"

## Task Commits

1. **Task 1: E6 convergence checks over the curve CSV** - `8670251` (feat)
2. **Task 2: Plotting and the README section** - `b2f851c` (feat)

**Plan metadata:** this commit (docs: complete plan)

## Files Created/Modified

- `training/curve_analysis.py` - `decile_gain`/`final_slope`/`check_convergence`/`Verdict`/
  `read_rows`; matplotlib-free, reads `training/curves.py`'s FIELDNAMES
- `training/plot_curves.py` - matplotlib rendering + CLI (`render_all`, `main`); re-exports
  `curve_analysis`'s public names; `sys.path` bootstrap for direct-path execution
- `tests/unit/training/test_curves.py` - extended (not replaced) with 6 new tests: rising/
  flat curve converges, flat-noise fails the decile check, still-climbing fails the slope
  check, per-role verdicts stay independent, plus a `read_rows` round-trip test
- `tests/unit/training/test_plot_curves.py` - new file: PNG rendering, role-skip when a role
  has no rows, the CLI's stdout contract, and a subprocess test proving the plan's literal
  `python training/plot_curves.py <csv> <outdir>` invocation form actually works
- `README.md` - new file: project overview + the rule-42 learning-curves section
- `docs/phases/phase-3/TODO.md` - row 03-09 marked done (☑)

## Decisions Made

- `final_slope`'s return value is a total win-rate drift over the window (regression rate x
  window span), not a bare per-episode rate — this was an open design choice the plan left
  unspecified ("final slope within convergence_tolerance"); numerically verified against
  three synthetic curves (rising-then-flat, flat-noise, still-climbing) before writing the
  implementation, confirming the semantics discriminate correctly
- `curve_analysis.py`/`plot_curves.py` split at the 150-line gate, matching this phase's
  established precedent (03-05 through 03-08 all split at the same gate); the E6 analysis
  tests stay in `tests/unit/training/test_curves.py` per the plan's explicit instruction,
  while the new rendering-only tests got their own `test_plot_curves.py` (a genuinely
  different module under test, not a second file for `curves.py` itself)
- README.md did not exist in the repo before this plan (confirmed via `git log --all -- README.md`
  returning nothing) — created it now rather than treating the plan's "existing structure"
  instruction as blocking; content borrows `.planning/PROJECT.md`'s framing for the top
  matter so the new file matches this project's established voice

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `uv run python training/plot_curves.py <csv> <outdir>` failed with
`ModuleNotFoundError: No module named 'training'`**
- **Found during:** Task 2, manual CLI verification per the plan's own verify step
- **Issue:** Direct-path script execution (`python training/plot_curves.py`) puts the
  script's own directory (`training/`) on `sys.path[0]`, not the repo root, so the module's
  `from training.curve_analysis import ...` absolute import could not resolve. `-m
  training.plot_curves` and pytest's own imports were unaffected — only the plan's literal
  invocation form broke.
- **Fix:** Added a guarded `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`
  at the top of `plot_curves.py`, gated on `__package__ in (None, "")` so it is a no-op under
  `-m`/pytest and only activates for direct-path execution.
- **Files modified:** `training/plot_curves.py`
- **Verification:** `uv run python training/plot_curves.py <fixture>.csv <outdir>` now
  produces the three PNGs and prints their paths; re-verified via a subprocess-based pytest
  test (`test_cli_runs_by_direct_path_uv_style`) so the fix stays regression-tested.
- **Committed in:** `b2f851c` (Task 2 commit)

**2. [Rule 3 - Blocking] `training/plot_curves.py`/analysis logic would have exceeded the
150-line gate as a single file**
- **Found during:** Task 1, before writing any code (estimated line budget up front)
- **Issue:** The plan's own text anticipated this ("or in a small sibling module if that file
  approaches 150 lines") — combining the E6 analysis functions with matplotlib rendering and
  a CLI in one file was projected to land well past 150 code lines.
- **Fix:** Split into `training/curve_analysis.py` (107 code lines, matplotlib-free) and
  `training/plot_curves.py` (which imports and re-exports the analysis names, keeping it at
  ~90 code lines including the rendering functions and CLI).
- **Files modified:** `training/curve_analysis.py` (new), `training/plot_curves.py`
- **Verification:** `bash scripts/check_line_limit.sh` clean on both files.
- **Committed in:** `8670251` (curve_analysis.py), `b2f851c` (plot_curves.py)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking)
**Impact on plan:** Both fixes were necessary for the plan's own literal success criteria
(the CLI invocation form named in the plan; the 150-line gate the plan itself anticipated).
No scope creep — no functionality was added beyond what the plan specified.

## Issues Encountered

None beyond the two deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `training/curve_analysis.check_convergence(rows, params)` is ready for 03-10's GATE tests
  to import directly against a real (or fixture) `curves.csv`
- `training/plot_curves.render_all(csv_path, outdir)` is ready for 03-10 to call once the
  overnight training run produces a real `artifacts/<run>/curves.csv`
- README.md's learning-curves section has the exact structure 03-10 needs to fill in: three
  named PNG paths (`artifacts/curves/winrate_cop.png`, `winrate_thief.png`,
  `mean_reward.png`) and four "*pending (03-10)*" measured-number slots per role
- No blockers. 03-10 (§10.4 gate tests + coverage audit + the actual overnight run) is the
  final Phase-3 plan.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-01*

## Self-Check: PASSED

All claimed files found on disk (`training/curve_analysis.py`, `training/plot_curves.py`,
`tests/unit/training/test_plot_curves.py`, `README.md`, `tests/unit/training/test_curves.py`,
`docs/phases/phase-3/TODO.md`) and both task commits (`8670251`, `b2f851c`) verified present
in `git log`.
