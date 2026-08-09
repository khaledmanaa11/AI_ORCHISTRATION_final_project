# Phase 5 PLAN — Cloud Exposure and Tunneling

**Version:** 1.00 · **Status:** ◐ approved · **Updated:** 2026-08-09

> How Phase 5 is built. The authoritative plan set lives in
> `.planning/phases/05-cloud-exposure-and-tunneling/` (outline + 05-01…05-03); this file is
> the grader-facing map of it.

## Components

| Component | Files | Plan |
|---|---|---|
| Tunnel lifecycle | `network/tunnel_manager.py`, `shared/tunnel_config.py`, `config/{police,thief}/tunnel.json`, `agent_lifecycle.py` wiring | 05-01 |
| Shared-secret channel | `network/secret_guard.py` (ASGI middleware), `peer_runtime.py` (middleware + explicit client transport), `.env-example` | 05-02 |
| Gate 5 evidence | `scripts/gate5_tunnel_smoke.py`, `docs/phases/phase-5/GATE-5-MEASUREMENT.md`, `LOCALTONET-FALLBACK.md` | 05-03 |

## Interfaces

- `TunnelManager(params, network_params, *, connect, disconnect, kill, get_process, sleep,
  clock)` — every pyngrok call injected (Gatekeeper/Watchdog DI house style). `start() →
  public_url`, `healthy()`, `ensure_connected()` (bounded by Table 19 `retry_count` /
  `backoff_seconds`, same static domain), `stop()`.
- `SharedSecretMiddleware` — pure ASGI; 403 before MCP routing on missing/mismatched header;
  `secrets.compare_digest`; attached via `run_async(middleware=[...])` only when the secret
  env var is set.
- Client side: `StreamableHttpTransport(opponent_url, headers={secret, ngrok-skip-browser-warning})`
  built explicitly in `PeerRuntime.client()` — a bare `Client(url)` drops headers (fastmcp
  3.4.5, verified in research).

## Wave graph

```
w1: 05-01  (tunnel lifecycle)
      |
w2: 05-02  (secret channel — header name lives in 05-01's tunnel.json)
      |
w3: 05-03  (gate evidence + runbook + graph refresh)
```

## Test plan

- All pytest suites stay offline; the tunnel and pyngrok are faked at the injected-callable
  boundary. Loopback integration proves the secret channel end-to-end.
- The only network-touching artifact is the manual smoke script (human-run, env-gated).
- Existing Phase 2–4 tests pass unmodified: tunnel-off and secret-off are the defaults.

## Phase ADRs

D-54 (pyngrok, not ngrok-python — Python 3.11 floor) · D-55 (zero new numbers — Table 19 +
D-18 reuse) · D-56 (ASGI-boundary enforcement + explicit client transport) · D-57
(host_origin_protection stays off; Localtonet documentation-only). Authoritative text:
[05-PLAN-OUTLINE.md §1](../../../.planning/phases/05-cloud-exposure-and-tunneling/05-PLAN-OUTLINE.md).

## Risks

- ngrok free-tier terms can shift (flagged in research): re-verify the dashboard before
  claiming the domain and before league day.
- Monthly quota (1 GB / 20k requests) is shared across all testing — close tunnels between
  sessions; rehearse the gate loopback-first.
- The remote round needs a second machine/network — scheduled as the phase's human item.
