---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 02 — plan 02-07 executed (NET-06 deadline tracker + retry/backoff + technical-win verdict); 3 plans remain (02-08…02-10)
last_updated: "2026-07-29T12:19:08+03:00"
last_activity: 2026-07-29 -- Executed 02-07-PLAN.md (src/pursuit/network/deadline.py + src/pursuit/network/verdict.py, TDD RED/GREEN/REFACTOR): wait_for_opponent(queue, *, timeout) bounds a single queued-envelope wait; call_with_retry(send, *, timeout, retries, backoff, sleep, clock) runs a narrow retries+1-attempt retry ladder with except ToolError: raise placed BEFORE except RETRYABLE_TRANSPORT_ERRORS = (McpError, DeadlineExpired), so an opponent tool-body rejection can never be laundered into an unearned technical win (RESEARCH Pitfall 4); exhausted retries return a CallOutcome carrying a TechnicalWin with measured evidence (attempts/elapsed_seconds/last_error), never a side effect. Task 1 STEP 0 found 02-RESEARCH.md's cited `MCPError` does not exist in the installed fastmcp 3.4.5/mcp packages -- the real class is `McpError` (mixed case) -- corrected throughout. All eight tests passed first try after that fix; coverage 100%, full suite green (136 passed, 16 skipped), ruff/line-limit clean repo-wide.
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 16
  completed_plans: 13
  percent: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-27)

**Core value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.
**Current focus:** Phase 02 — fastmcp-infrastructure (Phase 01 complete; Wave 0 of Phase 02 executed)

## Current Position

Phase: 02 (fastmcp-infrastructure) — EXECUTING (Wave 2 / plan 02-07 done)
Plan: 8 of 11 executed (02-00, 02-01, 02-02, 02-03, 02-04, 02-05, 02-06, 02-07 done;
  02-08…02-10 remain across Waves 3-5)
Status: Phase 1 of 8 done — 7 phases remaining. Next: continue Phase 02 with plan 02-08
  (handshake responder) or run /gsd:execute-phase 2 again to pick up where this session
  stopped.
Last activity: 2026-07-29 -- Executed 02-07-PLAN.md (TDD RED/GREEN/REFACTOR). Task 1
  STEP 0: verified the exception surface before writing any test -- `from mcp import
  MCPError` (as 02-RESEARCH.md's cited snippet spells it) raises ImportError against the
  installed fastmcp 3.4.5/mcp packages; the real class is `McpError` (mixed case),
  confirmed against mcp.shared.exceptions.McpError's source and the Raises: docstrings in
  fastmcp/client/mixins/tools.py; issubclass(ToolError, McpError) is False. Wrote the
  eight-test NET-06 suite (split into test_deadline.py + test_deadline_retry.py at the
  150-line gate, shared fakes in the former per QUAL-02); confirmed ModuleNotFoundError
  RED gate. Task 2 GREEN: implemented src/pursuit/network/verdict.py
  (TechnicalWinReason/TechnicalWin/CallOutcome, pre-authorised split) and
  src/pursuit/network/deadline.py (DeadlineExpired, RETRYABLE_TRANSPORT_ERRORS =
  (McpError, DeadlineExpired), a single _bounded asyncio.wait_for site, wait_for_opponent,
  call_with_retry with except ToolError: raise placed before except
  RETRYABLE_TRANSPORT_ERRORS) -- all eight tests passed first try; fixed two blocking
  issues found while running the plan's own gates (deadline.py measured 171 code lines on
  first draft, compacted docstrings to fit under 150 without dropping content; the
  docstring's own "no bare except Exception" sentence tripped the plan's bare-except grep
  audit, reworded without weakening the rule). Task 3 REFACTOR: coverage 100% (58/58
  statements, all branches), full suite green (136 passed, 16 skipped, no regression),
  all four static audits (numeric literals, no-default signatures, ToolError exclusion,
  no module-level mutable state) re-confirmed, decision-trace greps (Table 19, minimum)
  present in the module docstring, git status confirmed zero overlap with 02-06 -- no
  further code changes needed so no separate Task 3 commit.

Progress: [█░░░░░░░░░] 13%  (1 of 8 phases)

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-base-logic P00 | 9min | 3 tasks | 23 files |
| Phase 01-base-logic P01 | 15min | 3 tasks | 9 files |
| Phase 01 P02 | 10min | 3 tasks | 6 files |
| Phase 01 P03 | 5min | 3 tasks | 4 files |
| Phase 01-base-logic P04 | 9min | 4 tasks | 8 files |
| Phase 02-fastmcp-infrastructure P00 | 12min | 3 tasks | 20 files |
| Phase 02-fastmcp-infrastructure P01 | 18min | 3 tasks | 6 files |
| Phase 02-fastmcp-infrastructure P02 | 12min | 3 tasks | 4 files |
| Phase 02-fastmcp-infrastructure P03 | 12min | 3 tasks | 3 files |
| Phase 02-fastmcp-infrastructure P04 | 13min | 3 tasks | 6 files |
| Phase 02-fastmcp-infrastructure P05 | 10min | 3 tasks | 1 file |
| Phase 02-fastmcp-infrastructure P06 | 25min | 3 tasks | 5 files |
| Phase 02-fastmcp-infrastructure P07 | 20min | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Init: RL (tabular Q-learning) with a Bayes+Manhattan fallback as the strategy
- Init: Fixed 8-phase build order (book §10.3 stages 1–7 + submission phase 8) — phases are not re-derived
- Init: Real `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` (Segal §2.2), not `.planning/` pointers
- Init: GSD config — Balanced models, Interactive mode, branching none, TDD on, UI phases off
- [Phase ?]: D-05: all game numerics in game_params.json — zero hardcoded values in any src/ file (Appendix F §2 rule 1)
- [Phase ?]: D-06: game_params.json duplicated byte-for-byte in config/police/ and config/thief/ for Phase-2 NET-09 identity check
- [Phase ?]: D-04: package name is pursuit — neutral, usable by both cop and thief repos at Phase 8 split
- [Phase 01-01]: D-07: constants.py/Enum hold only structural non-numeric values; zero game numbers hardcoded
- [Phase 01-01]: D-08: barriered cell is impassable; get_legal_moves excludes it (prerequisite for BASE-05)
- [Phase 01-01]: D-12: GameState @dataclass(frozen=True); immutable snapshot pattern; dataclasses.replace for transitions
- [Phase 01-01]: D-13: STAY (current position) always in legal moves; agent can always pass even surrounded by barriers
- [Phase 01-01]: D-14: Outcome enum names all four outcomes; only CAPTURE/SURVIVAL produced in Phase 1
- [Phase 01-02]: D-10: barrier-on-thief IS accepted; capture consequence owned by detect_capture (01-03)
- [Phase 01-02]: D-11: quota enforced via params.barrier_quota only; zero numeric literals in barrier.py (AST verified)
- [Phase 01-02]: Validate-first order in place_barrier prevents Pitfall 2 (spurious quota consumption on invalid placements)
- [Phase 01-03]: D-12 check order: BASE-03 (cop==thief) -> BASE-04 (thief in barriers) -> BASE-05 (no legal moves) -> None
- [Phase 01-03]: D-13 note: BASE-05 independent trigger geometrically impossible; STAY always legal unless BASE-04 fires first
- [Phase 01-03]: D-14: score_outcome reads exclusively from params.score_* fields; only literal 0 for TECHNICAL_LOSS
- [Phase 01-03]: D-15: Phase 1 produces only CAPTURE/SURVIVAL; TIE/TECHNICAL_LOSS unreachable but scored for completeness
- [Phase 01-03]: D-16: evaluate_turn_end uses params.survival_threshold (no hardcoded value)
- [Phase Phase 01-04]: D-09: engine.apply_cop_action wires cop move + barrier placement in one cop action
- [Phase Phase 01-04]: D-12: engine wires the turn boundary: apply_cop_action does cop-acts + capture-check, apply_thief_move does thief-move + turn-increment + survival-check
- [Phase Phase 01-04]: increment_turn() added to state.py so engine.py has zero non-zero numeric literals (AST scan clean)
- [Phase 02-00]: D-04/D-16/D-17/D-18: config/{police,thief}/network.json holds every network number; ports 8001/8002 and watchdog_poll_seconds=1 are engineering defaults not traced to PARAMETERS.md; retry_count=3/backoff_seconds=5 reused from Table 19 Gatekeeper rows
- [Phase 02-01]: QUAL-02: require_key/require_int/require_str extracted to src/pursuit/shared/loader_helpers.py at the second consumer (network_config.py); config.py re-pointed at it, zero private validator copies remain
- [Phase 02-01]: NET-02 guaranteed by construction: load_network_config returns a fresh NetworkParams every call, no module-level cache/singleton; verified by identity checks in both directions (police vs thief, and two calls to the same file)
- [Phase 02-01]: Reused 02-00's NetworkConfigKey.ENV_HOST/ENV_PORT/ENV_OPPONENT_URL for the D-16 override names instead of adding a duplicate NetworkEnvVar class
- [Phase 02-02]: D-06: Envelope frozen dataclass fixed at exactly four keys {type, turn, sender, payload}; from_dict accepts wire `type` as a string only, never a MessageType instance; Phase-4 hint / Phase-6 commit arrive as new MessageType members, never new envelope keys
- [Phase 02-02]: D-08/D-15: config_digest hashes canonically re-serialized JSON (sort_keys=True, separators=(",", ":")), never raw file bytes, so formatting drift can never fake a NET-09 config mismatch; canonical_json() is the single project-wide canonicalisation Phase 6's commit-reveal hash must reuse (QUAL-02)
- [Phase 02-02]: digests_match uses secrets.compare_digest per CLAUDE.md's standing digest-comparison idiom, ahead of Phase 6 where it becomes security-critical
- [Phase 02-03]: D-09/D-12: State enum fixed at exactly six members; ALLOWED_TRANSITIONS is an explicit dict[State, frozenset[State]] keyed by every member, GAME_OVER/ERROR terminal (empty frozenset) — no FSM library imported or installed
- [Phase 02-03]: D-10: RECOVERABLE_ATTEMPTS is exactly six pairs (four self-transition duplicates + two late-handshake pairs); every other illegal pair — including anything out of ERROR and any backwards jump to INIT — is PROTOCOL_VIOLATION and escalates to State.ERROR
- [Phase 02-03]: NET-05: transition() calls the injected reporter from a single call site before the outcome branch, guaranteeing every illegal attempt is reported exactly once and a legal transition reports zero times
- [Phase 02-03]: reporter is injected as a TransitionReporter Protocol parameter, not imported — state_machine.py has zero dependency on 02-04's event log, keeping 02-03/02-04 same-wave-safe; 02-04's adapter must match the exact keyword-only __call__(*, current, target, severity, reason) -> None shape
- [Phase 02-03]: NET-02: TurnStateMachine keeps state on the instance only (self._state); no module-level mutable current-state variable anywhere in state_machine.py
- [Phase 02-04]: D-11/NET-05/NET-07: append_event() enforces validate->serialize->write->flush->os.fsync->echo, in that literal order — a rejected record never creates/grows the log, durability always precedes the console echo
- [Phase 02-04]: D-14/D-18/NET-07 (RESEARCH Pitfall 6): Watchdog.check_once() runs on_freeze (suppressing exceptions) THEN the injected exit_action, verified by reading the incident file from inside the exit callable itself; threshold_seconds/poll_seconds are required keyword-only constructor args with no default in source
- [Phase 02-04]: watchdog_poll_seconds was already present in NetworkParams/network.json (=1, D-18) before this plan ran — no hand-off gap to close at 02-09
- [Phase 02-04]: Plan-internal tension (same category as 02-03's event_log substring issue): EventType.WATCHDOG_INCIDENT = "watchdog_incident" is required verbatim by the interfaces contract, but the plan's own verify/decoupling-audit scripts substring-scan for "watchdog" in event_log.py and flag it. Resolved by rewording every avoidable docstring mention (in both event_log.py and watchdog.py) and documenting the one irreducible, schema-required occurrence in the SUMMARY; true import-level decoupling (no `import` of watchdog in event_log.py or vice versa) independently re-verified and holds
- [Phase 02-05]: DOC-02: docs/PRD_mcp_transport.md written and approved in Wave 1, before any transport source exists (SEGAL §2.5 step 5) — documentation-only plan, zero source/config touched
- [Phase 02-05]: D-16/D-18 category separation enforced structurally: §10.1 (PARAMETERS.md-traced: 30s/60s/3/5s, Table 19 rows 6/7/4/3) and §10.2 (engineering defaults: ports 8001/8002, watchdog_poll_seconds=1) are two visually distinct tables so neither reader nor future phase can conflate them
- [Phase 02-05]: D-17 reuse of Table 19 Gatekeeper rows 3-4 for the NET-06 retry/backoff pair documented in prose as a deliberate, auditable reuse (both minimum status, may be raised never lowered) rather than an invented second pair of numbers
- [Phase 02-06]: NET-09 seam: register_tools/build_server/PeerRuntime all accept a keyword-only handshake_handler; None keeps the D-05 generic ack (pinned so 02-08's fake-peer tests stay valid), a supplied async handler's reply is returned verbatim and nothing is enqueued -- the exact hook 02-09 uses to bind 02-08's respond_to_handshake without editing tools.py
- [Phase 02-06]: QUAL-02: all four D-05 handlers share one _accept(queue, message_type, turn, sender, payload) helper that translates Envelope.from_dict's TypeError/KeyError/ValueError into fastmcp.exceptions.ToolError, decode-before-enqueue so nothing half-parsed ever reaches the queue
- [Phase 02-06]: RESEARCH Open Question 2 resolved by measurement, not assumption: task.cancel() alone left the listening port bound (FastMCP 3.4.5's run_http_async has no exposed uvicorn should_exit handle); PeerRuntime now binds its own listening socket and hands it to run_async via sockets=[...] so stop() closes the real OS socket directly -- re-measured SHUTDOWN CLEAN
- [Phase 02-06]: fastmcp 3.4.5 API shape notes for later plans -- no plural mcp.get_tools(); use (await mcp.get_tool(name)).fn for the coroutine-function guard; Client has no public timeout attribute, only the private _session_kwargs['read_timeout_seconds'], but client.transport.url is public
- [Phase 02-07]: Exception-surface correction for all later plans touching NET-06/transport errors: the installed fastmcp 3.4.5/mcp packages spell the transport exception `McpError` (mixed case), NOT `MCPError` as 02-RESEARCH.md's cited snippet spells it -- `from mcp import MCPError` raises ImportError; `from mcp import McpError` is correct. issubclass(ToolError, McpError) is False, so RESEARCH Pitfall 4's except-clause design (ToolError excluded from the retryable set) is unaffected, only the import spelling
- [Phase 02-07]: D-13/D-17 implemented: RETRYABLE_TRANSPORT_ERRORS = (McpError, DeadlineExpired); except ToolError: raise placed BEFORE except RETRYABLE_TRANSPORT_ERRORS inside call_with_retry so an application-level tool rejection can never become an unearned technical win; exhausted retries return a CallOutcome carrying a TechnicalWin (reason, attempts, timeout_seconds, backoff_seconds, elapsed_seconds, last_error) as a returned value only -- deadline.py never ends the game, scores, or logs
- [Phase 02-07]: __all__ written as an immutable tuple, not a list, in deadline.py -- satisfies both the plan's literal "export the seven public names" instruction and the NET-02 AST guard that forbids module-level list/dict/set literals

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Team code (SUB-06)~~ **Decided: `khm-mn17`** (08-CONTEXT.md); per-game config naming still a league prerequisite
- Reporting (REPORT-01) is submission-critical: a missing/contradictory report zeroes both teams
- League opponents must be contacted early (this week) — scored games realistically Aug 11–12 post-exam

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-29T12:19:08+03:00
Stopped at: Completed 02-07-PLAN.md (src/pursuit/network/deadline.py +
  src/pursuit/network/verdict.py — NET-06 deadline tracker + retry/backoff +
  technical-win verdict, D-13/D-17, TDD RED/GREEN/REFACTOR; Task 1 STEP 0 found and fixed
  the MCPError -> McpError exception-spelling drift from 02-RESEARCH.md). SUMMARY at
  .planning/phases/02-fastmcp-infrastructure/02-07-SUMMARY.md.
  Carried forward: Phase-01 code review CR-01 still deferred; Phase-2 triplet
  (docs/phases/phase-2/{PRD,PLAN,TODO}.md) — TODO row 2-06 ticked; row 2-07 still needs
  ticking, plus rows for 02-08..02-10 as those plans land, and the full sweep (plus root
  docs/TODO.md) at /gsd:verify-work time.
Resume file: None — continue with plan 02-08 (handshake responder) via
  /gsd:execute-phase 2 (clear context first).
  Per-day sequence from Phase 3 on: /gsd:graphify → [/gsd:ai-integration-phase N for 3 & 4]
  → /gsd:plan-phase N --chunked → /gsd:execute-phase N → /gsd:verify-work N
