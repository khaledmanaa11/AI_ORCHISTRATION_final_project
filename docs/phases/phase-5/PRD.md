# Phase 5 PRD — Cloud Exposure and Tunneling

**Version:** 1.00 · **Status:** ◐ approved · **Updated:** 2026-08-09

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); do not restate it — capture
> only what is specific to this phase. Numbers come from [PARAMETERS.md](../../PARAMETERS.md).

## Goal
Expose the local FastMCP server publicly via ngrok or Localtonet (ROADMAP Phase 5).

## Requirements covered
- **CLOUD-01** — each peer reachable on the public internet through ngrok/Localtonet.
- **CLOUD-02** — an agent on a remote machine connects through the tunnel and plays a full
  round against the local agent.

## Acceptance criteria (= §10.4 milestone gate)
1. Each peer is reachable on the public internet through ngrok/Localtonet.
2. An agent on a remote machine connects through the tunnel and plays a full round against
   the local agent. *(Inherently needs a second machine + human — recorded as the phase's
   human-pending evidence item in
   [GATE-5-MEASUREMENT.md](GATE-5-MEASUREMENT.md) once 05-03 creates it.)*

## In scope / Out of scope (this phase)
- **In:** launcher-managed ngrok tunnel (`pyngrok`, free-tier static domain), a tenth config
  block `tunnel.json`, reconnect-to-same-domain on drop, shared-secret request header
  (interim protection), the smoke script and the remote-round procedure, the Localtonet
  fallback runbook (rule 10).
- **Out:** commit-reveal / nonce / Step-0 (Phase 6 — layers on top of the header),
  Gmail/GUI (Phase 7), any change to the Phase-2 transport, envelopes, or handshake shapes.

## Dependencies
- Depends on: Phase 4 (language-and-scent) — complete; live GATE-4 API run pending a key.
- External: `pyngrok` (new, D-54), ngrok free-tier account + claimed static domain,
  `NGROK_AUTHTOKEN` / `PURSUIT_NGROK_DOMAIN` / `PURSUIT_TUNNEL_SECRET` env vars.

## Success metrics & test scenarios
- Unit: TunnelManager lifecycle fully faked (start/URL/reconnect-bounded/stop), config
  loader fail-loud, middleware 403/pass, client transport carries headers.
- Integration (offline): two loopback peers with the secret channel active — correct secret
  plays, missing/wrong secret dies at the boundary with 403.
- Manual: `scripts/gate5_tunnel_smoke.py` (needs the env vars) produces JSON evidence for
  criterion 1; the documented remote-round procedure produces criterion 2's evidence.
- Standing gates: ruff 0 · coverage ≥85% · files ≤150 code lines · no secrets · no invented
  numbers (D-55: tunnel reconnect reuses Table 19 + D-18 values).

## Design decisions (phase ADRs)
D-54…D-57 — recorded authoritatively in
[05-PLAN-OUTLINE.md §1](../../../.planning/phases/05-cloud-exposure-and-tunneling/05-PLAN-OUTLINE.md).
