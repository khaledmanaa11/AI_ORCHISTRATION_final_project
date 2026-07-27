# PLAN — Architecture & Technical Planning

**Version:** 1.00 · **Last updated:** 2026-07-27

> Architecture document per [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §2.2: C4 diagrams,
> process flows, ADRs, and data contracts. Numbers are illustrative pointers only — the
> binding values are in [PARAMETERS.md](PARAMETERS.md). See [PRD.md](PRD.md) for *what*,
> [TODO.md](TODO.md) for *when*.

## 1. C4 Model

### Level 1 — System Context

```
        +-------------------+        MCP over tunnel        +-------------------+
        |   OUR TEAM        |  <------------------------->  |  OPPONENT TEAM    |
        |  cop  +  thief    |     (hints, moves, commits)   |  cop  +  thief    |
        +---------+---------+                               +-------------------+
                  |
                  | send-only JSON report (Gmail API, OAuth2)
                  v
        +-------------------+
        |  Lecturer inbox   |  rmisegal+uoh26finalgame@gmail.com
        +-------------------+
```

Our cop plays the opponent's thief; our thief plays their cop. No central server, no referee.

### Level 2 — Container (one deployable per agent)

```
  config/police/  ─┐                        ┌─ config/thief/
                   ▼                        ▼
  +----------------------------+   +----------------------------+
  |  POLICE PROCESS            |   |  THIEF PROCESS             |
  |  (separate OS process)     |   |  (separate OS process)     |
  |  FastMCP server + client   |   |  FastMCP server + client   |
  +----------------------------+   +----------------------------+
        │  NO shared runtime state between the two (rule 2)  │
        └── shared *library* code only (src/<pkg>/), never live game state ──┘
```

Each container is independently launchable and reads only its own config directory.

### Level 3 — Component (inside one peer)

```
  +-------------------------------------------------------------+
  |  PeerRuntime                                                |
  |                                                             |
  |  [MCP Transport]  server (@mcp.tool) + client to opponent   |
  |        │                                                    |
  |  [Orchestrator + State Machine]  turn order, illegal-state  |
  |        │            reporting, watchdog, deadline tracker   |
  |        ▼                                                     |
  |  [Strategy Module : BrainBase]  belief map → Q-policy →     |
  |        │            _pick_move / _decide_move (fallback:    |
  |        │            Bayes + Manhattan)                      |
  |        ▼                                                     |
  |  [Language Layer]  LLM hint decode (in) + bluff gen (out)   |
  |        │                                                    |
  |  [Crypto]  commit-reveal (SHA-256), nonce, canonical JSON   |
  |        │                                                    |
  |  [Gatekeeper]  quota → token bucket → DOS → Gmail API       |
  |        │                                                    |
  |  [SDK layer]  single entry point; GUI/CLI are thin shells   |
  +-------------------------------------------------------------+
```

### Level 4 — Code (key types; final names set during their phase)

- `sdk.GameSDK` — single entry point exposing every operation (§4).
- `services.board.Board` — grid, movement legality, barriers, capture detection.
- `services.orchestrator.Orchestrator` — state machine + turn loop.
- `strategy.BrainBase` — `_pick_move` (cop & thief), `_decide_move` (cop barriers);
  subclasses `QLearningBrain`, `BayesManhattanBrain` (fallback).
- `strategy.belief.BeliefMap`, `strategy.scent.ScentField` — belief/pheromone models.
- `language.decoder`, `language.bluff` — LLM decode/bluff (only touchpoints of the LLM).
- `crypto.commit_reveal` — hash/nonce/reveal/audit over canonical JSON.
- `shared.gatekeeper.ApiGatekeeper`, `shared.config.Config`, `shared.version` (1.00).

## 2. Process Flows (UML-style)

### 2.1 Per-turn decision pipeline (§6.2)

```
incoming hint + scent
   → hint decode (LLM parses text)
   → belief update (Bayes rule)
   → Q-policy move choice        ← the ALGORITHM decides here, never the LLM (rule 25)
   → LLM bluff text (deception, ≤ hint word limit)
   → Commit pack (out)
```

### 2.2 Commit-reveal exchange (§5.3)

```
A: Commit(H = SHA256(canonical{state,move,intent,nonce}))  ──►  B
A                                             ◄──  B: Acknowledge
A: Reveal(move, hint, intent)  (nonce STILL hidden)         ──►  B   (and symmetric)
... repeat each turn ...
End of game:
A: FinalReveal(all nonces)  ◄──►  B: FinalReveal(all nonces)
Both re-hash the full log and compare  →  any mismatch = technical loss, 0/0 (rule 19)
```

### 2.3 Deployment

```
Dev:    police(localhost:PA)  ◄─► thief(localhost:PT)        (Phases 1–4, 6)
League: local peer ──ngrok/Localtonet──► public URL ◄── opponent peer   (Phase 5+)
Report: peer ──Gatekeeper──► Gmail API (OAuth2 send-only) ──► lecturer inbox
```

## 3. Architecture Decision Records (ADRs)

| # | Decision | Rationale | Alternatives / trade-off |
|---|----------|-----------|--------------------------|
| ADR-1 | **Tabular Q-learning** for move selection | Game is a Dec-POMDP; reward maps directly from the scoring table; finite 7×7 state space is tractable without a neural net (§B) | Pure Bayes+Manhattan (kept as fallback — predictable); deep RL (overkill, out of scope) |
| ADR-2 | **FastMCP** peer protocol | MCP is the mandated protocol; `@mcp.tool` makes each peer a symmetric server+client | A2A/ACP (optional complements only, not required) |
| ADR-3 | **Two separate processes**, shared library only | Rule 2 — sharing live state is instant disqualification for information leakage | Single process w/ two threads (forbidden: shared memory) |
| ADR-4 | **One gatekeeper** for all external calls | Satisfies both Segal §5 and the rulebook §9.3.1; overflow queues, never crashes | Per-call rate limiting (duplication, drift; where the two specs differ, take the stricter value) |
| ADR-5 | **Canonical JSON** (`sort_keys=True, separators=(",",":")`) for hashing | Byte-identical input on both peers; inconsistent serialization is the top cause of a false mismatch | Pickle/repr (non-portable, fragile) |
| ADR-6 | **`secrets`** for nonces (`token_hex(16)`, `compare_digest`) | Cryptographically secure; blocks dictionary attacks (rule 18) | `random` (predictable — disqualifying) |
| ADR-7 | **LLM only at the two ends** (decode-in, bluff-out) | Rule 25 — a hallucinated move is an illegal move and a technical loss | LLM chooses moves (forbidden) |
| ADR-8 | **Heuristic fallback** always live | Non-stationary env (opponent co-learns); bounds damage on unvisited Q-states | Q-only (acts on meaningless zero for unseen states) |

## 4. Interfaces & Contracts

### 4.1 Strategy interface

```python
class BrainBase:
    def _pick_move(self, obs: Observation) -> Move: ...        # cop & thief
    def _decide_move(self, obs: Observation) -> Barrier | None: ...  # cop only
```
Wired via config `[strategy]` `police_class` / `thief_class` in `package.module:Class` form.

### 4.2 MCP tools (geometric; coordinates only at transport, never in hints)

`receive_commit(hash)` · `acknowledge()` · `receive_reveal(move, hint, intent)` ·
`answer_geometry(query)` · `final_reveal(nonces)`. Hints crossing the *game* channel are
natural language only (rules 26–27).

### 4.3 Gatekeeper

```python
class ApiGatekeeper:
    def __init__(self, config: RateLimitConfig): ...
    def execute(self, api_call, *args, **kwargs): ...   # rate-check → queue → retry → log
    def get_queue_status(self) -> QueueStatus: ...
```
Limits from `config/rate_limits.json` (Table 19: rpm ≥30, parallel ≥2, backoff ≥5s,
retries ≥3, queue ≥100). Token bucket: `tokens ← min(C, tokens + r·Δt)`, allow iff `≥1`.

## 5. Data Schemas — the four JSON artifacts (PARAMETERS.md)

All share a `game_uid`; filenames embed `game_id` and match number `<NN>`.

- **`declaration_<game_id>.json`** — pre-game seal: both identities, repo URLs, MCP
  addresses, hardware spec, language model, agreed token ceiling, start/end times, commit hash.
- **`config_<game_id>_g<NN>.json`** — the agreed configuration: every numeric parameter,
  cryptographically locked, byte-identical on both sides; version `1.00`.
- **`log_<game_id>_g<NN>.json`** — turn-by-turn journal: commitments, moves, hints,
  verdicts, nonce, hash — enough for full replay verification.
- **`result_<game_id>.json`** — final summary across sub-games; **this is the mandatory
  emailed report**; includes total tokens consumed (rule 54).

Commit-pack hashed object: `{"state":…, "move":…, "intent":"truth|lie", "nonce":…}` →
canonical JSON → SHA-256.

## 6. Repository Layout (§2.4)

```
src/<pkg>/{sdk,services,shared,constants.py} · tests/{unit,integration}
docs/{PRD,PLAN,TODO,PRD_<mechanism>}.md · config/{police,thief,setup.json,rate_limits.json}
data/ results/ assets/ notebooks/ · README.md · pyproject.toml · uv.lock · .env-example · .gitignore
```

## 7. Concurrency (§15)

Multiprocessing separates cop and thief (CPU-bound, own memory — also satisfies rule 2).
Multithreading handles I/O (network, mail). Shared structures guarded by locks / `queue.Queue`.

---
*ADRs are append-only; supersede rather than edit. Update this file when a contract changes.*
