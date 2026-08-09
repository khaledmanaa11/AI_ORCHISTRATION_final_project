---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 04-10 (bluff generator). Phase 4 wave 4 (04-09 + 04-10) is now fully done. Wave 5 (04-11) is next.
last_updated: "2026-08-09T01:12:00.000Z"
last_activity: 2026-08-09 -- Phase 04 wave 4 completed (04-10 bluff generator: wordcount.py, hintbank.py/hintbank_templates.py, bluff.py/bluff_prompt.py, compose() total by construction)
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 56
  completed_plans: 34
  percent: 30
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-27)

**Core value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.
**Current focus:** Phase 04 — language-and-scent

## Current Position

Phase: 04 (language-and-scent) — EXECUTING
Plan: 10 of 14 (waves 1–4 done: 04-01..04-10; wave 4 now FULLY COMPLETE —
  see .planning/phases/04-language-and-scent/04-10-SUMMARY.md.
  Next: 04-11 (BeliefAdapter), starting wave 5. Resume point (carry-overs
  J-N are new from 04-10, still relevant to 04-12):
  .planning/phases/04-language-and-scent/RESUME.md)

04-10 delivered: services/llm/wordcount.py (count()/truncate(), one
  whitespace-splitting rule), services/llm/hintbank.py +
  hintbank_templates.py (HintBank, a seeded per-game template bank keyed
  by ClaimKind/Intent, import-time validated against the REAL shipped
  language.json word limit), services/llm/bluff.py + bluff_prompt.py
  (BluffContext + compose(), the total 5-step hint composer: one call,
  one retry on overflow, truncate, assert_no_coordinates, bank fallback
  on every failure path; D-39's style guide never reveals `intent` to the
  model, D-36). Deviation: the word limit's config home is language.json's
  model group (not deception.json as the plan's files_modified listed) --
  reasoning in 04-10-SUMMARY.md, RESUME.md carry-over A closed / J opened.
  assert_no_coordinates moved network/hint_payload.py -> new
  shared/hint_guard.py (re-exported), matching 04-08's Intent precedent.
  Full gates green: 1001 passed, 94.81% coverage, ruff/line-limit/
  no-llm-in-strategy all clean. Knowledge graph refreshed this session
  (4917 nodes / 8593 edges / 311 communities).

04-09 delivered: strategy/scent_check.py (contradicts(), the Sec4.4 lie
  detector reproducing the book's 0.9 -> 0.81 worked example exactly),
  strategy/reliability.py (Reliability, a bounded [r_min, r_max] adaptive
  coefficient, D-51 — a disclosed revision of D-40's "fixed" framing),
  strategy/belief_hint.py (hint_likelihood(), the D-40 Bayes mix weighted
  well below scent and never zeroing a cell), plus two new belief.json
  config groups (reliability, hint_likelihood). End-to-end Sec4.4
  reproduction measured and committed: a fully-lying opponent's reliability
  collapses 0.5 -> 0.2 -> 0.05 (r_min) within two turns; a fully-truthful
  one holds at 0.5 for all ten; both regimes' fused-posterior argmax
  tracks the real scent trail, not the claim. Full gates green: 903
  passed, 94.55% coverage, ruff/line-limit/no-llm-in-strategy all clean.

<!-- The narrative below this line is Phase 3 history, retained deliberately: it
     records why the run-2 architecture exists. It is NOT the current position. -->

  completion but FAILED GATE-4 for both roles on real, measured evidence (see
  docs/phases/phase-3/RUN-1-POSTMORTEM.md) — no bar was lowered, no table was promoted.
  That diagnosis plus a 3-agent literature review produced D-09-superseded (distance is
  the wrong objective for both roles; cop-win iff the thief's free component is a
  forest) and a validated 15-plan run-2 build order (03-11..03-25, 7 waves, RL demoted
  from mover to a ~60-weight linear evaluator under alpha-beta search, D-26). Wave 1's
  first plan, **03-11 (graph primitives), is fully executed**: `pursuit.strategy.graph`
  (components/cycles/territory — free_cells, neighbors, component_of, degree,
  edge_count, articulation_points, cycle_rank, is_forest, reduction_value,
  voronoi_split, territory_diff), 3 tasks + 1 coverage-gap fix, 4 commits
  (12be2e4/52c85f2/b4b06fa/af5f0de), 100% package coverage. Wave 1's second plan,
  **03-12 (thief safety rule -- never step into N[cop]), is now also fully executed**:
  `src/pursuit/strategy/safety.py` (`closed_neighbourhood`/`safe_moves`, D-31's measured
  296/300=0.987 vs 283/300=0.943 free win, pure/D-03, never-empty guarantee) wired into
  `fallback.py::_evade` (filter-then-rank, `_pursue` untouched) and guarded by a
  non-vacuous 160-game regression test, 2 commits (71b201d/20d87f6). Wave 1's third
  plan, **03-13 (turns_remaining + the whole run-2 config surface), is now also fully
  executed**: `encoding.py`'s key field 5 is exact `turns_remaining` (turn_bucket
  deleted, D-06 superseded); every knob 03-14..03-25 need is declared once across
  `StrategyKey`/`TrainingKey` + new `strategy_schema.py` + both role `strategy.json`
  files (15 added, 1 removed); `QTable.SCHEMA_VERSION` bumped 1->2 so a run-1-format
  table fails loud instead of loading wrong, 3 commits (da27684/050d95d/dd7384e).
  Next: 03-14 (terminal signal, R2+R4) finishes wave 1.
Status: Executing Phase 04
  pending). Phase 3 run 2 wave 1 is underway: 3 of 15 run-2 plans done. Waves 1-6 are
  autonomous; wave 7 (03-25) is a human-operator checkpoint (the overnight training run
  and the real GATE-4 remeasurement) — do not run verify-work 3 until it passes. Three
  standing constraints carried into every remaining plan: 03-23's pre-flight gate must
  exit 0 before any training job starts; the 0.55 GATE-4 bar is NOT lowered (D-28); and
  03-21 stops and asks rather than inventing a number if its two target checks conflict.
  5 phases remain after Phase 3 closes.
Last activity: 2026-08-08 -- Phase 04 execution started
  config surface). Full account is in the frontmatter `last_activity` field above;
  condensed here: 3 tasks (encode_state's turns_remaining field, the full run-2
  StrategyKey/TrainingKey + strategy_schema.py + both config files, qtable
  schema-version fail-loud), 1 mechanical deviation (Rule 3 — test_strategy_config.py
  split at the 150-line gate into a new test_strategy_config_run2.py, the exact
  contingency the plan's own context section named in advance). Two known stale
  references deliberately left untouched, out of this plan's file-ownership scope
  (docs/PRD_rl_strategy.md Sec2 — 03-22's; training/harness.py's docstring — 03-14's
  this wave) — both flagged in 03-13-SUMMARY.md for the owning plan to fix in passing.
  Full repo gates green: `ruff check .` 0 violations, line-limit clean,
  474 passed / 2 skipped (same 2 pre-existing skips). Graphify rebuilt (3583
  nodes/6484 edges/234 communities) and `GRAPH_REPORT.md` refreshed.
  `docs/phases/phase-3/TODO.md` deliberately not touched — same rationale as 03-11/03-12.

Progress: [█░░░░░░░░░] 13%  (1 of 8 phases; Phase 2 code complete pending verify-work;
  Phase 3 run 2: 3 of 15 plans (03-11, 03-12, 03-13) done, 12 remain across waves 1-7,
  wave 7 is a human-operator checkpoint)

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
| Phase 03 P02 | 12min | 3 tasks | 5 files |
| Phase 03 P03 | 18min | 2 tasks | 4 files |
| Phase 03 P04 | ~35min | 3 tasks | 11 files |
| Phase 03 P05 | ~25min | 2 tasks | 6 files |
| Phase 03 P06 | ~20min | 2 tasks | 5 files |
| Phase 03 P07 | ~70min | 2 tasks | 19 files |
| Phase 03 P08 | ~50min (this session; Tasks 1-3 committed in a prior, interrupted session) | 1 task (Task 4) | 11 files |
| Phase 03 P09 | ~20min | 2 tasks | 6 files |
| Phase 03 P10 | ~40min (Tasks 1-3 only; Task 4 pending operator) | 3 of 4 tasks | ~20 files |
| Phase 03 P11 (run-2 wave 1) | ~25min | 3 tasks + 1 coverage-gap fix | 8 files |
| Phase 03 P13 | 45min | 3 tasks | 12 files |

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
- [Phase 03-02]: BrainBase ABC + frozen Observation/Decision seam; Action IntEnum order frozen and pinned by test (STRAT-01); build_brain resolves via an explicit dict, never eval/exec/importlib (STRAT-03, D-07); AST-walk structural tests prove no pursuit.network or LLM/HTTP/subprocess/socket import is reachable from src/pursuit/strategy/ (STRAT-07), demonstrated to actually fail when triggered
- [Phase 03-03]: bfs(state, start, goal, agent, params) is the single barrier-aware distance oracle for the phase (QUAL-02); adjacency comes entirely from board.get_legal_moves via a per-step probe state (dataclasses.replace), never reimplemented; UNREACHABLE=-1 sentinel (not math.inf) for a walled-off goal, never raises; neighbours sorted ascending (row, col) at every expansion for deterministic tie-breaking; no walk() helper added since gameplay calls bfs() fresh every turn and a multi-step walk is a test-time concern only
- [Phase 03-04]: prior.spread() is the Bayes PREDICTION step only (no evidence term, Phase-4 seam); mass invariant asserted inside the function on both entry and exit, not spot-checked in tests; fallback.pick() ranks candidates via bfs() distance only (cop minimizes, thief maximizes tie-breaking toward more onward legal moves), unreachable target never raises; HeuristicBrain is fully playable for both roles, instance state only (D-03), and is the single heuristic implementation fallback.py owns (QUAL-02)
- [Phase 03-04]: Deviation -- registry.build_brain(role, params, game_params) now REQUIRES GameParams threaded to every brain constructor (BrainBase._pick_move/_decide_move deliberately carry none, per 03-02); this is now the fixed calling convention 03-06's QLearningBrain must also match
- [Phase 03-05]: encode_state/turn_bucket take (obs, params: StrategyParams, game_params: GameParams) as two explicit typed parameters, matching 03-04's build_brain(role, params, game_params) convention; blocked_mask bit order frozen to Action's own IntEnum order (NORTH=bit0..WEST=bit3, STAY excluded); QTable JSON schema nests values+visits inside one per-key object so they can never desynchronize; durable_write.py's retries/backoff stay required keyword-only args with no defaults, QTable.save() supplies its own module-level structural constants (_SAVE_RETRIES=3/_SAVE_BACKOFF_SECONDS=0.1s)
- [Phase 03-05]: Deviation (Rule 3 - blocking) -- tests/unit/strategy/test_qtable.py split into test_qtable.py (API + fail-loud load) and test_qtable_durability.py (crash/retry mechanics) after hitting 152 code lines against the 150-line gate; no test weakened or removed
- [Phase 03-06]: QLearningBrain(role, params, game_params, rng=None) matches the fixed build_brain calling convention; rng is optional/keyword-only (unseeded random.Random() default) so the registry path still constructs a working brain, while 03-08 injects a seeded one by constructing directly; epsilon is a mutable instance attribute initialized from params.epsilon_eval, reassigned per-episode by 03-08's own decay schedule rather than re-read from config per decision; exploration is legal-move-filtered per PRD Sec5's literal wording, the greedy/argmax branch is deliberately NOT filtered (matches the PRD; any legal-move guardrail is AI-SPEC Sec6's distinct, not-yet-owned "Legal-move filter" online guardrail); both explore and exploit inside the visited region tag source=QTABLE, per the plan's own literal task text
- [Phase 03-06]: Deviation (Rule 3 - blocking, repeat of 03-05's pattern) -- test_qlearning.py split into test_qlearning.py + test_qlearning_learning.py + non-collected _qlearning_fixtures.py helper (mirrors tests/unit/_fakes_agent.py) after hitting 174 code lines; Deviation (Rule 2 - missing coverage) -- added a _decide_move barrier=None test mirroring HeuristicBrain's, closing qlearning.py to 100% coverage
- [Phase 03-07]: choose_barrier(state, game_params, believed_thief_cell, min_gain) scores candidates by BFS-distance increase to a fixed anchor (the board corner diagonally farthest from the cop's own cell) -- an autonomous scoring-metric decision since the plan left the exact metric open; bfs() is provably symmetric between cop/thief in this codebase, so a direct cop-thief-distance metric could not discriminate a cop-favoring placement, and the anchor cell itself is excluded from candidates to close a trivial self-referential exploit found before any test was written
- [Phase 03-07]: min_gain is a 4th explicit parameter (not folded into game_params) because barrier_quota (PARAMETERS.md, D-05) and barrier_min_gain (engineering default, D-18) live in two different config objects (GameParams vs StrategyParams) by this codebase's established architecture; both _decide_move implementations build a post-move probe state before calling choose_barrier, matching sdk.engine.apply_cop_action's real move-then-barrier order so declared==applied holds by construction
- [Phase 03-07]: Deviation (Rule 2/3 - blocking) -- strategy.barrier_min_gain (value 1) added to StrategyParams/both strategy.json files; required first splitting src/pursuit/constants.py (at the exact 150-code-line ceiling) into constants.py (game-domain enums) + new src/pursuit/config_keys.py (ConfigKey/NetworkConfigKey/StrategyKey/TrainingKey), 5 import sites updated mechanically. Deviation (Rule 3 - blocking, repeat of 03-05/03-06) -- test_barriers.py split into test_barriers.py + test_barriers_integration.py at the 150-line gate
- [Phase 03-08]: run_training(config: TrainingRunConfig) bundles game_params+cop_params+thief_params into one object rather than the plan's literal single-StrategyParams run_training(params) sketch -- one run trains BOTH roles' tables together under two configs that legitimately differ in brain_class/qtable_path/reward_*, matching the EpisodeConfig precedent (game_params+learner_params) already established by this plan's own inherited harness.py; run-level scalars (seed/episodes/checkpoint_every/pool_snapshot_every/artifacts_dir) are validated equal between cop.json/thief.json up front (require_shared_run_fields), raising loud on drift rather than silently picking one side
- [Phase 03-08]: A single shared random.Random(seed) instance drives opponent sampling AND both QLearningBrains' own epsilon-greedy exploration -- not a per-brain sub-seed -- matching docs/PRD_rl_strategy.md Sec5's D-19 wording verbatim ("epsilon-greedy action selection and opponent sampling use a seeded random.Random(training.seed) instance"); this is what makes RunState.rng_state's one getstate() reproduce the whole run, and is a training-pipeline determinism choice unrelated to project rule 2 (which governs the two DEPLOYED match-time processes, not this offline single-process harness)
- [Phase 03-08]: Training checkpoints Q-tables under StrategyParams.artifacts_dir using the qtable_path's basename, never at the repo-relative qtable_path itself -- that path is reserved for the FINAL BLESSED table a later plan copies in at run end (RESEARCH Sec3), and rewriting a multi-MB table there every checkpoint_every episodes would churn OneDrive on every interval (D-22); checkpoint_every/pool_snapshot_every read as global (both-roles) cadences, curve_log_every reads per-role, matching each cadence's own purpose (crash recovery/anti-collapse vs. per-role learning curves, D-25); winrate_vs_baseline is scoped to opponent_kind=="heuristic" episodes specifically so the column means what its name says
- [Phase 03-08]: Deviation (Rule 3 - blocking, repeat of 03-05/06/07) -- run_training's setup/orchestration split into training/loop.py (episode-loop orchestration) + loop_setup.py (once-per-run resume/checkpoint/pool-build/Windows-guard helpers) + progress.py (pure mutable bookkeeping) + run_config.py (shared TrainingRunConfig/RunResult, breaking a would-be import cycle) at the 150-line gate. Deviation (Rule 2 - missing coverage) -- added a direct test for harness.py's previously-uncovered _role_won(role, None) branch, closing it to 100%
- [Phase 03-09]: final_slope(rows, role, window) returns a total win-rate drift over the trailing window (least-squares regression rate x window span), not a raw per-episode rate -- makes it directly comparable to convergence_tolerance (a win-rate delta, 0.02), since a 0.02-per-episode bound would be nonsensical over a 20000-episode window; numerically verified against three synthetic curves before implementation
- [Phase 03-09]: training/curve_analysis.py split out of plot_curves.py at the 150-line gate (QUAL-08), the exact contingency the plan's own text named; plot_curves.py re-exports the analysis names so `training.plot_curves` still satisfies the plan's literal decile_gain/final_slope/check_convergence spec, and stays the repo's only matplotlib importer (D-20, verified repo-wide, not just src/)
- [Phase 03-09]: Deviation (Rule 3 - blocking) -- the plan's literal `uv run python training/plot_curves.py <csv> <outdir>` invocation failed (direct-path execution puts training/ on sys.path[0], not the repo root); fixed with a guarded sys.path bootstrap gated on `__package__ in (None, "")`, regression-tested via a subprocess pytest test
- [Phase 03-09]: README.md did not exist anywhere in the repo before this plan (confirmed via git log); created it now with a project overview borrowing .planning/PROJECT.md's framing, plus the mandatory rule-42 learning-curves section; every figure and measured win-rate is explicitly marked "pending (03-10)" since no training run has executed yet -- zero fabricated numbers, only configured bars (win_rate_margin/eval_games/seed/etc.) read from config/police/strategy.json
- [Phase 03-10]: Held-out eval seeds (D-23) are asserted disjoint from training seeds by an executable check (assert_seeds_held_out), not a comment -- this is the one assumption that, if silently wrong, makes the whole GATE-4 number meaningless (the heuristic is both sparring partner and eval opponent, so training-set contamination would let a table "beat" the baseline on positions it already trained against); the win-rate margin is compared against the measured heuristic-vs-heuristic baseline per role, never an assumed 50%, since the game is not role-symmetric
- [Phase 03-10]: test_beats_baseline.py's GATE-4 test SKIPS (not passes, not xfails) with a stated reason while no trained table exists -- a green GATE-4 that never loaded a table would be the single worst outcome for the phase's central claim; the skip is intentionally left for Task 4 (the human operator's training run) to close, never faked or bypassed by the automated executor
- [Phase 03-10]: 03-10 Task 4 (`checkpoint:human-action gate="blocking"`) was executed only through Tasks 1-3 in this automated run; Task 4 itself -- the overnight training run, GATE-4 measurement, and table promotion -- was deliberately left untouched per the phase's own design (it needs a human watching a real Windows machine for console QuickEdit suspension, OneDrive/Defender interference, and sleep). No qtable file, no README number, and no 03-10-SUMMARY.md exist yet as a direct, verified consequence

- [Phase 03-10 post-mortem]: **T4-followup-1 and T4-followup-2 are WITHDRAWN, both premises measured false.** The cop was not undertrained (0.900 training win rate); it was evaluated on states it never trained on. The thief's `fallback_rate` collapse was a symptom; the cause is that it never receives a capture update at all
- [Phase 03-10 post-mortem]: **Distance is the wrong objective for both roles.** cop-win ⟺ the thief's free component is a forest; the cop destroys cycles and the thief preserves one. Both current brains optimise BFS distance, and the cop's barrier rule (max distance to a fixed corner anchor) has no literature support
- [Phase 03-10 post-mortem]: **RL is demoted from "the strategy" to "weight tuning"** — alpha-beta over a cycle-based evaluation is the policy; ~60 weights replace a 1.7M-entry table. Reverses the init-time framing of tabular Q-learning as the strategy, without changing the phase breakdown
- [Phase 03-10 post-mortem]: **γ must differ by role** — cop 0.99 (discounting IS its capture-sooner incentive), thief 1.0 (discounting attenuates its only good outcome). Terminal rewards come from the real scoring table (cop 20/5, thief 10/5), reversing `docs/PRD_rl_strategy.md` §4's decision to hand-tune symmetric 1.0/1.0 with no capture penalty — that decision is the direct origin of the degenerate thief
- [Phase 03-10 post-mortem]: `min_win_rate_absolute = 0.55` is **ours (D-14, `docs/PRD_rl_strategy.md` §8), not a Segal fixed value** — it appears nowhere in `docs/PARAMETERS.md`. Re-arguable on evidence; must not be moved merely because a run failed
- [Phase 03-10 post-mortem]: Subagent output is **not** taken at face value — the algorithms researcher's headline depth benchmark failed independent replication against the real engine, and an earlier cop-number attribution in this session was wrong and is corrected in `last_activity`

- [Phase 03-11]: No new decisions -- every contract (adjacency-equivalence proof, the
  never-raise convention for out-of-set cells, `cycle_rank`'s connected-only
  precondition, `voronoi_split`'s neither-side tie rule) was already fully specified by
  the plan and the cited research doc. One implementation note worth recording:
  `voronoi_split` advances both source frontiers one BFS layer per round inside a
  single loop rather than running two independently-timed BFS passes and comparing
  distances afterward, so "reached on the same round" is the literal definition of a tie

- [Phase 03-11]: STATE.md's own YAML frontmatter does not parse (`yaml.safe_load`
  raises `ScannerError`, confirmed pre-existing on `HEAD` before this session touched
  the file) -- long unquoted plain scalars containing natural-language colons break
  YAML's plain-scalar grammar. ~85 occurrences repo-wide; full fix is out of scope for
  a single plan (would mean reformatting the whole historical narrative). Logged in
  Deferred Items, not fixed, per the deviation rules' scope boundary

- [Phase 03-12]: No new decisions beyond what D-31 and the plan already specified. Two
  implementation notes worth recording: (1) the two-arm regression test differs ONLY by
  monkeypatching `fallback.safe_moves` (real spy vs a no-op) inside `monkeypatch.context()`
  blocks against the production call site, rather than adding a production toggle
  parameter to `_evade`/`pick` just for testability; (2) the plan's own ~100ms/game
  timing assumption did not reproduce (measured ~34-38s for the 160-game suite,
  cProfile-traced to 03-07's pre-existing `choose_barrier`, not this plan's code) --
  recorded honestly in the test module's docstring rather than shrinking `n=60` or
  disabling barrier placement to hit the stale target

- [Phase 03-13]: Every seeded value is labelled by provenance in 03-13-SUMMARY.md
  (measured / sourced / engineering default), none claimed as a PARAMETERS.md value:
  `search_depth_cap=5` is D-26's own measured real-engine figure; `min_distinct_starts`,
  `terminal_spread_min/ratio_max`, `floor_episode_fraction_max` are copied verbatim from
  `TRAINING-METHODOLOGY.md` SF.3; `pfsp_exponent=1.0` follows AlphaStar's
  `f_var(x)=x(1-x)` but the exact exponent is flagged secondary-sourced only; the four
  `barrier_weight_*` values fix only the strict ordering `cycle_rank > component_size >
  territory > distance`, magnitudes are 03-21's to set. `docs/PRD_rl_strategy.md` Sec2
  and `training/harness.py`'s docstring both still reference the deleted `turn_bucket`
  by name -- left untouched deliberately (03-22's and 03-14's files respectively, per
  outline SS7 file-ownership), flagged for the owning plan to correct in passing

- [Phase 04-09]: D-51 implemented as a literal DISCLOSED REVISION of D-40, not an
  extension: `belief.json`'s `hint_likelihood.weight` (fixed, validated below
  `scent_likelihood.weight` by name) and `reliability.prior` (the adaptive
  coefficient's starting point) are two INDEPENDENT config fields, not the same
  number reused twice -- resolves an ambiguous reading in 04-09-PLAN.md's own
  prose, documented in 04-09-SUMMARY.md's Decisions Made for 04-13 to carry into
  `PRD_belief_map.md`/`RULES-RESOLUTION-LANG.md`. `strategy/scent_check.py::contradicts()`
  reproduces the book's Sec4.4 worked example (0.9 -> 0.81) exactly;
  `strategy/reliability.py::Reliability.observe()` is measured to settle EXACTLY at
  `r_min`/`prior` under 1000 extreme observations, not just bounded;
  `strategy/belief_hint.py::hint_likelihood()` returns an all-zero grid at
  confidence=0 specifically so `BeliefMap.update()`'s own zero-guard buys an EXACT
  (not approx) no-op for `NO_EVIDENCE`, per the plan's own stricter verify wording

### Pending Todos

- 03-13..03-16 in `docs/phases/phase-3/TODO.md` (pre-flight assertions, cycle-based eval +
  alpha-beta, barrier rewrite, run-2 config, exact `turns_remaining` -- 03-11/03-12/03-13's
  rows are now code-complete, still unticked pending 03-24's reconciliation pass)

- Two subagent correction passes were cut off by API limits and never finished: re-measure the
  alpha-beta depth table against the real engine, and pin exact page/section for the Bansal
  δ-uniform ablation numbers and the ε-floor figures. Until then those specific numbers in
  `ALG-COMPARISON.md` and `TRAINING-METHODOLOGY.md` are UNVERIFIED — the qualitative findings
  and the independently-checked citations stand

### Blockers/Concerns

- ~~Team code (SUB-06)~~ **Decided: `khm-mn17`** (08-CONTEXT.md); per-game config naming still a league prerequisite
- Reporting (REPORT-01) is submission-critical: a missing/contradictory report zeroes both teams
- League opponents must be contacted early (this week) — scored games realistically Aug 11–12 post-exam

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Tooling correctness (pre-existing, out of scope for 03-11) | This file's YAML frontmatter does not actually parse (`yaml.safe_load` on `.planning/STATE.md`'s frontmatter raises `ScannerError: mapping values are not allowed here`) — the narrative fields (`stopped_at`, `last_activity`) are long unquoted plain scalars containing many `word: word` sequences, and a bare `: ` inside a plain YAML scalar always terminates it. Confirmed pre-existing: `git show HEAD:.planning/STATE.md` (the commit before this session touched the file) already fails the same way. ~85 colon-space occurrences repo-wide in this file make a full fix (block-scalar or quoted-string conversion of every long field) out of scope for a single plan's execution — it would mean rewriting the whole historical narrative's formatting. Consistent with this file's own established note ("`gsd-tools.cjs state advance-plan`/`update-progress` are NOT used on this file — hand-authored"), no tooling in this project currently parses this frontmatter as YAML, so the impact today is cosmetic/latent, not functional. One trivial, in-place instance was fixed while editing this session's own `stopped_at` text (`` `autonomous: false` `` → `` `autonomous=false` ``); no other pre-existing instance was touched. | ☐ open, latent (not blocking) | 2026-08-04, discovered during 03-11's STATE.md update |

## Session Continuity — READ THIS FIRST

**Next command: `/gsd:execute-phase 3`** (resumes at 03-13 — 03-11 and 03-12 are done and
committed). If the SessionStart banner reports the graph STALE, run
`graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/`
first, per CLAUDE.md (this session already did so after 03-12 landed: 3523 nodes/6406
edges/233 communities). **Do not run `/gsd:verify-work 3`** — GATE-4 stays unmet until
03-25 (the wave-7 human-operator checkpoint) remeasures it. **Do not run another training
job** until 03-13's pre-flight assertions are in place — 03-13 is next, not skippable.

Wave 1 status: 03-11 (graph primitives) and 03-12 (thief safety rule) done. 03-13
(turns_remaining + config surface), 03-14 (terminal signal) remain to finish wave 1.
Each subsequent execute-phase invocation should just pick up the next undone plan file
under `.planning/phases/03-blind-strategy-module-rl-policy/03-1[3-9]-PLAN.md` /
`03-2[0-5]-PLAN.md` in order — no further reading of the planning inputs below is needed,
they were only for authoring the 15 plans, which is already done.

Inputs the planner read before writing 03-11..03-25 (kept for reference, not re-reading
needed during execution):

| Document | What it settles |
|---|---|
| `docs/phases/phase-3/RUN-1-POSTMORTEM.md` | Why GATE-4 failed, measured; withdraws T4-followup-1/2 |
| `docs/research/PURSUIT-AND-EVASION-STRATEGY.md` | Thief design; cop-win ⟺ forest; barrier placement rules |
| `docs/research/TRAINING-METHODOLOGY.md` | Per-role γ, rewards, start states, self-play, pre-flight checks |
| `docs/research/ALG-COMPARISON.md` | Algorithm per role, features, state representation |

**Design decision that session changed:** RL is demoted from "the strategy" to "tuning ~60
evaluation weights". Strength comes from alpha-beta search over a cycle-based evaluation
(D-26) — 03-11's `pursuit.strategy.graph` package (this session) is the measurement layer
that evaluation is built on. This does NOT re-derive the phase breakdown (CLAUDE.md) — it
is still Phase 3, stage 3 of the book's seven.

**Uncommitted at session end:** `training/eval_aggregate.py` + edits to
`eval_stats.py`/`eval_report.py`/`evaluate.py` and two test files (the T4-followup-3
eval-honesty fix, tests green: 97 passed / 1 skipped); the four new docs above;
`.planning/phases/02-fastmcp-infrastructure/02-UAT.md`; `.pytest-tmp/` (scratch, should be
gitignored — it is the only `ruff` hit in the tree).

**Carried forward unchanged:** Phase-01 code review CR-01 still deferred; Phase-2 verify-work
(docs/phases/phase-2/TODO.md row 2-99 + root docs/TODO.md) still pending.

---

Last session: 2026-08-01T22:10:00+03:00
Stopped at: Completed 03-10-PLAN.md Tasks 1-3 (`tests/integration/{test_shortest_path,
  test_policy_fallback,test_strategy_pluggable,test_beats_baseline}.py`,
  `scripts/check_no_llm_in_strategy.{py,sh}`, `training/evaluate.py` +
  `training/eval_{scenarios,arms,stats,report}.py`, `artifacts/eval_scenarios.json`, and the
  STRAT-01..07 coverage audit in `docs/phases/phase-3/TODO.md` -- the §10.4 GATE-1/2/3
  integration tests, the GATE-4 evaluation CLI and committed eval scenario set, and the
  phase-wide requirements-coverage audit, STRAT-01..07). **Task 4 (blocking human-action
  checkpoint) intentionally NOT executed** — it is the overnight training run, and this
  automated session correctly stopped rather than attempting it. No SUMMARY.md exists for
  03-10 because the plan is genuinely incomplete.
  Carried forward: Phase-01 code review CR-01 still deferred; Phase-2 verify-work
  (docs/phases/phase-2/TODO.md row 2-99 + root docs/TODO.md) still pending — Phase 3
  planning/execution proceeded ahead of it per this session's instructions.
  docs/phases/phase-3/TODO.md rows 03-00..03-09 ticked, 03-10 row marked in-progress with
  Task 4 called out as the remaining blocker, plus 3 new unticked operator-step rows from
  03-RESEARCH.md Sec3; 03-96, 03-99 remain untouched (03-99 is /gsd:verify-work 3's job).
Resume file: None — Tasks 1-3 are fully committed (3 task commits: 1dea409, 8c8471f,
  b15d033) but 03-10 as a PLAN is not done. **Next step is the human operator running 03-10
  Task 4** (see docs/phases/phase-3/TODO.md's new operator-step rows, or
  03-10-PLAN.md's Task 4 block, for the exact commands and Windows setup: redirect output to
  a file since console QuickEdit suspends the process on click, confirm
  training.artifacts_dir resolves outside OneDrive, exclude that directory from Defender
  real-time scanning, confirm sleep is disabled, then `uv run python -m training.loop
  2>&1 | tee run.log`, inspect curves via `training/plot_curves.py`, measure the gate via
  `uv run python training/evaluate.py --full --assert-gate`, and only on a pass promote the
  tables + fill README's placeholder numbers). Once that lands, either re-run
  /gsd:execute-phase 3 to have it write 03-10-SUMMARY.md and close the phase, or write the
  SUMMARY directly — either closes out Phase 3's final plan.
  **Post-session fix (commit 89ddcbb)**: the operator tried
  `uv run python -m training.harness` per 03-10-PLAN.md's literal Task 4 text and it exited
  immediately doing nothing -- 03-08 built `run_training()` (in `training/loop.py`, not
  `harness.py`) but never wired a runnable entry point to it anywhere in `training/`.
  Added `main()`/`_load_run_config()` to `training/loop.py` (not `harness.py`, to avoid a
  circular import since `loop.py` already imports from `harness.py`); the real command is
  `uv run python -m training.loop`. Verified with a 6-episode run in an isolated temp dir
  before adding `tests/unit/training/test_loop.py::test_load_run_config_reads_the_real_
  committed_config_files` and `::test_main_runs_training_via_load_run_config_and_prints_
  the_final_episode` (the latter mocks only `run_training` itself, so `_load_run_config`'s
  real config-file resolution stays covered). `docs/phases/phase-3/TODO.md`'s op-1 row
  corrected to match. Full gates re-verified green after the fix: ruff 0, line-limit clean,
  427 passed / 2 skipped, coverage 96.43%.
  Per-day sequence from Phase 3 on: /gsd:graphify → [/gsd:ai-integration-phase N for 3 & 4]
  → /gsd:plan-phase N --chunked → /gsd:execute-phase N → /gsd:verify-work N. Note: the
  CLAUDE.md-mandated graphify refresh for this plan's new code already ran this session
  (graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md}
  .planning/graphs/) -- 3190 nodes / 5849 edges / 201 communities, GRAPH_REPORT.md committed
  alongside the Task-3 docs commit.
  Note on tooling: per 03-03's finding, `gsd-tools.cjs state advance-plan`/`update-progress`
  are NOT used on this file -- this update was hand-authored, matching the established
  per-plan narrative format.

---

Last session: 2026-08-04T12:31:00+03:00
Stopped at: Completed 03-11-PLAN.md (graph primitives, run-2 wave 1's first plan) in
  full. All 3 tasks executed TDD (tests written and confirmed red before each
  implementation went green), each committed atomically: Task 1 `components.py`
  (`12be2e4`), Task 2 `cycles.py` (`52c85f2`), Task 3 `territory.py` (`b4b06fa`). A
  4th commit (`af5f0de`) closed a Rule-2 coverage gap found during final verification
  (two documented contract branches -- the DFS-root cut-vertex case and
  `cycle_rank(frozenset())==0` -- had no direct test; 2 tests added, package coverage
  98%->100%). `03-11-SUMMARY.md` written. Full repo gates green: `ruff check .` 0
  violations, line-limit clean (new files 100/37/55/32 code lines), 456 passed / 2
  skipped (the pre-existing GATE-4 skip, untouched), coverage 97.05% (>=85% floor).
  Graphify rebuilt and `GRAPH_REPORT.md` refreshed (3457 nodes/6273 edges/234
  communities). `docs/phases/phase-3/TODO.md` deliberately not touched -- its
  03-11..03-16 row numbering predates the 15-plan wave breakdown and reconciling it is
  03-24's ("triplet refresh") explicit job.
Resume file: None -- 03-11 is fully committed and closed. **Next step is
  `/gsd:execute-phase 3`**, which resumes at **03-12** (thief safety rule — never step
  into `N[cop]`; see `.planning/phases/03-blind-strategy-module-rl-policy/03-12-PLAN.md`).
  Waves 1-6 remain autonomous; wave 7 (`03-25`) is the human-operator checkpoint (the
  overnight training run and the real GATE-4 remeasurement) -- do not run
  `/gsd:verify-work 3` before it passes.

---

Last session: 2026-08-04T13:00:00+03:00
Stopped at: Completed 03-12-PLAN.md (thief safety rule -- never step into N[cop], run-2
  wave 1's second plan) in full. Both tasks committed atomically: Task 1 `safety.py`
  (`71b201d`, test-first: `test_safety.py` confirmed red against a `ModuleNotFoundError`
  before the module existed, green after -- 7 unit tests), Task 2 wiring + regression
  guard (`20d87f6`). `src/pursuit/strategy/safety.py` -- `closed_neighbourhood`/
  `safe_moves`, pure (D-03), never-empty guarantee, docstring carries the full D-31
  296/300=0.987 vs 283/300=0.943 provenance plus the unsoftened "did not fully
  reproduce, lost 3/20, flawed control" caveat. `fallback.py::_evade` filters legal
  moves through `safe_moves` before ranking with the UNCHANGED
  `(unreachable?, distance, onward)` key -- filter-then-rank, `_pursue` byte-identical.
  `tests/unit/strategy/test_fallback.py` needed zero changes (verified before/after,
  all 6 cases hold under the filtered behaviour). New
  `tests/integration/test_thief_safety.py`: non-vacuous 160-game regression guard, two
  arms differing ONLY by `monkeypatch.context()`-scoped patches of `fallback.safe_moves`
  (real spy vs no-op) against the same 20 committed GATE-4 scenarios + 60 seeded random
  starts (`n=60`, `REGRESSION_TOLERANCE=0.05`, `seed=314159`, named test-local
  constants, D-19); asserts grid filtered-survival >= unfiltered, random-start rate
  within one noise band, filter-bound counter > 0 (non-vacuous), and the per-turn
  N[cop] invariant across all 160 games via a spy wrapper. Does not reproduce D-31's
  own flawed disabled-barrier control. `03-12-SUMMARY.md` written (self-check PASSED).
  One deviation, a documentation correction (not a code fix): the plan's own
  ~100ms/game timing estimate did not reproduce -- measured ~34-38s for the 160-game
  suite, `cProfile`-traced to 03-07's pre-existing `choose_barrier` (out of this plan's
  scope), not this plan's own code. Recorded honestly in the test module's own
  docstring; `n=60` was NOT reduced and barrier placement was NOT disabled to chase the
  stale target. Full repo gates green: `ruff check .` 0 violations, line-limit clean
  (new files 50/76/157 code lines, `fallback.py` still well inside its own ceiling),
  464 passed / 2 skipped (same 2 pre-existing skips as 03-11), coverage 97.95%
  (>=85% floor), `safety.py`/`fallback.py` both individually 100% covered. Full-repo
  `--cov` run took 7m47s on this Windows machine, confirmed genuinely CPU-bound
  throughout (`Get-Process ... CPU`), not the known Windows stdio-hang pattern.
  Graphify rebuilt (3523 nodes/6406 edges/233 communities) and `GRAPH_REPORT.md`
  refreshed and committed. `docs/phases/phase-3/TODO.md` deliberately not touched --
  same rationale as 03-11 (03-24's "triplet refresh" job).
Resume file: None -- 03-12 is fully committed and closed. **Next step is
  `/gsd:execute-phase 3`**, which resumes at **03-13** (turns_remaining + config
  surface; see `.planning/phases/03-blind-strategy-module-rl-policy/03-13-PLAN.md`).
  Waves 1-6 remain autonomous; wave 7 (`03-25`) is the human-operator checkpoint (the
  overnight training run and the real GATE-4 remeasurement) -- do not run
  `/gsd:verify-work 3` before it passes.
  Note on tooling: per 03-03's finding and 03-11's precedent, `gsd-tools.cjs state
  advance-plan`/`update-progress` are NOT used on this file -- this update was
  hand-authored, matching the established per-plan narrative format.
