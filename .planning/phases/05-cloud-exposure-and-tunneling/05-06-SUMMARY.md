---
phase: 05-cloud-exposure-and-tunneling
plan: "06"
subsystem: network
tags: [hint-channel, language, wire-log, rule-20, d-11, d-14, lang-01, lang-03, cloud-02, gate-4]

# Dependency graph
requires:
  - phase: 04-language-and-scent
    provides: record_hint / the pending_hints+incoming_hints buffers (04-04, 04-12), compose_and_send_hint + decode_turn_hint (04-12, 06-02), build_hint / HintKey (04-04)
  - phase: 06-security-and-cryptography
    provides: turn_commit_send.log_received and its local_turn contract (06-05 Gap 1), commit_state.PendingAction.turn (06-02 D-58)
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-04's board_outcome-threaded _play_to_turn_loop_end, imported unmodified"
provides:
  - "turn_hint_buffer.record_hint: every inbound HINT is written to the wire-mirroring JSONL, keyed on OUR turn, before the drop guard"
  - "_HINT_LOOKBACK_TURNS: the named one-turn receive window that makes the language channel deliverable to a responder at all"
  - "_usable_stamp / _buffer_if_not_older: freshest-hint-wins buffering that cannot raise on peer data"
  - "turn_actions: the responder stamps its hint with pending.turn, and neither branch composes for a turn that already resolved"
  - "tests/integration/test_hint_delivery.py: the two-peer proof that both sides stamp the turn played AND both sides decode"
  - "tests/unit/_hint_fixtures.py: shared hint-test helpers (one copy, QUAL-02)"
affects: [05-08, 07-reporting-and-visualization-shell]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A receive window expressed as a NAMED structural constant with its timing derivation in source, explicitly not a config key or a PARAMETERS.md value"
    - "Peer-supplied fields read through a `_usable_*` helper that returns None instead of raising, on any path whose exception no caller catches"
    - "A re-specified test states in its own docstring WHY it changed and what the old fixture certified"

key-files:
  created:
    - src/pursuit/network/turn_hint_buffer.py
    - tests/unit/test_turn_hint_buffer.py
    - tests/unit/test_hint_freshness.py
    - tests/unit/_hint_fixtures.py
    - tests/integration/test_hint_delivery.py
  modified:
    - src/pursuit/network/turn_buffer.py
    - src/pursuit/network/turn_actions.py
    - tests/unit/test_turn_buffer.py
    - tests/integration/test_gate4.py
    - docs/phases/phase-4/GATE-4-MEASUREMENT.md
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md

key-decisions:
  - "The inbound hint receipt is logged BEFORE the drop guard: a hint we discard still crossed the wire, and rule 20's replay evidence must show it"
  - "record_hint keeps its (ctx, sender, turn, payload) signature and rebuilds the Envelope locally, so all three call sites and their tests stay byte-unmodified -- nothing is lost, since each caller has already established the type is HINT"
  - "_HINT_LOOKBACK_TURNS = 1 is a module constant with its derivation in a comment, in the same class as agent_audit_wiring._DECLARE_RETRIES -- no new numeric leaf in any config file (CLAUDE.md rule 1)"
  - "The freshness guard reads the STORED payload's stamp through _usable_stamp, which treats missing/None/str/bool/float/list/dict all as 'no usable stamp -> replace' -- a TypeError here escapes run_turn_loop and ends the game"
  - "The initiator branch got the same `outcome is None` guard even though it is behaviour-neutral there, so the two branches read as one rule rather than an asymmetry a later change would 'tidy away'"
  - "test_hint_delivery's inbound-record assertion is a gap-free PREFIX at most one short, not an exact count: the last hint a side pushes can still be in flight when the RECEIVER's loop resolves and exits, which is the channel being best-effort by design"
  - "docs/phases/phase-6/gate6_measurement_evidence.json was regenerated to run the gate, then restored with git checkout -- the /gsd:verify-work 6 and 05-04 convention -- so this plan's diff stays code-only and cannot collide with 05-05's own concurrent regeneration"

patterns-established:
  - "Revert probes recorded verbatim INCLUDING the one whose result contradicted the plan's prediction, with the reason the prediction could not hold"
  - "Attribution measured before blame: a flaky test was probed at a pre-change worktree, at HEAD, with and without the suspect guard, before being logged as not-ours"

# Metrics
duration: 75min
completed: 2026-08-14
---

# Phase 5 Plan 06: Hint Flow — Wire Evidence and Two-Way Delivery Summary

**Every inbound HINT is now durable, replayable wire evidence keyed on local truth, and the language channel actually delivers in both directions for the first time — the receive window carries one named turn of lookback, the responder stamps the turn it actually played instead of one in the future, and no hint is composed for a turn that already resolved; measured on a real two-process loopback game where both sides log `message_received`+`hint` records and both sides decode.**

## Performance

- **Duration:** ~75 min
- **Started:** 2026-08-14T12:44Z · **Completed:** 2026-08-14T13:58Z
- **Tasks:** 3 of 3
- **Files created:** 5 · **Files modified:** 6

## Task Commits

| Task | Commit | Note |
|---|---|---|
| 1 — inbound hints reach the wire log | **`7619758`** `fix(05-06): inbound hints reach the wire log` | clean |
| 2 — window and stamp, together | **`ead48df`** | **content correct and complete, but carries 05-05's commit message — see Issues** |
| 3 — re-specify the five tests | **`f32bb3a`** `test(05-06): re-specify the five tests that froze the bugs` | clean |

**Plan metadata:** the `docs(05-06): …` commit that carries this file.

## Accomplishments

- **G3 closed.** `record_hint` moved to a new `turn_hint_buffer.py` sibling and now calls
  `turn_commit_send.log_received` **before** the drop guard. The record's own top-level turn
  is `ctx.state.turn`; the nested envelope keeps the peer's declared turn verbatim — the exact
  06-05 Gap-1 split, so a hint record can never become an attacker-controllable audit join key.
  Proven inert to the audit by a paired before/after over the same log.
- **G4 closed, both halves in one commit.** `_HINT_LOOKBACK_TURNS = 1` is a named structural
  constant carrying its derivation in source; the responder stamps `pending.turn`. Reverting
  either half alone is recorded below.
- **G1's stagger half closed.** Neither branch composes a hint for a turn that already resolved
  — 17.4 s of the 2026-08-13 round's 18 s inter-side divergence, gone.
- **The freshness guard cannot kill a game.** The stored stamp is peer data on a path that
  validates nothing beyond `isinstance(payload, dict)`; seven hostile shapes (string, None,
  bool, float, list, dict, absent) are each buffered without raising.
- **Five tests that certified the bugs now certify the fix**, each stating in its own docstring
  what the old fixture froze and why.

## Files Created/Modified

### Created
- `src/pursuit/network/turn_hint_buffer.py` (**118**/150) — `record_hint`, the window constant,
  `_usable_stamp`, `_buffer_if_not_older`. Coverage **100%**.
- `tests/unit/test_turn_hint_buffer.py` (90/150) — the wire-evidence half (5 tests).
- `tests/unit/test_hint_freshness.py` (134/150) — the window/freshness half (6 tests).
- `tests/unit/_hint_fixtures.py` (39/150) — shared helpers, one copy.
- `tests/integration/test_hint_delivery.py` (117/150) — the two-peer proof (3 tests).

### Modified
- `src/pursuit/network/turn_buffer.py` — **146 → 136**/150; `record_hint` re-exported with an
  explicit `__all__`. Coverage **100%**.
- `src/pursuit/network/turn_actions.py` — **143 → 143**/150 (the `(c)`/`(d)` edits are in-place
  condition/argument changes; every explanation is a `#` comment, which the gate does not count).
  Coverage **99%**.
- `tests/unit/test_turn_buffer.py` — 122 → **103**/150.
- `tests/integration/test_gate4.py` — 125 → **149**/150.
- `docs/phases/phase-4/GATE-4-MEASUREMENT.md` — criterion-3 amendment + one superseded row.
- `deferred-items.md` — item #4.

## Verification (measured, not claimed)

| # | Gate | Result |
|---|---|---|
| 1 | `uv run ruff check .` | **All checks passed!** — 0 violations |
| 2 | `uv run pytest tests/ --cov` | **1293 passed, 96.35%** (baseline 1262 / 96.30%) |
| 3 | `bash scripts/check_line_limit.sh` | **exit 0** |
| 4 | `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| 5 | `uv run python scripts/measure_gate6.py` | **exit 0 — all three book §10.4 criteria PASS** |
| 6 | `tests/integration/test_step0_and_audit.py` unmodified | **confirmed** — untouched in all three 05-06 commits; last touched by 05-04's `8f35721`; clean in the worktree |
| 7 | real loopback game | **PASS** — table below |

**On the test count.** 05-05 executed in parallel and committed four times during this plan, so
1293 is the joint total. 05-06 contributes **+11** (5 wire-evidence, 5 window/freshness/hostile-stamp
+ delivery, 1 lookback-boundary sibling); 05-05 contributes the remaining +20. No test was lost:
the five re-specified tests are all still collected, and the four `record_hint` cases that moved
files are all present in `test_hint_freshness.py`.

### GATE-6 re-run

```
GATE-6 measurement -- localhost, zero env vars
  criterion_1_four_phases_commit_reveal: PASS
  criterion_2_hash_nonce_mismatch_technical_loss: PASS
  criterion_3_step0_verified_before_move_1: PASS
```

Run twice (after Task 1, and again at the end), `exit 0` both times. The regenerated evidence
JSON differed from the committed one in the two mtime lines, `generated_at`, **and one
substantive pair**: `police_received` and `thief_received` each gained `"hint": 5` where both
previously read `{commit: 5, reveal: 5}`. That pair **is** G3 at the integration level — Task 1's
records appearing in the gate's own envelope-type census. Every verdict field was byte-identical,
so the file was restored with `git checkout --` per the `/gsd:verify-work 6` and 05-04 convention
(and to avoid colliding with 05-05's concurrent regeneration of the same file); the measured
numbers are recorded here instead.

## Item 7 — a real loopback game, measured

`uv run python scripts/dev_launch.py` (two real processes, real sockets, no `ANTHROPIC_API_KEY`),
17.4 s wall, **exit 0**, both sides ending `game_over=capture` → `audit_verdict matched=true`:

| Side | Hints SENT (turn stamps) | Inbound `message_received`+`hint` | `incoming_hint.outcome` per turn |
|---|---|---|---|
| police (initiator) | **5** — `0,1,2,3,4` | **4** | `no_hint, no_hint, no_evidence, no_evidence, no_hint` |
| thief (responder) | **4** — `0,1,2,3` | **5** | `no_hint, no_evidence, no_evidence, no_evidence` |

Against the **2026-08-13 remote round** (the "before"): police stamped `0,1,2,3,4` and thief
stamped `1,2,3,4,5`; **neither log contained a single** `message_received`+`hint` record; the
thief's five `incoming_hint.outcome` values were all `no_hint` with `token_spend.calls = 0`.

Both sides now have inbound hint records, and **both** sides have at least one non-`no_hint`
outcome — the assertion the round would have failed. (`no_evidence` rather than `evidence` is
the keyless template decode path, not a delivery failure: the text arrived and was decoded.)

**Did the measurement match the derived GATE-4 expectation? Yes, exactly.** Derived first:
initiator `len(turns) == ctx.state.turn`, responder `== ctx.state.turn - 1`. Measured: police
5 hints over 5 turns, thief 4 over 5. The mocked `test_gate4.py` run reports the identical
shape (police 5/5, thief 4/5). No number was read off a run and frozen.

## Revert-probe results (recorded verbatim)

### Probe A — revert (c) only, the responder's outgoing stamp

```
E   AssertionError: responder hint turns [1, 2, 3, 4] must equal its reveal turns [0, 1, 2, 3, 4] minus the resolved terminal turn
E   assert [1, 2, 3, 4] == [0, 1, 2, 3]
FAILED tests/integration/test_hint_delivery.py::test_both_sides_stamp_the_turn_they_actually_played
1 failed, 2 passed in 2.97s
```

**Assertion 1 fails, reproducing the remote round's `1..5`-vs-`0..4` asymmetry exactly.
Assertion 2 does NOT fail, and the plan's prediction that it would cannot hold.** Reverting (c)
restores the mis-stamp, and the mis-stamp *helps* delivery: a hint stamped one turn in the
future is read by the peer as a future hint and kept. That is 05-UAT.md G4's own finding — "the
police decoded thief hints only because of a SECOND bug" — so it is logically impossible for
reintroducing that bug to stop the channel delivering. The suite is still non-vacuous for (c):
assertion 1 catches it in its most literal form. Recorded rather than smoothed over.

### Probe B — revert (a) only, the lookback window

```
E   AssertionError: thief/responder: every turn read no_hint ['no_hint', 'no_hint', 'no_hint', 'no_hint'] -- the channel delivered nothing
FAILED tests/integration/test_hint_delivery.py::test_both_sides_actually_receive_a_decodable_hint
1 failed, 2 passed in 3.26s
```

**Assertion 2 fails, as predicted** — the responder's five-`no_hint`-in-a-row shape reproduced on
loopback. The police half still passes, which is the asymmetry the two bugs produced together.

Both halves were restored and the file re-verified after each probe; `git diff` on
`turn_actions.py` was inspected to confirm the tree returned exactly to the committed state.

## Deviations from Plan

**1. [Rule 3 - Blocking] `tests/unit/test_turn_hint_buffer.py` crossed the 150-line gate**
- **Found during:** Task 2, adding the freshness and hostile-stamp cases (155/150).
- **Fix:** split — never compress. The window/freshness half moved to
  `tests/unit/test_hint_freshness.py`, and the helpers both files need moved to
  `tests/unit/_hint_fixtures.py` (one copy, QUAL-02, the `_fakes_agent.py` precedent).
- **Committed in:** `ead48df`

**2. [Rule 3 - Blocking] `tests/unit/test_turn_buffer.py` crossed the gate under Task 3**
- **Found during:** Task 3 (168/150 after the re-specification).
- **Fix:** `record_hint`'s four cases moved to `test_hint_freshness.py`, which already owns
  "which inbound hint wins and which is too late". They keep calling `turn_buffer.record_hint`
  — the re-exported name every production call site uses — so the re-export stays exercised.
  Nothing was deleted; `git diff` confirms every removed assertion reappears, strengthened.
- **Committed in:** `f32bb3a`

**3. [Rule 1 - Bug in my own test] `test_hint_delivery`'s inbound-record assertion was wrong as first written**
- **Found during:** Task 2, first run — `assert 4 == 5`.
- **Issue:** it asserted the receiver logs exactly as many hints as the peer sent. The last hint
  a side pushes can still be in flight when the RECEIVER's turn loop resolves and exits, so it is
  never drained. Asserting an exact count would have pinned a race.
- **Fix:** a gap-free PREFIX, at most one short, with the reason (best-effort channel, 04-04) in
  the docstring. Measured, not assumed: police received 4 of the thief's 4, thief received 4 of
  the police's 5.
- **Committed in:** `ead48df`

**Total deviations:** 3 auto-fixed (2× Rule 3 line-gate splits, 1× Rule 1 in a test this plan
wrote). **No production behaviour beyond the plan's text was changed.** No assertion was removed,
none widened to a subset or `in` check.

## Issues Encountered

### Task 2's commit carries 05-05's message — a shared-index collision, not a lost change

05-05 executed in the **same worktree** on the **same git index**. Between my `git add` of Task
2's six files and my `git commit`, 05-05's own executor ran a path-less `git commit`, which swept
my staged files into `ead48df` (`feat(05-05): a game id the construction-time wiring can
follow`). Verified file-by-file: all six of Task 2's files —
`turn_hint_buffer.py`, `turn_actions.py`, `test_hint_delivery.py`, `test_turn_hint_buffer.py`,
`test_hint_freshness.py`, `_hint_fixtures.py` — are present and correct in that commit.

**Deliberately not rewritten.** A `reset --soft` + re-split would invalidate `ead48df`, a hash
05-05 has already recorded in its own SUMMARY, and would race a still-running executor. The
content is right, the history is intact, and the plan's binding constraint — *the window
relaxation and the responder stamp fix land TOGETHER, in ONE commit* — is satisfied: both halves
are in `ead48df` and the tree was never left between them.

Task 3 was committed with `git commit -- <paths>` and **no** `git add`, so it never entered the
shared index and landed clean. **Carry-forward for any future parallel wave in one worktree:
always use the path-limited form.** Two other collisions cost time and are worth naming: the
pre-commit hook runs `ruff check` over the WHOLE repo, so a parallel executor's half-written file
blocks an unrelated commit (hit twice, waited both times, never `--no-verify`); and a shared
harness import can be transiently broken mid-edit (`NameError: negotiated_game_id`) and invalidate
a probe run.

### `test_late_peer_teardown.py`'s non-vacuity test flakes under load — measured as NOT ours

Two failures observed during verification, both inside the window where 05-05's executor was also
running pytest on the same box. Attribution measured before blame:

| Tree | Scope | Runs | Result |
|---|---|---|---|
| `f5372e2` (pre-05-06, separate worktree) | file alone / whole `tests/integration` | 6 / 4 | clean / clean |
| HEAD | file alone | 1 | clean |
| HEAD | `tests/integration` minus `test_hint_delivery.py` | 3 | clean |
| HEAD | whole `tests/integration` | 4 | clean |
| HEAD | full `tests/` | 1 | 1293 passed |

A targeted probe that disabled 05-06's `outcome is None` compose guard and re-ran the
audit-heavy integration files 4× was clean **with and without** the guard, so the production
change is not the trigger. The real cause is that the test pins a 0.3 s race on real sockets.
Logged in full, with the suggested deterministic-sequencing fix, at `deferred-items.md` #4.
**Not fixed here:** `late_peer_harness.py` is 05-04's file, outside this plan's `files_modified`,
and its `linger=True` path must keep the peer arriving DURING the grace window — the two paths
need designing together.

### GATE-4's criterion 3 needs a responder-side re-measurement

Recorded honestly in `GATE-4-MEASUREMENT.md` rather than assumed to carry over. The criterion-3
table is police-side only, and the police is the initiator, whose behaviour is unchanged — so
its PASS stands on its own measured evidence. But the "2 × 68 = 136" consistency check assumed
the two roles compose identically and no longer holds (the symmetric expectation is now
68 + (68 − games) = 133), and **no responder-side count was ever measured with a real key**.
`scripts/measure_gate4.py` must be re-run with a real `ANTHROPIC_API_KEY` before submission
(D-32 already requires this) and criterion 3's table given a thief-side row.

### Line-count headroom

`tests/integration/test_gate4.py` is now **149/150** and `tests/unit/test_hint_freshness.py`
**134/150**. The next change to `test_gate4.py` must split before it adds anything.

## Knowledge graph

Refreshed after the code landed: **7016 nodes / 12737 edges / 438 communities** (was
6827/12372/429 after 05-04). `graph.html` skipped over graphify's 5000-node viz limit, matching
the 04-12/05-03/05-04/06-04 precedent (gitignored regardless).
`graphify explain "record_hint"` resolves it to
`src/pursuit/network/turn_hint_buffer.py L100` with 6 edges — both `await_move` and
`drain_trailing_hint` still reaching it, confirming the re-export did not orphan a caller.

## User Setup Required

None — every measurement in this summary ran offline with zero environment variables set.

## Next Phase Readiness

- **G3 and G4 are closed on the code side, and G1's stagger half with them.** Criterion 2's
  "verdicts agree" clause now has all three of the pieces it was missing across 05-04 and 05-06:
  honest attribution, a grace window, and a responder that no longer runs 17 s past the end.
- **05-08** (the human remote round, attempt 2) is the only thing that can close GATE-5
  criterion 2, and 05-05 + 05-06 were its two named blockers. Its checklist item "both sides'
  logs carry `message_received` + `hint` records; both sides have at least one non-`no_hint`
  incoming hint" is now satisfied on loopback and is expected to hold over ngrok — nothing in
  either fix depends on transport.
- **G5** (the silent keyless-LLM fallback) is untouched by this plan and still open.
- **Nothing is ticked in ROADMAP.md**, per this project's standing convention;
  `docs/phases/phase-5/TODO.md` row 05-06 is marked ◐ with the commit hashes, to be ☑'d at
  `/gsd:verify-work 5`.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-14*

## Self-Check: PASSED

All 12 claimed files verified present on disk; all 3 task commit hashes verified in `git log`.
Two claims re-measured during the check rather than carried over:

- **"the five re-specified tests are all still collected"** — confirmed by name, not by count:
  `test_record_hint_buffers_by_sender`, `test_record_hint_overwrites_a_second_hint_from_the_same_sender`,
  `test_record_hint_silently_drops_a_hint_for_an_already_resolved_turn` (now in
  `test_hint_freshness.py`), plus `test_await_move_buffers_a_leading_hint_then_returns_the_move`
  and `test_drain_trailing_hint_records_a_hint_present_on_the_queue` (still in
  `test_turn_buffer.py`, each with an added `incoming_hints` assertion).
- **`git diff` on the two Task-3 test files shows five removed assertion lines**, and each was
  verified to reappear: four inside the moved `record_hint` cases in `test_hint_freshness.py`
  (each now joined by an `incoming_hints` assertion), and `test_gate4.py`'s
  `len(turns) == ctx.state.turn` replaced by the stronger derived per-role expectation. **None
  deleted, none widened to a subset or `in` check.**

`docs/phases/phase-5/TODO.md` row 05-06 updated from ☐ to ◐ with the commit hashes and the
measured result, per CLAUDE.md's per-phase-triplet rule; it is ☑'d at `/gsd:verify-work 5`.
