# Phase 5: Cloud Exposure and Tunneling - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 exposes each peer's FastMCP HTTP server to the public internet through a tunnel
and proves it: a remote agent connects through the tunnel and plays a **full round**
against the local agent (CLOUD-01, CLOUD-02). The transport does not change — Phase 2
chose streamable HTTP so this phase only adds the tunnel and URL wiring.

Out of scope: crypto/auth protocol (Phase 6 — but see interim protection below),
reporting (Phase 7).

**Planning-day note:** refresh the graph (`/gsd:graphify`) before
`/gsd:plan-phase 5 --chunked` (task 05-96).

</domain>

<decisions>
## Implementation Decisions

### Tunnel
- **Primary provider: ngrok** — free-tier static domain (URL survives restarts — matters
  on league day), solid Windows support, auth token via env var (`NGROK_AUTHTOKEN`,
  never in source). **Localtonet documented as the fallback** (both are named by rule
  10, so either is compliant).
- **Launcher-managed lifecycle**: agent startup can launch the tunnel (ngrok Python
  SDK/API), read the assigned public URL, print it for sharing with the opponent team,
  and verify liveness. The opponent's URL is pasted into the per-agent config — the
  Phase-2 endpoint seam, unchanged.

### Validation (Stage-5 gate)
- **Genuine remote round**: one agent runs on a different machine/network (friend's
  laptop, phone hotspot, university PC) against the tunnel URL — a full round, exactly
  what the gate demands. Same-machine-via-public-URL is acceptable only as a smoke test
  before the real one.

### Interim protection
- **Shared-secret header** until Phase 6: a token (env var, exchanged with the opponent
  team alongside the URL) checked on every request — keeps internet scanners off the
  exposed MCP tools. Phase 6's commit-reveal layers on top; this header stays as
  transport-level hygiene.

### Claude's Discretion
- ngrok SDK vs subprocess management; reconnect/retry behavior on tunnel drop
- How the printed URL/token exchange is formatted for the opponent team
- Test structure (tunnel mocked in unit tests; real tunnel only in the manual gate run)

</decisions>

<specifics>
## Specific Ideas

- League-day flow to preserve: start agent → tunnel up → static URL + secret shared with
  opponent → opponent pastes into their config → handshake (config hash + scent lock)
  → play.
- ngrok free-tier static domain should be claimed early (one-time setup) so the URL in
  shared configs never churns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-cloud-exposure-and-tunneling*
*Context gathered: 2026-07-28*
