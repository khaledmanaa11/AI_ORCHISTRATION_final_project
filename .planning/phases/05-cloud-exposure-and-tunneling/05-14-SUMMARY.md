---
phase: 05-cloud-exposure-and-tunneling
plan: "14"
subsystem: network/language-channel
tags: [gap-closure, G8, evidence-integrity, hint-channel, rule-20, LANG-01, LANG-03, QUAL-11]
one_liner: "A re-sent hint is decoded once on BOTH roles' timings -- the marker had to move from arrival to consumption, which the plan's own version could not see -- and both take_my_turn branches stamp the turn actually played, including with commit_reveal off."
requires:
  - "05-06: the widened receive window (_HINT_LOOKBACK_TURNS) and the freshness guard"
  - "05-12: the peer-data boundary rule (validators total over hostile input)"
  - "05-13: the turn-loop/audit shape left byte-identical where untouched"
provides:
  - "turn_hint_store.consume_hint: the one place an inbound hint is spent, and the one place it is marked spent"
  - "turn_hint_store.is_replay: the single-decode guarantee, with the window width untouched"
  - "pre_turn_state.turn on take_my_turn's initiator branch: the turn actually played, on both protocol paths"
  - "docs/PARAMETERS.md 'Derived protocol constants' section: _HINT_LOOKBACK_TURNS with its derivation"
affects:
  - "src/pursuit/network/turn_hint_buffer.py, turn_hint_store.py, turn_language_io.py, turn_actions.py"
  - "docs/PARAMETERS.md, docs/phases/phase-5/TODO.md"
tech-stack:
  added: []
  patterns:
    - "Split at the 150-line gate, never compress (turn_hint_buffer.py 141 -> 88 + 91)"
    - "Shared test drivers in a non-test _*.py helper module (the _hint_fixtures.py precedent)"
    - "A plain install_spy(monkeypatch) instead of a cross-imported @pytest.fixture (ruff F811)"
key-files:
  created:
    - src/pursuit/network/turn_hint_store.py
    - tests/unit/test_hint_replay.py
    - tests/unit/test_hint_replay_window.py
    - tests/unit/_hint_decode_fixtures.py
    - tests/integration/test_hint_stamp_toggle_off.py
  modified:
    - src/pursuit/network/turn_hint_buffer.py
    - src/pursuit/network/turn_language_io.py
    - src/pursuit/network/turn_actions.py
    - src/pursuit/security/audit_shape.py
    - docs/PARAMETERS.md
    - docs/phases/phase-5/TODO.md
    - .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md
decisions:
  - "The consumed marker is written at CONSUMPTION, not at arrival. The plan specified arrival and relied on maybe_resolve's clear as the marker's lifetime; measured, that lifetime is right for the responder and destroyed before the initiator's decode, which still decoded a re-send twice."
  - "Only a STRICTLY NEWER stamp re-enters. buffer_if_not_older's inclusive >= is right for an overwrite and wrong for a replay guard -- reusing it re-admits the exact repeat."
  - "An arrival with no usable stamp cannot prove it is newer, so it does not re-enter either. Same 'peer data proves nothing until it does' rule usable_stamp keeps."
  - "The window WIDTH is untouched. Marker and window dovetail rather than overlap; re-narrowing is the tempting wrong fix and is refuted by probe P4 (6 failures)."
  - "_HINT_LOOKBACK_TURNS is PUBLISHED in PARAMETERS.md while 05-12's _MAX_PEER_GAME_ID is not, deliberately and with the reason recorded in both places -- one is a protocol constant two implementations must agree on, the other a structural filesystem limit."
  - "The toggle-off MOVE stamp (deferred #13) was measured and NOT fixed: the repair changes turn_commit.initiate's signature, which on the commit-reveal-ON path feeds the D-59 hash input and the D-64 ledger join key."
metrics:
  duration: "~2h"
  completed: 2026-08-16
  tasks: 3
  commits: 7
  tests_added: 7
  suite: "1491 passed / 0 failed / 96.59% (baseline 1484 / 96.58%)"
---

# Phase 05 Plan 14: The Hint Channel Is Correct on Every Supported Path — Summary

G8 closed. Two evidence-integrity defects in the hint channel are fixed, and the headline is
that **the plan's own fix for the first one was half right — the probe is what said so.**

---

## Task 1 — one inbound hint is decoded at most once (`f6bbc0f`, `54619a1`)

**Before, measured against live source at `4fd1d74`.** `decode_turn_hint` POPS
`ctx.incoming_hints` (`turn_language_io.py:59`) while `_buffer_if_not_older` compares an
arrival only against what is *still* buffered. A hint re-sent for turn N-1 after a pop
therefore sailed through the (correctly) widened window and was decoded a **second** time,
re-driving `observe_reliability` and the belief update on evidence already counted. Before
05-06 widened the window the old `turn < ctx.state.turn` guard dropped the duplicate as a
side effect; nothing did afterwards.

**The plan's fix, and why it was not enough.** It specified repurposing `ctx.pending_hints`
as the consumed marker — recorded at *arrival*, cleared by `maybe_resolve`, "precisely the
right lifetime for a replay guard whose lookback window is one turn wide". Probed directly:

```
                stamp  state.turn  marker at decode                          decodes  2nd outcome
responder         3         4      {'text':...,'turn':3}                        1      no_hint
initiator         3         4      None                                         2      no_evidence
```

The two roles' timings differ, and the attempt-4 evidence is what says so — re-measured this
session from the committed logs:

| side | inbound hint records | `record_turn` vs `envelope_turn` |
|---|---|---|
| machine B (thief / responder) | 6 + 6, both games | `record_turn == envelope_turn + 1` — 6 of 6 |
| machine A (police / initiator) | 5 + 5, both games | delta 0 — 5 of 5 |

The responder's hint arrives *after* its receiver has resolved, so arrival and decode fall in
the same clear-interval and the arrival-time marker is still there. The initiator's arrives
*during* the turn; `maybe_resolve` then clears `pending_hints` before `take_my_turn` decodes
it a turn later, **destroying the marker before the consumption it was meant to mark**.

**Fixed by moving the write to the consumption.** `turn_hint_store.consume_hint` performs the
same pop and leaves what it took in `pending_hints`; `decode_turn_hint` calls it instead of
popping a dict it does not own. The one place that spends a hint is now the one place that
marks it spent. After: initiator `decodes=1`, responder `decodes=1`.

`turn_hint_buffer.py` measured **141/150** with the guard in it, so the buffers were **SPLIT**
into `turn_hint_store.py` — never compressed (CLAUDE.md; the 05-12/05-13 precedent). 88 and 91
code lines respectively. The seam is real: `record_hint` keeps the ingestion policy (log the
receipt, then the drop window), the store owns the buffers and their rules.

**Two loose ends the plan named, both done.**

- The **confounded `token_spend.calls = 0` sentence is deleted**, not reworded. Re-measured:
  machine B's 2026-08-13 log shows `calls = 0` on all five `language_turn` records — but that
  same zero covers the COMPOSE half, whose texts came from the template bank
  (`services/language_turn.py:76-81`), so it is equally consistent with "no key at all". Two
  unconfounded proofs replace it: (1) `decode_turn_hint` emits `no_hint` on exactly one
  branch — the buffer pop returning nothing — which sits UPSTREAM of every provider concern,
  while a key-starved decode takes the other branch and logs `no_evidence` *with* the text
  (`llm/decode.py:66-67`, the TemplateProvider neutral); so the thief's 5-of-5 `no_hint` says
  the buffer was empty whatever the key situation was. (2) The 6/6 boundary measurement above.
- **`_HINT_LOOKBACK_TURNS` is recorded in `docs/PARAMETERS.md`** under a new
  *"Derived protocol constants — **not** Appendix F values"* section, with its derivation, both
  measurements, and **no Status column on purpose** — a derived constant is not `fixed`,
  `minimum` or `negotiable`. It stays a source constant with no config leaf (rule 1).
  Both the doc and the source comment state why this is treated **differently on purpose**
  from 05-12's `_MAX_PEER_GAME_ID`: this one is a message ORDER two independent
  implementations must agree on, that one is a structural 255-byte path-component limit
  nobody should tune. They are deliberately not harmonised.

## Task 2 — both branches stamp the turn actually played (`91dbc86`)

**Before.** `turn_actions.py:128` stamped `ctx.state.turn` on the initiator branch, justified
by a comment claiming the initiator's own `maybe_resolve` is a no-op. That holds only with
commit-reveal ON — a **precondition the comment assumed rather than stated**. With
`ctx.security.commit_reveal` false (`turn_commit.py:63-64`, `:100-101`, a supported path
pinned by `test_commit_reveal_protocol.py`'s byte-equivalence case) `pending_action` is never
set, so BOTH sides come through that branch; the second mover finds the opponent's slot
already filled, `maybe_resolve` advances N -> N+1, and the hint went out **one turn in the
future**. The receiver's drop guard never fires for a future stamp, so it corrupted wire
evidence *silently* rather than dropping it (rule 20).

**After.** `pre_turn_state.turn` — captured before `record_action`/`maybe_resolve`, the same
discipline `await_opponent_turn`'s `observed_turn` keeps. Measured on a full toggle-off game:

```
                        BEFORE            AFTER
first mover  hints      [0..15]           [0..15]     (control side, unchanged)
second mover hints      [1..15]           [0..14]
```

Latent, not active — shipped config is `commit_reveal: true` — and fixed anyway, because a
latent evidence defect on a supported toggle is still a defect. The commit-reveal-ON path is
byte-unchanged: `test_hint_delivery.py` passes **unedited**, 3/3.

## Task 3 — tests (`914662c`, `9852b3f`)

Three new modules plus one shared driver, 7 tests:

- **`test_hint_replay.py`** — asserted at the DECODE boundary, not at the buffer, because the
  defect is not "a dict got overwritten": it is `observe_reliability` and the belief update
  driven twice. Counts both side effects and reads `decode_turn_hint`'s own outcome word,
  whose values say the right things apart (`no_evidence` = a text arrived and was decoded;
  `no_hint` = nothing was in the buffer). **Both roles' timings covered separately**, which is
  the whole point of the module.
- **`test_hint_replay_window.py`** — the boundaries. A genuinely newer hint is still decoded
  (this is the discrimination the rule owes: "refuse everything after a pop" would pass every
  replay case while silencing the channel — the 0-of-5 shape 05-06 exists to have fixed); an
  unstamped re-send is refused without raising; and the marker/window hand-off across
  `maybe_resolve` is asserted rather than argued.
- **`test_hint_stamp_toggle_off.py`** — the `commit_reveal=False` stamp, with the first mover
  as the paired fairness control. **Ground truth is derived (`0..N-1`), never the MOVE
  envelope**, which is itself stamped `1..16` on that path (deferred #13) — comparing hints
  against moves would have compared two wrong numbers and passed vacuously.

## Revert probes — all five fail, with real counts

| # | What was reverted | Result |
|---|---|---|
| P1 | the replay guard removed entirely | **3 failed** / 28 passed |
| P2 | **THE PLAN'S OWN FIX** — marker at arrival, not at consumption | **1 failed** / 30 passed — exactly `..._on_the_initiator_timing`; the responder case passes, which is the measurement |
| P3 | `is_replay` reuses `buffer_if_not_older`'s inclusive comparison | **3 failed** / 28 passed |
| P4 | **THE WRONG FIX** — re-narrow the window to `turn < ctx.state.turn` | **6 failed** / 25 passed |
| P5 | initiator branch stamps `ctx.state.turn` again | **2 failed** (after the self-audit below; 1 before) |

P4 is the discrimination this plan owed. Re-narrowing would "fix" the duplicate by dropping
the hint before it was ever decoded, reopening the gap 05-06 exists to close — and it fails
`test_record_hint_keeps_a_hint_one_turn_old` and
`test_both_sides_actually_receive_a_decodable_hint`, both **byte-unedited**.

## Self-audit findings on my own diff

1. **A test that failed to fail.** `test_the_peer_receives_the_corrected_numbers_on_the_wire`
   originally asserted only `got == sent[:len(got)]` — which holds just as well when BOTH
   sides' numbers are one turn into the future. It **passed against probe P5**, the exact
   regression it exists to catch. Pinned on the played turns instead (`9852b3f`); P5 now fails
   2 of 2 in that file. Found by RUNNING the wrong fix, not by reading the code — the same
   lesson 05-13 recorded.
2. **Production callers grepped for every new name.** `buffer_if_not_older` 2 call sites,
   `is_replay` 1, `consume_hint` 1, `usable_stamp` reached through both, `_HINT_LOOKBACK_TURNS`
   1. No dead validator shipped. `ctx.pending_hints` — declared, cleared and written since
   Phase 4 with **zero production readers** — now has one, so `test_turn_buffer.py`'s four
   assertions on it stop being a write-only-buffer trap without a character changed.
3. **No vacuous passes by construction.** No `parametrize` anywhere in the new files (05-12's
   empty-parametrize-is-a-silent-SKIP trap), every case has a named non-vacuity assertion
   (`assert first_mover and second_mover`, `assert got`), and every count assertion is an
   equality (`== 1`), which fails against 0 as well as 2.

## Deviations from plan

**1. [Rule 1 - Bug] The plan's marker placement did not close the initiator's replay.**
Found during Task 3 while deriving the test's ground truth; confirmed by direct probe before
any code changed. Fixed by writing the marker at consumption. `turn_language_io.py` was
already in the plan's `files_modified`, so the decode site was in scope. Commit `54619a1`.

**2. [Rule 3 - Blocking] `turn_hint_buffer.py` breached the 150-line gate at 141/150 + 11.**
Split into `turn_hint_store.py`, never compressed. Commit `54619a1`.

**3. [Rule 1 - Bug] `security/audit_shape.py:30` cross-referenced `turn_hint_buffer._usable_stamp`,**
which the split moved. Corrected in the same commit rather than left stale.

**4. [Rule 3 - Blocking] ruff `F811` on a cross-module `@pytest.fixture` import.** Resolved by
making the spy a plain `install_spy(monkeypatch)` function in `_hint_decode_fixtures.py` —
one line per test, no `# noqa` anywhere.

**5. [Scope boundary - logged, NOT fixed] Deferred item #13.** On the same toggle-off path the
second mover's MOVE envelope is stamped `1..16` for turns `0..15` (`send_move_only` reads
`ctx.state.turn` after the same `maybe_resolve`). Same defect class, one line away — but the
repair changes `turn_commit.initiate`'s signature, and on the commit-reveal-ON path that
`turn` feeds `commit_own_action`'s D-59 hash input and the D-64 ledger join key, where a wrong
number is a rules-19/22 technical loss rather than an evidence blemish. That wants its own
plan with its own tamper tests, not a drive-by inside a hint-channel fix.

## Gates

```
ruff check .                    All checks passed!
scripts/check_line_limit.sh     exit 0
check_no_llm_in_strategy.py     OK
pytest --cov                    1491 passed / 0 failed / 96.59%   (baseline 1484 / 96.58%)
  turn_hint_store.py            100%
  turn_hint_buffer.py           100%
  turn_language_io.py           100%
  turn_actions.py                99%  (line 208, a pre-existing defensive log_illegal branch
                                       in the untouched await_opponent_turn block)
measure_gate6.py                exit 0 -- all three criteria PASS; evidence JSON differed in
                                exactly 3 timestamp lines, every verdict field byte-identical;
                                RESTORED, not committed
dev_launch.py                   exit 0 -- one shared uid 83143c7b54bdbfbc, both sides
                                audit_verdict matched=true, zero technical_win, zero
                                watchdog_incident; police hints [0,1,2,3,4] == reveals,
                                thief hints [0,1,2,3] == reveals[:-1]; both sides decode
                                real inbound hints (3 of 5 / 3 of 4 non-no_hint)
knowledge graph                 7656 nodes / 13731 edges / 465 communities
                                (was 7588 / 13614 / 465)
```

**One failure in the first full-suite run**, `test_late_peer_teardown.py::test_without_the_linger_the_late_peers_own_push_is_cut_off`
— the documented **deferred item #4** flake (a 0.3 s real-socket race, attribution already
measured across three worktrees and found not to be caused by any of these plans). Re-run
alone **3/3 pass**, and it did **not** fire in either of the two subsequent full-suite runs
(1491 passed / 0 failed both times). Nothing was touched.

Nothing weakened, nothing skipped, no `--no-verify`.

## Self-Check: PASSED

Every created file verified present on disk and every commit hash verified in `git log`.
