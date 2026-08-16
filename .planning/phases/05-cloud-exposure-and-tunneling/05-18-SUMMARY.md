---
phase: 05-cloud-exposure-and-tunneling
plan: "18"
subsystem: network/envelope-boundary
tags: [gap-closure, false-accusation, rules-16-22, rule-36, NET-06, NET-07, CLOUD-02, SEC-05, class-fix, routing-not-timing]
one_liner: "The initiator's own wait stops reading an honest peer's published ledger as an illegal move -- both roles now share one tail leg instead of one having the type discipline and its sibling not -- and the whole defect class is pinned by a test that enumerates all 12 queue-pull sites from source, which found instance six on its first run."
requires:
  - "05-17: the FINAL_REVEAL routing that makes the repair safe -- the ledger is already in ctx.commit_state.early_final_reveal, so skipping it in the turn loop costs the audit nothing"
  - "05-16 (deferred #10): the per-bounded-attempt watchdog touch, which turn_commit.py:103 was the last production caller still missing"
  - "05-15 (G10): the same envelope-TYPE check one layer further in, at receive_final_reveal"
  - "05-13 (G6): the on_attempt hook and the ArmedWatchdog/injected-clock harness, reused verbatim"
provides:
  - "network/turn_commit_wait_reveal.py: the tail wait BOTH roles run; h_commit: str | None, where None is the initiator"
  - "tests/unit/_pull_site_discovery.py: the 12 pull sites read out of src/pursuit/network/ by a two-stage AST walk, raising rather than returning empty"
  - "tests/unit/_pull_site_drivers.py: one driver per site plus the probe harness"
  - "tests/unit/test_envelope_boundary_invariant.py: the standing class guard -- no traceback, named reasons only, the ledger survives"
  - "deferred #18 CLOSED; #19 (instance six) and #20 (three modules at the gate) opened with measurements"
affects:
  - "src/pursuit/network/turn_commit.py (147 -> 149; the police branch and its docstring)"
  - "src/pursuit/network/turn_commit_wait.py (135 -> 151 -> 122 after the split)"
  - "tests/unit/_turn_loop_fixtures.py, _early_reveal_fixtures.py, test_early_final_reveal.py, test_early_reveal_routing.py"
tech-stack:
  added: []
  patterns:
    - "Enumerate the sites FROM SOURCE (AST), never from a hand-written list -- a list is a snapshot, and going stale is the mechanism by which this class regenerated five times"
    - "Bound a transitive AST closure by the RETURN ANNOTATION, so it stops exactly where the Envelope stops flowing outward"
    - "Join a source-derived site set against a hand-written driver set and fail on EITHER mismatch -- undriven sites and stale drivers are both blind spots"
    - "Remove the second code path rather than teaching it the same lesson: both roles share one leg"
    - "Assert a positive COUNT, not the absence of a complaint -- `not breaches` is satisfied by a matrix that never ran"
key-files:
  created:
    - src/pursuit/network/turn_commit_wait_reveal.py
    - tests/unit/test_early_final_reveal_police.py
    - tests/unit/_pull_site_discovery.py
    - tests/unit/_pull_site_drivers.py
    - tests/unit/test_envelope_boundary_invariant.py
    - tests/unit/test_toggle_off_move_boundary.py
    - tests/unit/test_turn_commit_wait_reveal.py
  modified:
    - src/pursuit/network/turn_commit.py
    - src/pursuit/network/turn_commit_wait.py
    - tests/unit/_early_reveal_fixtures.py
    - tests/unit/_turn_loop_fixtures.py
    - tests/unit/test_early_final_reveal.py
    - tests/unit/test_early_reveal_routing.py
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
decisions:
  - "KEEP WAITING, not end the game on the peer's FINAL_REVEAL. Both candidates were RUN against the real turn loop and run_final_audit. Ending the game has no truthful expression inside await_and_respond's contract: (None, None) makes await_opponent_turn raise AttributeError, and the only other door is hand-building a TechnicalWin, whose own docstring says every field is MEASURED by the ladder and never assumed -- and which, measured, accuses a peer that demonstrably just spoke."
  - "Both roles share ONE leg rather than the police branch getting its own copy of the type test. Every instance of this class has been a boundary where one path had the discipline and its sibling did not; the repair removes the second path."
  - "h_commit=None is a meaningful value, not a sentinel: the initiator holds no outstanding commit because `initiate` already collected this turn's ACK. The `is not None` guard stops a payload with no h_commit key from matching None by accident."
  - "turn_commit_wait_reveal.py is NOT re-exported from turn_commit_wait, breaking that module's otherwise-universal habit: it imports H_COMMIT_KEY from there, so a re-export back would be an import cycle. Three importers name it directly."
  - "Instance six (deferred #19, turn_buffer.await_move on the toggle-off path) was RECORDED, not fixed: shipped config is commit_reveal true, turn_buffer.py is not in files_modified and sits at 146/150, and phase 5 ends here. Its test asserts the SCOPE and fails deliberately when #19 is closed, so the record cannot rot."
  - "Deferred #16 and #17 left OPEN with their measurements, per the plan's non-goals. #17 is carried into the invariant as a NAMED exemption, asserted to be a real discovered site and probed to confirm the check it exempts is live."
metrics:
  duration: "~4h"
  tasks: 3
  commits: 4
  completed: 2026-08-17
---

# Phase 05 Plan 18: Close the Fifth Instance, Pin the Class — Summary

**An honest peer's published ledger no longer becomes our own 0-point technical loss with a
decoder's error string attached, and the defect class that produced that five times over now
has a standing guard instead of a fifth point fix.** Three tasks, four atomic commits, nine
new cases, six revert probes. The guard justified itself immediately: it found **instance
six** on its first run.

## The reproduced declaration

Measured at HEAD (`da45b55`), police role, queue `[FINAL_REVEAL, REVEAL]`, verbatim:

```
await_and_respond (police) returned type = final_reveal   verdict = None
await_opponent_turn outcome              = Outcome.TECHNICAL_LOSS
technical_win reasons                    = ['payload must be a dict, got NoneType']
queue left = 1        <- the REVEAL we were actually waiting for was never read
buffered  = Envelope(type=FINAL_REVEAL, ...)   <- 05-17's routing, working
```

`turn_commit.await_and_respond`'s police branch called the pull primitive **bare** — `return
await next_protocol_message(ctx)` — with no type test at all, and handed whatever arrived to
`turn_actions.await_opponent_turn` as if it were the opponent's REVEAL. The peer's ledger
payload is `{"records": [...]}`, `decode_revealed_action` looks for a `move` sub-key,
`payload.get("move")` is None, and `turn_buffer.reject_peer_payload` turns that into a
technical loss naming the peer. A **false declaration under rules 16/22**, reachable in a
league game against any second implementation that publishes its ledger the moment it
resolves.

The audit was never the problem: 05-17's buffer already had the ledger safe, so
`audit_verdict matched=true` held even while the turn loop mis-declared. This was about the
**game outcome** — we lost a game we did not lose.

## The design decision, and why

The plan required both candidates to be **measured**, not argued. They were, against this
same turn loop and `run_final_audit`:

| scenario | keep waiting | end the game on the peer's FINAL_REVEAL |
|---|---|---|
| ledger arrives, REVEAL still follows | `outcome=None`, **no accusation** | `AttributeError: 'NoneType' object has no attribute 'sender'` (returning no envelope), or a **fabricated** `technical_win{opponent_unresponsive}` against a peer that demonstrably just spoke |
| ledger arrives, REVEAL never comes | `technical_loss` + `opponent_unresponsive` | same outcome, on fabricated evidence |
| genuinely silent peer (rule 36) | unchanged | unchanged |

**Keep waiting wins, and the reason is that ending the game has no truthful expression
here.** `await_and_respond` returns `tuple[Envelope | None, TechnicalWin | None]`. Returning
`(None, None)` crashes the caller. The only other door is building a `TechnicalWin` by hand
— and that dataclass's own docstring says every field is *"measured by call_with_retry's own
retry ladder — never assumed or defaulted — so the declaration this carries is defensible at
audit (rules 16/22)"*. A verdict with `attempts=0, elapsed_seconds=0.0` is exactly the
fabrication that sentence exists to forbid.

Waiting costs nothing that is not already owed. The ledger is already safe in the buffer, so
the audit matches either way; the REVEAL is normally the very next item on the queue; and a
peer that really has stopped exhausts the ladder and earns D-13's own **measured**
`opponent_unresponsive`. NET-06's in-game sanction is not softened — only renamed from a
claim about a malformed MOVE the peer never sent to a claim we can defend.

**Zero numeric values moved.** Routing and outcome attribution only. 05-17 had already
measured the tempting timing fix directly: widening the receive ladder to 21 attempts, 10x
the shipped value, produced a byte-identical accusation.

### The shape of the repair

Both roles now end in **one leg**, `wait_for_reveal_capturing_early_ack`, with
`h_commit: str | None` where `None` means "this side holds no outstanding commit" — true of
the initiator, because `initiate` already collected this turn's ACK inside
`wait_for_ack_and_commit`. Serving both roles from one function is the deliberate part:
every instance of this class has been a boundary where one path had the type discipline and
its sibling did not, so the repair **removes the second path** rather than teaching it the
same lesson a fifth time.

## The enumeration: 12 sites, read from source

`tests/unit/_pull_site_discovery.py` walks `src/pursuit/network/` with a two-stage AST rule:

- **seed** — a top-level function whose body, *including nested closures* (where `_pull`
  lives in two of them), reads the inbound queue;
- **closure** — iterated to a fixpoint over any function that calls a set member whose own
  **return annotation mentions `Envelope`**.

The annotation is what bounds the closure, and that is the load-bearing choice. Without it
the set climbs through every caller up to `run_agent`; with it, it stops exactly where the
Envelope stops flowing outward — so `turn_actions.await_opponent_turn` is **in** (it binds
one and reads its type) while `turn_commit.initiate` is **out** (its leg returns a hash).

**SITE COUNT: 12**, and every one of the five historical instances sits inside it.

| module | site |
|---|---|
| `turn_commit.py` | `await_and_respond` ← instance five |
| `turn_actions.py` | `await_opponent_turn` ← where the non-move envelope entered move handling |
| `turn_buffer.py` | `await_move` ← instance six |
| `turn_buffer.py` | `drain_trailing_hint` |
| `agent_teardown.py` | `linger_for_peer` ← deferred #17 |
| `turn_commit_pull.py` | `next_protocol_message` ← 05-17's fix |
| `agent_audit_exchange.py` | `receive_final_reveal` ← 05-15's fix |
| `turn_commit_wait.py` | `wait_for_ack_and_commit`, `wait_for_matching_ack`, `wait_for_opponent_commit` |
| `turn_commit_wait_reveal.py` | `wait_for_reveal_capturing_early_ack` |
| `deadline_wait.py` | `wait_for_opponent` |

The invariant is asserted three ways over 12 sites × 9 `MessageType` members = **108
combinations**: no traceback; every accusation a pull site writes is a `TechnicalWinReason`
member and never a decoder's message; a peer's FINAL_REVEAL is returned, buffered or left
queued but never destroyed.

The middle one is the sharp one, and it is what makes this a class fix rather than a
FINAL_REVEAL fix: `opponent_unresponsive` is a claim we measured, `'payload must be a dict,
got NoneType'` accuses a peer of sending a malformed MOVE it never sent.

## Probes — every one run, with real counts

| # | probe | result |
|---|---|---|
| A | Task 2 reverted | **8 breach rows** on the shipped path; both boundary modules fail |
| B | enumeration pointed at a non-existent package | `AssertionError: ZERO pull sites discovered ...` — **fails loudly, not a silent pytest skip** |
| C | one driver deleted | `undriven sites ['await_and_respond'], stale drivers []` |
| C′ | a **brand-new pull function** dropped into `src/pursuit/network/` | `undriven sites ['brand_new_pull']` — the "covered on the day it lands" claim, proven rather than asserted |
| D | deferred #17's exemption removed | `linger_for_peer(agent_teardown.py) <- final_reveal: the peer's published ledger was destroyed` — the exempted check is live |
| E | `kept` forced to `True` everywhere | `12 sites kept the ledger, expected 12 discovered minus 1 exempt` |
| F | `h_commit is not None` guard removed | `(REVEAL, None, True) != (REVEAL, None, False)` |

Task 2's own revert probe: **3 of the 4** new police cases fail
(`['payload must be a dict, got NoneType']` vs `['opponent_unresponsive']`, and
`ProcessKilledError`). The fourth — rule 36's counter-control — passes either way, which is
precisely what makes it a control and not a consequence of the fix.

## Rule 36 survives intact

Asserted in **three** modules, unchanged, and passing at HEAD *before* the fix as well as
after: a genuinely silent peer still earns `technical_win{opponent_unresponsive}` with the
same reason string. Nothing arrives, nothing is buffered, the ladder runs, and the sanction
fires. A fix that spared silent peers would have turned the whole 108-cell matrix green and
broken the game; it does not.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 2 — missing critical functionality] `turn_commit.py:103` was the last production
caller of `next_protocol_message` taking `on_attempt=None`**

- **Found during:** Task 2, by grepping every production caller of the primitive.
- **Issue:** 05-16 (deferred #10) marked five turn-loop ladders against `watchdog_threshold`
  and skipped this branch for the same reason the type test was skipped — it does not read
  like a wait leg. So the initiator's whole `(retry_count + 1) × response_timeout` ladder ran
  **unmarked**. Measured pre-fix on the injected clock at shipped Table-19 values: freeze at
  attempt 2 of 4, `t=70.0 s`, `touches=0`, `ProcessKilledError` — `os._exit(1)` mid-game, and
  the D-13 verdict due at t=140 s never spoken.
- **Fix:** adopting the shared leg passes `on_attempt=ctx.watchdog.touch` like the other four.
  Pinned by `test_the_initiators_own_wait_marks_its_ladder_like_every_other_leg`, on the
  existing 05-13/05-16 harness (`_turn_loop_fixtures`, injected clock, zero real sleeps).
- **Commit:** `f099ad2`

**2. [Rule 3 — blocking] `turn_commit_wait.py` breached the gate at 151/150**

- **Found during:** Task 2, at the line-limit gate.
- **Fix:** **split, never compressed.** `wait_for_reveal_capturing_early_ack` moved to
  `turn_commit_wait_reveal.py` (135 → 151 → **122**), along the division 05-18 itself created:
  three role-specific legs stay, the one shared leg leaves. Not re-exported — it imports
  `H_COMMIT_KEY` from the parent, so a re-export back would be an import cycle; the three
  importers name it directly. One intermediate step *was* de-duplication rather than a split:
  the leg docstring and the call-site comment carried the same decision narrative twice, and
  the duplicate prose was removed (QUAL-02) before the split was taken anyway at 151.
- **Commit:** `f099ad2`

**3. [Rule 3 — blocking] `test_envelope_boundary_invariant.py` breached at 151/150**

- **Fix:** the deferred-#19 case split to `test_toggle_off_move_boundary.py` (**118** / **65**),
  along a real seam — the class guard here, the one instance it found there.
- **Commit:** `e01708c`

### Found by self-audit, after the tasks were "done"

**4. [Rule 1 — bug] the `h_commit is not None` guard was UNPINNED**

- **Found during:** the self-audit, by deleting the guard and running the suite.
- **Issue:** the guard was added in Task 2 and documented in the docstring as load-bearing.
  Removing it left **all 1538 tests green**. The trap is `dict.get` returning `None`: with
  `h_commit=None`, an ACK carrying no `h_commit` key makes the comparison read
  `None == None`, so a peer's contentless ACK sets `own_ack_received`. Inert on the police
  role *today* — which is exactly why nothing reported it, and why it would surface three
  plans later with the cause long gone.
- **Fix:** `tests/unit/test_turn_commit_wait_reveal.py`, both directions asserted (without
  the second, a guard hard-wired to `False` passes the first and pins nothing). Probe F
  confirms it fires.
- **Commit:** `f27b17f`

### One assertion of mine could not fail

`assert len(sites) * len(MessageType) >= len(DRIVERS)` was written as an anti-vacuity guard
and is trivially true (108 ≥ 12). Replaced with a **positive count** —
`ledgers_kept == len(sites) - len(_LEDGER_EXEMPT)` — which is falsifiable and which probe E
confirms fires. `not breaches` alone is satisfied by a matrix that never ran, by a `kept`
flag wired to a constant, and by an exemption set that swallowed everything.

## Instance six, recorded not fixed (deferred #19)

The enumeration found it on its **first run**, which is the argument for the enumeration.
`turn_buffer.await_move` — the `commit_reveal=False` wait — has no type test of any kind and
returns every non-HINT envelope to move handling:

```
commit_reveal ON   0 of 9 unnamed reasons          <- this plan's Task 2
commit_reveal OFF  8 of 9 unnamed reasons, every one
                   'payload has neither direction nor x/y keys'
```

Not fixed here: shipped config is `commit_reveal: true`, `turn_buffer.py` is not in this
plan's `files_modified` and sits at 146/150 so the repair needs its own split, and phase 5
ends with this plan. Latent on a supported toggle is still a defect — 05-14 (G8) fixed one
of exactly this shape — so it is written down **with its numbers**. Its test asserts the
*scope*, never that the defect is correct, and **fails deliberately when #19 is closed**, so
whoever fixes it is sent to the record rather than leaving a stale entry behind.

Deferred **#16** and **#17** are left OPEN with their measurements, exactly as the plan's
non-goals require. **#20** is new: three modules within two lines of the gate, with their
seams named.

## Verification — quoted, against the 1530 / 96.64% baseline

```
1. uv run ruff check .                         -> All checks passed!
2. uv run pytest tests/ --cov                  -> 1539 passed in 187.69s
                                                  Total coverage: 96.64%
3. bash scripts/check_line_limit.sh            -> exit 0  (tree-wide)
   ... plus EVERY new file explicitly by path  -> exit 0
4. uv run python scripts/check_no_llm_in_strategy.py -> OK
5. uv run python scripts/dev_launch.py         -> exit 0
     police  uid=afa6aa3840d63e88  technical_win=0  watchdog_incident=0
             game_over=capture  audit_verdict=(matched=True, 5 turns)
     thief   uid=afa6aa3840d63e88  technical_win=0  watchdog_incident=0
             game_over=capture  audit_verdict=(matched=True, 5 turns)
```

**1530 → 1539 tests (+9), coverage 96.64% unchanged, zero failures.** The tree-wide
line-limit form enumerates via `git ls-files`, so it passes **vacuously** on untracked
files; every new file was therefore also checked explicitly by path, before and after
staging.

`test_late_peer_teardown` passed in every full run.

## Commits

| hash | message |
|---|---|
| `d249625` | `test(05-18)`: reproduce the initiator reading an honest peer's ledger as an illegal move |
| `f099ad2` | `fix(05-18)`: the initiator's own wait gets the type discipline the other legs have |
| `e01708c` | `test(05-18)`: pin the envelope-boundary class across all 12 pull sites, enumerated from source |
| `f27b17f` | `test(05-18)`: pin the h_commit None guard — found unpinned by self-audit |

## Self-Check: PASSED

All 7 created files exist on disk. All 4 commit hashes resolve in `git log`. Deferred #18
carries its `CLOSED by 05-18` block; #19 and #20 exist; #16 and #17 are both still
`Status: OPEN` with their measurements untouched, as the plan's non-goals require.
