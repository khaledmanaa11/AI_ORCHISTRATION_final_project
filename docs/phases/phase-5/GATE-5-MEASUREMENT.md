# GATE-5 measurement — Phase 5, book §10.4 milestone 5

**Status:** Criterion 1 **PENDING** (the smoke script has not yet been run — this machine has
none of `NGROK_AUTHTOKEN` / `PURSUIT_NGROK_DOMAIN` / `PURSUIT_TUNNEL_SECRET` set). Criterion 2
**PENDING** (the genuine remote round needs a second machine and a human operator; see
[Criterion 2](#criterion-2--the-genuine-remote-round-cloud-02) below).
**Date:** 2026-08-09 · **Plan:** 05-03 · **Method:** `scripts/gate5_tunnel_smoke.py` for
criterion 1; a human-run procedure, recorded here, for criterion 2.

Per rule 38 and this plan's own must_haves: **the phase is not fully measured while either
row above reads PENDING.** `/gsd:verify-work 5` must not tick GATE-5 until both criteria carry
real evidence — mirroring `docs/phases/phase-4/GATE-4-MEASUREMENT.md`'s own live-PENDING
discipline, applied here to both criteria rather than one.

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
[`gate5_smoke_evidence.json`](gate5_smoke_evidence.json) (does not exist yet — no run has
happened on this machine) with these fields, all of which must hold for `"verdict": "PASS"`:

| Field | Must be |
|---|---|
| `url_is_https_and_matches_domain` | `true` — `public_url` is `https://` and its host equals `PURSUIT_NGROK_DOMAIN` exactly |
| `authorized_request_reached_mcp` | `true` — the secret-header request returned the five D-05 tool names through the tunnel |
| `unauthorized_request_rejected_403` | `true` — the no-header request got a 403 through the tunnel, not loopback |
| `round_trip_seconds` | a real, non-zero number (informational — no §10.4 latency bound exists for this criterion) |

**Current evidence.** None — `gate5_smoke_evidence.json` has not been generated on this
machine. **Rerun command:** the command block above. Once run, replace this paragraph with the
three field values and the resulting verdict; do not summarize a run that did not happen.

---

## Criterion 2 — the genuine remote round (CLOUD-02)

**Status: PENDING.** This criterion inherently needs a second machine on a different network
and a human to operate it — it cannot be produced by any script in this repository, and
same-machine-via-public-URL (criterion 1's smoke test, above) is never a substitute for it
(must_haves). This section is the full procedure a human with two machines follows to close it,
mirroring `GATE-4-MEASUREMENT.md`'s own live-run precedent: state the exact steps, then wait for
a real run rather than softening the PENDING status.

**Procedure:**

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
other), and the machine/network note from step 7. None of that exists yet on this
repository's history; this procedure is what the next human-operator session runs.

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
