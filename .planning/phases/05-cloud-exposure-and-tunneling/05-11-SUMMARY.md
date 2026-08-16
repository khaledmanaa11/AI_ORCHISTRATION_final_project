---
phase: 05-cloud-exposure-and-tunneling
plan: "11"
subsystem: infra
tags: [ngrok, pyngrok, tunnel, reconnect, asyncio, watchdog-cadence, remote-round]

# Dependency graph
requires:
  - phase: 05-01
    provides: "TunnelManager (DI seams, bounded ensure_connected), tunnel_wiring.run_with_tunnel, the D-55 cadence declaration in tunnel_config.py"
provides:
  - "ensure_connected() has a production caller: monitor_tunnel(), a watch task run_with_tunnel starts after the exchange block and cancels in finally"
  - "poll cadence = NetworkParams.watchdog_poll_seconds (D-55/D-18 reuse) -- zero new numeric parameters"
  - "healthy()/ensure_connected() pushed through asyncio.to_thread -- the event loop keeps serving the peer during a 15-20 s repair"
  - "a raising probe or connect attempt is one SPENT Table-19 attempt (the attempt-2 ERR_NGROK_334 shape), never a crash, never an escape from the bound"
  - "one exhausted repair ends the watch with a printed EXHAUSTED line -- D-55's bound stays per-drop, never an unbounded retry loop"
  - "tunnel-off (every loopback test/dev flow) starts no task and changes nothing"
affects: [05-08, league-day]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Watch-task lifetime == body() lifetime: create_task after start(), cancel+suppress before tunnel.stop() (PeerRuntime.stop() shape)"
    - "Sync blocking collaborator driven from async via injectable to_thread seam; tests inject an inline stand-in -- zero real threads/sleeps"
    - "Detection-envelope honesty: pyngrok healthy() latches startup flags and probes the LOCAL agent API only -- stated in the docstring, not papered over"

key-files:
  created:
    - tests/unit/test_tunnel_wiring_monitor.py
  modified:
    - src/pursuit/network/tunnel_manager.py
    - src/pursuit/network/tunnel_wiring.py
    - tests/unit/test_tunnel_manager_reconnect.py
    - tests/unit/test_tunnel_wiring.py
    - tests/unit/test_agent_entrypoint.py
---

# 05-11 — the tunnel watch: `ensure_connected()` finally has a caller

**Trigger.** Remote-round attempt 2 (2026-08-16, game `5efbc5811fabfac4`): machine A's
ngrok ingress died at turn 4; B's pushes got `ConnectError`; A idled 60 s and its watchdog
killed it verdictless. `TunnelManager.ensure_connected()` — designed, tested and documented
for exactly this under D-55 — was called by nothing in `src/` or `scripts/`. Evidence:
`docs/phases/phase-5/remote-round-2026-08-16/`, narrative in GATE-5-MEASUREMENT.md
Attempt 2.

**What landed.**

1. `tunnel_manager.py` — `network_params` made public (the watch reads the D-55 cadence);
   `ensure_connected()` contains a raising probe (dead agent process = "unhealthy") and a
   raising connect attempt (ERR_NGROK_334, no route, DNS) as one spent attempt each, so
   the Table-19 bound holds for every failure mode; `healthy()`'s docstring states its
   detection envelope honestly (process/local-API death yes; live-process session blip no
   — that is the ngrok agent's own built-in reconnect).
2. `tunnel_wiring.py` — `monitor_tunnel()`: every `watchdog_poll_seconds`, probe via
   `to_thread`; on a drop, one bounded repair via `to_thread`; DOWN/RESTORED/EXHAUSTED
   printed as retained-console evidence; return after one exhausted repair.
   `run_with_tunnel` starts the task after `start()` + exchange block and cancels it in
   `finally` before `tunnel.stop()`.
3. Tests — 3 new reconnect cases (raise-as-spent-attempt, later-attempt success after an
   earlier raise, raising probe), 7-case `test_tunnel_wiring_monitor.py` (cadence pinned
   to `watchdog_poll_seconds`, repair-and-continue, bounded give-up, probe-raise,
   watch-lifetime == body-lifetime, exhausted-watch survival, tunnel-off starts no task).
   Existing fakes gained only a `network_params` attribute.

**Measured.** `ruff check` 0 · `check_line_limit.sh` exit 0 · suite **1374 passed** ·
coverage ≥ gate 85. Adversarial 3-lens review (concurrency / rule-compliance /
does-it-fix-the-evidence) ran before commit; its REAL findings changed the diff:

- **Teardown could eat the game** (empirically proven): a watch task that died raising
  re-raised out of `run_with_tunnel`'s `finally`, masking the resolved outcome AND
  skipping `tunnel.stop()`. Now: non-cancellation exceptions contained to a printed
  `TUNNEL_WATCH_ERROR_LINE`, `tunnel.stop()` unconditional, pinned by
  `test_run_with_tunnel_survives_a_watch_that_died_raising`.
- **A straggling repair could resurrect the agent** (empirically proven): cancelling
  `to_thread` does not stop the worker thread; a repair landing after `stop()` re-spawned
  ngrok — and a watchdog `os._exit(1)` skips pyngrok's atexit reaper, orphaning an agent
  that makes the NEXT launch fail with ERR_NGROK_334. Now: `ensure_connected` checks
  `_stopped` before each connect (`test_ensure_connected_after_stop_never_resurrects`);
  the race narrows to one in-flight connect, stated in the docstring instead of the
  previous false "never races the teardown" claim.
- **The to_thread property was unpinned** (reviewer re-ran the monitor suite against a
  loop-blocking variant: all passed). Now `_InlineToThread` counts calls and the counts
  are asserted.
- Docstring honesty: the ERR_NGROK_334 console is the **2026-08-14** failed launch, not
  attempt 2's round — reattributed; the unsourced "the ngrok agent's own built-in
  reconnect handles it" reassurance dropped; `healthy()` now also states that
  `get_ngrok_process` is not read-only (it may start a fresh agent, whose
  healthy-without-our-domain state is the residual blind spot).

**Known limitations, accepted and stated.** Repair timing vs the peer's REAL patience
(attempt 2 measured ≈15.6 s: instant `ConnectError` collapses the 30 s/attempt ladder to
its backoffs): detection ~1 s + leading 5 s backoff + connect RTT fits the window only in
the good case; one contained 334 raise lands at its edge. The Table-19 ladder shape
(sleep-before-retry) is kept as designed rather than re-engineered. The repair path never
calls `watchdog.touch()` — a repair longer than the remaining watchdog budget still loses
to our own watchdog (boundary: watchdog.py stays untouched). pyngrok's local-API probe
has no timeout; a hung (not dead) local API would wedge the watch silently — fixing it
needs a probe-timeout number that PARAMETERS.md does not supply (rule-1 blocker, raised
and declined).

**Deliberately out (rule-1 blockers raised, declined).** A public-URL probe (needs a probe
timeout — a new number), a consecutive-unhealthy debounce (same), any watchdog.py change
(the documented boundary stands), a Localtonet code path.
