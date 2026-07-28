# PRD — MCP Transport (FastMCP Peer Layer)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-07-28

> Per-mechanism PRD required by CLAUDE.md and [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md)
> §2.3, written before the code it describes (§2.5 step 5). Inherits the project
> [PRD.md](PRD.md); covers only the FastMCP peer layer delivered in Phase 2. Every
> number is either traced to [PARAMETERS.md](PARAMETERS.md) or labelled an engineering
> default in §10 — nothing here is invented.

## 1. Mechanism and scope

The FastMCP peer layer is the P2P transport for a refereeless cops-and-robbers match:
two independent processes — cop and thief — exchange coordinate-only messages over MCP
streamable HTTP, with no central server and no third process arbitrating the game.

**Requirements covered:**

| REQ-ID | Description |
|--------|-------------|
| NET-01 | Cop and thief run as two separate processes under `config/police/` vs `config/thief/` |
| NET-02 | No shared runtime state, memory, or variables between the two agents |
| NET-03 | Each agent is simultaneously a FastMCP server (exposes tools) and client (calls the opponent's tools) |
| NET-04 | The orchestrator is the single entry point, driving turn order through a proper state machine |
| NET-05 | Every attempt to transition to an illegal state is reported |
| NET-06 | A deadline tracker prevents freezing while waiting on the opponent |
| NET-07 | A watchdog monitors process crashes and rescues data |
| NET-08 | A geometric message sent over localhost is received and decoded correctly by the other agent |
| NET-09 | The configuration file is verified byte-for-byte identical on both sides |
| DOC-02 | Every algorithm/central mechanism has its own `docs/PRD_<mechanism>.md` (this document) |

**In scope (Phase 2):** transport composition, the four-tool surface with stub bodies,
the message envelope, push turn-passing, handshake + config digest, the turn state
machine, deadline/retry/technical-win resilience, the watchdog, and the JSONL event log.

**Out of scope:** strategy/RL move selection (Phase 3) — the envelope and orchestrator
reserve the decision point, Phase 2 does not implement it. Hints/scent/LLM text
(Phase 4) — the envelope reserves a `hint` type, Phase 2 does not implement it.
ngrok/Localtonet tunneling (Phase 5) — the transport is chosen so this later requires
zero changes, Phase 2 does not implement it. Commit-reveal and Step-0 (Phase 6) — the
handshake reserves room for a Step-0 declaration, Phase 2 does not implement it.
Gmail reporting and the live GUI (Phase 7) — the JSONL event log is their future input,
Phase 2 does not implement them.

## 2. Topology — symmetric peer, no referee (D-01, D-03, NET-01/02/03)

- Each agent process is **simultaneously** a FastMCP server (exposing `@mcp.tool`) and a
  `fastmcp.Client` calling the opponent's tools. Symmetric: no strong side, no weak side.
- **No third process.** NET-04's "single entry point" is satisfied *per agent* by that
  agent's own orchestrator (D-01). A dev launcher may spawn both peers locally for
  iteration but must never coordinate them — the standalone two-terminal path is the
  league path.
- **No shared runtime state** (NET-02): `config/police/` and `config/thief/` start two
  separate OS processes, each with its own `FastMCP` instance, own event loop, own
  queue. Sharing a live game-state object between the two sides is an
  information-leakage disqualification, not merely a design smell.

```
  config/police/                          config/thief/
  ┌─────────────────────┐                 ┌─────────────────────┐
  │ Peer A (police)      │                 │ Peer B (thief)       │
  │  server (@mcp.tool) ◄├─────────────────┤ client (fastmcp.Client)
  │  client (fastmcp.Client)├──────────────►│ server (@mcp.tool)   │
  └─────────────────────┘                 └─────────────────────┘
```

## 3. Transport and process composition (D-03)

- Transport is **FastMCP streamable HTTP** on configured localhost ports. Use
  `transport="http"` (the primary name in FastMCP 3.4.5; `"streamable-http"` is an
  accepted alias). This is the same transport Phase 5 tunnels through ngrok/Localtonet,
  so cloud exposure requires **zero transport changes**.
- **One asyncio event loop per process.** The server runs as a background task:
  `asyncio.create_task(mcp.run_async(transport="http", host=..., port=...))`. The
  orchestrator runs as a sibling coroutine on the same loop and owns
  `fastmcp.Client(opponent_url, timeout=response_timeout)` for outgoing calls. This is
  the concrete answer to "how do a server and a client coexist in one process without
  deadlock" (NET-03).

### 3.1 Two rules that must never be broken

1. **`host` and `port` are passed to `run_async()`, never to the `FastMCP(...)`
   constructor.** In FastMCP 3.4.5 both are listed in `_REMOVED_KWARGS` and passing
   them to the constructor raises `TypeError` at server-construction time, before a
   single tool is registered. Several still-indexed public docs and most
   training-era examples show the stale `FastMCP("Name", host=..., port=...)` shape —
   it does not work on the version this project installs. Values come from the
   per-agent `network.json` (§9).
2. **`mcp.run()` is never called from async code.** It is blocking and wraps
   `anyio.run()`; called from a running loop it either raises or spins up a second,
   disconnected loop, leaving the server and the in-process client unable to talk.
   Only `await mcp.run_async(...)` is used here.

At `GAME_OVER` the background server task is cancelled and the listening port must
actually be released — verified explicitly by the implementation rather than assumed.

## 4. Tool surface (D-05, NET-03/NET-08)

**All four tools are defined now with real signatures and stub bodies; later phases
fill in behavior but never reshape the protocol.**

| Tool | Signature | Phase-2 semantics | Later phases |
|------|-----------|-------------------|--------------|
| `handshake` | `async def handshake(turn: int, sender: str, payload: dict) -> dict` | Proves reachability and exchanges the config digest; payload `{"role", "config_digest"}`; returns this agent's role + digest | Phase 6 adds the Step-0 declaration to the same call |
| `receive_move` | `async def receive_move(turn: int, sender: str, payload: dict) -> dict` | Decodes the envelope, enqueues it, returns `{"status": "ack"}` immediately; payload `{"x", "y"}` | Phase 4 carries a hint alongside; Phase 6 carries commit/reveal fields |
| `receive_barrier` | `async def receive_barrier(turn: int, sender: str, payload: dict) -> dict` | Same enqueue-and-ack stub; payload `{"x", "y"}` — the cop's barrier declaration | Phase 3 consumes it in the strategy loop |
| `game_over` | `async def game_over(turn: int, sender: str, payload: dict) -> dict` | Same enqueue-and-ack stub; payload carries the outcome and reason | Phase 7 feeds the mutual game report |

- **Every handler is `async def`.** A plain `def` body is executed by FastMCP in a
  worker threadpool; touching a main-loop `asyncio.Queue` from that thread is not
  thread-safe and produces intermittently lost messages rather than a clean crash. The
  implementation carries a test asserting each handler is a coroutine function.
- **The tool name supplies the envelope's `type`.** The three wire arguments are
  `turn`, `sender`, `payload`; the handler pairs them with its own `MessageType` to
  reconstruct the full `Envelope` of §5.
- **No handler blocks on the opponent.** See §6.

This document leads the code (SEGAL §2.5) — if implementation finds a mismatch, the PRD
is corrected first, then the code follows.

## 5. Message envelope (D-06, NET-08)

Every message on the wire is `{type, turn, sender, payload}` — one shape for every kind.

| Field | Type | Meaning |
|-------|------|---------|
| `type` | `MessageType` enum | Phase 2: `handshake`, `move`, `barrier`, `game_over` |
| `turn` | `int` | The turn this message belongs to |
| `sender` | `"police" \| "thief"` | Who sent it |
| `payload` | `dict` | Type-specific data |

**Phase 2 exercises `type=move` with payload `{"x": <int>, "y": <int>}` —
coordinates only.** No board state, no belief map, no barrier list on the wire. This is
a rule, not a convenience: the true board is never transmitted or displayed.

```json
{"type": "move", "turn": 3, "sender": "police", "payload": {"x": 1, "y": 2}}
```

**Extension path:** Phase 4 adds `hint`, Phase 6 adds `commit` / `reveal` — new `type`
values inside the *same* envelope; no new message shape, no protocol reshaping.

Decoding is fail-loud: a malformed or unknown envelope is rejected and reported, never
silently coerced.

## 6. Turn-passing — push, not poll (D-07)

- After choosing its move an agent calls the opponent's `receive_move`; that
  **incoming call wakes the opponent's turn**. There is no polling loop anywhere in
  the design.
- Mechanism: the handler `await queue.put(envelope)` onto a per-process
  `asyncio.Queue` and returns an ack immediately. A separate orchestrator coroutine
  consumes the queue.
- Why the handler must not wait for the opponent: waiting inside a request handler
  deadlocks the ASGI request path — the process cannot answer the very call it is
  waiting on. The waiting belongs in the orchestrator, bounded by the deadline tracker
  (§9).
- Sequence: `MY_TURN` → send → `WAIT_OPPONENT` → incoming call enqueues → orchestrator
  wakes → `MY_TURN`.
