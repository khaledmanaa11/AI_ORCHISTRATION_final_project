---
phase: 05-cloud-exposure-and-tunneling
plan: "09"
subsystem: network
tags: [net-06, deadline, retry-ladder, exception-taxonomy, httpx, fastmcp, rule-36, cloud-02]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: record_audit_incomplete + run_final_audit(board_outcome=) (05-04), the late_peer_harness real-socket sequence (05-04), SharedSecretMiddleware's 403 (05-02)
  - phase: 02-fastmcp-infrastructure
    provides: call_with_retry / RETRYABLE_TRANSPORT_ERRORS / the D-13 ladder and D-17 parameter provenance (02-07)
provides:
  - "src/pursuit/network/deadline_errors.py: the NET-06 exception taxonomy with ONE owner -- both tuples, the wrapper predicate, and the member-by-member argument for each"
  - "httpx.TransportError is a retryable transport family; httpx.HTTPError deliberately is not (HTTPStatusError is a sibling under it)"
  - "RAISE_UNRETRIED_ERRORS: ToolError + httpx.LocalProtocolError + httpx.UnsupportedProtocol -- the raise-first set, subtracting by raise-first rather than by narrowing the retryable tuple"
  - "unwraps_to_retryable: fastmcp's connect-path RuntimeError wrapper is contained by its DIRECT CAUSE, never by its class"
  - "error_evidence: one definition of the TechnicalWin.last_error text, naming the wrapper AND its cause"
  - "tests/integration/test_connect_failure_containment.py: the first real-socket assertion in this repo about what a CLOSED peer port actually raises through the production client construction"
affects: [05-07, 05-08, 07-reporting-and-visualization-shell]

# Tech tracking
tech-stack:
  added: ["httpx>=0.28.1 (promoted from transitive to declared -- src/ imports it now)"]
  patterns:
    - "Subtract by raise-first, never by narrowing the retryable tuple: a future member of a transport family stays retryable by default"
    - "Contain a wrapped exception by its DIRECT CAUSE against named tuples -- precise where catching the wrapper class would be a catch-all in all but name"
    - "A real-socket anchor beside every constructed-exception unit test, because a mocked failure proves nothing about the wire shape"

key-files:
  created:
    - src/pursuit/network/deadline_errors.py
    - tests/unit/test_deadline_httpx.py
    - tests/unit/test_deadline_wrapped_connect.py
    - tests/unit/test_transport_failure_containment.py
    - tests/integration/test_connect_failure_containment.py
  modified:
    - src/pursuit/network/deadline.py
    - pyproject.toml
    - uv.lock
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
    - docs/phases/phase-5/TODO.md

key-decisions:
  - "The retryable class is httpx.TransportError, NOT httpx.HTTPError -- HTTPStatusError's MRO goes straight to HTTPError, and the 403 from SharedSecretMiddleware is an application answer about our OWN credentials; measured non-vacuous by probe C, where HTTPError swept the production 403 into the ladder"
  - "LocalProtocolError and UnsupportedProtocol are subtracted by JOINING THE RAISE-FIRST CLAUSE, never by narrowing the tuple, so any future httpx addition under TransportError stays retryable by default"
  - "DEVIATION, measured: the widened tuple alone does NOT close the defect. fastmcp 3.4.5 re-raises a connect-path fault as RuntimeError(...) from exc, and the connect path is how every outgoing envelope starts. Contained by unwraps_to_retryable, which decides on the DIRECT CAUSE against the same two named tuples -- never on the RuntimeError class"
  - "deadline.py SPLIT into deadline_errors.py rather than compressing the taxonomy: the full argument does not fit inside the 150-code-line gate, and CLAUDE.md says split, never compress"
  - "httpx.HTTPStatusError still propagates unretried and unaccused. Correct for the 403; logged as deferred item #6 for 5xx/429, which needs a status-code policy decision this plan's constraints forbid making inline"

patterns-established:
  - "Revert probes recorded in three flavours: against the pre-fix code, against the design alternative (HTTPError), and against the partial fix (tuple-only)"
  - "An always-green control is documented with WHAT it discriminates against, so nobody reads it as vacuous"

# Metrics
duration: 105min
completed: 2026-08-14
---

# Phase 5 Plan 09: Transport Failure Containment Summary

**A dropped connection is now a bounded, measured, correctly-attributed verdict instead of a
process death — and the measurement found that the planned fix was only half of it: `httpx`'s
raw `ConnectError` is what arrives on an already-open session, but on the CONNECT path (how
every outgoing envelope in this codebase starts) fastmcp re-raises it as a `RuntimeError`
wrapper, so the widened tuple alone still reproduced the 2026-08-13 artifact verbatim.**

## Performance

- **Duration:** ~105 min
- **Started:** 2026-08-14T13:54Z
- **Completed:** 2026-08-14T15:40Z (approx.)
- **Tasks:** 2 of 2
- **Files created:** 5 · **Files modified:** 5

## Accomplishments

- **The rule-36 crash is closed on the path that actually fires.** Re-measured on the same
  `late_peer_round(linger=False)` sequence that reproduced the defect: the late peer now ends
  `game_over` → `audit_incomplete` → `message_received` → `audit_verdict{matched: true}`, with
  `peer_error is None` and **zero `technical_win` records on either side**. Pre-fix it ended on
  `game_over` and nothing after it.
- **The two boundaries earn the two different verdicts.** In-game exhaustion accuses (the peer
  really was unreachable for the whole ladder); a teardown-time failure with a board outcome
  already standing takes 05-04's `record_audit_incomplete` path and accuses nobody.
- **The 403 path is provably untouched**, and provably so by *measurement* rather than by
  assertion: written with `httpx.HTTPError` in place of `TransportError`, both 403 controls
  fail (probe C).
- **No catch-all was introduced.** `grep -rn "except Exception\|except BaseException"
  src/pursuit/network/deadline.py` → no match. Every widening is a named class or a predicate
  over named tuples.
- **The taxonomy now has one owner** (`deadline_errors.py`), reached by splitting rather than
  compressing, with `deadline.py` keeping the D-13/D-17 policy and re-exporting every name.

## Task Commits

1. **Task 1: `httpx.TransportError` joins the NET-06 retry ladder** — `f31ece5` (fix)
2. **Task 2: contain the WRAPPED connect failure, and prove both boundaries** — `f602eb3` (fix)

**Plan metadata:** the `docs(05-09): ...` commit that carries this file (a hash cannot be
embedded in the object that defines it).

## Files Created/Modified

### Created
- `src/pursuit/network/deadline_errors.py` (141/150) — the whole taxonomy: three retryable
  families with the argument for every member, the raise-first set, `unwraps_to_retryable`,
  `error_evidence`. 100% covered.
- `tests/unit/test_deadline_httpx.py` (109/150) — the ladder's httpx third: retry, transient
  recovery, the 403 control, the two local-fault controls.
- `tests/unit/test_deadline_wrapped_connect.py` (75/150) — the wrapper shape plus the two
  controls that keep it from being "retry RuntimeError".
- `tests/unit/test_transport_failure_containment.py` (146/150) — the two boundaries + three
  controls (Task 2's named artifact).
- `tests/integration/test_connect_failure_containment.py` (63/150) — the REAL-SOCKET anchor.

### Modified
- `src/pursuit/network/deadline.py` (130 → 139/150) — the raise-first clause, the wrapper
  clause, `try/except/else` so the sleep is written once, and a summary paragraph pointing at
  the sibling. 100% covered.
- `pyproject.toml` / `uv.lock` — `uv add httpx` (never pip).
- `deferred-items.md` — #1 closed with its correction; #5 and #6 added.
- `docs/phases/phase-5/TODO.md` — new 05-09 row, marked ◐ with both commit hashes.

## Verification (measured, not claimed)

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed!** — 0 violations |
| `uv run pytest tests/ --cov` | **1308 passed, 96.36%** (baseline **1293 / 96.35%** → **+15 tests, +0.01pp**, 0 failed) |
| `bash scripts/check_line_limit.sh` | exit 0 |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `uv run python scripts/measure_gate6.py` | **exit 0 — all three book §10.4 criteria PASS** |
| Item 6 — no catch-all | `grep -rn "except Exception\|except BaseException" src/pursuit/network/deadline.py` → **no match** |
| `uv run python scripts/dev_launch.py` | **exit 0**, 17 s wall clock |

New/changed module coverage: `deadline.py` **100%**, `deadline_errors.py` **100%**.

### GATE-6 re-run verdict

```
GATE-6 measurement -- localhost, zero env vars
  criterion_1_four_phases_commit_reveal: PASS
  criterion_2_hash_nonce_mismatch_technical_loss: PASS
  criterion_3_step0_verified_before_move_1: PASS
```

The regenerated `gate6_measurement_evidence.json` differs from the committed one in exactly
**four kinds of line**: two `predates_detail` mtimes, `generated_at`, and the police/thief
`hint` counts swapping 4↔5 (05-06's documented best-effort tail — the last hint a side pushes
can still be in flight when the receiver's loop exits). **Every verdict field is
byte-identical.** Restored with `git checkout --` so this plan's diff stays code-only, the
05-04 / verify-work-6 convention.

### `dev_launch.py` — 05-04's measured state, not regressed

`exit 0`, 17 s. Both sides' logs end `game_over{outcome: capture}` → `audit_verdict{matched:
true}`; **zero** `audit_incomplete` and **zero** `technical_win` on either side. A clean game
never touches any of this plan's new code paths.

### `test_late_peer_teardown.py` — measured runtime, honestly

| Tree | File runtime | The no-linger case alone |
|---|---|---|
| Task 1 only (tuple widened) | 26.40 s | 14.83 s |
| Task 2 landed (wrapper contained) | **33.28 s** | **21.42 s** |

Both cases **pass**, 3/3 runs. The growth is the point: pre-fix the failing push died on
attempt 1, and it now walks the whole ladder (4 attempts × ~1.7 s connect-refused on Windows
loopback + 3 × the harness's 1 s backoff) before returning a verdict. **Deferred item #4's
load-sensitive 0.3 s race did not reproduce** on a quiet box — the run was alone, as intended.
It was not relaxed and its assertions were not touched.

Worth recording for 05-04's benefit: the pinned no-linger test now passes through its
**`audit_incomplete` branch** rather than its `peer_error is not None` branch. 05-04 wrote it
to assert the durable PROPERTY ("B's own push did not land") instead of today's exception type,
explicitly so it would survive this fix — and it did, with no edit.

## Revert-probe results (recorded verbatim)

### Probe A — the fix cases, against the pre-05-09 tuple

`git show HEAD~1:src/pursuit/network/deadline.py > src/pursuit/network/deadline.py`, then the
containment file:

```
2 failed, 3 passed in 2.67s

FAILED test_in_game_a_dropped_connection_is_a_recorded_technical_win_not_a_crash
src\pursuit\network\turn_commit_send.py:46: in _call
    return await client.call_tool(tool_name, args)
E   httpx.ConnectError: All connection attempts failed

FAILED test_at_the_audit_boundary_a_dropped_push_accuses_nobody
src\pursuit\network\agent_audit_wiring.py:122: in run_final_audit
    send_verdict = await push_final_reveal(ctx, own_records)
E   httpx.ConnectError: All connection attempts failed
```

Read: **both fix cases fail pre-fix in the most literal form** — the exception escapes
production code rather than becoming a verdict, out of the in-game COMMIT push and out of the
final-reveal push respectively. **Controls 3, 4 and 5 were already GREEN pre-fix**, exactly as
the plan predicted: they encode preserved behaviour (case 3) and the two subtractions (cases 4
and 5), neither of which the pre-fix code could get wrong because it retried neither.

### Probe B — the PARTIAL fix (widened tuple, raise-first clause NOT extended)

```
1 failed, 4 passed in 2.60s

FAILED test_our_own_deterministic_fault_is_raised_immediately
    with pytest.raises(httpx.TransportError):
E   Failed: DID NOT RAISE TransportError
```

Case 5 is therefore **not vacuous despite being green pre-fix**: against the tuple-only version
of this plan our own malformed request is swallowed into the ladder, burning three backoffs on
the way to a false accusation.

### Probe C — the DESIGN ALTERNATIVE (`httpx.HTTPError` in place of `httpx.TransportError`)

```
2 failed, 8 passed in 2.78s

FAILED tests/unit/test_transport_failure_containment.py::test_a_403_about_our_own_secret_never_becomes_an_accusation
FAILED tests/unit/test_deadline_httpx.py::test_a_403_is_not_swept_into_the_retry_ladder
    with pytest.raises(httpx.HTTPStatusError, match="403"):
E   Failed: DID NOT RAISE HTTPStatusError
```

Both 403 controls fail. The `TransportError`-not-`HTTPError` distinction is therefore
**measured**, not an MRO argument.

### Probe D — the whole plan, against the shape production really produces

The one that changed the plan. `late_peer_round(linger=False)` re-run with **Task 1 landed and
nothing else**:

```
B (thief, LATE): last 5 = ['message_sent','message_sent','message_received','message_sent','game_over']
    counts: audit_incomplete=0 technical_win=0 audit_verdict=0
peer_error: RuntimeError Client failed to connect: All connection attempts failed
```

The artifact, **unfixed**. See deviation 3.

## What the thief's log ACTUALLY ends with (the plan's explicit question)

Post-fix, `linger=False` — the worst case, with A's listener genuinely closed:

```
B (thief, LATE): last 5 = ['message_sent','game_over','audit_incomplete','message_received','audit_verdict']
    counts: audit_incomplete=1 technical_win=0 audit_verdict=1
    audit_incomplete: {"reason": "own_final_reveal_send_failed",
                       "last_error": "RuntimeError: Client failed to connect: All connection
                                      attempts failed (cause: ConnectError: All connection
                                      attempts failed)",
                       "retries_attempted": 4}
    audit_verdict:    {"matched": true}
peer_error: None ; final_a: Outcome.CAPTURE ; final_b: Outcome.CAPTURE
```

**`audit_incomplete` + `audit_verdict`, not `audit_incomplete` + `technical_win`.** The
fall-through's `receive_final_reveal` did **not** exhaust, because A had already pushed its own
FINAL_REVEAL onto B's queue before tearing down — so B's receive was satisfied from the queue
and the audit completed and matched. That is measured, not assumed: the plan explicitly warned
that the other outcome was possible and that whichever fired was the point. Nothing here
weakens the receive-side sanction; a peer that genuinely withholds its nonces still exhausts
that ladder and still calls `record_technical_loss` (rule 36), which
`test_audit_send_failure.py::test_a_peer_that_withholds_its_own_nonces_is_still_a_technical_loss`
continues to pin.

Case 2 reached 05-04's `record_audit_incomplete` path **exactly as predicted, with no change
to 05-04's code**.

## Decisions Made

- **Split, not compress.** The full taxonomy argument takes deadline.py to ~162 code lines
  against a 150 gate. CLAUDE.md is explicit ("split files, never compress code to fit"), and
  this repo has four precedents for the exact move (`agent_audit_verdict.py`, `game_identity.py`,
  `secret_wiring.py`, `turn_hint_buffer.py`). `deadline.py` re-exports all three names, so every
  pre-05-09 importer resolves unchanged — verified by grep across `src/` and `tests/`.
- **Contain the wrapper by CAUSE, never by class.** `except RuntimeError` alone would be a
  catch-all in all but name (our own bugs raise `RuntimeError`). `unwraps_to_retryable` re-raises
  anything whose cause is absent, unrelated, or itself raise-first — so a wrapped scheme-less URL
  still fails loudly, pinned by its own control.
- **`error_evidence` names the wrapper AND its cause.** The audit-incomplete record a grader
  reads now distinguishes "the session dropped mid-call" from "we never connected at all".
  Existing assertions (`"McpError" in last_error`) are unaffected: a direct exception has no
  cause and its text is byte-identical to before.
- **`httpx.HTTPStatusError` deliberately keeps propagating.** Correct for the 403 by this
  plan's own constraint 2. Logged as deferred item **#6** for 5xx/429, which is genuinely
  reachable mid-game through ngrok and needs a status-code policy this plan may not invent.

## Deviations from Plan

**Three deviations. One is substantive and changed what the plan delivers; two are line-gate
splits. Nothing in the plan was skipped, weakened or reinterpreted.**

**1. [Rule 3 - Blocking] `deadline.py` split into `deadline_errors.py`**
- **Found during:** Task 1, before writing the docstring.
- **Issue:** `deadline.py` measured 119 code lines; the taxonomy the plan asks for is ~40 more,
  landing at ~162 against the 150-line gate.
- **Fix:** Relocate-and-re-export, the established house move. `deadline.py` keeps the D-13/D-17
  policy and a summary paragraph; the sibling owns the taxonomy.
- **Consequence for the plan's verify block:** `grep -n "TransportError"
  src/pursuit/network/deadline.py` shows the reasoning paragraph and the raise-first comment,
  but the tuple ENTRY is now in the sibling. Stated plainly rather than glossed.
- **Committed in:** `f31ece5`

**2. [Rule 3 - Blocking] Two test-file splits**
- **Found during:** Tasks 1 and 2.
- **Issue:** `test_deadline.py` (104) and `test_deadline_retry.py` (105) have no room for the
  new cases; `test_transport_failure_containment.py` landed at 146 with no room for the wrapper
  cases.
- **Fix:** `tests/unit/test_deadline_httpx.py` and `tests/unit/test_deadline_wrapped_connect.py`,
  both importing the shared fakes from `test_deadline.py` rather than duplicating them (QUAL-02,
  the precedent `test_deadline_retry.py` itself set). **`test_deadline.py` and
  `test_deadline_retry.py` are byte-unmodified** — they pin the ToolError and McpError contracts
  this plan must not disturb, exactly as the plan required.
- **Committed in:** `f31ece5`, `f602eb3`

**3. [Rule 1 - Bug] THE SUBSTANTIVE ONE: the planned fix did not fix the defect**
- **Found during:** Task 2, re-running `late_peer_round(linger=False)` to answer the plan's own
  question about what the thief's log ends with.
- **Issue:** With Task 1 landed and passing every test, the late peer **still** ended on
  `game_over` with nothing after it, and `peer_error` was
  `RuntimeError: Client failed to connect: All connection attempts failed`. Cause: `httpx`'s raw
  exception is what arrives on an ALREADY-OPEN session (`client.call_tool` — the shape 05-04
  happened to capture, and the shape the plan was written from), but on the CONNECT path fastmcp
  3.4.5 catches it at `client/client.py:616-624` and re-raises
  `RuntimeError(f"Client failed to connect: {exc}") from exc`, preserving only
  `httpx.HTTPStatusError` and `McpError` unwrapped. **Every outgoing envelope in this codebase
  opens a fresh `async with ctx.runtime.client()`, so the wrapped shape is the COMMON one.**
- **Verified before fixing, against the real client:** a `fastmcp.Client` built exactly the way
  `PeerRuntime.client()` builds it, pointed at a closed loopback port, raises
  `builtins.RuntimeError` with `__cause__ = httpx.ConnectError`. Confirmed in the fastmcp source
  as well as by measurement.
- **Fix:** `unwraps_to_retryable` + `error_evidence` in `deadline_errors.py`, and a
  cause-guarded `except RuntimeError` clause in `call_with_retry`. No catch-all: the decision is
  made by the same two named tuples as everything else.
- **Why not Rule 4:** no new structure, no new dependency, same module, same decision rule — and
  without it the plan's own must_have truth #1 ("a transport-level connection failure never kills
  the process") is false.
- **Proven by:** `test_deadline_wrapped_connect.py` (3 cases incl. two controls),
  `test_connect_failure_containment.py` (2 real-socket cases), and probe D above.
- **Committed in:** `f602eb3`

---

**Total deviations:** 3 auto-fixed (2 × Rule 3 splits, 1 × Rule 1 — the fix that makes the plan
true). **Impact on scope:** two source functions and two test files beyond the plan's
`files_modified`, all inside `deadline.py`'s own module boundary.

## Issues Encountered

### A mocked failure proved nothing about the wire shape — again

The plan, the deferred item, and 05-04's own measurement all named `httpx.ConnectError`, and
five unit tests plus a real-socket 403 anchor all passed against that reading while the actual
defect stayed open. The only thing that caught it was re-running the end-to-end harness and
reading the peer's log. `test_connect_failure_containment.py` exists so the next reader gets the
wire shape asserted rather than inferred, and it asserts fastmcp's wrapper explicitly, so a
version bump that changes the wrapping fails loudly instead of silently reopening the crash.

### `httpx.HTTPStatusError` from a 5xx/429 is still an uncaught mid-game crash

`mcp/client/streamable_http.py` calls `response.raise_for_status()` at five sites, so any non-2xx
becomes `HTTPStatusError` — and fastmcp's connect path preserves that class unwrapped. For the
403 that is deliberate and correct. For a 502 from ngrok when the peer's local server blips, or a
429 on a free-tier rate limit, it is the same rule-36 crash class this plan just closed, through
a different door. Logged as deferred item **#6** with a suggested shape; not fixed, because
branching on HTTP status codes is a policy decision this plan's own constraint 2 forbids making
inline.

### Line-count headroom

`tests/unit/test_transport_failure_containment.py` is **146/150** and
`src/pursuit/network/deadline_errors.py` **141/150**. Neither has room for another case; the next
change to either should split first.

## Knowledge graph

Refreshed after the code landed (05-96): **7127 nodes / 12937 edges / 437 communities** (was
7016 / 12737 / 438). `graph.html` skipped over graphify's 5000-node viz limit, matching the
04-12 / 05-03 / 05-04 / 06-04 precedent (gitignored regardless). `graphify explain
"unwraps_to_retryable"` resolves to `deadline_errors.py` L142 with **`call_with_retry` as a
production caller**, not a test-only node.

## User Setup Required

None — every measurement in this summary ran offline with zero environment variables set.

## Next Phase Readiness

- **Deferred item #1 is closed**, on the shape production actually produces, measured end to end.
  The general case 05-04 could not close with its linger — a peer later than the grace window —
  is now a contained verdict rather than a crash.
- **05-07** (G5, keyless LLM made legible) and **05-08** (the HUMAN remote round, attempt 2 — the
  only thing that can close GATE-5 criterion 2) remain open.
- **Carry-forward for 05-08:** if the round produces a 502 or 429 from either tunnel, expect the
  crash described in deferred item #6, and capture the console output — it is the missing
  measurement that item needs.
- **Nothing is ticked in ROADMAP.md**, per this project's standing convention;
  `docs/phases/phase-5/TODO.md` gained a 05-09 row marked ◐ with both commit hashes, to be ☑'d at
  `/gsd:verify-work 5`.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-14*

## Self-Check: PASSED

All 10 claimed files verified present on disk; both task commit hashes verified in `git log`.
Four claims RE-MEASURED at self-check time rather than carried over from earlier in the run:

- every cited line count re-run through `check_line_limit.sh` and matching this file exactly
  (146 / 141 / 139 / 109 / 75 / 63);
- `grep -rn "except Exception\|except BaseException" src/pursuit/network/deadline.py` → **no
  match** (verification item 6);
- `git diff --stat 384da44 HEAD -- tests/unit/test_deadline.py tests/unit/test_deadline_retry.py`
  → **empty**, so both pre-existing NET-06 test files are byte-unmodified as the plan required;
- the re-exports resolve and are the SAME objects: `RETRYABLE_TRANSPORT_ERRORS` =
  `[McpError, DeadlineExpired, TransportError]`, `RAISE_UNRETRIED_ERRORS` =
  `[ToolError, LocalProtocolError, UnsupportedProtocol]`, and
  `deadline.DeadlineExpired is agent_teardown.DeadlineExpired` → `True`, so the split did not
  fork the exception identity any `except` clause depends on.
