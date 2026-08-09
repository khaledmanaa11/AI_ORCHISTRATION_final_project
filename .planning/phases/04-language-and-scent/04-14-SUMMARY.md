---
phase: 04-language-and-scent
plan: "14"
subsystem: testing
tags: [gate-4, measurement, anthropic-haiku-4-5, reproducibility, honesty-clause, scent-decay, belief-map]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plan 04-12)
    provides: "the live turn-pipeline integration (Figure 7) and turn_events.language_turn_record JSONL fields this measurement reads"
  - phase: 04-language-and-scent (plan 04-13)
    provides: "docs/phases/phase-4/{PRD,PLAN,TODO}.md and RULES-RESOLUTION-LANG.md this measurement's write-up sits alongside"
provides:
  - "scripts/measure_gate4.py + 7 helper modules: a seeded, reproducible GATE-4 measurement CLI, --mocked (default, no key) and --live (real API, refuses to attempt anything without a key)"
  - "docs/phases/phase-4/GATE-4-MEASUREMENT.md: all three Sec10.4 criteria quoted verbatim from ROADMAP.md, each with a measured number, method and verdict; live section PENDING with the exact rerun command"
  - "tests/integration/test_gate4.py: the gate's structural absolutes frozen as a mocked, no-key, no-network CI regression test"
affects: [phase-5-cloud-exposure, phase-6-security, phase-7-reporting-shell]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Measurement-by-spying, never by editing: scripts/gate4_beliefspy.py wraps BeliefAdapter.decide (unmodified) to read self.belief.posterior() before/after each call, rather than adding instrumentation to strategy/beliefadapter.py -- the measurement describes the shipped game, not a special build"
    - "Reuse the real two-peer harness (tests/integration/two_peer_game.play_two_peer_game) for measurement AND for the frozen test, rather than a third hand-rolled runner (RESUME.md carry-over W)"
    - "A criterion the JSONL does not literally carry (scent decay values; intent-vs-text ordering) is measured against the shipped production objects/call-graph directly instead, with the substitution documented as a stronger guarantee than a log-timestamp diff would give, not a weaker one"
    - "Guarded sys.path bootstrap (__package__ in (None, ''), matching training/plot_curves.py's Phase-3 precedent) lets a scripts/ entry point import pursuit.*/tests.* without a scripts/__init__.py"

key-files:
  created:
    - scripts/measure_gate4.py
    - scripts/gate4_games.py
    - scripts/gate4_beliefspy.py
    - scripts/gate4_scent.py
    - scripts/gate4_mockprovider.py
    - scripts/gate4_fixtures.py
    - scripts/gate4_report.py
    - scripts/gate4_runner.py
    - tests/integration/test_gate4.py
    - docs/phases/phase-4/GATE-4-MEASUREMENT.md
    - docs/phases/phase-4/gate4_measurement_mocked.json
    - docs/phases/phase-4/gate4_measurement_live.json
  modified: []

key-decisions:
  - "Scent decay (criterion 2) has no per-turn JSONL field to mine -- 04-12 logs belief entropy/argmax/reliability, never the scent grid. Measured instead by driving the shipped ScentField/scent.py directly with the locked, loaded scent.json (the same objects and functions a real game calls), compared against the closed-form scent.expected_strength_after() -- documented as the faithful reading of 'not a special build' for a quantity the log does not carry."
  - "Intent-before-text (criterion 3) is proven structurally, not from a log timestamp: turn_language_io.send_turn_hint calls build_deception_plan() (fixes plan.intent) before compose_outgoing(plan, ...) -- plan is a required positional argument, so no call producing hint text can exist without an intent already decided. The JSONL fuses text+intent into one record once both exist, so there is no pair of timestamps to diff; the structural proof is stronger, not a fallback."
  - "Belief-on/off comparison reported as measured (1.0 vs 0.0 cop win rate), NOT smoothed into the outline's 'no gain' prediction. Root-caused: network/turn_language.py's belief.enabled=false fallback hands the raw brain the TRUE current opponent cell (ctx.state directly), not a blind one -- pre-dating D-48/D-43 and never updated. The comparison measures belief vs omniscience, not belief vs blindness; documented as an honest methodological gap, not fixed (out of a measurement plan's scope to change strategy code)."
  - "Anthropic's Haiku 4.5 pricing ($1/$5 per MTok input/output) is a cited script constant, not sourced from docs/PARAMETERS.md -- that file governs only the book's own game numerics. Flagged for reconfirmation before Phase 7's league spend email."
  - "--live attempts ZERO network calls when ANTHROPIC_API_KEY is absent -- checked and returned before building any config, provider, or game -- and this was empirically verified this session, not just asserted, by actually invoking --live with no key set."

patterns-established:
  - "GATE measurement scripts belong in scripts/, split at the 150-line gate same as production code, and reuse the real two-peer harness rather than a bespoke one -- this is the shape any later GATE re-measurement (a re-run before league games, or a Phase 5/6 regression check) should follow."

requirements-completed: [LANG-01, LANG-04, LANG-05, LANG-06, LANG-07]

# Metrics
duration: ~50min (approximate; no precise session-start timestamp captured, same caveat as 04-12-SUMMARY.md)
completed: 2026-08-09
---

# Phase 4 Plan 14: GATE-4 Measurement Summary

**GATE-4's three §10.4 criteria measured with real numbers via a seeded, reproducible two-peer harness — all PASS in `--mocked` mode; the plan's own live-API requirement (D-32) is honestly reported as PENDING rather than faked, with the exact rerun command a human needs.**

## Performance

- **Duration:** ~50 min (approximate)
- **Completed:** 2026-08-09
- **Tasks:** 3/3
- **Files:** 12 created, 0 modified

## Accomplishments

- `scripts/measure_gate4.py` + 7 helper modules — a seeded (`GATE4_SEEDS = (30260801, 30260802, 30260803)`), reproducible GATE-4 measurement CLI reusing 04-12's `play_two_peer_game` (not a third hand-rolled harness). `--mocked` (default) never touches a network — verified by re-running it twice and diffing the output: every criterion number was byte-identical, only wall-clock timing differed. `--live` was actually invoked with no key present and correctly attempted zero network calls, writing a clean `PENDING` JSON rather than silently falling back to template numbers.
- Criterion 1 (hint → inference): `scripts/gate4_beliefspy.py` spies the real, **unmodified** `BeliefAdapter.decide` to read `self.belief.posterior()` immediately before/after each call. Measured: 22/136 decision points across both roles carried evidence; mean absolute posterior L1 shift on exactly those 22 turns was **1.171** (a large, non-trivial reallocation of mass on a distribution that sums to 1). No-evidence turns showed exactly 0.0 shift, by construction.
- Criterion 2 (scent decay, locked): the network event log carries no per-turn scent-field snapshot, so `scripts/gate4_scent.py` drives the shipped `ScentField`/`strategy/scent.py` directly with the locked, loaded `scent.json` — max deviation from the closed-form decay law was **1.11×10⁻¹⁶** (machine noise) over 12 decay-only turns. The real `scent_digest()` on both `config/police/scent.json` and `config/thief/scent.json` matched exactly (`c0e63220b3…`), the same digest 04-01/RESUME.md's own wave-1 table already recorded — an independent cross-check.
- Criterion 3 (hint every turn): 68/68 police-side turns carried a hint, max 11 words (limit 15), both `intent` values occurred (55 lie / 13 truth), zero outgoing coordinate leaks across every hint text and every move payload, and intent-before-text proven structurally at 1.0 (see key-decisions).
- `docs/phases/phase-4/GATE-4-MEASUREMENT.md` quotes all three §10.4 criteria verbatim from `.planning/ROADMAP.md`, gives each a number/method/verdict, reports decode-fixture accuracy (1.0/1.0 EN/HE, explicitly labelled a re-validation-logic check in mocked mode, not a live-model proof), and reports the belief-on/off comparison **honestly** — the measured 1.0-vs-0.0 cop win rate does not match the outline's "no gain" prediction, and the doc explains the real (confounded) reason why rather than smoothing it over.
- `tests/integration/test_gate4.py` freezes the gate's structural absolutes (handshake digest match, hint-every-turn + zero coordinates, intent-before-text via a live call-order spy) as 3 mocked, no-key, no-network tests. Empirically verified this session (via a throwaway, discarded probe silencing one side's hint channel) that the exact assertion this suite makes genuinely fails when the property it guards is broken.

## Task Commits

Each task was committed atomically:

1. **Task 1: the measurement script** — `64e59b3` (feat)
2. **Task 2: run it, live and mocked** — `371c1b8` (docs)
3. **Task 3: freeze the gate as a test** — `c125833` (test)

**Plan metadata:** committed alongside this SUMMARY.

## Files Created/Modified

- `scripts/measure_gate4.py` — CLI entry: `--mocked`/`--live`, sys.path bootstrap, writes the JSON result, prints a summary
- `scripts/gate4_games.py` — seeded two-peer game runner (belief on/off, seed injection via `dataclasses.replace`), per-turn wall time and coordinate-leak scan straight from the JSONL
- `scripts/gate4_beliefspy.py` — the criterion-1 posterior-delta spy (context manager, patches and restores `BeliefAdapter.decide`)
- `scripts/gate4_scent.py` — criterion-2 decay-law check + real handshake digest comparison
- `scripts/gate4_mockprovider.py` — `RecordedResponseProvider` (fixture-driven decode responses, fixed bluff phrase bank, own call/token counters since it bypasses the gatekeeper)
- `scripts/gate4_fixtures.py` — decode-fixture accuracy scoring, mocked and live variants
- `scripts/gate4_report.py` — assembles the JSON result, computes verdicts from numbers, Haiku 4.5 cost calc
- `scripts/gate4_runner.py` — the two run modes (`run_mocked`/`run_live`), live's key-absence short-circuit
- `tests/integration/test_gate4.py` — 3 frozen structural-absolute tests
- `docs/phases/phase-4/GATE-4-MEASUREMENT.md` — the write-up
- `docs/phases/phase-4/gate4_measurement_mocked.json` — raw mocked-mode result
- `docs/phases/phase-4/gate4_measurement_live.json` — raw live-mode result (currently the PENDING stub)

## Decisions Made

See `key-decisions` in the frontmatter for the full list with rationale. The one with the widest blast radius: the belief-on/off comparison's confound (§`turn_language.py`'s `belief.enabled=false` fallback being omniscient, not blind) is a genuine finding about existing 04-11/04-12 code, surfaced by this measurement plan but explicitly **not fixed** here — fixing it would mean changing strategy code from inside a measurement-only plan, which is out of scope. It is recorded in RESUME.md carry-over BB for whichever future plan touches that fallback path next.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Mocked-mode token spend read from the wrong accounting object, always showing zero**
- **Found during:** Task 1, first `--mocked` run
- **Issue:** `RecordedResponseProvider` bypasses `AnthropicProvider` entirely (it stands in for it), so it never passes through `Gatekeeper.submit()` — the real budget-accounting call site. Reading `ctx.language.gatekeeper.budget.report()` for the mocked path therefore always returned `calls=0, input_tokens=0, output_tokens=0`, silently hiding the simulated spend the plan asked to be reported.
- **Fix:** `RecordedResponseProvider` now tracks its own `calls`/`input_tokens`/`output_tokens` and exposes a `.report()` method mirroring `TokenBudget.report()`'s shape; `gate4_games.py` reads from the provider directly (not the gatekeeper) when `mocked=True`. Clearly labelled `"level": "full (simulated)"` and a top-level `"note"` field in the JSON so this can never be misread as real API usage.
- **Files modified:** `scripts/gate4_mockprovider.py`, `scripts/gate4_games.py`
- **Verification:** re-ran `--mocked`; `token_spend.games` now shows non-zero, plausible call/token counts (e.g. 23–48 calls, 895–1870 input tokens per game across the seeded set), still clearly labelled simulated.
- **Committed in:** `64e59b3` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug, discovered by actually running the script rather than only reading the code).
**Impact on plan:** Necessary for the plan's own must_haves ("Also record... total tokens and cost") to be honest rather than silently wrong. No scope creep.

## Issues Encountered

None beyond what is captured above as a deviation. One methodological finding worth restating here (not a bug in this plan's own code, and not fixed by this plan — see Decisions Made above): the belief-on/off comparison's fallback-path confound in `network/turn_language.py`, predating this plan.

## User Setup Required

**External API key required to close out the one remaining item.** No `USER-SETUP.md` was generated (this is a single environment variable, not a multi-step service setup), but it is the phase's sole blocker:

1. Obtain a valid `ANTHROPIC_API_KEY` (Anthropic Console).
2. Run `ANTHROPIC_API_KEY=sk-ant-... uv run python scripts/measure_gate4.py --live` from the repo root.
3. Update `docs/phases/phase-4/GATE-4-MEASUREMENT.md`'s **Live status** section with the real result (replace the PENDING block with the script's output).
4. Only then run `/gsd:verify-work 4`.

## Next Phase Readiness

- **Phase 4's own build order is complete** — all 14 plans (04-01..04-14) executed, code+docs+measurement all in place.
- **`/gsd:verify-work 4` must NOT run yet.** GATE-4 is measured and PASSING in `--mocked` mode, but the plan's own D-32 requirement (a real API game) is PENDING on `ANTHROPIC_API_KEY`. Per rule 38, a phase whose gate was only measured mocked is not fully measured, and ticking anything before the live run would misreport the phase's true status.
- Once the live run lands and `GATE-4-MEASUREMENT.md`'s Live status section is updated, `/gsd:verify-work 4` can run and tick every Phase-4 TODO/ROADMAP row.
- Knowledge graph was NOT refreshed this session (measurement-only plan touching `scripts/`/`tests/`/`docs/`, no `src/` code changed — the graph already reflects 04-13's own refresh from the prior session, 5320 nodes/9778 edges/333 communities).
- No blockers for Phase 5 once Phase 4 is verified, beyond the standing league-scheduling concerns already tracked in `.planning/STATE.md`'s Blockers/Concerns section.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-09*

## Self-Check: PASSED

- All 12 claimed created files verified present on disk with `[ -f ]` (8 scripts, 1 test, 1 doc,
  2 JSON artifacts), plus `04-14-SUMMARY.md` and the updated `RESUME.md` itself.
- All 3 claimed task commit hashes (`64e59b3`, `371c1b8`, `c125833`) verified present in
  `git log --oneline --all`.
- Full-suite re-confirmation at self-check time: `uv run pytest tests/ --cov` — 1051 passed,
  95.21% coverage (required 85%); `uv run ruff check .` — 0 violations; `bash
  scripts/check_line_limit.sh` (repo-wide + explicit scripts/test files) — 0 violations;
  `uv run python scripts/check_no_llm_in_strategy.py` — clean.
- `scripts/measure_gate4.py --mocked` re-run and diffed against a prior run: only
  `wall_time_seconds`/`generated_at` differ; every criterion number byte-identical.
- `scripts/measure_gate4.py --live` re-confirmed to attempt zero network calls with no key set.
- **Nothing ticked:** `grep -n "04-14" .planning/ROADMAP.md` still shows `- [ ] 04-14: ...`;
  `docs/phases/phase-4/TODO.md`'s 04-14 row still shows `☐`.
