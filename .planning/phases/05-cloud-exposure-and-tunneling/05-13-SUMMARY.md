---
phase: 05-cloud-exposure-and-tunneling
plan: "13"
subsystem: network
tags: [watchdog, net-07, final-reveal, mutual-audit, false-accusation, injected-clock, deadline-ladder]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-04's board_outcome wiring and record_audit_incomplete (the send-leg non-accusation this plan makes reachable and then mirrors)"
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-12's clean 1479/96.57% baseline and its reject-shapes-never-conventions rule"
  - phase: 02-fastmcp-infrastructure
    provides: "Watchdog (D-14/NET-07) with injected clock/on_freeze/exit_action, and call_with_retry's D-13/D-17 ladder"
provides:
  - "the final audit touches the freeze watchdog once per BOUNDED attempt on BOTH legs, so a 135 s ladder no longer ends in os._exit(1) at t=60 s with no verdict"
  - "next_protocol_message's optional on_attempt hook (default None -- every turn-loop caller byte-identical)"
  - "a receive-leg failure is non-accusatory only when our OWN push already failed too; rule 36's withheld-nonces sanction is untouched"
  - "tests/unit/_fakes_watchdog.py -- the REAL Watchdog on an injected clock, the seam no suite had"
  - "agent_step0_wiring.py -- the Step-0 half split off agent_audit_wiring at exactly 150/150"
affects: [05-14, 05-15, 07-reporting-and-visualization-shell, league-day-remote-round]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "touch-per-bounded-attempt: liveness is marked by an attempt STARTING, never by a heartbeat, so a wedged event loop is still killed"
    - "injected-clock NET-07 testing: the real Watchdog with clock/on_freeze/exit_action injected and check_once() driven by hand -- zero real sleeps, os._exit unreachable"
    - "the wrong fix as a revert probe: P4 applies the tempting shortcut and must fail the controls"

key-files:
  created:
    - src/pursuit/network/agent_step0_wiring.py
    - tests/unit/_fakes_watchdog.py
    - tests/unit/test_audit_watchdog.py
  modified:
    - src/pursuit/network/agent_audit_exchange.py
    - src/pursuit/network/agent_audit_wiring.py
    - src/pursuit/network/agent_audit_verdict.py
    - src/pursuit/network/turn_commit_wait.py
    - src/pursuit/network/agent_entrypoint.py
    - tests/unit/_fakes_agent.py
    - tests/unit/test_audit_send_failure.py
    - tests/unit/test_agent_teardown.py
    - tests/integration/late_peer_harness.py

key-decisions:
  - "The touch goes at the START of each bounded attempt, not around the whole ladder: that is what preserves NET-07 while making the ladder survivable."
  - "A failed RECEIVE is non-accusatory ONLY when our own push already failed. A push that LANDED proves the channel worked, so the withheld-nonces sanction (rule 36) is unchanged -- the plan's artifact line implied an unconditional relaxation, which would have deleted a control its own truths require."
  - "On the non-accusatory receive path run_final_audit RETURNS rather than falling through: with peer_records == [] the same TECHNICAL_LOSS re-enters through the AUDIT_HASH_MISMATCH door."
  - "turn_commit_wait.next_protocol_message's on_attempt defaults to None, so the TURN LOOP's identical 135 s-vs-60 s exposure is left untouched and logged as deferred #10 -- it is a parameter-and-policy decision, not this plan's scope."
  - "agent_audit_wiring.py was SPLIT at exactly 150/150 rather than after a breach, following 05-10's security/audit.py precedent."

patterns-established:
  - "ArmedWatchdog.check() mirrors Watchdog._run's stop gate, not just check_once -- otherwise a control against 'disarm the watchdog' passes against exactly that wrong fix."
  - "make_ctx merges net_overrides into ONE dict before dataclasses.replace, so a test can trade the fast defaults back for the real Table-19 values."

# Metrics
duration: 95min
completed: 2026-08-16
---

# Phase 5 Plan 13: The Audit Survives Long Enough To Be Honest Summary

**`run_final_audit` now touches the freeze watchdog once per bounded attempt on both legs, so a 135 s retry ladder against a stalled tunnel edge ends in a recorded `audit_verdict` instead of `os._exit(1)` at t=60 s — and a failed receive stops accusing a peer that may have answered, without softening rule 36.**

## Performance

- **Duration:** ~95 min
- **Started:** 2026-08-16T16:21Z
- **Completed:** 2026-08-16T17:56Z
- **Tasks:** 3 (+ 4 deviation/self-audit commits)
- **Files created:** 4 · **modified:** 10

## The gap, restated against live source

Measured at `448ca09` before any edit:

- `grep -rn "watchdog.touch()" src/` returned **exactly five** sites — `turn_buffer.py:103,151`,
  `turn_commit_send.py:52,132`, `turn_commit_wait.py:70`. **All turn-loop. None in the audit path.**
- `run_agent` arms the watchdog at `agent_entrypoint.py:76` and stops it only at `:134`, spanning
  `run_final_audit` at `:110`.
- `config/*/network.json`: `response_timeout=30`, `retry_count=3`, `backoff_seconds=5`,
  `watchdog_threshold=60`. So one ladder is `4 x 30 + 3 x 5 = 135 s` against a 60 s threshold whose
  freeze action is `os._exit(1)`.

Against a peer whose socket accepts TCP but never answers, the process died at t=60 s and 05-04's
`record_audit_incomplete` at t~135 s **never ran**. The log ended on `watchdog_incident` with no
`audit_verdict`, and the peer then declared us `opponent_unresponsive`: the 2026-08-13 artifact
through a second door. 05-04's authors **knew** the no-touch fact — they cite it at
`agent_entrypoint.py:127-129` as why `stop_watchdog` must precede the linger. They protected the
linger and stepped over the audit.

## Task Commits

1. **Task 1: per-attempt watchdog touch** — `d5f2f36` (fix)
2. **Task 2: the receive leg stops accusing** — `a2f7034` (fix)
3. **Deviation: split at exactly 150/150** — `6920d4d` (refactor)
4. **Task 3: the window that hid G6 is now expressible** — `ce89f02` (test)
5. **Deviation: correct the three claims this fix falsified** — `2633df4` (docs)
6. **Self-audit: close a hole in my own NET-07 control** — `da58bc2` (test)
7. **Self-check: the stale-grep docstring shipped a stale grep count** — `63c4ba1` (docs)

## What each task changed

### Task 1 — `d5f2f36`, the touch (`agent_audit_exchange.py`, `turn_commit_wait.py`)

`push_final_reveal`'s per-attempt `_call` closure now opens with `ctx.watchdog.touch()`.
`next_protocol_message` gained a keyword-only `on_attempt: Callable[[], None] | None = None`,
invoked at the start of each bounded pull; `receive_final_reveal` is the **only** caller that
passes one, and it passes `ctx.watchdog.touch`.

**Why this placement is the fix and not a bypass.** Each attempt is itself bounded by
`response_timeout`, so the widest possible gap between two touches is
`response_timeout + backoff_seconds` = **35 s < 60 s**. A genuinely wedged event loop stops
producing attempts altogether and is still killed. The touch marks a real attempt **starting** —
the shape `turn_commit_send.push` already wraps this same ladder in — never a heartbeat on a dead
loop.

### Task 2 — `a2f7034`, the receive leg (`agent_audit_wiring.py`, `agent_audit_verdict.py`)

`record_audit_incomplete` gained a keyword-only `reason` (default `_OWN_SEND_FAILED`, so every
05-04 call site is byte-identical) rather than a second near-identical writer.
`OWN_RECEIVE_FAILED = "own_final_reveal_receive_failed"` is named at the call site by the module
that owns the policy.

**The discrimination, and the plan correction it required.** See *Deviations* below: the plan's
artifact line read "`record_technical_loss` reserved for mismatch / unresolved loop", which is an
**unconditional** relaxation of the receive leg — and its own truth 4 requires
"withheld nonces -> TECHNICAL_LOSS" to keep firing. Both cannot hold. Resolved on
`send_verdict is not None`:

| our push | our receive | board outcome | verdict |
|---|---|---|---|
| landed | failed | stands | **TECHNICAL_LOSS** (rule 36) — unchanged |
| failed | failed | stands | `audit_incomplete` x2, board outcome stands, **return** |
| failed | ok | stands | `audit_incomplete`, fall through, `audit_verdict` (05-04) |
| any | any | **none** | TECHNICAL_LOSS — the turn loop never resolved |

Returning rather than falling through is load-bearing: with `peer_records == []` every honest turn
fails at `audit_state` and the same TECHNICAL_LOSS re-enters through the `AUDIT_HASH_MISMATCH`
door — a false accusation through the back door.

### Task 3 — `ce89f02`, the tests

`tests/unit/_fakes_watchdog.py` (new): `ManualClock`, `ArmedWatchdog` (the **real** `Watchdog` with
clock/`on_freeze`/`exit_action` injected, `check_once()` driven by hand), and
`StalledClient`/`StalledQueue` — a peer whose socket accepts TCP and never answers, on either leg,
raising the exact `DeadlineExpired` that `deadline_wait.bounded` raises.

`make_ctx` gained `watchdog=` (default unchanged) and now merges `net_overrides` into **one** dict
before `dataclasses.replace` — previously splatting made the five fast-test defaults
un-overridable (`TypeError: got multiple values for keyword argument`), which is a second, smaller
reason the G6 window was inexpressible.

`tests/unit/test_audit_watchdog.py` (new), four cases; `tests/unit/test_audit_send_failure.py`
gained case 5. **Cases 1–4 there are byte-unedited** — the three paired fairness controls pass
without a character changed.

## Measurements (real output)

**The ladder, measured through the shipped config, zero real sleeps:**

```
config: response_timeout=30 retry_count=3 backoff=5 watchdog_threshold=60
attempt cost = 35
SEND: attempts=4 injected_elapsed=140.0s real=0.000s touches=6 checks=[False, False, False, False]
      fired=[] out=None kinds=['audit_incomplete', 'audit_verdict']
BOTH: pushes=4 pulls=4 injected_elapsed=280.0s real=0.000s fired=[] out=None
      reasons=['own_final_reveal_send_failed', 'own_final_reveal_receive_failed']
```

140 s of ladder against a 60 s threshold, in 0.000 s of wall clock, with **zero** freeze polls
firing and an `audit_verdict` written. Before the fix the same ladder produced `os._exit(1)`.

**Revert probes.** Each fix undone, the two G6 files re-run, then restored:

| probe | what was undone | result |
|---|---|---|
| **P1** | push-leg `ctx.watchdog.touch()` removed | **1 failed / 8 passed** — `checks=[False, True, True, True]`, "NET-07 killed the audit mid-ladder" |
| **P2** | receive-leg `on_attempt=ctx.watchdog.touch` removed | **1 failed / 8 passed** — `checks=[False, True, True, True]`, "NET-07 killed the receive leg" |
| **P3** | receive leg accuses unconditionally (pre-05-13 shape) | **1 failed / 8 passed** — `assert outcome is not Outcome.TECHNICAL_LOSS` |
| **P4** | **THE WRONG FIX**: touches removed + `ctx.watchdog.stop()` across the audit | **3 failed / 6 passed** — the push-ladder case (touches == 0), the genuine-freeze case, and `test_the_audit_never_disarms_the_watchdog` |

P4 is the one that matters. A blanket "disarm the watchdog during the audit" makes the ladder
survivable by **deleting NET-07**, and three tests refuse it.

**Gates, at `da58bc2`:**

```
1484 passed in 159.34s          (baseline 1479)
Required test coverage of 85.0% reached. Total coverage: 96.58%   (baseline 96.57%)
ruff check .                 -> All checks passed!   exit 0
scripts/check_line_limit.sh  -> exit 0
scripts/check_no_llm_in_strategy.py -> OK   exit 0
```

Changed-module coverage: `agent_audit_exchange` **100%**, `agent_audit_verdict` **100%**,
`agent_audit_wiring` **100%**, `agent_step0_wiring` **100%**, `turn_commit_wait` **100%**.

**Live loopback game** (`uv run python scripts/dev_launch.py`, exit 0): one shared uid
`59dc79e25016a0d8` across both sides' log, both `game_over -> capture`, both
`audit_verdict matched=true`, **zero `technical_win`, zero `watchdog_incident`**.

**GATE-6** re-measured (`scripts/measure_gate6.py`, exit 0): all three book §10.4 criteria **PASS**.
`gate6_measurement_evidence.json` differed in exactly **3 timestamp lines**, every verdict field
byte-identical — **restored, not committed**: a Phase-5 plan should not churn a Phase-6 evidence
file (05-12 precedent).

**Knowledge graph** refreshed: **7588 nodes / 13614 edges / 465 communities** (was 7524 / 13490 /
466). `graph.html` skipped again over the 5000-node viz limit; `graph.json` gitignored.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 4-adjacent — plan self-contradiction, resolved by the plan's own truths] The receive-leg relaxation had to be conditional**

- **Found during:** Task 2
- **Issue:** the plan's artifact line says "`record_technical_loss` reserved for mismatch /
  unresolved loop" — an unconditional receive-leg relaxation. Its own **truth 4** requires
  "withheld nonces -> TECHNICAL_LOSS" to keep firing, and that control is precisely a failed
  receive with a board outcome standing (`test_a_peer_that_withholds_its_own_nonces_is_still_a_technical_loss`).
  Implemented as written, the fix would have **deleted a fairness control its own must_haves
  demand** — the receive-leg twin of the wrong fix P4 refutes.
- **Fix:** the relaxation is conditioned on `send_verdict is not None`. Truth 3 says "a peer that
  **may** have answered"; a push that landed proves the channel worked, so only a double failure
  is evidence about us. Both truths now hold simultaneously.
- **Files:** `src/pursuit/network/agent_audit_wiring.py`
- **Verification:** P3 (unconditional accusation) fails the new case; the untouched control 3 fails
  under an unconditional relaxation. Both directions pinned.
- **Committed in:** `a2f7034`

**2. [Rule 3 — Blocking] `turn_commit_wait.py` had to be edited, and it is not in the plan's `files_modified`**

- **Found during:** Task 1
- **Issue:** the plan requires "the mirrored receive-leg case is covered as well as the send leg",
  but `receive_final_reveal` delegates to `next_protocol_message`, whose only touch is **after**
  its whole ladder. Without a hook there the receive leg keeps the identical 135 s-vs-60 s
  exposure and `record_audit_verdict` is still never reached.
- **Fix:** optional keyword-only `on_attempt`, **default `None`**, so all four turn-loop
  `wait_for_*` legs are byte-identical.
- **Files:** `src/pursuit/network/turn_commit_wait.py` (139 -> 145 code lines)
- **Verification:** P2 fails without it; the turn-loop suite passes unedited.
- **Committed in:** `d5f2f36`

**3. [Rule 3 — Blocking line gate] `agent_audit_wiring.py` reached exactly 150/150 -> split**

- **Found during:** Task 2
- **Issue:** the policy docstring took the file to exactly the limit. Legal, and with zero
  headroom the next edit breaches.
- **Fix:** `declare_step0` + `write_declaration` moved **verbatim** into the new
  `agent_step0_wiring.py` (79 lines), re-exported from `agent_audit_wiring.py` (now 96). Split
  along the seam that module's own opening sentence already named. 05-10 set the precedent by
  splitting `security/audit.py` at exactly 150/150.
- **Verification:** `agent_entrypoint`, `late_peer_harness`, the gate6 scripts and the suite all
  resolve unchanged; 21 targeted tests pass. Not one line shortened.
- **Committed in:** `6920d4d`

**4. [Rule 1 — Bug] Three docstrings/comments asserted what the evidence no longer supports**

- **Found during:** post-Task-3 self-audit
- **Issue:** `agent_entrypoint.py`'s teardown comment justified `stop_watchdog`-before-linger with
  "touch() is called nowhere in the audit path"; `test_agent_teardown.py`'s docstring stated the
  hazard as still open, citing the five-site grep; `late_peer_harness.py` implied its green run
  was evidence about the audit. All three became false.
- **Fix:** each corrected in place, with the **reason** distinguished from the **conclusion** — the
  linger is a drain loop with no bounded attempt of its own to touch on, so the ordering stands.
  `late_peer_harness.py` now names the gap it leaves rather than implying none.
- **Verification:** no assertion changed in either test file; both suites green.
- **Committed in:** `2633df4`

**5. [Rule 1 — Bug in my own test] `ArmedWatchdog.check()` ignored the stop flag, so the anti-wrong-fix control was unfalsifiable**

- **Found during:** running P4
- **Issue:** `Watchdog.check_once()` never consults `_stop` — only `Watchdog._run` does. Driving
  `check_once` by hand made a **stopped** watchdog look armed, so
  `test_the_audit_never_disarms_the_watchdog` — which exists solely to refute "just stop the
  watchdog across the audit" — would have **passed against exactly that wrong fix**. An
  unfalsifiable control is worse than no control: it certifies the thing it forbids.
- **Fix:** `check()` mirrors `_run`'s stop gate. Found by **running** the wrong fix, not by reading
  the code.
- **Verification:** P4 goes from 1 failure to 3, the two new ones being the genuine-freeze case and
  the never-disarms control.
- **Committed in:** `da58bc2`

**6. [Rule 1 — Bug in my own correction] `2633df4` said the grep "now returns seven"; it returns six**

- **Found during:** self-check of this SUMMARY's own claims
- **Issue:** the corrected `test_agent_teardown.py` docstring — a docstring whose entire purpose is
  to stop a stale grep count being used as evidence — shipped a stale grep count. The call-form
  grep `watchdog\.touch()` returns **six** sites, not seven: the receive leg's touch is **passed,
  not called** (`next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)`), so the call-form grep
  **undercounts the audit path by one**. Commit `2633df4`'s message carries the same wrong number
  and is left standing — the log is append-only evidence.
- **Fix:** the docstring now gives both numbers and says explicitly why they differ.
- **Verification:** `grep -rn "watchdog\.touch()" src/` -> 6; `grep -rn "watchdog\.touch" src/` -> 8
  (6 calls + 1 hook + 1 comment). Both quoted in the docstring's own terms.
- **Committed in:** `63c4ba1`

**7. [Rule 3 — Blocking] `make_ctx` could not accept the real Table-19 values**

- **Found during:** Task 3
- **Issue:** `dataclasses.replace(net, response_timeout=..., ..., **(net_overrides or {}))` raised
  `TypeError: got multiple values for keyword argument 'response_timeout'` for any test wanting the
  production ladder. A quiet second reason the G6 window was inexpressible.
- **Fix:** merge into one dict before `replace`. Strictly more permissive; same five defaults, same
  precedence, every pre-05-13 caller unaffected.
- **Committed in:** `ce89f02`

---

**Total deviations:** 7 auto-fixed (4 bug/self-correction, 3 blocking).
**Impact on plan:** no scope creep. Deviation 1 is a real correction to the plan's stated shape and
is the difference between closing G6 and deleting a fairness control; 5 is a real defect in my own
evidence, found by adversarial self-probe rather than by review.

## Self-audit (the lens 05-VERIFICATION applies)

- **Production callers, grepped for every new name.** `OWN_RECEIVE_FAILED` ->
  `agent_audit_wiring.run_final_audit`. `record_audit_incomplete(reason=)` -> same. `on_attempt=`
  -> `agent_audit_exchange.receive_final_reveal`, itself called from `run_final_audit`, itself
  called from `agent_entrypoint.run_agent:110`. `ctx.watchdog.touch()` in `_call` -> the live push
  path. `agent_step0_wiring.*` -> re-exported and consumed by `agent_entrypoint`. **No dead
  validator, no test-only function.**
- **Vacuity probes.** No `parametrize` anywhere in the new tests, so pytest's empty-set-is-a-SKIP
  trap cannot apply. `assert armed.checks and not any(armed.checks)` — the leading conjunct exists
  precisely so an empty poll list cannot pass. `assert reasons == [<two literals>]` cannot pass on
  an empty log; the `all(...)` that follows is guarded by it. `len(client.calls) == retry_count + 1`
  and `queue.pulls == retry_count + 1` pin that the ladder actually ran.
- **Falsifiability.** Every new case was run against its own reverted fix (P1–P3) and against the
  tempting wrong fix (P4). The one control that survived P4 vacuously was found and fixed.

## Issues Encountered

- **The plan's two must_haves disagreed about the receive leg.** Resolved in favour of the truths,
  documented as deviation 1 rather than silently picking one.
- **`push_final_reveal` does not plumb `call_with_retry`'s injected `sleep`.** At production values
  a four-attempt ladder costs 15 s of real wall clock. Worked around by charging the backoff to the
  injected watchdog clock — honest for NET-07, since that is the only clock `check_once` reads —
  rather than widening a production signature for a test. Logged as deferred #12.

## Deferred items logged (not fixed)

- **#10 (major)** — the **turn loop** still runs its own 135 s wait ladder against the 60 s
  watchdog. `on_attempt` defaults to `None` deliberately: in-game, a peer that never answers is
  exactly what NET-07's threshold bounds, and the turn loop already has a different deliberate
  answer (the D-13 ladder). Which bound should win mid-game is a parameter-and-policy decision
  needing its own plan. **Not** to be closed by widening `watchdog_threshold`.
- **#11 (minor)** — four files within six lines of the gate: `turn_commit_wait.py` 145,
  `test_audit_send_failure.py` 148, `test_audit_watchdog.py` 146, `_fakes_agent.py` 144. Named
  seams recorded for each.
- **#12 (minor)** — the injected `sleep`/`clock` seams are not threaded from `AgentContext`.

## Next Phase Readiness

05-14 (G8, the hint channel) and 05-15 (G10, the declaration story) remain. Nothing in this plan
touches either surface. The league-day path is materially safer: a stalled tunnel edge at game end
now costs a bounded, correctly-attributed `audit_incomplete` instead of a silent `os._exit(1)` that
made **us** the side with no verdict and no published nonces (rule 36).

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-16*
