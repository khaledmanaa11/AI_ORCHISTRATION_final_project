# Phase 2: FastMCP Infrastructure - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the P2P plumbing: cop and thief as **two separate processes** under
`config/police/` and `config/thief/`, each **simultaneously a FastMCP server and client**,
exchanging **coordinate-only** messages over localhost. A per-agent orchestrator drives
turn order through a state machine; a deadline tracker and watchdog prevent freezes; the
shared game config is verified byte-for-byte identical on both sides (NET-01…NET-09).

Out of scope: strategy/RL (Phase 3), hints/scent/LLM (Phase 4), tunneling (Phase 5),
commit-reveal crypto (Phase 6), Gmail reporting/GUI (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Topology & startup
- **Per-agent orchestrator**: each agent process embeds its own orchestrator/main loop
  running the turn state machine. No third referee process — NET-04's "single entry point"
  is satisfied per agent, consistent with the P2P no-central-server rule.
- **Dev launcher + standalone**: a small dev script starts both peers locally for fast
  iteration, but each agent also starts standalone with one command in its own terminal —
  the standalone path is the league path.
- **Transport: FastMCP streamable HTTP** on configured localhost ports — the same
  transport ngrok tunnels in Phase 5, so cloud exposure requires zero transport changes.
- **Endpoints live in per-agent config** (`config/police/`, `config/thief/`): own listen
  port + opponent URL. NOT in the shared `game_params.json` (whose byte-for-byte identity
  must hold across sides).

### Tool surface & protocol
- **Full tool surface now, stub bodies**: define `handshake`, `receive_move`,
  `receive_barrier`, `game_over` with real signatures in Phase 2; later phases fill in
  behavior but never reshape the protocol.
- **Typed message envelope** `{type, turn, sender, payload}` for every message kind.
  Phase 2 uses `type=move` with payload `{x, y}`; hints (Phase 4) and commits (Phase 6)
  become new types in the same envelope.
- **Push turn-passing**: after choosing its move, an agent calls the opponent's
  `receive_move`; that incoming call wakes the opponent's turn. No polling loops; the
  deadline tracker wraps the wait.
- **Handshake = connectivity + config hash**: the game-start handshake proves
  reachability AND exchanges a SHA-256 of the shared game config, satisfying NET-09 in
  the same step. Phase 6 later adds the Step-0 declaration to this handshake.

### State machine
- **States**: INIT → HANDSHAKE → MY_TURN ↔ WAIT_OPPONENT → GAME_OVER, plus ERROR.
  Commit-reveal sub-states are inserted by Phase 6 when they become real.
- **Illegal transitions (NET-05): severity-based** — every attempt is logged + rejected;
  recoverable ones (duplicate message, out-of-order retry) keep the game running;
  protocol violations escalate to ERROR and end the game.
- **Reporting**: structured JSONL event log per agent + human-readable console echo.
  The JSONL log is the seed of the Phase-7 `log_<game_id>` artifact and replay viewer.
- **Implementation: State enum + explicit allowed-transitions dict** in a small module.
  No FSM library dependency; trivially unit-testable; fits the 150-line limit.

### Resilience
- **Deadline (NET-06)**: on a missed 30s response deadline, retry N times with backoff
  (N and backoff from config, never source), then declare a **technical win**, log the
  evidence, and end cleanly.
- **Watchdog (NET-07): persist-every-turn** — game state and JSONL log are flushed to
  disk every turn, so a crash loses nothing; the watchdog is a **background thread in
  each agent** watching a last-activity timestamp against the 60s threshold; on freeze it
  writes a final incident record and exits cleanly.
- **Config check (NET-09)**: SHA-256 of `game_params.json` exchanged during handshake;
  any mismatch **aborts before move 1** with a clear logged report.

### Claude's Discretion
- Module layout, naming, and file split (within the 150-line limit)
- Exact retry count / backoff defaults — config values within the negotiable ranges
- Test structure and mocking approach for the peer-to-peer calls

</decisions>

<specifics>
## Specific Ideas

- Timeout values come from `docs/PARAMETERS.md`: response timeout 30 s, watchdog
  threshold 60 s — both negotiable, both config-driven, never hardcoded.
- The two-terminal standalone startup mirrors the real league; the dev launcher is a
  convenience only and must not become a referee.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-fastmcp-infrastructure*
*Context gathered: 2026-07-28*
