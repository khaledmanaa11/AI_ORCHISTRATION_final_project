# Phase 5 Plan Outline — Cloud Exposure and Tunneling

**Phase:** `05-cloud-exposure-and-tunneling` · **Written:** 2026-08-09 · **Plans:** 05-01 … 05-03
**Context:** [`05-CONTEXT.md`](05-CONTEXT.md) · **Research:** [`05-RESEARCH.md`](05-RESEARCH.md)
**Requirements:** CLOUD-01, CLOUD-02
**Gate:** §10.4 milestone 5 — *each peer is reachable on the public internet through
ngrok/Localtonet; an agent on a remote machine connects through the tunnel and plays a full
round against the local agent.*

**All plans are subject to the standing gates, not restated per plan:** `ruff check` → 0 ·
`pytest --cov` ≥ 85% · every file ≤ 150 code lines · `uv` only · zero invented numbers ·
zero secrets in source · tests offline (no real tunnel, no real network).

This phase is **wiring, not mechanism**: the Phase-2 transport does not change. Research
confirmed every needed seam already exists — `pyngrok` for the tunnel lifecycle,
`run_async(middleware=[...])` for the server-side check, an explicit
`StreamableHttpTransport(url, headers=...)` for the client side.

## 1. Decisions — D-54 … D-57

D-54 … D-57 are new this phase, resolved from `05-RESEARCH.md` under the autonomy directive.
The CONTEXT decisions (ngrok primary + static domain, launcher-managed lifecycle, genuine
remote round, shared-secret header) are locked and not re-derived.

| ID | Decision | Source |
|----|----------|--------|
| **D-54** | **`pyngrok`, not the official `ngrok-python` SDK.** `ngrok-python` 1.7.0 requires Python ≥3.12; this project runs 3.11.9 — `uv add ngrok` would fail outright (verified via PyPI JSON API). `pyngrok` (≥3.9) wraps the real `ngrok.exe`, manages the binary itself, and exposes `connect / get_ngrok_process().healthy() / disconnect / kill` — injectable as fakes, the same DI style as `Gatekeeper` and `Watchdog` | RESEARCH §Standard Stack |
| **D-55** | **Zero new numeric parameters.** Tunnel reconnect reuses `network.json`'s existing `retry_count` / `backoff_seconds` (Table 19) and the liveness poll reuses the `watchdog_poll_seconds` D-18 precedent. `tunnel.json` carries only structural values: provider, header name, domain env-var name | RESEARCH §Summary; CLAUDE.md rule 1 |
| **D-56** | **The secret is enforced at the ASGI boundary, injected at the transport constructor.** Server: one `SharedSecretMiddleware` in `run_async(middleware=[...])` — a request missing the header never reaches MCP routing. Client: explicit `StreamableHttpTransport(url, headers={...})` — a bare `Client(url)` silently drops headers (verified in fastmcp 3.4.5 source). Secret value from `PURSUIT_TUNNEL_SECRET` env only; header **name** from config | RESEARCH §Architecture |
| **D-57** | **`host_origin_protection` stays off, and Localtonet stays documentation-only.** FastMCP's built-in host guard in `mode="auto"` would 421-reject every tunneled request (loopback bind + ngrok Host header); it is off today and this phase documents why it must stay off or gain `allowed_hosts`. Localtonet (30-min free-tier timeout, dashboard-driven) is a runbook, not code — rule 10 names both providers, so documenting the fallback satisfies compliance without doubling the surface | RESEARCH §Pitfalls 2, §Localtonet |

**Not in scope:** commit-reveal/nonce/Step-0 (Phase 6 — the shared-secret header is interim
hygiene that stays underneath it), Gmail/GUI (Phase 7), any change to envelope shapes or the
handshake beyond what Phase 4 shipped.

## 2. Numbers — all reused, none invented

| Value | Number | Status | Source |
|---|---|---|---|
| Reconnect retries | `retry_count` = 3 | reused | PARAMETERS Table 19 (already in `network.json`) |
| Reconnect backoff | `backoff_seconds` = 5 | reused | Table 19 (already in `network.json`) |
| Liveness poll cadence | `watchdog_poll_seconds` = 1 | reused | D-18 engineering default (already in `network.json`) |
| Opponent's give-up window | ≈ 3 × (30 + 5) ≈ 105 s | derived | Table 19 values already shipped — reconnect must fit inside it |

`tunnel.json` introduces **no number**. Every new key is a string (provider, header name,
env-var names).

## 3. Where the code goes

```
src/pursuit/network/
  tunnel_manager.py        TunnelManager: start / public_url / healthy / reconnect / stop   (05-01)
  secret_guard.py          SharedSecretMiddleware (ASGI)                                    (05-02)
  peer_runtime.py          + middleware=[...] on run_async; client() builds explicit
                           StreamableHttpTransport with headers                             (05-02)
  agent_lifecycle.py       tunnel start before runtime, stop in the same finally            (05-01)

src/pursuit/shared/
  tunnel_config.py         load_tunnel_config + TunnelKey (enum beside loader,
                           the Phase-4 convention all four language-era loaders follow)     (05-01)

config/{police,thief}/
  tunnel.json              provider, header name, env-var names — byte-identical pair       (05-01)

scripts/
  gate5_tunnel_smoke.py    same-machine-via-public-URL smoke check                          (05-03)

docs/phases/phase-5/
  GATE-5-MEASUREMENT.md    smoke numbers + the genuine remote round (human evidence)        (05-03)
  LOCALTONET-FALLBACK.md   the rule-10 fallback runbook                                     (05-03)
```

## 4. Plans and waves

| Plan | Delivers | Wave | Depends on |
|---|---|---|---|
| **05-01** | Tunnel lifecycle — `pyngrok` dep, `tunnel.json` + loader, `TunnelManager` (DI'd, reconnect bounded by Table 19), lifecycle wiring, URL/secret exchange printout | 1 | — |
| **05-02** | Shared-secret channel — ASGI middleware, client transport headers, env plumbing, `.env-example` | 2 | 05-01 |
| **05-03** | Gate 5 — smoke script, in-process integration proof, `GATE-5-MEASUREMENT.md`, Localtonet runbook, graph refresh (05-96) | 3 | 05-01, 05-02 |

05-02 depends on 05-01 because the header **name** lives in `tunnel.json` (one config owner,
the Phase-4 pattern). 05-03 needs both, plus twelve turns of everything else already working.

The genuine remote round (CLOUD-02) inherently needs a second machine and a human — 05-03
builds and runs everything scriptable (the smoke path), and records the remote round as the
phase's single human-pending item, exactly the GATE-4 live-run precedent.

## 5. Decision → plan coverage

| Plan | Owns |
|---|---|
| 05-01 | D-54, D-55 |
| 05-02 | D-56 |
| 05-03 | D-57 (+ the CLOUD-02 evidence) |

## 6. Requirement coverage

| REQ | Landed by |
|---|---|
| CLOUD-01 each peer reachable through ngrok/Localtonet | 05-01, 05-02 |
| CLOUD-02 remote agent plays a full round through the tunnel | 05-03 (smoke scripted; remote round human-evidenced) |
