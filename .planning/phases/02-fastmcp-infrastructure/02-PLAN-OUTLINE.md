# Phase 2 — FastMCP Infrastructure: Plan Manifest

**Source artifacts:** `02-CONTEXT.md` (D-01…D-15), `02-RESEARCH.md` (verified FastMCP 3.4.5 API,
patterns, pitfalls, parameter sourcing), `ROADMAP.md` §Phase 2, `.planning/REQUIREMENTS.md`
(NET-01…NET-09), `docs/PARAMETERS.md` Table 19, plus two decisions locked with the user during
this planning session (D-16, D-17).

**All requirement IDs that must be covered:** NET-01, NET-02, NET-03, NET-04, NET-05, NET-06,
NET-07, NET-08, NET-09. Cross-cutting gates carried by individual plans: QUAL-02, QUAL-07,
QUAL-08, QUAL-09, QUAL-10, QUAL-11, QUAL-12, QUAL-13, DOC-02.

**§10.4 milestone gate (acceptance criteria for the phase):**

1. A geometric message sent by agent A over localhost is received and decoded correctly by agent B
2. Cop and thief run as two separate processes under `config/police/` and `config/thief/` with no
   shared runtime state
3. The orchestrator (single entry point) drives turn order via a state machine; illegal
   transitions are reported; watchdog + deadline tracker prevent hangs

**Deliberately excluded from this manifest:** `docs/phases/phase-2/{PRD,PLAN,TODO}.md`
(ROADMAP task 02-97) — the plan-phase orchestrator writes that triplet, not a plan. ROADMAP task
02-99 is a verify-work action, not a plan. `docs/PRD_mcp_transport.md` (ROADMAP 02-04) **is**
plan-owned, because CLAUDE.md §2.3 / DOC-02 require a per-mechanism PRD for the transport layer.

---

## Decision IDs

CONTEXT.md writes the Phase 2 decisions as unnumbered bullets. They are assigned IDs here in
reading order (Topology & startup → Tool surface & protocol → State machine → Resilience). D-16
and D-17 are the two answers locked with the user during this planning session and carry the same
weight as CONTEXT.md.

| ID | Decision |
|----|----------|
| **D-01** | **Per-agent orchestrator** — each agent process embeds its own orchestrator/main loop running the turn state machine. No third referee process; NET-04's "single entry point" is satisfied per agent, consistent with the P2P no-central-server rule. |
| **D-02** | **Dev launcher + standalone** — a small dev script starts both peers locally for fast iteration, but each agent also starts standalone with one command in its own terminal. The standalone path is the league path; the launcher must never become a referee. |
| **D-03** | **Transport: FastMCP streamable HTTP** on configured localhost ports — the same transport ngrok tunnels in Phase 5, so cloud exposure requires zero transport changes. |
| **D-04** | **Endpoints live in per-agent config** (`config/police/`, `config/thief/`): own listen port + opponent URL. NOT in the shared `game_params.json`, whose byte-for-byte identity must hold across sides. |
| **D-05** | **Full tool surface now, stub bodies** — define `handshake`, `receive_move`, `receive_barrier`, `game_over` with real signatures in Phase 2; later phases fill in behavior but never reshape the protocol. |
| **D-06** | **Typed message envelope** `{type, turn, sender, payload}` for every message kind. Phase 2 uses `type=move` with payload `{x, y}`; hints (Phase 4) and commits (Phase 6) become new types in the same envelope. |
| **D-07** | **Push turn-passing** — after choosing its move an agent calls the opponent's `receive_move`; that incoming call wakes the opponent's turn. No polling loops; the deadline tracker wraps the wait. |
| **D-08** | **Handshake = connectivity + config hash** — the game-start handshake proves reachability AND exchanges a SHA-256 of the shared game config, satisfying NET-09 in the same step. Phase 6 later adds the Step-0 declaration here. |
| **D-09** | **States**: INIT → HANDSHAKE → MY_TURN ↔ WAIT_OPPONENT → GAME_OVER, plus ERROR. Commit-reveal sub-states are inserted by Phase 6 when they become real. |
| **D-10** | **Illegal transitions (NET-05): severity-based** — every attempt is logged + rejected; recoverable ones (duplicate message, out-of-order retry) keep the game running; protocol violations escalate to ERROR and end the game. |
| **D-11** | **Reporting**: structured JSONL event log per agent + human-readable console echo. The JSONL log is the seed of the Phase-7 `log_<game_id>` artifact and replay viewer. |
| **D-12** | **Implementation: State enum + explicit allowed-transitions dict** in a small module. No FSM library dependency; trivially unit-testable; fits the 150-line limit. |
| **D-13** | **Deadline (NET-06)** — on a missed 30 s response deadline, retry N times with backoff (N and backoff from config, never source), then declare a **technical win**, log the evidence, and end cleanly. |
| **D-14** | **Watchdog (NET-07): persist-every-turn** — game state and JSONL log are flushed to disk every turn, so a crash loses nothing; the watchdog is a **background thread in each agent** watching a last-activity timestamp against the 60 s threshold; on freeze it writes a final incident record and exits cleanly. |
| **D-15** | **Config check (NET-09)** — SHA-256 of `game_params.json` exchanged during handshake; any mismatch **aborts before move 1** with a clear logged report. |
| **D-16** | **Ports (locked this session)** — police listens on **8001**, thief on **8002**. These live in per-agent network config (`config/police/network.json`, `config/thief/network.json`) and are **env-var overridable** for the league. They are an **engineering default, explicitly NOT a `docs/PARAMETERS.md` game value** — Appendix F does not cover network ports at all. Never present them as PARAMETERS.md-traced. |
| **D-17** | **NET-06 retry/backoff (locked this session)** — reuse `docs/PARAMETERS.md` Table 19 rows 3–4: **3 retries, 5 s backoff**. Both are *minimum* values, so meeting them is compliant. Every plan touching these must state explicitly that it reuses the Gatekeeper row and why, so the choice is auditable against CONTEXT.md's delegation of "exact retry count / backoff defaults" to Claude's discretion. Values live in config, never in source. |

**Claude's Discretion (CONTEXT.md, not numbered):** module layout / naming / file split within the
150-line limit; test structure and mocking approach for the peer-to-peer calls. RESEARCH.md's
recommended `src/pursuit/network/` split is adopted below under that delegation.

**Numeric values in play and their sources** — no number in this phase may come from anywhere else:

| Number | Source | Status |
|--------|--------|--------|
| response/deadline timeout **30 s** | PARAMETERS.md Table 19 row 6 | negotiable |
| watchdog threshold **60 s** | PARAMETERS.md Table 19 row 7 | negotiable |
| retries **3** | PARAMETERS.md Table 19 row 4, reused per D-17 | minimum |
| backoff **5 s** | PARAMETERS.md Table 19 row 3, reused per D-17 | minimum |
| ports **8001 / 8002** | D-16 (user-locked engineering default) | not a PARAMETERS.md value |
| board / quota / scoring numbers | Phase 1 `game_params.json` (unchanged) | already traced |

---

## Plan Manifest

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|------------|--------------|
| 02-00 | Phase-2 scaffold — dependency install + network config + test stubs: `uv add fastmcp` (resolves 3.4.5) and `uv add --dev pytest-asyncio`, add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` (RESEARCH Pattern 5), create `config/police/network.json` + `config/thief/network.json` carrying `host`, `port` (8001/8002 — D-16 engineering default, env-overridable), `opponent_url`, `response_timeout`=30, `watchdog_threshold`=60, `retry_count`=3, `backoff_seconds`=5 (D-04/D-16/D-17; all values traced in the table above), add `NetworkConfigKey` to `src/pursuit/constants.py` (structural key names only, no numbers — D-04), add port/opponent-URL override entries to `.env-example` with dummy values (QUAL-12), create `src/pursuit/network/__init__.py`, add a `network_params` fixture to `tests/conftest.py` using a **lazy import inside the fixture body** so collection never breaks before 02-01 lands, and create every Phase-2 test stub file (`pytest.skip` bodies) listed in the Wave Structure below. `uv.lock` regenerated. | 0 | — | QUAL-11, QUAL-12, QUAL-13 |
| 02-01 | Network config loader + shared loader-helper extraction (QUAL-02): extract `_require_key`/`_require_int` out of `src/pursuit/shared/config.py` into `src/pursuit/shared/loader_helpers.py` and re-point `config.py` at it (second copy = extract, QUAL-02 — existing `tests/unit/test_config.py` must stay green), then add `src/pursuit/shared/network_config.py` with a frozen `NetworkParams` dataclass + `load_network_config(path) -> NetworkParams`, fail-loud on every missing/mistyped key, following the exact Phase-1 loader pattern. Env-var override for `host`/`port`/`opponent_url` via `os.environ.get()` per D-16 (never a literal in source — D-04, D-16, D-17). | 1 | 02-00 | NET-01, NET-02, QUAL-02, QUAL-11 |
| 02-02 | Typed message envelope + canonical-JSON config digest: `src/pursuit/network/envelope.py` with a `MessageType` enum (`handshake`, `move`, `barrier`, `game_over` — extensible for Phase-4 `hint` / Phase-6 `commit`) and an `Envelope` frozen dataclass `{type, turn, sender, payload}` plus `to_dict`/`from_dict` round-trip decode with fail-loud validation (D-06; Phase 2 only exercises `type=move` with payload `{x, y}`); `src/pursuit/network/config_hash.py` with `config_digest(path) -> str` hashing the **canonically re-serialized** JSON (`sort_keys=True, separators=(",", ":")`) not raw bytes — reuses the SEC-03 canonical-JSON convention and avoids RESEARCH Pitfall 5 formatting-drift false mismatches (D-08, D-15). Both are pure functions; zero FastMCP dependency. | 1 | 02-00 | NET-08, NET-09 |
| 02-03 | Turn state machine + severity-based illegal-transition reporting: `src/pursuit/network/state_machine.py` with a `State` enum (INIT, HANDSHAKE, MY_TURN, WAIT_OPPONENT, GAME_OVER, ERROR — D-09), an explicit `ALLOWED_TRANSITIONS: dict[State, set[State]]` (D-12, no FSM library), a `TransitionSeverity` enum (RECOVERABLE vs PROTOCOL_VIOLATION), and `transition(current, target, *, reporter)` that applies legal transitions, **always reports every illegal attempt** (NET-05), keeps the game running on RECOVERABLE and escalates PROTOCOL_VIOLATION to `State.ERROR` (D-10). `reporter` is an injected callable/Protocol declared in this module, so the state machine imports nothing from `event_log` and stays parallel-safe. | 1 | 02-00 | NET-04, NET-05 |
| 02-04 | JSONL event log (persist-every-turn) + watchdog thread: `src/pursuit/network/event_log.py` with `append_event(path, record)` writing one canonical-JSON line then `flush()` + `os.fsync()` every call (D-11/D-14 durability; RESEARCH Pattern 9) and the minimal event schema (`game_uid`, `turn`, `event`, `sender`, `state_from`, `state_to`, `envelope`, `timestamp`) plus a human-readable console echo; `src/pursuit/network/watchdog.py` with a `Watchdog(threshold_seconds, on_freeze, ...)` daemon thread polling a `touch()`-updated monotonic timestamp, writing + fsyncing the incident record **before** exiting (RESEARCH Pitfall 6), with the exit call **injected** (defaults to `os._exit`) so tests assert the hard-exit path without killing pytest. No Unix signals — Windows-safe by construction. | 1 | 02-00 | NET-05, NET-07 |
| 02-05 | `docs/PRD_mcp_transport.md` — the per-mechanism PRD for the FastMCP peer layer (DOC-02, CLAUDE.md §2.3, ROADMAP 02-04). Written in Wave 1 so the mechanism is documented **before** the code it describes (SEGAL §2.5 step 5). Must contain: the symmetric server+client topology (D-01, D-03), the four-tool surface with exact signatures and Phase-2 stub semantics (D-05), the envelope schema and its Phase-4/6 extension path (D-06), push turn-passing and the no-polling rule (D-07), the handshake = connectivity + config-hash contract and the pre-move-1 abort (D-08, D-15), the state diagram + severity policy (D-09, D-10, D-12), the deadline/retry/technical-win policy **explicitly citing PARAMETERS.md Table 19 rows 3, 4, 6 and stating the D-17 Gatekeeper-row reuse and why**, the watchdog policy citing Table 19 row 7 (D-13, D-14), and a clearly labelled section marking ports 8001/8002 as a **D-16 engineering default, not a PARAMETERS.md game value**. | 1 | — | DOC-02 |
| 02-06 | FastMCP tool surface + `PeerRuntime` (server and client in one process — NET-03): `src/pursuit/network/tools.py` exposing `handshake`, `receive_move`, `receive_barrier`, `game_over` via `@mcp.tool` with **real signatures and stub bodies** (D-05), every handler `async def` so it stays on the orchestrator's event loop and may safely `await queue.put(...)` (RESEARCH Pitfall 2), each decoding its args into an `Envelope` (D-06) and returning an immediate ack — never blocking on the opponent (D-07); `src/pursuit/network/peer_runtime.py` building the server via a factory (no module-level singleton, so no cross-agent shared object — NET-02), owning the per-process `asyncio.Queue`, backgrounding `mcp.run_async(transport="http", host=..., port=...)` as an `asyncio.Task` and exposing an `fastmcp.Client(opponent_url, timeout=response_timeout)` for outgoing calls. **`host`/`port` go to `run_async()`, never to `FastMCP()`** (RESEARCH Pitfall 1); **never call the blocking `mcp.run()`** (Pitfall 3). Tests use the in-memory `Client(mcp)` transport only — no live socket (RESEARCH Pattern 5). Includes a test asserting every tool handler is a coroutine function. Clean shutdown of the background server task is verified explicitly (RESEARCH Open Question 2). | 2 | 02-01, 02-02 | NET-02, NET-03, NET-08 |
| 02-07 | Deadline tracker + retry/backoff + technical-win declaration: `src/pursuit/network/deadline.py` with `wait_for_opponent(queue, timeout)` wrapping `asyncio.wait_for` to bound the WAIT_OPPONENT state, and a `call_with_retry(send, *, retries, backoff)` loop that catches **`MCPError` only** for the timeout path and lets **`ToolError` propagate separately** (RESEARCH Pitfall 4 — a tool-side rejection must never be mistaken for a network timeout and trigger an unwarranted technical win), retrying `retries` times with `backoff` seconds between attempts before returning a `TechnicalWin` result carrying the evidence for the event log (D-13). Timeout/retries/backoff are **arguments supplied from `NetworkParams`** — 30 s / 3 / 5 s per PARAMETERS.md Table 19 rows 6, 4, 3 reused under D-17; no numeric literal in the module. | 2 | 02-01 | NET-06 |
| 02-08 | Handshake: connectivity proof + config-hash exchange + pre-move-1 abort: `src/pursuit/network/handshake.py` performing the INIT → HANDSHAKE transition (D-09), calling the opponent's `handshake` tool with this agent's `config_digest(game_params.json)` and role, comparing against the returned digest, and on mismatch **aborting before move 1** with a clear logged report rather than playing a game on divergent rules (D-08, D-15 — NET-09). Reachability failure is reported through the same severity path (D-10). Reuses 02-02's digest function and 02-06's client; state changes go through 02-03's `transition()`. Tests drive both the matching and mismatching digest paths through the in-memory client — never a live socket. | 3 | 02-02, 02-03, 02-06 | NET-03, NET-05, NET-09 |
| 02-09 | Orchestrator (single entry point) + agent main + dev launcher: `src/pursuit/network/orchestrator.py` — the per-agent turn loop (D-01) wiring handshake → MY_TURN ↔ WAIT_OPPONENT → GAME_OVER through 02-03's `transition()`, pushing each move to the opponent's `receive_move` (D-07), bounding every wait with 02-07's deadline tracker (D-13), `touch()`-ing 02-04's watchdog and appending a JSONL event **every turn** (D-11, D-14), and calling **only** `pursuit.sdk.engine` for game logic (QUAL-01 — zero board/capture logic re-implemented); `src/pursuit/main.py` — a thin shell (coverage-omitted) that reads `role.json` + `network.json` from the config dir given on the command line and runs the orchestrator, so `config/police/` and `config/thief/` start as two fully independent processes with no shared runtime object (NET-01, NET-02, NET-04); `scripts/dev_launch.py` — spawns both standalone processes for local iteration and gets out of the way, **never coordinating them** (D-02, CONTEXT-locked no-referee rule). Split `orchestrator.py` further if it approaches 150 lines — split, never compress. | 4 | 02-04, 02-07, 02-08 | NET-01, NET-02, NET-04, NET-05, NET-06, NET-07 |
| 02-10 | §10.4 milestone gate integration tests: `tests/integration/test_peer_roundtrip.py` proving **gate criterion 1** — a `type=move` envelope carrying `{x, y}` sent by peer A is received and decoded correctly by peer B, coordinates intact, through the real tool surface via the in-memory transport (NET-03, NET-06, NET-08, D-05/D-06/D-07); `tests/integration/test_turn_lifecycle.py` proving **gate criteria 2 and 3** — two independently constructed peer runtimes built from `config/police/` and `config/thief/` share no runtime object (NET-01, NET-02), a full INIT → HANDSHAKE → MY_TURN → WAIT_OPPONENT → GAME_OVER lifecycle runs through the orchestrator with a matching config digest (NET-04, NET-09), an illegal transition attempt is reported and correctly classified by severity (NET-05, D-10), a silent opponent triggers retry → backoff → technical win instead of a hang (NET-06, D-13), and a simulated freeze makes the watchdog write a fsynced incident record before its injected exit fires (NET-07, D-14). No test may touch a live socket or the real opponent. | 5 | 02-09 | NET-01…NET-09 (gate) |

---

## Decisions Coverage Trace

| Decision | Covered By |
|----------|------------|
| D-01 per-agent orchestrator, no referee process | 02-09 (loop + `main.py`), 02-05 (documented) |
| D-02 dev launcher + standalone two-terminal startup | 02-09 (`scripts/dev_launch.py`, `main.py`) |
| D-03 FastMCP streamable HTTP transport | 02-00 (`uv add fastmcp`), 02-06 (`run_async(transport="http", ...)`) |
| D-04 endpoints in per-agent config, not `game_params.json` | 02-00 (`network.json` files), 02-01 (`load_network_config`) |
| D-05 full four-tool surface now, stub bodies | 02-06, 02-05 (signatures documented), 02-10 (exercised) |
| D-06 typed envelope `{type, turn, sender, payload}` | 02-02 (shape + round-trip), 02-06 (tool args decode), 02-10 (gate) |
| D-07 push turn-passing, no polling | 02-06 (queue enqueue + immediate ack), 02-09 (loop pushes to opponent), 02-10 |
| D-08 handshake = connectivity + config hash | 02-02 (`config_digest`), 02-08 (exchange + compare) |
| D-09 State set INIT…ERROR | 02-03 (`State` enum), 02-08 (INIT→HANDSHAKE), 02-09 (full lifecycle) |
| D-10 severity-based illegal-transition policy | 02-03 (`transition()` + severity), 02-08 (reachability failure path), 02-09 (reporter wiring), 02-10 |
| D-11 JSONL event log + console echo | 02-04 (writer + schema), 02-09 (append every turn) |
| D-12 State enum + allowed-transitions dict, no FSM library | 02-03 |
| D-13 deadline → retry/backoff → technical win | 02-07 (mechanism), 02-09 (wiring), 02-10 (gate) |
| D-14 persist-every-turn + watchdog daemon thread | 02-04 (`event_log` + `Watchdog`), 02-09 (`touch()` per turn), 02-10 (gate) |
| D-15 config-hash mismatch aborts before move 1 | 02-02 (digest), 02-08 (abort path) |
| D-16 ports 8001/8002, env-overridable engineering default (**not** PARAMETERS.md) | 02-00 (`network.json` + `.env-example`), 02-01 (env override in loader), 02-05 (labelled as engineering default in the PRD) |
| D-17 retries 3 / backoff 5 s reused from PARAMETERS.md Table 19 rows 3–4, rationale stated | 02-00 (config values), 02-07 (consumer, zero literals), 02-05 (rationale documented) |

No orphan decisions: D-01…D-17 each appear in at least one plan.

> **Note on D-16's documentation duty.** CLAUDE.md requires the ports also be recorded as an
> engineering default in `docs/phases/phase-2/PLAN.md`. That file is written by the plan-phase
> orchestrator (ROADMAP 02-97) and is deliberately **not** a plan in this manifest; 02-05 carries
> the plan-owned half of the same statement in `docs/PRD_mcp_transport.md`.

---

## Wave Structure

```
Wave 0: 02-00  (deps + network config + constants + conftest + all test stubs)
Wave 1: 02-01, 02-02, 02-03, 02-04, 02-05
        (config loader / envelope+digest / state machine / event-log+watchdog / per-mechanism PRD)
Wave 2: 02-06, 02-07  (FastMCP tools + PeerRuntime / deadline tracker)
Wave 3: 02-08  (handshake — needs digest + state machine + peer runtime)
Wave 4: 02-09  (orchestrator + main.py + dev launcher — wires everything)
Wave 5: 02-10  (§10.4 milestone gate integration tests)
```

**Parallel-safety:** plans sharing a wave have **zero `files_modified` overlap**.

- Wave 1 — `02-01` owns `shared/loader_helpers.py`, `shared/network_config.py`,
  `shared/config.py`; `02-02` owns `network/envelope.py`, `network/config_hash.py`;
  `02-03` owns `network/state_machine.py`; `02-04` owns `network/event_log.py`,
  `network/watchdog.py`; `02-05` owns `docs/PRD_mcp_transport.md`. Each also owns only its own
  matching `tests/unit/test_*.py` stub. Disjoint by construction. `02-03`'s reporter is an
  injected Protocol declared in `state_machine.py`, so it does **not** import `02-04`'s
  `event_log` — that is what keeps the two parallel rather than sequential.
- Wave 2 — `02-06` owns `network/tools.py` + `network/peer_runtime.py`; `02-07` owns
  `network/deadline.py`. Disjoint. `02-07` takes timeout/retries/backoff as arguments rather
  than importing the runtime, so it depends only on `02-01`'s `NetworkParams` type.
- Waves 0, 3, 4, 5 are single-plan waves — no intra-wave overlap possible.

Wave-0 test stubs created by `02-00` (each later filled by exactly one plan, so the
stub-then-fill pattern never causes an intra-wave collision):
`tests/unit/test_network_config.py` (→02-01), `test_envelope.py` + `test_config_hash.py`
(→02-02), `test_state_machine.py` (→02-03), `test_event_log.py` + `test_watchdog.py` (→02-04),
`test_tools.py` + `test_peer_runtime.py` (→02-06), `test_deadline.py` (→02-07),
`test_handshake.py` (→02-08), `test_orchestrator.py` (→02-09),
`tests/integration/test_peer_roundtrip.py` + `tests/integration/test_turn_lifecycle.py` (→02-10).

---

## Requirement Coverage Audit

| Requirement | Plan(s) |
|-------------|---------|
| NET-01 two separate processes under `config/police/` vs `config/thief/` | 02-00, 02-01, 02-09, 02-10 |
| NET-02 no shared runtime state between the agents | 02-01, 02-06, 02-09, 02-10 |
| NET-03 each agent is simultaneously FastMCP server and client | 02-06, 02-08, 02-10 |
| NET-04 orchestrator is the single entry point, state-machine driven | 02-03, 02-09, 02-10 |
| NET-05 every illegal state transition is reported | 02-03, 02-04, 02-08, 02-09, 02-10 |
| NET-06 deadline tracker prevents freezing on the opponent | 02-07, 02-09, 02-10 |
| NET-07 watchdog monitors crashes and rescues data | 02-04, 02-09, 02-10 |
| NET-08 geometric message sent over localhost decoded correctly | 02-02, 02-06, 02-10 |
| NET-09 config file verified byte-for-byte identical on both sides | 02-02, 02-08, 02-10 |
| QUAL-02 no duplication — extract at 2+ copies | 02-01 |
| QUAL-11 zero hardcoded values in source | 02-00, 02-01, 02-07 |
| QUAL-12 zero secrets; `.env-example` committed | 02-00 |
| QUAL-13 `uv` is the sole package manager | 02-00 |
| DOC-02 per-mechanism PRD for the transport layer | 02-05 |

All nine of NET-01…NET-09 appear in at least one plan, and each is additionally pinned by a named
§10.4 gate assertion in 02-10. **Coverage complete.**

Standing gates carried by every plan and therefore not listed per-row: QUAL-07 (TDD red → green →
refactor), QUAL-08 (`bash scripts/check_line_limit.sh` — ≤150 lines, split never compress),
QUAL-09 (`uv run ruff check .` → 0), QUAL-10 (`uv run pytest --cov` ≥ 85%).

---

## OPEN — must ask user

One number required by this phase has **no source** in `docs/PARAMETERS.md` and is not covered by
D-16 or D-17. It is recorded here rather than invented.

| Number | Where it is needed | Why it has no source | Suggested resolution |
|--------|--------------------|----------------------|----------------------|
| **Watchdog poll interval** — how often the watchdog daemon thread wakes to compare `now - last_activity` against the 60 s threshold (RESEARCH Pattern 8 shows a placeholder `time.sleep(1.0)`) | `src/pursuit/network/watchdog.py` (plan 02-04) | PARAMETERS.md Table 19 row 7 supplies the *threshold* (60 s) but not the *sampling cadence*. Appendix F does not address it. It is deployment plumbing, in the same category as D-16's ports. | Ask the user to fix a value (any interval well below the 60 s threshold works; the smaller it is, the tighter the detection latency and the higher the idle CPU cost) and record it in `config/{police,thief}/network.json` as `watchdog_poll_seconds`, labelled — like the ports — an **engineering default, not a PARAMETERS.md game value**. Until answered, 02-04 must take the interval as a required constructor argument with **no default in source**, so the omission fails loudly rather than silently hardcoding a number. |

Nothing else in Phase 2 needs a number that PARAMETERS.md, D-16, or D-17 does not already supply.

---

## OUTLINE COMPLETE
