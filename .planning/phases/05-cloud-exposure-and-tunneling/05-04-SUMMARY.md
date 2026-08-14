---
phase: 05-cloud-exposure-and-tunneling
plan: "04"
subsystem: network
tags: [final-reveal-audit, teardown, watchdog, net-07, rules-16-22, event-log, fastmcp, httpx]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography
    provides: run_final_audit / record_technical_loss / record_audit_verdict (06-03, 06-05), the FINAL_REVEAL exchange, the corrected-game_over two-record pattern
  - phase: 05-cloud-exposure-and-tunneling
    provides: PeerRuntime's socket-owning stop() (D-56/05-02), run_with_tunnel's start-before/stop-after wrapping (05-01)
provides:
  - "EventType.AUDIT_INCOMPLETE + record_audit_incomplete: a failed OWN final-reveal push is recorded as non-accusatory evidence about us (rules 16/22)"
  - "run_final_audit(ctx, *, board_outcome): a failed push with a board outcome standing no longer aborts the audit, and no longer returns TECHNICAL_LOSS"
  - "record_technical_loss appends a CORRECTED game_over, so every post-turn-loop technical loss is durable and the log's last outcome matches the process exit code"
  - "agent_teardown.linger_for_peer: the bounded post-audit grace window, both bounds existing Table 19 fields, zero literals, zero new config keys"
  - "agent_lifecycle.stop_watchdog / stop_runtime: shutdown_cleanly's two halves, with shutdown_cleanly kept as their composition"
  - "tests/integration/late_peer_harness.py: the first two-peer harness in this repo that binds REAL loopback sockets, SEQUENCES the two sides, and actually tears down"
affects: [05-05, 05-06, 05-08, 07-reporting-and-visualization-shell]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Non-accusatory evidence records: a fault on OUR side of a two-party exchange gets its own event type, never the peer's sanction"
    - "Teardown as named, individually patchable steps (module-level helpers) so a unit order-list and an integration harness assert the SAME sequence"
    - "The non-vacuity probe pinned as a permanent second test rather than run once and discarded"

key-files:
  created:
    - src/pursuit/network/agent_teardown.py
    - tests/unit/test_audit_send_failure.py
    - tests/unit/test_agent_teardown.py
    - tests/integration/late_peer_harness.py
    - tests/integration/test_late_peer_teardown.py
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
  modified:
    - src/pursuit/network/agent_audit_verdict.py
    - src/pursuit/network/agent_audit_wiring.py
    - src/pursuit/network/agent_audit_exchange.py
    - src/pursuit/network/agent_entrypoint.py
    - src/pursuit/network/agent_lifecycle.py
    - src/pursuit/network/event_log.py
    - tests/unit/test_agent_entrypoint.py
    - tests/unit/test_agent_audit_wiring.py
    - tests/integration/test_step0_and_audit.py

key-decisions:
  - "A failed OWN final-reveal push after a real board outcome records AUDIT_INCOMPLETE and falls through to the receive+audit steps; TECHNICAL_LOSS is reserved for a turn loop that never resolved, a peer that withholds its nonces (rule 36), and a genuine AUDIT_HASH_MISMATCH (D-67)"
  - "The AUDIT_INCOMPLETE reason is a module constant, deliberately NOT a TechnicalWinReason member -- the record is not a technical win and its subject is our own send"
  - "record_audit_verdict's mismatch tail now DELEGATES to record_technical_loss rather than re-appending the same two records, so only one place owns 'which record is the log's last word'"
  - "Task 2 capture mechanism: option (b) -- module-level stop_watchdog/stop_runtime helpers in agent_lifecycle -- chosen over fake-context stop() methods, so test_agent_entrypoint.py's order list and test_late_peer_teardown.py's harness name the same three steps"
  - "The linger's bounds are NetworkParams.response_timeout (total cap) and NetworkParams.backoff_seconds (quiet interval); watchdog_threshold deliberately not borrowed"
  - "The watchdog is stopped BEFORE the linger rather than sprinkling touch() calls: by that point the turn loop is finished and there is nothing left for a freeze detector to rescue"
  - "Task 3's harness uses REAL loopback sockets, not the in-memory Client(server) transport, because only a real socket makes stop_runtime observable to the peer"

patterns-established:
  - "Fault attribution: an event type per SIDE of a two-party failure (audit_incomplete = us, technical_win = them)"
  - "Revert probes recorded verbatim with both halves -- the fix case failing pre-fix AND the controls passing pre-fix"

# Metrics
duration: 95min
completed: 2026-08-14
---

# Phase 5 Plan 04: Verdict Honesty and Bounded Teardown Grace Summary

**A failed own final-reveal push now records non-accusatory `audit_incomplete` evidence and still completes the audit instead of declaring a peer that already answered "unresponsive", and `run_agent` lingers on a Table-19-bounded grace window between the two halves of teardown so the peer's push is not cut off in the first place — measured end to end on real loopback sockets, where the pre-fix shape reproduces the 2026-08-13 remote-round artifact exactly.**

## Performance

- **Duration:** ~95 min
- **Started:** 2026-08-14T11:35Z (approx.)
- **Completed:** 2026-08-14T12:50Z (approx.)
- **Tasks:** 3 of 3
- **Files created:** 6 · **Files modified:** 9

## Accomplishments

- **The false accusation is structurally impossible.** `run_final_audit` takes the turn
  loop's own outcome; a failed OUTBOUND push with a board outcome standing writes one
  `audit_incomplete` record naming OUR send, returns no sanction, and falls through to the
  receive + audit steps. In the measured round this alone would have given machine B a
  matched `audit_verdict` instead of nothing at all.
- **Every genuine sanction still fires**, each proven by a paired control: no board outcome →
  TECHNICAL_LOSS; a peer withholding its nonces (rule 36) → TECHNICAL_LOSS; a genuine
  AUDIT_HASH_MISMATCH (D-67) → TECHNICAL_LOSS; and the `except ToolError` branch stays
  accusatory on purpose (06-06's PEER_PROTOCOL_ERROR).
- **Every post-turn-loop technical loss is now durable.** `record_technical_loss` appends a
  corrected `game_over`, closing the artifact where machine B's log ended on
  `game_over=capture` while its process exited on a technical loss.
- **Teardown no longer races a peer mid-exchange.** `linger_for_peer` drains the inbound
  queue until one quiet `backoff_seconds` window or the `response_timeout` cap — zero
  numeric literals in the module, zero new keys in any `config/*/network.json`.
- **NET-07 closed on the path this plan touches**: the watchdog is stopped BEFORE the linger,
  with the linger inside a `try/finally` so `stop_runtime` runs even on cancellation.
- **The structural test gap is closed**: the first harness in this repo that binds real
  loopback sockets, sequences the two sides, and actually performs the teardown steps.

## Task Commits

1. **Task 1: a failed own push is evidence about us — wired into production** — `8f35721` (fix)
2. **Task 2: the bounded post-audit grace window, inside the watchdog's window** — `6fd4fb9` (feat)
3. **Task 3: the sequenced two-peer proof** — `142c4b4` (test)

**Plan metadata:** the `docs(05-04): complete the verdict-honesty and bounded-teardown-grace plan` commit that carries this file (a hash cannot be embedded in the object that defines it).

## Files Created/Modified

### Created
- `src/pursuit/network/agent_teardown.py` (64/150) — `linger_for_peer`; the whole parameter
  provenance argument lives in its docstring.
- `tests/unit/test_audit_send_failure.py` (122/150) — the fix plus three paired fairness controls.
- `tests/unit/test_agent_teardown.py` (98/150) — the three linger shapes plus the NET-07 proof
  against an INJECTED `exit_action` (never `os._exit`), with its own non-vacuity control.
- `tests/integration/late_peer_harness.py` (126/150) — real-socket, sequenced two-peer harness.
- `tests/integration/test_late_peer_teardown.py` (61/150) — the three G1 assertions plus the
  pinned no-linger regression test.
- `.planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md` — one out-of-scope finding.

### Modified
- `src/pursuit/network/event_log.py` (120/150) — `EventType.AUDIT_INCOMPLETE`, additive.
- `src/pursuit/network/agent_audit_verdict.py` (120/150) — `record_audit_incomplete`;
  `record_technical_loss` appends the corrected `game_over`; `record_audit_verdict` delegates.
- `src/pursuit/network/agent_audit_wiring.py` (120/150) — `board_outcome`, the new control flow.
- `src/pursuit/network/agent_audit_exchange.py` (101/150) — re-export.
- `src/pursuit/network/agent_entrypoint.py` (99/150) — **the production wiring** and the new
  three-step teardown.
- `src/pursuit/network/agent_lifecycle.py` (144/150) — the two halves + the composition.
- `tests/unit/test_agent_entrypoint.py` (142/150) — three exact order lists + cancellation test.
- `tests/unit/test_agent_audit_wiring.py` — re-specified, not loosened.
- `tests/integration/test_step0_and_audit.py` (135/150) — `board_outcome` threaded through the
  one helper the tamper sibling and the four `gate6_*.py` scripts inherit.

## Verification (measured, not claimed)

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed!** — 0 violations |
| `uv run pytest tests/ --cov` | **1262 passed, 96.30%** (baseline 1251 / 96.26% → **+11 tests, +0.04pp**) |
| `bash scripts/check_line_limit.sh` | exit 0 |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `uv run python scripts/measure_gate6.py` | **exit 0 — all three book §10.4 criteria PASS** |
| Item 6 — production wiring | `agent_entrypoint.py:101: audit_outcome = await run_final_audit(ctx, board_outcome=outcome)`, with `outcome` from `run_turn_loop(ctx)` at `:91` |
| Item 7 — real caller | `agent_audit_wiring.py:125: record_audit_incomplete(ctx, send_verdict)` |

New-module coverage: `agent_teardown.py` **100%**, `agent_audit_verdict.py` **100%**,
`agent_audit_wiring.py` **100%**, `event_log.py` **100%**, `agent_lifecycle.py` 98%,
`agent_entrypoint.py` 87%.

### GATE-6 re-run verdict

Run twice (once after Task 1, once after Task 3), both `exit 0`:

```
GATE-6 measurement -- localhost, zero env vars
  criterion_1_four_phases_commit_reveal: PASS
  criterion_2_hash_nonce_mismatch_technical_loss: PASS
  criterion_3_step0_verified_before_move_1: PASS
```

The regenerated `docs/phases/phase-6/gate6_measurement_evidence.json` differs from the
committed one in exactly **3 lines** (two `predates_detail` mtimes and `generated_at`); every
verdict field is byte-identical. It was restored with `git checkout --` so this plan's diff
stays code-only — the same convention `/gsd:verify-work 6` used.

### Measured linger cost on a clean loopback game

`uv run python scripts/dev_launch.py`, wall clock for the whole two-process launch:

| Shape | Runs | Wall clock | Exit | Both sides' logs end on |
|---|---|---|---|---|
| **With the linger** | 2 | **17.44 s, 17.64 s** | **0** | `game_over=capture` → `audit_verdict matched=true` |
| Without (Task 2 stashed) | 4 | 14.56 / 14.67 / 14.72 / 14.44 s | 1 | police: `audit_verdict matched=true`; **thief: `game_over=capture` and nothing after it** |

**Added cost ≈ +2.8 to +3.0 s for the pair**, against a per-side quiet interval of
`backoff_seconds = 5 s` — less than one full window because the two sides linger
concurrently. Stated honestly: the baseline is **not** a like-for-like clean game, because
without the linger the thief process dies before completing its audit at all (see Issues).

## Revert-probe results (recorded verbatim)

### Task 1 — two halves, because the controls need the pre-fix call signature

**Probe A** — the file exactly as committed, run against pre-fix source (`384da44`):

```
4 failed in 3.92s
E   TypeError: run_final_audit() got an unexpected keyword argument 'board_outcome'   (x4)
```

**Probe B** — the same file with `board_outcome=` stripped from every call, so the control
cases exercise the pre-fix semantics rather than dying on the signature:

```
2 failed, 2 passed in 3.16s

FAILED test_a_failed_own_push_after_a_board_outcome_accuses_nobody
E   AssertionError: assert <Outcome.TECHNICAL_LOSS: 'technical_loss'> is not <Outcome.TECHNICAL_LOSS: 'technical_loss'>

FAILED test_a_peer_that_withholds_its_own_nonces_is_still_a_technical_loss
E   AssertionError: assert 'technical_win' == 'game_over'

PASSED test_a_failed_own_push_with_no_board_outcome_is_still_a_technical_loss
PASSED test_a_genuine_hash_mismatch_is_still_a_technical_loss
```

Read: **case 1 genuinely fails pre-fix on the substantive assertion** — the old code really
did return `TECHNICAL_LOSS` for our own failed send. Controls 2 and 4 were **already green
pre-fix** (preserved behaviour, exactly as the plan predicted). Control 3 fails pre-fix on
one sub-assertion only — the NEW corrected-`game_over` clause; its `TECHNICAL_LOSS` sanction
was already green. Control 4 was already green including its `game_over` clause, because
`record_audit_verdict`'s mismatch path had carried that record since 06-05.

### Task 2 — the `try/finally` around the linger

Replacing the finally block with three bare statements:

```
1 failed, 3 passed in 2.82s
FAILED test_the_runtime_is_stopped_even_when_the_linger_is_cancelled
E   AssertionError: assert 'linger_for_peer' == 'stop_runtime'
```

`stop_runtime` never ran — the server task and the bound port leak on a cancellation during
the grace window, exactly as the plan states.

### Task 3 — the no-linger sequence, in both directions

Running the harness with `linger=False` (the pre-Task-2 teardown):

```
E   httpx.ConnectError: All connection attempts failed
```

raised straight out of B's `run_final_audit`, so **B ends with no verdict at all** —
assertion 1 fails in its most literal form, and it is the 2026-08-13 artifact reproduced on
loopback. The reverse probe (flipping the pinned no-linger test to `linger=True`) fails too:

```
E   AssertionError: the late peer's push succeeded WITHOUT a linger -- harness proves nothing
```

so the harness genuinely distinguishes the two shapes rather than passing either way.

## Decisions Made

- **Capture mechanism (plan constraint 6): option (b)** — two thin module-level helpers
  `stop_watchdog`/`stop_runtime` in `agent_lifecycle`, so all three teardown steps stay
  patchable at `agent_entrypoint`'s namespace and the unit order list and the integration
  harness assert the SAME named sequence. No step was dropped from the order list.
- **`record_audit_verdict` now delegates its mismatch tail to `record_technical_loss`.** The
  plan asked for the corrected-`game_over` pattern in two places; making the second call the
  first is the no-duplication rule applied literally, and keeps one owner for "which record
  is the log's last word".
- **The pinned no-linger regression test asserts the PROPERTY, not the exception.** It asserts
  "B's own push did not land" (`peer_error is not None` **or** an `audit_incomplete` record),
  so it survives the deferred fix below instead of freezing today's crash as correct.
- **Task 3 uses real loopback sockets.** With the in-memory `Client(server)` transport
  `runtime.stop()` is a no-op (no server task, no listen socket), so an in-memory harness
  could not have made the teardown observable to the peer at all.
- **The watchdog is never started in the integration harness** — a real `Watchdog`'s default
  exit action is `os._exit(1)` and would kill the pytest process. NET-07 is proven in
  `test_agent_teardown.py` against an injected `exit_action` instead.

## Deviations from Plan

**None of the plan's instructions were skipped, weakened, or reinterpreted.** Three additions
beyond the literal text, all strengthenings:

**1. [Rule 2 - Missing Critical] The no-linger probe was PINNED as a test, not discarded**
- **Found during:** Task 3
- **Issue:** The plan asks for the revert probe to be run and reported. Reported-only, nothing
  stops a later change from making the linger dead code again.
- **Fix:** `test_without_the_linger_the_late_peers_own_push_is_cut_off`, asserting the durable
  property rather than the current exception type.
- **Verification:** Flipping it to `linger=True` makes it fail (recorded above).
- **Committed in:** `142c4b4`

**2. [Rule 2 - Missing Critical] The linger=True test also asserts `peer_error is None`**
- **Found during:** Task 3
- **Issue:** The harness has to capture B's audit failure to let the probe assert on it; a
  bare capture would let a real fault pass silently on the path that matters.
- **Fix:** The main test asserts no transport fault occurred at all.
- **Committed in:** `142c4b4`

**3. [Rule 2 - Missing Critical] The NET-07 test carries its own non-vacuity control**
- **Found during:** Task 2
- **Issue:** "no freeze fired" is trivially true if the window is simply too short.
- **Fix:** An identical, unstopped `Watchdog` is shown to treat the same idle window as a
  freeze (`check_once() is True`, `on_freeze` then `exit_action`, in that order).
- **Committed in:** `6fd4fb9`

---

**Total deviations:** 3 auto-fixed (all Rule 2, all test-strength additions).
**Impact on plan:** none on scope. No production behaviour beyond the plan's text was changed.

## Issues Encountered

### The pre-existing NET-07 window was FOUND by this plan, not introduced by it

Confirmed by measurement, exactly as the plan's context predicted:
`grep -rn "watchdog.touch()" src/` returns only `turn_buffer.py:111,159`,
`turn_commit_send.py:52,132`, `turn_commit_wait.py:70` — **nothing in the audit path**. So the
untouched window ALREADY spanned the whole of `run_final_audit` (receive ladder bounded at
4×30 + 3×5 = 135 s) against a `watchdog_threshold` of 60 s whose freeze action is
`os._exit(1)`. This plan **closes** that window by stopping the watchdog before the linger
rather than widening it.

### A real defect found while measuring the baseline — logged, not fixed

`httpx.ConnectError` escapes `call_with_retry` and **kills the process** on the way out.
`deadline.RETRYABLE_TRANSPORT_ERRORS` is exactly `(McpError, DeadlineExpired)` and the module
deliberately has no catch-all, so a connect failure to a peer that has already closed its
listener is not retried, not converted to a `TechnicalWin`, and not contained by
`agent_entrypoint`'s ToolError branch. Consequence when it fires: **we** become the side that
published no nonces (rule 36) and our own log carries no verdict.

Measured 4/4 runs on plain loopback with Task 2 reverted (thief stderr ends in
`httpx.ConnectError: All connection attempts failed`, `exit=1`, no `audit_incomplete`, no
`audit_verdict`). Task 2's linger closes the loopback occurrence completely (same command,
`exit 0`, both sides `audit_verdict matched=true`) but not the general case: a peer later than
one `backoff_seconds` would still hit a closed socket.

**Not fixed here, deliberately** — `deadline.py` is outside this plan's `files_modified`, its
no-retry contract was reviewed and affirmed in 06-06, and this plan's own constraints forbid
folding new failure classes into the `except ToolError` branch. Logged in full, with the
measurement and a suggested shape, at
`.planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md` #1.

### Line-count headroom

`agent_lifecycle.py` is now **144/150** and `tests/unit/test_agent_entrypoint.py` **142/150**.
Neither has room for another feature; the next change to either should split a sibling.

## Knowledge graph

Refreshed after the code landed (05-96): **6827 nodes / 12372 edges / 429 communities** (was
6577/11972/413). `GRAPH_REPORT.md` moved 476 lines. `graph.html` skipped over graphify's
5000-node viz limit, matching the 04-12/05-03/06-04 precedent (gitignored regardless).
`graphify explain "linger_for_peer"` confirms the node with 9 edges.

## User Setup Required

None — every measurement in this summary ran offline with zero environment variables set.

## Next Phase Readiness

- **G1 is closed on the code side.** Criterion 2's "verdicts agree" clause now has both halves
  it was missing: honest attribution, and a grace window that stops the failure arising.
- **05-05** (negotiated game_uid) and **05-06** (hint flow + the 17.4 s responder stagger)
  remain open; 05-06 in particular shortens the inter-side stagger the linger is currently
  absorbing.
- **05-08** (the human remote round, attempt 2) should be re-run only after 05-05 and 05-06
  land — it is the only thing that can close GATE-5 criterion 2.
- **Nothing is ticked in ROADMAP.md**, per this project's standing convention; `docs/phases/
  phase-5/TODO.md` row 05-04 is marked ◐ with the commit hashes, to be ☑'d at
  `/gsd:verify-work 5`.
- Carry-forward for whoever fixes deferred item #1: route it to `record_audit_incomplete`,
  never to a technical win — failing to CONNECT to a peer that has already torn down is
  evidence about the connection, not about the peer's honesty.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-14*

## Self-Check: PASSED

All 17 claimed files verified present on disk; all 3 task commit hashes verified in
`git log`. One correction applied during the check: the SUMMARY's cited line numbers for
the production wiring were re-measured after Task 2's docstring edit shifted them —
`agent_entrypoint.py:101` (call) and `:91` (`run_turn_loop`), confirmed by grep, not
carried over from the Task-1 measurement.
