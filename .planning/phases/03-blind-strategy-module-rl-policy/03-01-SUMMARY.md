---
phase: 03-blind-strategy-module-rl-policy
plan: "01"
subsystem: docs
tags: [prd, q-learning, rl-hyperparameters, doc-02, per-mechanism-prd]

# Dependency graph
requires:
  - phase: 03-blind-strategy-module-rl-policy (plan 00)
    provides: config/{police,thief}/strategy.json hyperparameter values this PRD cites verbatim
provides:
  - docs/PRD_rl_strategy.md v1.00 — the per-mechanism PRD for the Q-learning policy (DOC-02),
    written before any code under src/pursuit/strategy/ exists
  - the single unambiguous source for state-key format, Q-update equation, epsilon/alpha
    schedules, fallback trigger + distance metric, reward function, training regime and
    evaluation bar that 03-02..03-08 must match
affects: ["03-02", "03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09", "03-10"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-table parameter sourcing in every per-mechanism PRD: a PARAMETERS.md-traced game-value
      table (never altered here) and a separately labelled engineering-defaults table (D-18),
      following docs/PRD_mcp_transport.md's Sec10 house pattern"

key-files:
  created:
    - docs/PRD_rl_strategy.md
  modified:
    - docs/phases/phase-3/TODO.md

key-decisions:
  - "Documented, rather than silently followed, that the reward function's four values
    (reward_capture/survival/step/barrier_gain) are NOT reused from game_params.json's Table 17
    scoring (20/5/5/10/2) — Table 17 governs league outcomes only; the two are structurally
    different numeric scales and conflating them would put Q-update arithmetic at the mercy of a
    table this mechanism must never alter"
  - "Documented the STRAT-02 wording mismatch explicitly: REQUIREMENTS.md's fallback name is
    'Bayes + Manhattan' but the implementation contract fixed here is Bayes + barrier-aware BFS
    (D-09) — framed as a recorded, deliberate generalization (BFS degrades to Manhattan's value
    when no barrier blocks the path) rather than an undocumented drift"
  - "Split the plan's two tasks into two real commits (Sec1-6, then Sec7-10) rather than one,
    matching Task 1's own verify step ('No section beyond Sec6 yet') — required writing the file
    twice (truncated, then completed) since both tasks target the same single file"

patterns-established: []

# Metrics
duration: 6min
completed: 2026-07-31
---

# Phase 3 Plan 01: RL Strategy PRD Summary

**`docs/PRD_rl_strategy.md` v1.00 (327 lines) — the Q-learning policy's per-mechanism PRD, fixing the exact state-key format, Q-update/epsilon/alpha equations, Bayes+BFS fallback, reward table, sparring-pool training regime, and win-rate evaluation bar before any strategy code exists.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-31T16:27:22Z
- **Completed:** 2026-07-31T16:33:18Z
- **Tasks:** 2 completed
- **Files modified:** 1 created (docs/PRD_rl_strategy.md), 1 modified (docs/phases/phase-3/TODO.md, staged with the final metadata commit)

## Accomplishments
- `docs/PRD_rl_strategy.md` written and committed at Version 1.00 before any file under
  `src/pursuit/strategy/` exists (verified: directory absent both before and after this plan) —
  satisfies DOC-02 and SEGAL §2.5 step 5.
- State-key composition fixed exactly: `own_row,own_col|target_row,target_col|blocked_mask|barriers_used|turn_bucket`,
  with a worked numeric example (`2,3|5,5|9|6|1`) and the state-space arithmetic
  (49×49×16×15×3 = 1,728,720 theoretical keys vs `eval.max_table_keys=250000` as a populated-table
  health ceiling, not the same bound).
- Q-update, epsilon-decay, and alpha-decay each given as an explicit equation with every
  hyperparameter named as a `training.*`/`strategy.*` config key, never a literal.
- Fallback trigger (key-absent OR `visits < min_visits`) and the BFS-not-Manhattan deviation from
  STRAT-02's literal wording both documented with their reasons (D-08/D-09).
- Sec9's two-table split — PARAMETERS.md game values (board 7×7, barrier quota 14, move ceiling
  35, survival threshold 35, Table 17 scoring) vs a separately labelled engineering-defaults table
  covering every one of `config/{police,thief}/strategy.json`'s `[strategy]`/`[training]`/`[eval]`
  hyperparameters — cross-checked key-by-key against 03-00's actual JSON files, not invented.
- Full end-to-end digit sweep of the finished document (`grep -noE '[0-9][0-9.,×]*'`) confirmed
  every numeric literal is either a Sec9 table value, a section/rule/table citation, or part of
  the worked-example arithmetic explained inline — none unsourced.

## Task Commits

Each task was committed atomically:

1. **Task 1: PRD Sec1-6 (mechanism)** - `b4e9700` (docs)
2. **Task 2: PRD Sec7-10 (training, eval, parameters, boundaries)** - `f601e7f` (docs)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified
- `docs/PRD_rl_strategy.md` - per-mechanism PRD for the Q-learning policy: scope/requirements
  (Sec1), state encoding (Sec2), action space (Sec3), reward function (Sec4), update rule +
  exploration (Sec5), fallback (Sec6), training regime (Sec7), evaluation (Sec8), parameter
  sourcing (Sec9), boundaries/honesty (Sec10)
- `docs/phases/phase-3/TODO.md` - row 03-01 marked ☑; phase-gate line "docs/PRD_rl_strategy.md
  committed at v1.00 (DOC-02)" marked ☑

## Decisions Made
See `key-decisions` in frontmatter. No architectural decisions needed (documentation-only plan,
Rule 4 never triggered); the two entries above are documentation-accuracy calls made while
writing, not implementation choices.

## Deviations from Plan

None — plan executed exactly as written. The only departure from a literal single pass was
process, not content: to honor Task 1's own `<verify>` instruction ("No section beyond §6 yet"),
the file was written in two stages (truncated at §6, committed; then completed to §10, committed)
rather than written once and split after the fact. This produced the identical final document the
plan specifies, just via two real, separately-verified commits instead of one.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 03-02 (`BrainBase` + `Observation`/`Decision` contracts) and every later Phase-3 code plan
  (03-03…03-10) now has a single, cited source for the state-key format, the Q-update/epsilon/
  alpha equations, the fallback trigger and its BFS distance metric, the reward function, and the
  training/evaluation contract — no plan needs to re-derive or improvise any of these.
- No blockers. `src/pursuit/strategy/` remains untouched, confirming Wave 1 (documentation before
  code) held.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-07-31*

## Self-Check: PASSED

`docs/PRD_rl_strategy.md` confirmed present on disk at 327 lines with `**Version:** 1.00` in its
header (line 3). Both task commit hashes (`b4e9700`, `f601e7f`) confirmed present in
`git log --oneline --all`. `docs/phases/phase-3/TODO.md` confirmed present with row 03-01 and the
phase-gate DOC-02 line both marked `[x]`/☑.
