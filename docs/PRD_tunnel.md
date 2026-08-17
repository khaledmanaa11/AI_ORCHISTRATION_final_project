# PRD — The tunnel (public exposure, the shared-secret door, and the bounded repair)

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-08-17
**Requirements:** CLOUD-01, CLOUD-02 · **Rules:** **10** (a tunneling tool is used),
**39–40** (no credential in source or git), 42 · **Phase:** 5 (plans 05-01, 05-02, 05-03,
05-11) · **Related:** [PRD_mcp_transport.md](PRD_mcp_transport.md),
[ARCHITECTURE.md](ARCHITECTURE.md) §5,
[GATE-5-MEASUREMENT.md](phases/phase-5/GATE-5-MEASUREMENT.md)

> **This document exists because `PRD_mcp_transport.md` says it must.** That PRD covers the
> Phase-2 FastMCP peer layer and puts *"ngrok/Localtonet tunneling"* out of scope **in as
> many words** (`docs/PRD_mcp_transport.md:28`), so `network/`'s own PRD provably does not
> specify `src/pursuit/network/tunnel_manager.py`. `docs/SUBMISSION-CHECKLIST.md` tracks
> that hole as row `G1-M-TUNNEL`, and the gate derives it — the module has to exist and the
> disclaimer has to still be in the file — rather than asserting it.
>
> Per-mechanism PRD required by CLAUDE.md and [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md)
> §2.3, written after the code, mirroring [PRD_commit_reveal.md](PRD_commit_reveal.md)'s
> section order. Every number is traced or labelled structural — **nothing here is invented.**

---

## 1. Mechanism and scope

The transport is unchanged by this mechanism: `PRD_mcp_transport.md` chose streamable HTTP
precisely so cloud exposure would need **zero transport changes**. What this mechanism adds
is everything between "a local port" and "an opponent on another network can reach it, and
only they can":

| Module | Role |
|---|---|
| `src/pursuit/network/tunnel_manager.py` | the tunnel's whole lifecycle — start, health probe, bounded reconnect, stop |
| `src/pursuit/network/tunnel_wiring.py` | the decision to use a tunnel at all, the exchange block, the watch task, and the `run_with_tunnel` wrapper |
| `src/pursuit/shared/tunnel_config.py` | the fail-loud loader for `tunnel.json`, and `require_env` |
| `src/pursuit/network/secret_guard.py` | `SharedSecretMiddleware` — the lock on the public door (D-56) |
| `src/pursuit/network/secret_wiring.py` | where that middleware and the outgoing header are attached |
| `config/police/tunnel.json`, `config/thief/tunnel.json` | names only: a provider, a header name, three environment-variable names |

**In scope:** ngrok exposure through `pyngrok`; the static reserved domain; the
shared-secret ASGI boundary; the liveness watch and the bounded repair (05-11); the
operator-facing exchange block; and the Localtonet fallback as **documentation**
(`docs/phases/phase-5/LOCALTONET-FALLBACK.md`, D-57).

**Out of scope, each stated as what owns it instead:** the MCP tool surface, the handshake
and the state machine ([PRD_mcp_transport.md](PRD_mcp_transport.md)); commit-reveal and the
Step-0 declaration that crosses this channel ([PRD_commit_reveal.md](PRD_commit_reveal.md));
the freeze watchdog, which this mechanism deliberately does **not** touch (§2.3); and any
Localtonet *code path* — there is none anywhere in `src/`, `scripts/` or `config/`, which
that runbook states in its own first paragraph.

---

## 2. Topology and design (D-54, D-55, D-56, D-57)

### 2.1 The tunnel is opt-in, and the opt-in signal is an environment variable

`tunnel.json` carries **no enable flag** — D-55 makes that file strings only. The presence
of the static-domain environment variable is the signal:
`tunnel_wiring.build_tunnel_manager` returns `None` when `tunnel.json` is absent *or* its
`domain_env` variable is unset, and `run_with_tunnel(None, body)` runs `body()` exactly as
it always has. Every loopback test and every dev flow therefore takes the pre-Phase-5 path
unchanged, with no task created and no behaviour altered.

### 2.2 Every external call is injected, so no test touches ngrok

Each pyngrok call and timing primitive on `TunnelManager` is a **keyword-only, injectable
callable bound to the real function as a constructor default** — the DI style `Gatekeeper`
(clock/sleep) and `Watchdog` (clock/sleeper/exit_action) already use. Production callers
pass nothing.

`pyngrok` is imported in exactly one module, and only as function references. A plain
import never triggers pyngrok's own lazy binary download; that happens inside its first
real `connect()`. The consequence is that the whole unit suite drives this class with
fakes: **zero real processes, zero real sleeps, zero `ngrok.exe`** — which is what lets
`tests/unit/test_tunnel_manager.py`, `test_tunnel_manager_reconnect.py`,
`test_tunnel_wiring.py`, `test_tunnel_wiring_lifecycle.py` and `test_tunnel_wiring_monitor.py`
run offline as CLAUDE.md requires.

### 2.3 A tunnel drop is not a process freeze, and that is why the watchdog is untouched

`pyngrok` never auto-reconnects a dropped tunnel; it only exposes
`get_ngrok_process().healthy()` for a caller to poll. When ingress dies, the local FastMCP
server and the turn loop keep running — only the external path is broken. The concern is
therefore entirely `TunnelManager`'s, and `src/pursuit/network/watchdog.py` is deliberately
not modified by this mechanism.

### 2.4 The bounded repair, and the drop that proved it was never wired (05-11)

`ensure_connected()` reconnects to the **same** static domain while unhealthy, bounded by
`retry_count` with `backoff_seconds` waits — Table 19 rows 3/4, **reused**, so D-55 adds no
new number. The same domain every time, so the opponent's copy of our public URL never goes
stale mid-game.

**It was designed, tested and documented in 05-01 — and called by nothing.** Remote-round
attempt 2 (2026-08-16, game `5efbc5811fabfac4`) is the evidence: machine A's ingress died
at turn 4, B's pushes got `ConnectError`, A idled 60 s and its watchdog killed it
verdictless. `grep` over `src/` and `scripts/` returned no caller.

05-11 supplied it. `tunnel_wiring.monitor_tunnel` is a watch task that:

- polls every `NetworkParams.watchdog_poll_seconds` — the exact reuse
  `tunnel_config.py`'s docstring already declared under D-55/D-18, **zero new numbers**;
- runs both the probe and `ensure_connected()` through `asyncio.to_thread`, because
  `ensure_connected` is synchronous and sleeps: a 15–20 s loop stall would itself feed the
  peer's `OPPONENT_UNRESPONSIVE` ladder;
- prints `DOWN` / `RESTORED` / `EXHAUSTED` lines, which are retained console evidence under
  the remote-round runbook;
- **returns after one exhausted repair.** D-55's bound is per-drop, and this task never
  turns it into an unbounded retry loop.

`run_with_tunnel` starts the task after `start()` and the exchange block, and cancels it in
`finally` **before** `tunnel.stop()`. Three containment rules hold at the edges: a start
failure raises **before** `body()` is invoked at all (a peer that would play unreachable
must never begin the game); a repair already inside a worker thread when teardown lands is
turned into a no-op by `ensure_connected`'s own `_stopped` guard, never a resurrection of
the agent that was just killed; and a watch that *dies raising* is contained to one printed
line so it can never eat a resolved game or skip teardown.

### 2.5 The lock on the public door (D-56)

`SharedSecretMiddleware` is a pure ASGI callable attached in the **same** `run_async` call
that already passes `sockets=`, so it runs at the ASGI boundary — **before** any FastMCP
session or tool machinery sees the request. It was deliberately not written as a check
inside each `@mcp.tool` handler: five copies would drift, and a malformed non-tool request
would still reach the server before any of them ran.

Comparison uses `secrets.compare_digest`, the one digest-comparison idiom this project
already established in `src/pursuit/network/config_hash.py`. The rejection log records the
remote address and the missing/mismatched **fact** only — never the expected value, because
rule 4 extends to logs. Non-`http` scopes pass through untouched; an `http` scope without
the header gets a plain 403 and no session, no tool dispatch and no partial MCP state.

One defensive detail with a source: every outgoing call carries
`ngrok-skip-browser-warning`. ngrok's free-tier interstitial triggers only on
`Accept: text/html`, which the MCP client never sends, so this is a zero-cost no-op off
ngrok and is documented as such rather than as a fix for an observed failure.

### 2.6 Secrets are names, never values (rules 39–40)

`config/police/tunnel.json` is six string fields: a `provider`, a `secret_header` name, and
the **names** of three environment variables — `NGROK_AUTHTOKEN`, `PURSUIT_NGROK_DOMAIN`,
`PURSUIT_TUNNEL_SECRET`. No value is in git, and `.env` is untracked and ignored, proven by
its own `git check-ignore` assertion in `docs/SUBMISSION-CHECKLIST.md` group 4.

`load_tunnel_config` never touches `os.environ`. Resolution is a separate, explicit step:
`require_env` raises **naming the variable** and is called by `TunnelManager.start()` for
the authtoken and the domain **before** any pyngrok call, so a missing variable is one
clear startup message instead of a cryptic mid-connect ngrok failure.

The **exchange block** — the one artifact a human copy-pastes to the opposing team —
carries the public URL, the header name, and *which environment variable the opponent must
set*. It never carries the secret value.

---

## 3. Interfaces

```python
# src/pursuit/network/tunnel_manager.py
class TunnelManager:
    def __init__(self, params: TunnelParams, network_params: NetworkParams, *,
                 connect=ngrok.connect, disconnect=ngrok.disconnect, kill=ngrok.kill,
                 get_process=ngrok.get_ngrok_process, sleep=time.sleep,
                 clock=time.monotonic) -> None: ...
    def start(self) -> None: ...          # preflights both env vars BY NAME, then connects
    def healthy(self) -> bool: ...        # local ngrok agent process only -- see Sec4
    def ensure_connected(self) -> bool: ...  # bounded by retry_count/backoff_seconds
    def stop(self) -> None: ...           # disconnect then kill, exactly once, idempotent

# src/pursuit/network/tunnel_wiring.py
def build_tunnel_manager(config_dir, net: NetworkParams) -> TunnelManager | None: ...
def exchange_block(public_url: str, params: TunnelParams) -> str: ...
async def monitor_tunnel(tunnel: TunnelManager, *, sleep=asyncio.sleep,
                         to_thread=asyncio.to_thread) -> None: ...
async def run_with_tunnel(tunnel: TunnelManager | None, body, *, monitor=monitor_tunnel): ...

# src/pursuit/shared/tunnel_config.py
def load_tunnel_config(path) -> TunnelParams: ...   # raises KeyError / TypeError, fail-loud
def require_env(var_name: str) -> str: ...          # raises KeyError NAMING the variable

# src/pursuit/network/secret_guard.py
class SharedSecretMiddleware: ...                   # pure ASGI, 403 before any tool body
def build_middleware(...): ...
def client_headers(...): ...
```

---

## 4. What `healthy()` does and does not detect — stated, not implied

pyngrok latches its started/connected flags at startup and probes only the **local** agent
API. So `healthy()` detects **agent-process death and local-API death**. It does **not**
detect an upstream session blip while the local process lives — that is the ngrok agent's
own built-in reconnect. `get_ngrok_process` is also not read-only: pyngrok may start a
fresh agent in place of a dead one, and a fresh agent reporting healthy *without this
manager's domain bound* is the residual blind spot.

This envelope is written into the method's own docstring, and it is repeated here because
the temptation is to read the 05-11 watch task as closing every drop. It closes the drops
it can see.

---

## 5. Parameters and their sources

Every number this mechanism uses. **It introduces none of its own.**

| Parameter | Value | Status | Source |
|---|---|---|---|
| Reconnect attempts | `NetworkParams.retry_count` = 3 | **minimum** | `docs/PARAMETERS.md` Table 19 row 4, via `config/police/network.json` (D-17/D-55 reuse) |
| Backoff between attempts | `NetworkParams.backoff_seconds` = 5 | **minimum** | Table 19 row 3, same file |
| Liveness poll cadence | `NetworkParams.watchdog_poll_seconds` = 1 | reused | D-18 / D-55, same file — declared in `tunnel_config.py`'s docstring before it had a caller |
| Local port to expose | `NetworkParams.port` | config | `config/police/network.json` |
| Provider, header name, env-var names | strings | structural | `config/police/tunnel.json` (D-55) |
| Authtoken, domain, shared secret | **absent from the repository** | — | `os.environ` only (rules 39–40) |

`tunnel.json` contains **not one number** beyond its `version` string. That is the design:
a numeric knob in this file would be a number without a PARAMETERS row.

---

## 6. Acceptance criteria for this mechanism

The §10.4 Phase-5 milestone gate, measured in
[`GATE-5-MEASUREMENT.md`](phases/phase-5/GATE-5-MEASUREMENT.md). Both criteria carry real
runs; neither reads PENDING.

**Criterion 1 — each peer is reachable on the public internet. PASS**, measured
2026-08-09T09:41:20Z by `scripts/gate5_tunnel_smoke.py`, which drives the **real** shipped
`TunnelManager` and `SharedSecretMiddleware` rather than a reimplementation. Two real HTTP
round trips through the public URL: one with the secret header returned the tool list
(`200`) — five names at that date, nine since Phase 6 added the commit-reveal
handlers; one without it got `403` **through the tunnel**, not through loopback. Round trip
1.859 s (informational — §10.4 sets no latency bound). The script refuses to run, naming
every missing variable, if any of the three environment variables is unset.

That smoke test is explicitly **not** criterion 2: it proves reachability from the *same*
machine via the public URL.

**Criterion 2 — a remote agent connects through the tunnel and plays a full round. PASS**,
closed 2026-08-16 by **attempt 4**, after three attempts across three days failed for three
different reasons and the status was held at PENDING each time rather than softened.

| | |
|---|---|
| Attempt 1 (2026-08-13) | a complete round, but the two sides' verdicts **disagreed** and the game UIDs split — not closed |
| Attempt 2 (2026-08-16 am) | a mid-game tunnel-ingress drop; the designed repair had no caller — not closed; this is what 05-11 fixed |
| Attempt 3 (2026-08-16 midday) | clean, but on template-fallback hints, not the live model — not closed |
| **Attempt 4 (2026-08-16 ≈13:29Z)** | **two complete games, both `capture`, both `audit_verdict matched=true` on both sides, one shared game UID per game, live `claude-haiku-4-5` on both machines** |

Both games ran on commit `0632e04`, over
`perdurable-mireille-nonzoologically.ngrok-free.dev`, across a genuine network boundary —
machine A on a phone hotspot, machine B (Windows 11, 20-core) on wired ethernet. Both
peers' logs, ledgers and cross-signed declarations are retained under
`docs/phases/phase-5/remote-round-2026-08-16-attempt4/` and were independently re-verified,
**26/26 checks per game**: every ledger `h_commit` recomputes, each side's six committed
hashes are byte-identical to what the *other* side logged as received over the tunnel, the
outcomes and audit verdicts agree, and all four declaration digests recompute.

### 6.1 Three things attempt 4 does **not** prove

Copied from the measurement document rather than summarised away, because the narrative arc
"attempt 2 → 05-11 → attempt 4" invites exactly the wrong reading:

1. **The 05-11 repair path never fired.** No tunnel drop occurred in either game. Attempt 4
   is evidence that a **healthy** tunnel completes a round — not live evidence that
   `ensure_connected()` repairs a dropped one. That path's evidence is unit-level.
2. **The second game is a deterministic replay of the first** — identical moves, positions
   and outcome, by design of the policy's seeded tie-break. It corroborates the transport;
   it is not a second sample of the game logic.
3. **Machine B's console was not retained**, only machine A's. The closing condition — both
   JSONLs, agreeing verdicts, the network note — is met without it.

**And one thing neither criterion covers: this was our own second machine, not another
team's agent.** The cross-team case is 08-13's, and **no league game has been played.**

**OPEN:** none numerically — every value in §5 is traced or absent by design. Operationally
open: rule 10's Localtonet option exists only as a runbook; if it ever has to become code,
that is new scope, not a gap in this phase.
