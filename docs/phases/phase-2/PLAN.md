# Phase 2 PLAN — FastMCP Infrastructure

**Version:** 1.00 · **Updated:** 2026-07-28

> Phase-scoped architecture. Inherits the project [PLAN.md](../../PLAN.md); captures only
> the design specific to Phase 2. Mechanism detail lives in
> [PRD_mcp_transport.md](../../PRD_mcp_transport.md).

## Components & files

| Module / file (≤150 lines each) | Responsibility |
|---|---|
| `config/{police,thief}/network.json` | Per-agent endpoints + timeouts; the file that legitimately differs per side (D-04, D-16, D-18) |
| `src/pursuit/shared/loader_helpers.py` | `_require_key` / `_require_int` extracted from `shared/config.py`; consumed by **both** loaders (QUAL-02) |
| `src/pursuit/shared/network_config.py` | `NetworkParams` + `load_network_config()`; fail-loud, env-var override (D-16) |
| `src/pursuit/network/envelope.py` | `MessageType` enum + frozen `Envelope {type, turn, sender, payload}`; lossless round-trip, fail-loud decode (D-06) |
| `src/pursuit/network/config_hash.py` | `canonical_json()` + `config_digest()` (SHA-256 over canonical JSON) + `digests_match()` via `secrets.compare_digest` (D-08, D-15) |
| `src/pursuit/network/state_machine.py` | `State` enum, `ALLOWED_TRANSITIONS` table, `TransitionSeverity`, `transition(..., reporter)` (D-09, D-10, D-12) |
| `src/pursuit/network/event_log.py` | JSONL sink, one object per line, `flush()` + `os.fsync()` per write (D-11, D-14) |
| `src/pursuit/network/watchdog.py` | Daemon thread over a last-activity timestamp; incident record written **before** the injected exit (D-14, D-18) |
| `src/pursuit/network/tools.py` | Four `async def` `@mcp.tool` stubs: `handshake`, `receive_move`, `receive_barrier`, `game_over` (D-05); plus the injected `handshake_handler` seam that lets the real responder sit behind the real `handshake` tool (NET-09) |
| `src/pursuit/network/peer_runtime.py` | Factory-built server backgrounded via `run_async(transport="http", host, port)` + `Client` + per-process `asyncio.Queue` (D-03, D-07) |
| `src/pursuit/network/deadline.py` | `wait_for_opponent()` + `call_with_retry()`; technical-win verdict with measured evidence (D-13, D-17) |
| `src/pursuit/network/handshake.py` | Connectivity proof + config-digest exchange; mismatch aborts before move 1 (D-08, D-15) |
| `src/pursuit/network/orchestrator.py` | Turn loop only; `AgentContext` (D-01) |
| `src/pursuit/network/agent_lifecycle.py` | Config load, wiring, handshake (outbound `perform_handshake` + the inbound responder bound to the runtime at construction), shutdown |
| `src/pursuit/network/turn_events.py` | Pure JSONL record builders |
| `src/pursuit/main.py` | Thin standalone entry point — parses config dir, hands off (D-02) |
| `scripts/dev_launch.py` | Dev convenience only; holds no state, makes no decisions, **is not a referee** (D-01, D-02) |

## Interfaces & contracts

```python
# shared/network_config.py
load_network_config(path) -> NetworkParams   # host, port, opponent_url, response_timeout,
                                             # watchdog_threshold, watchdog_poll_seconds,
                                             # retry_count, backoff_seconds

# network/envelope.py
class Envelope:  type: MessageType; turn: int; sender: str; payload: dict
Envelope.from_dict(d) -> Envelope            # raises on malformed / unexpected key
Envelope.to_dict() -> dict

# network/config_hash.py
canonical_json(obj) -> str                   # sort_keys=True, separators=(",", ":")
config_digest(path) -> str                   # SHA-256 over canonical JSON
digests_match(a, b) -> bool                  # secrets.compare_digest

# network/state_machine.py
class TurnStateMachine:  attempt(target) -> TransitionResult   # reports every illegal attempt

# network/tools.py
register_tools(mcp, queue, *, handshake_handler=None) -> None
                                             # handshake_handler: async (turn, sender, payload)
                                             # -> dict. None keeps the generic stub ack; a handler
                                             # replaces it and its reply is returned verbatim

# network/peer_runtime.py
build_server(queue, server_name, *, handshake_handler=None) -> FastMCP
class PeerRuntime:                           # (params, server_name, *, serve=None,
    start(); stop()                          #  handshake_handler=None)
                                             # host/port go to run_async, NEVER the constructor
                                             # the responder is bound HERE, at construction:
                                             # register_tools fixes the tool body when the
                                             # server is built (NET-09)

# network/deadline.py
wait_for_opponent(queue, *, timeout) -> Envelope
call_with_retry(send, *, timeout, retries, backoff, sleep, clock) -> Result | TechnicalWin

# network/handshake.py
perform_handshake(...) -> HandshakeResult    # outbound; outcome is AGREED | CONFIG_MISMATCH
                                             #           | UNREACHABLE | MALFORMED_REPLY
respond_to_handshake(...) -> tuple[dict, HandshakeResult]
                                             # inbound, pure + synchronous, never raises;
                                             # agent_lifecycle wraps it in an async closure and
                                             # passes it as peer_runtime's handshake_handler
```

## Phase ADRs

| # | Decision | Rationale | Alternative / trade-off |
|---|----------|-----------|-------------------------|
| P2-1 | Per-agent orchestrator, no third process (D-01) | NET-04's "single entry point" is satisfied *per agent*; a referee process would break the P2P no-central-server rule | Central referee: rejected — contradicts the book's P2P premise |
| P2-2 | FastMCP **streamable HTTP** transport (D-03) | Phase 5 ngrok tunnels this transport unchanged, so cloud exposure needs zero transport rework | stdio: rejected — cannot be tunnelled |
| P2-3 | `host`/`port` passed to `run_async()`, never to `FastMCP(...)` | Verified against the pinned v3.4.5 source: the constructor rejects them (`_REMOVED_KWARGS`). Several public tutorials still show the stale shape | Constructor kwargs: raises `TypeError` |
| P2-4 | Tool handlers are `async def`, never plain `def` | Plain `def` bodies are dispatched to a worker threadpool, making a main-loop `asyncio.Queue` unsafe to touch | Sync handlers: thread-safety hazard |
| P2-5 | Push turn-passing via `asyncio.Queue` (D-07) | The handler enqueues and returns immediately; blocking inside a handler while this agent's client calls the opponent deadlocks both peers | Polling loop: wasteful and still racy |
| P2-6 | Canonical-JSON digest, not raw file bytes (D-08) | Two files identical in content but differing in key order, indentation, or trailing newline must agree — otherwise a formatting nit aborts a legal game | Raw bytes: brittle, false mismatches |
| P2-7 | Severity-based illegal transitions (D-10) | Duplicate/out-of-order messages are recoverable and keep the game running; protocol violations escalate to `ERROR`. Every attempt is reported either way (rule 5) | Uniform hard-fail: ends games over benign retries |
| P2-8 | Ports and poll interval labelled **engineering defaults** (D-16, D-18) | Appendix F does not cover these categories; labelling them keeps the PARAMETERS.md trace honest rather than implying a source that does not exist | Silent invention: violates rule 1 |

## Test plan (TDD)

- **Unit:** `tests/unit/` — one file per module; happy path + error case per public function.
  All peer-to-peer tests use the verified in-memory `Client(mcp_server_instance)` pattern —
  no socket, no subprocess, no dependency on the opponent.
- **Integration:** `tests/integration/` — `test_peer_roundtrip.py` (GATE-1),
  `test_turn_lifecycle.py` (GATE-2/3), `test_turn_resilience.py` (technical win, watchdog
  incident), plus a shared `conftest.py` so helpers exist once (QUAL-02).
- **No test sleeps on a real 30 s or 60 s threshold** — clock, sleeper, and params are all
  injected, so the timeout, retry-ladder, and freeze paths run deterministically and fast.
- **Coverage target:** ≥85% (`fail_under=85`).

## Per-mechanism PRDs written this phase

- [`docs/PRD_mcp_transport.md`](../../PRD_mcp_transport.md) — the FastMCP peer layer
  (DOC-02). Written in Wave 1, **before** the transport code it describes, per SEGAL §2.5
  step 5.

## Known limitation

The in-process gate tests prove NET-02 non-leakage and config-root parameterisation, but
cannot by themselves prove OS-level process separation. That remainder is closed by the
real two-terminal standalone launch (task 2-10), which is also the league path (D-02).
Each gate module carries a `LIMITATION` docstring stating what it does not prove.
