---
status: diagnosed
phase: 05-cloud-exposure-and-tunneling
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-08-13T14:01:37Z
updated: 2026-08-13T14:51:18Z
---

## Current Test

[testing complete — 8/9 pass; test 6 (the genuine remote round) RAN on 2026-08-13 after the
first pass closed, completed a full capture across two machines/networks, and surfaced 5
diagnosed gaps (a 6-agent Opus diagnosis pass, all verdicts CONFIRMED/high). The phase gate
stays UNTICKED per GATE-5-MEASUREMENT.md's own rule until a clean re-run closes criterion 2.]

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

## Summary

total: 9
passed: 8
issues: 1
pending: 0
skipped: 0

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
