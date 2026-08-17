---
phase: 08-submission-and-league-operations
plan: 05
subsystem: network
tags: [commit-reveal, turn-loop, envelope-boundary, evidence-integrity, deferred-items]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "deferred items #13, #19 and #20 — the measurements, the named repair shapes, and the named split seam"
  - phase: 07-reporting-shell
    provides: "07-18's source-enumerated pull-site boundary guard, which found #19 and judged this plan's work"
provides:
  - "#13 closed: the toggle-off MOVE envelope carries the turn actually played"
  - "#19 closed: `await_move` returns only a MOVE, buffers a FINAL_REVEAL, and skips everything else"
  - "`src/pursuit/network/turn_buffer_queue.py` — the queue readers, split along the seam #20 named"
  - "`tests/unit/test_shipped_path_turn_source.py` — an AST guard on the D-59 hash input and the D-64 join key"
affects: [08-10, 08-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Prove byte-identity of a shipped path with a nonce-pinned deterministic fingerprint, not with an argument"
    - "Contain a new parameter inside the branch that needs it, so the untouched path is identical BY CONSTRUCTION"
    - "Account a boundary matrix BY NAME (buffered / awaited / foreign), never by a total that a fixture row can pad"

key-files:
  created:
    - src/pursuit/network/turn_buffer_queue.py
    - tests/unit/test_toggle_off_move_turn_stamp.py
    - tests/unit/test_shipped_path_turn_source.py
  modified:
    - src/pursuit/network/turn_commit.py
    - src/pursuit/network/turn_commit_send.py
    - src/pursuit/network/turn_actions.py
    - src/pursuit/network/turn_buffer.py
    - src/pursuit/network/__init__.py
    - tests/unit/test_toggle_off_move_boundary.py
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
    - docs/SUBMISSION-CHECKLIST.md

key-decisions:
  - "CLOSE both, do not accept: #19's blast radius is provably zero on the shipped path (`await_move` has ONE production caller, the toggle-off branch), and #13's repair is containable to that same branch"
  - "`played_turn` is required and KEYWORD-ONLY — a default would let the next caller reintroduce #13 by omission, which is how it survived 05-14"
  - "The commit-reveal-ON path keeps `turn = ctx.state.turn` textually unmoved; `played_turn` is referenced only inside the toggle-off branch, so byte-identity holds by construction and is pinned by AST"
  - "A FINAL_REVEAL is buffered before it is skipped — skipping without buffering would have converted #19 into 05-17's defect on the same path"
  - "The two-consecutive-hints counter is NOT reset by a skipped foreign type: the rule says 'two hints with no MOVE', and resetting would hand a peer an unbounded hint channel"
  - "turn_buffer.py was split along the seam deferred #20 named, rather than compressed into its two remaining lines of headroom"

patterns-established:
  - "Long rationale goes in `#` comments, not docstrings: the 150-line gate counts docstring lines as code"
  - "A bookmark test that is supposed to fail on closure must be re-measured, not trusted"

# Metrics
duration: 120min
completed: 2026-08-17
---

# Phase 8 Plan 05: Deferred Items #13 and #19 Summary

**Both latent `commit_reveal=False` evidence defects CLOSED — the second mover's MOVE
envelope now carries the turn it actually played, and the toggle-off wait stops reading a
HANDSHAKE or a GAME_OVER as a move — with the shipped commit-reveal-ON path proven
byte-identical by a nonce-pinned fingerprint and the D-59 hash input pinned by AST.**

> **No `08-05-PLAN.md` exists.** Executed from `08-PLAN-OUTLINE.md` §9's `08-05` entry and the
> phase-5 `deferred-items.md` records for #13, #19 and #20. Every measurement was **re-derived
> at HEAD**.

## The decision: CLOSED, not accepted

The brief allowed either. Closure was chosen because the risk both items were deferred for
turned out to be **containable and measurable**, not because closure is tidier.

| | #13 | #19 |
|---|---|---|
| **Why it was deferred** | the repair changes `initiate`'s signature, and on the ON path the same `turn` feeds the D-59 hash input and the D-64 join key — rules 19/22 territory | `turn_buffer.py` sat at the 150-line gate with no room for the repair |
| **What made it safe** | the new parameter is **consumed only inside the toggle-off branch**, so the ON path is identical *by construction*, then verified empirically | `await_move` has **exactly one production caller** — `turn_commit.await_and_respond`'s `if not ctx.security.commit_reveal` branch. A commit-reveal-ON game never reaches it |
| **Shipped config, re-measured at HEAD** | `config/police/security.json` → `true` · `config/thief/security.json` → `true` | same |

## Byte-identity of the shipped path — measured, not argued

A deterministic ON-path drive with the nonce pinned (the exchange's only source of
non-determinism), run **before and after** the change:

```
fingerprint  c79f76aff7718084b2273777e6c7735e311a9c22e006f00beaa785e8dc82c08d
pushes       3, turns [0, 0, 0]
h_commit     6a34ee5cf5ebb8084eae5fd541c0d1a8eeed4d889afded9e67956ebf650ce087
ledger turns [0]
```

**Identical on both sides.** `turn = ctx.state.turn` in `initiate` is textually unmoved and
still what `commit_own_action(turn=…)` receives, so the **D-59 hash input and the D-64 ledger
join key were never in the change's path.**

The first two attempts at this fingerprint were **not** deterministic — the digest differed
run to run while `h_commit` stayed constant. The causes were the per-run `game_uid` and then
the log `timestamp`; both are redacted, and that is recorded rather than smoothed over,
because a fingerprint that varies for reasons you have not identified proves nothing.

`tests/unit/test_shipped_path_turn_source.py` makes the property permanent by AST: `played_turn`
must stay required and keyword-only, both committing entry points must still bind `turn` from
`ctx.state`, `commit_own_action` must still be fed the plain name `turn`, and `played_turn`
must be referenced **only** inside the toggle-off branch.

## #13 — the toggle-off MOVE turn stamp

Reproduced **RED first**: *"the MOVE envelope claims turn 1 for the action played on turn 0"*,
exactly 05-14's recorded measurement. `send_move_only` now takes `played_turn` for both the
envelope and the log record; `take_my_turn` supplies `pre_turn_state.turn` — the same
pre-resolve snapshot the hint stamp already uses, by the same rule. `GameState` is
`@dataclass(frozen=True)` and `maybe_resolve` **rebinds** `ctx.state`, so the snapshot holds.

The reproduction carries its own anti-vacuity case: without proof that `maybe_resolve` really
advanced the turn in that window, the buggy read and the correct one coincide and the
assertion is void.

## #19 — the toggle-off move wait had no type test

`await_move` now returns **only** a MOVE, buffers a FINAL_REVEAL on the way past, and keeps
waiting through anything else — the shape the other four `wait_for_*` legs have had since
05-18. The buffering is load-bearing: this leg pulls through `wait_for_opponent` directly and
does not inherit 05-17's buffering, so skipping *without* buffering would have converted #19
into 05-17's defect on the same path. Probed — removing it fails the class guard with *"the
peer's published ledger was destroyed"*.

Split along the seam **deferred #20 named itself**: `await_move`, `drain_trailing_hint` and
`HintProtocolError` moved to `src/pursuit/network/turn_buffer_queue.py`. `turn_buffer.py`
142 → **114**; the new file **93**. Re-exported, so every caller and every monkeypatch
resolves where it did.

### The finding: 05-18's bookmark did not fire

`test_toggle_off_move_boundary.py` asserted `counts["off"] > 0` **precisely so that whoever
closed #19 would be failed and sent to the deferred record.** It stayed green after the fix.

The nine `MessageType` members include **MOVE** — the type this leg *awaits* — and the fixture
builds it with a payload that is not a legal move, so the decoder rightly complains. That row
was never part of #19. It inflated 05-18's count from 7 to 8 and would have kept "still
reproduces" true forever.

Re-measured at HEAD, now accounted **by name** instead of by total:

```
commit_reveal ON   0 of 9 unnamed reasons
commit_reveal OFF  1 of 9  -- and the one is MOVE itself
```

Nine = 1 buffered (HINT) + 1 awaited (MOVE) + **7 foreign**. All seven closed on **both**
toggle settings. The rewritten test derives the foreign set from `MessageType`, asserts the
partition covers every member, and pins the malformed-MOVE row **positively** so it can never
pad the count again.

**07-18's guard judged this work and passed it on its own terms**: it followed the split
unaided, now reporting the site as `await_move(turn_buffer_queue.py)`.

## Task Commits

1. **#13 — stamp the toggle-off MOVE with the turn actually played** — `112e593` (fix)
2. **#19 — type test on `await_move`, plus the #20 split** — `12c3a0c` (fix)
3. **Records closed, #20 row relieved, graph refreshed** — `89ccdf0` (docs)

## Gate run, against the orchestrator's baseline

| Gate | Baseline | After 08-03 | After 08-05 |
|---|---|---|---|
| `uv run pytest --cov` | 2293 / 0 | 2331 / 0 | **2342 passed / 0 failed** |
| Coverage | 97.43% | 97.44% | **97.44%** |
| `ruff check .` | 0 | 0 | **0** |
| `check_line_limit.sh` | 0 | 0 | **0 violations**, exit 0 |
| `check_local_truth.py` | OK 7 | OK 7 | **OK, 7 modules** |
| `check_no_llm_in_strategy.py` | OK | OK | **OK** |
| `check_submission.py` | 41/32/13 | 49/24/13 | **49 PASS / 24 GAP / 13 UNJUDGED** — unchanged, as expected: neither deferred item was ever a gate row |

`git diff config/` is **empty**. `turn_commit.py` 149 · `turn_commit_send.py` 127 ·
`turn_actions.py` 147 · `turn_buffer.py` 114 · `turn_buffer_queue.py` 93 — all under 150.

### Rule-38 counters — all four numbers

| Run | police | thief | Delta |
|---|---|---|---|
| Full `uv run pytest --cov` | 1924 → 1924 | 1917 → 1917 | **0 / 0** |
| One real `scripts/dev_launch.py` game | 1924 → 1925 | 1917 → 1918 | **+1 / +1** |

The real game: `game_id` `b995f351b3796e23`, exit 0, **both seats** `audit_verdict
{"matched": true, "turn": 5}` and outcome `capture`, **zero** `technical_win`, **zero**
`watchdog_incident`, `commit_hash 12c3a0c0b5…` (this plan's #19 commit). Nothing sets the
games-played VALUE.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] A ninth `send_move_only` call site outside the grep**
- **Found during:** Task 1, on the full-suite run — `tests/unit/test_turn_push_watchdog.py`
  calls `send_move_only` directly, so the `turn_commit.initiate` grep never showed it.
- **Fix:** passed `ctx.state.turn` at that call site. No assertion weakened.
- **Committed in:** `112e593`

**2. [Rule 3 — Blocking] The line gate counts docstring lines as code**
- **Found during:** Task 1. #13's rationale in `initiate`'s docstring took `turn_commit.py`
  149 → **163** — a VIOLATION.
- **Fix:** relocated the prose to `#` comments, which is what the rest of that file already
  does. **No code was compressed**; 149 at HEAD. The same treatment was applied to
  `send_move_only` (146 → 127) so the next plan is not left at the gate.
- **Committed in:** `112e593`

**3. [Rule 2 — Missing Critical] The new module had to enter `network/__all__`**
- **Found during:** Task 2. 08-03's own packaging guard failed with `missing
  ['turn_buffer_queue']` the moment the file was staged.
- **Fix:** added it to the inventory. Recorded as the guard working, not as friction.
- **Committed in:** `12c3a0c`

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 missing-critical). No scope creep — nothing
outside #13, #19 and #20's named seam was touched.

## Issues Encountered

- **A commit message was corrupted by the shell.** Backticks inside a double-quoted `-m`
  string were command-substituted and three phrases were swallowed. Caught by reading the
  message back, and amended with `-F` from a file. Worth carrying: read a commit message back
  when it contains code.
- **The whole-blob fingerprint was non-deterministic twice** before the redaction set was
  right (`game_uid`, then `timestamp`). Recorded above rather than quietly fixed.
- **Out of scope, recorded not fixed:** on the toggle-off path a genuinely **malformed MOVE**
  is still rejected with the decoder's own message rather than a `TechnicalWinReason` member.
  That is the peer really having sent a malformed MOVE, not a type confusion, so it is outside
  #19; it is now pinned by a positive assertion so it cannot be mistaken for either a
  regression or an unfixed defect.

## Next Phase Readiness

- Phase-5 deferred items #13, #19 and #20-row-3 are closed; #20 rows 1 and 2 stay open and are
  re-measured (`turn_commit.py` at 149/150 is the one to watch).
- **08-10** will carry `src/pursuit/network/turn_buffer_queue.py` into both split repos; it is
  tracked, not gitignored, and in `network/__init__.py`'s `__all__`.
- Any future plan adding a `network/` module must add it to that `__all__` — 08-03's guard,
  which already caught this plan once.

**NOTHING WAS PUSHED. NO TAG WAS CREATED. NO REMOTE WAS TOUCHED.**

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*

## Self-Check: PASSED

- 3 created paths verified **present AND tracked by git AND not gitignored**.
- 3 task commits verified reachable: `112e593` `12c3a0c` `89ccdf0`.
- `git tag -l` **empty**; 143 commits sit ahead of `origin/main`, unpushed.
- Every number above was read from a command run in this session.
