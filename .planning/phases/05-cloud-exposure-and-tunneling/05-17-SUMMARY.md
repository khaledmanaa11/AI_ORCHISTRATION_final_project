---
phase: 05-cloud-exposure-and-tunneling
plan: "17"
subsystem: network/final-reveal-routing
tags: [gap-closure, false-accusation, rules-16-22, rule-36, NET-06, NET-07, CLOUD-02, SEC-05, routing-not-timing]
one_liner: "An early peer FINAL_REVEAL is buffered by the pull primitive instead of being eaten by whichever wait_for_* leg is running, and the audit consults that buffer before it waits -- so the silence we used to manufacture, and then punish with OPPONENT_UNRESPONSIVE, no longer exists; a genuinely silent peer is still accused, proven by a control that fails against every relaxation."
requires:
  - "05-15 (G10): the MIRROR of this boundary inside receive_final_reveal -- an envelope-TYPE check one layer further in, whose four cases now also pin this fix"
  - "05-16 (deferred #10): every bounded attempt marked, preserved byte for byte in the moved primitive"
  - "05-13 (G6): the per-bounded-attempt watchdog touch and the `on_attempt` hook, moved verbatim"
  - "05-04 (G1): board_outcome-driven non-accusation policy in run_final_audit, unchanged"
provides:
  - "network/turn_commit_pull.py: the D-58 pull primitive, split at the gate; a FINAL_REVEAL is RECORDED and still returned, a HINT is recorded and skipped"
  - "network/final_reveal_buffer.py: record_final_reveal (first arrival wins) / take_final_reveal (consumes)"
  - "commit_state.CommitTurnState.early_final_reveal: the per-GAME slot beside own_ack_received"
  - "receive_final_reveal: the buffer consulted BEFORE the ladder, so an early ledger short-circuits it"
  - "deferred items #16, #17, #18 -- all three measured, none fixed"
affects:
  - "src/pursuit/network/turn_commit_wait.py (145 -> 135; three now-false docstrings corrected)"
  - "src/pursuit/network/turn_buffer.py, agent_audit_exchange.py, commit_state.py"
tech-stack:
  added: []
  patterns:
    - "Split at the 150-line gate along a seam a deferred item had already NAMED (turn_commit_wait.py -> turn_commit_pull.py, deferred #11's own wording)"
    - "Buffer-and-RETURN vs buffer-and-SKIP: the special case is chosen by who wants the envelope, not by symmetry"
    - "Count the queue pulls to tell a short-circuit from a right-answer-after-the-ladder"
    - "Two duplicate copies carrying DIFFERENT payloads, so first-wins and last-wins are distinguishable"
key-files:
  created:
    - src/pursuit/network/turn_commit_pull.py
    - src/pursuit/network/final_reveal_buffer.py
    - tests/unit/test_early_final_reveal.py
    - tests/unit/test_early_reveal_routing.py
    - tests/unit/_early_reveal_fixtures.py
  modified:
    - src/pursuit/network/turn_commit_wait.py
    - src/pursuit/network/turn_buffer.py
    - src/pursuit/network/commit_state.py
    - src/pursuit/network/agent_audit_exchange.py
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
decisions:
  - "A FINAL_REVEAL is buffered and STILL RETURNED, unlike a HINT which is buffered and skipped. Skipping it would starve receive_final_reveal -- the one caller that wants it -- of the very envelope it waits for, which is the same false accusation through a different door."
  - "The buffer is consulted BEFORE the ladder, not after it. Probe P5 shows the after-variant returns the same records and accuses nobody while costing the audit its whole 135 s ladder against a 60 s watchdog_threshold; it is refuted by counting queue pulls (2 != 0)."
  - "First arrival wins. A re-send is either a transport retry (identical) or a peer revising what it published after seeing ours; rule 36 is about what a peer published."
  - "take_final_reveal CONSUMES. The justification in its first draft was false and is recorded as a correction, not silently rewritten -- probe P6 supplies the true one."
  - "turn_commit.py:103 (the police branch's bare pull) was NOT fixed. Measured pre-existing and byte-identical either way; the repair is a turn-loop policy decision. Filed as deferred #18."
metrics:
  duration: "~3h"
  tasks: 3
  commits: 4
  completed: 2026-08-17
---

# Phase 05 Plan 17: We Manufacture the Silence We Then Punish — Summary

**A rules-16/22 false-declaration path against a peer doing nothing wrong is closed, and
rule 36's sanction is proven intact rather than asserted.** Three tasks, four atomic
commits, six new cases, seven revert probes. The plan's own framing held up under attack:
the inference at `agent_audit_wiring.py:90-93` is sound and was not touched — what was
false was its premise, and the fix restores the premise.

---

## The reproduction, in this repository's own numbers

`b29a098` committed RED. An honest peer finishes its turn loop first and pushes its ledger;
our still-running `wait_for_reveal_capturing_early_ack` then receives the in-game REVEAL it
was waiting for, so our own turn loop completes normally and a board outcome stands.
Nothing anywhere went wrong. Measured at HEAD, verbatim:

```
TURN LOOP LEG: queued=2 -> returned type='reveal' verdict=None queue_left=0
AUDIT: our push landed? 1 call(s) = ['receive_final_reveal']
AUDIT OUTCOME: <Outcome.TECHNICAL_LOSS: 'technical_loss'>

{"event": "technical_win", "reason": "opponent_unresponsive", "retries_attempted": 2,
 "timeout_seconds": 0.05, "sender": "thief", "turn": 0, ...}
{"event": "game_over", "outcome": "technical_loss", "sender": "thief", "turn": 0, ...}
```

`queue_left=0` is the whole defect in one number: the peer's FINAL_REVEAL was consumed off
our own queue and destroyed. `1 call(s)` is the other half — our push **landed**, so
`run_final_audit` took the accusatory branch. **No `audit_verdict` was ever written**, and
the peer's real ledger — one turn, hashed through `commit_pack`, matching a COMMIT and a
REVEAL we had watched it send — was gone.

`retries_attempted: 2` is `make_ctx`'s fast test ladder; at shipped Table-19 values the
same exhaustion is 4 attempts and 135 s. **The ladder length is not the defect**, which is
what probe P2 exists to prove.

### Reachability, stated honestly rather than assumed

Two copies of THIS codebase serialise their own pushes — each `await`s its tool call, and
`tools._accept` enqueues before answering — so a clean loopback game never reorders. The
ordering needs a perturbation, and both available ones are ordinary league-day weather:

1. **A league peer is a second, independent implementation** (that is the whole premise of
   Phase 5's two-repo submission), free to publish its ledger the moment it resolves.
2. **Inside this codebase, one lost or ladder-exhausted message is enough.** The peer
   aborts its own turn loop, runs its own final audit, and publishes — while we are still
   waiting for the message it will now never send. That is
   `test_the_buffered_reveal_survives_our_own_leg_timing_out`, and it is the case where
   the two facts pull in opposite directions: our leg's OWN verdict about the missing
   REVEAL is untouched (NET-06 is not softened), while the ledger that arrived in the same
   window is still audited, so the audit does not stack a FALSE accusation on top of a
   legitimate one.

This is written down because the reproduction would otherwise read as a scenario chosen to
make the bug appear.

---

## Task-by-task

### Task 1 — `b29a098` (test, RED): the false accusation, reproduced

`tests/unit/test_early_final_reveal.py` + `tests/unit/_early_reveal_fixtures.py`. Failed at
HEAD for exactly the stated reason:
`assert (<Outcome.TECHNICAL_LOSS: 'technical_loss'>, 1) == (None, 0)`.

**The fixture refuses the cheap shortcut, deliberately.** The peer's ledger is built through
`security.commit_pack` itself and paired with two `message_received` wire records, so the
post-fix assertion is a **MATCHED audit over real hashes** — `[(True, 1)]` on
`(matched, len(peer_audit))`. With `records=[]` and nothing observed, `audit_peer_records`
returns `[]` and `all_matched([])` is True, so every case in this corridor would have passed
over a ledger that never arrived. That empty shape is also byte-indistinguishable from the
`{"records": []}` rule-36 evasion — the exact vacuity 05-15 caught in its own control.

Both halves are asserted **as one tuple**, applying 05-15's shadowed-assertion finding
pre-emptively: as separate statements the outcome assertion fires first and the accusation
count is never reached.

### Task 2 — `28adc4d` (fix): buffer it, do not eat it

**Routing, not timing. No timeout, retry count or backoff moved; no Table-19 value was
touched anywhere (CLAUDE.md rule 1).**

- `turn_commit_pull.next_protocol_message` records every FINAL_REVEAL into
  `ctx.commit_state.early_final_reveal` and **still returns it**;
- `agent_audit_exchange.receive_final_reveal` consults that buffer **at the top of every
  iteration, before the wait**;
- `final_reveal_buffer` holds the two functions; the slot lives on `CommitTurnState`.

**The asymmetry with HINT is the design, and it is the part worth reading.** A HINT is
buffered and SKIPPED because no caller of the primitive ever wants one. A FINAL_REVEAL is
buffered and RETURNED because exactly one caller does — and skipping it would starve
`receive_final_reveal` of the very envelope it is waiting for, burn a ladder, and produce
the same false accusation through a different door. Buffering is what makes the four
`wait_for_*` legs' tolerated-jitter drop harmless again: **the legs' drop policy is
byte-unchanged**, nothing here started keeping envelopes, and every drop is now free rather
than merely tolerated.

**Rule 36 is byte-unchanged.** An empty buffer still runs the full ladder and still returns
the verdict `run_final_audit` accuses on. Nothing about `agent_audit_wiring.py:90-97` was
edited.

**Two 150-line SPLITS, never compressions, both at seams already named on paper:**

| File | Before | After | Split |
|---|---|---|---|
| `turn_commit_wait.py` | 145 | **135** | `next_protocol_message` -> `turn_commit_pull.py` (78) |
| `turn_buffer.py` | 139 | **142** | the buffer -> `final_reveal_buffer.py` (58) |

The first is **deferred item #11's own wording** — "the four `wait_for_*` legs (policy) away
from `next_protocol_message` (the primitive) ... the same policy-vs-mechanism split
`handshake.py`/`handshake_wire.py` already uses". The moved body is **byte-identical**,
verified by diff: the only difference in the whole function is the two added lines.

```
$ diff <(git show HEAD:...turn_commit_wait.py | sed -n '90,109p') <(sed -n '/async def _pull/,/return envelope, None/p' turn_commit_pull.py)
18a19,20
>         if envelope.type is MessageType.FINAL_REVEAL:
>             turn_buffer.record_final_reveal(ctx, envelope)
```

Both names are re-exported, so `turn_commit.py`, `agent_audit_exchange.py`,
`agent_audit_observed.py`, the gate scripts and the whole suite resolve unchanged.

**The three now-false docstrings are corrected in place** — `wait_for_ack_and_commit`,
`wait_for_reveal_capturing_early_ack`, and `wait_for_opponent_commit`'s inline comment at
the old `:176`, the sentence this plan was written about. Each now says *why* its drop is
safe rather than asserting that it is. `turn_commit_wait.py`'s module docstring gained a
paragraph stating what "dropped as tolerated jitter" now means, and `next_protocol_message`'s
own "duplicate/unexpected types are the caller's own concern to drop" was corrected in the
move (a fourth false sentence the plan did not count — see deviations).

### Task 3 — `0a896aa` (test): the controls, and rule 36 kept intact

Six cases, split across two files at the 150-line gate along a real seam: the
accusation-shaped cases and their control in `test_early_final_reveal.py` (133), the routing
mechanism in `test_early_reveal_routing.py` (111). Split, never compressed — no assertion
was shortened to fit.

| Case | What it pins |
|---|---|
| the reproduction | the early-pushing peer is MATCHED, zero `technical_win`, ledger AUDITED |
| **the silent-peer counter-control** | a peer whose full turn we watched and which then published nothing still earns `TECHNICAL_LOSS` + `technical_win{opponent_unresponsive}` |
| leg times out | our leg's own NET-06 verdict is untouched AND the buffered ledger still reaches the audit |
| duplicate | first-wins over two DIFFERENT ledgers; a second receive call is not served the same ledger |
| second leg | the routing is in the shared primitive, pinned on `wait_for_opponent_commit` — the leg whose own comment named the drop |
| short-circuit | **zero queue pulls** across the audit |

No `parametrize` in either file, deliberately: an empty parameter set is a silent pytest
SKIP, and a control that skips is a control that cannot fail.

---

## Revert probes — every wrong fix RUN, with real counts

Run over the two new files **plus 05-15's four `test_agent_audit_receive.py` cases** (10
tests total), except P2 which needs its own harness.

| # | What was broken | Result |
|---|---|---|
| **P1** | the primitive's FINAL_REVEAL routing reverted (pre-fix producer) | **8 failed / 2 passed** |
| **P2** | **THE WRONG FIX — widen the receive ladder instead of routing** | ladder ran **21 attempts** (10x the shipped 4) and the accusation is **byte-identical**: `TECHNICAL_LOSS`, 1 `technical_win` |
| **P3** | the audit stops consulting the buffer (producer kept) | **4 failed / 6 passed** |
| **P4** | first-wins -> last-wins | **1 failed / 9 passed** |
| **P5** | the buffer consulted AFTER the ladder (the *defensive* wrong fix) | **1 failed / 9 passed**, on `2 != 0` queue pulls |
| **P6** | `take` -> peek (non-consuming) | **1 failed / 9 passed** |
| **P7** | the silent-peer counter-control against every relaxation | see below |

**P2 is the one the plan demanded, and it is decisive.** Widening the ladder is the
tempting fix, it moves a Table-19 number, and it **cannot work**: the envelope was already
consumed. Ten times the ladder produces the identical `technical_win{opponent_unresponsive}`
against the identical honest peer. `P2: ladder attempts actually run = [21]`.

**P5 is the discrimination this plan owed.** A buffer consulted after the ladder returns the
same records, accuses nobody, and passes every other assertion in this corridor — while
costing the audit its whole `(retry_count + 1) x response_timeout`, i.e. 135 s against a
60 s `watchdog_threshold` at shipped values (deferred #10's own arithmetic, and a real risk
of dying before the verdict is written). Zero pulls is the only visible difference, so the
fixture counts them.

**P7, the counter-control, stated as a probe rather than as a promise.** The silent-peer
case passed **unchanged in all six probes above** and fails against any relaxation of
`run_final_audit`'s accusatory branch — it is the case that would have made a
"stop-accusing" fix look correct. The plan's warning was right: a fix that spares the silent
peer has broken the game, and the shape of this change is "stop manufacturing the silence",
never "stop punishing it".

**One coupling worth naming:** P1 and P3 also fail three or four of 05-15's *own* receive-leg
cases. That is real — the consumer now depends on the producer having routed — and it means
the 05-15 contract is enforced through the buffer, so a future revert of either half is
caught by two independent plans' tests rather than one.

---

## Self-audit: a justification of my own that was false

`take_final_reveal`'s first docstring justified consuming rather than peeking by claiming a
peek "would spin on the same envelope forever". **That is false** — the caller returns on
the first non-None, so a peek terminates identically. Caught by reasoning the probe through
before running it, then confirmed by running it: P6 makes the function a peek and exactly one
assertion fails, the duplicate case's *second* receive call, which is served the ledger again
instead of the verdict a silent peer earns.

The false sentence is **replaced and recorded as a correction in the source**, not quietly
rewritten — the 05-13/05-14/05-15 house rule. The property is real, the reason given for it
was not, and those are different defects.

---

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — Blocking] Two 150-line gate breaches, both SPLIT, never compressed**
- **Found during:** Task 2, before anything landed. `turn_commit_wait.py` was at 145/150
  (deferred #11 has been watching it for three plans) and this change needs both the routing
  and three docstring corrections; `turn_buffer.py` was at 139 with ~20 lines of buffer to
  host.
- **Fix:** `next_protocol_message` -> `turn_commit_pull.py` along the seam deferred #11 had
  already named, body byte-identical bar the two added lines; the buffer ->
  `final_reveal_buffer.py`. Both re-exported.
- **Files:** `src/pursuit/network/turn_commit_pull.py`, `src/pursuit/network/final_reveal_buffer.py`
- **Commit:** `28adc4d`

**2. [Rule 1 — Bug] The plan counted THREE now-false docstrings; there are FOUR**
- **Found during:** Task 2, correcting them.
- **Issue:** the plan names `:176` and the two leg docstrings at `:119-136` / `:148-155`.
  `next_protocol_message`'s own docstring also ended "Duplicate/unexpected types are the
  caller's own concern to drop" — which is precisely the sentence the fix falsifies, and the
  only one *inside* the function that changed.
- **Fix:** corrected in the move, and the module docstring of `turn_commit_wait.py` gained a
  paragraph on what "dropped as tolerated jitter" now means, since three of its four legs
  now rely on a fact stated in a different file.
- **Commit:** `28adc4d`

**3. [Rule 2 — Missing critical] The plan's test file would have breached the gate**
- **Found during:** Task 3. One file with all six cases measures ~166 code lines.
- **Fix:** split into `test_early_final_reveal.py` (133) + `test_early_reveal_routing.py`
  (111) along the accusation/mechanism seam, plus `_early_reveal_fixtures.py` (111) for the
  shared `commit_pack`-built honest peer turn and the `CountingQueue`. Not one assertion was
  shortened.
- **Commit:** `0a896aa`

**4. [Rule 4 territory — NOT fixed, filed] A third false-accusation door, found by grepping
production callers**
- **Found during:** Task 3's caller grep, not by reading the diff.
- **Issue:** `turn_commit.py:103` — the POLICE branch of `await_and_respond` calls the pull
  primitive **bare**, with no type test, and hands whatever arrives to `await_opponent_turn`
  as the opponent's REVEAL. Measured: an early FINAL_REVEAL there becomes
  `Outcome.TECHNICAL_LOSS`, reason `'payload must be a dict, got NoneType'`.
- **Why not fixed:** measured **byte-identical with this plan's routing reverted**, so it is
  pre-existing; `turn_commit.py` is not in this plan's `files_modified`; and the repair
  requires deciding what the initiator should do when the peer has demonstrably ended the
  game — a turn-loop policy decision with its own controls.
- **Consequence of the fix for it:** strictly better. The ledger is now SAFE in the buffer
  (`buffered = MessageType.FINAL_REVEAL` where pre-fix it was `None`), so the audit still
  matches even while the turn loop mis-declares.
- **Filed as:** deferred item **#18**.

---

## Non-goals, filed WITH their measurements

**#16 — the linger's quiet interval is derived from the wrong clock.**
`agent_teardown.py:22-25` says "if the peer were going to retry, it would have retried inside
one backoff". A peer schedules its retry one backoff from its own **failure**, up to one
`response_timeout` after the attempt **started** — and the start is what we observe as the
arrival. At the shipped values (`response_timeout: 30`, `backoff_seconds: 5`, read from
`config/police/network.json`, none moved):

| our quiet interval | our total linger cap | worst-case arrival -> retry |
|---|---|---|
| **5 s** | **30 s** | **35 s** = `response_timeout + backoff_seconds` |

The retry lands **5 s after the whole linger returned** and **30 s after the interval the
prose claims covers it**. The window still covers a fast failure (connection refused, a 502);
it does not cover the slow case. Not a false-accusation path by itself — recorded because
that derivation is the entire reason the module contains no numeric literal, and a
derivation that does not hold is worse than a magic number: it looks audited.

**#17 — the linger drains a peer FINAL_REVEAL and discards it unaudited.**
`linger_for_peer` pulls through `deadline.wait_for_opponent`, a plain `queue.get()`, not
through the primitive — so **05-17's buffer does not cover that window**. Measured:

```
queue before linger      = 1
queue after linger       = 0        <- consumed
buffered after linger    = None     <- and NOT routed to the buffer
log kinds                = []       <- no record that it ever arrived
```

Left open because by then `run_final_audit` has already returned, so keeping the content
raises a policy question (does a peer that publishes after our audit get audited? what if our
verdict already accused it?) rather than a routing one. The cheap half — route the drain's
arrivals through `record_final_reveal` so the evidence survives — is now genuinely cheap and
is named in the item.

---

## Measurements

**Suite:** `1530 passed / 0 failed`, coverage **96.64%** (baseline **1524 / 96.62%**) —
**+6 tests, exactly the six added, +0.02pp**. All six changed/new modules at **100%**:
`turn_commit_pull.py` 26/26, `final_reveal_buffer.py` 11/11, `agent_audit_exchange.py`
30/30, `turn_commit_wait.py` 49/49, `commit_state.py` 27/27, `turn_buffer.py` 58/58.
**`test_late_peer_teardown` passed** — deferred #4's fix (`3babfe6`) held across every run
here, and nothing in this plan disturbed it.

**Gates:** `uv run ruff check .` -> **All checks passed**; `bash scripts/check_line_limit.sh`
-> **exit 0** tree-wide **and exit 0 again on the five new files named explicitly**, because
the no-argument form enumerates via `git ls-files` and would have passed **vacuously** over
untracked files; `uv run python scripts/check_no_llm_in_strategy.py` -> **OK** (this plan
touches no `strategy/` file at all — the algorithm decides, and no model is anywhere near
this path).

**Live two-process loopback game** (`uv run python scripts/dev_launch.py`, **exit 0**),
one shared uid `a97adb14e48fc621` across both logs and both filenames:

| | police | thief |
|---|---|---|
| `audit_verdict` | **matched=True**, 6 peer + 6 self | **matched=True**, 6 peer + 6 self |
| `technical_win` | **0** | **0** |
| `watchdog_incident` | **0** | **0** |
| `audit_incomplete` | 0 | 0 |
| `game_over` | `capture` | `capture` |

The thief's log carries one pre-adoption record (its first `illegal_transition`, index 0 of
50) under its own minted `da218ba0628f172d` — the expected 05-05 shape, since
`adopt_negotiated_game_id` rebinds at the handshake; every subsequent record and both
filenames carry the shared stem.

**GATE-6** (`uv run python scripts/measure_gate6.py`, exit 0) — all three §10.4 criteria
**PASS**. Evidence **RESTORED, not committed**: the diff against the committed copy is 2
`predates_detail` mtime lines, 1 `generated_at` line, and 05-15's two pre-existing
`"game_over": 1` counters (the committed evidence dates from 2026-08-14, before that plan).
Every verdict and boolean field byte-identical.

**Knowledge graph refreshed:** 7934 nodes / 14322 edges / 481 communities (was 7832 /
14141 / 479). `graph.html` was skipped by the tool itself — 7934 nodes exceeds its 5000-node
HTML viz limit — which is a pre-existing tooling ceiling, affects no committed artifact
(`graph.html` is gitignored), and is noted so the next reader does not read the copy step's
exit 1 as a build failure. `graph.json` and the committed `GRAPH_REPORT.md` both updated.

**Nothing weakened, nothing skipped, no `--no-verify`.**

---

## Self-Check: PASSED

Created files verified present on disk: `src/pursuit/network/turn_commit_pull.py`,
`src/pursuit/network/final_reveal_buffer.py`, `tests/unit/test_early_final_reveal.py`,
`tests/unit/test_early_reveal_routing.py`, `tests/unit/_early_reveal_fixtures.py`.
Commits verified in `git log`: `b29a098`, `28adc4d`, `0a896aa`, `0cb9aea`.
