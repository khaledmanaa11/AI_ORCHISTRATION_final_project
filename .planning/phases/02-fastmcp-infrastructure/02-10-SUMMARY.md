---
phase: 02-fastmcp-infrastructure
plan: "10"
subsystem: network
tags: [integration-tests, phase-gate, fastmcp, coverage-audit, net-01..09, tdd]

# Dependency graph
requires:
  - phase: 02-fastmcp-infrastructure (02-00 .. 02-09)
    provides: "NetworkParams/GameParams loaders, Envelope/MessageType, TurnStateMachine, event_log/watchdog, PeerRuntime/tools, deadline tracker + retry ladder, handshake perform/respond, turn orchestrator + agent lifecycle wiring, thin main.py"
provides:
  - "tests/integration/conftest.py -- integration-only shared fixtures (police_params, thief_params, peer_pair, client_for, agent_log_paths, read_events, recording_sleep, stepping_clock)"
  - "tests/integration/test_peer_roundtrip.py -- GATE-1 (§10.4 criterion 1)"
  - "tests/integration/test_turn_isolation.py -- GATE-2 (§10.4 criterion 2)"
  - "tests/integration/test_turn_lifecycle.py -- GATE-3 core (§10.4 criterion 3: full lifecycle, illegal-transition reporting)"
  - "tests/integration/test_turn_resilience.py -- GATE-3 resilience half (technical win, watchdog incident)"
  - "A closed NET-01..NET-09 requirement-coverage audit"
  - "A real, verified two-process standalone launch over localhost (D-02)"
  - "A production bug fix in turn_actions.py that makes multi-turn real games possible at all"
affects: [phase-3-strategy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase gate criterion -> named pytest node ID mapping (Phase-1 precedent from test_game_loop.py), now applied to the harder-to-fake NET-02/NET-05/NET-06/NET-07 criteria"
    - "In-memory two-peer wiring for a full lifecycle test: build two real default_context() AgentContexts, monkeypatch ONE side's runtime.client to target the other's real FastMCP server object (Client(other.runtime.server)) instead of the URL-based client -- proves the real tool surface end-to-end with zero socket"
    - "Ordered-subsequence assertion for a state path read back from JSONL (`all(x in iter(haystack) for x in needle)`) -- tolerates the legitimate MY_TURN<->WAIT_OPPONENT repeat without pinning an exact turn count"

key-files:
  created:
    - tests/integration/conftest.py
    - tests/integration/test_turn_isolation.py
    - tests/integration/test_turn_resilience.py
  modified:
    - tests/integration/test_peer_roundtrip.py
    - tests/integration/test_turn_lifecycle.py
    - src/pursuit/network/turn_actions.py
    - src/pursuit/main.py
    - tests/unit/test_orchestrator_loop.py
    - docs/phases/phase-2/TODO.md

key-decisions:
  - "A genuine production bug was found and fixed while building the GATE-3 full-lifecycle test, not invented by the test: turn_actions.py's await_opponent_turn called Envelope.from_dict on an already-decoded Envelope (tools.py's _accept always enqueues a real Envelope, never a dict), and take_my_turn unconditionally re-attempted the MY_TURN transition even when the machine was already there -- which await_opponent_turn's own prior call legitimately puts it in every single cycle after the first. Together these meant run_turn_loop could complete AT MOST one exchange before silently declaring a FALSE technical win (rules 16/22), and NO existing 02-09 unit test ever drove two full cycles or a genuinely-decoded queue item to catch it. Both are fixed in turn_actions.py; see the Deviations section for full detail and the empirical probe that found each one."
  - "test_illegal_transition_is_reported_and_handled_by_severity's RECOVERABLE half was removed and replaced, not just left broken: after the take_my_turn fix, a call with the machine already at MY_TURN is the NORMAL continuation of a real game, not a rejectable duplicate, so no state reachable through take_my_turn produces RECOVERABLE severity anymore. A new regression test asserts the corrected behavior directly; RECOVERABLE coverage for NET-05 was never uniquely provided by that sub-test anyway -- test_state_machine.py::test_recoverable_attempt_keeps_machine_usable already covers it at the state-machine level (QUAL-02)."
  - "test_turn_lifecycle.py's own line count (162) still exceeded 150 after the first split into {test_turn_lifecycle.py, test_turn_resilience.py}; split again into test_turn_isolation.py for the two GATE-2 tests, exactly the contingency plan 02-10 named in advance -- three gate modules instead of two, never a compressed one."
  - "The full-lifecycle gate test terminates the game via a real SDK CAPTURE outcome (a scripted second cop move onto the thief's actual position), not by delivering a synthetic game_over message: run_turn_loop has no code path that reacts to a MessageType.GAME_OVER envelope at all (confirmed by reading turn_actions.py), so inventing one would test something the shipped orchestrator does not do. This is the plan's own explicitly pre-authorized fallback."
  - "GATE-1's queue assertion decodes the queued item as an Envelope directly rather than via Envelope.from_dict, matching 02-06's actual design (tools.py's _accept always enqueues a real Envelope instance) -- confirmed by reading peer_runtime.py/tools.py before writing any assertion, per the plan's interface_binding_protocol."

patterns-established:
  - "When a plan discovers a bug in a PRIOR completed phase's shipped code while exercising it more realistically (e.g. two real peers instead of one fake), fix the bug in place, update only the unit tests whose assertions encoded the now-corrected behavior, and add a regression test naming the fix -- document the empirical probe that proved it, not just the final diff."

# Metrics
duration: ~110min
completed: 2026-07-29
---

# Phase 02 Plan 10: Section-10.4 Phase Gate + NET-01..09 Coverage Audit Summary

**Closes Phase 2's §10.4 milestone gate with eight named, passing integration test nodes across four new/filled modules, closes the NET-01..NET-09 coverage audit, and — while building the GATE-3 full-lifecycle test — found and fixed a real production bug in `turn_actions.py` that silently limited every real game to exactly one turn exchange before a false technical win; a live two-process localhost launch afterward ran a full 35-turn game to a clean SURVIVAL outcome.**

## Performance

- **Duration:** ~110 min
- **Completed:** 2026-07-29
- **Tasks:** 4/4 completed (GATE-1 fixtures+tests, GATE-2/GATE-3 tests + bug fix, coverage audit, real two-process launch)
- **Files modified:** 10 (3 created, 7 modified, across tests/integration, tests/unit, src/pursuit/network, src/pursuit, docs/phases)

## Accomplishments

- `tests/integration/conftest.py` — the once-defined shared fixtures every gate module in this plan uses: `police_params`/`thief_params`/`peer_pair` (real, socket-free `PeerRuntime`s), `client_for` (in-memory `fastmcp.Client`), `agent_log_paths`, `read_events`, `recording_sleep`, `stepping_clock`.
- `tests/integration/test_peer_roundtrip.py` — GATE-1: a `type=move` Envelope sent through the real four-tool surface is decoded intact on the other side (coordinates asserted for int-ness, not bare equality) across every fixture-derived board position.
- `tests/integration/test_turn_isolation.py` — GATE-2: `test_two_runtimes_share_no_runtime_state` asserts NET-02 POSITIVELY (mutate one side's queue/machine/log, prove the other untouched); `test_entry_point_is_config_dir_parameterised` proves `pursuit.main` is driven by `--config-dir` alone.
- `tests/integration/test_turn_lifecycle.py` — GATE-3 core: `test_full_lifecycle_init_to_game_over` drives the REAL `run_turn_loop` for one peer against another peer's real tool surface (in-memory transport) through a genuine `HANDSHAKE -> MY_TURN -> WAIT_OPPONENT -> MY_TURN -> GAME_OVER` path with a real SDK `CAPTURE` outcome, read back from the on-disk JSONL log; `test_illegal_transition_reported_with_severity` asserts BOTH `TransitionSeverity` outcomes from the real wired reporter's JSONL record.
- `tests/integration/test_turn_resilience.py` — GATE-3 resilience: silent-opponent technical win with recorded sleep durations `== [backoff_seconds] * retry_count` (D-17), zero wall-clock elapsed; watchdog incident-before-exit ordering proof via `Watchdog.check_once` with an injected clock, plus the healthy-agent control case.
- **A real production bug found and fixed** in `src/pursuit/network/turn_actions.py` (see Deviations) — without this plan's GATE-3 test, `run_turn_loop` could never complete more than one real exchange between two agents.
- **NET-01..NET-09 coverage audit closed** (see table below) — every requirement maps to at least one named, passing gate node plus its unit coverage.
- **A real two-process standalone launch** (Task 4) completed a full 35-turn game over real localhost HTTP to a clean `SURVIVAL` outcome, with two distinct PIDs, two distinct config roots/ports, and two distinct JSONL logs (see the dedicated section below).
- Full repo suite: 179 passed, 0 skipped, 0 failed. Coverage 96.87% (>= 85% gate). `ruff check .` and `bash scripts/check_line_limit.sh` both exit 0 repo-wide.

## Task Commits

1. **Task 1: GATE-1 integration fixtures + peer round-trip tests** — `9e7e17a` (test)
2. **Task 2a: fix two turn_actions.py bugs found by the GATE-3 lifecycle test** — `b45e767` (fix)
3. **Task 2b: GATE-2/GATE-3 turn lifecycle, isolation, and resilience tests** — `4e31d76` (test)
4. **Task 3: coverage audit** — verification only, no source changed; results recorded below and in this SUMMARY's commit
5. **Task 4: real two-process standalone launch** — no repo file modified (by design); evidence recorded below

## Files Created/Modified

- `tests/integration/conftest.py` — shared integration fixtures (created)
- `tests/integration/test_peer_roundtrip.py` — GATE-1, stub bodies replaced
- `tests/integration/test_turn_isolation.py` — GATE-2 (created, split from test_turn_lifecycle.py)
- `tests/integration/test_turn_lifecycle.py` — GATE-3 core, stub bodies replaced
- `tests/integration/test_turn_resilience.py` — GATE-3 resilience (created, split)
- `src/pursuit/network/turn_actions.py` — the two production bug fixes
- `src/pursuit/main.py` — docstring/help-text reworded (structural-guard compliance, no behavior change)
- `tests/unit/test_orchestrator_loop.py` — updated to match the corrected `take_my_turn` behavior
- `docs/phases/phase-2/TODO.md` — row `2-10` and the phase-gate checklist marked done

## Decisions Made

See `key-decisions` in the frontmatter. In short: a real orchestrator bug (not a test-authoring artifact) was found and fixed, one existing unit test's premise was corrected rather than preserved as-is, and the module split went one level deeper than planned (three integration modules, not two) to hold the 150-line gate.

## NET-01..NET-09 Coverage Audit (Task 3)

| Req | Gate node (this plan) | Unit coverage (elsewhere in Phase 2) | Result |
|-----|----------------------|--------------------------------------|--------|
| NET-01 | `test_turn_isolation.py::test_two_runtimes_share_no_runtime_state`; `::test_entry_point_is_config_dir_parameterised` | `tests/unit/test_network_config.py` | PASS |
| NET-02 | `test_turn_isolation.py::test_two_runtimes_share_no_runtime_state` | `tests/unit/test_peer_runtime.py`; `tests/unit/test_agent_lifecycle.py` | PASS |
| NET-03 | `test_peer_roundtrip.py::test_move_envelope_decoded_by_peer` | `tests/unit/test_peer_runtime.py`; `tests/unit/test_tools.py` | PASS |
| NET-04 | `test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over` | `tests/unit/test_orchestrator.py`; `tests/unit/test_orchestrator_loop.py` | PASS |
| NET-05 | `test_turn_lifecycle.py::test_illegal_transition_reported_with_severity` | `tests/unit/test_state_machine.py`; `tests/unit/test_agent_lifecycle.py` | PASS |
| NET-06 | `test_turn_resilience.py::test_silent_opponent_yields_technical_win` | `tests/unit/test_deadline.py`; `tests/unit/test_deadline_retry.py` | PASS |
| NET-07 | `test_turn_resilience.py::test_freeze_writes_incident_before_exit` | `tests/unit/test_watchdog.py`; `tests/unit/test_watchdog_thread.py` | PASS |
| NET-08 | `test_peer_roundtrip.py::test_coordinates_survive_round_trip` | `tests/unit/test_envelope.py`; `tests/unit/test_tools_dispatch.py` | PASS |
| NET-09 | `test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over` | `tests/unit/test_config_hash.py`; `tests/unit/test_handshake_abort.py` | PASS |

All eight named gate node IDs collect via `pytest --collect-only -q` and all eight pass in one invocation (`8 passed, 0 skipped, 0 failed`). Every unit module cited above exists on disk (verified — no row needed correcting against the plan's own table). Standing quality gates: `uv run pytest tests/ -q` → 179 passed; `uv run pytest --cov=pursuit --cov-report=term-missing` → 96.87% (>= 85%); `uv run ruff check .` → 0 violations; `bash scripts/check_line_limit.sh` → every file passes; no `requirements*.txt` anywhere in the repo.

## §10.4 criterion 2 — real process evidence (Task 4)

Both `--check-config` pre-flights succeeded independently before anything bound a port:
```
role=police  listen=127.0.0.1:8001  opponent_url=http://127.0.0.1:8002/mcp
role=thief   listen=127.0.0.1:8002  opponent_url=http://127.0.0.1:8001/mcp
```

Two independent processes were then started directly (`uv run python -m pursuit.main --config-dir config/police|config/thief`), each pointed at its own config root:

- **Two distinct PIDs**, alive simultaneously: police `14892`, thief `3656` (the `uv run` wrapper PIDs; each spawns its own Python grandchild running the actual FastMCP server + turn loop).
- **Two distinct config roots and ports**, read from each side's own `network.json`, never typed on the command line: police on `8001`, thief on `8002`.
- **The handshake completed over real HTTP** with matching config digests, and every move envelope for a complete game crossed the wire: both sides' JSONL logs show the identical alternating `message_sent`/`message_received` sequence, turn by turn, up to `turn=35`.
- **Two distinct JSONL event logs**, one per agent (`logs/police/<game_uid>.jsonl`, `logs/thief/<game_uid>.jsonl` — both gitignored, neither committed), each recording only its own agent's `sender` field — no shared log file.
- **The game ran to a real, clean terminal outcome on its own**: the police log's final record is `{"event":"game_over","outcome":"survival","turn":35,...}`, matching `game_params.json`'s `survival_threshold` exactly — the SAME production bug fix from Task 2 (turn_actions.py) is what makes this possible; before the fix this real two-process game would have died after one exchange with a false technical win.
- **An authentic, unplanned finding**: both sides' logs also show one `illegal_transition`/`RECOVERABLE` record for a `handshake -> handshake` self-attempt at turn 0 — because each side independently INITIATES an outbound handshake against the other AND answers the other's inbound handshake on the same machine, one of the two attempts on each side is a benign race that the state machine correctly classifies RECOVERABLE (D-10) rather than rejecting the game. No in-memory test in this plan can produce this exact race, since it requires two independently-scheduled real event loops.
- **Process/port cleanup**: after the bounded observation window, `proc.terminate()` was called on both `uv run` wrapper PIDs; by the time of the actual game outcome, both agents had already reached `GAME_OVER` and called `shutdown_cleanly()` on their own. A subsequent `netstat` scan showed no `LISTEN` socket remaining on `8001` or `8002`, and no `pursuit.main` process remained in the process list — confirmed clean, with no orphan.
- **No leak scan**: the captured stdout for both processes (FastMCP banner, uvicorn access logs, one console-echoed `illegal_transition` line per side) was scanned and contains no opponent-position value, no board coordinate outside a JSONL line the agent legitimately owns, and no secret-shaped string.

**What the pytest suite proves vs. what this launch proves:** every `tests/integration/` gate module states plainly (LIMITATION) that it proves object-level non-leakage and config-root independence using FastMCP's in-memory transport, never a literal socket or a second OS process. This launch is the other half: two real, separately-scheduled OS processes, a real HTTP handshake, and a real captured or survived game — the "over localhost" and "two separate processes" wording the hermetic suite deliberately does not claim.

**Minor procedural note (not a gate blocker):** the launch script's own `time.sleep(8)` + `terminate()` sequence targeted the `uv run` wrapper process, not its Python grandchild; on this Windows host the grandchild kept running after the wrapper was signaled and completed the full 35-turn game on its own roughly 22 real seconds after spawn. This is a test-harness detail (which process to signal), not a defect in `shutdown_cleanly`/`PeerRuntime.stop()` — confirmed by the clean port release and absence of any lingering process afterward.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `await_opponent_turn` called `Envelope.from_dict` on an already-decoded `Envelope`**
- **Found during:** Task 2, first write of `test_full_lifecycle_init_to_game_over` (confirmed first via an isolated probe script before touching test files)
- **Issue:** `tools.py`'s real `_accept()` always enqueues a decoded `Envelope` instance (never a dict) onto the receiving `PeerRuntime`'s queue. `turn_actions.py`'s `await_opponent_turn` unconditionally called `Envelope.from_dict(call_outcome.value)`, which raises `TypeError` when given an `Envelope` instead of a `dict`. Every existing 02-09 unit test constructed its `FakeRuntime` queue with a dict (`incoming.to_dict()`), so this was never exercised against the real production path.
- **Fix:** `envelope = queued if isinstance(queued, Envelope) else Envelope.from_dict(queued)` — handles both the real (Envelope) and existing-fake (dict) shapes.
- **Files modified:** `src/pursuit/network/turn_actions.py`
- **Verification:** Reproduced with a standalone probe script (`asyncio.run`-driven, two real `AgentContext`s) before the fix (`TypeError: Envelope.from_dict expects a dict, got Envelope`); confirmed resolved after the fix; `test_full_lifecycle_init_to_game_over` and the full existing unit suite (168 tests) both pass.
- **Committed in:** `b45e767`

**2. [Rule 1 - Bug] `take_my_turn` unconditionally re-attempted the `MY_TURN` transition, breaking every second-and-later turn**
- **Found during:** Task 2, the same probe script, extended to two pre-queued opponent moves
- **Issue:** `await_opponent_turn`'s own final line legitimately transitions `WAIT_OPPONENT -> MY_TURN` at the end of every successful cycle (D-09's repeatable cycle). `take_my_turn` then unconditionally called `ctx.machine.attempt(State.MY_TURN)` on every invocation, including the very next call in `run_turn_loop` — which always found the machine already at `MY_TURN`, colliding with itself as an illegal `(MY_TURN, MY_TURN)` self-transition. The state machine correctly classifies this RECOVERABLE (leaves state unchanged, reports it) — but `take_my_turn`'s own early-return-on-rejection then skipped the actual move entirely, silently turning every second-and-later "my turn" into a no-op. `await_opponent_turn` then waited again for an opponent message that would never come (the opponent was correctly waiting for ITS OWN reply), eventually exhausting retries and declaring a FALSE technical win after exactly one real exchange (rules 16/22). No existing 02-09 unit test drove `run_turn_loop` (or two direct `take_my_turn` calls) through a second real cycle to catch this.
- **Fix:** Guarded the entry attempt: `if current is not State.MY_TURN: result = ctx.machine.attempt(State.MY_TURN); ...` — symmetric to `await_opponent_turn`'s own guarded `HANDSHAKE` entry. Documented inline with the full reasoning.
- **Files modified:** `src/pursuit/network/turn_actions.py`
- **Verification:** Probe script before the fix showed a spurious `MY_TURN -> MY_TURN` RECOVERABLE report followed by a false `TECHNICAL_LOSS`; after the fix, two pre-queued moves plus a scripted capture on the second cop move produced a clean `Outcome.CAPTURE` with zero illegal reports. Confirmed at real multi-process scale in Task 4 (a full 35-turn game completing to `SURVIVAL`).
- **Files modified:** `src/pursuit/network/turn_actions.py`, `tests/unit/test_orchestrator_loop.py` (see below)
- **Committed in:** `b45e767`

**3. [Rule 1 - Bug, test correction] Updated `test_illegal_transition_is_reported_and_handled_by_severity` to match the corrected design**
- **Found during:** Task 2, immediately after applying fix #2 — the existing test's "recoverable_ctx" sub-test asserted that calling `take_my_turn` with the machine already at `MY_TURN` produces a RECOVERABLE rejection, which is exactly the bug being fixed.
- **Issue:** That assertion encoded the buggy behavior as intended behavior. After the fix, the only state from which `take_my_turn` can still produce an illegal-transition report is a genuinely different, non-`MY_TURN` state (e.g. `GAME_OVER`), and it can now only ever be `PROTOCOL_VIOLATION`.
- **Fix:** Split the test into `test_illegal_transition_is_reported_and_escalates_to_error` (keeps the still-valid `GAME_OVER` -> `PROTOCOL_VIOLATION` assertion, unchanged) and a new `test_take_my_turn_proceeds_when_the_machine_is_already_at_my_turn` (asserts the corrected behavior: no report, the move actually happens). RECOVERABLE severity coverage for NET-05 is unaffected — it was always independently covered by `tests/unit/test_state_machine.py::test_recoverable_attempt_keeps_machine_usable`, which this plan's audit already cites.
- **Files modified:** `tests/unit/test_orchestrator_loop.py`
- **Verification:** Full unit suite (168 tests) green after the change; no other test referenced the removed assertion.
- **Committed in:** `b45e767`

**4. [Rule 3 - Blocking] `src/pursuit/main.py` tripped its own structural guard via documentation text**
- **Found during:** Task 2, `test_entry_point_is_config_dir_parameterised`
- **Issue:** The module docstring's example usage and the `--config-dir` argparse help text both literally contained the substrings `config/police`/`config/thief` (as illustrative examples), which the test's own structural guard (`assert "config/police" not in source`) then flagged — the identical class of documentation-vs-audit-regex tension recorded in 02-09's SUMMARY (Deviations 4 and 6).
- **Fix:** Reworded both to describe the two config roots by role rather than by literal path (`<this agent's config directory>` / "this agent's own role directory under config/"), preserving meaning exactly.
- **Files modified:** `src/pursuit/main.py`
- **Verification:** Guard passes; `--check-config` output and behavior unchanged (re-verified).
- **Committed in:** `4e31d76`

**5. [Rule 3 - Blocking] `test_turn_lifecycle.py` exceeded the 150-code-line gate after the first split**
- **Found during:** Task 2, `bash scripts/check_line_limit.sh` (162 lines)
- **Issue:** Even after splitting the resilience tests into `test_turn_resilience.py` per the plan, the remaining four tests (two GATE-2, two GATE-3 core) plus their setup were still over budget.
- **Fix:** Split again, exactly as the plan's own contingency named: `test_turn_isolation.py` now holds the two GATE-2 tests (`test_two_runtimes_share_no_runtime_state`, `test_entry_point_is_config_dir_parameterised`); `test_turn_lifecycle.py` keeps the two GATE-3 core tests. Three integration gate modules instead of two, never compressed.
- **Files modified:** `tests/integration/test_turn_isolation.py` (new), `tests/integration/test_turn_lifecycle.py`
- **Verification:** `bash scripts/check_line_limit.sh` passes every file; all 8 gate nodes still collect and pass under their same names (task 3's audit table updated to the real module names).
- **Committed in:** `4e31d76`

---

**Total deviations:** 5 auto-fixed (2 real production bugs found via empirical probing and fixed at their source, 1 test correction to match the fix, 2 blocking line-limit/structural-guard issues). No architectural decision was required from the user — every fix stayed within the plan's own delegated discretion (bug fix in code this plan is directly exercising for the first time at multi-cycle/multi-process scale, file layout) or corrected a test whose assertion encoded the bug.
**Impact on plan:** The two production bug fixes are the most consequential outcome of this plan — they are the actual reason a real two-process game (Task 4) can complete at all beyond one exchange. No change to any D-01/D-02/D-04/D-05/D-06/D-07/D-08/D-09/D-10/D-11/D-14/D-15/D-16/D-17/D-18 policy or evidence shape; NET-05's RECOVERABLE coverage moved fully onto `test_state_machine.py`, where it was always independently proven.

## Issues Encountered

- Manually tracing `run_turn_loop`'s multi-cycle behavior by reading the code was insufficient and initially inconclusive given two existing unit tests (`test_full_turn_cycle`, the old `test_illegal_transition_is_reported_and_handled_by_severity`) that individually pinned down BOTH halves of what turned out to be a genuinely conflicting design. Resolved by writing small, disposable probe scripts (`asyncio.run`-driven, using the real production modules) to observe actual behavior empirically before touching any test or source file — this is the same discipline the plan's own `<interface_binding_protocol>` asks for ("bind to the real names... never guess and adjust until green").

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 2's §10.4 milestone gate is closed: all eight gate node IDs collect and pass, NET-01..NET-09 each map to a passing node, and a real two-process localhost game completed end-to-end to a genuine terminal outcome.
- `run_turn_loop`/`take_my_turn`/`await_opponent_turn` are now verified correct across a real multi-turn game (not just a single exchange) — this is the exact surface Phase 3's RL policy plugs into via `AgentContext.choose_move`, and it now behaves correctly for the many-turn games that phase will actually play.
- `docs/phases/phase-2/TODO.md` row `2-10` and the phase-gate checklist are marked done; row `2-99` (verify-work's full sweep + root `docs/TODO.md`) remains for `/gsd:verify-work 2`.
- No file owned by 02-00..02-08 was modified; the only prior-phase files touched are 02-09's own `turn_actions.py` (bug fix) and `main.py` (docstring wording), both within 02-09's original scope and both re-verified against 02-09's full existing test suite.

---
*Phase: 02-fastmcp-infrastructure*
*Completed: 2026-07-29*

## Self-Check: PASSED

All 10 claimed files verified present on disk (tests/integration/conftest.py,
test_peer_roundtrip.py, test_turn_isolation.py, test_turn_lifecycle.py,
test_turn_resilience.py; src/pursuit/network/turn_actions.py; src/pursuit/main.py;
tests/unit/test_orchestrator_loop.py; docs/phases/phase-2/TODO.md; this SUMMARY).
All three task commit hashes (9e7e17a, b45e767, 4e31d76) verified present in
`git log --oneline --all`.
