# Localtonet fallback runbook (D-57, rule 10)

**Status:** documentation only. **No Localtonet code path exists anywhere in `src/`,
`scripts/`, or `config/` — this file is the entire deliverable.** Rule 10 requires "a
tunneling tool," naming ngrok and Localtonet as the two named options ("either is
compliant" per `05-CONTEXT.md`'s own locked decision). ngrok is this project's primary,
integrated provider (`pyngrok`, `TunnelManager`, D-54). Building a second, parallel Python
integration for Localtonet — a second `TunnelManager`-equivalent, a second config shape, a
second set of tests — would double the engineering surface for a path whose only job is to
be available if ngrok is ever unusable on league day. A runbook a human can follow start to
finish satisfies rule 10's actual requirement (a tunneling tool is used) without that cost.
If this ever needs to become code, it is new scope, not a gap in this phase.

This document is self-contained: everything from install through league-day use is here,
with no dependency on any other file.

---

## 1. Install

Two options (`localtonet.com`):

- **Windows executable** — download the installer from the Localtonet website and run it.
- **Microsoft Store** — search "Localtonet" and install directly (simpler on a locked-down
  Windows machine, no installer execution needed).

Either way, the result is a `localtonet` CLI (or `localtonet.exe`) available in a terminal.

## 2. Authtoken

Localtonet requires an account and an auth token, the same shape as `NGROK_AUTHTOKEN`:

```
localtonet --authtoken <YOUR_LOCALTONET_TOKEN>
```

First run on Windows may instead prompt interactively for the token if it is omitted. As
with ngrok, **the token is a secret and is never committed** — if this fallback is ever
actually used, its token belongs in `.env` (already `.gitignore`d) or is typed at the
prompt, never in `config/*/tunnel.json` (which, like the ngrok path, would carry only the
env var's NAME if this were ever wired into code — it is not, per this document's opening
paragraph).

## 3. Dashboard port mapping

Unlike ngrok's `domain=` kwarg (scriptable), Localtonet's free tier configures the
HTTP-tunnel-to-local-port mapping through its **web dashboard**, not purely via CLI flags:

1. Log in to the Localtonet dashboard.
2. Create (or edit) an HTTP tunnel.
3. Point it at `127.0.0.1:<agent's local port>` — the same port this project's
   `config/<role>/network.json` already assigns (`8001` for police, `8002` for thief,
   D-04/D-16/D-17/D-18) and the same loopback host `PeerRuntime._run_http` already binds.
4. Save. The dashboard assigns a public URL (a random subdomain on the free tier — see
   §5 below for what that means operationally).

This is less scriptable than ngrok's `domain=` kwarg deliberately: this project does not
attempt to script it, since no code path uses it (§0 above).

## 4. Persistent service (optional, survives reboots)

```
localtonet --install-service --authtoken <YOUR_LOCALTONET_TOKEN>
localtonet --start-service
```

Installs Localtonet as a Windows service so the local agent process doesn't need a
separate terminal window kept open for the tunnel client itself. This does **not** remove
the free-tier 30-minute timeout described next — the *service* surviving a reboot is a
different property from the *tunnel* surviving 30 minutes of use.

## 5. The 30-minute free-tier timeout — why this is the fallback, not the primary

Localtonet's free plan (`localtonet.com`, confirmed at research time):

- 1 HTTP/TCP/UDP tunnel
- 1 GB bandwidth/month
- **A 30-minute tunnel timeout** — materially worse than ngrok's free plan, which has no
  documented session timeout (`ngrok.com/docs/pricing-limits/free-plan-limits`, "endpoints
  remain online indefinitely")
- A random subdomain by default; a static/custom domain is a paid-plan feature only

**This is the entire reason ngrok is primary and this is the fallback (D-57).** A league
match — commit/acknowledge/reveal/audit turns across a full game — can plausibly exceed 30
minutes; ngrok's static domain has no such ceiling. Localtonet is acceptable as a fallback
specifically because it is only ever needed if ngrok itself is unusable that day (account
issue, quota exhausted, service outage), not because its own limits are comparable.

## 6. League-day use: re-establishing the tunnel per window

If Localtonet is actually the provider in use on league day (ngrok unavailable):

1. Start (or restart) the tunnel — `localtonet --start-service` if installed as a service,
   or run `localtonet` directly with the dashboard-configured mapping from §3.
2. **Every ~30 minutes, the tunnel must be re-established** — the free-tier timeout is a
   hard ceiling, not a soft warning. A human operator (this project has no automated
   Localtonet reconnect, unlike `TunnelManager.ensure_connected()`'s bounded ngrok
   reconnect, D-55) needs to watch the clock and restart the tunnel before it drops, or
   restart it immediately after a drop is noticed — a game in progress when the tunnel
   drops loses public reachability until it is restarted, exactly like any other network
   partition the Phase-2 watchdog/retry machinery (`retry_count`/`backoff_seconds`, Table
   19) is designed to tolerate for the *opponent's* connection, not this project's own
   outbound exposure.
3. **The public URL may change on every restart** (free-tier random subdomain, §3) — unlike
   ngrok's static domain, the operator must re-share the new URL with the opponent team
   after every re-establishment, the same out-of-band exchange
   `docs/phases/phase-5/GATE-5-MEASUREMENT.md`'s procedure describes for ngrok, repeated as
   often as the timeout forces it.

---

*Phase: 05-cloud-exposure-and-tunneling*
*Plan: 05-03 (D-57)*
