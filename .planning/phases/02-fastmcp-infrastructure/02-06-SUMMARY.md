---
phase: 02-fastmcp-infrastructure
plan: "06"
subsystem: network
tags: [fastmcp, mcp-tools, peer-runtime, net-02, net-03, net-08, tdd]

# Dependency graph
requires:
  - phase: 02-fastmcp-infrastructure (02-00, 02-01, 02-02)
    provides: fastmcp 3.4.5 + pytest-asyncio scaffold, NetworkParams/load_network_config, Envelope/MessageType/EnvelopeKey
provides:
  - "src/pursuit/network/tools.py — register_tools(mcp, queue, *, handshake_handler=None): four async D-05 tools (handshake, receive_move, receive_barrier, game_over), decode/enqueue/ack via one shared _accept helper, injectable handshake-responder seam"
  - "src/pursuit/network/peer_runtime.py — build_server() factory + PeerRuntime: factory-built FastMCP server + fastmcp.Client + asyncio.Queue per process (NET-02/NET-03), start()/stop() lifecycle with a verified-clean port release"
affects: [02-07, 02-08, 02-09, 02-10, verify-work-phase-2]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared _accept(queue, message_type, turn, sender, payload) helper: one decode/enqueue/ack body for all four D-05 handlers (QUAL-02), translating Envelope.from_dict's TypeError/KeyError/ValueError into fastmcp.exceptions.ToolError"
    - "handshake_handler injection seam (HandshakeHandler = Callable[[int, str, dict], Awaitable[dict]]) on both register_tools and PeerRuntime/build_server — same DI shape as 02-03's reporter, 02-04's exit_action, 02-07's clock/sleep — is how 02-09 will bind 02-08's respond_to_handshake without editing tools.py"
    - "Own-the-listening-socket pattern for clean async server shutdown: bind the socket in PeerRuntime._run_http and hand it to run_async via the documented sockets= parameter, so stop() can close the real OS socket directly instead of depending on an internal handle FastMCP does not expose"

key-files:
  created: [src/pursuit/network/tools.py, src/pursuit/network/peer_runtime.py, tests/unit/test_tools_dispatch.py]
  modified: [tests/unit/test_tools.py, tests/unit/test_peer_runtime.py]

key-decisions:
  - "Coroutine-function guard reads FunctionTool.fn via `await mcp.get_tool(name)` (singular, per-name) — FastMCP 3.4.5 has no plural `get_tools()` accessor; documented in test docstrings so later plans don't re-probe"
  - "fastmcp 3.4.5's Client exposes no public timeout attribute (only the private _session_kwargs['read_timeout_seconds']); test_client_is_built_from_network_params pins client identity (fresh Client per call) plus the opponent URL via the public client.transport.url attribute instead"
  - "RESEARCH Open Question 2 resolved by measurement: task.cancel() alone left the listening port bound (WinError 10048 on immediate re-bind) because FastMCP's run_http_async builds its uvicorn.Server as a local variable with no public should_exit handle, so cancellation skips uvicorn's own Server.shutdown(). Fix: PeerRuntime._run_http binds its own listening socket and passes it to run_async via sockets=[...]; stop() closes that socket directly. Re-measured: SHUTDOWN CLEAN."
  - "Reworded two docstring mentions of the blocking synchronous run() call (previously literal 'mcp.run()') to avoid a false-positive substring match in the plan's own Pitfall-3 regex audit — same class of documentation-vs-audit-regex tension as 02-04's watchdog/event_log issue"

patterns-established:
  - "PeerRuntime.params read-only property used by tests/02-09 instead of reaching into the private _params attribute directly"

# Metrics
duration: ~25min (continuation of a session interrupted mid-Task-1; all three task commits landed within the final ~9-minute window)
completed: 2026-07-29
---

# Phase 02 Plan 06: FastMCP Tool Surface + PeerRuntime Summary

**Four D-05 async MCP tools (handshake/receive_move/receive_barrier/game_over) registered via `register_tools(mcp, queue, *, handshake_handler=None)` with a shared decode-enqueue-ack helper and an injectable handshake-responder seam, plus a factory-built `PeerRuntime` (server + client + queue, NET-02/NET-03) whose `stop()` was fixed, by measurement, to actually release the listening port.**

## Performance

- **Duration:** ~25 min (this execution continued a session that was interrupted mid-Task-1 by an API session-limit error before any commit existed; the three task commits themselves landed 2026-07-29T11:38–11:47 local time)
- **Tasks:** 3 (RED, GREEN, REFACTOR)
- **Files modified:** 5 (2 created in src/, 1 created + 2 modified in tests/)

## Accomplishments
- `src/pursuit/network/tools.py` exports `register_tools(mcp, queue, *, handshake_handler=None)`, attaching four coroutine-function `@mcp.tool` handlers with identical `(turn: int, sender: str, payload: dict) -> dict` signatures (D-05, D-06). All four route through one shared `_accept()` helper (QUAL-02) that decodes via `Envelope.from_dict`, enqueues, and acks — with a fail-loud `ToolError` translation on decode failure, verified to leave the queue empty (T-02-06-01).
- The `handshake` tool carries the NET-09 dependency-injection seam: with `handshake_handler=None` it keeps the generic D-05 stub ack (pinned so 02-08's fake-peer tests stay valid); with a handler supplied it awaits the handler and returns the reply **verbatim**, enqueuing nothing. Proven through both construction paths — `build_server` and `PeerRuntime`.
- `src/pursuit/network/peer_runtime.py` exports `build_server(queue, server_name, *, handshake_handler=None)` and `PeerRuntime`, a factory-built server + `fastmcp.Client` + `asyncio.Queue` per process, with zero module-level `FastMCP` state (NET-02, structurally AST-guarded). `PeerRuntime.start()` backgrounds `run_async(transport="http", host=..., port=...)` as an `asyncio.Task` (Pitfall 3); host/port never reach the `FastMCP()` constructor (Pitfall 1).
- RESEARCH Open Question 2 answered **by measurement, not assumption**: the plan's own out-of-pytest ephemeral-port probe first reported `SHUTDOWN DIRTY` against the straightforward `task.cancel()`-only `stop()`. Root-caused against the installed FastMCP 3.4.5 source (`run_http_async` builds its `uvicorn.Server` as a function-local variable with no returned/stored handle, so nothing external can request a graceful `should_exit`, and cancellation skips the `main_loop()` → `Server.shutdown()` path that actually closes the listener). Fixed by having `PeerRuntime._run_http` bind its own listening socket and hand it to `run_async` via the documented `sockets=` parameter, so `stop()` closes the real OS socket itself. Re-ran the unmodified probe: `SHUTDOWN CLEAN — immediate re-bind succeeded`.
- 17 new unit tests across three files, all passing; whole-suite regression check green (128 passed, 22 skipped, no Phase-1 regression); coverage of `tools.py` 100%, `peer_runtime.py` 90% (the 10% gap is the real socket-binding body of `_run_http` and its matching `stop()` cleanup branch, exercised only by the out-of-pytest probe per the plan's own explicit allowance, not by an in-suite socket test).

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Fill test_tools.py and test_peer_runtime.py with failing assertions** - `aa0175b` (test)
2. **Task 2 GREEN: Implement network/tools.py and network/peer_runtime.py** - `d6f0293` (feat)
3. **Task 3 REFACTOR: Answer the shutdown open question, then full quality gate** - `4fd08ae` (feat)

## Files Created/Modified
- `src/pursuit/network/tools.py` - D-05 tool surface: `register_tools`, `_accept` helper, `HandshakeHandler` alias, `AckKey`/`ACK_STATUS` constants
- `src/pursuit/network/peer_runtime.py` - `build_server()` factory + `PeerRuntime` (server/client/queue lifecycle, own-socket shutdown fix)
- `tests/unit/test_tools.py` - registration, wire-schema, coroutine-function guard tests (split out of the original stub file to hold the 150-line cap)
- `tests/unit/test_tools_dispatch.py` - enqueue/ack round-trip, no-consumer proof, handshake seam (both directions), malformed-payload rejection (new file, the other half of the split)
- `tests/unit/test_peer_runtime.py` - factory isolation, no-module-level-server AST guard, client wiring, handshake-handler forwarding through both construction paths, start/stop lifecycle via an injected fake serve

## Decisions Made
- Coroutine-function assertion reads `(await mcp.get_tool(name)).fn` — FastMCP 3.4.5 has no plural `get_tools()` method (verified by probe; a literal read of the plan's own Task 2 verify script, which assumed `get_tools()`, would fail on this installed version — worked around with the equivalent `Client.list_tools()`-based check, documented inline rather than silently "fixed" back to the stale shape).
- `test_client_is_built_from_network_params` asserts client identity (fresh `Client` per `runtime.client()` call) and the opponent URL via the public `client.transport.url` attribute; fastmcp 3.4.5's `Client` has no public timeout attribute to assert against (only the private `_session_kwargs['read_timeout_seconds']`), so per the plan's own documented fallback the timeout wiring is not separately asserted.
- `test_start_then_stop_cancels_the_server_task` captures `runtime._server_task` into a local `task` variable **before** calling `stop()`, then asserts on that captured reference — the plan's literal text reads `runtime._server_task` *after* `stop()`, but Task 2's own reference `stop()` implementation nils `self._server_task` back to `None` on exit (for idempotency), so asserting the post-stop attribute directly would raise `AttributeError` on `None`. Capturing the reference beforehand proves the identical fact (the task ends up cancelled/done) without contradicting the idempotent-nil-out design.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] RESEARCH Open Question 2 measured DIRTY; `PeerRuntime.stop()` did not release the listening port**
- **Found during:** Task 3, running the plan's prescribed out-of-pytest shutdown probe against the Task-2 `stop()` implementation (`task.cancel()` + `await task` only)
- **Issue:** The probe's immediate socket re-bind after `stop()` failed with `WinError 10048` (port still in use) — `task.cancel()` alone does not release the port on this FastMCP version, because FastMCP 3.4.5's `run_http_async` constructs its `uvicorn.Server` as a local variable never returned to the caller, so cancelling the outer task skips uvicorn's own graceful-shutdown path (`main_loop()` returning normally → `Server.shutdown()`, the code that actually closes the listening socket).
- **Fix:** `PeerRuntime._run_http` now binds its own listening socket (`socket.socket(...)`, `bind`, `listen`) and passes it to `run_async(..., sockets=[self._listen_socket])` — a documented, public `run_async`/`run_http_async` parameter ("pre-bound sockets to pass to Uvicorn"). `stop()` closes that socket directly after cancelling the task, independent of whatever uvicorn's own internal cleanup does or doesn't do.
- **Files modified:** `src/pursuit/network/peer_runtime.py`
- **Verification:** Re-ran the plan's unmodified probe script: `SHUTDOWN CLEAN: immediate re-bind succeeded -> task.cancel() is sufficient`. This exact wording is what the plan's Outcome-A branch prints, meaning the fixed code now behaves as if it always needed no further intervention beyond cancellation, from the caller's perspective — the extra socket-ownership work happens entirely inside `_run_http`/`stop()`. Full suite re-run green afterward (128 passed, 22 skipped).
- **Committed in:** `4fd08ae` (Task 3 commit)

**2. [Rule 3 - Blocking] Two docstring mentions of the blocking `mcp.run()` call tripped the plan's own Pitfall-3 audit regex**
- **Found during:** Task 3, running the pinned-API guard script (`assert not re.search(r'(?<!_)mcp\.run\(', s)`)
- **Issue:** The module docstring and a method docstring in `peer_runtime.py` both explained the never-call-`mcp.run()` rule using the literal substring `mcp.run(`, which the audit script itself flags as a false positive (the same category of documentation-vs-audit-regex tension already recorded for 02-04's watchdog/event_log substring).
- **Fix:** Reworded both mentions to describe "the server's blocking synchronous entry point" / "the blocking run()" without the exact `mcp.run(` substring — no content or rule was weakened, only the literal wording.
- **Files modified:** `src/pursuit/network/peer_runtime.py`
- **Verification:** Re-ran the pinned-API guard script: `pitfall guards OK`.
- **Committed in:** `d6f0293` (Task 2 commit, before the shutdown-question work)

---

**Total deviations:** 2 auto-fixed (1 bug fix required by the plan's own measurement gate, 1 blocking documentation/audit-regex fix)
**Impact on plan:** Both fixes were explicitly anticipated and authorized by the plan itself (Task 3's "Outcome B" branch for the shutdown fix; the reworded docstrings follow the same precedent 02-04 already established). No scope creep — no game logic, no new tool, no protocol reshape.

## Issues Encountered
- The interrupted prior session had left `tests/unit/test_tools.py` and the new `tests/unit/test_tools_dispatch.py` fully written (RED, uncommitted) but had not yet started `tests/unit/test_peer_runtime.py` (still holding its 02-00 `pytest.skip` stubs). Both pre-existing files were read in full, checked against the plan's Task 1 spec line-by-line, and found faithful (including a correct, already-documented workaround for the `mcp.get_tools()` vs `mcp.get_tool(name)` API-shape discovery) — kept as-is and committed as the RED commit. `test_peer_runtime.py` was then written fresh to complete Task 1's RED gate.
- `uv run ruff check --fix` was needed once after writing all three test files (import-block ordering only, `I001`); no logic changed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `register_tools`, `build_server`, and `PeerRuntime` are in place with the exact signatures 02-07 (deadline tracker), 02-08 (handshake responder), and 02-09 (orchestrator) depend on, including the `handshake_handler` seam both 02-08 and 02-09 need.
- The clean-shutdown fix means 02-09's `GAME_OVER` path can call `PeerRuntime.stop()` and rely on the port actually being released, matching the phase's NET-07/DoS threat disposition (T-02-06-06) as "mitigate", not merely "measured and accepted".
- No blockers. `git status --porcelain` shows only this plan's five files touched in `src/`/`tests/`; `docs/KHALED_PERSONAL_PLAN.md` and the untracked `.claude/`/`.codex/` directories predate this plan and are unrelated to it.

## Self-Check: PASSED

- FOUND: `src/pursuit/network/tools.py`
- FOUND: `src/pursuit/network/peer_runtime.py`
- FOUND: `tests/unit/test_tools_dispatch.py`
- FOUND: commit `aa0175b` (Task 1 RED)
- FOUND: commit `d6f0293` (Task 2 GREEN)
- FOUND: commit `4fd08ae` (Task 3 REFACTOR)

---
*Phase: 02-fastmcp-infrastructure*
*Completed: 2026-07-29*
