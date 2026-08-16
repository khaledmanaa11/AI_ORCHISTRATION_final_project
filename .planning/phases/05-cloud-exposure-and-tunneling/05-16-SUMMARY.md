---
phase: 05-cloud-exposure-and-tunneling
plan: "16"
subsystem: network
tags: [watchdog, net-07, turn-loop, deferred-10, injected-clock, deadline-ladder, revert-probe]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-13's on_attempt hook, its _fakes_watchdog.py injected-clock harness, and the ArmedWatchdog stop-flag gate (da58bc2) this plan reuses without reopening"
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-15's capture_declaration send leg -- the sixth unmarked ladder, found by sweeping rather than by reading the deferred item"
  - phase: 02-fastmcp-infrastructure
    provides: "Watchdog (D-14/NET-07) with injected clock/on_freeze/exit_action, and call_with_retry's D-13/D-17 ladder"
provides:
  - "every turn-loop ladder touches the freeze watchdog once per BOUNDED attempt, so a 140 s ladder against a stalled peer ends in D-13's honest verdict instead of os._exit(1) at t=60 s MID-GAME"
  - "NET-07 is preserved and PROVEN preserved: a wedged loop stops producing attempts and is still killed, refuted-by-probe against both tempting wrong fixes"
  - "LethalWatchdog -- os._exit(1)'s real semantics in a test, so 'no verdict was reached' is measured rather than inferred from a boolean"
  - "_turn_loop_fixtures.py and the shared assert_ladder_survived five-fact block"
affects: [07-reporting-and-visualization-shell, league-day-remote-round]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "touch-per-bounded-attempt, now applied at every call_with_retry site in the turn loop -- 05-13's pattern, finished"
    - "the lethal-exit test double: a control that raises where production would os._exit, so a case that RETURNS has itself proven survival"
    - "the harness-vacuity probe: strip the freeze poll out of the fake peer and confirm the suite notices (P7)"

key-files:
  created:
    - tests/unit/test_turn_loop_watchdog.py
    - tests/unit/test_turn_push_watchdog.py
    - tests/unit/_turn_loop_fixtures.py
  modified:
    - src/pursuit/network/turn_commit_wait.py
    - src/pursuit/network/turn_buffer.py
    - src/pursuit/network/turn_commit_send.py
    - src/pursuit/network/capture_declaration.py
    - tests/unit/_fakes_watchdog.py
    - tests/unit/test_audit_watchdog.py
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md

key-decisions:
  - "The exposure is SIX ladders, not the four the deferred item names. A stalled peer stalls our PUSH first -- turn_commit_send.push sends the COMMIT the wait leg awaits a reply to -- so marking only the waits would have left the turn loop dying at the same t=60 s one door earlier. Measured, not argued."
  - "NOT closed by widening watchdog_threshold. Every ladder case reads the bound from config and asserts the ladder OUTLIVES it, so moving the Table-19 number fails 6 of 8 cases on `assert 140.0 > 150`. That assertion exists to tell 'you marked the attempts' apart from 'you moved the number'."
  - "NOT closed by disarming the watchdog. A blanket ctx.watchdog.stop() fails 8 of 8, including the frozen-loop control and the never-disarms control."
  - "`LethalWatchdog` raises where production calls os._exit(1). 05-13's harness recorded that a freeze fired; this one records what it COST, which is the whole claim of deferred item #10."
  - "Task 1 was committed RED. The GSD TDD flow sanctions it and the pre-commit hook gates ruff + line-limit, not pytest, so the measurement is in the log as a failing run rather than as prose."
patterns-established:
  - "Probe your own harness (P7): strip the freeze poll out of the stalled peer and 7 of 8 cases must fail, otherwise the suite is certifying its own silence."
  - "assert_ladder_survived is one shared five-fact block, so no leg can drift into a weaker assertion set and each wrong fix has one named line to fail on."

# Metrics
duration: 130min
completed: 2026-08-16
---

# Phase 5 Plan 16: The Turn Loop Dies Of The Same Wound The Audit Did Summary

**Every ladder in the turn loop now touches the freeze watchdog once per bounded attempt, so a stalled peer costs 140 s of bounded retry and an honest `TechnicalWin` verdict instead of `os._exit(1)` at t=60 s mid-game — and there were six such ladders, not the four deferred item #10 named, because a stalled peer stalls our push before any wait leg is reached.**

## Performance

- **Duration:** ~130 min
- **Started:** 2026-08-16T19:35Z
- **Completed:** 2026-08-16T22:30Z (wall clock includes three full-suite runs and ten probe runs)
- **Tasks:** 3, each committed individually
- **Files created:** 3 · **modified:** 7

## Task Commits

1. **Task 1: measure the exposure before changing anything** — `a010a55` (test, RED)
2. **Task 2: mark every bounded attempt** — `4e3d42e` (fix)
3. **Task 3: pin it, and refute both wrong fixes by name** — `0993b05` (test)
4. **Deferred-items, trackers and this file** — the `docs(05-16)` commit that carries this file
   (a hash cannot be embedded in the object that defines it — 05-09's precedent)

## The gap, measured in this repository's own numbers

Run at `0ea5388` against unmodified source, injected clock, **0.000 s of real time**:

```
config: response_timeout=30 retry_count=3 backoff=5 watchdog_threshold=60
attempt cost (injected) = 35
wait attempts=2 injected_elapsed=70.0s touches=0 checks=[False, True] fired=['freeze','exit'] killed=True verdict=None
push attempts=2 injected_elapsed=70.0s touches=0 checks=[False, True] fired=['freeze','exit'] killed=True verdict=None
move attempts=2 injected_elapsed=70.0s touches=0 checks=[False, True] fired=['freeze','exit'] killed=True verdict=None
```

`killed=True` is not a flag the test sets — it is `LethalWatchdog` raising where production calls
`os._exit(1)`, so `verdict=None` is a **measured** fact: the D-13 ladder that would have answered
at t=140 s never got to speak. In production that second poll ends the process **mid-game**, with
our nonces ledgered and no FINAL_REVEAL sent — **we** become the side that published nothing
(rule 36 against us) while the peer records `opponent_unresponsive`. Same artifact class as G6,
one level up, where it costs the game rather than the audit.

After the fix, the same three legs:

```
wait attempts=4 injected_elapsed=140.0s touches=5 checks=[False, False, False, False] fired=[] killed=False verdict=TechnicalWin
push attempts=4 injected_elapsed=140.0s touches=5 checks=[False, False, False, False] fired=[] killed=False verdict=TechnicalWin
move attempts=4 injected_elapsed=140.0s touches=5 checks=[False, False, False, False] fired=[] killed=False verdict=TechnicalWin
```

140 s of ladder against a 60 s threshold, **zero** freeze polls firing, an honest verdict recorded.
`touches=5` is four per-attempt marks plus the retained post-ladder one. The widest gap between
two touches is `response_timeout + backoff_seconds` = **35 s < 60 s**.

## THE FINDING: the deferred item under-counted its own exposure by two ladders

Item #10 names four legs — the `wait_for_*` waits. Sweeping every `call_with_retry` site in
`src/pursuit/network/` found **six** unmarked ladders, and the two it missed are the ones that
matter most:

| leg | direction | why the item missed it |
|---|---|---|
| the four `wait_for_*` legs | receive | named |
| `turn_buffer.await_move` | receive | the toggle-off MOVE wait, a fifth leg with the same shape |
| **`turn_commit_send.push`** | **send** | **a stalled peer stalls this FIRST** — it sends the COMMIT the wait leg is waiting for a reply to |
| `turn_commit_send.send_move_only` | send | the toggle-off MOVE push |
| `turn_buffer.send_hint` | send | best-effort, but an unmarked best-effort ladder still gets `os._exit(1)` called on us |
| `capture_declaration` (05-15) | send | runs INSIDE `run_turn_loop`, where the watchdog stays armed to `agent_entrypoint:134` — so it killed us BEFORE `run_final_audit` could publish our nonces |

Had only the four named legs been fixed, a stalled peer would still have killed us at the identical
t=60 s, through the earlier door, and the plan's own objective — "a stalled peer costs us a bounded
ladder and an honest verdict, not a process death" — would have been false while every test passed.
The push case is a shipped test (`test_a_stalled_peer_costs_the_commit_push_a_ladder_and_not_the_process`),
not a footnote.

`grep -rn "watchdog\.touch" src/` now returns **18** = **12** calls + **5** `on_attempt=` hook
passes + **1** comment. The call-form grep alone returns **12** and undercounts the hooked legs by
five — the same trap 05-13 recorded as its deviation 6, stated here with both numbers rather than one.

## What each task changed

### Task 1 — `a010a55`, the RED half

`tests/unit/test_turn_loop_watchdog.py`, three ladder cases, committed **failing**, with the
before-numbers in the module docstring. `LethalWatchdog` subclasses 05-13's `ArmedWatchdog` and
raises `ProcessKilledError` when a poll fires — calling `super().check()` first and unconditionally,
so 05-13's stop-flag gate (`da58bc2`) still runs and the hole that plan found is not reintroduced.

`armed_from` / `attempt_cost` / `table19_overrides` extracted into `_fakes_watchdog.py` at their
**second** copy (CLAUDE.md's no-duplication rule). `test_audit_watchdog.py`'s four cases are
**byte-unedited** and went 146 → 142 code lines.

### Task 2 — `4e3d42e`, the fix

The four `wait_for_*` legs pass `on_attempt=ctx.watchdog.touch`. The same per-attempt touch opens
the closure of `turn_buffer.await_move`, `turn_buffer.send_hint`, `turn_commit_send.push`,
`turn_commit_send.send_move_only` and `capture_declaration`. Every post-ladder touch retained.

**No numeric value moved anywhere.** `turn_commit_wait.py` is unchanged at **145** code lines: the
four edits are inline keyword arguments and the rest is comment. The stale comment block at
`:68-77`, which stated as fact that only `receive_final_reveal` passes a hook, is corrected in
place and now carries the measurement plus the reason neither wrong fix is acceptable.

`turn_buffer.await_move`'s anonymous lambda became a named `_pull` closure — **only** because a
lambda cannot hold two statements. The awaited call is byte-identical.

### Task 3 — `0993b05`, the controls

Eight cases over two files plus the harness, split at the 150-line gate rather than compressed:
`test_turn_loop_watchdog.py` (110) keeps the wait legs and both NET-07 controls,
`test_turn_push_watchdog.py` (85) keeps the four push legs, `_turn_loop_fixtures.py` (74) holds
the harness and the shared `assert_ladder_survived` five-fact block.

## Revert probes — ten, each with a real count

| probe | what was changed | result |
|---|---|---|
| baseline | — | **8 passed** |
| **P1** | four `wait_for_*` legs lose the hook | **1 failed / 7 passed** — the wait-leg case only |
| **P2** | `turn_commit_send.push` loses its touch | **1 failed / 7 passed** — the commit-push case only |
| **P3** | `turn_buffer.await_move` loses its touch | **1 failed / 7 passed** — the move-wait case only |
| **P4** | `turn_buffer.send_hint` loses its touch | **1 failed / 7 passed** — the hint-push case only |
| **P5** | `send_move_only` loses its touch | **1 failed / 7 passed** — the move-push case only |
| **P6** | `capture_declaration` loses its touch | **1 failed / 7 passed** — the capture-claim case only |
| **W1** | **WRONG FIX A**: `watchdog_threshold` 60 → 150, fix left in | **6 failed / 2 passed** |
| **W1b** | **WRONG FIX A ALONE**: every touch reverted **and** threshold widened | **6 failed / 2 passed** |
| **W2** | **WRONG FIX B**: blanket `ctx.watchdog.stop()` across the turn loop | **8 failed / 0 passed** |
| **P7** | **my own harness**: the freeze poll stripped out of both stalled peers | **7 failed / 1 passed** |

Six single-leg reverts each fail **exactly one** case: the pinning is surgical, not diffuse.

**W1/W1b are the refutation deferred item #10 explicitly asked for.** The wrong fix makes the
symptom vanish — widen the threshold past 140 and no freeze ever fires — and the suite refuses it
anyway, because every ladder case reads `watchdog_threshold` from config and asserts the ladder
**outlives** it:

```
E   AssertionError: the ladder no longer outlives watchdog_threshold -- a Table-19 NUMBER was moved
E   assert 140.0 > 150
```

The two survivors under W1 are the frozen-loop and never-disarms controls, which do not assert
ladder length — correctly, since widening the threshold does not disarm the watchdog.

**W2 is the one that matters.** Disarming makes every ladder case survivable by **deleting NET-07**,
and all eight refuse it with the right messages:

```
the ladder ran unmarked          assert 1 >= 4        (x3, the ladder cases)
Failed: DID NOT RAISE ProcessKilledError               (the genuinely-frozen control)
the turn loop left the watchdog disarmed  assert False is True
```

**P7 is the probe 05-13, 05-14 and 05-15 each caught themselves needing.** Remove
`self._armed.check()` from `StalledQueue.get` and `StalledClient.call_tool` and **7 of 8 cases
fail** on `NET-07 killed the ladder mid-flight` — the leading `armed.checks` conjunct in
`assert_ladder_survived` is exactly the anti-vacuity guard, and it is falsifiable. The single
survivor is `test_the_turn_loop_never_disarms_the_watchdog`, which uses no stalled peer.

## Gates (real output, at `0993b05`)

```
uv run ruff check .                      -> All checks passed!   exit 0
bash scripts/check_line_limit.sh         -> exit 0
uv run python scripts/check_no_llm_in_strategy.py -> OK   exit 0
uv run pytest tests/ --cov               -> 1523 passed, 1 failed in 155.66s
                                            Total coverage: 96.62%
```

Against the inherited baseline of **1516 passed / 0 failed / 96.62%**: **+8 tests** (exactly the
eight added), coverage **unchanged at 96.62%**, and all four changed production modules at
**100%** — `turn_commit_wait` 67/67, `turn_buffer` 57/57, `turn_commit_send` 47/47,
`capture_declaration` 38/38.

**The one failure is the documented deferred item #4 flake**, `test_late_peer_teardown.py::test_without_the_linger_the_late_peers_own_push_is_cut_off`,
and it is **attributed by paired measurement rather than assumed** (see *Issues* below). It passes
2/2 alone immediately afterwards.

**Live loopback game** (`uv run python scripts/dev_launch.py`, live key exported, **exit 0**):
one shared uid `0f803ac4058d208a` across both sides' log **and both filenames**, both
`audit_verdict matched=true`, **zero `technical_win`, zero `watchdog_incident`** on either side.
The thief's log additionally carries its own pre-negotiation uid `78c0d2385a25cabf`, which is
05-05's expected rebind shape. One `illegal_transition` (`handshake -> handshake`, severity
`recoverable`) appears on each side — **pre-existing**, present identically in 05-15's own
`6ee059af51c508f5` run, not touched here.

**GATE-6** re-measured (`scripts/measure_gate6.py`, exit 0): all three book §10.4 criteria **PASS**.
`gate6_measurement_evidence.json` differed in exactly **3 timestamp/mtime lines** plus the two
`"game_over": 1` counters 05-15 introduced and also left uncommitted; every verdict field
byte-identical. **Restored, not committed** — a Phase-5 plan should not churn a Phase-6 evidence
file (05-12/05-13/05-15 precedent).

**Knowledge graph** refreshed: **7832 nodes / 14141 edges / 479 communities** (was 7719 / 13861 /
482). `graph.html` skipped again over the 5000-node viz limit; `graph.json` gitignored.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — the plan's premise was measurably incomplete] Two source files outside `files_modified` carried the same defect, and one of them is hit FIRST**

- **Found during:** Task 1, sweeping every `call_with_retry` site rather than only the ones the
  deferred item names.
- **Issue:** the plan's `files_modified` is `turn_buffer.py` + `turn_commit_wait.py`, and its
  success criterion is "the four turn-loop legs". Measured, `turn_commit_send.push` — the leg that
  sends the COMMIT the wait leg awaits — ran the identical unmarked 140 s ladder
  (`push attempts=2 elapsed=70.0s touches=0 checks=[False, True] verdict=None`), as did
  `send_move_only` and 05-15's `capture_declaration`. Fixing only the named legs would have left
  the process dying at the same t=60 s one door earlier, with the plan's own objective false and
  every test green.
- **Fix:** the same one-line per-attempt touch at all six legs; `turn_commit_send.py` and
  `capture_declaration.py` added to the change set.
- **Verification:** P2, P5 and P6 each fail exactly one case against their own revert.
- **Committed in:** `4e3d42e`

**2. [Rule 3 — Blocking line gate] The test file would have breached 150, so it was SPLIT (twice), never compressed**

- **Found during:** Task 3.
- **Issue:** `test_turn_loop_watchdog.py` reached 133 code lines with three cases and would have
  landed near 163 with the two NET-07 controls plus the three extra push legs.
- **Fix:** the harness moved to `tests/unit/_turn_loop_fixtures.py` (74) — a non-`test_*.py` module
  pytest never collects, the `_fakes_agent.py` / `_hint_decode_fixtures.py` precedent — and the four
  push legs to `tests/unit/test_turn_push_watchdog.py` (85), leaving 110. **Not one assertion was
  shortened to fit**; the split added assertions rather than removing them.
- **Committed in:** `0993b05`

**3. [CLAUDE.md no-duplication] Three Table-19 test helpers reached their second copy and were extracted**

- **Found during:** Task 1.
- **Issue:** `_armed`, `_attempt_cost` and the `net_overrides` dict trading the five fast defaults
  for the real ladder existed in `test_audit_watchdog.py` and were needed verbatim here.
- **Fix:** `armed_from` / `attempt_cost` / `table19_overrides` in `_fakes_watchdog.py`, re-exported
  through the private names in `test_audit_watchdog.py` so **all four of its cases are
  byte-unedited** (verified green before and after). Its `backoff_seconds=0` argument moved to live
  with the dict it explains. Side effect: that file went 146 → 142, off deferred item #11's list.
- **Committed in:** `a010a55`

**4. [Rule 1 — a bug in my own tooling, and it cost a false alarm] A runaway probe process pegged a core and made deferred #4 look deterministic**

- **Found during:** verification, when `test_late_peer_teardown` failed **4/4** — far worse than
  its documented flake behaviour.
- **Issue:** an earlier scratch probe of mine searched upward for `pyproject.toml` from the
  scratchpad, where none exists, so the loop never terminated at the filesystem root. It was
  backgrounded, survived a `kill %job`, and had burned **680 s of CPU** by the time it was found —
  precisely the load deferred item #4 is documented as sensitive to.
- **Fix:** processes killed; the attribution then re-done properly and recorded in the item.
- **Lesson worth keeping:** a "flaky test got worse" signal deserves a look at what else is running
  before it is written up as a finding. The measurement was nearly filed as a regression.

---

**Total deviations:** 4 auto-fixed (2 scope corrections forced by measurement, 1 blocking line
gate, 1 self-inflicted tooling bug). **Impact on plan:** no scope creep in the sense that matters —
deviation 1 is what makes the plan's own stated objective true rather than nominally satisfied.

## Self-audit (the lens 05-VERIFICATION applies)

- **Production callers, grepped for every changed name.** All four `wait_for_*` legs are imported
  and called from `turn_commit.py` (`:79`, `:111`, `:151`, `:164`) — the live D-58 entry points.
  `on_attempt=` now has **5** production call sites, four here and 05-13's audit receive leg; **no
  caller is left at the default**. The five new `ctx.watchdog.touch()` calls sit inside closures
  that `call_with_retry` invokes on the live push/pull paths. **No dead validator, no test-only
  production function.** `ProcessKilledError`, `LethalWatchdog`, `lethal`, `turn_ctx`, `stall`,
  `assert_ladder_survived`, `armed_from`, `attempt_cost` and `table19_overrides` are test-only **by
  design** and live in `_`-prefixed modules pytest never collects.
- **Vacuity probes.** `grep -c parametrize` returns **0** in all three new files, so pytest's
  empty-set-is-a-SKIP trap cannot apply. `assert armed.checks and not any(armed.checks)` leads with
  the non-empty conjunct precisely so an unpolled run cannot pass — **and that is probed, not
  asserted**: P7 strips the poll out of the harness and 7 of 8 cases fail.
  `assert (opponent, verdict) == ("h", None)` is **one tuple**, deliberately, so neither half can
  shadow the other — 05-15's finding, applied pre-emptively.
- **The honest limit of one assertion.** Under `LethalWatchdog`, `armed.fired == []` and the
  `not any(armed.checks)` half can never fail *in these cases*, because a fired freeze raises
  before the assertion is reached. They are redundant rather than vacuous — the load-bearing facts
  are that the call **returned at all**, that `touches >= attempts` (what W2 fails on) and that the
  ladder outlived the threshold (what W1 fails on). Recorded rather than left for a reviewer to
  find.
- **Falsifiability.** Every one of the six fixes was run against its own revert, and both named
  wrong fixes were run in full. The harness itself was run against its own removal.

## Issues Encountered

- **`test_late_peer_teardown` (deferred #4) is no longer a load-only flake.** Attributed by paired
  measurement rather than assumed: at `a010a55` **without** this plan's source changes it is
  1 failed / 2 passed over three runs of the file alone, and **with** them it is 1 failed / 2 passed
  over three runs — identical, on the item's own verbatim assertion message. The failing run is
  reliably the **first run after a source file changes**, with the two after it passing, which
  points at bytecode recompilation slowing A's teardown enough for B's 0.3 s-late push to land.
  Not fixed: `late_peer_harness.py` is 05-04's file and the only quick repair is to widen a timing
  constant, which is weakening the probe. Recorded in the item with the table.
- **`agent_audit_exchange.py` was deliberately not touched.** 05-13 proved that path; this plan
  reuses its hook and its harness and reopens neither.

## Deferred items

- **#10 — CLOSED** by this plan, with the before/after numbers, the six-ladder correction and both
  wrong-fix probes written into `deferred-items.md`.
- **#4 — updated** with the new attribution table above. Still open, still 05-04's file.
- **#11 — updated.** `test_audit_watchdog.py` is off the list (146 → 142); `turn_commit_wait.py`
  is deliberately unchanged at 145; `_fakes_watchdog.py` joins at 143.
- **#12, #13, #14, #15 — untouched.** #13 (the toggle-off MOVE envelope stamped `1..16` for turns
  `0..15`) is explicitly out of scope per this plan's `non_goals`: its repair changes
  `turn_commit.initiate`'s signature, and on the commit-reveal-ON path that `turn` feeds
  `commit_own_action`'s D-59 hash input and the D-64 ledger join key — rules 19/22 territory. It
  stays deferred **with 05-14's measurement recorded**, not silently.

## Next Phase Readiness

Phase 5's league-day path is materially safer in the half that decides games rather than audits: a
peer that goes quiet mid-game — the single likeliest tunnel failure — now costs a bounded 140 s
ladder and a correctly-attributed `TechnicalWin` instead of `os._exit(1)` at t=60 s with no verdict
and no published nonces. `/gsd:verify-work 5` remains next.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-16*

## Self-Check: PASSED

Every claim in this file re-verified against disk and git at `0993b05`, not copied from memory:

- **11 files** named as created/modified — all present on disk (3 created, 8 modified including
  this file and `deferred-items.md`).
- **5 commits** named — `a010a55`, `4e3d42e`, `0993b05` (this plan) and `da58bc2`, `0ea5388`
  (cited) all resolve.
- **Every line count re-measured**, not remembered: `turn_commit_wait.py` **145** (unchanged),
  `test_turn_loop_watchdog.py` **110**, `test_turn_push_watchdog.py` **85**,
  `_turn_loop_fixtures.py` **74**, `test_audit_watchdog.py` **142**. `check_line_limit.sh` exit 0
  tree-wide.
- **Every grep count re-run**: call form **12**, any form **18**, `on_attempt=` **5**. Both touch
  numbers are quoted in the body precisely because the call-form grep undercounts by five — the
  mistake 05-13 shipped and then corrected.
- **The 12 watchdog cases re-run at final HEAD**: 12 passed (8 new + 05-13's 4, still byte-unedited).
- **One draft number was found wrong by this check and corrected** rather than left standing: an
  earlier draft of the `deferred-items.md` #11 update said `_turn_loop_fixtures.py` (77) and
  `test_turn_push_watchdog.py` (91); the measured values are **74** and **85**.
- **One pre-existing condition noted, not introduced and not fixed:** `.planning/STATE.md`'s
  frontmatter has never been strictly valid YAML — the hand-authored narrative fields contain
  `: ` inside unquoted scalars. Verified by parsing `git show HEAD:.planning/STATE.md`, which
  fails on 05-15's own text. This plan matches the established format deliberately;
  `gsd-tools validate health` reports `status: healthy`, 0 errors, 0 warnings.
