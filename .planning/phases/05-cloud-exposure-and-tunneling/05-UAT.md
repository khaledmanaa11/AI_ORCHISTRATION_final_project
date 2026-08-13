---
status: complete
phase: 05-cloud-exposure-and-tunneling
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-08-13T14:01:37Z
updated: 2026-08-13T14:15:00Z
---

## Current Test

[testing complete — 8/9 pass, 1 human-pending (GATE-5 criterion 2, the genuine remote
round). Zero implementation gaps. The phase gate stays UNTICKED per GATE-5-MEASUREMENT.md's
own rule until criterion 2 carries real evidence.]

## Tests

> Every result below was re-measured during this UAT session against `HEAD = 384da44`,
> not copied from the plan SUMMARY files or 05-VERIFICATION.md. All three tunnel env vars
> (`NGROK_AUTHTOKEN`/`PURSUIT_NGROK_DOMAIN`/`PURSUIT_TUNNEL_SECRET`) confirmed UNSET on
> this machine for every offline measurement.

### 1. Tunnel-off default is transparent
expected: With none of NGROK_AUTHTOKEN/PURSUIT_NGROK_DOMAIN/PURSUIT_TUNNEL_SECRET set, the full offline suite passes; tunnel-off and secret-off are the structural defaults (no boolean flags), so every pre-Phase-5 flow runs byte-identically
result: pass
measured: `uv run pytest tests/ --cov` → **1251 passed, 96.26% coverage, exit 0**, fully offline, zero env vars set. Phase-5 modules: `peer_runtime.py`/`secret_guard.py`/`secret_wiring.py`/`tunnel_manager.py`/`tunnel_wiring.py`/`tunnel_config.py` all **100%**; `agent_entrypoint.py` 85% (its uncovered lines were added by Phase 6's audit wiring, not Phase 5 — was 100% at 05-VERIFICATION). `resolve_shared_secret` returns `None` when the env var is unset (measured directly), so no middleware and no header exist in any default flow.

### 2. Exchange block prints URL and env-var NAME, never the secret value
expected: tunnel_wiring.exchange_block() emits the public URL, the shared-secret header NAME, and which env var the opponent sets — no secret value field exists in the output at all
result: pass
measured: live call → `public_url=…`, `shared_secret_header=X-Pursuit-Secret`, `opponent_sets_env=PURSUIT_TUNNEL_SECRET`. Control probe: with `PURSUIT_TUNNEL_SECRET=super-secret-value-xyz` actually set in the environment, the block was regenerated and the value did **not** appear — leak check `False`.

### 3. Shared-secret boundary holds over real sockets
expected: Two real loopback PeerRuntimes over actual HTTP — correct secret header reaches the MCP tools, missing header gets 403, wrong secret gets 403, all before any FastMCP dispatch
result: pass
measured: `tests/integration/test_secret_channel.py` — all 3 cases PASSED in 1.48s (`test_correct_secret_completes_a_real_call`, `test_missing_header_dies_at_the_boundary_before_mcp_routing`, `test_wrong_secret_fails_every_call`) — real sockets, real ASGI middleware, offline.

### 4. Smoke script refuses cleanly offline
expected: uv run python scripts/gate5_tunnel_smoke.py with no env vars set exits non-zero naming every missing variable, before touching pyngrok, PeerRuntime, or the network
result: pass
measured: `env -u NGROK_AUTHTOKEN -u PURSUIT_NGROK_DOMAIN -u PURSUIT_TUNNEL_SECRET uv run python scripts/gate5_tunnel_smoke.py` → *"gate5_tunnel_smoke requires these environment variables, missing: NGROK_AUTHTOKEN, PURSUIT_NGROK_DOMAIN, PURSUIT_TUNNEL_SECRET"*, **EXIT=1**, instantly, no network.

### 5. GATE-5 criterion 1 — peer reachable on the public internet
expected: gate5_smoke_evidence.json shows verdict PASS — public_url is https and matches PURSUIT_NGROK_DOMAIN, authorized request returned the five D-05 tool names through the tunnel, unauthorized request got 403 through the tunnel
result: pass
measured: `docs/phases/phase-5/gate5_smoke_evidence.json` (real run, 2026-08-09T09:41:20Z): `verdict: "PASS"`, `public_url: https://perdurable-mireille-nonzoologically.ngrok-free.dev`, `url_is_https_and_matches_domain: true`, `authorized_request_reached_mcp: true`, `unauthorized_request_rejected_403: true`, `round_trip_seconds: 1.859`. GATE-5-MEASUREMENT.md records the run field-by-field including the two honest observations (`.dev` vs `.app` suffix; Windows teardown noise after PASS was computed).

### 6. GATE-5 criterion 2 — genuine remote round (CLOUD-02)
expected: An agent on a remote machine (different network) connects through the tunnel and plays a full round to a real outcome; both event logs retained, verdicts agree, machine/network pair noted
result: skipped
reason: Human-pending by construction — needs a second physical machine on a different network and an operator; no script in this repo can produce it (GATE-5-MEASUREMENT.md's own stated reasoning, re-confirmed). The full operator procedure exists (REMOTE-ROUND-RUNBOOK.md, 189 lines) and deliberately schedules the round AFTER Phase 6 so it exercises commit-reveal + live hints over the real network in one run. This is the phase's one open item; the phase gate stays unticked until it carries real evidence.

### 7. Operator-facing docs complete
expected: GATE-5-MEASUREMENT.md quotes both §10.4 criteria verbatim with honest statuses; REMOTE-ROUND-RUNBOOK.md and LOCALTONET-FALLBACK.md exist; .env-example documents the three env vars with dummy values; phase-5 PRD/PLAN/TODO triplet exists
result: pass
measured: all seven files confirmed on disk. GATE-5-MEASUREMENT.md: both criteria block-quoted verbatim from ROADMAP.md, criterion 1 PASS with evidence link, criterion 2 PENDING with the 7-step procedure. REMOTE-ROUND-RUNBOOK.md 189 lines (machine-B setup, both tunnel paths, digests, evidence retention). LOCALTONET-FALLBACK.md 113 lines, documentation-only (D-57). `.env-example:19-21` carries the three vars with dummy values. No `.env` tracked in git.

### 8. Segal §19.1 Table-5 gate green on whole repo
expected: ruff check → 0 violations; full pytest suite passes with coverage ≥ 85%; every file ≤ 150 code lines; no secrets in source; no LLM imports in strategy
result: pass
measured: `uv run ruff check .` → *All checks passed!* · `uv run pytest tests/ --cov` → **1251 passed, 96.26%** (≥85% required) · `bash scripts/check_line_limit.sh` → clean · `uv run python scripts/check_no_llm_in_strategy.py` → *OK: no forbidden imports* · secret grep over `config/`+`src/` → env-var NAMES only (the only non-doc hits are untracked `__pycache__` binaries containing those same names).

### 9. Adversarial pass on the secret boundary
expected: No vacuous pass — an empty PURSUIT_TUNNEL_SECRET means secret-off, never compare_digest("",""); the 403 body and rejection log never carry the expected value; client and server agree on the header name (case-insensitive match); non-http scopes cannot smuggle past the guard into tool dispatch
result: pass
measured: (a) `resolve_shared_secret` with the env var set to `""` → `None` (secret-off), set to a value → `("X-Pursuit-Secret", value)`, unset → `None` — the empty-string vacuous-pass hole is closed by construction (`if not secret_value`). (b) Live ASGI probe of `SharedSecretMiddleware` (expected=`s3cr3t-value`): exact-case header → 200; lowercase header → 200 (starlette Headers are case-insensitive, so client/server naming can never drift); missing → 403; wrong → 403; empty supplied value → 403. 403 body is `Forbidden` only; rejection log carries remote address + missing/mismatched FACT — leak checks `False` on both. (c) Route enumeration of the FastMCP http_app → exactly one route, `/mcp`, HTTP-only — no WebSocketRoute exists, so the middleware's non-http passthrough (lifespan) has no path to tool dispatch. (d) `config/{police,thief}/tunnel.json` byte-identical (measured), so both sides resolve the same header name.

## Summary

total: 9
passed: 8
issues: 0
pending: 0
skipped: 1

## Gaps

[none — zero implementation gaps. The one skipped test (criterion 2, the genuine remote
round) is a documented human-pending measurement, not a code gap: the code it exercises
(TunnelManager, SharedSecretMiddleware, the exchange-block/opponent-URL seam) is verified
complete, 100%-covered, and criterion 1's real run already proved the whole stack through a
public ngrok URL. Tracked in REMOTE-ROUND-RUNBOOK.md + GATE-5-MEASUREMENT.md; deliberately
scheduled after Phase 6.]

## Standing notes carried forward (not gaps)

1. `agent_entrypoint.py` coverage is 85% at this HEAD (was 100% at 05-VERIFICATION); the
   uncovered lines belong to Phase 6's audit wiring, not Phase 5. Overall gate comfortably
   green at 96.26%.
2. The knowledge graph was refreshed during Phase 5 itself (05-03: 5806 nodes, TunnelManager
   + SharedSecretMiddleware confirmed in the committed GRAPH_REPORT.md). The session banner's
   "2 commits behind" staleness is from post-Phase-6 docs-only commits, out of this phase's
   scope.
