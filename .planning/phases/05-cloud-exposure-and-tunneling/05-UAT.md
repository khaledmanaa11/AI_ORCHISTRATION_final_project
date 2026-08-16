---
status: diagnosed
phase: 05-cloud-exposure-and-tunneling
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md,
  05-05-SUMMARY.md, 05-06-SUMMARY.md, 05-07-SUMMARY.md, 05-09-SUMMARY.md,
  05-10-SUMMARY.md, 05-11-SUMMARY.md]
started: 2026-08-13T14:01:37Z
updated: 2026-08-16T16:45:00Z
rounds: 2
---

## Current Test

[testing complete — ROUND 2 (2026-08-16). §10.4 GATE-5 is **MET**: criterion 1 by the
2026-08-09 smoke, criterion 2 by remote-round attempt 4 (two machines, two networks,
agreeing verdicts on both sides, independently re-derived). Round 1's five gaps G1–G5 are
all present in live code with real production callers.

But a 12-agent adversarial pass (6 verifiers, each answered by a skeptic told to REFUTE it)
found **five NEW gaps, G6–G10**, three of them blocker-class and two of them introduced BY
the G1/G2 fixes themselves. Every one was re-confirmed by hand before being written here.
They do NOT reopen the §10.4 gate — they are league-day robustness and honesty defects.
Ready for `/gsd:plan-phase 5 --gaps`.]

## Tests

<!-- Tests 1-9 are ROUND 1 (2026-08-13, against HEAD 384da44). Tests 10-16 are ROUND 2
     (2026-08-16, against HEAD bcc04bf) and re-measure the phase after plans 05-04..05-11
     plus remote-round attempts 3 and 4. -->

### ROUND 1 — 2026-08-13

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
result: issue
reported: "did you see that we already did a live run and it has some bugs?" — operator ran the round 2026-08-13 ≈13:43 UTC (machine A: police, this box, phone hotspot; machine B: thief, Windows 11 laptop, wired ethernet), supplied machine B's logs/ledgers/declarations and machine A's console output (shutdown tracebacks included)
severity: blocker
measured: The round itself WORKED at the transport level — full 5-turn game to a real capture through two ngrok tunnels, commit→ack→reveal every turn, Step-0 declarations exchanged and HMAC-signed, police-side audit matched on self AND peer. Evidence retained at docs/phases/phase-5/remote-round-2026-08-13/. But the criterion's "verdicts agree" clause FAILED: machine B recorded a spurious technical_win{opponent_unresponsive} after its own game_over(capture), the two logs carry DIFFERENT game UIDs (074fc2b16888899e vs d50ceb00be724b93), and the round exposed that the responder never receives hints at all. 5 gaps diagnosed below; criterion 2 stays PENDING until a clean re-run.

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

### ROUND 2 — 2026-08-16, after 05-04..05-11 + remote-round attempts 3 and 4

> Method: every result re-measured against `HEAD = bcc04bf`. Code claims were checked in
> live `src/`, never against a SUMMARY. A 12-agent adversarial pass ran 6 verifiers (one per
> closure claim) each answered by a skeptic instructed to REFUTE the verdict; four skeptics
> landed hits. **Every finding recorded below was then re-confirmed by hand** (grep, source
> read, or a direct probe) before being written here — no agent claim is recorded on trust.

### 10. GATE-5 criterion 2 — the genuine remote round (re-test of Round 1's test 6)
expected: An agent on a remote machine (different network) plays a full round through the tunnel; both logs retained, verdicts AGREE, machine/network pair noted
result: pass
measured: Attempt 4 (2026-08-16 ≈13:29Z, games `b22361aa93ccf310` + `d265603c116a9f99`, A police on phone hotspot ↔ B thief on wired ethernet, both on `0632e04`). **Both machines** end each game `game_over outcome=capture` + `audit_verdict matched=true` (self AND peer, turns 0–5). I re-derived it independently: all 24 ledger `h_commit` values recompute as `sha256(canonical_json(payload))`; each side's six hashes are byte-identical to the commits the *other* side logged receiving; declarations cross-match byte-for-byte; digests recompute. Two agents re-derived the same, one of them adversarially. Attempt 3 (`9c1cf313482719d4`, template-fallback, honestly declared) also completed. Evidence: `docs/phases/phase-5/remote-round-2026-08-16-attempt{3,4}/`. **Caveat recorded as G10, not as a failure.**

### 11. G1 closed — no false accusation on a failed own final-reveal send
expected: A failed OWN final-reveal send records a non-accusatory `audit_incomplete` and leaves the board outcome standing; TECHNICAL_LOSS reserved for a real hash mismatch or an unresolved turn loop
result: issue
reported: "adversarial pass: the branch is unreachable under the slow-failure class"
severity: blocker
measured: The four fixes ARE in live source with real production callers (`run_final_audit(board_outcome=)` at agent_entrypoint.py:110; both `compose_and_send_hint` sites guarded by `outcome is None`; `linger_for_peer` on Table-19 config values with zero literals; the sequenced `late_peer_harness.py` — I confirmed `test_late_peer_teardown.py` passes 2/2 in 35s). **But the headline claim fails for timeout-class send failures** → G6.

### 12. G2 closed — one negotiated game_uid + audit validates peer committed state
expected: The negotiated id governs log/ledger/declaration/committed `state.game_id`; `_audit_one` validates the peer's committed `game_id`/`role`/`turn`; the Round-1 forged-record probe no longer reports "matched"
result: issue
reported: "adversarial pass: fix 1 hands an unvalidated peer string to a set constructor and a filesystem path"
severity: blocker
measured: Fixes 2/3/4 hold and survived attack — `_audit_one` genuinely dereferences `entry.payload.state` (audit.py:140-144 → audit_state.py:103-118), a missing/malformed `state` becomes a named mismatch rather than an exception, and the forged `{game_id: OTHER-GAME, turn: 99, role: police}` record is now rejected on three independent axes. Tests were made MORE faithful, not weakened (`git show 01ff8ed`). **Fix 1 is the problem** → G7.

### 13. G3+G4 closed — inbound hints logged, and hints actually decoded by both sides
expected: Inbound HINT envelopes appear in the wire JSONL; both sides stamp the turn actually played; the responder decodes ≥1 non-`no_hint` hint
result: pass
measured: `turn_hint_buffer.py:147-153` calls `log_received(..., local_turn=ctx.state.turn)` BEFORE the drop guard at :154. Live proof in attempt-4 logs: thief (the responder that decoded **0-of-5** in Round 1) now shows `no_hint` on turn 0 then `outcome: evidence` on turns 1–4 — **4-of-5** — and both sides carry `message_received`+`hint` records (6 thief / 5 police). Tests re-specified not deleted (`git show f32bb3a` removes three from `test_turn_buffer.py` and re-adds all three in `test_hint_freshness.py` with `incoming_hints` assertions added). Two residuals recorded as G8 (not blockers): the live delta is confounded by B's language layer also coming back online, and the send-side stamp fix is scoped to the `commit_reveal: true` branch (the shipped config).

### 14. G5 closed — keyless LLM legible, declared llm_name honest
expected: Startup WARNING when the key is absent; `llm_name` reflects real capability; declaration keeps exactly 10 keys; the key value is never logged
result: pass
measured: **The only closure no skeptic could dent** (`refuted: no`). `has_api_key()` returns a bare `bool` (client.py:28-36) in the one module owning the env-var name; the warning at language_wiring.py:124-137 interpolates only the variable NAME. Confirmed live end-to-end this session: attempt 3 ran keyless and declared `template-fallback (no LLM calls)`; attempt 4 ran with the key and declared `claude-haiku-4-5` — on **both** machines. Declaration still exactly 10 HMAC'd keys.

### 15. 05-09 / 05-10 / 05-11 wired into production
expected: Transport failures contained; malformed peer FINAL_REVEAL is a named mismatch not a crash; 5xx/429 retried while 4xx raises; `ensure_connected()` finally has a production caller
result: issue
reported: "adversarial pass: the peer-data boundary sweep is incomplete — a seventh instance is live at the handshake"
severity: blocker
measured: All three chains are genuinely wired — `RETRYABLE_STATUS_CODES = frozenset({429,500,502,503,504})` is enumerated (501/505 absent, so a deterministic refusal is not retried), and `ensure_connected()` now has its real caller at `tunnel_wiring.py:113`. **But the boundary rule that `audit.py:56-90` declares project-wide is violated three lines away** → G9. Also recorded there: the 05-11 detector may be near-unable to return `False`, and attempt 4 is NOT evidence the repair path works (no drop occurred).

### 16. Segal §19.1 Table-5 gate green on the whole repo
expected: ruff → 0; full suite passes with coverage ≥ 85%; every file ≤ 150 code lines; no secrets in source; no LLM imports in strategy
result: pass
measured: `uv run ruff check .` → *All checks passed!* · `bash scripts/check_line_limit.sh` → clean, exit 0 · `uv run python scripts/check_no_llm_in_strategy.py` → *OK: no forbidden imports* · secret scan over `config/` + `src/` for `sk-ant-`/assigned key literals → **zero hits** · `.env` confirmed **untracked** (`git ls-files --error-unmatch .env` → pathspec does not match) · `uv run pytest tests/ --cov` → **1374 passed, exit 0, 96.54%** (≥85% required). Flake honestly noted: an immediately preceding identical run gave `1373 passed, 1 failed` on `test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`; that test passes 3/3 alone and 1/1 alone under `--cov`, confirming the documented load-sensitive timing flake. An **uncommitted** working-tree change to that file (`perf_counter` → `thread_time` + `@pytest.mark.no_cover`) reduces but does not eliminate it; the budget and the assertion are unchanged, so it is a re-measurement, not a weakening — recorded as G10.

## Summary

total: 16
passed: 12
issues: 4
pending: 0
skipped: 0

<!-- Round 1: 9 tests, 8 pass / 1 issue (G1-G5, all now closed in code).
     Round 2: 7 tests, 4 pass / 3 issues (G6-G9) + G10 filed off test 10/16.
     Round 1's test 6 is superseded by Round 2's test 10, which PASSES. -->

## Phase verdict

**§10.4 GATE-5: MET.** Criterion 1 PASS (2026-08-09 smoke), criterion 2 PASS (attempt 4,
two agreeing verdicts across two machines on two networks, re-derived independently three
times including once adversarially). Round 1's G1–G5 are all present in live code with real
production callers, and G5 survived a dedicated attempt to break it.

**Not "done" in the stronger sense:** G6–G10 below are real, and G6/G7/G9 are league-day
blockers — a foreign peer can kill this process before move 1 (G9), and the two most
expensive failure modes of the 2026-08-13/08-16 rounds are still reachable through a second
door (G6). None of them is a §10.4 criterion, so they do not un-tick the gate; they are the
input to the next plan.

## Gaps

<!-- Diagnosed 2026-08-13 by a 6-agent Opus investigation over the retained remote-round
     evidence (docs/phases/phase-5/remote-round-2026-08-13/). All 6 verdicts CONFIRMED at
     high confidence. Two findings (hint-flow, game-uid) each reproduced by running the
     shipped production functions against the real ledgers. Ordering below is fix-sequence:
     G1 and G2 are the two that break the "verdicts agree" clause criterion 2 needs; G3/G4
     are evidence-integrity; G5 is legibility. Several gaps are pre-existing (present on
     loopback too) — the remote round is what made them visible. -->

- truth: "criterion 2's two sides record AGREEING final verdicts (rules 16/22: no false accusation)"
  status: failed
  reason: "Machine B declared machine A `opponent_unresponsive` (technical_win, retries_attempted 4) AFTER A had already delivered and processed B's final-reveal — A's peer_audit carries B's 5 ledger hashes byte-for-byte. Root cause is a teardown race with two compounding parts: (a) the responder keeps composing+sending a turn-5 hint for ~17s AFTER it already knows the game is over (take_my_turn returns the outcome only after compose_and_send_hint), so the two sides enter the audit phase ~17s apart with no GAME_OVER barrier between them; (b) the side that finishes first (A) runs run_final_audit then `finally: shutdown_cleanly` with ZERO grace — PeerRuntime.stop() hard-cancels the uvicorn task and closes the listen socket (deliberately bypassing graceful shutdown), killing B's still-open FINAL_REVEAL stream; (c) when B's own SEND then fails, run_final_audit converts a failed-to-DELIVER-our-own into Outcome.TECHNICAL_LOSS — but failing to deliver our own reveal is evidence about US, not the peer, and B's log's last game_over still reads `capture` while run_agent returns TECHNICAL_LOSS and main.py exits 1 (the two criterion-2 artifacts contradict each other on one machine)."
  severity: blocker
  test: 6
  root_cause: "Zero-grace hard teardown races a ~17s inter-side stagger; a failed outbound final-reveal SEND is mis-attributed as the PEER being unresponsive."
  artifacts:
    - path: "src/pursuit/network/agent_entrypoint.py:93"
      issue: "`finally: await shutdown_cleanly(ctx)` fires within ms of a matched audit — no linger window for a peer still mid-exchange"
    - path: "src/pursuit/network/peer_runtime.py:168"
      issue: "stop() is task.cancel() + listen_socket.close(), documented as bypassing uvicorn Server.shutdown() — cancels in-flight authenticated peer streams (the two secret_guard.py:75 CancelledError tracebacks in the console are the peer's live session dying)"
    - path: "src/pursuit/network/turn_actions.py:80"
      issue: "responder composes+sends a hint for an already-resolved terminal turn (outcome known at :76, returned at :89) — 17.4s of the 18s divergence in this round"
    - path: "src/pursuit/network/agent_audit_wiring.py:103"
      issue: "run_final_audit converts an audit-transport failure (our own push failing) into TECHNICAL_LOSS even when the turn loop already produced a board outcome"
    - path: "src/pursuit/network/agent_audit_verdict.py:43"
      issue: "record_technical_loss writes only a technical_win event, no corrected game_over — unlike the mismatch path (:93) — so the durable last-outcome record and the exit code disagree"
    - path: "tests/integration/test_step0_and_audit.py:100"
      issue: "both turn loops run in one asyncio.gather over in-memory clients and never call shutdown_cleanly — structurally cannot express a staggered/torn-down peer, which is why no test caught this"
  missing:
    - "run_final_audit: when a board outcome already exists, a failed final-reveal SEND records a non-accusatory audit_incomplete and returns None (leave the board outcome standing); reserve TECHNICAL_LOSS for a real AUDIT_HASH_MISMATCH or a turn loop that never resolved"
    - "skip compose_and_send_hint when the turn already resolved (guard on outcome is None, both branches)"
    - "bounded post-audit linger before teardown, reusing NetworkParams.response_timeout (no new literal); drain/answer inbound FINAL_REVEAL during it"
    - "an integration harness that SEQUENCES the two sides and actually calls shutdown_cleanly, proving a late peer still completes with a matched verdict"

- truth: "all four criterion-2 artifacts (both logs, both ledgers) carry ONE shared, negotiated game_uid so the two machines' logs are joinable (PARAMETERS.md:121-122)"
  status: failed
  reason: "There is no negotiated game id governing anything but two declaration FILENAMES. run_agent mints a local `secrets.token_hex(8)` and freezes log_path=logs/<role>/<uid>.jsonl (and the ledger stem) BEFORE the handshake runs. The handshake DOES exchange each side's proposed game_id, but the only consumer of result.peer_game_id is agent_audit_wiring._declared_game_id, scoped explicitly to the declaration filename only. So both declarations say 074fc2b16888899e (thief adopts peer's) while machine B's log+ledger keep d50ceb00be724b93. The same un-negotiated ctx.game_uid is sealed inside every hashed commit (build_state_record game_id=ctx.game_uid), so the two sides committed DIFFERENT game_ids in the same match — and audit.py never dereferences payload.state at all (it re-hashes the whole payload, which trivially succeeds since the foreign game_id is inside the hash the peer itself computed). CONFIRMED EXPLOITABLE by probe: a forged record claiming {game_id: OTHER-GAME, turn: 99, role: police} is reported 'matched' — because every side publishes all nonces at FINAL_REVEAL, a peer holds the opponent's complete past payloads and can replay the OPPONENT's own commits (role unchecked too). The book's anti-replay step-binding (PRD_commit_reveal.md:121-123's stated reason the state record exists) is not enforced."
  severity: blocker
  test: 6
  root_cause: "The handshake-negotiated game_id is adopted only for the declaration filename; ctx.game_uid (log/ledger stem AND committed state.game_id) stays the process-local random id, and the audit never validates the peer's committed game_id/role/turn against local truth."
  artifacts:
    - path: "src/pursuit/network/agent_entrypoint.py:53"
      issue: "resolved_game_uid = game_uid or secrets.token_hex(8) — always fresh-random per process; frozen into log_path at agent_lifecycle.py:83-88 before perform_handshake at :68"
    - path: "src/pursuit/network/agent_audit_wiring.py:59"
      issue: "_declared_game_id resolves the negotiated id but its own docstring scopes it to declaration_<id>.json only; ctx.game_uid is never updated"
    - path: "src/pursuit/network/turn_commit_ledger.py:68"
      issue: "build_state_record(game_id=ctx.game_uid) hashes the un-negotiated local id into every commit"
    - path: "src/pursuit/security/audit.py:49"
      issue: "_audit_one never reads entry.payload.state — game_id/role/turn inside the committed state are hashed but never validated; state record is write-only (zero production readers of its 5 fields)"
  missing:
    - "adopt the negotiated game_uid in run_agent right after result.agreed and BEFORE run_turn_loop opens the ledger: set ctx.game_uid, rename ctx.log_path to <negotiated>.jsonl (verified safe: only 1 illegal_transition record exists at that moment, ledger file not yet created); pass make_transition_reporter/make_freeze_handler a mutable binding so construction-time wiring survives"
    - "validate the peer's committed state in the audit: state.game_id == negotiated id AND state.role == opponent_role, added to _audit_one BEFORE the move comparison (MUST land WITH the id-adoption fix, never before it — alone it turns every honest round into a mutual technical loss)"
    - "free hardening, ship-independently: assert state.turn == entry.turn inside _audit_one (holds for every honest ledger; closes the replay-across-turns variant)"
    - "an integration test that hands the two sides DELIBERATELY DIFFERENT game_uids (today's harness gives both the same one and cannot fail) and asserts all four artifacts share one stem"

- truth: "inbound HINT envelopes are written to the wire-mirroring JSONL (D-11/D-14), so the log is replayable evidence of what crossed the wire (rule 20)"
  status: failed
  reason: "record_hint (the sole ingestion point for every inbound HINT, all three callers funnel through it) buffers into ctx.pending_hints/ctx.incoming_hints and never calls append_event — HINT is the only MessageType logged on SEND and not on RECEIVE. Proven in the evidence: machine A has 5 message_sent+hint records and ZERO message_received+hint, yet its language_turn records carry the thief's verbatim hint texts with outcome=evidence (the hints arrived, were decoded, drove belief updates — with no durable record they ever crossed the wire). Confirmed nothing downstream breaks: every wire-log consumer (audit observed(), the replay tests, the gate scripts) filters on envelope type before any turn-keyed work, and 'hint' has been an expected sent-type since Phase 4."
  severity: major
  test: 6
  root_cause: "record_hint is the one receive path that never appends an event_log record."
  artifacts:
    - path: "src/pursuit/network/turn_buffer.py:54"
      issue: "record_hint body is two dict assignments (:80-81), no append_event — unlike the reveal path (turn_actions.py:161) and commit path (turn_commit_send.py:97 via log_received)"
    - path: "tests/unit/test_turn_buffer.py:91"
      issue: "positive-path hint tests assert only on ctx.pending_hints, which is WRITE-ONLY in production (never read anywhere in src/); decode reads ctx.incoming_hints — a regression populating the dead buffer would pass the whole suite"
  missing:
    - "split record_hint out to a sibling module (turn_buffer is near the 150-line gate) and, before the late-drop guard, call log_received(...) with the record's own turn == ctx.state.turn and the nested envelope keeping the peer's declared turn (mirror test_audit_turn_binding.py)"
    - "regression test asserting a message_received+hint line lands with correct turn binding; one asserting a LATE hint is still logged though still dropped from both buffers; one asserting observed(direction=message_received) is unchanged by hint records"

- truth: "the language/scent hint channel actually delivers — a responder decodes the hints its opponent sends (Phase 4's whole point)"
  status: failed
  reason: "PRE-EXISTING and present on loopback too; the remote round only made it obvious. The receive-side drop rule turn_buffer.py:78 (`if turn < ctx.state.turn: return`) is structurally unsatisfiable for the responder: a side emits its hint for turn N only at the TAIL of turn N (after REVEAL(N) + an LLM compose), by which point the receiver's maybe_resolve has already advanced its state.turn to N+1 — so N < N+1 and every correctly-stamped inbound hint is discarded before reaching ctx.incoming_hints. The thief decoded 0-of-5 in EVERY game (loopback included); token_spend.calls=0 because decode was skipped, not because B lacked a key. The police decoded thief hints only because of a SECOND bug — the responder mis-stamps its outgoing hint with the post-resolve state.turn (N+1) instead of pending.turn (N), so police reads it 'in the future' and keeps it, decoding one turn stale. CRITICAL: uniform stamping ALONE makes it worse (0-of-10, not 3-of-10) — the drop window must be relaxed AND stamping fixed together."
  severity: major
  test: 6
  root_cause: "The late-hint drop guard is unsatisfiable for the responder given when hints are emitted vs when state.turn advances; compounded by a responder outgoing-stamp that reads state.turn after maybe_resolve advanced it."
  artifacts:
    - path: "src/pursuit/network/turn_buffer.py:78"
      issue: "PRIMARY. `if turn < ctx.state.turn: return` — true for every correctly-stamped inbound hint; necessary+sufficient for the responder's 0-for-5 on loopback and ngrok alike"
    - path: "src/pursuit/network/turn_actions.py:84"
      issue: "responder stamps outgoing hint with ctx.state.turn read AFTER maybe_resolve (:76) advanced it N->N+1; pending.turn (correct, already used for the REVEAL) is in scope — also logs every thief language_turn one turn ahead of the action"
    - path: "tests/unit/test_turn_buffer.py:44"
      issue: "test_record_hint_silently_drops_a_hint_for_an_already_resolved_turn asserts the buggy behaviour as intended — must be re-specified, not deleted"
  missing:
    - "relax the drop window (e.g. keep turn >= ctx.state.turn - 1, or consume latest-per-sender regardless of stamp) AND fix the responder outgoing stamp to pending.turn — together, never separately"
    - "an integration test asserting BOTH sides' outbound hint envelope turn equals the turn being played, and that a two-peer game produces at least one non-no_hint incoming_hint on BOTH sides (the round produced five no_hint in a row on B and no test caught it)"

- truth: "the operator can tell when the LLM is disabled, and the Step-0 declaration honestly reflects it (rule 38)"
  status: failed
  reason: "By-design fallback (Phase 4 sanctioned keyless runs; hint bank is intended no-key behavior) but SILENTLY. Machine B ran claude_api with no key: LLM off is gated only on ANTHROPIC_API_KEY, read in one place, lazily on first call; compose() catches the NO_KEY LlmFailure and returns hint_bank.select(...) on a branch with NO log statement, and there is no logging.basicConfig anywhere so only WARNING+ reaches stderr. The operator was shown `llm_name: claude-haiku-4-5` at startup on a box about to make ZERO calls, because llm_name is a pure echo of config's model_id, never consulting the env/provider/usage. A and B ship byte-identical model config, so their declarations are indistinguishable while A made 8 calls and B made 0. Cosmetic sibling: A's turn-4 hint drifted to third person ('The player is currently positioned...') — the compose prompt describes writing FOR a player rather than AS the player."
  severity: minor
  test: 6
  root_cause: "The key-absent fallback path emits no operator warning, and the declared llm_name reflects config aspiration, not actual capability."
  artifacts:
    - path: "src/pursuit/services/llm/bluff.py:76"
      issue: "the LlmFailure->hint_bank branch has no _log line; _log is used only in the exception arm a returned LlmFailure never reaches"
    - path: "src/pursuit/network/agent_audit_wiring.py:48"
      issue: "llm_name = cfg.language.model.get('model_id', ...) — pure config echo, never checks env/provider/usage; the value is inside the HMAC'd declaration so change the VALUE only, never the field set"
    - path: "src/pursuit/network/language_wiring.py:79"
      issue: "_build_provider constructs AnthropicProvider without probing the env — no startup warning path exists"
  missing:
    - "a presence-only has_api_key() helper (client.py already owns the env-var name) and a startup WARNING from _build_provider when provider is claude_api and the key is absent — probe presence only, never log the value (rule 4)"
    - "gate the declared llm_name: provider=template, or claude_api with no key -> a string that says 'template fallback'; else model_id (keep exactly the 10 declaration keys — it's HMAC'd)"
    - "pin first person in the compose SYSTEM prompt (bluff_prompt.py) and update the STYLE_GUIDE block quoted in PRD_deception.md §6 in the same commit; do NOT add a post-compose person validator (fuzzy, would silently divert good hints to the bank)"

<!-- ===================== ROUND 2 GAPS (2026-08-16, HEAD bcc04bf) =====================
     Found by a 12-agent adversarial pass (6 verify + 6 refute, opus/high). Diagnosis is
     already complete, so root_cause/artifacts/missing are filled here rather than left for
     a diagnosis step. EVERY finding below was re-confirmed by hand before being recorded:
     G6 and G7 by source read, G9 by a direct executable probe, G10 by file comparison.
     Fix order: G9 (cheapest, kills us before move 1) -> G6 -> G7 -> G8 -> G10. -->

- truth: "a failed OWN final-reveal send records a non-accusatory audit_incomplete and never accuses a peer that answered (G1's headline requirement)"
  status: failed
  reason: "G1's fix is correct but UNREACHABLE for the timeout class of send failure. The freeze watchdog is armed across the whole audit (started agent_entrypoint.py:76, stopped only at :134 AFTER run_final_audit returned at :110), and Watchdog.touch() is never called anywhere in the audit path -- I grepped src/ myself: all five touch sites are turn-loop only (turn_buffer.py:103,151; turn_commit_send.py:52,132; turn_commit_wait.py:70), and agent_lifecycle.py:144 states this in its own words. push_final_reveal runs call_with_retry at response_timeout=30 / retry_count=3 / backoff=5, i.e. up to 4x30 + 3x5 = 135s with zero touches, against watchdog_threshold=60. For a peer whose socket accepts TCP but never answers -- a stalled tunnel edge, exactly the failure 05-11 exists for -- the watchdog calls os._exit() at t=60s and record_audit_incomplete (agent_audit_wiring.py:133) at t~135s NEVER RUNS. The log ends on watchdog_incident with no audit_verdict and the peer declares us opponent_unresponsive: the 2026-08-13 artifact reproduced through a second door. The 05-04 authors knew about the no-touch fact -- agent_entrypoint.py:127-129 cites it as why stop_watchdog must precede the linger -- so they protected fix 3 from the watchdog and left fix 1 exposed to it. Separately, the RECEIVE leg still returns record_technical_loss on failure (agent_audit_wiring.py:135-137) and the linger runs only in the finally, AFTER the audit, so it cannot rescue that leg."
  severity: blocker
  test: 11
  root_cause: "The freeze watchdog outlives the turn loop but nothing in the audit path touches it, so any audit-phase retry ladder longer than watchdog_threshold is killed mid-ladder."
  artifacts:
    - path: "src/pursuit/network/agent_entrypoint.py:76,110,134"
      issue: "watchdog armed at :76, run_final_audit at :110, stop_watchdog only at :134 -- the whole audit runs under an untouched watchdog"
    - path: "src/pursuit/network/agent_audit_exchange.py:58-62"
      issue: "push_final_reveal's ladder is up to 135s of wall time with no ctx.watchdog.touch()"
    - path: "src/pursuit/network/agent_audit_wiring.py:133"
      issue: "record_audit_incomplete is unreachable when the ladder outlives watchdog_threshold=60"
    - path: "src/pursuit/network/agent_audit_wiring.py:135-137"
      issue: "the RECEIVE leg still returns record_technical_loss{opponent_unresponsive}; the requirement's 'reserve TECHNICAL_LOSS for a real mismatch or an unresolved turn loop' is unmet on that leg"
    - path: "tests/unit/_fakes_agent.py:24,150 and tests/integration/late_peer_harness.py"
      issue: "the unit fakes force response_timeout=0.05 and start no watchdog; the integration harness deliberately starts no watchdog -- no test can express this window"
  missing:
    - "touch the watchdog around each audit-phase send/receive attempt, OR stop the watchdog before run_final_audit and rely on the audit's own bounded ladders (whichever is decided, it must be one line reachable from run_agent, not a helper without a caller)"
    - "extend the non-accusation rule to the RECEIVE leg: a failed receive with a board outcome standing records audit_incomplete, not technical_win{opponent_unresponsive}"
    - "a test that runs the audit failure path against a REAL watchdog and a REAL 30s-class ladder (the current fakes make the window inexpressible)"

- truth: "the negotiated game id is adopted safely -- a peer cannot use it to crash us, relocate our files, or make us accuse an honest opponent (G2's fix 1)"
  status: failed
  reason: "adopt_negotiated_game_id hands an unvalidated, peer-controlled value into a set constructor and a filesystem path. I read the source to confirm all three: (a) game_identity.py:157-158 builds `{ctx.game_uid, result.peer_game_id}` from a value read with no type check at handshake_evaluate.py:162 -- a peer sending `game_id: {}` or `[]` raises `TypeError: unhashable type` inside a function with no guard, and run_agent's only except is `except ToolError` at :118, so the process dies BEFORE MOVE 1 and we publish no nonces (rule 36 against us). (b) On the thief, negotiated_game_id returns the peer's raw string (game_identity.py:71), and :162-164 builds `ctx.log_path.parent / f'{resolved}{suffix}'` then calls `.replace(target)` -- so `game_id: '../../evil'` relocates our wire log and, because ledger_path derives from log_path.stem, our nonce ledger too, overwriting the destination with no check. (c) `peer_game_id or own_uid` at :71 means a falsy '' leaves the thief on its own uid (re-opening the exact 2026-08-13 split) while :158's `is not None` test still builds `{own_uid, ''}`, which EXCLUDES the peer's real id -- so every honest peer record fails membership at audit_state.py:113-118 and we self-declare TECHNICAL_LOSS against an honest opponent (rules 16/22)."
  severity: blocker
  test: 12
  root_cause: "The G2 fix adopts a peer-controlled string as a hash-set member, a filesystem path component, and an audit membership key, with no type or content validation at any of the three uses."
  artifacts:
    - path: "src/pursuit/network/game_identity.py:157-158"
      issue: "set literal over result.peer_game_id -- TypeError on an unhashable peer value, unguarded"
    - path: "src/pursuit/network/game_identity.py:162-164"
      issue: "peer string becomes a filesystem path component and the target of Path.replace (traversal + silent overwrite); an illegal/over-long name raises an unguarded OSError from the same line"
    - path: "src/pursuit/network/game_identity.py:71"
      issue: "`peer_game_id or own_uid` treats '' as absent while :158 treats it as present -- the two disagree, and the disagreement false-accuses"
    - path: "src/pursuit/network/handshake_evaluate.py:162"
      issue: "peer_game_id is read verbatim; Envelope.from_dict validates the payload only as a dict (envelope.py:98-115), so its values are arbitrary JSON"
  missing:
    - "validate peer_game_id at the handshake boundary as the project's boundary rule requires: a str, non-empty, matching the uid character class, bounded length -- anything else is a named non-agreement, never an exception"
    - "derive the on-disk stem from a sanitised value (or keep our own uid for filenames and store the negotiated id as data only), so no peer string ever reaches a Path"
    - "make :71 and :158 agree on what counts as 'absent' so a falsy id cannot both fall back AND poison the candidate set"
    - "adversarial tests: unhashable game_id, traversal game_id, empty-string game_id, over-long game_id -- each ending in a named outcome, never a traceback"

- truth: "no function that reads peer-controlled data raises -- malformed peer input is always a NAMED MISMATCH (the project's own boundary rule, stated at security/audit.py:56-90)"
  status: failed
  reason: "A seventh instance of the boundary-rule defect is live, three lines from the shape 05-10 fixed, and it kills the process at the HANDSHAKE. config_hash.digests_match raises TypeError on any non-str argument, and both handshake call sites pass peer-controlled values unchecked: handshake_evaluate.py:118 (config, unconditional) and :124-125 (scent, live because agent_entrypoint.py:80,85 always supplies local_scent_digest) sit OUTSIDE the try/except at :151-156, which wraps the DECODE block only -- reading envelope.payload[DIGEST] at :155 is a plain dict lookup that succeeds for an int. I REPRODUCED THIS MYSELF with a direct probe against live source: remote digest int -> TypeError, list -> TypeError, dict -> TypeError; controls stayed contained (a wrong str -> named mismatch, None -> 'digest absent from peer payload'). handshake.py calls evaluate() bare on both halves, and run_agent's only except is ToolError at :118, so the TypeError escapes to main.py and kills us at the handshake with no verdict, no FINAL_REVEAL, no nonces -- rule 36 against us. The exit code is 1, which REMOTE-ROUND-RUNBOOK.md:195-196 teaches the operator to read as 'a technical loss was recorded'; a crash and a recorded loss are indistinguishable in the retained evidence. audit.py:89 says 'A SEVENTH is now a review failure rather than a discovery' -- this is the seventh. Worse, tests/unit/test_config_hash.py:131-135 PINS the crash as intended (`with pytest.raises(TypeError)`), so the suite actively certifies the process kill at the boundary 05-10 claims to close."
  severity: blocker
  test: 15
  root_cause: "05-10 fixed the step0 declaration CONTAINER's type and left the DIGEST's type unchecked in the same corridor; a green test pins the raising contract as correct."
  artifacts:
    - path: "src/pursuit/network/config_hash.py:57-58"
      issue: "digests_match raises TypeError on non-str -- the only raising leaf still reachable from peer data"
    - path: "src/pursuit/network/handshake_evaluate.py:118,124-125"
      issue: "both compare_named_digest calls sit outside the try/except at :151-156"
    - path: "src/pursuit/network/handshake.py:84-87,96,107-110"
      issue: "evaluate() called bare on both halves; :96 documents respond_to_handshake as 'never raises', which the probe disproves"
    - path: "tests/unit/test_config_hash.py:131-135"
      issue: "asserts pytest.raises(TypeError) -- must be RE-SPECIFIED to expect a named mismatch, not deleted"
  missing:
    - "treat a non-str peer digest as a named non-agreement inside compare_named_digest (the same shape as its existing None branch), so digests_match keeps its strict contract for internal callers"
    - "re-specify test_config_hash.py:131-135 to assert the named mismatch; keep a direct digests_match test for the strict internal contract"
    - "extend the boundary-rule comment at audit.py:56-90 with instance 7 and the handshake corridor"

- truth: "the hint channel is correct on every supported path, and the live-round improvement is attributable to the code fix"
  status: failed
  reason: "Two residuals on an otherwise-closed G3/G4. (a) The headline 0-of-5 -> 4-of-5 delta is CONFOUNDED: on 2026-08-13 machine B reported token_spend.calls = 0 on every language_turn record including the compose half, i.e. that machine made zero model calls all round, while in attempt 4 it makes 2/turn. So the delta cannot isolate the code fix from B's language layer coming back online. The unconfounded proofs are the other two: no_hint -> populated buffer, and 6/6 inbound records at env_turn == record_turn - 1, exactly on the window boundary. Worse, turn_hint_buffer.py:37-39 cites that same zero as evidence that 'decode was skipped, not key-starved' -- the zero equally shows compose never called a model, so it does not support the claim it is attached to. (b) The send-side stamp fix covers only the commit_reveal: true branch. turn_actions.py:128 still stamps ctx.state.turn, justified by a comment asserting the initiator's maybe_resolve is a no-op -- true only with commit-reveal ON. With ctx.security.commit_reveal false (a supported, documented toggle) both sides take that branch and the second mover stamps its hint one turn in the FUTURE: the original G4 bug, still live on that path, and the drop guard never fires for a future stamp so it corrupts wire evidence silently. Shipped config is commit_reveal: true, so this is latent, not active."
  severity: minor
  test: 13
  root_cause: "The live-round delta is attributed to the fix without controlling for the responder's LLM coming back online; and the outgoing-stamp fix is branch-scoped while its justifying comment is stated unconditionally."
  artifacts:
    - path: "src/pursuit/network/turn_hint_buffer.py:37-39"
      issue: "derives the lookback constant from a statistic that equally supports the opposite reading"
    - path: "src/pursuit/network/turn_actions.py:121-128"
      issue: "comment claims the initiator's maybe_resolve is always a no-op; false when commit_reveal is off, where the future-stamp bug returns"
    - path: "src/pursuit/network/turn_hint_buffer.py:47"
      issue: "_HINT_LOOKBACK_TURNS = 1 is a source literal absent from docs/PARAMETERS.md -- a Table-5 hardcoded-value risk (CLAUDE.md rule 1), defensible only by the _DECLARE_RETRIES precedent"
  missing:
    - "restate the lookback derivation on the two unconfounded proofs and drop the token_spend argument"
    - "stamp pending.turn on the initiator branch too, or make the comment's precondition explicit and assert it"
    - "either move _HINT_LOOKBACK_TURNS into PARAMETERS.md/config, or record in the phase docs why it is a protocol constant rather than a tunable"

- truth: "the phase's own evidence and trackers describe exactly what happened -- no overclaim (rule 38)"
  status: failed
  reason: "Three documentation defects, all found by the adversarial pass and all re-confirmed by hand. (a) OVERCLAIM, and it is mine from earlier today: GATE-5-MEASUREMENT.md called attempt 4 two games and said the round was 'repeated twice with the live model', which reads as independent replication. I compared the two ledgers move-by-move myself: on BOTH machines game 1 and game 2 are IDENTICAL -- same moves, same positions, same turn-5 barrier, same outcome; only nonces, hashes, uid and hint text differ. That is deterministic-by-design (the seeded tie-break), so game 2 is a second exercise of the TRANSPORT and zero additional gameplay evidence, and the 'per game' doubling of the cross-checks is not two samples. (b) DEAD DECLARATION PATH exposed by that same evidence: strategy/deception.py:73 declare_truthfully() -- its own docstring calls it 'the one constructor for a barrier or capture declaration' for rules 15/16 and 21/22 -- has ZERO production callers; I grepped src/ myself and found only the definition and its own error string. All four DeceptionPlan constructions in the policies hardcode kind=ClaimKind.LOCATION (deception_cop.py:77,83; deception_thief.py:97,103), so ClaimKind.BARRIER/CAPTURE are unreachable and bluff_prompt.py:89,91 plus hintbank_templates.py:115-116 are dead. In both attempt-4 games the police places a barrier on turn 5 and captures on turn 6 while every utterance it makes is an intent:lie LOCATION bluff. docs/RULES.md:41 makes rule 15 a MUST and :52 makes rule 21 a MUST. **RESOLVED 2026-08-16 against the book extract, at plan-phase, BEFORE any code moved — the alarm was mine and it was wrong: there is NO rules violation.** Rule 15's sanction is audit-shaped ('Board forgery and automatic loss AT AUDIT'), and PRD_commit_reveal.md:88-102 (§2.2, D-66/SEC-07) DELIBERATELY moved the barrier off its own envelope into the committed action — the composite {move, barrier} crosses the wire inside REVEAL, is hashed into H_commit and cross-checked at audit (D-67), which the live turn-5 reveal shows. Rules 16/22 punish LYING and 21 punishes DENYING REALITY; none mandates a distinct message type. So `declare_truthfully` is DEAD CODE carrying a docstring that misdescribes the design, not a missing feature, and the binding enforcement is DeceptionPlan.__post_init__ (untouched). One genuine residual remains, and it is a BOOK line rather than a RULES.md line: phase-3/RULES-RESOLUTION.md:51 quotes §3.5 p.22 Table 2 'the cop lands on the thief's cell and declares Capture Claim', while capture today is derived and never announced — compliant as RULES.md is worded, de-riskable with zero new protocol by sending the existing GAME_OVER envelope. Planned as 05-15. (c) TRACKER ROT: docs/phases/phase-5/TODO.md carries DUPLICATE rows with contradictory statuses -- 05-09 at line 21 (done) and line 23 (in progress), 05-10 at line 22 (done) and line 24 (in progress) -- a stale header and a stale 05-08 row both still saying criterion 2 is PENDING, and 05-11 filed out of order."
  severity: major
  test: 10
  root_cause: "Determinism made a re-run look like a replication; the rules-15/21 declaration constructor was written but never wired; the tracker accumulated duplicate rows across parallel executors."
  artifacts:
    - path: "docs/phases/phase-5/GATE-5-MEASUREMENT.md"
      issue: "'repeated it twice with the live model' / 'Two consecutive complete games' imply independent replication of an identical deterministic game"
    - path: "src/pursuit/strategy/deception.py:73"
      issue: "declare_truthfully has zero production callers -- the same dead-code shape as the pre-05-11 ensure_connected()"
    - path: "src/pursuit/strategy/deception_cop.py:77,83 and deception_thief.py:97,103"
      issue: "every DeceptionPlan hardcodes ClaimKind.LOCATION, so no barrier/capture declaration can ever be generated"
    - path: "docs/phases/phase-5/TODO.md:19,21,22,23,24"
      issue: "duplicate 05-09/05-10 rows with contradictory statuses; stale header and 05-08 row"
  missing:
    - "correct the GATE-5 narrative to say the second game is a deterministic re-run exercising the transport, not an independent sample (DONE in this pass)"
    - "de-duplicate and de-stale docs/phases/phase-5/TODO.md (DONE in this pass)"
    - "DONE at plan-phase: the rules question was settled against docs/RULES.md + PRD_commit_reveal.md §2.2 -- rules 15/16 are already satisfied by the committed action, so no declaration needs wiring; see 05-15-PLAN.md must_haves for the quoted rule text"
    - "remove (or explicitly reserve) the dead declare_truthfully + unreachable BARRIER/CAPTURE templates and prompt branches, and fix the docstring that misdescribes the design -- 05-15 task 1"
    - "append a dated superseded-by note to PRD_mcp_transport.md:65, which still calls receive_barrier 'the cop's barrier declaration' -- 05-15 task 2"
    - "de-risk the capture Claim by sending the existing GAME_OVER envelope on the capturing turn, driven by the resolved outcome so it cannot disagree with the ledger -- 05-15 task 3"

## Standing notes carried forward (not gaps)

1. The `illegal_transition handshake->handshake` on line 1 of both logs is the known-benign
   symmetric-handshake artifact (state_machine.py:71 recoverable allow-list) — NOT a gap.
2. Machine B's `games_played_so_far: 8` vs A's `173` are both honest per-role counters
   (games_played.json). Flagged only because rule 38 is the absolute-DQ rule for that field:
   never hand-edit or reset those counters while touching the fallback-marker code.
3. Two console traceback classes on A after game end are cosmetic Windows/asyncio teardown
   noise (WinError 995 from the proactor accept task; the uvicorn lifespan CancelledError) —
   already documented for the smoke script, extend to the real agent. The TWO ASGI
   CancelledErrors through secret_guard.py:75 are NOT cosmetic — they are the peer's live
   session being cancelled and are part of G1.
4. Durability checked: event_log.append_event, CommitLedger.append, durable_write_json are
   all synchronous write→flush→fsync→close with no await — no cancellation can eat a record;
   game-log writes never happen inside the cancelled server task (tool handlers only enqueue).
5. `agent_entrypoint.py` coverage is 85% at this HEAD (was 100% at 05-VERIFICATION); the
   uncovered lines belong to Phase 6's audit wiring, not Phase 5. Overall gate green at 96.26%.
