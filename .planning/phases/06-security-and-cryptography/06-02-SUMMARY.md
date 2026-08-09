---
phase: 06-security-and-cryptography
plan: "02"
subsystem: network
tags: [commit-reveal, fastmcp, asyncio, state-machine, wire-protocol]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography plan 01
    provides: "src/pursuit/security/ (commit_pack.commit/verify_reveal/build_commit_payload, state_record.build_state_record, ledger.CommitLedger) + shared/security_config.SecurityParams/load_security_config, the 11th per-agent config block"
provides:
  - "turn_commit.py's D-58 both-locked Commit->Ack->Reveal exchange wired live into the turn loop, both roles, with a traced and MEASURED deadlock-freedom fix"
  - "D-66/SEC-07: the cop's barrier placement finally travels over the wire inside the committed action -- the live P2P pipeline was barrier-less before this plan"
  - "MessageType.COMMIT/ACK/REVEAL/FINAL_REVEAL + their tool handlers (FINAL_REVEAL's body is 06-03's job)"
  - "AgentContext.security (required) + AgentContext.commit_state (CommitTurnState/PendingAction, D-58 scratch state)"
affects: [06-03-step0-and-audit, 06-04-gate-and-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "5-file network-package split for one D-58 exchange: agent_context.py + commit_state.py (150-line room-making, Task 2), turn_commit.py + turn_commit_wait.py + turn_commit_send.py (policy vs. two flavors of mechanism, Task 3) -- mirrors the handshake.py/handshake_wire.py/handshake_evaluate.py precedent, extended to three siblings when two were not enough"
    - "role-branch inside a plan-specified 'unconditional' function: await_and_respond branches on ctx.role because the fixed send-first convention (design note 7) makes the initiator's own await_opponent_turn call structurally different from the responder's -- a naive unconditional reading of D-58 deadlocks"
    - "PendingAction stores the ALREADY-BUILT payload/hash/turn, never re-derives them at reveal time, because ctx.state has moved past resolve_turn by then"
    - "FailAfterClient (succeed N calls, fail after) added to tests/unit/_fakes_agent.py -- the second shared fake needed to drive a multi-message exchange partway before injecting an opponent going silent"

key-files:
  created:
    - src/pursuit/network/agent_context.py
    - src/pursuit/network/commit_state.py
    - src/pursuit/network/turn_commit.py
    - src/pursuit/network/turn_commit_wait.py
    - src/pursuit/network/turn_commit_send.py
    - tests/unit/test_agent_context.py
    - tests/unit/test_turn_commit.py
    - tests/unit/test_turn_commit_responder.py
    - tests/unit/test_turn_commit_initiate_failures.py
    - tests/unit/test_turn_commit_respond_failures.py
    - tests/unit/test_turn_resolve.py
    - tests/integration/test_commit_reveal_protocol.py
    - tests/integration/test_commit_reveal_protocol_barrier.py
    - tests/integration/test_commit_reveal_protocol_jitter.py
    - tests/integration/test_language_pipeline_replay.py
  modified:
    - src/pursuit/network/envelope.py
    - src/pursuit/network/tools.py
    - src/pursuit/network/orchestrator.py
    - src/pursuit/network/agent_lifecycle.py
    - src/pursuit/network/agent_wiring.py
    - src/pursuit/network/turn_actions.py
    - src/pursuit/network/turn_language.py
    - src/pursuit/network/turn_language_io.py
    - src/pursuit/network/turn_resolve.py
    - tests/unit/_fakes_agent.py
    - tests/unit/test_turn_language.py
    - tests/integration/test_gate4.py
    - tests/integration/test_language_pipeline.py
    - tests/integration/test_turn_lifecycle.py
    - tests/unit/test_peer_runtime.py
    - tests/integration/test_secret_channel.py
    - scripts/gate5_tunnel_smoke.py

key-decisions:
  - "D-58 role branch (Rule 1 bug fix, MEASURED): await_and_respond checks ctx.role -- police (design note 7's fixed first-mover) already committed+revealed THIS turn inside its own initiate() by the time its own await_opponent_turn runs, so it must only WAIT for the opponent's REVEAL, never decide again. The plan's own literal unconditional reading of await_and_respond hung a real two-peer game for 136s before returning a false technical loss; fixed, now 1.15s."
  - "PendingAction carries 3 fields beyond the plan's literal 5-field sketch (action_payload, h_commit, turn) -- ctx.state advances past resolve_turn before reveal_pending runs (maybe_resolve fires earlier in the same take_my_turn branch, mirroring the initiator's own position), so reveal must send the exact already-committed payload, never a re-derived one that could drift from what was actually hashed and ledgered"
  - "turn_commit.py needed a THIRD sibling (turn_commit_send.py) beyond the plan's two pre-authorized files -- 251 code lines even after the wait-primitive split, mirroring the already-cited handshake.py/handshake_wire.py/handshake_evaluate.py 3-file precedent, not an improvised fallback"
  - "test_turn_lifecycle.py's GATE-3 single-sided harness (peer B's own turn loop never runs) opts out via security.commit_reveal=False, matching its own pre-existing documented LIMITATION note -- orthogonal to what GATE-3 tests, and structurally incompatible with a real two-way D-58 handshake"
  - "test_gate4.py/test_language_pipeline.py's three foreseeable casualties fixed exactly as critical_correctness_3 specified, each re-verified via a throwaway probe to still catch a real violation before being left in place"

patterns-established:
  - "Ledger filename convention (D-64, for 06-03): <log-file-stem>.ledger.jsonl, sibling of ctx.log_path -- e.g. a.jsonl -> a.ledger.jsonl. Built by turn_commit_wait._ledger_path(ctx)."
  - "game_id interim decision (for 06-03/D-61): commit_own_action passes ctx.game_uid as build_state_record's game_id -- no cross-peer game_id negotiation exists yet; 06-03 reconciles this once D-61 lands."

# Metrics
duration: ~100min
completed: 2026-08-09
---

# Phase 6 Plan 2: D-58 Commit-Ack-Reveal Wire Protocol + D-66 Barrier-Over-the-Wire Summary

**The book's actual both-locked Commit->Acknowledge->Reveal exchange (Sec5.3.2) now runs live between the two real FastMCP peers -- barrier placement travels over the wire for the first time (D-66), a real measured deadlock in the responder-dispatch logic was found and fixed (136s hang -> 1.15s), and the toggle-off path is proven byte-identical to pre-Phase-6.**

## Performance

- **Duration:** ~100 min
- **Tasks:** 4 (all executed autonomously, no checkpoints)
- **Files modified/created:** 33 (17 source/script, 16 test)

## Accomplishments

- **The four-phase protocol runs on the wire, for real.** `MessageType.COMMIT/ACK/REVEAL/FINAL_REVEAL` + their tool handlers (Task 1); `turn_commit.py`'s `initiate`/`await_and_respond`/`reveal_pending` (Task 3) drive the exchange from both `turn_actions.py` entry points (`take_my_turn` branches on `ctx.commit_state.pending_action`; `await_opponent_turn` calls `turn_commit.await_and_respond` unconditionally, per the plan's own literal spec).
- **A real, measured deadlock found and fixed (Rule 1).** The plan's own literal reading of D-58 — call the full responder decide-now flow unconditionally from every `await_opponent_turn` — deadlocks the INITIATOR (police): by the time police's own `await_opponent_turn` runs, it already committed+revealed its own action for that turn inside `take_my_turn`/`initiate`; asking it to wait for a SECOND opponent COMMIT that will never arrive hangs the full `NetworkParams` retry ladder (measured: 136 seconds) before falsely declaring a technical loss. Fixed: `await_and_respond` branches on `ctx.role` — police (design note 7's fixed first-mover) only waits for the opponent's REVEAL; thief runs the full decide-now flow. Re-measured: 1.15 seconds, correct outcome.
- **D-66/SEC-07 closed: barriers travel over the wire.** `turn_language.py`'s `choose_destination` now stashes the full `Decision.barrier` onto `ctx.commit_state.chosen_barrier`; `turn_resolve.py`'s `record_action` builds `CopAction(barrier=...)` XOR `CopAction(move=...)`, never both (verified: `grep -n "CopAction(move=.*barrier=" turn_resolve.py` matches nothing); the receiver validates BOTH sub-keys of the composite `{move, barrier}` dict through the already-shipped `move_payload.decode`/`is_legal(BARRIER)` branch. Proven end to end: a forced one-shot barrier brain in `test_commit_reveal_protocol_barrier.py` shows both engines independently resolving the identical barrier cell and count.
- **Toggle-off is proven byte-equivalent**, not just asserted — a dedicated integration test plays a full game with both sides' `security.commit_reveal=False` and shows only `handshake`/`move`/`hint` envelope types, zero barriers ever placed.
- **Jitter tolerance proven at the integration level** — a duplicate ACK injected mid-game is dropped, the game still reaches a normal outcome, never a spurious technical loss.
- **GATE-4's real invariant survives the new concurrency.** The `test_intent_is_always_committed_before_the_hint_text_exists` order-list assertion (which relied on same-side back-to-back atomicity, no longer true once the responder's plan/compose are separated by a real network round trip) is replaced with an identity-based (`id()`) pairing proof — verified via a throwaway probe that it still fails when a compose genuinely runs on a plan the spy never saw produced.

## Task Commits

Each task was committed atomically:

1. **Task 1: four new wire message kinds** - `0711829` (feat)
2. **Task 2: the AgentContext split — security, and the D-58/D-66 scratch state** - `fb7d46a` (feat)
3. **Task 3: the widened choose surface, record_action's barrier, and turn_commit.py's D-58 exchange** - `22c75fc` (feat)
4. **Task 4: prove it — two-peer protocol test, forced barrier, and the three foreseeable casualties** - `bf5d6ff` (test)

**Plan metadata:** (this commit, appended after STATE.md/graph update)

## Files Created/Modified

- `src/pursuit/network/envelope.py` — `MessageType` gains COMMIT/ACK/REVEAL/FINAL_REVEAL (nine members total)
- `src/pursuit/network/tools.py` — `receive_commit`/`receive_ack`/`receive_reveal`/`receive_final_reveal` handlers, mirroring `receive_hint`'s `_accept` pattern
- `src/pursuit/network/agent_context.py` (new) — `Coord`/`ChooseMove`/`AgentContext` (moved verbatim from orchestrator.py), `build_context` (moved verbatim from agent_lifecycle.py); `AgentContext.security: SecurityParams` (required, no default) + `commit_state: CommitTurnState` (defaulted)
- `src/pursuit/network/commit_state.py` (new) — `PendingAction`/`CommitTurnState` (D-58/D-66 scratch state), split from agent_context.py at the 150-line gate
- `src/pursuit/network/orchestrator.py` / `agent_lifecycle.py` — both re-export the moved names unchanged, dropping well under the 150-line ceiling
- `src/pursuit/network/agent_wiring.py` — `AgentConfig.security`, `load_agent_config` loads `security.json`
- `src/pursuit/network/turn_language.py` — `choose_destination` stashes `Decision.barrier` onto `ctx.commit_state.chosen_barrier`
- `src/pursuit/network/turn_language_io.py` — `send_turn_hint` split into `plan_turn_deception` (stage 3 alone) + `compose_and_send_hint` (stages 4-5)
- `src/pursuit/network/turn_resolve.py` — `record_action` gains optional `barrier`; new `decode_revealed_action` (shape-aware receive-side decode/validate)
- `src/pursuit/network/turn_commit.py` (new) — the three D-58 public entry points: `initiate`/`await_and_respond`/`reveal_pending`
- `src/pursuit/network/turn_commit_wait.py` (new) — wait primitives + `commit_own_action`/`build_action_payload`
- `src/pursuit/network/turn_commit_send.py` (new) — push/log/technical-loss mechanics, `send_move_only` (toggle-off)
- `src/pursuit/network/turn_actions.py` — `take_my_turn` branches on `ctx.commit_state.pending_action`; `await_opponent_turn` drives `turn_commit.await_and_respond`
- 16 test files (see frontmatter `key-files`) — new proof suites + the 6 foreseeable-casualty fixes

## Exact Signatures for 06-03 (verbatim, do not re-derive)

```python
# src/pursuit/network/turn_commit.py
async def initiate(
    ctx: AgentContext, current: State, pre_cell: Coord, dest: Coord,
    barrier: Coord | None, plan: object | None,
) -> Outcome | None: ...

async def await_and_respond(ctx: AgentContext) -> tuple[Envelope | None, TechnicalWin | None]: ...

async def reveal_pending(ctx: AgentContext) -> Outcome | None: ...

# src/pursuit/network/commit_state.py
@dataclass
class PendingAction:
    move: Coord
    barrier: Coord | None
    plan: object | None          # DeceptionPlan | None
    incoming_log: dict
    regime: str
    action_payload: dict         # the exact D-59/D-66 composite dict, already committed+ledgered
    h_commit: str                # this side's own commit hash for the turn
    turn: int                    # the turn this action was decided for (pre-resolve)

@dataclass
class CommitTurnState:
    pending_action: PendingAction | None = None
    own_ack_received: bool = False
    chosen_barrier: Coord | None = None

# The D-59/D-66 composite action dict shape (what gets committed and revealed):
# {"move": {"kind": "move", "direction": <DirectionWord>},
#  "barrier": {"kind": "barrier", "direction": <DirectionWord>} | None}

# Ledger filename convention (D-64):
# <ctx.log_path.stem>.ledger.jsonl, same directory as ctx.log_path
# e.g. logs/police/<game_uid>.jsonl -> logs/police/<game_uid>.ledger.jsonl
# built by turn_commit_wait.py's _ledger_path(ctx) -- 06-03 reads its OWN
# ledger the same way.
```

**What 06-03 needs to know:**

- **game_id interim decision:** `commit_own_action` passes `ctx.game_uid` as `build_state_record`'s `game_id` — there is still no cross-peer `game_id` negotiation (D-61 is 06-03's job). Once D-61 lands, either re-point this at the negotiated value or confirm `game_uid` already IS that value.
- **The nonce never crosses the wire** in COMMIT/ACK/REVEAL — only `h_commit` (COMMIT/ACK payloads) and the composite action dict (REVEAL payload). The nonce lives solely in each side's own `CommitLedger`, read via `CommitLedger(path).read_all()` (06-01's own signature) — this is what 06-03's FINAL_REVEAL/audit exchange will publish.
- **`FINAL_REVEAL`'s `MessageType`/tool handler exist but are unused** — `receive_final_reveal` just enqueues via the standard `_accept` pattern; 06-03 owns the body (what payload shape it carries, how it's consumed).
- **D-67's audit needs, per turn, per side:** the `h_commit` we observed at COMMIT time (already in our own JSONL's `message_sent`/`message_received` records), the `payload` our own `CommitLedger` holds (`{state, move, intent, nonce}`), and the action actually recorded in our own wire log's REVEAL record — all three are already durably available; 06-03 wires the cross-check, doesn't need to invent new storage.
- **`ctx.state.turn` is unreliable inside the responder's own `reveal_pending`** (it has already advanced past `engine.resolve_turn`) — always use `pending.turn` there, never `ctx.state.turn`, for anything that needs to key by the turn being revealed.

## Decisions Made

See frontmatter `key-decisions` for the full list with rationale. The single most consequential one: **the D-58 role branch inside `await_and_respond`**, a genuine, measured bug fix to what the plan's own literal text specified (an unconditional responder-flow call from every `await_opponent_turn` invocation). Traced, reasoned about, and confirmed by direct measurement (a real two-peer game hanging 136 seconds before this fix, completing in 1.15 seconds after) rather than assumed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `await_and_respond` deadlocked the initiator without a role branch**
- **Found during:** Task 3, first real two-peer integration test run (`test_gate4.py::test_handshake_scent_digest_matches_before_any_move`)
- **Issue:** The plan's own literal text specifies `await_and_respond` as always running the full "wait for opponent COMMIT, decide now, commit, send COMMIT+ACK, wait for REVEAL" flow. Called unconditionally from every `await_opponent_turn`, this makes the fixed-first-mover side (police, design note 7) — which already committed+revealed its OWN action for the turn inside its own `take_my_turn`/`initiate` — wait for a SECOND opponent COMMIT that will never arrive that turn.
- **Fix:** `await_and_respond` branches on `ctx.role`: `if ctx.role == "police": return await next_protocol_message(ctx)` (just wait for the opponent's REVEAL) before running the full responder flow.
- **Files modified:** `src/pursuit/network/turn_commit.py`
- **Verification:** Measured directly — before the fix, `test_handshake_scent_digest_matches_before_any_move` took 136.00s (retry ladder exhaustion, then a symmetric-but-wrong outcome); after, 1.15s with a real completed game. Full suite re-run green afterward.
- **Committed in:** `22c75fc` (Task 3 commit)

**2. [Rule 1 - Bug prevention] `PendingAction` needed 3 fields beyond the plan's literal sketch**
- **Found during:** Task 3, while implementing `reveal_pending`
- **Issue:** The plan's `PendingAction` sketch has 5 fields (`move`, `barrier`, `plan`, `incoming_log`, `regime`). By the time `reveal_pending` runs, `ctx.state` has already advanced past `engine.resolve_turn` (the plan's own `turn_actions.py` spec calls `maybe_resolve` BEFORE `reveal_pending`, mirroring the initiator's position) — so re-deriving the composite action payload from `ctx.state` at reveal time would use the WRONG pre-turn cell, and re-tagging the REVEAL envelope's turn from `ctx.state.turn` would use the wrong (post-resolve) number.
- **Fix:** Added `action_payload: dict`, `h_commit: str`, `turn: int` to `PendingAction` — `reveal_pending` sends the EXACT already-committed dict, matches ACKs by the exact hash, and tags REVEAL with the exact pre-resolve turn.
- **Files modified:** `src/pursuit/network/commit_state.py`, `src/pursuit/network/turn_commit.py`
- **Verification:** `test_turn_commit_responder.py::test_reveal_pending_sends_the_stash_without_deciding_again` asserts the sent payload equals `pending.action_payload` exactly.
- **Committed in:** `fb7d46a` (fields added), `22c75fc` (used)

**3. [Rule 3 - Blocking] `turn_commit.py` needed a third sibling file**
- **Found during:** Task 3, after the first two-file split (turn_commit.py + turn_commit_wait.py) still measured 251/168/161/155 code lines across several iterations
- **Issue:** The plan pre-authorizes exactly TWO sibling files for the D-58 exchange (`turn_commit.py`, `turn_commit_wait.py`). Even after moving the wait primitives and the commit+ledger helper out, `turn_commit.py` alone still exceeded 150 lines (measured 251, then 168, then 161, then 154 across successive extractions).
- **Fix:** Created `turn_commit_send.py` (push/log/technical-loss mechanics), mirroring the ALREADY-CITED `handshake.py`/`handshake_wire.py`/`handshake_evaluate.py` three-file precedent — extended to a third sibling here for the same reason.
- **Files modified:** `src/pursuit/network/turn_commit_send.py` (new)
- **Verification:** `bash scripts/check_line_limit.sh` clean on all three files (turn_commit.py=147, turn_commit_wait.py=150, turn_commit_send.py=107).
- **Committed in:** `22c75fc` (Task 3 commit)

**4. [Rule 3 - Blocking] `test_language_pipeline.py` needed a split**
- **Found during:** Task 4, after fixing `_replay_from_log`'s shape-aware decode logic
- **Issue:** The plan's own critical_correctness_3 section specifies the exact edits needed to `test_language_pipeline.py`'s inline move-check and `_replay_from_log`; applying them pushed the file to 179 code lines.
- **Fix:** Split into `test_language_pipeline.py` (Figure-7 order test) + `test_language_pipeline_replay.py` (full two-peer game + replay), both well under 150.
- **Files modified:** `tests/integration/test_language_pipeline.py`, `tests/integration/test_language_pipeline_replay.py` (new)
- **Committed in:** `bf5d6ff` (Task 4 commit)

**5. [Rule 1 - Bug, out-of-plan fallout from Task 1, caught by the full suite] Three stale hardcoded tool-name sets**
- **Found during:** Task 2's full-suite verification run (not caused by Task 2 itself — caused by Task 1's new tool names, only surfaced once the full suite ran)
- **Issue:** `tests/unit/test_peer_runtime.py`, `tests/integration/test_secret_channel.py`, and `scripts/gate5_tunnel_smoke.py` each hardcoded the OLD five-tool name set, going stale the moment Task 1 added four new tools.
- **Fix:** Updated all three to the real nine-tool set.
- **Files modified:** `tests/unit/test_peer_runtime.py`, `tests/integration/test_secret_channel.py`, `scripts/gate5_tunnel_smoke.py`
- **Committed in:** `fb7d46a` (Task 2 commit, alongside the split it was verified with)

**6. [Rule 3 - Blocking] `test_turn_lifecycle.py`'s GATE-3 harness needed the toggle off**
- **Found during:** Task 3's full-suite verification run
- **Issue:** `test_full_lifecycle_init_to_game_over` drives only peer A's real `run_turn_loop`; peer B is a synthetic single-envelope injection whose own turn loop never runs (its own documented LIMITATION note, predating Phase 6). Once `security.commit_reveal` defaults true on the real shipped configs this test loads, A's `initiate()` waits forever for a COMMIT/ACK that B's never-running loop can never send.
- **Fix:** `ctx_a.security`/`ctx_b.security` overridden to `commit_reveal=False` right after construction — orthogonal to what GATE-3 (state-machine/turn-order) actually tests.
- **Files modified:** `tests/integration/test_turn_lifecycle.py`
- **Verification:** Both tests in the file pass; the file's own assertions (state path, outcome, event counts) are completely unchanged.
- **Committed in:** `22c75fc` (Task 3 commit)

---

**Total deviations:** 6 auto-fixed (1 measured deadlock bug fix, 1 field-completeness bug prevention, 2 forced file splits, 2 pre-existing-fallout/toggle fixes)
**Impact on plan:** All six were necessary for correctness or the hard 150-line gate. No scope creep — every fix stayed inside files this plan already owns or files the plan's own changes broke.

## Issues Encountered

The 136-second measured deadlock (deviation #1) was the one genuine surprise — everything else was either an anticipated line-limit split or foreseeable, mechanical fallout from Task 1's additive change. No blockers remain.

## User Setup Required

None — no external service configuration required. Everything in this plan runs on localhost, real FastMCP peers, zero credentials.

## Next Phase Readiness

- `turn_commit.py`'s three entry points, `PendingAction`/`CommitTurnState`'s shape, the composite action dict shape, and the `<log-file-stem>.ledger.jsonl` ledger convention are all documented above verbatim for 06-03 to consume.
- `FINAL_REVEAL`'s wire type and tool handler exist and enqueue correctly but carry no real body yet — 06-03's job.
- `game_id`/`game_uid` reconciliation (D-61) is still open — `commit_own_action` uses `ctx.game_uid` as an explicit interim choice, flagged for 06-03.
- Full repo gates green: 1184 passed / 1 pre-existing timing flake (confirmed passes in isolation, unrelated to this plan), 96.07% coverage (+0.26pp over the pre-plan baseline), `ruff check .` 0 violations, `scripts/check_line_limit.sh` clean, `scripts/check_no_llm_in_strategy.py` OK.
- No blockers for 06-03.

---
*Phase: 06-security-and-cryptography*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 15 created files verified present on disk; all 4 task commits
(`0711829`, `fb7d46a`, `22c75fc`, `bf5d6ff`) verified present in
`git log --oneline --all`. Full gate suite independently re-confirmed:
1184 passed / 1 pre-existing timing flake (isolated re-run: passes,
0.20s), 96.07% coverage, `ruff check .` 0 violations,
`scripts/check_line_limit.sh` clean, `scripts/check_no_llm_in_strategy.py`
OK.
