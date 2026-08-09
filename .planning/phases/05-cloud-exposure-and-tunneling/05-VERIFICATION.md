---
phase: 05-cloud-exposure-and-tunneling
verified: 2026-08-09T05:58:21Z
status: human_needed
score: 16/16 automated must-haves verified; 2/2 book §10.4 criteria pending on human runs (expected, documented)
human_verification:
  - test: "GATE-5 criterion 1 -- run the smoke script with a real ngrok account: `NGROK_AUTHTOKEN=<token> PURSUIT_NGROK_DOMAIN=<domain>.ngrok-free.app PURSUIT_TUNNEL_SECRET=<secret> uv run python scripts/gate5_tunnel_smoke.py`"
    expected: "gate5_smoke_evidence.json written to docs/phases/phase-5/ with verdict=PASS: public_url is https and matches the claimed domain; the secret-header request returns the five D-05 tool names through the tunnel; the no-header request returns 403 through the tunnel (not loopback)."
    why_human: "Needs a real ngrok account and a claimed static domain -- this machine has none of NGROK_AUTHTOKEN/PURSUIT_NGROK_DOMAIN/PURSUIT_TUNNEL_SECRET set. The script itself refuses to run and names the missing vars (verified: preflight() unit-tested offline)."
  - test: "GATE-5 criterion 2 (CLOUD-02) -- the genuine remote round: start one peer with the tunnel on machine A, share the exchange block's public URL + secret out-of-band with a remote operator on machine B (different network), point machine B's PURSUIT_OPPONENT_URL at machine A's public URL, play one full round to a real outcome, retain both peers' event logs and verdicts."
    expected: "Both machines' logs/<role>/<game_uid>.jsonl exist and agree on a final verdict (capture/survival/tie/technical loss); the machine/network pair used is noted in GATE-5-MEASUREMENT.md."
    why_human: "Inherently requires a second physical machine on a different network and a human operator on each side -- this cannot be produced by any script in this repository (GATE-5-MEASUREMENT.md's own stated reasoning, cross-checked against the code: no simulated remote-machine path exists anywhere in scripts/ or tests/)."
---

# Phase 5: Cloud Exposure and Tunneling Verification Report

**Phase Goal:** Expose the local FastMCP server publicly via ngrok or Localtonet.
**Verified:** 2026-08-09T05:58:21Z
**Status:** human_needed
**Re-verification:** No -- initial verification

## Goal Achievement

All CODE-level must-haves from 05-01/05-02/05-03 were re-verified directly against the
repository (not the SUMMARY prose) -- config files read byte-for-byte, source modules read
in full, every project gate re-run from scratch, and `git diff` checked against the
pre-Phase-5 commit to confirm the transport itself is untouched. Both book §10.4 success
criteria remain PENDING, exactly as `docs/phases/phase-5/GATE-5-MEASUREMENT.md` states --
this is the expected, honestly-documented state (rule 38), not a gap: neither criterion can
be produced without a real ngrok account (criterion 1) or a second machine and human
operator on a different network (criterion 2), and no code in this phase pretends
otherwise.

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Tunnel is driven by `pyngrok` (D-54), never `ngrok-python`, every pyngrok call injected | VERIFIED | `pyproject.toml:9` `"pyngrok>=8.1.2"`; `uv.lock` pins `pyngrok` 8.1.2; `src/pursuit/network/tunnel_manager.py` constructor takes `connect/disconnect/kill/get_process/sleep/clock` all keyword-only with real pyngrok defaults bound once |
| 2 | Zero new numeric parameters (D-55) -- `tunnel.json` is strings only; reconnect reuses `NetworkParams.retry_count`/`backoff_seconds` | VERIFIED | `config/police/tunnel.json` and `config/thief/tunnel.json` read directly -- 6 string fields, no numeric leaf (`"version": "1.00"` is a string). `tunnel_manager.py:96-111` `ensure_connected()` uses `self._network_params.retry_count`/`backoff_seconds`, no new numeric field anywhere in `TunnelParams` |
| 3 | Secret/domain/token values come from `os.environ.get()` only, never committed | VERIFIED | `grep -rn "authtoken\|ngrok-free" config/ src/` returns only field/env-var NAMES; `.env-example` has dummy placeholder values only; no `.env` tracked in git; `secret_wiring.resolve_shared_secret` and `tunnel_config.require_env` both read via `os.environ` |
| 4 | Transport (`PeerRuntime`, envelope, handshake, tools.py) byte-untouched except seam-only additions | VERIFIED | `git diff 8d5e77f -- envelope.py handshake*.py tools.py` = empty; `git diff 8d5e77f -- peer_runtime.py` is a pure +32/-1 additive diff (constructor kwarg, `middleware=` at existing `run_async` call, explicit `StreamableHttpTransport` replacing the bare-string `Client(...)` call) -- no existing method signature removed or reshaped |
| 5 | Lifecycle mirrors watchdog: tunnel starts before the runtime, stops after `shutdown_cleanly`, start failure aborts before the game begins | VERIFIED | `agent_entrypoint.py:34-55` -- `run_with_tunnel(tunnel, _play)` where `_play` runs `start_server`→handshake→turn loop→`shutdown_cleanly` in its own `finally`; `tunnel_wiring.py:56-71` `run_with_tunnel` calls `tunnel.start()` (raises loudly, unhandled) before `body()`, `tunnel.stop()` in its own `finally` after `body()` returns |
| 6 | Reconnect targets the SAME static domain, bounded by reused Table 19 numbers; watchdog.py untouched | VERIFIED | `tunnel_manager.py:104-111` `ensure_connected()` re-resolves `domain_env` (same domain) each retry, loop bounded by `retry_count`; `git diff 8d5e77f -- src/pursuit/network/watchdog.py` = empty |
| 7 | Exchange printout: public URL + which env var to set, never the secret value | VERIFIED | `tunnel_wiring.py:43-53` `exchange_block()` emits `public_url`, `shared_secret_header` (name), `opponent_sets_env` (var name) -- no secret value field exists in the function at all |
| 8 | `config/police/tunnel.json` and `config/thief/tunnel.json` byte-identical | VERIFIED | Both files read directly -- identical content; `tests/unit/test_tunnel_config.py::test_role_files_are_byte_identical` passes |
| 9 | D-56: shared-secret check lives at the ASGI boundary (one `SharedSecretMiddleware` via `run_async(middleware=[...])`), never inside an `@mcp.tool` handler | VERIFIED | `secret_guard.py` -- pure ASGI `__call__(scope, receive, send)`; `peer_runtime.py:137` `middleware=build_middleware(self._shared_secret)` in the same `run_async` call that passes `sockets=`; `git diff 8d5e77f -- tools.py` empty (no tool-level check added) |
| 10 | D-56: client always builds `StreamableHttpTransport(url, headers=...)` explicitly, never a bare `Client(url)` string | VERIFIED | `peer_runtime.py:152-154` `client()` builds `StreamableHttpTransport` explicitly every call, with a comment citing the bare-string header-drop regression |
| 11 | Comparison uses `secrets.compare_digest`; rejection log carries no secret value | VERIFIED | `secret_guard.py:74` `secrets.compare_digest(supplied, self._expected)`; log line (`:79-82`) records only remote address, method, path, and the `missing`/`mismatched` fact |
| 12 | Secret-off by default (env var absent) -- no middleware installed, no header sent, loopback/tests unaffected | VERIFIED | `secret_wiring.resolve_shared_secret` returns `None` when `secret_env` unset; `build_middleware(None)`→`None`; `client_headers(None)`→ only the ngrok-bypass header; full `pytest` suite (1116 tests) passes with these vars unset on this machine |
| 13 | D-57: `host_origin_protection` stays off; reason documented at the call site | VERIFIED | `peer_runtime.py:121-127` comment; confirmed live: `fastmcp.settings.Settings().http_host_origin_protection` → `False` on this install (fastmcp 3.4.5) |
| 14 | Localtonet is documentation-only (D-57), no code path | VERIFIED | `docs/phases/phase-5/LOCALTONET-FALLBACK.md` states this explicitly; `grep -ri localtonet src/ scripts/` finds no source hits (doc file only) |
| 15 | GATE-5-MEASUREMENT.md quotes both §10.4 criteria verbatim, records both as evidence-gated, not verdicts | VERIFIED | File read in full -- both criteria block-quoted from ROADMAP.md unedited; criterion 1 has a field-by-field PASS definition; criterion 2 has the full 7-step human procedure |
| 16 | Nothing ticked anywhere in trackers (phase triplet, root docs/TODO.md, ROADMAP.md) | VERIFIED | `docs/phases/phase-5/TODO.md`, `docs/TODO.md` rows 97-98, and `.planning/ROADMAP.md` lines 159-164 all show `[ ]`/`☐` for every 05-0x row and the phase gate checklist |

**Score:** 16/16 automated truths verified. The two book §10.4 criteria (reachability,
remote round) are the phase's actual goal-level outcomes and both remain PENDING by design
-- see Human Verification below.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pursuit/network/tunnel_manager.py` | `TunnelManager` DI'd lifecycle | VERIFIED | 123 lines, `start/healthy/ensure_connected/stop`, `public_url` attr present, 100% covered |
| `src/pursuit/shared/tunnel_config.py` | `load_tunnel_config` + `TunnelKey` beside loader | VERIFIED | `TunnelKey` enum + `TunnelParams` + `load_tunnel_config`/`require_env`, 100% covered |
| `config/police/tunnel.json`, `config/thief/tunnel.json` | strings only, byte-identical | VERIFIED | 6 string fields each, identical content, no numeric leaf |
| `src/pursuit/network/secret_guard.py` | `SharedSecretMiddleware`, `compare_digest` | VERIFIED | pure ASGI class + `build_middleware`/`client_headers` factories, 100% covered |
| `src/pursuit/network/peer_runtime.py` | `run_async` gains `middleware=`; `client()` builds explicit `StreamableHttpTransport` | VERIFIED | both seams present and wired (lines 137, 152-154), 100% covered |
| `scripts/gate5_tunnel_smoke.py` | one-command smoke run, JSON evidence out | VERIFIED | drives the real `TunnelManager`/`PeerRuntime` (no reimplementation); `preflight()` refuses to run without env vars, unit-tested |
| `docs/phases/phase-5/GATE-5-MEASUREMENT.md` | both criteria + evidence | VERIFIED (content); PENDING (actual evidence) | both criteria quoted, both procedures complete, both marked PENDING honestly |
| `docs/phases/phase-5/LOCALTONET-FALLBACK.md` | rule-10 fallback runbook | VERIFIED | self-contained install→league-day runbook, no code |
| `docs/phases/phase-5/{PRD,PLAN,TODO}.md` | phase triplet | VERIFIED | all three exist, nothing ticked |
| `.planning/graphs/GRAPH_REPORT.md` | refreshed, tunnel modules present | VERIFIED | `TunnelManager`/`SharedSecretMiddleware` both found in the committed report; `graph.json`/`graph.html` correctly gitignored (not tracked) |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `agent_entrypoint.py` (`run_agent`) | `tunnel_wiring.py` (`TunnelManager`) | `run_with_tunnel` wraps the whole body | WIRED | `agent_entrypoint.py:34,55`; tunnel starts before `_play()`, stops after, in its own `finally` |
| `tunnel_manager.py` | `shared/network_config.py` | reconnect bounds reused, not redeclared (D-55) | WIRED | `ensure_connected()` reads `self._network_params.retry_count`/`.backoff_seconds` directly |
| `peer_runtime.py` | `secret_guard.py` | middleware attached in the same `run_async` call that passes `sockets=` (D-56) | WIRED | `peer_runtime.py:137` |
| `peer_runtime.py` | `shared/tunnel_config.py` | header name sourced from one owner (via `secret_wiring.resolve_shared_secret`) | WIRED | `agent_lifecycle.py:129` resolves and threads `shared_secret` into the one `PeerRuntime(...)` construction site |
| `scripts/gate5_tunnel_smoke.py` | `tunnel_manager.py` | smoke script drives the real `TunnelManager` | WIRED | `gate5_tunnel_smoke.py:57,98` imports and constructs the real class, no parallel implementation |
| `docs/phases/phase-5/GATE-5-MEASUREMENT.md` | `.planning/ROADMAP.md` | criteria quoted verbatim | WIRED | text-for-text match against ROADMAP.md lines 150-153 |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|---|---|---|
| CLOUD-01 (each peer reachable via tunnel) | Code SATISFIED / Evidence PENDING | No blocker in code -- `TunnelManager` + `SharedSecretMiddleware` are complete, tested (100% coverage on all Phase-5 modules), and wired. Evidence requires a human-run smoke script with a real ngrok account (not available on this machine by design) |
| CLOUD-02 (remote agent plays a full round through the tunnel) | Code SATISFIED / Evidence PENDING | No blocker in code -- the exchange-block/opponent-URL seam (D-16/Phase-2) is unchanged and reused as documented. Evidence requires a second machine and human operator |

### Standing Gates (re-run fresh, not taken from SUMMARY)

| Gate | Result |
|---|---|
| `uv run ruff check .` | 0 violations |
| `uv run pytest tests/ --cov` | **1116 passed**, **95.70%** coverage (≥85% required); all Phase-5 modules (`tunnel_manager.py`, `tunnel_wiring.py`, `agent_entrypoint.py`, `secret_guard.py`, `secret_wiring.py`, `peer_runtime.py`, `tunnel_config.py`) at **100%** line coverage |
| `bash scripts/check_line_limit.sh` | clean |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `git diff` on `envelope.py`/`handshake*.py`/`tools.py` since pre-Phase-5 | empty on all three |
| `git diff` on `peer_runtime.py` since pre-Phase-5 | additive-only, +32/-1, seam-only (middleware kwarg, explicit transport) |
| Secret-literal grep across `src/`, `config/`, `.env-example` | zero real values found, names/dummies only |

### Anti-Patterns Found

None. Scanned every Phase-5-created/modified source file (`tunnel_manager.py`,
`tunnel_wiring.py`, `agent_entrypoint.py`, `secret_guard.py`, `secret_wiring.py`,
`peer_runtime.py`, `tunnel_config.py`, `gate5_tunnel_smoke.py`, `gate5_smoke_checks.py`) for
TODO/FIXME/placeholder/stub markers -- zero matches.

### Human Verification Required

Both items below are the phase's own book-mandated §10.4 milestone criteria. They are
**expected pendings**, explicitly documented as such in
`docs/phases/phase-5/GATE-5-MEASUREMENT.md` (both criteria marked PENDING with exact
procedures, per rule 38's honesty requirement) -- not gaps in the implementation. All code
that these procedures exercise (`TunnelManager`, `SharedSecretMiddleware`, the smoke
script, the exchange-block/opponent-URL seam) is verified complete and correct above.

#### 1. GATE-5 criterion 1 — public reachability smoke run

**Test:**
```
NGROK_AUTHTOKEN=<token> PURSUIT_NGROK_DOMAIN=<your-claimed-domain>.ngrok-free.app \
PURSUIT_TUNNEL_SECRET=<shared-secret> \
uv run python scripts/gate5_tunnel_smoke.py
```
**Expected:** `docs/phases/phase-5/gate5_smoke_evidence.json` is written with
`"verdict": "PASS"` -- `public_url` is `https://` and matches `PURSUIT_NGROK_DOMAIN`
exactly; the secret-header request returns the five D-05 tool names through the tunnel;
the no-header request returns 403 through the tunnel (not loopback).
**Why human:** Needs a real ngrok account and a claimed static domain, none of which exist
on this machine. `preflight()` (the offline-safe half) is already unit-tested and confirmed
to refuse cleanly, by name, when the vars are absent.

#### 2. GATE-5 criterion 2 (CLOUD-02) — genuine remote round

**Test:** Follow the 7-step procedure in `docs/phases/phase-5/GATE-5-MEASUREMENT.md`
("Criterion 2"): start the local agent with the tunnel + secret on machine A, read the
printed exchange block, deliver the URL and secret value to a remote operator on machine B
(different network) out-of-band, have machine B point `PURSUIT_OPPONENT_URL` at machine A's
public URL, play one full round to a real outcome, retain both `logs/<role>/<game_uid>.jsonl`
files and the final verdicts, note the machine/network pair.
**Expected:** Both event logs exist, both sides' final verdicts agree, and the
machine/network note is recorded in `GATE-5-MEASUREMENT.md`.
**Why human:** Requires an actual second computer on an actual different network operated by
a human -- inherently outside what any script in this repository can produce (confirmed: no
simulated-remote-machine test exists anywhere in `tests/` or `scripts/` for this criterion,
by design).

### Gaps Summary

No implementation gaps found. Every must-have from plans 05-01, 05-02, and 05-03 was
re-verified directly against source (not SUMMARY prose): the tunnel lifecycle is real and
DI'd (D-54), `tunnel.json` carries zero numeric leaves and reuses Table 19's reconnect
bounds (D-55), the shared-secret channel sits at the correct ASGI boundary with
`compare_digest` and a secret-off default (D-56), `host_origin_protection` is confirmed off
via a live probe of `fastmcp.settings` (D-57), and the pre-existing transport
(`envelope.py`/`handshake*.py`/`tools.py`) is byte-identical to before the phase while
`peer_runtime.py`'s diff is purely additive at the two documented seams. All standing gates
(ruff, pytest/coverage, line limit, no-LLM-in-strategy) pass fresh on this machine, matching
the SUMMARYs' claimed numbers exactly (1116 passed, 95.70% coverage). The only open items
are the two book §10.4 milestone criteria themselves, which the phase's own documentation
already and correctly records as PENDING pending a human operator with a real ngrok account
and a second machine -- exactly the class of item this task instructed to report as
human-verification, not as a gap.

---

*Verified: 2026-08-09T05:58:21Z*
*Verifier: Claude (gsd-verifier)*
