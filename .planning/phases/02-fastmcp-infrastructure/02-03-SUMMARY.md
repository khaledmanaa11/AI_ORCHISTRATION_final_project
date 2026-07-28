---
phase: 02-fastmcp-infrastructure
plan: "03"
subsystem: infra
tags: [state-machine, enum, transitions, severity, reporter-protocol, tdd]

# Dependency graph
requires:
  - phase: 02-fastmcp-infrastructure (02-00)
    provides: "src/pursuit/network/__init__.py package, tests/unit/test_state_machine.py stub file"
provides:
  - "src/pursuit/network/state_machine.py — State enum (D-09), ALLOWED_TRANSITIONS dict (D-12), TERMINAL_STATES, TransitionSeverity, RECOVERABLE_ATTEMPTS, TransitionReporter Protocol, TransitionResult, classify_severity(), transition(), TurnStateMachine (NET-04, NET-05)"
affects: [02-08, 02-09, 02-10, phase-6-commit-reveal]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Injected-reporter Protocol instead of an imported logging module — keeps state_machine.py free of any dependency on 02-04's event-log module, enabling same-wave parallel execution and trivial fake-reporter testing"
    - "Single reporter call site inside transition(), executed before the outcome branch — guarantees NET-05's 'never silent' property structurally rather than by convention"
    - "Severity classified by a second explicit table (RECOVERABLE_ATTEMPTS) rather than a caller-supplied flag or an if/elif chain, consistent with D-12's table-driven spirit"
    - "TransitionResult.continues derives from TERMINAL_STATES membership, not a repeated pair of equality checks (QUAL-02)"

key-files:
  created:
    - src/pursuit/network/state_machine.py
  modified:
    - tests/unit/test_state_machine.py
    - docs/phases/phase-2/TODO.md

key-decisions:
  - "D-09/D-12 implemented verbatim per the plan's <interfaces> contract: six State members, ALLOWED_TRANSITIONS as dict[State, frozenset[State]] with every member as a key, GAME_OVER/ERROR terminal (empty frozenset)"
  - "D-10 RECOVERABLE_ATTEMPTS is exactly the six pairs from the plan's design_notes item 3: four self-transition duplicates (HANDSHAKE, MY_TURN, WAIT_OPPONENT, GAME_OVER) plus two late-handshake pairs ((MY_TURN, HANDSHAKE), (WAIT_OPPONENT, HANDSHAKE)); every other illegal pair — including anything out of ERROR and any backwards jump to INIT — is PROTOCOL_VIOLATION"
  - "Reworded two docstring passages (module docstring, TransitionReporter docstring) to avoid the literal substring 'event_log' while still stating that this module has no dependency on 02-04's reporting/audit-trail module — same tension as 02-02's HINT/COMMIT docstring-vs-grep issue, resolved the same way (meaning preserved, literal substring avoided)"
  - "Task 3 (REFACTOR) required zero code changes: Task 2's implementation already satisfied every REFACTOR-gate audit (100% coverage, 0 ruff violations, line limit passed, zero numeric literals, no FSM dependency, single reporter call site, table-driven lookup) on first pass — no second commit was created since there was nothing to change (TDD rule: commit only if changes)"

patterns-established:
  - "Pattern: when a module's own docstring needs to reference a not-yet-built sibling module by a name a later verification grep checks for zero occurrences of, describe the sibling by role ('02-04's reporting/audit-trail module') rather than by its literal future module name"

# Metrics
duration: ~12min (this session; Task 1 RED was completed and committed in a prior interrupted session)
completed: 2026-07-28
---

# Phase 2 Plan 03: Turn State Machine + Illegal-Transition Reporting Summary

**A six-state D-09 turn state machine driven entirely by an explicit `ALLOWED_TRANSITIONS` table (D-12, no FSM library), where `transition()` reports every illegal attempt to an injected reporter before classifying it as RECOVERABLE (game continues) or PROTOCOL_VIOLATION (escalates to `ERROR`) per D-10/NET-05.**

## Performance

- **Duration:** ~12 min this session (GREEN + REFACTOR verification); Task 1 RED was already committed from a prior interrupted session and verified still valid before continuing
- **Completed:** 2026-07-28
- **Tasks:** 3/3 completed (RED already done and verified / GREEN implemented and committed this session / REFACTOR ran as pure verification, zero code changes needed)
- **Files modified:** 2 (1 created: `state_machine.py`; 1 pre-existing from prior session: `test_state_machine.py`), plus `docs/phases/phase-2/TODO.md` status update

## Accomplishments

- `src/pursuit/network/state_machine.py` — `State` enum (six D-09 members: `INIT`, `HANDSHAKE`, `MY_TURN`, `WAIT_OPPONENT`, `GAME_OVER`, `ERROR`), `ALLOWED_TRANSITIONS` explicit `dict[State, frozenset[State]]` keyed by every member, `TERMINAL_STATES = {GAME_OVER, ERROR}`, `TransitionSeverity` enum (`RECOVERABLE`/`PROTOCOL_VIOLATION`), `RECOVERABLE_ATTEMPTS` frozenset of six illegal-but-benign `(current, target)` pairs, `TransitionReporter` Protocol (keyword-only `current`/`target`/`severity`/`reason`), frozen `TransitionResult` dataclass with a `continues` property, `classify_severity()`, `transition(current, target, *, reporter)`, and `TurnStateMachine` (per-instance state only, `attempt()` method).
- The NET-05 gate (`test_illegal_transition_is_rejected_and_reported`) and the D-10 severity-path tests (`test_recoverable_attempt_keeps_machine_usable`, `test_protocol_violation_escalates_to_error`) all pass, along with the D-09 round-trip test, the NET-02 isolation test, and the structural no-`event_log`-import guard — all 10 tests in `test_state_machine.py`.
- `transition()` calls the injected `reporter` from a single call site, before the outcome branch is computed — every illegal attempt (RECOVERABLE or PROTOCOL_VIOLATION) is reported exactly once; a legal transition never calls the reporter.
- Zero numeric literals (AST-verified, bool-excluding scan: `numeric literals: []`). No import of `pursuit.network.event_log`, `logging`, `print`, or `open`. No FSM library added to `pyproject.toml` (`transitions|statemachine|automat` grep clean).
- Coverage of `pursuit.network.state_machine`: **100%** (57/57 statements), all branches of `transition()`, `classify_severity()`, `TransitionResult.continues`, and `TurnStateMachine.attempt()` exercised. Full unit suite: **95 passed, 34 skipped**, zero Phase-1/Phase-2 regressions. `ruff check .` and `bash scripts/check_line_limit.sh` both exit 0 repo-wide.

## Final ALLOWED_TRANSITIONS Table (for 02-08/02-09)

```python
ALLOWED_TRANSITIONS = {
    State.INIT:          frozenset({State.HANDSHAKE, State.ERROR}),
    State.HANDSHAKE:      frozenset({State.MY_TURN, State.WAIT_OPPONENT, State.ERROR}),
    State.MY_TURN:        frozenset({State.WAIT_OPPONENT, State.GAME_OVER, State.ERROR}),
    State.WAIT_OPPONENT:  frozenset({State.MY_TURN, State.GAME_OVER, State.ERROR}),
    State.GAME_OVER:      frozenset(),
    State.ERROR:          frozenset(),
}
```

## Final RECOVERABLE_ATTEMPTS (for 02-08/02-09)

```python
RECOVERABLE_ATTEMPTS = frozenset({
    (State.HANDSHAKE, State.HANDSHAKE),        # duplicate handshake re-delivery
    (State.MY_TURN, State.MY_TURN),            # duplicate move message
    (State.WAIT_OPPONENT, State.WAIT_OPPONENT),# duplicate wait/ack message
    (State.GAME_OVER, State.GAME_OVER),        # duplicate game-over message
    (State.MY_TURN, State.HANDSHAKE),          # late handshake after we advanced
    (State.WAIT_OPPONENT, State.HANDSHAKE),    # late handshake after we advanced
})
```

Every illegal pair not in this set — including any attempt out of `ERROR`, and any
backwards jump to `INIT` from any other state — is `TransitionSeverity.PROTOCOL_VIOLATION`
and escalates the machine to `State.ERROR`.

## TransitionReporter Signature (for 02-04's event log)

```python
class TransitionReporter(Protocol):
    def __call__(
        self, *, current: State, target: State,
        severity: TransitionSeverity, reason: str,
    ) -> None: ...
```

02-04's event-log adapter must expose a callable matching this exact keyword-only shape;
02-09 wires the two together when constructing `TurnStateMachine(reporter, initial=...)`.

## Conditional Split

**Not needed.** `state_machine.py` landed at 181 raw lines / under the 150 code-line limit
(check_line_limit.sh excludes blanks and comment lines and passed with no violation).
`test_state_machine.py` similarly passed under the limit. No `transition_policy.py` or
`test_transition_severity.py` was created — all public names remain importable from
`pursuit.network.state_machine` as the single module path, per the plan's interface note.

## Task Commits

1. **Task 1 RED: Fill test_state_machine.py with failing NET-04/NET-05 assertions** — `6d04e81` (test) — completed and committed in a prior interrupted session; verified this session to still produce the RED gate (`ModuleNotFoundError: No module named 'pursuit.network.state_machine'`) and to contain all ten required tests with zero `pytest.skip` bodies before continuing.
2. **Task 2 GREEN: Implement state_machine.py** — `be453cc` (feat)
3. **Task 3 REFACTOR: severity paths, coverage, full-suite audit** — no additional commit; Task 2's implementation already passed every REFACTOR-gate check (100% coverage, 0 ruff violations, line limit clean, zero numeric literals, no FSM library, single reporter call site) on the first pass, so there was no behavior-preserving change to make or commit (TDD rule: commit only if changes).

**Plan metadata:** committed alongside this SUMMARY (see final commit below)

## Files Created/Modified

- `src/pursuit/network/state_machine.py` — `State`, `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `TransitionSeverity`, `RECOVERABLE_ATTEMPTS`, `TransitionReporter`, `TransitionResult`, `classify_severity`, `transition`, `TurnStateMachine` (NET-04, NET-05, D-09, D-10, D-12)
- `tests/unit/test_state_machine.py` — 10 real tests replacing the 02-00 skip stub (already present from the prior session's RED commit; re-verified, unchanged this session)
- `docs/phases/phase-2/TODO.md` — row `2-03` marked done (☑)

## Decisions Made

- Implemented the `<interfaces>` block verbatim — no deviation from the six-state enum, the
  two-table design, or the `TurnStateMachine.attempt()` shape, since the plan explicitly marks
  this surface as consumed verbatim by 02-08/02-09/02-10.
- Reworded the module docstring and the `TransitionReporter` docstring to avoid the literal
  substring `event_log` (which the plan's own `test_state_machine_module_does_not_import_event_log`
  structural guard greps for) while still documenting the design rationale — this module has no
  dependency on 02-04's reporting module — in prose. This is the same category of tension 02-02
  hit with its `HINT`/`COMMIT` docstring-vs-grep conflict, resolved the same way: preserve meaning,
  avoid the exact literal substring the automated check scans for.
- No `## OPEN` items — no numeric value was ever needed anywhere in this module; the AST scan
  confirms `numeric literals: []`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, documentation only] Module docstring literally contained "event_log", tripping the module's own structural guard test**
- **Found during:** Task 2 (GREEN), first test run after writing `state_machine.py`
- **Issue:** The initial module docstring and `TransitionReporter` docstring explained the
  injected-reporter design by naming `pursuit.network.event_log` directly, which caused
  `test_state_machine_module_does_not_import_event_log` to fail — that test asserts the literal
  substring `"event_log"` is absent from the source file (a structural guard against import
  coupling with 02-04, not literally an import statement scan).
- **Fix:** Reworded both docstring passages to describe the sibling module by role ("02-04's
  reporting/audit-trail module") instead of by its literal future module name, preserving the
  exact design rationale required by the plan's behavior block without the substring the test
  scans for.
- **Files modified:** src/pursuit/network/state_machine.py
- **Verification:** All 10 tests pass, including the structural guard; `grep -c event_log` on
  the file returns 0.
- **Committed in:** be453cc (Task 2 commit — fixed before the commit was made, not a follow-up)

---

**Total deviations:** 1 auto-fixed (documentation-only rewording, discovered and fixed before the Task 2 commit)
**Impact on plan:** No scope creep, no behavior change to any function or table. The fix was a
wording adjustment resolving the same category of plan-internal tension already seen and
resolved in 02-02 (instructive prose content vs. a literal-substring smoke test).

## Issues Encountered

- Confirmed the note in the execution brief was accurate: `6d04e81` ("test(02-03): add failing
  tests for turn state machine (NET-04/NET-05)") already existed from a prior interrupted
  session. Verified it against the plan's Task 1 behavior block (all ten named tests present,
  `FakeReporter` double present, zero `pytest.skip` remaining, `ruff check` clean, RED gate
  reproduces `ModuleNotFoundError`) before treating it as done and starting from Task 2 — no
  duplicate RED commit was created.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `State`, `ALLOWED_TRANSITIONS`, `TransitionSeverity`, `TransitionResult`, `TransitionReporter`,
  `transition()`, and `TurnStateMachine` are ready for 02-08's handshake (`INIT -> HANDSHAKE`
  through `transition()`, with reachability failures routed through the same severity path) and
  02-09's orchestrator (owns one `TurnStateMachine` per process, wires an event-log-backed
  reporter matching the `TransitionReporter` Protocol into its constructor).
- 02-04's event log has an exact, pinned keyword signature to adapt to
  (`__call__(self, *, current, target, severity, reason) -> None`) — no coordination needed
  beyond matching that shape.
- 02-10's gate tests can assert illegal-attempt reporting and severity classification directly
  against this module's public surface; no reshaping expected.
- No blockers carried into the rest of Wave 1 — this plan touched only
  `src/pursuit/network/state_machine.py` (new) and confirmed `tests/unit/test_state_machine.py`
  (already present), neither of which overlaps 02-01's `shared/*`, 02-02's `envelope.py` /
  `config_hash.py`, 02-04's `event_log.py` / `watchdog.py`, or 02-05's
  `docs/PRD_mcp_transport.md`.
- `uv run pytest tests/unit/ -x -q` baseline after this plan: **95 passed, 34 skipped**, 0
  collection errors, 0 regressions. Coverage of `pursuit.network.state_machine`: 100%.

---
*Phase: 02-fastmcp-infrastructure*
*Completed: 2026-07-28*

## Self-Check: PASSED

All claimed files verified present on disk (src/pursuit/network/state_machine.py,
tests/unit/test_state_machine.py, .planning/phases/02-fastmcp-infrastructure/02-03-SUMMARY.md).
Both task commit hashes (6d04e81, be453cc) verified present in `git log --oneline --all`.
