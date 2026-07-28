# PRD — MCP Transport (FastMCP Peer Layer)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-07-28

> Per-mechanism PRD required by CLAUDE.md and [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §2.3, written before the code it describes (§2.5 step 5). Inherits the project [PRD.md](PRD.md); covers only the FastMCP peer layer delivered in Phase 2. Every number is either traced to [PARAMETERS.md](PARAMETERS.md) or labelled an engineering default in §10 — nothing here is invented.

## 1. Mechanism and scope

The FastMCP peer layer is the P2P transport for a refereeless cops-and-robbers match: two independent processes — cop and thief — exchange coordinate-only messages over MCP streamable HTTP, with no central server and no third process arbitrating the game.

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

**In scope (Phase 2):** transport composition, the four-tool surface with stub bodies, the message envelope, push turn-passing, handshake + config digest, the turn state machine, deadline/retry/technical-win resilience, the watchdog, and the JSONL event log.

**Out of scope, each phrased as a future-phase extension, not a Phase-2 deliverable:** strategy/RL move selection — the envelope and orchestrator reserve the decision point, Phase 3 fills it. Hints/scent/LLM text — the envelope reserves a `hint` type, Phase 4 fills it. ngrok/Localtonet tunneling — the transport is chosen so this later requires zero changes, Phase 5 adds it. Commit-reveal and Step-0 — the handshake reserves room for a Step-0 declaration, Phase 6 adds it. Gmail reporting and the live GUI — the JSONL event log is their future input, Phase 7 adds them.

## 2. Topology — symmetric peer, no referee (D-01, D-03, NET-01/02/03)

- Each agent process is **simultaneously** a FastMCP server (exposing `@mcp.tool`) and a `fastmcp.Client` calling the opponent's tools. Symmetric: no strong side, no weak side.
- **No third process.** NET-04's "single entry point" is satisfied *per agent* by that agent's own orchestrator (D-01). A dev launcher may spawn both peers locally for iteration but must never coordinate them — the standalone two-terminal path is the league path.
- **No shared runtime state** (NET-02): `config/police/` and `config/thief/` start two separate OS processes, each with its own `FastMCP` instance, own event loop, own queue. Sharing a live game-state object between the two sides is an information-leakage disqualification, not merely a design smell.

```
  config/police/                          config/thief/
  ┌─────────────────────┐                 ┌─────────────────────┐
  │ Peer A (police)      │                 │ Peer B (thief)       │
  │  server (@mcp.tool) ◄├─────────────────┤ client (fastmcp.Client)
  │  client (fastmcp.Client)├──────────────►│ server (@mcp.tool)   │
  └─────────────────────┘                 └─────────────────────┘
```

## 3. Transport and process composition (D-03)

- Transport is **FastMCP streamable HTTP** on configured localhost ports. Use `transport="http"` (the primary name in FastMCP 3.4.5; `"streamable-http"` is an accepted alias). This is the same transport Phase 5 tunnels through ngrok/Localtonet, so cloud exposure requires **zero transport changes**.
- **One asyncio event loop per process.** The server runs as a background task: `asyncio.create_task(mcp.run_async(transport="http", host=..., port=...))`. The orchestrator runs as a sibling coroutine on the same loop and owns `fastmcp.Client(opponent_url, timeout=response_timeout)` for outgoing calls — the concrete answer to "how do a server and a client coexist in one process without deadlock" (NET-03).

### 3.1 Two rules that must never be broken

1. **`host` and `port` are passed to `run_async()`, never to the `FastMCP(...)` constructor.** In FastMCP 3.4.5 both are listed in `_REMOVED_KWARGS` and passing them to the constructor raises `TypeError` at server-construction time, before a single tool is registered. Several still-indexed public docs and most training-era examples show the stale `FastMCP("Name", host=..., port=...)` shape — it does not work on the version this project installs. Values come from the per-agent `network.json` (§10).
2. **`mcp.run()` is never called from async code.** It is blocking and wraps `anyio.run()`; called from a running loop it either raises or spins up a second, disconnected loop, leaving the server and the in-process client unable to talk. Only `await mcp.run_async(...)` is used here.

At `GAME_OVER` the background server task is cancelled and the listening port must actually be released — verified explicitly by the implementation rather than assumed.

## 4. Tool surface (D-05, NET-03/NET-08)

**All four tools are defined now with real signatures and stub bodies; later phases fill in behavior but never reshape the protocol.**

| Tool | Signature | Phase-2 semantics | Later phases |
|------|-----------|-------------------|--------------|
| `handshake` | `async def handshake(turn: int, sender: str, payload: dict) -> dict` | Proves reachability and exchanges the config digest; payload `{"role", "config_digest"}`; returns this agent's role + digest | Phase 6 adds the Step-0 declaration to the same call |
| `receive_move` | `async def receive_move(turn: int, sender: str, payload: dict) -> dict` | Decodes the envelope, enqueues it, returns `{"status": "ack"}` immediately; payload `{"x", "y"}` | Phase 4 carries a hint alongside; Phase 6 carries commit/reveal fields |
| `receive_barrier` | `async def receive_barrier(turn: int, sender: str, payload: dict) -> dict` | Same enqueue-and-ack stub; payload `{"x", "y"}` — the cop's barrier declaration | Phase 3 consumes it in the strategy loop |
| `game_over` | `async def game_over(turn: int, sender: str, payload: dict) -> dict` | Same enqueue-and-ack stub; payload carries the outcome and reason | Phase 7 feeds the mutual game report |

- **Every handler is `async def`.** A plain `def` body is executed by FastMCP in a worker threadpool; touching a main-loop `asyncio.Queue` from that thread is not thread-safe and produces intermittently lost messages rather than a clean crash. The implementation carries a test asserting each handler is a coroutine function.
- **The tool name supplies the envelope's `type`.** The three wire arguments are `turn`, `sender`, `payload`; the handler pairs them with its own `MessageType` to reconstruct the full `Envelope` of §5.
- **No handler blocks on the opponent.** See §6.

This document leads the code (SEGAL §2.5) — if implementation finds a mismatch, the PRD is corrected first, then the code follows.

## 5. Message envelope (D-06, NET-08)

Every message on the wire is `{type, turn, sender, payload}` — one shape for every kind.

| Field | Type | Meaning |
|-------|------|---------|
| `type` | `MessageType` enum | Phase 2: `handshake`, `move`, `barrier`, `game_over` |
| `turn` | `int` | The turn this message belongs to |
| `sender` | `"police" \| "thief"` | Who sent it |
| `payload` | `dict` | Type-specific data |

**Phase 2 exercises `type=move` with payload `{"x": <int>, "y": <int>}` — coordinates only.** No board state, no belief map, no barrier list on the wire. This is a rule, not a convenience: the true board is never transmitted or displayed.

```json
{"type": "move", "turn": 3, "sender": "police", "payload": {"x": 1, "y": 2}}
```

**Extension path:** Phase 4 adds `hint`, Phase 6 adds `commit` / `reveal` — new `type` values inside the *same* envelope; no new message shape, no protocol reshaping. Decoding is fail-loud: a malformed or unknown envelope is rejected and reported, never silently coerced.

## 6. Turn-passing — push, not poll (D-07)

- After choosing its move an agent calls the opponent's `receive_move`; that **incoming call wakes the opponent's turn**. There is no polling loop anywhere in the design.
- Mechanism: the handler `await queue.put(envelope)` onto a per-process `asyncio.Queue` and returns an ack immediately. A separate orchestrator coroutine consumes the queue.
- Why the handler must not wait for the opponent: waiting inside a request handler deadlocks the ASGI request path — the process cannot answer the very call it is waiting on. The waiting belongs in the orchestrator, bounded by the deadline tracker (§9).
- Sequence: `MY_TURN` → send → `WAIT_OPPONENT` → incoming call enqueues → orchestrator wakes → `MY_TURN`.

## 7. Handshake and config integrity (D-08, D-15, NET-09)

- The game-start handshake does **two jobs in one call**: it proves the opponent is reachable, and it exchanges a SHA-256 digest of the shared game config — satisfying NET-09 in the same step.
- Digest input is the **canonically re-serialized** JSON of `game_params.json`, not the raw file bytes: `json.dumps(obj, sort_keys=True, separators=(",", ":"))` encoded UTF-8, then SHA-256. Two reasons: it reuses the project's already-locked canonical-JSON convention (the same one Phase 6 commit-reveal uses — one canonical form, not two), and it makes the check immune to formatting drift (trailing newline, indentation, line endings) that would otherwise produce a mismatch that looks like tampering but is only a whitespace accident.
- **Mismatch aborts before move 1.** The agent writes a clear report to the event log naming both digests and stops; it does not play a game on divergent rules. Reachability failure is reported through the same severity path (§8).
- Phase 6 later adds the Step-0 declaration to this same handshake; Phase 2 does not implement Step-0.

## 8. Turn state machine and failure severity (D-09, D-10, D-12, NET-04/NET-05)

```
INIT → HANDSHAKE → MY_TURN ⇄ WAIT_OPPONENT → GAME_OVER
                       │              │
                       └──────────────┴──────────► ERROR
```

| From | Allowed targets |
|------|------------------|
| `INIT` | `HANDSHAKE` |
| `HANDSHAKE` | `MY_TURN`, `WAIT_OPPONENT`, `ERROR` |
| `MY_TURN` | `WAIT_OPPONENT`, `GAME_OVER`, `ERROR` |
| `WAIT_OPPONENT` | `MY_TURN`, `GAME_OVER`, `ERROR` |
| `GAME_OVER` | — (terminal) |
| `ERROR` | — (terminal) |

- Implementation shape: a `State` enum plus an explicit allowed-transitions dict. **No FSM library** — a six-state machine does not justify a dependency, and the hand-rolled version is trivially unit-testable and fits the 150-line file limit (D-12).
- **Every illegal transition attempt is reported** (NET-05) — this is unconditional. What varies is the consequence, by severity:

  | Severity | Examples | Consequence |
  |----------|----------|-------------|
  | RECOVERABLE | duplicate message, out-of-order retry | logged, rejected, state unchanged, game continues |
  | PROTOCOL_VIOLATION | a transition the protocol cannot produce | logged, escalated to `ERROR`, game ends |

- Reporting goes to a structured JSONL event log per agent plus a human-readable console echo; the JSONL log is the seed of the Phase-7 replay artifact. The log records local truth only — the true board is never reconstructed or displayed live.
- Commit-reveal sub-states are inserted by Phase 6; Phase 2 leaves room for them and adds none.

## 9. Resilience — deadline, retry, technical win, watchdog (D-13, D-14, NET-06/NET-07)

- **Deadline (NET-06):** every wait on the opponent is bounded by the response timeout. On a missed deadline the agent retries with backoff, and only after the retries are exhausted does it declare a **technical win**, log the evidence, and end cleanly. All three numbers come from config, never from source — see §10.
- **`MCPError` vs `ToolError` — do not conflate them.** `MCPError` is the transport/protocol timeout signal and is the only exception that feeds the retry → technical-win path. `ToolError` means the opponent's tool body itself rejected the call — a different failure mode that routes to the state machine's severity handling. Catching both with one broad `except` would let a legitimate tool-side rejection trigger an unearned technical win, which is a false declaration.
- **Watchdog (NET-07):** a background daemon thread in each agent compares a `touch()`-ed last-activity timestamp against the watchdog threshold. Game state and the JSONL log are flushed to disk **every turn** (persist-every-turn), so a crash loses nothing. On a detected freeze the watchdog writes a final incident record, **flushes and fsyncs it before** hard-exiting — once the process is torn down no buffered write survives, which would defeat the whole point of "rescues data".
- The design uses no Unix signals, so it behaves identically on the Windows development box and on a Linux league host.

## 10. Parameters and their sources

Every number this mechanism uses appears below with its source; a number that is not in this section does not belong in the transport layer.

### 10.1 Traced to PARAMETERS.md

| Parameter | Value | Source | Status | Config key |
|-----------|-------|--------|--------|------------|
| Response / deadline timeout | **30 sec** | [PARAMETERS.md](PARAMETERS.md) Table 19 row 6 | negotiable | `response_timeout` |
| Watchdog threshold | **60 sec** | [PARAMETERS.md](PARAMETERS.md) Table 19 row 7 | negotiable | `watchdog_threshold` |
| Retries before declaring a technical win | **3** | [PARAMETERS.md](PARAMETERS.md) Table 19 row 4 (reused — see below) | minimum | `retry_count` |
| Backoff between retries | **5 sec** | [PARAMETERS.md](PARAMETERS.md) Table 19 row 3 (reused — see below) | minimum | `backoff_seconds` |

**Why rows 3-4 are reused (D-17).** Table 19 is titled "Gatekeeper: rate limiting and protection" and its worked example scopes it to the Phase-7 outgoing-mail Gatekeeper. CONTEXT.md delegates the exact retry count and backoff for NET-06 to implementation discretion within the negotiable ranges. Rather than invent a second, unrelated pair of numbers for the same question — "how many times do we retry a network request, and how long do we wait between attempts" — this mechanism **deliberately reuses** the only project-wide precedent. Both rows are **minimum** values, so meeting them exactly is compliant; they may be raised later, never lowered. This paragraph exists so the choice is auditable as a documented reuse rather than mistaken for an invented value.

### 10.2 Engineering defaults — NOT PARAMETERS.md game values

**The values in this subsection are a different kind of number from §10.1.** `docs/PARAMETERS.md` / Appendix F governs *game* parameters — board, quotas, scoring, timeouts, thresholds. It does not address network ports or thread sampling cadence at all; those are deployment plumbing. They are recorded here as engineering defaults so that no reader, and no future phase, mistakes them for a traced game parameter. The placement rule still applies in full: they live in config, never as a literal in source.

| Default | Value | Decision | Where it lives | Overridable |
|---------|-------|----------|----------------|-------------|
| Police listen port | **8001** | D-16 | `config/police/network.json` | yes — env var |
| Thief listen port | **8002** | D-16 | `config/thief/network.json` | yes — env var |
| Watchdog poll interval | **1 sec** | D-18 | `config/{police,thief}/network.json` → `watchdog_poll_seconds` | yes — config |

- **D-16:** the ports are a locked engineering default, env-var overridable so the league can relocate them without a code change. Never present them as PARAMETERS.md-traced.
- **D-18:** Table 19 row 7 supplies the watchdog *threshold* (60 sec) but not the *sampling cadence*. The poll interval is the separate question of how often the daemon thread wakes to compare; it sits well below the threshold. A smaller interval tightens detection latency and costs more idle CPU. Like the ports, it is an engineering default, not a game value.

### 10.3 Configuration placement (D-04)

Endpoints — own listen host/port and the opponent URL — live in **per-agent** config: `config/police/network.json` and `config/thief/network.json`. They are deliberately **not** in the shared `game_params.json`, whose byte-for-byte identity across both sides is exactly what §7's digest check verifies; putting per-side values there would guarantee a mismatch. This mirrors the existing `role.json` precedent: same schema, legitimately different values per side, loaded once at startup into separate objects per process — not shared runtime state.

## 11. Acceptance criteria for this mechanism

Restated from the Phase-2 §10.4 milestone gate as observable checks:

1. A geometric (`type=move`, payload `{x, y}`) envelope sent by peer A is received and decoded correctly by peer B, coordinates intact.
2. Cop and thief run as two separate processes from `config/police/` and `config/thief/` with no shared runtime state.
3. The per-agent orchestrator drives turn order through the state machine; illegal transitions are reported with a severity; the deadline tracker and watchdog prevent hangs.

**OPEN:** None — every number this mechanism needs is either traced in §10.1 or labelled an engineering default in §10.2.
