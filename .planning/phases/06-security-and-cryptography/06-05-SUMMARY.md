---
phase: 06-security-and-cryptography
plan: "05"
subsystem: security
tags: [gap-closure, audit, turn-binding, d67, rule-36, outcome-durability]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography plan 02
    provides: "turn_commit.py's D-58 exchange, log_received, the wire log this audit reads"
  - phase: 06-security-and-cryptography plan 03
    provides: "audit.py's three ordered checks + the rule-36 coverage check, agent_audit_* wiring"
provides:
  - "The mutual audit's evidence dicts keyed on LOCAL turn truth (Gap 1, blocker) -- turn-skew can no longer disable the D-67 check or empty the rule-36 coverage intersection"
  - "A caught mismatch is durable (Gap 2, major): a corrected game_over record + a non-zero process exit code"
  - "src/pursuit/network/turn_commit_ledger.py + agent_audit_verdict.py: two 150-line-gate splits, one of which removes a real duplicated definition"
  - "tests/unit/test_audit_turn_binding.py: the adversarial sibling of test_audit_coverage.py -- the first tests in this repo whose two observed dicts deliberately disagree"
affects: [phase-7-reporting-shell]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Enforcement checks must own their join keys: any index, key, or lookup field an adversary supplies makes the check advisory. This is the THIRD instance of the same failure mode in Phase 6 (dead verify_declaration -> vacuous all_matched([]) -> attacker-controlled turn key), and this one defeated the fix for the second."
    - "A cross-check test must make its two sides DISAGREE. test_audit_coverage.py built both observed dicts from one honest fixture, so its keys always agreed -- which is exactly why 1227 green tests and a PASS gate coexisted with a live bypass."
    - "Prove a regression test is non-vacuous with a throwaway probe: revert the fix, confirm the test fails, restore. Done here -- 4 of 5 unit cases fail against the pre-fix code, and the 5th is the honest-peer fairness control that SHOULD be insensitive."
    - "Prefer removing the adversary from an input over adding a check on the adversary's input -- the latter is what created the false-accusation risk this plan explicitly declined (rules 16/22, mirroring 06-03's Step-0 digest-equality trap)."

key-files:
  created:
    - src/pursuit/network/turn_commit_ledger.py
    - src/pursuit/network/agent_audit_verdict.py
    - tests/unit/test_audit_turn_binding.py
    - tests/unit/test_outcome_durability.py
  modified:
    - src/pursuit/network/turn_commit_send.py
    - src/pursuit/network/turn_commit_wait.py
    - src/pursuit/network/turn_commit.py
    - src/pursuit/network/turn_actions.py
    - src/pursuit/network/agent_audit_exchange.py
    - src/pursuit/network/agent_audit_wiring.py
    - src/pursuit/main.py
    - tests/integration/test_step0_and_audit_tamper.py
    - docs/PRD_commit_reveal.md
    - docs/phases/phase-6/GATE-6-MEASUREMENT.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "Keyed the audit on local turn truth rather than validating the peer's declared turn. Both close the exploit; only the first cannot produce a FALSE accusation. Rejecting on a turn-stamp disagreement assumes no legitimate skew exists anywhere in the protocol -- exactly the assumption that made 06-03's literal Step-0 digest-equality check wrong. The in-game rejection was therefore considered and deliberately NOT added, and the reasoning is recorded in docs/PRD_commit_reveal.md §2.6.1 rather than left implicit."
  - "src/pursuit/security/audit.py was NOT touched. Its three ordered checks, the trailing-commit exemption, and the coverage check are all correct -- they were being fed attacker-controlled keys. Changing correct logic to compensate for a problem one layer below it would have weakened the function and hidden the real defect."
  - "The pre-audit game_over record is left in place rather than rewritten. The log is append-only evidence and the board result is a real fact about the game; the corrected record is appended after it, and the LAST game_over is the audited one."
  - "turn_actions.py's inline technical-win block was a byte-for-byte copy of turn_commit_send.technical_loss. Replaced with the call (no-duplication rule) rather than shaving lines elsewhere to satisfy the 150-line gate -- the gate says split or de-duplicate, never compress."

patterns-established:
  - "ledger_path has ONE definition (turn_commit_ledger.py). It previously existed as two private copies, in the ledger's writer and in its reader -- the two places that must never disagree about where a game's nonces live."

# Metrics
duration: ~55min
completed: 2026-08-09
---

# Phase 6 Plan 5: Gap closure — audit turn-binding + verdict durability

**The mutual audit no longer trusts the opponent's own turn numbers, so a forged or withheld
reveal can no longer be hidden behind a relabelled integer; and a caught mismatch now survives
in the log and in the exit code instead of evaporating.**

## What was wrong

Found by a 5-lens adversarial audit run during `/gsd:verify-work 6`. All five lenses converged
independently on Gap 1; all five skeptics failed to refute it; both gaps were then reproduced
by hand against the shipped functions with paired controls before any code was written.

**Gap 1 (blocker).** `agent_audit_exchange.observed()` built both `observed_commits` and
`observed_reveals` keyed on `envelope.get(TURN)` — the peer's own declared turn, taken verbatim
off the wire. Nothing in `src/` ever compared an inbound envelope's turn to `ctx.state.turn`.
A peer stamping its COMMIT and REVEAL envelopes with disjoint turns therefore:

- emptied `set(observed_commits) & set(observed_reveals)`, so the rule-36 coverage check yielded
  nothing and `{"records": []}` passed again — **the exact evasion 06-03's own follow-up existed
  to close**; and
- sent every claimed entry down the `turn not in observed_reveals` trailing-commit exemption,
  which returns `matched=True`, so the D-67 revealed-vs-played check never ran.

Cheapest variant: stamp every envelope `turn=0`. Both dicts collapse to one key, one valid
record satisfies an N-turn game's audit, and N−1 nonces stay secret forever.

**Gap 2 (major).** `game_over` — the only event carrying an `outcome` field — is written inside
`run_turn_loop`, *before* the audit runs, and was never corrected. `main.py` then discarded
`run_agent`'s overridden outcome and returned 0. A caught cheat left a log whose outcome still
read as the cheater's win, and a zero exit code.

## What changed

- `log_received` takes a required `local_turn` and stamps the record with it. The nested
  envelope is stored **unchanged**, so the peer's claimed turn survives as evidence — the fix
  removes the adversary from the join key without discarding what the adversary said.
- `wait_for_opponent_commit` takes the responder's pre-resolve turn, captured in
  `await_and_respond` before it decides anything.
- `await_opponent_turn` captures `ctx.state.turn` **before** `record_action`/`maybe_resolve`,
  which advances it — the same hazard 06-02 flagged for `reveal_pending`.
- `observed()` keys both dicts on the record's own top-level turn.
- `record_audit_verdict` appends a corrected `game_over` on a mismatch; `main.py` maps
  `TECHNICAL_LOSS` to a non-zero exit code and stays a thin shell.

This also fails closed in the other direction for free: a peer publishing its FINAL_REVEAL
records under skewed turn numbers finds them absent from `observed_commits` (check 1 fails)
while the real turns go unreported (the coverage check names them).

## Task Commits

1. **Task 1: bind the audit's join key to local turn truth** — `4012a18` (feat)
2. **Task 2: prove it with disagreeing observed dicts** — `e5ec5b5` (test)
3. **Task 3: make a caught mismatch durable** — `eecd4be` (feat)
4. **Task 4: PRD + gate report + graph** — `65db6d9` (docs)

Plan itself: `621f254`.

## Proof that the new tests are not vacuous

Reverting `observed()` to the pre-fix key fails **4 of the 5** new unit cases. The one that
still passes is `test_an_honest_peer_is_still_matched` — the fairness control, which is exactly
the case that should be insensitive to the fix. Probe run, confirmed, reverted.

## Deviations from Plan

**1. [Rule 3 - Blocking] Two 150-line splits, both pre-authorized in spirit by the plan's gate**

- `turn_commit_wait.py` hit 156 → `turn_commit_ledger.py` (new) takes `build_action_payload` /
  `commit_own_action` / `ledger_path`. Bonus, and the reason this split is better than a
  mechanical one: `ledger_path` had been **duplicated** in `agent_audit_wiring.py`. Both now
  import the single definition, so the ledger's writer and its reader can no longer drift on
  where a game's nonces live.
- `agent_audit_exchange.py` hit 159 after the Gap-2 fix → `agent_audit_verdict.py` (new) takes
  the verdict-recording half, along the seam that file's own docstring already named. Both
  public names re-exported, so `agent_audit_wiring` is unaffected.

**2. [Rule 1 - No duplication] `turn_actions.py`'s inline technical-win block**

It was a byte-for-byte copy of `turn_commit_send.technical_loss` (same record, same GAME_OVER
attempt, same return). Replaced with the call. This was the honest way to get the file back
under 150 after adding one line — the rule is split or de-duplicate, never compress.

**3. [Declined, deliberately] The in-game turn-stamp rejection**

The plan listed it as an optional second layer that had to earn its place. It did not: keying
on local truth already closes both exploit paths, and rejecting a disagreeing stamp assumes no
legitimate skew exists anywhere in the protocol — the assumption that made 06-03's literal
Step-0 digest-equality check wrong, and a rules-16/22 false-accusation hazard. Recorded in
`docs/PRD_commit_reveal.md` §2.6.1 so the choice is visible rather than an omission.

## Verification

- Full suite: **1238 passed**, coverage **99.38%** (was 1226 / 99.33% before this plan; +12
  tests). The one failure across runs is the known load-sensitive
  `test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`,
  re-confirmed passing in isolation at 0.18s — unrelated, matching the pre-existing baseline.
- `ruff check .` → 0 violations. `scripts/check_line_limit.sh` → exit 0.
  `scripts/check_no_llm_in_strategy.py` → OK.
- **GATE-6 re-measured after the fix: all three §10.4 criteria still PASS**, exit 0, zero env
  vars.
- `test_toggle_off_is_byte_equivalent_to_pre_phase_6` passes unchanged — the toggle-off path is
  untouched.
- No wire-format change: COMMIT/ACK/REVEAL/FINAL_REVEAL payloads, the composite
  `{move, barrier}` dict, and the handshake payload are all byte-identical, so an opponent
  team's implementation still interoperates.
- No invented numeric value. The one new constant, `main.EXIT_TECHNICAL_LOSS = 1`, is a
  conventional process exit status and is labelled structural.

## Issues Encountered

None beyond the two forced splits. The fix was narrower than the finding: one join key, one
extra record, one exit code.

## Next Phase Readiness

- Both `06-UAT.md` gaps are closed and proven closed. Phase 6 is ready to be marked verified.
- The completeness critic from the same adversarial audit raised two further items **outside
  this plan's scope**, logged in `deferred-items.md` rather than silently fixed: an uncaught
  `ToolError` can escape `call_with_retry` mid-game, and `tools.py::_accept` never checks that
  `envelope.sender` is the opponent's role. Neither is a Phase-6 gate criterion; both are real
  and should be picked up before league play.

---
*Phase: 06-security-and-cryptography*
*Completed: 2026-08-09*
