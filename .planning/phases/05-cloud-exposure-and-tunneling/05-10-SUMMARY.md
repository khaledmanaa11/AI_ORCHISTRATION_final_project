---
phase: 05-cloud-exposure-and-tunneling
plan: "10"
subsystem: infra
tags: [audit, rule-36, httpx, fastmcp, retry-ladder, peer-data, commit-reveal, ngrok]

# Dependency graph
requires:
  - phase: 05-04
    provides: "record_audit_incomplete / record_technical_loss, the two verdict sinks, and the board_outcome wiring this plan pins"
  - phase: 05-05
    provides: "the _audit_one verify_reveal containment whose shape this plan follows and whose class tuple it widens"
  - phase: 05-09
    provides: "deadline_errors.py, the NET-06 exception taxonomy this plan extends from class to status"
provides:
  - "audit_peer_records is TOTAL over peer-supplied input -- every shape a peer can send reaches a recorded verdict, and every malformed one still loses under rule 36"
  - "join-key USABILITY as the malformed test, so an honest peer whose turn is an integral float is not technically-lost"
  - "RETRYABLE_STATUS_CODES {429, 500, 502, 503, 504} and retryable_status -- an ngrok 502 costs a backoff instead of the game"
  - "the 403 contract unchanged: a 4xx is re-raised unretried and accuses nobody"
  - "the boundary rule stated once in source, naming all six instances of the peer-data crash pattern"
  - "the board_outcome=outcome production wiring pinned by a value-identity test"
affects: [05-08, 06, 07, league-day]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Peer-data totality: any function reading a structure the PEER sent returns a named mismatch, never raises"
    - "Malformed = unusable as a join key, never 'not a Python int' -- permissive on integral floats, strict on shape"
    - "Retryability by STATUS where the exception class cannot answer, via an ENUMERATED frozenset, never a range"
    - "Split-and-re-export at the 150-line gate; prose relocates to the module that owns the argument"

key-files:
  created:
    - src/pursuit/security/audit_shape.py
    - src/pursuit/security/audit_record.py
    - src/pursuit/network/deadline_status.py
    - src/pursuit/network/deadline_wait.py
    - tests/unit/test_audit_hostile_records.py
    - tests/unit/test_transport_status_containment.py
    - tests/unit/test_agent_entrypoint_audit_wiring.py
  modified:
    - src/pursuit/security/audit.py
    - src/pursuit/network/handshake_step0.py
    - src/pursuit/network/deadline.py
    - src/pursuit/network/deadline_errors.py
    - tests/unit/test_handshake_step0_declaration.py
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md

key-decisions:
  - "The turn test is join-key USABILITY, not isinstance(turn, int): an integral float normalises via int() and proceeds, because JSON has no int/float distinction and a type check would technically-lose an honest peer (rules 16/22)"
  - "An unreadable records CONTAINER yields ONE malformed mismatch and does NOT fall through to the coverage check, so it stays distinguishable from the {'records': []} evasion in our own evidence"
  - "_missing_turns SKIPS an unparseable entry rather than bailing, so one garbage record cannot delete rule-36 coverage for every valid turn"
  - "RETRYABLE_STATUS_CODES is ENUMERATED, never 'any 5xx': 501 and 505 are deterministic refusals that would burn the ladder and end in a false accusation"
  - "A non-object step0_declaration (instance 6) resolves to the EXISTING digest-only outcome, not a STEP0_MISMATCH abort -- a hard abort would add a false-accusation path and buy nothing, since a peer can already reach that outcome by sending no declaration"
  - "Three files were split rather than compressed; audit.py landed at exactly 150/150 first and deadline.py BREACHED at 152, both fixed by relocate-and-re-export"

patterns-established:
  - "The boundary rule lives as a module COMMENT in security/audit.py naming every instance, so a seventh is a review failure rather than a discovery"
  - "Paired controls carry the discrimination: every fix ships with the honest case it must NOT break, and that control is proven to fail against the tempting wrong rule"

# Metrics
duration: 118min
completed: 2026-08-14
---

# Phase 05 Plan 10: Close the Peer-Data Crash Paths Summary

**Every shape a peer can put on the wire now reaches a recorded verdict instead of killing the
process — plus an ngrok 502 costs a backoff rather than the game, while a 403 about our own
secret still accuses nobody.**

## Performance

- **Duration:** ~118 min
- **Started:** 2026-08-14T15:05Z
- **Completed:** 2026-08-14T17:03Z
- **Tasks:** 3 of 3
- **Files created:** 7 · **Files modified:** 6

## Accomplishments

- `audit_peer_records` is total over peer input. Nine hostile shapes that raised at HEAD now
  return named mismatches, and every one of them still **loses** under rule 36.
- The recurring pattern is closed and **named in source**. The boundary rule sits as a module
  comment in `security/audit.py` listing all six instances, so a seventh is a review failure.
- A **sixth instance was found** during the sweep — stated plainly below, since the plan asked
  for the answer either way.
- The likeliest real league-day failure (ngrok 502 while the peer's server is briefly down) is
  now a backoff, and the 403 anchor `test_secret_channel.py` passes **unedited**, 3/3.
- The `board_outcome=outcome` production wiring is pinned by a test that fails without it.

## Task Commits

1. **Task 1: a malformed peer FINAL_REVEAL is a mismatch, not a crash** — `ab4951b` (fix)
2. **Task 2: a gateway blip is transient, a 403 is still ours** — `49b58ac` (feat)
3. **Task 3: pin the wiring that has no test, and correct the record** — `6a9df51` (test)

## The 05-VERIFICATION hostile-shape probe, before and after

Same probe script, same fixtures, run against the shipped function at the pre-plan baseline
`495aa9d` and again at `6a9df51`. Verbatim output.

| # | Peer sends | BEFORE (HEAD `495aa9d`) | AFTER (`6a9df51`) |
|---|---|---|---|
| A | `records` is a string | `RAISES TypeError: string indices must be integers, not 'str'` | `[(-1, False, 'malformed final reveal: records is str, not a list -- no nonces could be read from it (rule 36)')]` |
| B | entry is a string | `RAISES TypeError: string indices must be integers, not 'str'` | `[(-1, False, 'malformed final-reveal record: expected an object, got str'), (1, False, 'turn 1: committed and revealed in-game but absent from final reveal')]` |
| C | entry has no `turn` | `RAISES KeyError: 'turn'` | `[(-1, False, "malformed final-reveal record: no 'turn' field"), (1, False, '...absent from final reveal')]` |
| D | `turn` is `"1"` | `RAISES TypeError: '<' not supported between instances of 'int' and 'str'` | `[(-1, False, "malformed final-reveal record: turn '1' (str) cannot serve as a join key"), (1, False, '...absent...')]` |
| E | `turn` is `None` | `RAISES TypeError: '<' not supported between instances of 'int' and 'NoneType'` | `[(-1, False, 'malformed final-reveal record: turn None (NoneType) cannot serve as a join key'), (1, False, '...absent...')]` |
| F | `turn` is `[1]` | `RAISES TypeError: unhashable type: 'list'` | `[(-1, False, 'malformed final-reveal record: turn [1] (list) cannot serve as a join key'), (1, False, '...absent...')]` |
| G | `turn` is `1.5` | `returns [(1, False, 'absent from final reveal'), (1.5, False, 'turn 1.5: no observed commit')]` — no crash, but a nonsense detail | `[(-1, False, 'malformed final-reveal record: turn 1.5 (float) cannot serve as a join key'), (1, False, '...absent...')]` |
| H | valid + malformed mixed | `RAISES KeyError: 'turn'` | `[(-1, False, "…no 'turn' field"), (1, True, 'turn 1: matched')]` |
| I | `intent` is `"maybe"` | `RAISES ValueError: build_commit_payload: intent must be one of ['lie', 'truth'], got 'maybe'` | `[(1, False, "turn 1: malformed final-reveal payload -- build_commit_payload: intent must be one of ['lie', 'truth'], got 'maybe'")]` |
| J | `intent` is `None` | `returns [(1, False, 'malformed final-reveal payload -- …must be a str, got NoneType')]` (already contained) | unchanged |
| K | `nonce` is `""` | `RAISES ValueError: build_commit_payload: nonce must be a non-empty str` | `[(1, False, 'turn 1: malformed final-reveal payload -- build_commit_payload: nonce must be a non-empty str')]` |

**Controls, before and after:**

| Control | BEFORE | AFTER |
|---|---|---|
| honest peer | `[(1, True, 'turn 1: matched')]` | `[(1, True, 'turn 1: matched')]` |
| honest peer, `turn` = float `3.0` | `[(3.0, True, 'turn 3.0: matched')]` | `[(3, True, 'turn 3: matched')]` |
| `{"records": []}`, 3 turns observed | 3 × `absent from final reveal` | 3 × `absent from final reveal` |

Case **K** is a genuine addition to the plan's own account of instance 5: the plan named the
`intent` ValueError, and the empty-`nonce` ValueError from the same function is a second source
of the same class. The single widening to `(TypeError, KeyError, ValueError)` closes both.

## Revert probes — every claim earned its discrimination

| # | Probe | Result |
|---|---|---|
| M1 | `join_key_turn` rewritten as `isinstance(turn, int)` | **1 failed** — `test_control_an_honest_peer_whose_turn_arrives_as_a_float_is_still_matched`: `assert [(-1, False), (3, False)] == [(3, True)]`. The float control owes exactly this discrimination and delivers it |
| M2 | `_missing_turns` reverted to `{entry["turn"] for entry in peer_records}` | **4 failed**, including `test_one_garbage_entry_does_not_disable_the_coverage_check_for_the_valid_turns` (`KeyError: 'turn'`) |
| M3 | instance-6 guard removed from `_step0_verified` | **4 failed** — `AttributeError: 'float' object has no attribute 'get'` |
| M4 | `deadline.py`'s whole `HTTPStatusError` clause removed (pre-Task-2 ladder) | **5 failed** — 429/500/502/503/504 all raise instead of recording a verdict |
| M5a | `retryable_status` widened to *all* `HTTPStatusError` | **7 failed** — every 400/403/404/501/505 case, the enumeration test, and the wrapped-403 test. Our own wrong secret becomes an accusation |
| M5b | `retryable_status` written as `429 or 500 <= code < 600` (**the "any 5xx" rule**) | **3 failed** — 501 and 505 swept in; `assert True is False … retryable_status(HTTPStatusError("Server error '501 Not Implemented' …"))`. This is the M2 control the plan required |
| M6 | `board_outcome=outcome` removed from `agent_entrypoint.py:110` | **2 failed** — `assert None is <object …>`. The four pre-existing `test_agent_entrypoint.py` cases still **passed**, which is precisely why nothing caught it before |

## Was a SIXTH instance found? — **YES**

Stated plainly because the plan asked for the answer either way, and a negative would have been
worth recording too.

**Instance 6: `handshake_step0._step0_verified` raises `AttributeError` on a peer
`step0_declaration` that is not an object.** Measured before the fix:

```
'a-string'  -> RAISES AttributeError 'str' object has no attribute 'get'
['list']    -> RAISES AttributeError 'list' object has no attribute 'get'
7           -> RAISES AttributeError 'int' object has no attribute 'get'
```

`evaluate`'s try/except wraps the DECODE block only, so this is uncaught; `respond_to_handshake`
advertises itself as "Pure, synchronous, never raises", which was simply false for this shape.
On the **outbound** half it escapes `perform_handshake` into `run_agent` and kills the process
**at the handshake, before move 1** — so a foreign league implementation whose declaration
container shape merely differs costs us the game without one move being played.

Treated exactly as the plan directed: it resolves to the **existing digest-only outcome**, named
distinctly in the detail (`…container is not an object -- unreadable, treated as digest-only`).
A hard `STEP0_MISMATCH` abort was considered and declined — there is no content to verify, a
peer wanting that outcome can already have it by sending no declaration at all (so no evasion is
opened), and aborting would add a **new** false-accusation path against an honest foreign shape,
which is the exact class of defect this phase has corrected four times already.

The sweep also covered the other peer-data readers and found them **already total**:
`move_payload.decode` contains `(KeyError, ValueError, TypeError)` by design;
`audit_state.state_binding_detail` reads every field with `.get()`;
`turn_hint_buffer._usable_stamp` refuses non-int stamps; `tools._accept` translates
`Envelope.from_dict`'s three exception classes into a descriptive `ToolError`.

## Verification results

| # | Gate | Result |
|---|---|---|
| 1 | `uv run ruff check .` | **All checks passed!** (0 violations) |
| 2 | `uv run pytest tests/ --cov` | **1361 passed, 1 failed, 96.51%** — see the flake note below. Baseline 1327/96.37% → **+35 tests, +0.14 pp** |
| 3 | `bash scripts/check_line_limit.sh` | exit **0** |
| 4 | `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| 5 | `uv run python scripts/measure_gate6.py` | **all three §10.4 criteria PASS** (`criterion_1_four_phases_commit_reveal`, `criterion_2_hash_nonce_mismatch_technical_loss`, `criterion_3_step0_verified_before_move_1`) |
| 6 | `grep "except Exception\|except BaseException"` in `audit.py` + `deadline*.py` | **no match** |
| 7 | `uv run python scripts/dev_launch.py` | exit **0** |

**dev_launch, measured:** one shared uid **`ac3a02d87460b28e`** as the file stem on *both* sides;
police 42 records, thief 41; **both** end `audit_verdict matched=True`; **zero** `technical_win`
and **zero** `audit_incomplete` on either side; both ledgers (`<uid>.ledger.jsonl`) and all four
declarations (own + peer, both roles) present under that uid. The trailing `WinError 995` /
lifespan `CancelledError` is the documented proactor teardown noise, printed after exit 0.

**The one failing test is the documented load flake, and attribution was measured, not assumed.**
`tests/integration/test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`
asserts `max()` of a per-turn wall-clock decision time against a 50 ms budget. Measured under
`--cov`: `cop max=29.955ms`, a 40 % margin over 35 turns, so one scheduling hiccup trips it.
05-VERIFICATION recorded the identical failure on 2026-08-14. Re-run alone: **4/4 pass** in
0.20–0.34 s. Decisive attribution: `pytest --collect-only` places it at **item 3 of 1362**,
while every test this plan adds is at item 624 or later — it runs *before* all of them and
cannot be affected by them. Nothing was relaxed and nothing was skipped.

## Files Created/Modified

**Created**

- `src/pursuit/security/audit_shape.py` — `join_key_turn` / `container_detail` / `NO_USABLE_TURN`.
  The one shape gate, with the join-key-usability argument in full.
- `src/pursuit/security/audit_record.py` — `AuditRecord` / `all_matched`, re-exported by `audit.py`.
- `src/pursuit/network/deadline_status.py` — `RETRYABLE_STATUS_CODES` / `retryable_status`, and
  the inherited `httpx.HTTPError`-is-not-the-class argument.
- `src/pursuit/network/deadline_wait.py` — `bounded` / `wait_for_opponent`, re-exported by `deadline.py`.
- `tests/unit/test_audit_hostile_records.py` — the matrix plus three controls (17 tests).
- `tests/unit/test_transport_status_containment.py` — the status boundaries plus the 501 control (12 tests).
- `tests/unit/test_agent_entrypoint_audit_wiring.py` — the `board_outcome` value-identity pin (2 tests).

**Modified**

- `src/pursuit/security/audit.py` — the boundary-rule comment naming all six instances; the shape
  gate; `(TypeError, KeyError, ValueError)`; the skip-not-bail coverage check; the container guard.
- `src/pursuit/network/handshake_step0.py` — instance 6.
- `src/pursuit/network/deadline.py` — the status clause; the corrected `call_with_retry` docstring.
- `src/pursuit/network/deadline_errors.py` — `_is_retryable` joining class and status in one place.
- `tests/unit/test_handshake_step0_declaration.py` — 4 parametrized instance-6 cases.
- `.planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md` — see below.

## Deferred-items record

- **#2** — re-measured, **still open** at 148/150, with a dated table of the three splits this
  plan took rather than logging a fourth instance of the same item.
- **#3** — the refuted line corrected **by appending a dated correction**, never by rewriting.
  The original text stands verbatim. The correction adds what the note could not have known: the
  containment was also too narrow *for the call it wrapped* (`ValueError`).
- **#5** — the 429 exhaustion residual **appended here**, not filed as a new item, because it is
  identical in kind to the ours-versus-theirs ambiguity already examined and accepted.
- **#6** — **CLOSED by 05-10**, with both deviations from its own suggested shape recorded.
- **#7** — **written into the file for the first time**, in full, closure included.
  05-VERIFICATION recorded it in its frontmatter and anti-patterns table but never added it here,
  so a reader following the pointer found nothing.

## Decisions Made

1. **Join-key usability, never `isinstance`.** Verified at HEAD that a float `3.0` turn was
   already audited correctly and returned `matched`; a type check would have converted that
   honest peer into a technical loss (rules 16/22).
2. **The container guard does not fall through to the coverage check.** An unreadable peer and
   the `{"records": []}` evasion both lose, but they must stay distinguishable in the evidence.
3. **Enumerated status set.** 501/505 excluded because they are deterministic — the mirror of
   05-09's `LocalProtocolError` subtraction, not a new principle.
4. **Instance 6 is lenient, not accusatory**, for the reasons argued in that module's docstring.
5. **Split, never compress**, three times.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing Critical] Instance 6: `_step0_verified` raises on a non-object declaration**
- **Found during:** Task 1, sweeping for a sixth instance as the plan directed.
- **Issue:** `AttributeError` on peer-controlled data, escaping `perform_handshake` into
  `run_agent` and killing the process at the handshake before move 1.
- **Fix:** Guard the container; resolve to the existing digest-only outcome with a distinct detail.
- **Files modified:** `src/pursuit/network/handshake_step0.py`,
  `tests/unit/test_handshake_step0_declaration.py`
- **Verification:** 4 parametrized cases; revert probe M3 fails without the guard.
- **Committed in:** `ab4951b`
- **Authorised by the plan:** *"If you find a SIXTH instance while working, treat it exactly the
  same way and say so in the SUMMARY."*

**2. [Rule 3 — Blocking] `audit.py` landed at exactly 150/150; split `audit_record.py`**
- **Found during:** Task 1, measuring after the guards landed.
- **Issue:** The gate passed, but at zero headroom — one line worse than deferred item #2's
  148/150, and a trap for the next change.
- **Fix:** Relocate `AuditRecord`/`all_matched` behind a re-export. `audit.py` → **142/150**.
- **Committed in:** `ab4951b`

**3. [Rule 3 — Blocking] `deadline.py` BREACHED at 152; split `deadline_wait.py`**
- **Found during:** Task 2. The plan pre-authorised the `deadline_errors.py` seam but the
  overflow landed in `deadline.py`, which it had measured at 139 with 11 free.
- **Issue:** Line gate **FAILED**: `VIOLATION: src/pursuit/network/deadline.py has 152 code lines`.
- **Fix:** Two moves, neither of them compression. The 05-10 argument was *relocated* into
  `deadline_status.py` (keeping a duplicate copy in `deadline.py` would itself have violated the
  no-duplication rule), and `bounded`/`wait_for_opponent` were split into `deadline_wait.py` and
  re-exported. `deadline.py` → **134/150**.
- **Verification:** line gate exit 0; all 1291 unit tests pass; every importer
  (`turn_buffer`, `turn_commit_wait`, `agent_teardown`, `test_deadline.py`) unchanged.
- **Committed in:** `49b58ac`

**4. [Rule 1 — Bug] `call_with_retry`'s docstring became false**
- **Found during:** Task 2. It stated an `HTTPStatusError` "matches no clause here and
  propagates" — true before this plan, wrong after it.
- **Fix:** Rewritten to describe the actual behaviour (retryable statuses laddered, everything
  else re-raised from inside its own clause).
- **Committed in:** `49b58ac`

**5. [Rule 2 — Missing Critical] Deferred item #7 did not exist in `deferred-items.md`**
- **Found during:** Task 3. 05-VERIFICATION referenced item 7 by number in two places but never
  wrote it into the file, leaving a dangling pointer.
- **Fix:** Written in full — measured before/after, the join-key reasoning, the coverage-check
  side door, instance 6 — with its closure.
- **Committed in:** `6a9df51`

---

**Total deviations:** 5 auto-fixed (2 missing-critical, 2 blocking, 1 bug).
**Impact on plan:** No scope creep. Two are line-gate mechanics the plan explicitly
pre-authorised; two close the same defect class the plan exists to close; one repairs a
documentation pointer. Every plan constraint was honoured: no catch-all, no `--no-verify`, no
test weakened or deleted, and `test_audit_coverage.py`, `test_audit_turn_binding.py`,
`test_audit_state_binding.py` and `tests/integration/test_secret_channel.py` all pass
**unmodified** — `git diff 495aa9d -- <those four> config/` is empty.

## Issues Encountered

- **A `git checkout --` during revert probe M3 reverted the whole file**, wiping the instance-6
  fix rather than just the probe patch. Caught immediately, the fix was re-applied and re-tested.
  Subsequent probes used a scratchpad backup-and-restore instead of `git checkout`.
- **`SIM300` (Yoda condition)** on `RETRYABLE_STATUS_CODES == frozenset({...})`. Rewritten as
  `sorted(...) == [...]`, which reads better anyway. Not suppressed.

## Line-gate accounting

| File | Before | After |
|---|---|---|
| `security/audit.py` | 131 | **142** |
| `network/deadline.py` | 139 | **134** |
| `network/deadline_errors.py` | 141 | **140** |
| `security/audit_shape.py` | — | 73 |
| `security/audit_record.py` | — | 26 |
| `network/deadline_status.py` | — | 69 |
| `network/deadline_wait.py` | — | 35 |

## Knowledge graph

Refreshed after the code landed: **7287 nodes, 13159 edges, 439 communities** (was 6738/12190).
`GRAPH_REPORT.md` and `graph.json` copied into `.planning/graphs/`; spot-checked
`graphify explain "retryable_status"` — present at `deadline_status.py:70`, degree 6, with the
`call_with_retry` and `_is_retryable` call edges resolved.

## User Setup Required

None — no external service configuration required. No new config key, no new numeric leaf, no
secret. `RETRYABLE_STATUS_CODES` members are structural RFC 9110 constants, not PARAMETERS.md
values; `git diff` over `config/` is empty for this plan.

## Next Phase Readiness

- **05-08 (the remote round) is no longer being sent into a known crash path.** The three shapes
  most likely to end it — an unparseable peer FINAL_REVEAL, an ngrok 502, and a foreign Step-0
  declaration container — now each produce a recorded verdict instead of a dead process.
- **GATE-5 criterion 2 remains open and remains human-only.** Nothing here can close it: it needs
  a second physical machine on a different network and two operators, per
  `docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md`.
- **Open deferred items after this plan:** #2 (minor, 148/150), #4 (minor, load-sensitive test),
  #5 (accepted residual, now including the 429 half). Items #1, #3, #6 and #7 are closed.

## Self-Check: PASSED

Every claim above re-verified against disk and git rather than against memory.

- **7 created files present** — `audit_shape.py`, `audit_record.py`, `deadline_status.py`,
  `deadline_wait.py`, and the three new test files. Plus this SUMMARY and
  `.planning/graphs/GRAPH_REPORT.md`.
- **3 task commits present** — `ab4951b`, `49b58ac`, `6a9df51`, each confirmed by
  `git log --oneline --all`.
- **The four untouched anchors are genuinely untouched** —
  `git diff 495aa9d -- test_audit_coverage.py test_audit_turn_binding.py
  test_audit_state_binding.py test_secret_channel.py config/` returns **nothing**.
- **One correction made during this self-check, recorded rather than quietly fixed:** an earlier
  draft named the pre-plan baseline as `384da44`. That commit is an ancestor of HEAD but roughly
  thirty commits back — the real parent of `ab4951b` is **`495aa9d`**, and the before-probe and
  the anchor diffs were both run from there. Compared against `384da44` the two audit test files
  *do* differ, which would have made the "unmodified" claim above false as written. The baseline
  is corrected throughout.
- **Working tree** clean apart from `docs/phases/phase-6/gate6_measurement_evidence.json` (the
  GATE-6 measurement artifact this plan's own verification regenerated) and `.planning/graphs/`,
  both carried by the plan-metadata commit.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-14*
