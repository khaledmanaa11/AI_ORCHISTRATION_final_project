# Phase 5 PLAN — Cloud Exposure and Tunneling

**Version:** 1.02 · **Status:** ◐ approved · **Updated:** 2026-08-16 (GATE-5 met; second
gap-closure set 05-12..05-15 added from the verify-work Round 2 audit)

> How Phase 5 is built. The authoritative plan set lives in
> `.planning/phases/05-cloud-exposure-and-tunneling/` (outline + 05-01…05-03, the first
> gap-closure set 05-04…05-11, and the second set 05-12…05-15); this file is the
> grader-facing map of it.
>
> **Gate status:** both §10.4 criteria PASS — criterion 1 by the 2026-08-09 smoke, criterion
> 2 by remote-round attempt 4 (2026-08-16). The 05-12…05-15 set does **not** reopen the gate;
> it closes five defects (G6–G10) found by an adversarial audit run *after* closure, three of
> them league-day blockers. See `.planning/.../05-UAT.md` Round 2.

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
| Remote round (attempts 2–4) | `docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md`, `GATE-5-MEASUREMENT.md`, `remote-round-2026-08-16-attempt{3,4}/` | 05-08 |
| Transport-failure containment | `network/deadline.py`, `deadline_status.py` | 05-09 |
| Peer-data boundary (6 instances) | `security/audit.py`, `audit_shape.py`, `audit_record.py`, `handshake_step0.py` | 05-10 |
| Tunnel watch | `network/tunnel_wiring.py`, `tunnel_manager.py` | 05-11 |
| **Peer input cannot kill us (G7+G9)** | `network/config_hash.py`, `game_identity.py`, `security/audit.py` | **05-12** |
| **Audit survives to be honest (G6)** | `network/agent_audit_exchange.py`, `agent_audit_wiring.py` | **05-13** |
| **Hint channel correct everywhere (G8)** | `network/turn_hint_buffer.py`, `turn_actions.py`, `docs/PARAMETERS.md` | **05-14** |
| **Declaration story settled (G10)** | `strategy/deception.py`, `services/llm/hintbank_templates.py`, `docs/PRD_mcp_transport.md` | **05-15** |

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

### Second gap-closure set (05-12..05-15) — after the verify-work Round 2 audit, 2026-08-16

Fully **sequential**, one plan per wave. The files are largely disjoint, but this repo has
one git index and a whole-tree pre-commit hook, so parallel executors mix each other's
commits and block each other — waves here buy nothing and cost correctness.

```
w4: 05-12  (G9+G7 — a malformed peer cannot kill us at the handshake)   BLOCKER
      |
      |  05-13 asserts on the audit path 05-12 leaves reachable
w5: 05-13  (G6 — the audit touches the watchdog, both legs stop accusing)  BLOCKER
      |
w6: 05-14  (G8 — single-decode guarantee, both-branch stamping)
      |
w7: 05-15  (G10 — dead declaration code removed, docs corrected, capture Claim de-risked)
```

Fix order is by blast radius, not by severity label: **05-12 first** because until it lands
any opponent — hostile or merely differently-implemented — can end our game before move 1,
which makes every later fix unobservable in a real round.

One ordering here is correctness-critical:

- **05-12** — the peer-id validation must be SAFETY-only (type, non-empty, no path
  separator, bounded length) and must never enforce our id *convention*. A regex demanding
  16 hex characters would reject an honest league opponent using UUIDs and convert it into a
  self-inflicted rules-16/22 loss — the same trap 05-10 avoided when it refused
  `isinstance(turn, int)` for the peer's turn field.

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

Second-set decisions (05-12..05-15), from the verify-work Round 2 audit:
peer-supplied values are validated for **safety only, never for conformance to our
conventions** — an honest opponent with a different id vocabulary must still be matched
(rules 16/22), which is why 05-12 rejects only non-str / empty / path-bearing / over-long
ids and leaves D-61's membership-not-equality audit check exactly as specified; the audit
path **touches the watchdog per bounded attempt** rather than stopping the watchdog, so
NET-07 freeze detection is preserved instead of traded away; `digests_match` keeps its
strict raising contract for internal callers while the containment lands one level up in
`compare_named_digest`, mirroring the `None` branch it already has; and the rules-15/16
question is **settled, not deferred** — the barrier is declared inside the committed action
per `PRD_commit_reveal.md` §2.2 (D-66/SEC-07) and rule 15's sanction is audit-shaped, so
`declare_truthfully` is dead code rather than a missing feature, with the only genuine
residual being the *capture* Claim, de-risked using the `GAME_OVER` envelope that already
exists.

D-54 (pyngrok, not ngrok-python — Python 3.11 floor) · D-55 (zero new numbers — Table 19 +
D-18 reuse) · D-56 (ASGI-boundary enforcement + explicit client transport) · D-57
(host_origin_protection stays off; Localtonet documentation-only). Authoritative text:
[05-PLAN-OUTLINE.md §1](../../../.planning/phases/05-cloud-exposure-and-tunneling/05-PLAN-OUTLINE.md).

## Risks

- ngrok free-tier terms can shift (flagged in research): re-verify the dashboard before
  claiming the domain and before league day.
- Monthly quota (1 GB / 20k requests) is shared across all testing — close tunnels between
  sessions; rehearse the gate loopback-first.
- ~~The remote round needs a second machine/network~~ — **closed 2026-08-16 at attempt 4**
  (attempts 1–3: disagreeing verdicts, a mid-game ingress drop, then a clean template-fallback
  round). Kept as a risk note for league day: the round depends on a second operator, and
  attempts 1–3 each failed for a different reason, so budget for a retry rather than assuming
  one clean run.
- **The 05-11 tunnel-repair path has never fired in a live round** — no drop occurred in
  attempt 4, so it is proven wired but not proven effective. Its detector probes the LOCAL
  ngrok agent API, which is a narrower envelope than "our public ingress is reachable".
- **05-12's peer-id validation is the highest-risk instruction in the second set.** Written
  too tightly it rejects an honest league opponent and converts a clean game into a
  self-inflicted rules-16/22 loss. The plan states safety-only validation as a `must_have`
  truth with an honest-foreign-convention control test for exactly this reason.
- Three plans touch `agent_audit_wiring.py` (102 code lines at HEAD) and two touch
  `agent_entrypoint.py`; `agent_wiring.py` sits at 148/150, `turn_buffer.py` at 146 and
  `turn_actions.py` at 143. Each plan re-measures with `scripts/check_line_limit.sh` and
  splits a sibling where a fix does not fit — never compresses code to fit.
- 05-04/05-05 touch commit-reveal and audit code while GATE-6's three criteria all PASS.
  Both re-run `scripts/measure_gate6.py` and require all three to still PASS.
