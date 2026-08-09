---
phase: 06-security-and-cryptography
plan: "06"
subsystem: network
tags: [gap-closure, peer-fault, toolerror, sender-validation, rule-36]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography plan 05
    provides: "the turn-binding fix; the durable-verdict pathway this plan's peer-fault path reuses"
provides:
  - "Peer-fault containment: a ToolError from the opponent ends the game through the existing technical-loss pathway instead of killing the process before FINAL_REVEAL (rule 36 exposure closed)"
  - "TechnicalWinReason.PEER_PROTOCOL_ERROR + verdict.peer_protocol_verdict (measured evidence builder)"
  - "Sender validation on every game-message handler, with the handshake deliberately exempt"
  - "orchestrator.opponent_role -- the single definition of the expected inbound sender"
affects: [phase-7-reporting-shell, phase-8-league]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Catch a deliberately-unretryable exception where the GAME can end cleanly, not where it is raised. deadline.py's `except ToolError: raise` contract is correct; the defect was that no layer above it converted the exception into an outcome."
    - "An optional security check threads from the ONE place that knows the answer (agent_lifecycle knows cfg.role) and defaults to off, so it cannot disturb any existing caller or test while still being live in real play."
    - "Order matters when two fixes interact: sender rejection raises ToolError AT the peer, which before the peer-fault fix would have crashed a peer running this same codebase. Both landed in one plan, containment first."

key-files:
  created:
    - tests/unit/test_peer_protocol_error.py
    - tests/unit/test_sender_validation.py
  modified:
    - src/pursuit/network/verdict.py
    - src/pursuit/network/orchestrator.py
    - src/pursuit/network/agent_entrypoint.py
    - src/pursuit/network/tools.py
    - src/pursuit/network/peer_runtime.py
    - src/pursuit/network/agent_lifecycle.py
    - docs/PRD_commit_reveal.md
    - .planning/phases/06-security-and-cryptography/deferred-items.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "deadline.py NOT modified. Its `except ToolError: raise` is deliberate and right -- an application-level rejection is not a transport failure and must never be retried. Converting it there would have masked real peer bugs behind a retry ladder; the fix belongs where the game can end on its terminal path."
  - "PEER_PROTOCOL_ERROR is a NEW reason rather than reusing OPPONENT_UNRESPONSIVE. A peer that rejects promptly is not unresponsive, and a technical-win declaration that said so would be a false statement about measured evidence (rules 16/22)."
  - "The handshake tool is EXEMPT from sender validation, with its own test. The peer's role is precisely what the handshake negotiates; checking it in the tool would reject the message that establishes the fact. Making the exemption explicit and tested keeps it a decision rather than an oversight."
  - "expected_sender defaults to None (no check) at every layer. Only agent_lifecycle -- the one place that knows cfg.role for a real match -- supplies it, so the ~1200 existing tests and every fake-driven harness are byte-unaffected while live play is protected."

patterns-established:
  - "orchestrator.opponent_role joins engine_agent as the second and last resident of the police/thief vocabulary. Any future need for the opponent's role name imports it rather than writing the literals again."

# Metrics
duration: ~40min
completed: 2026-08-09
---

# Phase 6 Plan 6: Peer-fault containment and sender validation

**A hostile or merely buggy opponent can no longer kill this agent mid-game before it publishes
its nonces, and can no longer impersonate us on the wire.**

Closes `deferred-items.md` items 3 and 4 — both found by the 06-05 adversarial audit, both
verified by hand before being logged, and neither a §10.4 gate criterion.

## Item 3 was a rule-36 exposure, not just a crash

`deadline.py` re-raises `ToolError` on purpose. That is correct. The defect was that **nothing
above it caught the exception**, so the process died by traceback at the worst possible moment:
`{state, move, intent, nonce}` already in our ledger, no FINAL_REVEAL sent. *We* became the
side that published no nonces — because of one line in their code. And since `tools.py:71`
raises `ToolError` at the peer for a malformed envelope, two honest copies of this codebase
would have killed each other on the first envelope either one rejected.

`run_turn_loop` and the Final-Reveal audit boundary now catch it and route it into the existing
technical-loss pathway, so the game ends on its terminal path — which writes `game_over` and
still runs the audit that publishes our ledger.

**The premise is proven, not assumed.** `test_a_hostile_tool_body_really_does_escape_the_retry_ladder`
drives a real FastMCP round trip against a server whose tool body raises, and asserts the
`ToolError` genuinely escapes `call_with_retry`.

## Item 4 closes the field every audit lens missed

All five lenses of the 06-05 audit chased `turn`; none read `sender`. `_accept` took it off the
wire and enqueued it, and `turn_actions` feeds it into `engine_agent()` and `record_action()` —
so a peer stamping *our* role lands in our own half of the turn buffer, where `maybe_resolve`
can never fire. A silent stall, not a rejected message.

Every game-message handler now rejects a non-opponent sender exactly the way it rejects a
malformed envelope. The handshake is deliberately exempt, with a test saying so.

## Task Commits

1. **Task 1: contain a peer ToolError** — `877f617` (feat)
2. **Task 2: reject a spoofed sender** — `78ebb8c` (feat)
3. **Task 3: docs + graph** — this commit (docs)

Plan itself: `2ac81af`.

## The measurement item 4 required

The plan made keeping the sender check conditional on honest play never tripping it — a false
rejection would be a rules-16/22 hazard. Measured with the check **live** on every real
two-peer integration test:

- Full suite: **1251 passed, 0 failed** (the known `test_belief_policy` timing flake did not
  even fire this run). Coverage 99.29%.
- `uv run python scripts/measure_gate6.py`: exit 0, **all three §10.4 criteria PASS**.

The check stays.

## Deviations from Plan

None. Both tasks landed as specified, no file exceeded the 150-line gate, and no split was
required.

## Verification

- `ruff check .` → 0 violations; `check_line_limit.sh` → exit 0; `check_no_llm_in_strategy.py`
  → OK.
- No wire-format change: no envelope key added, removed, or reshaped. An opponent team's own
  implementation still interoperates, provided it stamps its own role as `sender` — which the
  protocol already required.
- No invented numeric value; this plan adds no threshold, timeout, or tunable.

## Issues Encountered

None. One test needed the real `TurnStateMachine(reporter, initial=...)` signature and a
`sys.modules` fake (because `run_turn_loop` resolves the turn halves by deferred import) —
mechanical, not a design problem.

## Next Phase Readiness

- `deferred-items.md` items 1-4: items 3 and 4 are now **CLOSED**. Items 1 and 2 remain open by
  design — item 1 (FINAL_REVEAL not logged as its own envelope record) is a logging-granularity
  gap with equivalent evidence already available via `audit_verdict`; item 2 (measurement runs
  advance the real games-played counter) is correct rule-37 behaviour, flagged only so a reader
  is not surprised.
- Phase 6 is closed on all fronts its own gate and its two follow-up audits identified.

---
*Phase: 06-security-and-cryptography*
*Completed: 2026-08-09*
