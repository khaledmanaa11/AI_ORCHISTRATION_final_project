---
phase: 04-language-and-scent
plan: "04"
subsystem: api
tags: [fastmcp, transport, direction-token, hint-payload, mcp-tools]

# Dependency graph
requires: []
provides:
  - "MessageType.HINT on the shared Envelope (D-47) -- four-key shape and REQUIRED_KEYS unchanged"
  - "hint_payload.py: Intent (truth|lie) + HintKey (text/intent/turn) shape, assert_no_coordinates LANG-02 guard, build_hint()"
  - "receive_hint MCP tool, fifth member of the D-05 tool surface, same decode-enqueue-ack pattern as the other four"
  - "move_payload.py: direction-token move/barrier codec (D-53) -- encode/decode/is_legal, legacy {x,y} still accepted"
  - "turn_actions.py wired to send a direction-token move + placeholder hint every turn, and to reject an illegal/unparseable opponent payload as a technical loss instead of crashing"
  - "turn_buffer.py hint buffer: record_hint, await_move (leading-hint tolerant), drain_trailing_hint (non-blocking), send_hint, reject_peer_payload"
affects: [04-08-deception-policy, 04-10-bluff-generator, 04-12-turn-pipeline-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "150-line-gate module split: hint-payload shape lives in hint_payload.py, not envelope.py (mirrors handshake.py/handshake_wire.py)"
    - "Codec never raises on attacker-controlled input: move_payload.decode returns ResolvedAction(ok=False, reason=...); the caller converts that to Outcome.TECHNICAL_LOSS, never an exception"
    - "Non-blocking opportunistic drain (asyncio.Queue.get_nowait, put back if wrong type) lets an optional message (hint) ride beside a mandatory one (move) without a peer that never sends it stalling the turn"

key-files:
  created:
    - src/pursuit/network/move_payload.py
    - src/pursuit/network/hint_payload.py
    - tests/unit/test_move_payload.py
    - tests/unit/test_hint_payload.py
    - tests/unit/test_turn_buffer.py
  modified:
    - src/pursuit/network/envelope.py
    - src/pursuit/network/tools.py
    - src/pursuit/network/turn_actions.py
    - src/pursuit/network/turn_buffer.py
    - src/pursuit/network/orchestrator.py
    - tests/unit/test_envelope.py
    - tests/unit/test_tools.py
    - tests/unit/test_peer_runtime.py
    - tests/unit/test_orchestrator.py
    - tests/unit/test_orchestrator_loop.py

key-decisions:
  - "Origin-derived direction vectors (top-left/-right, bottom-left/-right), never a hardcoded top-left assumption -- flipping origin flips the sense of north, verified by test"
  - "decode()'s legacy {x,y} branch converts the coordinate back into a direction word FIRST, then resolves through the identical word->cell step the direction-shape branch uses -- exactly one validation path, per the plan's own requirement"
  - "Hint buffering is symmetric best-effort on both ends: a failed outgoing hint push never ends the game (the move is the authoritative channel), and a missing incoming hint never blocks resolution"
  - "AgentContext gained pending_hints (dict, default empty) -- the only way to give the hint buffer per-agent persistent state without a module-level global (NET-02); documented as a deviation since orchestrator.py is not in this plan's files_modified list"

requirements-completed: [LANG-01, LANG-02, LANG-03]

# Metrics
duration: ~55min
completed: 2026-08-08
---

# Phase 4 Plan 04: Transport Layer for Hints and Direction-Token Moves Summary

**Direction-token move codec (D-53) plus a typed HINT envelope with a pre-committed intent flag (D-47), wired into the live turn loop so every turn sends words instead of coordinates and a placeholder hint instead of nothing.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-08-08T21:15:00Z (approx.)
- **Completed:** 2026-08-08T21:42:00Z
- **Tasks:** 3
- **Files modified:** 15 (5 created, 10 modified)

## Accomplishments

- Outgoing moves are now direction words (`north`/`south`/`east`/`west`/`stay`) plus a `kind` (`move`/`barrier`) -- zero numeric coordinates on our outgoing wire, satisfying rule 27 / LANG-02.
- A Phase-2 peer speaking the legacy `{"x","y"}` coordinate shape is still fully understood: `decode()` converts it back into the same direction word and validates through one shared path.
- `MessageType.HINT` rides the existing four-key `Envelope` unchanged, carrying free text, a pre-committed `intent` (`truth`|`lie`), and the turn it refers to -- the exact shape Phase 6's `H_commit = SHA256(State‖Move‖Intent‖Nonce)` will hash.
- Every turn now pushes a placeholder hint alongside the move (`receive_hint`, the fifth `@mcp.tool` handler), buffered atomically with the move via a new per-context hint buffer, without ever blocking on a peer that sends none.
- An illegal or unparseable payload from the opponent (bad direction, off-board step, diagonal, garbage, duplicate/late hint) is rejected as `Outcome.TECHNICAL_LOSS` with a JSONL evidence record -- never a crash, never a silently-coerced STAY.

## Task Commits

Each task was committed atomically:

1. **Task 1: the direction token codec** - `107189e` (feat)
2. **Task 2: MessageType.HINT and the receive_hint tool** - `d49fe0c` (feat)
3. **Task 3: send both, buffer both** - `9094d23` (feat)

_No separate plan-metadata commit yet -- this SUMMARY and the STATE/ROADMAP updates are the orchestrator's responsibility per this run's isolation contract (worktree parallel execution)._

## The two facts the league opponent must be told (per this plan's `<output>` instruction)

**Direction vocabulary** (wire values, `src/pursuit/network/move_payload.py`):
- `direction`: one of `"north"`, `"south"`, `"east"`, `"west"`, `"stay"` (relative to the mover's own pre-turn cell; for a cop barrier, relative to the cop).
- `kind`: `"move"` or `"barrier"`.
- Outgoing payload shape: `{"kind": "move"|"barrier", "direction": "north"|"south"|"east"|"west"|"stay"}`.
- A legacy `{"x": int, "y": int}` payload is still accepted on receipt (D-53 interop) but is never emitted by this codebase.

**Hint payload keys** (`src/pursuit/network/hint_payload.py`, envelope `type="hint"`):
- `text`: free-form natural-language string (LANG-02: no digit pair, no ordered-pair form, no "row N column M" grid reference -- enforced only on the outgoing/send path).
- `intent`: `"truth"` or `"lie"`, committed before the text exists (LANG-03).
- `turn`: the game turn the hint refers to (int).

## Files Created/Modified

- `src/pursuit/network/move_payload.py` - Direction/ActionKind/Origin enums, `encode`/`decode`/`is_legal` (D-53)
- `src/pursuit/network/hint_payload.py` - Intent/HintKey enums, `assert_no_coordinates`, `validate_hint_payload`, `build_hint` (D-47, split from envelope.py at the 150-line gate)
- `src/pursuit/network/envelope.py` - `MessageType.HINT` added; four-key shape and `REQUIRED_KEYS` unchanged
- `src/pursuit/network/tools.py` - `receive_hint`, fifth `@mcp.tool` handler, same decode-enqueue-ack pattern
- `src/pursuit/network/turn_actions.py` - `take_my_turn` sends a direction-token move + placeholder hint; `await_opponent_turn` decodes/validates the incoming move and rejects illegal payloads as a technical loss
- `src/pursuit/network/turn_buffer.py` - hint buffer (`record_hint`), `await_move`, `drain_trailing_hint`, `send_hint`, `reject_peer_payload`, `HintProtocolError`
- `src/pursuit/network/orchestrator.py` - `AgentContext.pending_hints` field (deviation, see below)
- `tests/unit/test_move_payload.py`, `test_hint_payload.py`, `test_turn_buffer.py` - new, dedicated coverage
- `tests/unit/test_envelope.py`, `test_tools.py`, `test_peer_runtime.py`, `test_orchestrator.py`, `test_orchestrator_loop.py` - updated for the new tool surface and payload shape

## Decisions Made

- **Origin is derived, never assumed.** `move_payload.py` computes the direction-to-vector mapping from an `origin` string (`top-left` by default, matching `game_params.json` Table 13 row 3) rather than hardcoding `pursuit.constants.Direction`'s existing top-left-only convention. Flipping `origin` flips the sense of `north` in the resolved cell, verified by `test_flipping_origin_flips_the_sense_of_north`.
- **One validation path for both wire shapes.** `decode()`'s legacy `{x,y}` branch first converts the coordinate delta back into a `DirectionWord`, then resolves through the identical word-to-cell step the direction-shape branch uses, so a diagonal or off-board legacy coordinate is rejected by the same logic as a malformed direction word.
- **The codec never raises on attacker-controlled input.** `decode()` always returns a `ResolvedAction`; `ok=False` carries a `reason` string. `encode()` is the one function allowed to raise (`ValueError`), because it only ever receives OUR OWN algorithm's already-legal move.
- **Hints are optional on both ends, symmetrically.** A failed outgoing hint push does not end the game (the move is rules-13/14's authoritative channel); a missing incoming hint never blocks `maybe_resolve`. This directly implements "a peer that never sends hints must still be playable."
- **Placeholder hint text is explicit scaffolding**, named `PLACEHOLDER_HINT_TEXT` in `turn_buffer.py` with a docstring pointing at 04-08 (deception policy)/04-10 (bluff generator)/04-12 (turn-pipeline integration) as the plans that replace it with the real pipeline.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking / CLAUDE.md 150-line gate] Split hint-payload shape into a new `hint_payload.py`**
- **Found during:** Task 2
- **Issue:** Adding `Intent`, `HintKey`, `assert_no_coordinates`, `validate_hint_payload`, and `build_hint` directly to `envelope.py` would have pushed it past the 150-code-line pre-commit gate (~184 lines).
- **Fix:** New sibling module `src/pursuit/network/hint_payload.py`, mirroring the existing `handshake.py`/`handshake_wire.py` split. `envelope.py` itself only gained the one `MessageType.HINT` member.
- **Files modified:** `src/pursuit/network/hint_payload.py` (new), `tests/unit/test_hint_payload.py` (new) -- neither was in this plan's frontmatter `files_modified` list, but both are direct, mandatory consequences of the hard line-limit gate ("split files, never compress code to fit").
- **Verification:** `bash scripts/check_line_limit.sh` passes on every touched file; `uv run ruff check .` clean.
- **Committed in:** `d49fe0c` (Task 2 commit)

**2. [Rule 1 - Bug] Updated `tests/unit/test_peer_runtime.py`'s hardcoded 4-tool-name assertion**
- **Found during:** Task 2 (full-suite run after the `receive_hint` tool landed)
- **Issue:** `test_build_server_registers_the_tool_surface` asserted the tool set was exactly the original four names; adding a fifth tool (this task's explicit goal) broke it.
- **Fix:** Extended the expected set to include `"receive_hint"`. No assertion was weakened -- the test still asserts an EXACT set, now the correct five-member one.
- **Files modified:** `tests/unit/test_peer_runtime.py`
- **Verification:** `uv run pytest tests/unit/test_peer_runtime.py` passes.
- **Committed in:** `d49fe0c` (Task 2 commit)

**3. [Rule 2 - Missing Critical] Added `AgentContext.pending_hints`**
- **Found during:** Task 3
- **Issue:** The plan's own rules ("a second hint for the same turn from the same sender is a protocol error... a hint for a turn already resolved is a protocol error") require per-agent state that survives across `take_my_turn`/`await_opponent_turn` calls. `AgentContext` (in `orchestrator.py`, not in this plan's `files_modified` list) already holds the analogous `pending_cop_action`/`pending_thief_move` fields for exactly this reason.
- **Fix:** Added `pending_hints: dict[str, dict] = field(default_factory=dict)` next to the existing pending-action fields, with a docstring note. A fresh `dict` per `AgentContext` instance -- never module-level, never shared between cop and thief (NET-02, rule 2). Every existing `AgentContext(...)` call site uses keyword arguments and does not pass this field, so the change is fully backward compatible.
- **Files modified:** `src/pursuit/network/orchestrator.py`
- **Verification:** Verified neither sibling wave-1 plan (04-01, 04-03) touches `orchestrator.py`; full test suite green.
- **Committed in:** `9094d23` (Task 3 commit)

**4. [Rule 1 - Bug] Updated `test_orchestrator.py`/`test_orchestrator_loop.py` assertions that hardcoded the OLD `{x,y}` shape and single-push call count**
- **Found during:** Task 3 (full-suite run after wiring `encode()`/`send_hint()` into `take_my_turn`)
- **Issue:** `test_full_turn_cycle`, `test_take_my_turn_proceeds_when_the_machine_is_already_at_my_turn`, and `test_silent_opponent_produces_a_technical_win` (all pre-existing, none in this plan's `files_modified` list) asserted the exact outgoing `{"x","y"}` payload and a single `client().calls` entry -- both direct, unavoidable consequences of this task's explicit goal (direction-token payload + a second push for the placeholder hint).
- **Fix:** Updated each assertion to the new expected shape (`move_payload.encode(...)`, never re-derived by hand) and call count (2, move then hint). No assertion was deleted or weakened; `test_full_turn_cycle` additionally now asserts `"x" not in sent.payload`.
- **Files modified:** `tests/unit/test_orchestrator.py`, `tests/unit/test_orchestrator_loop.py`
- **Verification:** Full suite green (436 passed).
- **Committed in:** `9094d23` (Task 3 commit)

**5. [Rule 1 - Bug] `drain_trailing_hint` false-positive on a pre-queued future-turn move**
- **Found during:** Task 3 (integration-test run: `tests/integration/test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over` started failing)
- **Issue:** The test pre-queues both of the thief's moves (turn 1 and turn 2) before the loop starts. The first draft of `drain_trailing_hint` treated ANY non-hint item found immediately after a move as a same-turn protocol violation and raised, which incorrectly fired on the legitimately-queued turn-2 move sitting behind turn-1's.
- **Fix:** `drain_trailing_hint` now puts a non-hint item straight back on the queue (`put_nowait`) instead of raising -- it only ever consumes an actual `HINT`, leaving anything else for the call that actually needs it.
- **Files modified:** `src/pursuit/network/turn_buffer.py`
- **Verification:** `tests/integration/test_turn_lifecycle.py` passes unmodified; `tests/unit/test_turn_buffer.py::test_drain_trailing_hint_puts_back_a_non_hint_item` pins the fix directly.
- **Committed in:** `9094d23` (Task 3 commit)

---

**Total deviations:** 5 auto-fixed (1 blocking/gate-driven module split, 3 pre-existing-test corrections for this task's unavoidable shape/surface change, 1 real bug caught by the integration suite before it shipped).
**Impact on plan:** All five were necessary for correctness or for the mandatory 150-line gate. No scope creep -- every touched file outside the frontmatter `files_modified` list is either a mechanical consequence of this task's stated goal or a hard engineering-standard requirement (CLAUDE.md).

## Issues Encountered

None beyond the deviations documented above (all resolved during execution).

## Known Stubs

- **`PLACEHOLDER_HINT_TEXT`** (`src/pursuit/network/turn_buffer.py`) -- a constant string (`"Placeholder hint text; the real bluff generator lands in a later plan."`) sent with `intent=truth` on every turn. This is intentional, explicitly documented scaffolding per this plan's own instructions (Task 3: "This plan sends a placeholder hint... say so in the code comment so nobody ships it thinking it is the feature"). Plan 04-08 (deception policy) picks the real `intent`/payload, 04-10 (bluff generator) phrases it, and 04-12 (turn-pipeline integration) wires that real pipeline into `send_hint`, replacing this constant outright. Not a gap in THIS plan's own scope -- LANG-01's full "every turn, true and sometimes false" requirement is explicitly deferred to those later plans per the phase outline's decision-coverage trace.

## Threat Flags

| Flag | File | Description |
|------|------|--------------|
| threat_flag: new-network-endpoint | src/pursuit/network/tools.py (`receive_hint`) | A fifth MCP tool accepting attacker-controlled free text + intent from the opponent. Mitigated: text is stored/logged as opaque data (never parsed/executed/formatted unsafely); `assert_no_coordinates` only constrains OUR OWN outgoing text, by design (LANG-02 is a send-side rule); `validate_hint_payload`'s shape check runs on outgoing construction only, matching the existing "transport handler never judges semantics" boundary. No `<threat_model>` block existed in this plan to pre-register this disposition. |

## Next Phase Readiness

- Wave-1 sibling plans (04-01 scent, 04-03 gatekeeper) are independent of this plan's files; no merge conflicts expected.
- Plan 04-02 (handshake scent digest) and 04-06 (provider layer) can proceed once this wave closes -- neither depends on this plan directly, but 04-12 (turn-pipeline integration, wave 6) depends on this plan (04-04) plus 04-02/04-10/04-11 and will replace `PLACEHOLDER_HINT_TEXT` with the real bluff pipeline.
- `move_payload.decode`/`is_legal` are ready for the belief map (04-05) and deception policy (04-08) to build on: both are pure, side-effect-free, and importable without pulling in any network/LLM dependency (keeps `scripts/check_no_llm_in_strategy.py`'s rule-25 guard trivially satisfiable for anything that imports them).
- No blockers. Full test suite: 436 passed, 0 failed, ruff clean, line-limit gate clean, coverage 91.82% (≥ 85% required).

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-08*
