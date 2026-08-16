# Phase 5 PRD — Cloud Exposure and Tunneling

**Version:** 1.02 · **Status:** ◐ approved · **Updated:** 2026-08-16 (both acceptance
criteria MET; second gap-closure set 05-12..05-15 added)

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

## Gap closure — what attempt 1 of criterion 2 exposed (2026-08-13)
A genuine remote round ran across two machines on two networks and played a full 5-turn game
to a real capture — the tunnel and shared-secret transport did their job end to end. It did
**not** close criterion 2: the two sides' final verdicts disagreed, the two logs carried
different game UIDs, and the round exposed that a responder never receives hints at all.
Five gaps were diagnosed over the retained evidence (`05-UAT.md`, all CONFIRMED at high
confidence) and are closed by plans 05-04..05-08:

| Gap | What was wrong | Plan |
|---|---|---|
| G1 | A side's own failed final-reveal SEND was recorded as the PEER being unresponsive — a false accusation (rules 16/22) against a peer whose records that side had already audited; teardown cancelled the server with zero grace while the peer was mid-exchange | 05-04 (+ the 17.4 s responder tail, in 05-06) |
| G2 | The handshake-negotiated game id governed only a declaration FILENAME; log, ledger and every committed `state.game_id` kept a process-local random id, and the audit never read the state record at all | 05-05 |
| G3 | HINT was the only message type logged on send and not on receive — no durable record that hints crossed the wire (rule 20) | 05-06 |
| G4 | The receive-side drop window was structurally unsatisfiable for a responder, so the thief decoded 0 of 5 hints in every game, loopback included | 05-06 |
| G5 | A keyless run fell back to the template bank silently and still declared the configured model name (rule 38) | 05-07 |

**Criterion 2 CLOSED at attempt 4** (2026-08-16): two machines on two networks (hotspot ↔
wired ethernet), agreeing `capture` verdicts and `audit_verdict matched=true` on **both**
sides, one shared game UID per game, live `claude-haiku-4-5` hints declared on both sides.
Evidence `remote-round-2026-08-16-attempt4/`; narrative in
[GATE-5-MEASUREMENT.md](GATE-5-MEASUREMENT.md) Attempt 4. Every earlier attempt's evidence is
retained permanently and is not rewritten.

## Second gap closure — what the post-closure audit exposed (2026-08-16)

`/gsd:verify-work 5` re-measured the phase against live source rather than SUMMARY claims,
running six verifiers each answered by a skeptic instructed to refute it. G1–G5 were
confirmed genuinely closed with real production callers. Five further gaps were found, all
re-confirmed by hand, and are closed by plans 05-12..05-15. **None is a §10.4 criterion**, so
the gate above stands; three are league-day blockers.

| Gap | What is wrong | Plan |
|---|---|---|
| G6 | G1's non-accusation branch is unreachable under a slow send failure: the audit path never touches the freeze watchdog, so a ≤135 s push ladder is killed at the 60 s threshold and `record_audit_incomplete` never runs. The RECEIVE leg still accuses outright | 05-13 |
| G7 | The D-61 negotiated game id is peer-controlled and reaches a set constructor (unhashable → crash), a filesystem path (`../../evil` → traversal + silent overwrite) and the audit's membership key (`''` → false accusation of an honest peer) unvalidated | 05-12 |
| G8 | A hint re-sent after decode pops the buffer is decoded twice, double-counting evidence into the belief posterior; the initiator branch still stamps `state.turn` on the commit-reveal-off path | 05-14 |
| G9 | A non-str peer digest raises `TypeError` at the handshake and kills the process before move 1 — rule 36 against us. The project's own boundary rule (`audit.py:56-90`) says the seventh instance is "a review failure rather than a discovery"; this is it, and a green test currently pins the crash as intended | 05-12 |
| G10 | Doc/tracker honesty: attempt 4's "two games" are one deterministic game replayed (corrected); `declare_truthfully` is dead code whose docstring misdescribes the design; a stale PRD line contradicts `PRD_commit_reveal.md` §2.2 | 05-15 (doc parts already corrected) |

**Rules check, settled at plan-phase rather than deferred:** G10 initially read as a
rules-15/21 violation because no barrier or capture declaration is ever transmitted. Checked
against `docs/RULES.md` and `PRD_commit_reveal.md` §2.2 (D-66/SEC-07), it is not: the barrier
is declared openly *inside the committed action*, hashed into `H_commit` and cross-checked at
audit, which is exactly what rule 15's audit-shaped sanction contemplates. The only genuine
residual is the *capture* Claim, which is derived rather than announced — compliant as
`RULES.md` is worded, de-risked in 05-15 with the `GAME_OVER` envelope that already exists.

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
