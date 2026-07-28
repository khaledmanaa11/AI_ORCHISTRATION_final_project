# Phase 2: FastMCP Infrastructure - Research

**Researched:** 2026-07-28
**Domain:** FastMCP (Python MCP framework) peer-to-peer symmetric server+client, asyncio orchestration, state machines, watchdog/deadline resilience, config integrity hashing.
**Confidence:** HIGH for the FastMCP API surface (verified against the exact pinned stable release source on GitHub and cross-checked with PyPI's JSON API); MEDIUM-HIGH for the composed "both server and client in one process" pattern (synthesized from verified primitives — no official FastMCP example matches our exact symmetric-peer topology); HIGH for repo-fit findings (read directly from this repo's existing code).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Topology & startup**
- **Per-agent orchestrator**: each agent process embeds its own orchestrator/main loop running the turn state machine. No third referee process — NET-04's "single entry point" is satisfied per agent, consistent with the P2P no-central-server rule.
- **Dev launcher + standalone**: a small dev script starts both peers locally for fast iteration, but each agent also starts standalone with one command in its own terminal — the standalone path is the league path.
- **Transport: FastMCP streamable HTTP** on configured localhost ports — the same transport ngrok tunnels in Phase 5, so cloud exposure requires zero transport changes.
- **Endpoints live in per-agent config** (`config/police/`, `config/thief/`): own listen port + opponent URL. NOT in the shared `game_params.json` (whose byte-for-byte identity must hold across sides).

**Tool surface & protocol**
- **Full tool surface now, stub bodies**: define `handshake`, `receive_move`, `receive_barrier`, `game_over` with real signatures in Phase 2; later phases fill in behavior but never reshape the protocol.
- **Typed message envelope** `{type, turn, sender, payload}` for every message kind. Phase 2 uses `type=move` with payload `{x, y}`; hints (Phase 4) and commits (Phase 6) become new types in the same envelope.
- **Push turn-passing**: after choosing its move, an agent calls the opponent's `receive_move`; that incoming call wakes the opponent's turn. No polling loops; the deadline tracker wraps the wait.
- **Handshake = connectivity + config hash**: the game-start handshake proves reachability AND exchanges a SHA-256 of the shared game config, satisfying NET-09 in the same step. Phase 6 later adds the Step-0 declaration to this handshake.

**State machine**
- **States**: INIT → HANDSHAKE → MY_TURN ↔ WAIT_OPPONENT → GAME_OVER, plus ERROR. Commit-reveal sub-states are inserted by Phase 6 when they become real.
- **Illegal transitions (NET-05): severity-based** — every attempt is logged + rejected; recoverable ones (duplicate message, out-of-order retry) keep the game running; protocol violations escalate to ERROR and end the game.
- **Reporting**: structured JSONL event log per agent + human-readable console echo. The JSONL log is the seed of the Phase-7 `log_<game_id>` artifact and replay viewer.
- **Implementation: State enum + explicit allowed-transitions dict** in a small module. No FSM library dependency; trivially unit-testable; fits the 150-line limit.

**Resilience**
- **Deadline (NET-06)**: on a missed 30s response deadline, retry N times with backoff (N and backoff from config, never source), then declare a **technical win**, log the evidence, and end cleanly.
- **Watchdog (NET-07): persist-every-turn** — game state and JSONL log are flushed to disk every turn, so a crash loses nothing; the watchdog is a **background thread in each agent** watching a last-activity timestamp against the 60s threshold; on freeze it writes a final incident record and exits cleanly.
- **Config check (NET-09)**: SHA-256 of `game_params.json` exchanged during handshake; any mismatch **aborts before move 1** with a clear logged report.

### Claude's Discretion
- Module layout, naming, and file split (within the 150-line limit)
- Exact retry count / backoff defaults — config values within the negotiable ranges
- Test structure and mocking approach for the peer-to-peer calls

### Specifics
- Timeout values come from `docs/PARAMETERS.md`: response timeout 30 s, watchdog threshold 60 s — both negotiable, both config-driven, never hardcoded.
- The two-terminal standalone startup mirrors the real league; the dev launcher is a convenience only and must not become a referee.

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NET-01 | Cop and thief run as two separate processes under `config/police/` vs `config/thief/` | Two independent `uv run` invocations of the same entry point, each pointed at its own config dir via role/env |
| NET-02 | No shared runtime state between the two agents | Each process gets its own `FastMCP` instance, own `asyncio` event loop, own in-memory queues — nothing imported as a live singleton across processes |
| NET-03 | Each agent is simultaneously a FastMCP server and client | Verified: `FastMCP` (server) + `fastmcp.Client` (client) both run in one asyncio event loop via `run_async()` as a background task |
| NET-04 | Orchestrator is the single entry point, driving turn order via a state machine | `State` enum + allowed-transitions dict pattern (CONTEXT-locked); one `main.py`/`PeerRuntime` per agent |
| NET-05 | Every illegal state transition is reported | Transition function logs + rejects; severity-based (recoverable vs ERROR) per CONTEXT |
| NET-06 | Deadline tracker prevents freezing while waiting on the opponent | `asyncio.wait_for()` around the incoming-queue wait; `Client(..., timeout=...)` bounds outgoing calls; retry/backoff from config |
| NET-07 | Watchdog monitors process crashes and rescues data | Daemon `threading.Thread` polling a last-activity timestamp; `os._exit()` on freeze after writing incident record |
| NET-08 | A geometric message sent over localhost is received and decoded correctly | `@mcp.tool` handler + `Client.call_tool()` round-trip verified against real FastMCP source |
| NET-09 | Config file verified byte-for-byte identical on both sides | SHA-256 of canonical-JSON-reserialized `game_params.json`, exchanged in the `handshake` tool call |
</phase_requirements>

---

## Summary

Phase 2 wires the P2P transport layer on top of the pure Phase-1 game engine. The project has **no FastMCP dependency installed yet** — `pyproject.toml` currently declares `dependencies = []` and `uv.lock` has no `fastmcp` or `mcp` entries. The first concrete task for the planner is `uv add fastmcp` (which resolves the `fastmcp` meta-package → `fastmcp-slim[client,server]`, currently PyPI version **3.4.5**, confirmed directly against PyPI's JSON API and cross-checked against the exact `v3.4.5` git tag source) plus `uv add --dev pytest-asyncio` for async test support.

FastMCP's core API is small and stable across the 2.x→3.x line: `FastMCP(name)` + `@mcp.tool` to build a server, `mcp.run(transport=...)` / `await mcp.run_async(transport=...)` to serve it, and `fastmcp.Client(url_or_server, timeout=...)` as an async-context-manager client whose `call_tool()` returns a `CallToolResult` with `.data` (structured), `.content` (raw content blocks), and `.is_error`. The one recurring trap — confirmed directly in the pinned source, and contradicted by some web summaries scraped from older docs — is that **`host`/`port` are NOT constructor arguments** on `FastMCP()` in the version this project will install; passing them raises `TypeError`. They must be passed to `run()`/`run_async()`/`run_http_async()` at call time, or read from `FASTMCP_HOST`/`FASTMCP_PORT` env vars. Since CONTEXT.md locks endpoints into per-agent config JSON (not env vars, not `game_params.json`), the plan should read `host`/`port` from a new per-agent config file and pass them explicitly to `run_async(transport="http", host=..., port=...)`.

The "simultaneously server and client" requirement (NET-03) is answerable with one asyncio event loop per process: launch `mcp.run_async(transport="http", ...)` as a background `asyncio.Task`, and run the orchestrator (which owns a `fastmcp.Client` pointed at the opponent) as a sibling coroutine on the *same* loop — never call the blocking `mcp.run()` from inside async code (verified: it wraps `anyio.run()` internally and will raise if called from a running loop). The push-turn-passing pattern CONTEXT.md locks in maps cleanly onto an `asyncio.Queue`: an **`async def`** tool handler (not a plain `def`, which FastMCP silently runs in a worker threadpool — verified in source) enqueues the incoming envelope and returns an immediate ack; the orchestrator awaits the queue with `asyncio.wait_for(..., timeout=response_timeout)` to implement the deadline tracker (NET-06). For testing without a live network (research question 7), FastMCP ships an official **in-memory transport** — `Client(mcp_server_instance)` — that talks to the server object directly inside the test process, with a real worked example (`pytest-asyncio`, `asyncio_mode = "auto"`, `async def test_x(client): ...`) pulled from FastMCP's own repository.

**Primary recommendation:** `uv add fastmcp` (locks whatever resolves, expected 3.4.5) + `uv add --dev pytest-asyncio`; build a `src/pursuit/network/` package with one FastMCP server instance per process, a `PeerRuntime` that runs the server via `run_async()` as a background task on the same event loop as an `fastmcp.Client`-driven orchestrator, `async def` tool handlers that only enqueue onto an `asyncio.Queue`, and a `State` enum + transitions-dict state machine gating every queue consumption. Test everything with `Client(mcp)` in-memory — never a live socket.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastmcp` | **not yet installed** — `uv add fastmcp` resolves to **3.4.5** as of this research (verified via `https://pypi.org/pypi/fastmcp/json`, `info.version`); requires Python `>=3.10` (matches `pyproject.toml`'s `>=3.10`) | Server (`FastMCP`, `@mcp.tool`) + client (`Client`, `call_tool`) for MCP over streamable HTTP | This is the project's mandated protocol library (CLAUDE.md: "There is no 'MCB' — the protocol is MCP via FastMCP") |
| `pytest-asyncio` | not yet installed — add as dev dependency, `>=1.2.0` per FastMCP's own example `pyproject.toml` | Enables `async def test_...` without manual `@pytest.mark.asyncio` when `asyncio_mode = "auto"` | Required by FastMCP's own documented and repo-verified testing pattern (`examples/testing_demo`) |
| Python stdlib: `asyncio` | stdlib | Single event loop per agent process; `Queue`, `wait_for`, `create_task` | No dependency needed; this is exactly what FastMCP's own async server/client primitives are built on |
| Python stdlib: `threading` | stdlib | Watchdog background daemon thread | Segal §15: multithreading for I/O-bound / monitoring work |
| Python stdlib: `hashlib` | stdlib | SHA-256 of canonical-JSON config for NET-09 | No third-party crypto library needed for a plain digest |
| Python stdlib: `json` | stdlib | Canonical JSON re-serialization (`sort_keys=True, separators=(",",":")`), JSONL event log | Matches the project's already-locked canonical-JSON convention (SEC-03, Phase 6) |
| Python stdlib: `os` (`os.fsync`, `os._exit`) | stdlib | Durable JSONL flush; watchdog hard-exit on freeze | Standard, portable (Windows-compatible) primitives for these exact needs |
| Python stdlib: `dataclasses`, `enum` | stdlib | `Envelope` message shape, `State`/`MessageType` enums | Matches Phase 1's established pattern (`GameState`, `Direction`, `Outcome`) |

### Supporting (dev tooling only)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `uv` | system | Package/run manager | `uv add fastmcp`, `uv add --dev pytest-asyncio`, `uv run pytest`, `uv run ruff check` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `asyncio.Queue` push-turn-passing | Polling loop (client repeatedly asks "has the opponent moved yet?") | CONTEXT.md explicitly rules this out ("No polling loops"); polling also wastes the response-timeout budget and complicates the deadline tracker |
| One asyncio event loop per process (server task + client coroutine together) | Server on a background OS thread with its own loop, client on the main thread | Cross-thread `asyncio.Queue` is not thread-safe (would need `call_soon_threadsafe`/`run_coroutine_threadsafe`); the single-loop approach is simpler and is exactly what FastMCP's own `run_async()` is designed to be awaited alongside |
| Hand-rolled FSM library | `transitions` PyPI package | CONTEXT.md explicitly locks "State enum + explicit allowed-transitions dict... No FSM library dependency" — do not introduce one |
| `watchdog` PyPI package (filesystem watcher) | stdlib `threading.Thread` polling a timestamp | Wrong tool — that package watches filesystem events, not process/turn liveness; CONTEXT.md's "watchdog" is a liveness monitor, not a file watcher |

**Installation:**
```bash
uv add fastmcp
uv add --dev pytest-asyncio
```

---

## Architecture Patterns

### Recommended Project Structure

```
src/pursuit/
├── network/                        # NEW in Phase 2
│   ├── __init__.py
│   ├── envelope.py                 # Envelope dataclass {type, turn, sender, payload}; MessageType enum
│   ├── tools.py                    # @mcp.tool definitions: handshake, receive_move, receive_barrier, game_over (stub bodies)
│   ├── peer_runtime.py             # owns the FastMCP instance + Client; runs server via run_async() as background task
│   ├── state_machine.py            # State enum + ALLOWED_TRANSITIONS dict + transition() with severity-based rejection (NET-05)
│   ├── deadline.py                 # asyncio.wait_for wrapper + retry/backoff loop; raises/declares technical win (NET-06)
│   ├── watchdog.py                 # daemon thread watching last-activity timestamp; incident record + os._exit (NET-07)
│   ├── config_hash.py              # canonical-JSON SHA-256 of game_params.json (NET-09)
│   └── event_log.py                # JSONL writer: flush()+os.fsync() per turn (NET-07 persist-every-turn)
├── shared/
│   └── network_config.py           # loads per-agent network.json: host, port, opponent_url, retry_count, backoff_seconds
main.py (or src/pursuit/main.py)    # single entry point per agent (NET-04); reads role.json + network_config, builds PeerRuntime
scripts/
└── dev_launch.py                   # convenience: spawns both agent processes locally; NOT a referee (CONTEXT-locked)

config/
├── police/
│   └── network.json                 # NEW — {"host": "127.0.0.1", "port": <police_port>, "opponent_url": "http://127.0.0.1:<thief_port>/mcp"}
└── thief/
    └── network.json                 # NEW — mirrored, port/opponent_url swapped (legitimately different, like role.json)
```

Each file above is a single-responsibility module sized to comfortably fit the 150-line limit — this split is a **recommendation** under CONTEXT.md's "Claude's Discretion: module layout, naming, and file split."

### Pattern 1: Server construction and tool registration

**What:** One `FastMCP` instance per process; tools registered with `@mcp.tool`. Async tool bodies for anything that must touch the shared event-loop state (queues); sync-body tools are safe only for pure, fast, non-shared-state work.
**When to use:** Always, for every exposed tool (`handshake`, `receive_move`, `receive_barrier`, `game_over`).
**Verified against:** pinned stable tag `v3.4.5` of `PrefectHQ/fastmcp` (`fastmcp_slim/fastmcp/server/server.py`, `fastmcp_slim/fastmcp/tools/function_tool.py`) and the official quickstart/tools docs.

```python
# Source: gofastmcp.com/servers/tools (verified against v3.4.5 source: fastmcp_slim/fastmcp/tools/function_tool.py)
from fastmcp import FastMCP

mcp = FastMCP("pursuit-peer")

@mcp.tool
async def receive_move(turn: int, sender: str, payload: dict) -> dict:
    """Opponent's move envelope arrives here. Must be `async def` — see Pitfall 2."""
    await incoming_queue.put({"turn": turn, "sender": sender, "payload": payload})
    return {"status": "ack"}
```

### Pattern 2: Running server + client in the same process (NET-03)

**What:** `mcp.run()` is a **synchronous, blocking** call — verified source: it wraps `anyio.run(partial(self.run_async, ...))` and therefore **cannot** be called from inside a running event loop. The async twin, `await mcp.run_async(transport=..., host=..., port=...)`, runs forever inside the *current* loop and is exactly what you background with `asyncio.create_task()` so the same loop can also drive a `fastmcp.Client` toward the opponent.
**When to use:** Every agent process — this is the concrete answer to "how do server and client coexist without deadlock."
**Verified against:** `v3.4.5` `fastmcp_slim/fastmcp/server/mixins/transport.py` (`run`, `run_async`, `run_http_async` definitions).

```python
# Source: v3.4.5 fastmcp_slim/fastmcp/server/mixins/transport.py (run/run_async/run_http_async signatures)
import asyncio
from fastmcp import FastMCP, Client

mcp = FastMCP("pursuit-peer")
# ... @mcp.tool definitions ...

async def peer_main(my_host: str, my_port: int, opponent_url: str, response_timeout: float):
    server_task = asyncio.create_task(
        mcp.run_async(transport="http", host=my_host, port=my_port)
    )
    async with Client(opponent_url, timeout=response_timeout) as client:
        result = await client.call_tool(
            "receive_move", {"turn": 1, "sender": "cop", "payload": {"x": 1, "y": 2}}
        )
    # ... orchestrator loop continues on this same event loop ...
    server_task.cancel()

asyncio.run(peer_main("127.0.0.1", 8001, "http://127.0.0.1:8002/mcp", 30.0))
```

**Do NOT** call `mcp.run()` anywhere inside this coroutine tree — verified: it creates its own event loop via `anyio.run()` and will error (or silently create a second, disconnected loop) if invoked from async code. Only `run_async()` is safe here.

### Pattern 3: Push turn-passing via `asyncio.Queue` (deadlock/reentrancy safety)

**What:** The incoming tool handler must never itself block waiting on the opponent (that would create a request-handling deadlock inside the ASGI server). It enqueues and returns immediately; a *separate* orchestrator coroutine consumes the queue.
**Why `async def`, not `def`:** Verified in `v3.4.5` `fastmcp_slim/fastmcp/tools/function_tool.py`: a plain `def` tool body is executed via `call_sync_fn_in_threadpool` — i.e. in a **worker thread**, not on the main event loop. A worker thread pushing onto a plain `asyncio.Queue` created on the main loop is not safe without `loop.call_soon_threadsafe()`/`run_coroutine_threadsafe()`. Making the handler `async def` keeps it on the same event loop as the queue and the orchestrator, so a plain `asyncio.Queue` is sufficient — no cross-thread synchronization needed.

```python
# Source: synthesized from verified FastMCP async-tool execution semantics
# (fastmcp_slim/fastmcp/tools/function_tool.py: "Sync function: run in threadpool")
incoming_queue: asyncio.Queue = asyncio.Queue()

@mcp.tool
async def receive_move(turn: int, sender: str, payload: dict) -> dict:
    await incoming_queue.put({"turn": turn, "sender": sender, "payload": payload})
    return {"status": "ack"}

async def wait_for_opponent(deadline_seconds: float) -> dict:
    """NET-06 deadline tracker: bounds the WAIT_OPPONENT state."""
    return await asyncio.wait_for(incoming_queue.get(), timeout=deadline_seconds)
```

### Pattern 4: Client call with timeout (NET-06)

**What:** `Client(...)` accepts a `timeout: datetime.timedelta | float | int | None` at construction (applies to all requests), and `call_tool(..., timeout=...)` accepts the same type **per call**, overriding the client-level default. On timeout, `call_tool()` raises `MCPError` (imported as `from mcp import MCPError` — the underlying MCP SDK's exception, re-exported through `fastmcp`), not a bare `asyncio.TimeoutError`.
**Verified against:** `v3.4.5` `fastmcp_slim/fastmcp/client/client.py` (`__init__` signature, line ~264) and `fastmcp_slim/fastmcp/client/mixins/tools.py` (`call_tool` signature + docstring `Raises: MCPError: If the tool call request results in a TimeoutError | JSONRPCError`).

```python
# Source: v3.4.5 fastmcp_slim/fastmcp/client/mixins/tools.py (call_tool signature + Raises docstring)
from mcp import MCPError
from fastmcp import Client
from fastmcp.exceptions import ToolError  # raised for tool-side errors, distinct from MCPError

async with Client(opponent_url, timeout=response_timeout_seconds) as client:
    try:
        result = await client.call_tool("receive_move", payload, timeout=response_timeout_seconds)
    except MCPError:
        # deadline tracker: this is the "missed response deadline" signal (NET-06)
        ...
    except ToolError:
        # opponent's tool body raised — a different failure mode, not a timeout
        ...
```

### Pattern 5: In-memory testing (no live network) — research question 7

**What:** FastMCP ships a first-class **in-memory transport**: pass the `FastMCP` server instance itself (not a URL) into `Client()`. This shares no socket, no subprocess — it's a direct in-process call path, ideal for the project's "no test depends on a live network" rule.
**Verified against:** `gofastmcp.com` testing patterns doc + a real, current worked example pulled directly from the FastMCP repo: `examples/testing_demo/server.py` + `examples/testing_demo/tests/test_server.py` + `examples/testing_demo/pyproject.toml`.

```python
# Source: PrefectHQ/fastmcp examples/testing_demo/tests/test_server.py (verified, current repo example)
import pytest
from fastmcp import Client

@pytest.fixture
async def client():
    from pursuit.network.tools import mcp  # the module-level FastMCP() instance
    async with Client(mcp) as client:
        yield client

async def test_receive_move_acks(client: Client):
    result = await client.call_tool("receive_move", {"turn": 1, "sender": "cop", "payload": {"x": 0, "y": 0}})
    assert result.data == {"status": "ack"}
```

```toml
# Source: PrefectHQ/fastmcp examples/testing_demo/pyproject.toml (verified, current)
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```
Add `asyncio_mode = "auto"` to this project's existing `[tool.pytest.ini_options]` block (currently `testpaths = ["tests"]`, `addopts = "--tb=short"` — no asyncio mode set) so `async def test_...` functions run without a `@pytest.mark.asyncio` decorator on every one.

**Faking a peer for state-machine/deadline tests:** for illegal-transition and timeout-path tests that don't need a real opponent, drive the `state_machine.transition()` function and `deadline.wait_for_opponent()` directly with a **fake/never-filled** `asyncio.Queue` (or `asyncio.wait_for` a never-resolving future) — no FastMCP transport involved at all. For "opponent sends a malformed/duplicate/out-of-order message" tests, call `receive_move`/`receive_barrier` directly through the in-memory `Client(mcp)` with crafted arguments; no second process needed.

### Pattern 6: Byte-for-byte config verification (NET-09)

**What:** `config/police/game_params.json` and `config/thief/game_params.json` are already guaranteed byte-identical by Phase 1 (D-06, verified with `diff`). For the handshake hash, **hash the canonically-re-serialized JSON content, not the raw file bytes.**

**Recommendation and reasoning:** Two options exist:
1. **Raw file bytes** (`hashlib.sha256(path.read_bytes()).hexdigest()`) — simplest, and correct today because Phase 1 already enforces byte-identical files.
2. **Canonical JSON** (`hashlib.sha256(json.dumps(json.load(f), sort_keys=True, separators=(",", ":")).encode()).hexdigest()`) — hashes the *semantic* content, immune to incidental formatting drift (trailing newline, indentation, key order) that a future edit to one side's file (but not the other) could introduce without failing the `diff`-based Phase-1 check if someone bypasses it.

**Recommend option 2 (canonical JSON)** for two reasons: (a) it is **already the project's locked convention** for hash inputs — SEC-03 mandates `sort_keys=True, separators=(",", ":")` for the Phase-6 commit-reveal hash, and reusing the identical serialization function for NET-09 avoids maintaining two different "canonical form" implementations; (b) it decouples the integrity check from file-system formatting accidents, which is exactly the failure mode RULES.md flags as the most common real cause of a hash mismatch ("a canonical-JSON serialization bug, not fraud" — RULES.md quick-reference list, item 4). Confidence: MEDIUM-HIGH — this is project-logic synthesis, not a FastMCP API fact, but it is directly supported by the project's own already-locked SEC-03 decision.

```python
# Source: project convention (SEC-03 canonical JSON), applied to NET-09
import hashlib, json
from pathlib import Path

def config_digest(path: "Path | str") -> str:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### Pattern 7: State machine (State enum + transitions dict) — NET-04, NET-05

**What:** CONTEXT.md locks this exact shape. No FSM library.

```python
# Source: project decision (CONTEXT.md "Implementation: State enum + explicit allowed-transitions dict")
from enum import Enum

class State(Enum):
    INIT = "init"
    HANDSHAKE = "handshake"
    MY_TURN = "my_turn"
    WAIT_OPPONENT = "wait_opponent"
    GAME_OVER = "game_over"
    ERROR = "error"

ALLOWED_TRANSITIONS: dict[State, set[State]] = {
    State.INIT: {State.HANDSHAKE},
    State.HANDSHAKE: {State.MY_TURN, State.WAIT_OPPONENT, State.ERROR},
    State.MY_TURN: {State.WAIT_OPPONENT, State.GAME_OVER, State.ERROR},
    State.WAIT_OPPONENT: {State.MY_TURN, State.GAME_OVER, State.ERROR},
    State.GAME_OVER: set(),
    State.ERROR: set(),
}

class TransitionSeverity(Enum):
    RECOVERABLE = "recoverable"   # duplicate/out-of-order retry — logged + rejected, game continues
    PROTOCOL_VIOLATION = "protocol_violation"  # escalates to ERROR, ends the game

def transition(current: State, target: State, *, log) -> State:
    """NET-05: every illegal attempt is reported. Legal moves apply; illegal ones
    are logged with a severity and either rejected (state unchanged) or escalated
    to ERROR, per CONTEXT.md's severity-based policy."""
    if target in ALLOWED_TRANSITIONS[current]:
        return target
    log.illegal_transition(current, target)  # NET-05 — always reported
    return current  # or State.ERROR for protocol_violation severity — see event_log.py schema
```

### Pattern 8: Watchdog as a background daemon thread — NET-07, Windows caveats

**What:** A `threading.Thread(daemon=True)` polls a shared last-activity timestamp (updated by the orchestrator every turn) against the config-driven `watchdog_threshold` (60 s default, Table 19 row 7). On freeze, it writes a final incident record and force-exits.

**Windows-specific caveats (general Python/OS knowledge, not FastMCP-specific — HIGH confidence, standard library semantics):**
- `os._exit(code)` terminates the process immediately, skipping `atexit` handlers, `finally` blocks, and non-daemon-thread joins. This is the **correct** choice for a watchdog: a plain `sys.exit()` called from a non-main thread only raises `SystemExit` in *that thread* — it does **not** terminate the process if the main thread (running the asyncio loop / uvicorn server) is itself frozen, which is precisely the freeze scenario the watchdog exists to escape.
- Windows does not support POSIX `SIGALRM` and has a much smaller usable signal set than Linux (essentially `SIGINT`/`SIGBREAK` reliably; `SIGTERM` can be registered but is not reliably delivered the way it is on POSIX for externally-signalled shutdown). Do not build the watchdog around Unix signals — the daemon-thread + timestamp-polling design CONTEXT.md already locks in sidesteps this entirely, which is a good reason to keep it that way on this Windows dev box.
- Write the incident record (and flush/fsync it) **before** calling `os._exit()` — once `os._exit()` runs, no further Python code executes, including any buffered-but-unflushed file writes.

```python
# Source: standard Python threading/os semantics (Windows-portable; not FastMCP-specific)
import os, threading, time

class Watchdog:
    def __init__(self, threshold_seconds: float, on_freeze):
        self._last_activity = time.monotonic()
        self._threshold = threshold_seconds
        self._on_freeze = on_freeze
        self._thread = threading.Thread(target=self._run, daemon=True)

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        while True:
            time.sleep(1.0)
            if time.monotonic() - self._last_activity > self._threshold:
                self._on_freeze()   # write incident record, flush+fsync JSONL log
                os._exit(1)         # hard-exit; do not use sys.exit() from a worker thread
```

### Pattern 9: JSONL event log (persist-every-turn) — NET-07

**What:** Flush + `os.fsync` after every write so a crash mid-game loses nothing, matching the CONTEXT-locked "persist-every-turn" watchdog strategy.

```python
# Source: standard Python file-durability idiom (os.fsync), applied per CONTEXT-locked persist-every-turn policy
import json, os
from pathlib import Path

def append_event(log_path: "Path | str", record: dict) -> None:
    line = json.dumps(record, sort_keys=True, separators=(",", ":"))
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())
```

**Minimal schema seed** (extends cleanly for Phase 4 hints, Phase 6 commit-reveal, Phase 7 replay viewer — MEDIUM confidence, this is a synthesis of the CONTEXT-locked envelope shape + REPORT-09/rule-20 "Verified OK" replay requirement, not a FastMCP fact):

```json
{
  "game_uid": "…",
  "turn": 3,
  "event": "message_sent | message_received | state_transition | illegal_transition | technical_win | watchdog_incident",
  "sender": "police | thief",
  "state_from": "MY_TURN",
  "state_to": "WAIT_OPPONENT",
  "envelope": {"type": "move", "turn": 3, "sender": "police", "payload": {"x": 1, "y": 2}},
  "timestamp": "2026-07-28T00:00:00Z"
}
```

### Anti-Patterns to Avoid

- **Calling `mcp.run()` from async code.** Verified: it wraps `anyio.run()` and cannot run inside an already-running loop. Always use `await mcp.run_async(...)` when the orchestrator itself is a coroutine — which it must be, since it also drives a `Client`.
- **Sync (`def`) tool handlers that touch shared asyncio state.** Verified: FastMCP runs plain `def` tool bodies in a worker threadpool (`call_sync_fn_in_threadpool`). Touching a main-loop `asyncio.Queue` from that thread without `call_soon_threadsafe`/`run_coroutine_threadsafe` is a race condition waiting to happen. Use `async def` for `receive_move`/`receive_barrier`/`handshake`/`game_over`.
- **Passing `host=`/`port=` to `FastMCP(...)`.** Verified in the exact pinned source (`v3.4.5`): this raises `TypeError` — `_REMOVED_KWARGS` explicitly lists both, pointing you at `run_http_async()` or the `FASTMCP_HOST`/`FASTMCP_PORT` env vars instead. Several web docs (including one page fetched during this research) still show the older `FastMCP("Name", host=..., port=...)` shape — that is stale training-data-era syntax, not what this project will install. Pass host/port to `run()`/`run_async()` instead, sourced from the new per-agent `network.json`.
- **A referee-like dev launcher.** CONTEXT.md is explicit: the dev launcher that starts both peers locally for convenience must never become a third coordinating process/referee — it only spawns two independent standalone processes and gets out of the way.
- **Polling for the opponent's move.** CONTEXT.md rules this out; push turn-passing via the incoming tool handler + `asyncio.Queue` is the locked design.
- **Hardcoding retry count / backoff / port numbers directly in `network/*.py` source.** All of these belong in the new per-agent `network.json` config file (QUAL-11); see Parameter Sourcing below for which numbers already exist in `PARAMETERS.md` and which do not.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP wire protocol / JSON-RPC framing | A hand-rolled HTTP+JSON message format | `fastmcp` (`FastMCP`, `Client`) | This is the mandated protocol per CLAUDE.md; FastMCP already implements streamable-HTTP MCP framing, content-block/structured-content marshalling, and the client-side async context manager |
| Per-call timeout + cancellation | Manual `threading.Timer` / socket timeout plumbing | `Client(..., timeout=...)` / `call_tool(..., timeout=...)`, wrapped further in `asyncio.wait_for()` for the queue-side wait | Verified: FastMCP's client already raises a well-defined `MCPError` on timeout; reinventing this at the socket layer risks silently swallowing partial reads |
| In-process test double for a live MCP server | Spinning up a real HTTP server + client in every unit test | `Client(mcp_server_instance)` in-memory transport | Verified official pattern, zero network dependency, matches the project's "no test depends on a live network" rule directly |
| FSM library (e.g. `transitions`) | Any third-party state-machine package | `State` enum + `ALLOWED_TRANSITIONS` dict (CONTEXT-locked) | Explicitly locked by CONTEXT.md; a 6-state machine does not justify a dependency, and the hand-rolled version is trivially unit-testable and fits the 150-line limit |
| Canonical JSON serialization | A second bespoke "stable JSON" function for NET-09 | Reuse the same `sort_keys=True, separators=(",", ":")` convention already locked for SEC-03 | One canonical-form implementation shared across NET-09 (config hash) and the future SEC-03 (move/commit hash) avoids drift between two "canonical JSON" definitions |

**Key insight:** FastMCP already solves the hard, protocol-level parts of "two symmetric peers talk MCP over HTTP" (framing, content blocks, async client lifecycle, timeouts). What Phase 2 must still hand-write is entirely **this project's own orchestration logic on top** — the state machine, the deadline/backoff policy, the watchdog, and the config hash — none of which FastMCP provides or should provide, since they encode this project's specific rules (rules 3–7, 11), not generic MCP semantics.

---

## Common Pitfalls

### Pitfall 1: `FastMCP(host=..., port=...)` — stale API shape
**What goes wrong:** Code copied from an older tutorial/blog constructs `FastMCP("name", host="127.0.0.1", port=8000)` and gets a `TypeError: FastMCP() no longer accepts 'host'. Pass 'host' to 'run_http_async()', or set FASTMCP_HOST.`
**Why it happens:** Training data and several currently-indexed web docs describe an older constructor shape. Verified directly against this project's actual installable version (`v3.4.5` tag): `_REMOVED_KWARGS` explicitly rejects `host`, `port`, `sse_path`, `message_path`, `streamable_http_path`, `json_response`, `stateless_http`, `debug`, `log_level`, and several `on_duplicate_*`/`tool_serializer`/`include_tags`/`exclude_tags` kwargs.
**How to avoid:** Always pass `host`/`port` to `mcp.run(transport="http", host=..., port=...)` / `run_async(...)` / `run_http_async(...)`, sourced from the new `network.json` config, never to the `FastMCP()` constructor.
**Warning signs:** `TypeError` at server-construction time, before any tool is even registered.

### Pitfall 2: A plain `def` tool handler silently races the event loop
**What goes wrong:** `receive_move` is written as `def receive_move(...)` (no `async`). FastMCP runs it in a worker threadpool. If its body does `incoming_queue.put_nowait(...)` on a plain `asyncio.Queue` created on the main event loop, this is a cross-thread call into asyncio internals that are not thread-safe — intermittent, hard-to-reproduce corruption or lost messages, not a clean crash.
**Why it happens:** FastMCP intentionally threadpools sync tool bodies "to avoid blocking the event loop" (verified: `call_sync_fn_in_threadpool` in `fastmcp_slim/fastmcp/tools/function_tool.py`) — a sensible default for CPU-bound or blocking-I/O tools, but a trap for tools that need to touch shared asyncio state.
**How to avoid:** Declare every tool that touches the incoming-queue / orchestrator state as `async def`, even though the body itself does no I/O beyond `await queue.put(...)`.
**Warning signs:** Flaky tests where a move is occasionally "lost"; works fine under the in-memory test client (still async-safe there) but misbehaves intermittently only under real HTTP load — worth adding an explicit unit test asserting the handler is a coroutine function (`asyncio.iscoroutinefunction`).

### Pitfall 3: Calling the blocking `mcp.run()` inside async code
**What goes wrong:** Somewhere inside the orchestrator's `async def` call chain, `mcp.run()` gets called instead of `await mcp.run_async()`. Verified: `run()` calls `anyio.run(partial(self.run_async, ...))` — invoking it while a loop is already running either raises immediately or (depending on backend) spins up a second, disconnected loop, so the server and the orchestrator's `Client` end up unable to talk to each other in-process.
**Why it happens:** Most FastMCP quickstart examples show `if __name__ == "__main__": mcp.run()` for the single-purpose "just a server" case, which this project's dual server+client agent is not.
**How to avoid:** Use `run_async()` exclusively inside the agent's async orchestrator; reserve `run()` only for a hypothetical process whose *entire* job is to be a server with no client role (not this project's shape).
**Warning signs:** `RuntimeError: This event loop is already running` or a client call that times out even though the server logs show it started.

### Pitfall 4: Confusing `MCPError` (timeout) with `ToolError` (opponent's tool raised)
**What goes wrong:** The deadline tracker (NET-06) catches the wrong exception type and either misses real timeouts or misclassifies a legitimate tool-side rejection (e.g., "illegal move") as a network timeout, triggering an unwarranted technical win.
**Why it happens:** Both are plausible-looking exception names; verified source shows they are distinct and mean different things: `MCPError` (from the `mcp` package, re-exported through `fastmcp`) covers `TimeoutError | JSONRPCError` at the protocol/transport level; `ToolError` (from `fastmcp.exceptions`) is raised client-side when `raise_on_error=True` (the default) and the tool's own result was an error.
**How to avoid:** Catch `MCPError` specifically for the NET-06 deadline-tracker retry/backoff/technical-win path; catch `ToolError` separately for "the opponent's tool rejected my call" (a different, non-timeout failure mode that the state machine should route to its own illegal/error handling, not the deadline tracker).
**Warning signs:** Tests that assert a technical win on a deliberately-slow opponent also incidentally pass when the opponent instead raises a `ToolError` — a sign the except-clauses are too broad (e.g. a bare `except Exception`).

### Pitfall 5: Hashing raw config bytes when formatting can silently drift
**What goes wrong:** NET-09's config hash is computed over raw file bytes. Later, one side's `game_params.json` gets re-saved by an editor with different line endings or trailing whitespace (still semantically identical, `diff --ignore-blank-lines` would show nothing meaningful) and the hash mismatches, aborting the game even though nothing about the *game* actually differs.
**Why it happens:** Raw-byte hashing conflates "identical formatting" with "identical meaning."
**How to avoid:** Hash the canonically-re-serialized JSON (Pattern 6 above), reusing the SEC-03 canonical-JSON convention already locked for Phase 6.
**Warning signs:** A hash mismatch that a manual visual diff of the two files shows as "no differences I can see" — almost always whitespace/line-ending drift, not a real tampering event.

### Pitfall 6: Watchdog thread writes nothing before `os._exit()`
**What goes wrong:** The watchdog detects a freeze, calls `os._exit(1)` immediately, and the "final incident record" never actually reaches disk — defeating NET-07's entire purpose ("rescues data").
**Why it happens:** `os._exit()` terminates the process instantly with no cleanup; any buffered-but-unflushed write is lost.
**How to avoid:** Explicitly `flush()` + `os.fsync()` the incident record (reuse Pattern 9's `append_event`) *synchronously, before* calling `os._exit()` — not via a `finally` block, atexit hook, or anything that depends on normal interpreter shutdown running.
**Warning signs:** Integration test that simulates a freeze and then re-reads the JSONL log after the (simulated, not actually process-killing) watchdog fires — must find the incident record already flushed to disk.

---

## Code Examples

See Architecture Patterns section above — every example there is either pulled verbatim from a verified official source (cited inline) or clearly marked as this project's own synthesis. No separate duplicate examples are repeated here.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `FastMCP(name, host=..., port=...)` constructor kwargs | `host`/`port` passed to `run()`/`run_async()`/`run_http_async()`, or `FASTMCP_HOST`/`FASTMCP_PORT` env vars | Somewhere between the 2.x line and the pinned `v3.4.5` (exact version boundary not confirmed — flagged as an open question below) | Any code (including some currently-live web documentation) written against the older constructor shape will crash with `TypeError` at server construction |
| `transport="streamable-http"` as the primary/only streamable name | `transport="http"` is now the documented default/primary name; `"streamable-http"` remains a valid alias (`Transport = Literal["stdio", "http", "sse", "streamable-http"]`, both accepted in `run_http_async`) | Confirmed current in `v3.4.5` | CONTEXT.md's locked language says "FastMCP streamable HTTP" — either literal string works; recommend `transport="http"` since it is the primary/default name in the installed version, with a code comment noting `"streamable-http"` is an accepted alias for readability if preferred |
| `fastmcp` as a single monolithic package | `fastmcp` is now a thin meta-package depending on `fastmcp-slim[client,server]` (workspace also contains `fastmcp_remote`, `fastmcp_tasks`) | Confirmed current in the `PrefectHQ/fastmcp` repo structure (no top-level `src/`; code lives under `fastmcp_slim/fastmcp/`) | Irrelevant to this project's usage — `uv add fastmcp` still installs everything needed (`Client`, `FastMCP`, `@mcp.tool`) via the dependency chain; only matters if you go looking for the source and expect a `src/` folder |

**Deprecated/outdated in this project's context:**
- Any tutorial/example showing `FastMCP(host=..., port=...)`: will not work against the version this project installs.
- `python -m pytest` / bare `python`: forbidden project-wide (CLAUDE.md) regardless of FastMCP version.

---

## Repo-Fit Findings (research question 8)

- **SDK layer (`src/pursuit/sdk/engine.py`)** already exposes the Phase-1 pure game engine as a thin façade: `make_state`, `legal_moves`, `apply_cop_action`, `apply_thief_move`, `check_capture`, `score`. Phase 2's network layer should **call into this SDK**, not reimplement or duplicate any board/capture/scoring logic — e.g. once a `receive_move` envelope is decoded, the orchestrator hands the parsed `(x, y)` to `apply_cop_action`/`apply_thief_move` exactly as Phase 1 already defines them. Phase 2's own SDK-layer additions (if any orchestrator-facing façade functions are needed) should live in `src/pursuit/sdk/` alongside `engine.py`, per QUAL-01.
- **Config loading (`src/pursuit/shared/config.py`)** is a fail-loud, typed loader (`load_game_params(path) -> GameParams`) for `game_params.json` only — it does not know about network/endpoint config. Phase 2 should add a **parallel, structurally similar** loader (e.g. `src/pursuit/shared/network_config.py`, `load_network_config(path) -> NetworkParams`) for the new `config/{police,thief}/network.json`, following the exact same fail-loud/typed-dataclass pattern (`_require_key`, `_require_int` helpers) already established — this is "extract at 2+ copies" territory (QUAL-02) if the two loaders end up sharing enough structure; watch for that as the second loader is written and factor a shared `_require_key`/`_require_int` helper into `shared/` if so.
- **Constants (`src/pursuit/constants.py`)** currently holds `Direction`, `CellState`, `Outcome`, `ConfigKey` — all structural, no numeric game values (D-07 from Phase 1). Phase 2 should add its own structural enums here or in a new `network/` module scope: `MessageType` (`move`, `barrier`, `handshake`, `game_over`, and later `hint`/`commit`), and possibly a `ConfigKey`-style `NetworkConfigKey` class for the new JSON's field names (`host`, `port`, `opponent_url`, `retry_count`, `backoff_seconds`) — consistent with the existing "avoid magic strings" convention.
- **`config/police/role.json` / `config/thief/role.json`** already establish the precedent for **legitimately different per-side config files** (only the `role` value differs). The new `network.json` files follow the identical precedent: same schema, different `port`/`opponent_url` values per side — this is not a NET-02 shared-state violation (these are static files loaded once at startup into separate `NetworkParams` objects per process, not a live shared object).
- **No SDK-layer or shared-module changes are needed to accommodate networking** beyond the additions above — the existing `sdk/engine.py` functions are pure and side-effect-free, so calling them from inside an async tool handler or the orchestrator coroutine is safe with no blocking concerns (they do no I/O).

---

## Parameter Sourcing (research question 9)

| Needed number | In `docs/PARAMETERS.md`? | Value / status | Notes |
|---|---|---|---|
| Response/deadline timeout (NET-06) | **Yes** — Table 19 row 6 | `30 sec`, **negotiable** | Directly usable as the default `response_timeout` in `network.json` |
| Watchdog threshold (NET-07) | **Yes** — Table 19 row 7 | `60 sec`, **negotiable** | Directly usable as the default `watchdog_threshold` in `network.json` |
| Retry count before declaring technical win (NET-06) | **Partially** — Table 19 row 4 (`[retries before failure]`) | `3`, **minimum** | Table 19 is titled "Gatekeeper: rate limiting and protection" and its worked example in `docs/PROJECT_GUIDE.md` §G scopes it to the outgoing-mail Gatekeeper (Phase 7). CONTEXT.md explicitly delegates "exact retry count / backoff defaults" to Claude's discretion "within the negotiable ranges" — **recommendation**: reuse this value (3) for the NET-06 deadline-tracker retry count too, since it is the only project-wide precedent for "how many times do we retry a network request" and reusing it avoids inventing an unrelated second number. This is a recommendation under delegated discretion, not a hard trace — flag it as such in the plan. |
| Backoff between retries (NET-06) | **Partially** — Table 19 row 3 (`[wait after error]`) | `5 sec`, **minimum** | Same caveat as above — recommend reusing `5 sec` as the NET-06 backoff default under CONTEXT.md's delegated discretion. |
| Listen port (per agent) | **No** | — | Not a game parameter; Appendix F/PARAMETERS.md does not cover network ports (this is deployment plumbing, not a rule-governed game value). CLAUDE.md rule 1 still applies to *any* number in source, so port numbers must live in the new `config/{police,thief}/network.json`, never hardcoded — but the *value itself* is not something PARAMETERS.md can supply. |
| Opponent URL (per agent) | **No** | — | Same as above — a string, not sourced from PARAMETERS.md, lives in `network.json`. |

### OPEN — must ask user
- **Exact port numbers for `config/police/network.json` and `config/thief/network.json`.** `docs/PARAMETERS.md` has no port entries (network ports are not an Appendix-F game parameter). Per CLAUDE.md rule 1 ("If a number you need is not in that file, stop and ask"), the plan must not silently invent specific port values (e.g. `8001`/`8002`) as project fact — the planner should either (a) ask the user for a preferred port pair, or (b) explicitly document the chosen ports as an **engineering default** (not a game parameter) in the phase's own `docs/phases/phase-2/PLAN.md`, clearly distinguished from PARAMETERS.md-sourced values, since Appendix F simply does not address this category of number.

---

## Open Questions

1. **Exact FastMCP version boundary where `host`/`port` constructor kwargs were removed**
   - What we know: Confirmed **present** (i.e., `host`/`port` rejected) at the pinned stable `v3.4.5` tag — this is the version that will actually be installed today via `uv add fastmcp`.
   - What's unclear: Whether this removal happened earlier in the 2.x line or specifically in the 3.x line — irrelevant for this project since 3.4.5 is what will install, but worth noting for anyone reading older tutorials.
   - Recommendation: No action needed — code against the verified `v3.4.5` API (host/port to `run()`/`run_async()`, never to the constructor) and this is correct regardless of the exact historical boundary.

2. **Graceful shutdown of the backgrounded `run_async()` task**
   - What we know: `asyncio.create_task(mcp.run_async(...))` starts a uvicorn-backed server as a background task; `task.cancel()` will raise `CancelledError` into it, which should stop `uvicorn.Server.serve()`.
   - What's unclear: Whether cancellation alone is a *clean* shutdown (properly closing the listening socket, letting in-flight requests complete) versus something that should instead set `uvicorn.Server.should_exit = True` for a graceful stop — not verified against source in this research pass.
   - Recommendation: The planner should treat "clean shutdown of the background server task at `GAME_OVER`" as its own small verification step during execution (e.g., confirm the port is actually released and a second `bind()` on the same port succeeds immediately after shutdown) rather than assuming `task.cancel()` alone is sufficient.

3. **`http_host_origin_protection` default and its interaction with future Phase 5 tunneling**
   - What we know: Verified default in `v3.4.5` settings (`fastmcp_slim/fastmcp/settings.py`): `http_host_origin_protection: bool | Literal["auto"] = False` — off by default, so no Host-header surprises for Phase 2's plain localhost-to-localhost traffic.
   - What's unclear: Whether Phase 5 (tunneling via ngrok/Localtonet, out of this phase's scope) will need `"auto"` or an explicit `allowed_hosts` list once traffic arrives via a public tunnel hostname rather than `127.0.0.1`.
   - Recommendation: Not a Phase 2 concern — flag for Phase 5's own research pass; Phase 2 can safely leave this setting at its default.

4. **Exact retry-count/backoff reuse for NET-06 (Table 19 rows 3–4) vs. a phase-2-specific config value**
   - What we know: CONTEXT.md delegates this to Claude's discretion "within the negotiable ranges"; Table 19 rows 3–4 are the only existing project numbers in that neighborhood, but they're titled/scoped to the mail Gatekeeper.
   - What's unclear: Whether the planner/user would prefer a distinct, phase-2-specific default instead of reusing the Gatekeeper's numbers.
   - Recommendation: Documented under "Parameter Sourcing" above as a recommendation, not a hard trace — the plan should state explicitly which choice it made and why, so it's auditable against CONTEXT.md's delegation.

---

## Sources

### Primary (HIGH confidence)
- `https://pypi.org/pypi/fastmcp/json` — ground-truth latest version (`3.4.5`), `requires_python` (`>=3.10`), full release list including `4.0.0a1`/`4.0.0a2` pre-releases (queried directly via `curl`, not summarized)
- `https://github.com/PrefectHQ/fastmcp` — repo root structure (confirms `jlowin/fastmcp` now redirects to `PrefectHQ/fastmcp`); confirmed `default_branch: main`, not archived
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/v3.4.5/fastmcp_slim/fastmcp/server/server.py` — `FastMCP.__init__` signature, `_REMOVED_KWARGS` dict (host/port rejection), `Transport` literal
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/v3.4.5/fastmcp_slim/fastmcp/server/mixins/transport.py` — `run()`, `run_async()`, `run_http_async()` exact implementations (confirmed `anyio.run()` wrapping, host/port defaults)
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/v3.4.5/fastmcp_slim/fastmcp/client/client.py` — `Client.__init__` signature (`timeout`, `init_timeout`, transport-type overloads including `FastMCP` in-memory)
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/v3.4.5/fastmcp_slim/fastmcp/client/mixins/tools.py` — `call_tool()` exact signature, `CallToolResult` fields (`content`, `structured_content`, `data`, `is_error`), `Raises: ToolError | MCPError` docstrings, `from fastmcp.exceptions import ToolError`
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/main/fastmcp_slim/fastmcp/tools/function_tool.py` — confirms sync tool bodies run via `call_sync_fn_in_threadpool`, async bodies run directly on the event loop
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/main/fastmcp_slim/fastmcp/settings.py` — `env_prefix="FASTMCP_"`, default `host="127.0.0.1"`, `port=8000`, `transport="stdio"`, `http_host_origin_protection=False` default
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/main/fastmcp_slim/fastmcp/__init__.py` — confirms `from fastmcp import FastMCP, Client` public import surface (lazy-loaded)
- `https://raw.githubusercontent.com/PrefectHQ/fastmcp/main/examples/testing_demo/server.py`, `.../tests/test_server.py`, `.../pyproject.toml` — real, current, official in-memory-testing worked example (`Client(mcp)`, `pytest-asyncio`, `asyncio_mode = "auto"`, `result.data`)
- This repo, read directly: `pyproject.toml`, `uv.lock` (confirmed **no fastmcp/mcp dependency installed yet**), `src/pursuit/{constants.py, sdk/engine.py, shared/config.py}`, `config/{police,thief}/{game_params.json, role.json}`, `docs/{PARAMETERS.md, RULES.md, SEGAL_GUIDELINES.md, PROJECT_GUIDE.md}`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/phases/01-base-logic/*` (house style for RESEARCH.md/PLAN.md), `scripts/check_line_limit.sh`

### Secondary (MEDIUM confidence)
- `https://gofastmcp.com/getting-started/quickstart`, `https://gofastmcp.com/deployment/running-server`, `https://gofastmcp.com/clients/client`, `https://gofastmcp.com/servers/tools`, `https://gofastmcp.com/clients/transports`, `https://gofastmcp.com/patterns/testing` — official docs site, fetched via WebFetch summarization (not raw HTML); broadly consistent with the verified source but the constructor-kwargs example on the quickstart page (`FastMCP("MyServer", host=..., port=...)`) is now confirmed **stale** against the actual installable version — treat the docs site as MEDIUM confidence and prefer the pinned-source findings above wherever they conflict
- WebSearch results on `MCPError`/timeout behavior (GitHub issues, third-party blog posts) — used only to corroborate, not as the primary source; the primary source for the exact exception semantics is the pinned `v3.4.5` source itself (HIGH)

### Tertiary (LOW confidence)
- Two WebFetch summaries of FastMCP "release notes" pages returned **internally inconsistent dates** (one labeled the same version numbers "2024," another "2026") — these specific date claims are not trusted; only the version-number ordering (3.4.5 stable, 4.0.0a1/a2 alpha ahead of it) was cross-checked and confirmed against PyPI's JSON API and git tags, which is why that ordering is reported above but the release *dates* are omitted from this document as unverified.

---

## Metadata

**Confidence breakdown:**
- Standard stack (fastmcp version, install command): HIGH — cross-checked PyPI JSON API ground truth against the exact pinned git tag's source code
- FastMCP API surface (server construction, tool decorator, run/run_async, Client, call_tool, timeouts, exceptions, in-memory testing): HIGH — every claim traced to a specific line/section of the `v3.4.5` tagged source or a current, real repo example
- Composed "server+client in one process" / push-turn-passing pattern: MEDIUM-HIGH — built from verified primitives, but is this project's own synthesis, not copied from an official matching example (no official FastMCP example implements a symmetric two-agent peer)
- State machine / watchdog / deadline / event-log patterns: HIGH for the general Python/OS mechanics (threading, os._exit, os.fsync — standard, well-established); MEDIUM-HIGH for how they compose with FastMCP's asyncio model (synthesis, verified individually but not as an assembled whole)
- Config-hash approach (canonical JSON vs raw bytes): MEDIUM-HIGH — a reasoned recommendation grounded in this project's own already-locked SEC-03 convention, not an external fact to verify
- Parameter sourcing: HIGH where PARAMETERS.md is cited directly; explicitly flagged OPEN (not invented) where no such value exists (ports)
- Repo-fit findings: HIGH — read directly from this repository's current source in this session

**Research date:** 2026-07-28
**Valid until:** Re-verify FastMCP version/API surface if execution is delayed more than ~14 days (fast-moving library: 8 releases from `2.14.7` through `4.0.0a2` observed within the surrounding months) — re-run `curl https://pypi.org/pypi/fastmcp/json` and diff against `3.4.5` before executing if a long gap occurs.
