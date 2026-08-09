---
phase: 04-language-and-scent
plan: "12"
subsystem: network
tags: [turn-pipeline, figure-7, language-turn, belief-adapter, hint-buffering, d-48, d-33, d-53]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plan 04-02)
    provides: "handshake carries an optional local_scent_digest keyword (D-46, rule 23)"
  - phase: 04-language-and-scent (plan 04-04)
    provides: "direction-token move codec, MessageType.HINT, the hint buffer + PLACEHOLDER_HINT_TEXT scaffolding this plan replaces outright"
  - phase: 04-language-and-scent (plan 04-10)
    provides: "bluff.compose()/BluffContext, HintBank, the language.json model.hint_word_limit config home"
  - phase: 04-language-and-scent (plan 04-11)
    provides: "BeliefAdapter.decide() (Figure-7 belief order internally), registry.build_brain(..., belief_config=, scent_model=)"
provides:
  - "services/language_turn.py: decode_incoming/compose_outgoing, the ONE timeout-guarded entry point for the language half of a turn"
  - "network/turn_actions.py wired in Figure 7 order: decode -> choose (belief-aware) -> resolve -> send move -> plan deception (after the move) -> compose -> send hint"
  - "D-48's regime decision (known_opponent_cell) in one place, logged per turn"
  - "agent_lifecycle.default_context now builds a REAL registry brain, ScentField and LanguageRuntime for every live game -- the first plan to wire Phase 3/4's strategy into the actual network turn loop"
  - "turn_events.language_turn_record: the full per-turn language channel snapshot (regime, belief entropy/argmax, reliability, token spend, incoming/outgoing hint)"
  - "The live handshake now sends a real local_scent_digest (closes the still-open half of 04-02's carry-over 1)"
affects: [04-13-docs-and-rules-resolution, 04-14-gate-4-measurement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional hint-sending: AgentContext.brain/scent_field/language default to None so every pre-existing bare test fixture is unaffected (move-only turns); every REAL game (agent_lifecycle.default_context) always wires all three, so LANG-01 holds for actual play"
    - "known_cell computed ONCE per take_my_turn call, before record_action/maybe_resolve can mutate the state it depends on, then threaded explicitly into both the move decision and the JSONL regime field -- never recomputed after resolution may have already fired"
    - "A dedicated turn_language.py (pure/sync) + turn_language_io.py (the two awaited stages) split, mirroring turn_resolve.py/turn_buffer.py's own split -- turn_actions.py stays the orchestration skeleton, never the place new logic accretes"
    - "Hint buffering is now failure-tolerant on BOTH timing axes: a late hint (already-resolved turn) is silently dropped, a second not-yet-consumed hint from the same sender overwrites rather than raising -- only await_move's separate 'two hints, no move' liveness cap still raises"

key-files:
  created:
    - src/pursuit/services/language_turn.py
    - src/pursuit/network/language_wiring.py
    - src/pursuit/network/brain_wiring.py
    - src/pursuit/network/turn_language.py
    - src/pursuit/network/turn_language_io.py
    - src/pursuit/network/turn_resolve.py
    - tests/unit/services/test_language_turn.py
    - tests/unit/test_language_wiring.py
    - tests/unit/test_turn_language.py
    - tests/integration/two_peer_game.py
    - tests/integration/test_language_pipeline.py
    - tests/integration/test_llm_degradation.py
    - tests/integration/test_language_timing.py
  modified:
    - src/pursuit/network/turn_actions.py
    - src/pursuit/network/turn_buffer.py
    - src/pursuit/network/orchestrator.py
    - src/pursuit/network/agent_wiring.py
    - src/pursuit/network/agent_lifecycle.py
    - src/pursuit/network/turn_events.py
    - tests/unit/test_orchestrator.py
    - tests/unit/test_orchestrator_loop.py
    - tests/unit/test_turn_buffer.py
    - tests/unit/test_agent_lifecycle.py
    - tests/integration/test_turn_lifecycle.py
    - tests/integration/test_game_loop.py

key-decisions:
  - "Hint-sending is CONDITIONAL on ctx.language (None -> move-only, matching pre-04-04 mechanics for bare test fixtures); every real game always wires it. This is a deliberate, documented departure from 04-04's UNCONDITIONAL placeholder, needed because sending a real hint now requires a real LanguageRuntime, and forcing every unit-test fixture to build one would be a disproportionate cost for tests that are not testing the language channel."
  - "[Rule 1 - Bug] record_hint's 'late hint' and 'duplicate hint' checks (04-04's own design) both raised HintProtocolError, ending the game as a spurious TECHNICAL_LOSS. A REAL two-peer concurrent game (never exercised before this plan -- prior tests only drove one real turn loop against injected envelopes) measurably hits both timing patterns, since the move and the hint are now two genuinely independent, variable-latency round-trips. Fixed: late drops silently, a second hint from the same sender overwrites. Only await_move's own separate 'two hints, no move' liveness cap still raises."
  - "known_cell (D-48's regime signal) is computed ONCE, early in take_my_turn, and threaded explicitly into both the move decision and the JSONL log -- record_action/maybe_resolve mutate state that known_opponent_cell reads, so recomputing it after resolution could silently answer a different question than the one the move was actually chosen under."
  - "Deception's belief map falls back to a FRESH, unbiased BeliefMap when ctx.brain is not a BeliefAdapter (belief disabled, or no brain wired at all) -- LANG-01 requires a hint every turn regardless of belief.enabled; the fallback only affects the DECEPTION claim's danger/herding modulation, never movement."
  - "local_scent_digest is now passed for real on the live path (agent_lifecycle.default_context's responder AND run_agent's outbound perform_handshake call) but the parameter itself stays optional -- 04-02's other, still-open half of carry-over 1 ('consider making it required') is deliberately NOT taken: several other test call sites (test_handshake_abort.py, test_handshake_client.py) still construct offers without one, and requiring it there is out of this plan's scope."

patterns-established:
  - "Per-process LanguageRuntime (gatekeeper + provider + HintBank + deception RNG), built once at agent_lifecycle.default_context time and held for the game -- same ownership discipline as 04-09's Reliability / 04-10's HintBank, now actually wired into the live path."

requirements-completed: [LANG-01, LANG-02, LANG-03, LANG-05, LANG-06]

# Metrics
duration: ~110min (approximate; no precise session-start timestamp captured)
completed: 2026-08-09
---

# Phase 4 Plan 12: Turn-Pipeline Integration Summary

**The book's Figure-7 pipeline (decode -> belief -> move -> deception -> bluff) now runs for real inside `take_my_turn`/`await_opponent_turn`, replacing 04-04's placeholder hint and wiring Phase 3/4's strategy brain into the live network turn loop for the first time -- plus a genuine concurrency bug (spurious technical losses from hint-timing races) found and fixed only by actually running two peers against each other.**

## Performance

- **Duration:** ~110 min (approximate)
- **Completed:** 2026-08-09
- **Tasks:** 4/4
- **Files:** 13 created, 12 modified (25 total)

## Accomplishments

- `src/pursuit/services/language_turn.py` -- the plan's own named artifact: `decode_incoming`/`compose_outgoing`, each independently timeout-guarded against `turn_budget_seconds()` (the smaller of `network.response_timeout`/`network.watchdog_threshold`), skipping outright below `MIN_CALL_BUDGET_SECONDS` rather than risking a forfeit.
- `take_my_turn` now runs the whole chain every turn: decode the opponent's last-revealed hint -> choose the move (`BeliefAdapter.decide()` when belief is enabled, else the raw brain, else `first_legal_move`) -> buffer + resolve -> send the direction-token move -> plan the claim (after the move, so it can reference what was actually committed to) -> compose -> send the hint. `PLACEHOLDER_HINT_TEXT` is gone (`grep` confirms no match anywhere in `src/`).
- D-48's regime decision (`known_opponent_cell`) lives in exactly one place, computed once before any state mutation, and is logged per turn (`regime: "A"|"B"` in the new `language_turn` JSONL record) -- Regime A once the opponent has revealed a move (one turn behind for the first mover, same-turn for the second, matching design note 7), Regime B only before anything has ever been revealed.
- `agent_lifecycle.default_context` now builds a REAL registry-constructed brain (BeliefAdapter-wrapped when `belief.enabled`), one `ScentField` per role, and one `LanguageRuntime` (gatekeeper + provider + `HintBank` + deception RNG) per process, per game -- this is the first plan in the whole project that wires Phase 3's strategy and Phase 4's language layer into the actual live two-process turn loop; every prior phase only exercised them through direct engine calls or single-sided injected tests.
- `turn_events.language_turn_record` gives the replay viewer (rule 20), the audit (rule 36) and Phase 7's GUI the full per-turn language channel in one record: regime, belief entropy + argmax, the reliability coefficient, token spend, and the incoming/outgoing hint -- entropy/argmax/reliability are honestly `None` when belief is disabled, never fabricated.
- A real two-peer concurrent game (`tests/integration/two_peer_game.py`) surfaced a genuine, previously-latent bug: 04-04's own "late hint" and "duplicate hint" checks both ended the game as a spurious `Outcome.TECHNICAL_LOSS` purely from ordinary network/processing jitter, since the move and the hint are two independent round-trips with real, variable-latency decode/compose work in between. Fixed (Rule 1): a late hint is dropped silently, a second not-yet-consumed hint overwrites.
- The live handshake now sends a real `local_scent_digest` on both the inbound responder and the outbound `perform_handshake` call (`agent_lifecycle.py`), closing the still-open half of 04-02's carry-over 1 (D-46, rule 23 now actually enforced on the live path, not just the unit-tested handshake API).
- Measured, not assumed: per-turn wall time with the language layer ON is ~37ms/turn, OFF ~18ms/turn, against a `network.watchdog_threshold` of 60s -- roughly three orders of magnitude of margin (`tests/integration/test_language_timing.py`).
- Four full two-peer degradation games all finish with a correctly-scored, agreeing outcome: no API key, every provider call failing (cycling every `LlmFailureReason`), the token budget pre-loaded past `TEMPLATE_ONLY` (a provider that would succeed if called proves `compose()` never calls it once degraded), and a silent peer that never sends a hint at all (the other side finishes on scent alone, `NO_EVIDENCE` every turn, a valid posterior throughout).

## Task Commits

Each task was committed atomically:

1. **Task 1: one guarded entry point for the language half-turn** - `e458dc3` (feat)
2. **Task 3: the event log, and what it must never contain** - `a73c5a9` (feat) -- committed before Task 2 since Task 2's `turn_language_io.py` depends on it
3. **Task 2: wire the turn loop in Figure 7 order** - `440ab78` (feat)
4. **Task 4: prove the degradation paths** - `4a2dbcd` (test)

**Plan metadata:** committed alongside this SUMMARY.

_Note: Task ordering in this commit sequence follows dependency order (1 -> 3 -> 2 -> 4), not the plan's own numeric order, since Task 2's turn-pipeline wiring depends on both Task 1's `language_turn.py` and Task 3's `turn_events.language_turn_record`._

## Files Created/Modified

- `src/pursuit/services/language_turn.py` -- `decode_incoming`/`compose_outgoing`/`turn_budget_seconds`, the one timeout-guarded entry point
- `src/pursuit/network/language_wiring.py` -- `LanguageRuntime`, `build_language_runtime()` (gatekeeper, provider, `HintBank`, seeded RNGs)
- `src/pursuit/network/brain_wiring.py` -- `build_brain_and_scent()`, `build_turn_collaborators()`, `inner_brain()`
- `src/pursuit/network/turn_language.py` -- the Figure-7 sync assembly: `known_opponent_cell`, `choose_destination`, `build_deception_plan`, `observe_reliability`, `belief_snapshot`
- `src/pursuit/network/turn_language_io.py` -- `decode_turn_hint`/`send_turn_hint`, the two AWAITED stages
- `src/pursuit/network/turn_resolve.py` -- `record_action`/`maybe_resolve`, split out of `turn_buffer.py`
- `src/pursuit/network/turn_actions.py` -- rewritten `take_my_turn`/`await_opponent_turn` orchestration
- `src/pursuit/network/turn_buffer.py` -- hint buffer: late/duplicate handling fixed, `send_hint(text=, intent=)`, `PLACEHOLDER_HINT_TEXT` removed
- `src/pursuit/network/orchestrator.py` -- `AgentContext` gains `brain`/`scent_field`/`language`/`incoming_hints`
- `src/pursuit/network/agent_wiring.py` -- `AgentConfig` loads strategy/language/belief/scent/deception.json; `make_handshake_responder(local_scent_digest=)`
- `src/pursuit/network/agent_lifecycle.py` -- `default_context`/`run_agent` build and use the real collaborators + scent digest
- `src/pursuit/network/turn_events.py` -- `language_turn_record()`
- `tests/integration/two_peer_game.py` -- the shared two-real-peer game harness
- `tests/integration/test_language_pipeline.py` -- Figure-7 order spy + full-game hint/move assertions + replay-matches-log proof
- `tests/integration/test_llm_degradation.py` -- the four degradation games
- `tests/integration/test_language_timing.py` -- measured per-turn wall time, on vs off
- `tests/integration/test_game_loop.py` -- extended with a belief+language full game (engine-only, zero network)
- `tests/unit/services/test_language_turn.py`, `tests/unit/test_language_wiring.py`, `tests/unit/test_turn_language.py` -- new-module unit coverage
- `tests/unit/test_orchestrator.py`, `tests/unit/test_orchestrator_loop.py`, `tests/unit/test_turn_buffer.py`, `tests/unit/test_agent_lifecycle.py`, `tests/integration/test_turn_lifecycle.py` -- updated for the legitimately-changed contracts

## Decisions Made

See `key-decisions` in the frontmatter for the full list with rationale. The two with the widest blast radius:

1. **Hint-sending is conditional on real language wiring**, not unconditional as 04-04 shipped it. Production games are unaffected (LANG-01 holds, measured in `test_language_pipeline.py`/`test_llm_degradation.py`); bare test fixtures that never opt in revert to move-only turns.
2. **A late or duplicate hint no longer ends the game.** This is a correction to 04-04's own design, found by actually running two peers concurrently for the first time in the project's history -- the exact class of bug this plan's verification (a real two-peer game) exists to catch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Late/duplicate hint handling turned ordinary network jitter into a spurious technical loss**
- **Found during:** Task 4, first real two-peer concurrent game run (via the new `two_peer_game.py` harness)
- **Issue:** `record_hint`'s "late" and "duplicate" checks (04-04's own design, both raising `HintProtocolError`) fire naturally once the move and the hint are two independent round-trips with real decode/compose latency between them -- a fast opponent legitimately moves on before a slower side's previous hint push completes, or sends a second hint before the first is consumed.
- **Fix:** A late hint (turn < ctx.state.turn) is now silently dropped; a second hint from the same sender before resolution overwrites the first instead of raising. Only `await_move`'s separate "two consecutive hints, no move" liveness cap (a different, still-valid protection) still raises.
- **Files modified:** `src/pursuit/network/turn_buffer.py`, `tests/unit/test_turn_buffer.py` (two tests updated to assert the new, non-raising contract)
- **Verification:** `tests/integration/two_peer_game.py`-based games (`test_language_pipeline.py`, `test_llm_degradation.py`, `test_language_timing.py`) run repeatedly and reliably to completion; re-ran 3x back to back with consistent results.
- **Committed in:** `440ab78` (Task 2 commit)

**2. [Rule 3 - Blocking] Several files/split-outs not in the plan's own `files_modified` list**
- **Found during:** Tasks 2-4, hitting the 150-code-line gate repeatedly while wiring the full pipeline through `AgentContext`/`agent_lifecycle.py`
- **Issue:** The plan's `files_modified` names only `peer_runtime.py, agent_wiring.py, turn_actions.py, turn_events.py, language_turn.py` plus three test files. Wiring a real brain + language runtime into the live path unavoidably touches `orchestrator.py` (new `AgentContext` fields -- same precedent 04-04 already set for `pending_hints`) and `turn_buffer.py` (hint cache + scent-field advance), and the line-limit gate forced four NEW split-out modules (`language_wiring.py`, `brain_wiring.py`, `turn_language.py`, `turn_language_io.py`, `turn_resolve.py`) plus their own dedicated test files.
- **Files modified:** see `key-files` above; `peer_runtime.py` was NOT touched (nothing about it needed to change).
- **Verification:** every touched/new file passes `bash scripts/check_line_limit.sh` individually and repo-wide; `uv run ruff check .` clean.
- **Committed in:** `440ab78`/`4a2dbcd`

---

**Total deviations:** 2 (1 real concurrency bug fix, 1 file-ownership expansion forced by the 150-line gate and the join-turn architecture). Both necessary; no scope creep beyond what wiring a real, previously-never-exercised live pipeline required.
**Impact on plan:** The bug fix is a genuine correctness improvement with real league-game stakes (a hint could otherwise end a real match). The extra files are mechanical consequences of the hard line-limit gate, matching this phase's own established precedent.

## Issues Encountered

None beyond what is captured above as deviations. One design tension resolved under the autonomy directive: Task 2's literal prose lists "advance the scent field" as a step between decode and `BeliefAdapter.decide()`, but RESUME.md's carry-over S is explicit that `ScentField.advance()` must run exactly once per JOINT turn, after `resolve_turn`. The carry-over's stronger, more specific guidance was followed: `advance()` now lives centrally in `turn_resolve.maybe_resolve()`, firing exactly when a joint turn actually resolves, regardless of which side's call completes the pair.

## Verification (plan's own block, run in full on the merged tree)

1. `uv run ruff check .` -> **0 violations**. `uv run pytest tests/ --cov` -> **1048 passed, 95.21%** (floor 85%, up from the pre-plan baseline of 1020 passed / 94.94%).
2. `bash scripts/check_line_limit.sh` -> clean, repo-wide. `turn_actions.py` split into `turn_actions.py` + `turn_language.py` + `turn_language_io.py` + `turn_resolve.py`, never compressed.
3. All existing integration tests pass; the one payload-shape-legitimate change (`test_turn_lifecycle.py` now passes `local_scent_digest=` to `perform_handshake`, matching what `agent_lifecycle.default_context`'s real responder now requires) is documented above. No assertion was weakened or deleted anywhere.
4. No test performs network I/O -- `grep`-checked across every new test file for `requests.`/`httpx.`/`aiohttp.`/`socket.`/`urlopen`: no match. Every degradation/pipeline test explicitly unsets `ANTHROPIC_API_KEY`.
5. `uv run python scripts/check_no_llm_in_strategy.py` -> clean.
6. Per-turn wall time measured with the language layer ON and OFF: **~37ms/turn ON, ~18ms/turn OFF**, against `network.watchdog_threshold=60s` -- roughly 1600x margin ON, 3300x OFF (`tests/integration/test_language_timing.py`, printed and asserted).

## User Setup Required

None -- no external service configuration required. Every test explicitly unsets `ANTHROPIC_API_KEY`; the real `AnthropicProvider` path is exercised structurally (construction, degrade-to-`NO_KEY`) but never actually calls the network in this plan's own test suite.

## Next Phase Readiness

- **04-13** (docs + `RULES-RESOLUTION-LANG.md` + phase triplet) can now cite: the real Figure-7 pipeline running live, the measured per-turn timing, the four degradation results, and the late/duplicate-hint bug-and-fix as a concrete example of "why running the real two-peer game matters" for its own report.
- **04-14** (GATE-4 measurement) has everything it needs already wired: a real game against the real `AnthropicProvider` just needs `ANTHROPIC_API_KEY` set in the environment -- no code changes required, only the key and a real run.
- `docs/phases/phase-4/` still does not exist (RESUME.md's still-open item 5); the plan set assigns it to 04-13, unchanged by this plan.
- Knowledge graph refreshed this session (`graphify update .`): 5221 nodes / 9687 edges / 336 communities; `GRAPH_REPORT.md` copied to `.planning/graphs/` and committed. `graph.html` was NOT regenerated this run (5221 nodes exceeds graphify's 5000-node HTML visualization limit) -- the previous `graph.html` remains on disk as a stale, gitignored artifact; regenerate with `GRAPHIFY_VIZ_NODE_LIMIT` raised if a fresh one is needed locally.
- No blockers for wave 7.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-09*

## Self-Check: PASSED

- All 13 claimed created files verified present on disk with `[ -f ]`.
- All 4 claimed task commit hashes (`e458dc3`, `a73c5a9`, `440ab78`, `4a2dbcd`) verified
  present in `git log --oneline --all`.
- Full-suite re-confirmation at self-check time: `uv run pytest tests/ --cov` -- 1048
  passed, 95.21% coverage (required 85%); `uv run ruff check .` -- 0 violations;
  `bash scripts/check_line_limit.sh` (project-wide) -- 0 violations; `uv run python
  scripts/check_no_llm_in_strategy.py` -- clean; `grep -rn "PLACEHOLDER_HINT_TEXT\s*="
  src/` -- no match.
