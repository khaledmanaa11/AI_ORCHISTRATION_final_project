---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 03 — plan 03-09 executed (learning-curve reader-side E6 convergence checks + matplotlib plotting CLI + rule-42 README section, STRAT-06); 1 more Phase-3 plan remains (03-10)
last_updated: "2026-08-01T20:44:00+03:00"
last_activity: 2026-08-01 -- Executed 03-09-PLAN.md in full (2 tasks, both committed individually). Task 1 added training/curve_analysis.py -- decile_gain/final_slope/check_convergence reading training/curves.py's CSV schema (that writer verified untouched via git diff across both commits, QUAL-02); thresholds come from StrategyParams (win_rate_margin/convergence_window/convergence_tolerance), zero literals; verdicts are per-role (D-25), proven via three synthetic curves (rising-then-flat converges, flat-noise fails only the decile check, still-climbing fails only the slope check) numerically pre-verified before writing the implementation. Task 2 added training/plot_curves.py -- the repo's only matplotlib importer (D-20, confirmed via a repo-wide grep, not just src/): per-role win-rate-vs-baseline PNGs with epsilon on a secondary axis, plus a shared mean-reward PNG with a separately labelled line per role (never averaged). Created README.md (did not exist anywhere in the repo before this plan -- confirmed via git log) with the rule-42 learning-curves section: states the configured win_rate_margin/min_win_rate_absolute/eval_games/convergence_window/convergence_tolerance/episodes/seed from config/police/strategy.json, with every figure and measured win-rate explicitly marked "pending (03-10)" since no training run has executed yet -- zero fabricated numbers. Deviations (both Rule 3 - blocking): (1) the plan's literal `uv run python training/plot_curves.py <csv> <outdir>` invocation failed with ModuleNotFoundError because direct-path script execution puts training/ itself on sys.path[0], not the repo root -- fixed with a guarded sys.path bootstrap (gated on __package__ in (None, "")) and regression-tested via a subprocess test; (2) proactively split the E6 analysis functions into training/curve_analysis.py (matplotlib-free) rather than one plot_curves.py file, the exact contingency the plan named for the 150-line gate (QUAL-08) -- plot_curves.py re-exports the analysis names so training.plot_curves still satisfies the plan's literal spec. Full repo gates green: ruff 0, line-limit clean, 355 tests passed / 1 skipped, coverage 96.94% overall (curve_analysis.py 94%, plot_curves.py 97%). Graphify graph rebuilt (2996 nodes/5239 edges/194 communities) and GRAPH_REPORT.md refreshed. docs/phases/phase-3/TODO.md row 03-09 updated.
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 27
  completed_plans: 26
  percent: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-27)

**Core value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.
**Current focus:** Phase 03 — blind-strategy-module-rl-policy (Phases 01-02 code complete; Phase 03 plan 08 of 11 executed)

## Current Position

Phase: 03 (blind-strategy-module-rl-policy) — EXECUTING (plan 03-09 of 11 done)
Plan: 10 of 11 executed (03-00, 03-01, 03-02, 03-03, 03-04, 03-05, 03-06, 03-07, 03-08, 03-09
  done; 03-10 remains). Next plan is 03-10 (§10.4 gate tests + coverage audit + the real
  overnight training run).
Status: Phase 1 of 8 done, Phase 2's code plans all executed (verify-work 2 still pending),
  Phase 3's config scaffold (03-00), per-mechanism PRD (03-01), strategy seam (03-02), the
  barrier-aware BFS distance oracle (03-03), the Bayes prior + BFS fallback +
  `HeuristicBrain` baseline (03-04), the canonical state-key encoding + JSON `QTable`
  (03-05), `QLearningBrain` (03-06), the cop barrier sub-policy `choose_barrier` wired into
  both brains (03-07), the offline training harness (03-08), and the E6 convergence checks +
  matplotlib plotting CLI + rule-42 README section (03-09) -- all landed. `training/` can now
  produce a trained Q-table AND turn its curve CSV into rendered PNGs and a pass/fail
  convergence verdict; only the phase-gate audit and the actual overnight run (03-10) remain
  to close Phase 3. 5 phases remain after Phase 3 closes. Next: /gsd:execute-phase 3 to
  continue with 03-10.
Last activity: 2026-08-01 -- Executed 03-09-PLAN.md in full (learning curves + plotting +
  README section, STRAT-06). Task 1 added `training/curve_analysis.py` --
  `decile_gain`/`final_slope`/`check_convergence` reading `training/curves.py`'s CSV schema
  without touching that writer (verified via `git diff` showing zero change across both
  commits, QUAL-02); thresholds sourced from `StrategyParams`
  (`win_rate_margin`/`convergence_window`/`convergence_tolerance`), zero literals; verdicts
  computed per role (D-25), proven via three synthetic curves (rising-then-flat converges,
  flat-noise fails only the decile-gain check, still-climbing fails only the slope check --
  each numerically pre-verified before the implementation was written). Task 2 added
  `training/plot_curves.py` -- confirmed the repo's only matplotlib importer via a
  repo-wide grep (not just `src/`): per-role win-rate-vs-baseline PNGs with the epsilon
  schedule on a secondary axis, plus one shared mean-reward PNG carrying a separately
  labelled line per role, never averaged (D-25). Created `README.md`, which did not exist
  anywhere in the repo before this plan (confirmed via `git log --all -- README.md`
  returning nothing) -- borrowed `.planning/PROJECT.md`'s framing for the top matter, then
  added the mandatory rule-42 learning-curves section stating the configured
  `win_rate_margin` (0.10) / `min_win_rate_absolute` (0.55) / `eval_games` (200 = 20
  scenarios x 10 seeds) / `convergence_window`+`convergence_tolerance` (20000/0.02) /
  `episodes` (300000) / `seed` (1337) from `config/police/strategy.json`, with every figure
  and every measured win-rate explicitly marked "pending (03-10)" -- zero fabricated
  numbers, per the plan's own hard requirement. Deviations (both Rule 3 - blocking): (1) the
  plan's literal `uv run python training/plot_curves.py <csv> <outdir>` invocation failed
  with `ModuleNotFoundError: No module named 'training'` -- direct-path script execution
  puts `training/` itself on `sys.path[0]`, not the repo root, so the module's
  `from training.curve_analysis import ...` absolute import could not resolve (`-m
  training.plot_curves` and pytest's own imports were unaffected). Fixed with a guarded
  `sys.path.insert(...)` gated on `__package__ in (None, "")`, regression-tested via a
  subprocess-based pytest test so the literal CLI form stays covered. (2) Proactively split
  the E6 analysis functions into `training/curve_analysis.py` (matplotlib-free) rather than
  packing them into `plot_curves.py` -- the exact contingency the plan's own text named for
  the 150-line gate (QUAL-08); `plot_curves.py` re-exports the analysis names so
  `training.plot_curves` still satisfies the plan's literal function-location spec, and the
  E6 tests stayed in `tests/unit/training/test_curves.py` per the plan's explicit
  instruction while the new rendering-only tests got their own `test_plot_curves.py`. Full
  repo gates green: `ruff check .` 0 violations, line-limit clean, 355 tests passed / 1
  skipped, coverage 96.94% overall (`curve_analysis.py` 94%, `plot_curves.py` 97%). Graphify
  graph rebuilt (2996 nodes/5239 edges/194 communities) and `GRAPH_REPORT.md` refreshed.
  `docs/phases/phase-3/TODO.md` row 03-09 updated.

Progress: [█░░░░░░░░░] 13%  (1 of 8 phases; Phase 2 code complete pending verify-work;
  Phase 3 plan 10 of 11 executed)

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

Last session: 2026-08-01T20:44:00+03:00
Stopped at: Completed 03-09-PLAN.md (`training/curve_analysis.py` + `training/plot_curves.py`
  + `README.md` + their tests -- the E6 convergence checks, the matplotlib plotting CLI, and
  the rule-42 README learning-curves section, STRAT-06). Task 1: `decile_gain`/
  `final_slope`/`check_convergence` in the new `training/curve_analysis.py`, reading
  `training/curves.py`'s CSV without touching that writer (QUAL-02), verdicts per role
  (D-25), thresholds sourced from `StrategyParams`. Task 2: `training/plot_curves.py`
  renders per-role win-rate PNGs (epsilon on a secondary axis) plus a shared mean-reward
  PNG, and is the repo's only matplotlib importer (D-20); `README.md` created (did not
  exist before) with the rule-42 section carrying configured-not-measured numbers and
  "pending (03-10)" placeholders for every figure and measured win-rate. SUMMARY at
  .planning/phases/03-blind-strategy-module-rl-policy/03-09-SUMMARY.md, including the
  final_slope-as-total-drift decision, the curve_analysis.py/plot_curves.py 150-line-gate
  split, the sys.path-bootstrap fix for direct-path CLI execution, and the README-did-not-
  exist finding.
  Carried forward: Phase-01 code review CR-01 still deferred; Phase-2 verify-work
  (docs/phases/phase-2/TODO.md row 2-99 + root docs/TODO.md) still pending — Phase 3
  planning/execution proceeded ahead of it per this session's instructions.
  docs/phases/phase-3/TODO.md rows 03-00..03-09 ticked; rows 03-10, 03-96, 03-99 remain.
Resume file: None — 03-09 is fully committed (2 task commits + this docs/SUMMARY/STATE
  commit). Next step is /gsd:execute-phase 3 to continue with 03-10 (§10.4 gate tests +
  coverage audit + the actual overnight training run, the final Phase-3 plan) — once that
  run completes, `training/plot_curves.py` and `training/curve_analysis.check_convergence`
  are ready to fill README.md's "pending (03-10)" placeholders with the real PNGs and
  measured win-rate/convergence numbers. Per-day sequence from Phase 3 on:
  /gsd:graphify → [/gsd:ai-integration-phase N for 3 & 4] → /gsd:plan-phase N --chunked →
  /gsd:execute-phase N → /gsd:verify-work N. Note: the CLAUDE.md-mandated graphify
  refresh for this plan's new code already ran this session (graphify update . && cp
  graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/) -- 2996 nodes /
  5239 edges / 194 communities, GRAPH_REPORT.md committed alongside this plan's docs commit.
  Note on tooling: per 03-03's finding, `gsd-tools.cjs state advance-plan`/`update-progress`
  are NOT used on this file -- this update was hand-authored, matching the established
  per-plan narrative format.
