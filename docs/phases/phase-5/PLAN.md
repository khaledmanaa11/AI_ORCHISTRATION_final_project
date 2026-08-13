# Phase 5 PLAN — Cloud Exposure and Tunneling

**Version:** 1.01 · **Status:** ◐ approved · **Updated:** 2026-08-13 (gap-closure set 05-04..05-08 added)

> How Phase 5 is built. The authoritative plan set lives in
> `.planning/phases/05-cloud-exposure-and-tunneling/` (outline + 05-01…05-03, plus the
> gap-closure set 05-04…05-08); this file is the grader-facing map of it.

## Components

| Component | Files | Plan |
|---|---|---|
| Tunnel lifecycle | `network/tunnel_manager.py`, `shared/tunnel_config.py`, `config/{police,thief}/tunnel.json`, `agent_lifecycle.py` wiring | 05-01 |
| Shared-secret channel | `network/secret_guard.py` (ASGI middleware), `peer_runtime.py` (middleware + explicit client transport), `.env-example` | 05-02 |
| Gate 5 evidence | `scripts/gate5_tunnel_smoke.py`, `docs/phases/phase-5/GATE-5-MEASUREMENT.md`, `LOCALTONET-FALLBACK.md` | 05-03 |
| Verdict honesty + teardown grace | `network/agent_teardown.py` (new), `agent_audit_wiring.py`, `agent_audit_verdict.py`, `agent_entrypoint.py`, `agent_lifecycle.py`, `event_log.py` | 05-04 |
| One negotiated game id | `network/game_identity.py` (new), `agent_wiring.py`, `agent_context.py`, `agent_lifecycle.py`, `agent_entrypoint.py`, `security/audit.py` | 05-05 |
| Hint channel: logged and delivering | `network/turn_hint_buffer.py` (new), `turn_buffer.py`, `turn_actions.py` | 05-06 |
| LLM legibility | `services/llm/client.py`, `bluff.py`, `bluff_prompt.py`, `network/language_wiring.py`, `agent_audit_wiring.py` | 05-07 |
| Remote round attempt 2 | `docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md`, `GATE-5-MEASUREMENT.md`, `remote-round-2026-08-14/` | 05-08 |

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

Gap closure, after the 2026-08-13 remote round (attempt 1) exposed five gaps. Every arrow is
a genuine shared-file or correctness dependency; wave 2's two plans are file-disjoint from
each other and run in parallel:

```
w1: 05-04  (G1 — verdict honesty wired into run_agent, linger, NET-07, sequenced proof)
      |
      |  05-05 shares agent_entrypoint.py + agent_audit_wiring.py
      |  05-06 IMPORTS tests/integration/test_step0_and_audit.py, which 05-04 edits
      |
w2: 05-05  (G2 — negotiated game id + audit state validation)   05-06  (G3+G4 — hint log,
      |                                                                    delivery, no
      |  shares agent_audit_wiring.py                                      terminal hint)
w3: 05-07  (G5 — LLM legibility)
      |
w4: 05-08  (remote round attempt 2 — HUMAN-RUN, blocking checkpoint)
```

Two orderings inside that graph are correctness-critical, not conveniences, and are enforced
as task dependencies inside their plans:

- **05-05** — the audit-side validation of the peer's committed `state.game_id`/`role` must
  land in the same plan as, and never before, the negotiated-id adoption. Shipped alone it
  turns every honest remote round into a mutual TECHNICAL_LOSS, because the two sides commit
  different game ids today.
- **05-06** — relaxing the receive-side hint drop window and fixing the responder's outgoing
  stamp must land together, in one commit. The stamp fix alone takes a round from 3-of-10
  decodes to 0-of-10.


## Test plan

- All pytest suites stay offline; the tunnel and pyngrok are faked at the injected-callable
  boundary. Loopback integration proves the secret channel end-to-end.
- The only network-touching artifact is the manual smoke script (human-run, env-gated).
- Existing Phase 2–4 tests pass unmodified: tunnel-off and secret-off are the defaults.

## Phase ADRs

Gap-closure decisions (05-04..05-08), recorded here because they are new to this phase:
the post-audit grace window reuses `NetworkParams.response_timeout` (Table 19 row 6) as its
total cap and `backoff_seconds` (row 3) as its quiet interval — `watchdog_threshold` is
deliberately NOT used, since it answers "has this process stopped making progress", a
different question; a failed OWN final-reveal send becomes non-accusatory evidence while a
genuine hash mismatch and a genuinely withholding peer both still lose (rules 16/22, rule 36);
the peer's committed `state.game_id` is validated only when the handshake actually negotiated
one, so a league opponent that publishes none is never accused; the hint lookback window is a
named structural constant, not a config key (CLAUDE.md rule 1).

D-54 (pyngrok, not ngrok-python — Python 3.11 floor) · D-55 (zero new numbers — Table 19 +
D-18 reuse) · D-56 (ASGI-boundary enforcement + explicit client transport) · D-57
(host_origin_protection stays off; Localtonet documentation-only). Authoritative text:
[05-PLAN-OUTLINE.md §1](../../../.planning/phases/05-cloud-exposure-and-tunneling/05-PLAN-OUTLINE.md).

## Risks

- ngrok free-tier terms can shift (flagged in research): re-verify the dashboard before
  claiming the domain and before league day.
- Monthly quota (1 GB / 20k requests) is shared across all testing — close tunnels between
  sessions; rehearse the gate loopback-first.
- The remote round needs a second machine/network — attempt 1 ran 2026-08-13 and did not
  close the criterion; attempt 2 (05-08) is the phase's remaining human item.
- Three plans touch `agent_audit_wiring.py` (102 code lines at HEAD) and two touch
  `agent_entrypoint.py`; `agent_wiring.py` sits at 148/150, `turn_buffer.py` at 146 and
  `turn_actions.py` at 143. Each plan re-measures with `scripts/check_line_limit.sh` and
  splits a sibling where a fix does not fit — never compresses code to fit.
- 05-04/05-05 touch commit-reveal and audit code while GATE-6's three criteria all PASS.
  Both re-run `scripts/measure_gate6.py` and require all three to still PASS.
