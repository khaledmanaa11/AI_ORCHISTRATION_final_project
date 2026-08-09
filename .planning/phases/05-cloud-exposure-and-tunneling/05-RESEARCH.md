# Phase 5: Cloud Exposure and Tunneling - Research

**Researched:** 2026-08-09
**Domain:** ngrok/Localtonet tunneling wrapped around an existing FastMCP 3.4.5 streamable-HTTP
peer (Python 3.11.9, uv, Windows 11)
**Confidence:** HIGH (stack/SDK choice, transport seams — read directly from installed source
and official docs) / MEDIUM (Localtonet fallback, reconnect UX) / LOW-flagged where noted

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tunnel**
- Primary provider: ngrok — free-tier static domain (URL survives restarts — matters on
  league day), solid Windows support, auth token via env var (`NGROK_AUTHTOKEN`, never in
  source). Localtonet documented as the fallback (both are named by rule 10, so either is
  compliant).
- Launcher-managed lifecycle: agent startup can launch the tunnel (ngrok Python SDK/API),
  read the assigned public URL, print it for sharing with the opponent team, and verify
  liveness. The opponent's URL is pasted into the per-agent config — the Phase-2 endpoint
  seam, unchanged.

**Validation (Stage-5 gate)**
- Genuine remote round: one agent runs on a different machine/network (friend's laptop,
  phone hotspot, university PC) against the tunnel URL — a full round, exactly what the
  gate demands. Same-machine-via-public-URL is acceptable only as a smoke test before the
  real one.

**Interim protection**
- Shared-secret header until Phase 6: a token (env var, exchanged with the opponent team
  alongside the URL) checked on every request — keeps internet scanners off the exposed
  MCP tools. Phase 6's commit-reveal layers on top; this header stays as transport-level
  hygiene.

### Claude's Discretion
- ngrok SDK vs subprocess management; reconnect/retry behavior on tunnel drop
- How the printed URL/token exchange is formatted for the opponent team
- Test structure (tunnel mocked in unit tests; real tunnel only in the manual gate run)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

## Summary

Phase 5 wraps, but does not touch, the Phase-2 transport. `PeerRuntime._run_http` (in
`src/pursuit/network/peer_runtime.py`) already binds `127.0.0.1:<port>` and calls
`FastMCP.run_async(transport="http", host=..., port=..., sockets=[...])`; a tunnel process
forwards that same local port to a public HTTPS URL. Nothing about the MCP protocol, the
envelope shapes, or `NetworkParams` changes — only two new seams are added: (1) a
`TunnelManager` that starts/monitors/stops the tunnel process and exposes its public URL,
wired into `agent_lifecycle.run_agent` alongside `PeerRuntime.start()`/`stop()`; and (2) a
shared-secret check on every request, which is a **client-side header on the
`fastmcp.Client`** plus a **server-side ASGI middleware on `run_async`**, both of which have
concrete, already-parameterized seams in the installed fastmcp 3.4.5 source (see Architecture
Patterns).

**Primary recommendation:** use `pyngrok` (not the official `ngrok-python` SDK) to drive the
ngrok agent — `ngrok-python` 1.7.0 requires Python **>=3.12** (verified via PyPI JSON API),
and this project runs Python **3.11.9**; installing it would fail outright. `pyngrok`
requires only `>=3.9`, is a pure-Python wrapper that downloads and manages the real
`ngrok.exe` binary for you (no hand-rolled subprocess/stdout-parsing/local-API-polling code
needed), and its public functions (`ngrok.connect`, `ngrok.get_ngrok_process().healthy()`,
`ngrok.disconnect`, `ngrok.kill`) are trivial to inject as fakes in unit tests — the same
dependency-injection style already used by `Gatekeeper` (`clock`/`sleep`) and `Watchdog`
(`clock`/`sleeper`/`exit_action`) in this codebase.

A second, higher-value finding: **Table 19 in `docs/PARAMETERS.md`** ("Gatekeeper: rate
limiting and protection" — retries=3, wait-after-error=5s, response-timeout=30s) already
supplies every retry/backoff number `network.json` uses today (`retry_count`,
`backoff_seconds`, `response_timeout`), and `watchdog_poll_seconds` (1s) is the codebase's
own precedent for an "engineering default, not book-sourced" polling cadence
(`watchdog.py` docstring, "D-18"). The tunnel's own reconnect-on-drop logic should **reuse
these existing numbers** (retries_before_failure=3, wait_after_error=5s from Table 19;
poll cadence = the same 1s D-18 precedent) rather than inventing new ones — this keeps the
phase compliant with CLAUDE.md rule 1 ("never invent a numeric value") with **zero new
numeric parameters required** for `tunnel.json`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pyngrok` | 8.1.2 (latest, `requires_python >= 3.9`) | Drive the local `ngrok` agent: auth, connect, read public URL, health-check, disconnect | Pure-Python wrapper, manages the `ngrok.exe` binary itself, actively maintained (alexdlaird/pyngrok), Windows wheels/binary supported, works on the project's actual Python 3.11.9 |
| `fastmcp` | 3.4.5 (already pinned) | Unchanged — server + `Client` | No change; tunnel wraps it |
| `starlette` (fastmcp dep, already installed) | matches fastmcp 3.4.5's pin | ASGI middleware base class for the shared-secret check | Already a transitive dependency (`fastmcp.server.http` imports `starlette.middleware.Middleware`) — no new dependency needed |

### Explicitly rejected
| Instead of | Rejected | Why |
|------------|----------|-----|
| `pyngrok` | `ngrok` (official `ngrok-python` SDK, 1.7.0) | `requires_python = ">=3.12"` (verified via `https://pypi.org/pypi/ngrok/json`); project's venv is Python 3.11.9 (`uv run python --version`). Installing it would fail at `uv add` time. Bumping the interpreter to unblock it is out of scope for this phase and would force `pyproject.toml`'s `requires-python` floor up project-wide. |
| `pyngrok` | Hand-rolled `subprocess.Popen(["ngrok", "http", ...])` + poll `http://127.0.0.1:4040/api/tunnels` | Reinvents exactly what `pyngrok` already does (binary download/management, health check, structured `NgrokTunnel` object with `.public_url`) — a "don't hand-roll" case (see below) |

### Installation
```bash
uv add pyngrok
```
No other new runtime dependency. Localtonet is documentation-only in this phase (see
below) — no Python package.

## Architecture Patterns

### Where the tunnel lifecycle hooks in

`src/pursuit/network/agent_lifecycle.py::run_agent()` is the single per-agent entry point
(confirmed by reading it): it builds `AgentContext` via `default_context()`, calls
`ctx.watchdog.start()`, then `await start_server(ctx)` (which is `await ctx.runtime.start()`),
then opens `ctx.runtime.client()` for the handshake, runs the turn loop, and in `finally`
calls `shutdown_cleanly(ctx)` (`ctx.watchdog.stop()` then `await ctx.runtime.stop()`). A
`TunnelManager` fits the same shape:

```
run_agent():
    cfg = load_agent_config(config_dir)          # existing
    tunnel = TunnelManager(cfg.tunnel)            # NEW — cfg.tunnel from a new tunnel.json
    tunnel.start()                                 # NEW — before/alongside ctx.runtime.start()
    print(f"public_url={tunnel.public_url}")       # NEW — the opponent-facing artifact
    ctx = default_context(cfg, ...)
    ctx.watchdog.start()
    await start_server(ctx)
    try:
        ... handshake + turn loop, unchanged ...
    finally:
        await shutdown_cleanly(ctx)
        tunnel.stop()                              # NEW — mirror ctx.watchdog.stop() ordering
```

`AgentConfig` (in `agent_wiring.py`) already loads nine per-agent config files
(`game_params.json`, `network.json`, `belief.json`, `deception.json`, `language.json`,
`strategy.json`, `resolution.json`, `scent.json`, `role.json`) via a uniform fail-loud
`load_*_config(path)` pattern built on `shared/loader_helpers.py`'s `require_str`/
`require_int`/etc. Add a tenth: `config/{police,thief}/tunnel.json` +
`pursuit.shared.tunnel_config.load_tunnel_config()` + a `TunnelConfigKey` class in
`config_keys.py`, following that exact convention — this is the established "don't
duplicate a config loader" seam, not a new pattern.

**What actually needs to live in `tunnel.json` vs. env vars vs. reused numbers:**
- `provider` ("ngrok" | "localtonet") — structural, config
- the shared-secret **header name** (e.g. `"X-Pursuit-Secret"`) — structural, config
- NOT the auth token, NOT the shared-secret value, NOT the static domain if it's
  considered sensitive/per-deployment — these are `os.environ.get()` only
  (`NGROK_AUTHTOKEN`, a new `PURSUIT_TUNNEL_SECRET`, and optionally
  `PURSUIT_NGROK_DOMAIN` mirroring the existing `PURSUIT_HOST`/`PURSUIT_PORT`/
  `PURSUIT_OPPONENT_URL` env-override convention already in `network_config.py`)
- reconnect retry count / backoff seconds — **reuse** `network.json`'s existing
  `retry_count`/`backoff_seconds` (Table 19 rows 4/3) or `NetworkParams` directly, rather
  than adding new numbers to `tunnel.json` (see Summary)
- liveness poll cadence — **reuse** `watchdog_poll_seconds` (the existing D-18 engineering
  default already in `network.json`) rather than adding a new one

### Client-side: injecting the shared-secret header

`PeerRuntime.client()` currently does:
```python
return Client(self._params.opponent_url, timeout=self._params.response_timeout)
```
Passing a bare URL **string** to `Client()` goes through `fastmcp.client.transports.
inference.infer_transport()`, which builds a `StreamableHttpTransport(url=...)` with
**no headers** (confirmed by reading `inference.py` and `transports/http.py` in the
installed 3.4.5 package). To attach a header on every outgoing call, construct the
transport explicitly instead:

```python
# Source: .venv/Lib/site-packages/fastmcp/client/transports/http.py (StreamableHttpTransport.__init__)
from fastmcp.client.transports import StreamableHttpTransport

transport = StreamableHttpTransport(
    self._params.opponent_url,
    headers={
        "X-Pursuit-Secret": shared_secret,          # from os.environ, D-16-style override
        "ngrok-skip-browser-warning": "true",         # harmless no-op off ngrok; see Pitfalls
    },
)
return Client(transport, timeout=self._params.response_timeout)
```
This is a one-line change at the one place `Client(...)` is constructed (NET-03's own
documented seam — "the caller owns the async-context-manager lifetime; the runtime never
holds an open client of its own").

### Server-side: enforcing the header on every request

`FastMCP.run_async`/`run_http_async` (confirmed via `inspect.signature` on the installed
3.4.5 package, and by reading `fastmcp/server/mixins/transport.py`) already accepts:
```python
middleware: list[ASGIMiddleware] | None = None   # ASGIMiddleware = starlette.middleware.Middleware
```
This is the **best seam** for a shared-secret check: it wraps the whole ASGI app
(everything under `/mcp`, before any MCP session/tool dispatch), so a request missing the
header never reaches FastMCP's own routing — no partial state, no risk of the check being
bypassable via some other path. `PeerRuntime._run_http` already calls `run_async(...,
sockets=[...])`; add `middleware=[...]` to that **same call**:

```python
# Source: read from .venv/Lib/site-packages/fastmcp/server/mixins/transport.py (run_http_async signature)
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

class SharedSecretMiddleware:
    def __init__(self, app, *, header_name: str, secret: str) -> None:
        self.app, self.header_name, self.secret = app, header_name, secret

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            headers = Request(scope=scope).headers
            if headers.get(self.header_name) != self.secret:
                response = PlainTextResponse("Forbidden", status_code=403)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)

# wired in PeerRuntime._run_http:
await self._mcp.run_async(
    transport="http", host=..., port=..., sockets=[self._listen_socket],
    middleware=[Middleware(SharedSecretMiddleware, header_name=..., secret=...)],
)
```
`PeerRuntime.__init__` needs a new optional constructor param (e.g. `shared_secret:
tuple[str, str] | None`) threaded into `_run_http`, matching the existing
`handshake_handler` injection style.

### Anti-Patterns to Avoid
- **Don't use FastMCP's own `Middleware`/`add_middleware()` (the MCP-protocol-level
  middleware, `fastmcp.server.middleware.Middleware`) for the secret check.** That system
  dispatches on `tools/call`, `resources/read`, etc. — it only sees *valid, already-parsed*
  MCP requests, so a scanner sending garbage or a plain unauthenticated `GET /mcp` would
  still reach the server internals before being rejected. The ASGI `middleware=[...]` list
  on `run_async` is the outer boundary and is the correct seam.
- **Don't enable FastMCP's built-in `host_origin_protection` as a substitute for the
  shared-secret header without also setting `allowed_hosts`.** See Pitfall 2 below — it is
  currently off (`False`) in this codebase and should stay off unless `allowed_hosts` is
  explicitly configured with the ngrok hostname, or every real remote handshake will get a
  `421 Misdirected Request` before the shared secret is even checked.
- **Don't reinvent ngrok's binary lifecycle.** `pyngrok` already exposes `ngrok.connect()`,
  `get_ngrok_process().healthy()`, `ngrok.disconnect()`, `ngrok.kill()` — a hand-rolled
  `subprocess` + `requests.get("http://127.0.0.1:4040/api/tunnels")` poller duplicates this
  for no benefit and is untested-by-upstream on Windows in ways `pyngrok` already is.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Start/track/kill the ngrok agent process, download the right platform binary | `subprocess.Popen` + manual binary download + polling `127.0.0.1:4040/api/tunnels` | `pyngrok` (`ngrok.connect`, `ngrok.get_ngrok_process()`, `ngrok.kill()`) | Binary download, platform detection, process supervision and the local REST client are exactly what `pyngrok` (8.1.2, actively maintained) already does; hand-rolling it duplicates a well-tested wrapper for a Windows target it already supports |
| Attach a header to every outbound FastMCP call | Wrapping/monkeypatching `httpx` at a lower level | `StreamableHttpTransport(url, headers={...})` passed explicitly into `Client(...)` | It's a first-class constructor parameter already; no need to reach below the transport layer |
| Reject unauthenticated HTTP requests before they reach MCP tool dispatch | A custom check inside every `@mcp.tool` handler in `tools.py` | One ASGI `middleware=[Middleware(SharedSecretMiddleware, ...)]` passed to `run_async` | Middleware runs once, for every route, before FastMCP's own session/tool machinery — checking inside each of the five tool handlers means five places to keep in sync and a window where malformed non-tool requests still reach the server |

**Key insight:** every piece of this phase's "new" infrastructure (tunnel process lifecycle,
header injection, header enforcement) already has a first-class seam in either `pyngrok` or
the already-pinned `fastmcp`/`starlette` — the phase is wiring, not new mechanism.

## Common Pitfalls

### Pitfall 1: passing a bare URL string to `fastmcp.Client()` silently drops headers
**What goes wrong:** `Client(url_string)` infers a `StreamableHttpTransport` with
`headers={}` — the shared-secret header never gets sent, and the server-side middleware
rejects every real cross-peer call with 403, even though the URL and secret are both
"correct" in config.
**Why it happens:** `infer_transport()` only builds a bare `StreamableHttpTransport(url=...)`
when given a string; header injection requires constructing the transport object yourself.
**How to avoid:** Always construct `StreamableHttpTransport(url, headers={...})` explicitly
in `PeerRuntime.client()` once the shared-secret header is added; never regress to
`Client(url)`.
**Warning signs:** Every outbound call to the opponent returns 403 while a bare `curl`/manual
request with the header succeeds.

### Pitfall 2: `host_origin_protection` + loopback bind = 421 if ever turned on
**What goes wrong:** `PeerRuntime` binds `host=127.0.0.1` (loopback). FastMCP 3.4.5 ships a
built-in `HostOriginGuardMiddleware` (`fastmcp/server/http.py`), controlled by
`host_origin_protection` (default `False`, confirmed by reading `run_http_async`'s
signature — currently unset anywhere in this codebase, so inactive today). If a future
phase (e.g. Phase 6 hardening) turns this on with `mode="auto"` **without** adding
`allowed_hosts`, its `_should_validate_host()` returns `True` specifically *because* the
server is loopback-bound, and `_allowed_hosts_for_scope()` only allows
`("127.0.0.1", "localhost", "::1")` plus the literal bound host (`"127.0.0.1"`) — the
incoming `Host:` header from a real request through the ngrok tunnel will be the ngrok
hostname (e.g. `foo.ngrok-free.app`), which matches none of those, and the request gets a
`421 Misdirected Request` before the shared-secret middleware even runs.
**Why it happens:** the guard's "auto" mode treats "server is bound to loopback" as the
signal to validate Host, which is true for this project's whole architecture (every peer
binds `127.0.0.1` and is reached from outside only via the tunnel).
**How to avoid:** leave `host_origin_protection` off in this phase (matches current
behavior — no code change needed). If a later phase turns it on, `allowed_hosts` MUST
include both peers' ngrok hostnames (config-sourced, not hardcoded).
**Warning signs:** the real remote round (CLOUD-02) works in a smoke test but a config
change elsewhere in the codebase suddenly makes every remote handshake fail with 421.

### Pitfall 3: pyngrok tunnels do not auto-reconnect
**What goes wrong:** if the local `ngrok` agent process dies (crash, network blip, laptop
sleep) mid-game, `pyngrok` does not restart it or re-establish the tunnel on its own — the
public URL simply stops forwarding.
**Why it happens:** `pyngrok` is a thin wrapper around the `ngrok` binary's own process
lifecycle; it does not implement supervision beyond exposing `get_ngrok_process().healthy()`
for the caller to poll.
**How to avoid:** poll `get_ngrok_process().healthy()` on the same cadence as the existing
freeze watchdog (`watchdog_poll_seconds`), and on failure call `ngrok.connect(port,
domain=static_domain)` again, bounded by the existing `retry_count`/`backoff_seconds`
(Table 19 rows 4/3) — reconnecting to the **same static domain** restores the same public
URL, so the opponent never needs a new URL mid-game.
**Important distinction:** a tunnel drop is NOT the "process freeze" `watchdog.py` (rule 7)
already guards — the local FastMCP server and turn loop keep running; only the external
ingress path is broken. This is a genuinely separate concern belonging to the new
`TunnelManager`, not bolted onto `Watchdog`.
**Correctness note for planners:** reconnecting the tunnel does not retroactively deliver a
request the opponent's client tried to send during the outage — that recovery is the
*opponent's own* `NetworkParams.retry_count`/`backoff_seconds` (Phase 2, already built).
With `response_timeout=30`, `retry_count=3`, `backoff_seconds=5` (current `network.json`
values), the opponent's own call gives up after roughly `3 × (30 + 5) ≈ 105s` — the tunnel's
own liveness-poll-plus-reconnect budget should comfortably fit inside that window so a
same-turn reconnect is invisible to the opponent.
**Warning signs:** opponent reports a single dropped move around the same time the local
machine's network blipped; local logs show a `TunnelManager` reconnect event in that window.

### Pitfall 4: ngrok's free-tier interstitial page (not a blocker here, but add the header anyway)
**What goes wrong:** ngrok serves an HTML "you are about to visit an ngrok tunnel" warning
page to first-time **browser** visitors on the free plan.
**Why it doesn't actually block this project:** the interstitial only triggers for requests
that `Accept: text/html` — MCP's streamable-HTTP client sends `Accept: application/json,
text/event-stream`, never `text/html`, so real peer-to-peer traffic should already bypass it
(MEDIUM confidence — confirmed via multiple independent secondary sources, not ngrok's own
docs page directly, so treat as needing a smoke-test confirmation, not certainty).
**How to avoid any residual risk for free:** send `ngrok-skip-browser-warning: true` as an
extra header alongside the shared secret (see client-side snippet above) — zero cost, and
also makes manual `curl`/browser-based smoke checks against the tunnel URL behave.
**Warning signs:** a manual `curl https://<domain>.ngrok-free.app/mcp` during a smoke test
returns an HTML warning page instead of an MCP error/response.

### Pitfall 5: monthly ngrok quota is a real ceiling across the whole team's testing, not per-game
**What goes wrong:** the free plan caps at 1 GB/month data transfer and 20,000 HTTP
requests/month (official docs, see Sources) — a single 35-turn game's JSON payloads are
tiny and nowhere near this, but repeated practice/smoke-test sessions across a multi-week
project **do** accumulate against the same monthly counters.
**How to avoid:** don't leave the tunnel running idle for long stretches; close it between
test sessions (`TunnelManager.stop()`), and treat the monthly cap as a reason to rehearse
the CLOUD-02 gate procedure locally (loopback) before spending quota on the real remote run.
**Warning signs:** ngrok dashboard usage graph climbing without a clear source — check for
a forgotten `dev_launch.py`-adjacent process left tunneling.

## Code Examples

### pyngrok: claim/read the static domain, start, verify liveness, stop
```python
# Source: https://pyngrok.readthedocs.io/en/latest/ (connect/get_tunnels/kill) +
# https://github.com/alexdlaird/pyngrok (domain= kwarg, confirmed against v3 agent usage)
import os
from pyngrok import ngrok

def start_tunnel(port: int, domain: str) -> str:
    # NGROK_AUTHTOKEN read automatically from the environment if set;
    # ngrok.set_auth_token(...) is the explicit alternative.
    tunnel = ngrok.connect(port, domain=domain)   # e.g. domain="myteam-cop.ngrok-free.app"
    return tunnel.public_url                       # "https://myteam-cop.ngrok-free.app"

def tunnel_is_healthy() -> bool:
    return ngrok.get_ngrok_process().healthy()

def stop_tunnel(public_url: str) -> None:
    ngrok.disconnect(public_url)
    ngrok.kill()
```

### Localtonet: CLI-only fallback (documentation, not code)
```
localtonet --authtoken <TOKEN>
# then configure the HTTP tunnel (IP 127.0.0.1, port <agent port>) via the web dashboard
# or the --install-service / --start-service flags for a persistent Windows service
```
(No Python integration in this phase — see Localtonet section below.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| ngrok v2 random 8-hour URLs (`ngrok.connect(subdomain=..., region=...)` → `*.ngrok.io`) | ngrok v3 free "assigned dev domain" / claimed static domain (`--domain=name.ngrok-free.app`), persists indefinitely | ngrok's 2023 "static domains for all users" change (blog: `ngrok.com/blog/free-static-domains-ngrok-users`) | The CONTEXT.md assumption ("static domain survives restarts") is correct and current — confirmed against `ngrok.com/docs/pricing-limits/free-plan-limits` today |

**Deprecated/outdated:** old pyngrok/ngrok-v2-era examples using `subdomain=` and
`region=` kwargs (`*.au.ngrok.io`-style URLs) are stale; use `domain=` with a full
`*.ngrok-free.app` hostname claimed from the dashboard instead.

## Open Questions

1. **Is there really a Feb-2026 free-tier restriction to 2-hour sessions / forced random
   URLs?**
   - What we know: ngrok's own current docs page (`ngrok.com/docs/pricing-limits/
     free-plan-limits`, fetched today) states no session timeout ("endpoints remain online
     indefinitely") and confirms "1 automatically assigned dev domain" — directly
     contradicting third-party claims of a 2-hour cap and forced random URLs found via
     WebSearch.
   - What's unclear: those contradicting claims trace to a competing tunneling service's
     own marketing blog (`instatunnel.*`), not an ngrok source — LOW confidence, likely
     competitor FUD, but ngrok pricing pages are known to change without much notice.
   - Recommendation: trust the official docs (HIGH confidence, fetched live) for planning,
     but have whoever claims the static domain double-check the live dashboard/plan page
     immediately before league day, since this is a free-tier product whose terms can shift.

2. **Does the MCP streamable-HTTP client truly never trigger ngrok's browser interstitial?**
   - What we know: the interstitial is documented (by secondary sources, not ngrok's own
     docs directly) to trigger only on `Accept: text/html` browser requests; MCP's client
     sends `Accept: application/json, text/event-stream`.
   - What's unclear: not verified against ngrok's own docs directly, and ngrok's exact
     detection heuristic (Accept header vs. User-Agent sniffing) wasn't found in a primary
     source.
   - Recommendation: send `ngrok-skip-browser-warning: true` defensively (zero cost, same
     headers dict as the shared secret) and confirm during the smoke-test step of the gate
     script rather than relying on the interstitial never appearing.

3. **Exact pyngrok Windows binary storage path / firewall prompt behavior on first run.**
   - What we know: `pyngrok` stores its config at `%HOMEPATH%\AppData\Local\ngrok\ngrok.yml`
     on Windows (secondary source) and downloads the `ngrok.exe` binary itself on first use;
     Windows Defender Firewall may prompt to allow network access the first time `ngrok.exe`
     runs (normal for any new listening/outbound process, not ngrok-specific).
   - What's unclear: not verified against pyngrok's own official docs page directly (that
     fetch didn't surface the exact path).
   - Recommendation: treat as a non-blocking smoke-test observation — the plan's smoke-test
     step (same-machine-via-public-URL, per CONTEXT.md) will surface any firewall prompt
     immediately, cheaply, before the real remote round.

## Localtonet (documented fallback — not integrated in code)

Per CONTEXT.md, Localtonet is the fallback named to satisfy rule 10 ("MUST use a tunneling
tool... either is compliant") — it does not need a `TunnelManager`-equivalent Python
integration in this phase; a short runbook satisfies the requirement without doubling the
engineering surface for a path that's "documented," not "built."

**Free plan (from `localtonet.com`, MEDIUM confidence — official site, not a docs-specific
page):**
- 1 HTTP/TCP/UDP tunnel
- 1 GB bandwidth/month
- **30-minute tunnel timeout** — materially worse than ngrok's free plan (no documented
  timeout); a real constraint if this ever became primary
- Random subdomain by default; custom/static domains are a paid-plan feature
- Auth: `localtonet --authtoken <TOKEN>` (or interactive prompt on first Windows run);
  `--install-service --authtoken <TOKEN>` / `--start-service` for a persistent Windows
  service
- Port-to-URL mapping is configured via the web dashboard, not purely CLI-driven — less
  scriptable than ngrok's `domain=` kwarg

**Recommended runbook content for the plan:** install steps (exe or Microsoft Store),
`--authtoken` setup, dashboard port mapping to `127.0.0.1:<agent port>`, and a note that the
30-minute timeout means a fallback session must be restarted (`localtonet --start-service`
survives reboots but the free-tier tunnel itself still needs re-establishing per that
window) if used on league day.

## Testing Strategy (structural recommendation)

**Unit tests (fully mocked, no network, no real `ngrok.exe`):**
- Mock boundary = the `pyngrok.ngrok` module-level functions themselves (`connect`,
  `disconnect`, `kill`, `get_ngrok_process`), injected into `TunnelManager` as callables —
  same DI pattern as `Gatekeeper`'s `clock`/`sleep` and `Watchdog`'s
  `clock`/`sleeper`/`exit_action` (both already in this codebase).
- Fake `connect` returns a simple object/dataclass with `.public_url` — assert
  `TunnelManager.start()` reads and stores it, `TunnelManager.stop()` calls
  `disconnect`+`kill` in order, and reconnect-on-drop logic (fake `healthy()` flipping
  False) retries the configured number of times with the configured backoff before giving
  up, using an injected fake `sleep` (never a real wait in tests).
- Config loader tests for `load_tunnel_config()` follow the exact shape of
  `tests/unit/test_network_config.py` (missing-key → `KeyError`, wrong-type → `TypeError`,
  env-var override behavior if added).
- Middleware tests: build a FastMCP `http_app()` (or drive `run_async` in-process) with the
  `SharedSecretMiddleware` attached and hit it via `httpx.ASGITransport`/Starlette
  `TestClient` — no real socket, no real ngrok — asserting a 403 without the header and
  success with it. Same in-process pattern already implied by `tools.py`'s own design
  (tools are tested via `Client(FastMCP_instance)` in-memory transport per the existing
  `PeerRuntime.server` accessor).
- Client-header test: construct `PeerRuntime.client()` and assert the returned `Client`'s
  underlying transport carries the expected headers (no network call needed — inspect the
  `StreamableHttpTransport.headers` attribute directly).

**Integration test (still no real internet, matches the `tests/integration/test_gate4.py`
precedent):** two in-process/loopback `PeerRuntime`s with the middleware attached, one
`Client` with the correct header (succeeds) and one without (403) — proves the wiring
end-to-end without needing `ngrok.exe` or a real account.

**The one manual gate-run script** (mirrors the Phase-4 precedent: `scripts/gate4_*.py` +
`docs/phases/phase-4/GATE-4-MEASUREMENT.md` + `gate4_measurement_live.json`) — recommend
`scripts/gate5_tunnel_smoke.py` (same-machine-via-public-URL smoke check, automatable) and
a `docs/phases/phase-5/GATE-5-MEASUREMENT.md` capturing the **genuine remote round**
(CLOUD-02) evidence, since that step inherently needs a second machine/network and cannot
be scripted end-to-end from this repo alone. The smoke script should assert: tunnel process
starts, `public_url` matches an `https://` pattern, a real HTTP round-trip through the
public URL reaches the local FastMCP `/mcp` route and returns a valid MCP response, and a
request missing the shared-secret header is rejected (403) through the tunnel, not just
locally.

## Sources

### Primary (HIGH confidence)
- `.venv/Lib/site-packages/fastmcp/` (installed 3.4.5 source, read directly): `client/
  transports/http.py`, `client/transports/inference.py`, `client/client.py` (`Client.
  __init__` signature via `inspect`), `server/http.py` (`HostOriginGuardMiddleware`,
  `DEFAULT_HOSTS`, `host_origin_protection` default), `server/mixins/transport.py`
  (`run_http_async` signature, `middleware: list[ASGIMiddleware]`)
- `https://pypi.org/pypi/ngrok/json` and `https://pypi.org/pypi/pyngrok/json` — exact
  `requires_python` and available wheel filenames for both packages
- `https://ngrok.com/docs/pricing-limits/free-plan-limits` — free-plan quotas (1GB/mo,
  20k requests/mo, 5k TCP/mo, 4000 req/min, 1 dev domain, no session timeout)
- Project source: `src/pursuit/network/peer_runtime.py`, `agent_lifecycle.py`,
  `agent_wiring.py`, `tools.py`, `handshake.py`, `watchdog.py`,
  `src/pursuit/shared/network_config.py`, `src/pursuit/shared/loader_helpers.py`,
  `src/pursuit/config_keys.py`, `src/pursuit/main.py`, `scripts/dev_launch.py`,
  `docs/PARAMETERS.md` (Table 19), `docs/RULES.md` (rule 10), `docs/TODO.md` (05-01/05-02)

### Secondary (MEDIUM confidence)
- `https://github.com/alexdlaird/pyngrok` (README, `domain=` kwarg for v3 static/reserved
  domains)
- `https://pyngrok.readthedocs.io/en/latest/` (API surface: `connect`, `get_tunnels`,
  `get_ngrok_process().healthy()`, `disconnect`, `kill`, `PyngrokConfig`)
- `https://ngrok.com/docs/getting-started/python` (official `ngrok-python` quickstart —
  confirms the SDK's shape even though it's not the recommended package here)
- `https://localtonet.com/` and CLI-flag search results (`--authtoken`,
  `--install-service`) for the fallback runbook
- Multiple independent secondary sources on the `ngrok-skip-browser-warning` header
  behavior (GitHub PRs/issues, blog posts) — consistent with each other but not
  cross-checked against an ngrok first-party docs page directly

### Tertiary (LOW confidence — flagged, not relied on)
- `instatunnel.*` blog posts claiming a Feb-2026 "2-hour session cap / forced random URLs"
  on ngrok's free plan — a competing product's marketing content, directly contradicted by
  ngrok's own current docs (see Open Question 1); do not plan around this claim, but verify
  the live dashboard once before league day

## Metadata

**Confidence breakdown:**
- Standard stack (pyngrok vs ngrok-python): HIGH — decided by a verifiable, hard
  `requires_python` incompatibility (PyPI JSON API), not preference
- Architecture (client header seam, server middleware seam, config-loader pattern): HIGH —
  read directly from installed fastmcp source and existing project source
- ngrok free-tier limits: HIGH (official docs page, fetched live) with one explicitly
  flagged LOW-confidence contradicting claim
- Localtonet: MEDIUM — official site + CLI search, not an exhaustive docs crawl (matches
  its "documented fallback only" scope)
- Reconnect/retry UX: MEDIUM — no official "recommended pattern" doc for this; recommendation
  is derived from `pyngrok`'s actual API surface plus this project's own existing
  retry/backoff/watchdog conventions

**Research date:** 2026-08-09
**Valid until:** ~30 days for the fastmcp/pyngrok API surface (stable, pinned versions);
~7-14 days for ngrok's free-plan terms specifically (see Open Question 1) — re-check the
live pricing/limits page shortly before claiming the static domain and again shortly before
league day.
