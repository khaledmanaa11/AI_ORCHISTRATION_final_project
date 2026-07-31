---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 03 — plan 03-01 executed (docs/PRD_rl_strategy.md v1.00, the Q-learning per-mechanism PRD, written before any src/pursuit/strategy/ code, DOC-02); 9 more Phase-3 plans remain (03-02..03-10)
last_updated: "2026-07-31T19:33:18+03:00"
last_activity: 2026-07-31 -- Executed 03-01-PLAN.md (docs/PRD_rl_strategy.md, documentation-only, no source/config touched): Task 1 wrote Sec1-6 (mechanism scope + STRAT-01..07/DOC-02 requirements table; state-key composition own/target/blocked-mask/barriers-used/turn-bucket with a worked example and state-space arithmetic 49x49x16x15x3=1,728,720; 5-action space with the barrier decision deliberately excluded, D-12; reward table distinguished from game_params.json Table 17 scoring; Q-update + epsilon/alpha decay equations named only as config keys; fallback trigger key-absent-OR-visits-below-min_visits with the Bayes prior and the STRAT-02-says-Manhattan-but-implementation-is-barrier-aware-BFS deviation recorded). Task 2 appended Sec7-10 (offline training regime stepping pursuit.sdk.engine directly never the network layer, D-17; sparring pool composition/sampling and the two distinct checkpoint cadences; QLearningBrain-vs-HeuristicBrain win-rate success bar citing AI-SPEC Sec5 E5; the Sec9 two-table parameter split -- PARAMETERS.md game values never altered vs D-18 engineering defaults, every one of 03-00's config/{police,thief}/strategy.json keys cited verbatim; Sec10 believed-target input contract D-11, STRAT-07/rule 25, role isolation D-03, truthful barrier declarations). Committed as two separate task commits (b4e9700, f601e7f) to match Task 1's own verify step requiring no section beyond Sec6 before that commit. docs/phases/phase-3/TODO.md row 03-01 and the phase-gate DOC-02 line both ticked. No deviations; full digit sweep of the finished document confirmed no unsourced number.
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 27
  completed_plans: 18
  percent: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-27)

**Core value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.
**Current focus:** Phase 03 — blind-strategy-module-rl-policy (Phases 01-02 code complete; Phase 03 plan 01 of 11 executed)

## Current Position

Phase: 03 (blind-strategy-module-rl-policy) — EXECUTING (plan 03-01 of 11 done)
Plan: 2 of 11 executed (03-00, 03-01 done; 03-02..03-10 remain). Next plan is 03-02
  (`BrainBase` + `Observation`/`Decision` contracts + config-driven brain registry, STRAT-03/07).
Status: Phase 1 of 8 done, Phase 2's code plans all executed (verify-work 2 still pending),
  Phase 3 scaffolding (config + loader + Enums, 03-00) and the RL strategy per-mechanism PRD
  (03-01, DOC-02) both landed this session. 5 phases remain after Phase 3 closes. Next:
  /gsd:execute-phase 3 to continue with 03-02.
Last activity: 2026-07-31 -- Executed 03-01-PLAN.md, the documentation-only Phase-3 PRD plan
  (no source/config touched, per its own objective — the PRD had to exist and be approved
  before any policy code, SEGAL §2.5 step 5). Task 1: `docs/PRD_rl_strategy.md` Sec1-6 —
  mechanism scope + STRAT-01..07/DOC-02 requirements table; the exact state-key composition
  (own cell, believed target cell, agent-relative blocked-direction bitmask, barriers-used
  count, bucketed turn phase) with a worked example (`2,3|5,5|9|6|1`) and the state-space
  arithmetic (49×49×16×15×3 = 1,728,720 theoretical keys vs the 250,000 `max_table_keys`
  health ceiling); the 5-action space with the barrier decision deliberately excluded (D-12);
  the reward table, explicitly distinguished from `game_params.json` Table 17's league
  scoring; the Q-update and epsilon/alpha decay equations, every hyperparameter named only as
  a config key; the fallback trigger (key-absent OR visits below `min_visits`) with the Bayes
  motion-model prior and the recorded STRAT-02-says-Manhattan-but-implementation-is-
  barrier-aware-BFS deviation (D-08/D-09). Task 2: Sec7-10 — the offline training regime
  stepping `pursuit.sdk.engine` directly, never the network layer (D-17); the sparring pool
  composition/sampling rule and the two distinct checkpoint cadences (crash-recovery vs
  pool-snapshot); the `QLearningBrain`-vs-`HeuristicBrain` win-rate success bar citing
  AI-SPEC §5 E5 rather than restating it; Sec9's two-table parameter split (PARAMETERS.md
  game values, never altered here, vs the D-18 engineering-defaults table covering every one
  of 03-00's `config/{police,thief}/strategy.json` keys, cross-checked verbatim); Sec10's
  believed-target input contract (D-11), STRAT-07/rule 25, role isolation (D-03), and
  truthful/quota-respecting barrier declarations. Committed as two separate commits
  (`b4e9700`, `f601e7f`) rather than one, so Task 1's own verify step ("no section beyond
  Sec6 yet") was satisfied by a real intermediate commit, not just by writing order.
  `docs/phases/phase-3/TODO.md` row 03-01 and the phase-gate DOC-02 line both ticked. No
  deviations; a full digit sweep of the finished 327-line document confirmed every numeric
  literal traces to a Sec9 table row or is a section/rule/table citation.

Progress: [█░░░░░░░░░] 13%  (1 of 8 phases; Phase 2 code complete pending verify-work;
  Phase 3 plan 2 of 11 executed)

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
| Phase 02-fastmcp-infrastructure P08 | 30min | 3 tasks | 5 files |
| Phase 02 P09 | 75min | 3 tasks | 15 files |
| Phase 02 P10 | 110min | 4 tasks | 10 files |
| Phase 03 P00 | 19min | 3 tasks | 23 files |
| Phase 03 P01 | 6min | 2 tasks | 2 files |

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
- [Phase 02-09]: Design note 8 resolved: call_with_retry DOES retry DeadlineExpired (RETRYABLE_TRANSPORT_ERRORS includes it), so await_opponent_turn wraps wait_for_opponent in call_with_retry rather than declaring a technical win on the first inbound timeout; retries_attempted is always the measured attempt count, never a constant
- [Phase 02-09]: Two 150-line-gate splits: orchestrator.py -> {orchestrator.py, turn_actions.py} (not pre-authorised by the plan, done anyway per Segal's hard line limit) and agent_lifecycle.py -> {agent_lifecycle.py, agent_wiring.py} (pre-authorised). The orchestrator/turn_actions re-export needed a PEP 562 module __getattr__ instead of an eager import -- an eager cross-import was reproduced as a genuine circular import when turn_actions.py was imported first, verified fixed under both import orders
- [Phase 02-09]: fastmcp.Client is a required async context manager (Client.__aenter__ calls self._connect()) -- take_my_turn/run_agent always enter it via `async with` before calling a tool; the plan's own pseudocode omitted this and was adapted accordingly
- [Phase 02-10]: Real production bug found and fixed via 02-10's GATE-3 test, not by 02-10 itself: turn_actions.py's take_my_turn unconditionally re-attempted State.MY_TURN every call, but await_opponent_turn's own final line legitimately leaves the machine at MY_TURN at the end of every cycle after the first -- colliding as an illegal self-transition, silently no-opping every second-and-later turn and starving await_opponent_turn into a FALSE technical win. No 02-09 unit test ever drove a real second cycle to catch it. Fixed by guarding take_my_turn's entry attempt on `current is not State.MY_TURN`, symmetric to await_opponent_turn's own guarded HANDSHAKE entry. A second, related bug (await_opponent_turn calling Envelope.from_dict on an already-decoded Envelope -- tools.py's real _accept enqueues an Envelope instance, never a dict) was fixed the same way. Both confirmed via standalone probe scripts and re-verified at real two-process scale (Task 4: a full 35-turn game completed cleanly to SURVIVAL)
- [Phase 02-10]: NET-05's RECOVERABLE severity coverage was never uniquely provided by the orchestrator-level test that assumed the now-fixed buggy behavior -- it was always independently covered by tests/unit/test_state_machine.py::test_recoverable_attempt_keeps_machine_usable (QUAL-02); the orchestrator-level test was corrected to assert the fixed behavior instead of the bug
- [Phase 02-10]: A three-way split was needed for the integration gate modules (test_peer_roundtrip.py, test_turn_isolation.py, test_turn_lifecycle.py, test_turn_resilience.py), one level deeper than the plan's own two-way split anticipation -- test_turn_lifecycle.py still exceeded 150 lines after the first split, so the two GATE-2 tests moved to test_turn_isolation.py, exactly the contingency the plan named in advance
- [Phase 03-00]: StrategyKey/TrainingKey Enums address every Phase-3 hyperparameter; strategy_config.py is loader_helpers' 3rd consumer
- [Phase 03-00]: artifacts_dir empty-defaults under LOCALAPPDATA (D-22); reward_capture/reward_survival/reward_step/reward_barrier_gain and alpha_floor/alpha_decay_episodes/eval_seed_offset are engineering defaults not sourced from AI-SPEC
- [Phase 03-01]: docs/PRD_rl_strategy.md v1.00 written before any src/pursuit/strategy/ code (DOC-02): reward function does NOT reuse game_params.json Table 17 scoring; STRAT-02's Manhattan fallback wording is implemented as barrier-aware BFS, documented as a deliberate deviation

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

Last session: 2026-07-31T19:33:18+03:00
Stopped at: Completed 03-01-PLAN.md (docs/PRD_rl_strategy.md — the Phase-3 per-mechanism PRD
  for the Q-learning policy, documentation-only, no source/config touched). SUMMARY at
  .planning/phases/03-blind-strategy-module-rl-policy/03-01-SUMMARY.md, including the
  reward-vs-scoring-table and STRAT-02-Manhattan-vs-BFS documentation-accuracy decisions.
  Carried forward: Phase-01 code review CR-01 still deferred; Phase-2 verify-work
  (docs/phases/phase-2/TODO.md row 2-99 + root docs/TODO.md) still pending — Phase 3
  planning/execution proceeded ahead of it per this session's instructions.
  docs/phases/phase-3/TODO.md rows 03-00, 03-01 ticked; rows 03-02..03-10, 03-96, 03-99
  remain.
Resume file: None — 03-01 is fully committed (2 task commits + this docs/SUMMARY/STATE
  commit). Next step is /gsd:execute-phase 3 to continue with 03-02 (`BrainBase` +
  `Observation`/`Decision` contracts + config-driven brain registry, STRAT-03/07).
  Per-day sequence from Phase 3 on: /gsd:graphify → [/gsd:ai-integration-phase N for 3 & 4]
  → /gsd:plan-phase N --chunked → /gsd:execute-phase N → /gsd:verify-work N. Note: the
  CLAUDE.md-mandated graphify build/refresh for Phase 3 has still not run this session —
  do it before/after the next execute-phase batch (graphify update . && cp
  graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/).
