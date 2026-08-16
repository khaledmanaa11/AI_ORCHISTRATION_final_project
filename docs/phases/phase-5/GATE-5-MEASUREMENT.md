# GATE-5 measurement — Phase 5, book §10.4 milestone 5

**Status:** Criterion 1 **PASS** — measured 2026-08-09T09:41:20Z against the reserved domain
`perdurable-mireille-nonzoologically.ngrok-free.dev`; evidence in
[`gate5_smoke_evidence.json`](gate5_smoke_evidence.json). Criterion 2 **PENDING** — two genuine
remote rounds have run. Attempt 1 (2026-08-13): full capture across two machines/networks, but
the verdicts disagree and the logs carry different game UIDs. Attempt 2 (2026-08-16): the
attempt-1 protocol fixes all held — one shared game UID, cross-verified Step-0 declarations,
honest failure records — but machine A's tunnel ingress died at turn 4 and nothing repaired
it, so no agreeing verdicts exist; see
[Attempt 1](#attempt-1--2026-08-13-completed-round-criterion-not-yet-closed) and
[Attempt 2](#attempt-2--2026-08-16-mid-game-tunnel-drop-criterion-not-yet-closed) below.
**Date:** 2026-08-09 · **Plan:** 05-03 · **Method:** `scripts/gate5_tunnel_smoke.py` for
criterion 1; a human-run procedure, recorded here, for criterion 2.

Per rule 38 and this plan's own must_haves: **the phase is not fully measured while either
row above reads PENDING.** `/gsd:verify-work 5` must not tick GATE-5 until both criteria carry
real evidence — mirroring `docs/phases/phase-4/GATE-4-MEASUREMENT.md`'s own live-PENDING
discipline. Criterion 1 now carries a real run; criterion 2 remains the one open item.

---

## The two criteria — quoted verbatim from `.planning/ROADMAP.md` Phase 5 (not ours to edit)

> **Success Criteria** (book milestone gate, §10.4):
>
> 1. Each peer is reachable on the public internet through ngrok/Localtonet
> 2. An agent on a remote machine connects through the tunnel and plays a full round against
>    the local agent

Each criterion gets a method and a number below — not a verdict standing alone.

---

## Criterion 1 — each peer is reachable on the public internet through ngrok/Localtonet

**Method.** `scripts/gate5_tunnel_smoke.py` — the scriptable half of this criterion. It drives
the REAL, shipped `TunnelManager` (05-01) and `SharedSecretMiddleware` (05-02), never a parallel
reimplementation: starts one peer (`config/police` by default), brings up its ngrok tunnel,
and makes two real HTTP round trips through the **public URL** (not loopback) to that peer's
own `/mcp` route — one carrying the shared-secret header (must succeed, a valid MCP tool list),
one without it (must return 403 through the tunnel, proving the boundary holds under a real
public request, not just in the loopback integration test 05-02 already shipped
(`tests/integration/test_secret_channel.py`)).

This is a **smoke test, not the remote round** — it proves reachability from the SAME machine
via the public URL, deliberately never presented as criterion 2's genuine second-machine
connection (must_haves; the distinction CONTEXT.md locks). It needs a real ngrok account and is
therefore a manual script, not a CI test — stated in its own docstring.

**Run it:**

```
NGROK_AUTHTOKEN=<token> PURSUIT_NGROK_DOMAIN=<your-claimed-domain>.ngrok-free.app \
PURSUIT_TUNNEL_SECRET=<shared-secret> \
uv run python scripts/gate5_tunnel_smoke.py
```

It refuses to run — naming every missing variable — if any of the three above are unset;
`scripts/gate5_smoke_checks.py::missing_env_vars` is the exact, offline-tested function that
preflight uses (`tests/unit/test_gate5_tunnel_smoke_preflight.py`).

**What a PASS looks like.** The script writes
[`gate5_smoke_evidence.json`](gate5_smoke_evidence.json) with these fields, all of which must
hold for `"verdict": "PASS"`:

| Field | Must be |
|---|---|
| `url_is_https_and_matches_domain` | `true` — `public_url` is `https://` and its host equals `PURSUIT_NGROK_DOMAIN` exactly |
| `authorized_request_reached_mcp` | `true` — the secret-header request returned the five D-05 tool names through the tunnel |
| `unauthorized_request_rejected_403` | `true` — the no-header request got a 403 through the tunnel, not loopback |
| `round_trip_seconds` | a real, non-zero number (informational — no §10.4 latency bound exists for this criterion) |

**Current evidence — measured run, 2026-08-09T09:41:20Z.** `verdict: PASS`.

| Field | Measured |
|---|---|
| `public_url` | `https://perdurable-mireille-nonzoologically.ngrok-free.dev` |
| `url_is_https_and_matches_domain` | `true` — host matched `PURSUIT_NGROK_DOMAIN` exactly |
| `authorized_request_reached_mcp` | `true` — the five D-05 tool names returned through the tunnel (`POST /mcp` → `200 OK`) |
| `unauthorized_request_rejected_403` | `true` — `SharedSecretMiddleware` logged the rejection and returned `403 Forbidden` through the public URL |
| `round_trip_seconds` | `1.859` (informational — §10.4 sets no latency bound for this criterion) |

Two observations from the run, recorded rather than smoothed:

1. **The reserved domain is a `.ngrok-free.dev`, not `.ngrok-free.app`.** ngrok issues both
   suffixes; `check_public_url` matches `https://<configured host>` generically and hardcodes
   no suffix, so this needed no code change. The command block above still shows `.app` as the
   illustrative shape — read it as "your claimed domain, whatever suffix ngrok gave it".
2. **Windows asyncio emits `OSError [WinError 995]` and a `CancelledError` during teardown**,
   after both assertions have passed and the tunnel has stopped. This is uvicorn/proactor
   socket-close noise on shutdown, not a failure of either assertion — the script had already
   computed `verdict: PASS` and exited 0. Noted so a future reader does not mistake the
   traceback for a broken gate.

**Rerun command:** the command block above.

---

## Criterion 2 — the genuine remote round (CLOUD-02)

**Status: PENDING.** This criterion inherently needs a second machine on a different network
and a human to operate it — it cannot be produced by any script in this repository, and
same-machine-via-public-URL (criterion 1's smoke test, above) is never a substitute for it
(must_haves). This section is the full procedure a human with two machines follows to close it,
mirroring `GATE-4-MEASUREMENT.md`'s own live-run precedent: state the exact steps, then wait for
a real run rather than softening the PENDING status.

**Procedure.** The operator-facing expansion of the seven steps below — machine-B setup,
the two tunnel paths for the second machine, the digests to verify, and the evidence to
retain — is [`REMOTE-ROUND-RUNBOOK.md`](REMOTE-ROUND-RUNBOOK.md). The canonical steps:

1. **Start the local agent** on machine A with the tunnel and shared secret configured:
   ```
   NGROK_AUTHTOKEN=<token> PURSUIT_NGROK_DOMAIN=<claimed-domain>.ngrok-free.app \
   PURSUIT_TUNNEL_SECRET=<shared-secret> \
   uv run python -m pursuit.main --config-dir config/police
   ```
   (or `config/thief` — either role proves the same criterion.)
2. **Read the exchange block** `tunnel_wiring.exchange_block()` prints to stdout on startup:
   the public URL, the shared-secret header NAME, and which env var the opponent must set for
   its VALUE — never the secret value itself in this block.
3. **Deliver the public URL and the secret value** to the remote operator out-of-band (a
   message, a call — never committed to the repo, never emailed in plaintext with the
   config). The remote operator sets `PURSUIT_TUNNEL_SECRET` (or the header's configured env
   var name) to that value locally.
4. **Remote config paste.** On machine B, the remote operator points their own peer's
   `PURSUIT_OPPONENT_URL` (the Phase-2 `network.json`/env-override seam, D-16) at machine A's
   public URL + `/mcp`, and starts their own agent.
5. **Play one full round** to a real outcome (capture, survival, tie, or technical loss) — not
   a partial handshake.
6. **Retain both peers' event logs** (`logs/<role>/<game_uid>.jsonl`) and the final verdict
   each side records, as the evidence this section links once the round has actually happened.
7. **Note the machine/network pair used** (e.g., "machine A: Windows 11, home network; machine
   B: `<description>`, `<network>`") — the criterion is about a genuine network boundary, and
   which one was crossed is part of the evidence.

**What closes this section.** Both retained JSONLs (paths filled in here), both final
verdicts (must agree — rule 38's own honesty requirement applies to this round like any
other), and the machine/network note from step 7.

### Attempt 1 — 2026-08-13, completed round, criterion NOT yet closed

A genuine remote round ran 2026-08-13 ≈13:43 UTC: machine A (this box, police, 12-core,
**on a phone hotspot**, ngrok domain `perdurable-mireille-nonzoologically.ngrok-free.dev`)
vs machine B (remote Windows 11 laptop, thief, 20-core, **on wired ethernet — a different
network**, its own tunnel at `corny-ocelot-dominion.ngrok-free.dev`, which also passed its
own criterion-1 smoke — evidence retained). Both sides ran commit `384da44`. The step-7
machine/network note is therefore satisfied: hotspot ↔ wired ethernet is a real network
boundary, crossed in both directions through the two tunnels. The round played **all 5 turns to a real capture**, commit → ack → reveal on
every turn, Step-0 declarations exchanged and HMAC-signed, and the police-side final audit
**matched on both self and peer** — the tunnel + shared-secret transport did its job
end-to-end. Evidence: [`remote-round-2026-08-13/`](remote-round-2026-08-13/) (both event
logs, both ledgers, both declaration pairs, machine B's smoke evidence).

**Why this does not close criterion 2 (rule 38):** the two sides' final verdicts
**disagree**. Machine A recorded `capture` with a clean `audit_verdict`; machine B recorded
`capture` and then a spurious `technical_win {reason: opponent_unresponsive}`. Diagnosed
(6-agent pass, 2026-08-13): machine A completed its own **matched** audit — its `peer_audit`
carries machine B's five ledger hashes byte-for-byte, so B's final-reveal push attempt 1 WAS
delivered and processed — then hard-cancelled its server and killed its ngrok tunnel with
zero grace while B's exchange was still in flight; B's remaining attempts died in ~0.65 s
each against the closed listener, and B converted its own failed SEND into an accusation
against a peer that had just answered it. The round also surfaced protocol/evidence bugs (the two logs
carry **different game UIDs** — `074fc2b16888899e` on A vs `d50ceb00be724b93` on B — inbound
hints are never wire-logged, and the responder never receives hints at all), diagnosed and
tracked as gaps in `.planning/phases/05-cloud-exposure-and-tunneling/05-UAT.md`. The
criterion stays **PENDING** until a re-run after those fixes produces two logs, one shared
game UID, and two agreeing verdicts.

### Attempt 2 — 2026-08-16, mid-game tunnel drop, criterion NOT yet closed

Same machine/network pair as attempt 1, reversed operational shape on machine B: Smart App
Control (`WinError 4556`) blocks pyngrok's downloaded binary there, so B ran the signed
Microsoft-Store ngrok CLI standalone (`ngrok http 8002 --domain=corny-ocelot-dominion...`)
with the agent tunnel-off (`PURSUIT_NGROK_DOMAIN` unset) — the runbook's Path C. Both sides
ran commit `9bda33a`. Game `5efbc5811fabfac4` — **one shared game UID across all four
artifacts on both machines** (the 05-05/D-61 fix, confirmed live), Step-0 declarations
cross-verified byte-for-byte in both directions, five ledger rows each, turns 0–3 played
with commit → ack → reveal and live LLM hints both ways. Evidence:
[`remote-round-2026-08-16/`](remote-round-2026-08-16/).

**Why this does not close criterion 2 (rule 38):** at 09:35:01Z machine B received A's
turn-4 commit (A→B still delivering); B's pushes to A then died with `ConnectError` —
its 4-attempt ladder gave up at 09:35:16.9Z, so B's real patience in this failure mode
measured **≈15.6 s**, not the nominal 30 s/attempt (a `ConnectError` returns instantly;
only the backoffs remain). A one-directional break: **machine A's public ingress (its
ngrok tunnel) dropped mid-game.** A stayed alive and listening until its watchdog killed
it at 09:36:02Z with **no verdict written**; B recorded
`technical_win {opponent_unresponsive}` → `game_over: technical_loss`, then its own
failed FINAL_REVEAL push honestly as `audit_incomplete {own_final_reveal_send_failed}`
(the 05-04/05-10 fixes, confirmed live — attempt 1's false accusation did not recur).
One verdict, no agreement. Root cause in `src/`: `TunnelManager.ensure_connected()` —
the bounded reconnect designed for exactly this under D-55 — had **no production
caller**; a dropped tunnel was permanent. Closed by plan 05-11
(`.planning/phases/05-cloud-exposure-and-tunneling/05-11-PLAN.md`): a watch task now
polls tunnel health every `watchdog_poll_seconds` for the whole game and repairs a
detected drop with the existing Table-19 bound. Detection envelope stated honestly there:
pyngrok's `healthy()` sees agent-process/local-API death, not a live-process session
blip — whether A's exact drop was in the detectable class is not recoverable from the
retained evidence. Evidence gap, stated for attempt 3: **neither console was retained**
for this round (the runbook's amended §5 list requires them) — attempt 3 must
`Tee-Object` both consoles from the start. The criterion stays **PENDING** until attempt
3 produces two agreeing verdicts on one shared game UID.

---

## Why criterion 2 cannot be scripted from this repo alone

Every other Phase-5 assertion — tunnel lifecycle, reconnect bounds, the shared-secret
boundary, the public-URL round trip — is provable by one process on one machine, because the
opponent side can be simulated with a second local `PeerRuntime` (05-02's own
`test_secret_channel.py` does exactly this). Criterion 2 is different by construction: "an
agent on a **remote machine**" is not a property this repository's test suite, or any script
it runs, can produce by itself — it requires an actual second computer on an actual different
network, operated by an actual second person (or the same person, physically elsewhere). That
is not a testing gap to close with more mocking; it is the literal content of the criterion.

---

*Phase: 05-cloud-exposure-and-tunneling*
*Plan: 05-03*
