---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: PHASE 5 PLAN 04 EXECUTED (2026-08-14) -- G1 CLOSED ON THE CODE SIDE. The 2026-08-13 remote round's false accusation is now structurally impossible: run_final_audit takes the turn loop's board_outcome (wired at agent_entrypoint.py:101, FROM run_turn_loop at :91 -- the production wiring, not a dead branch), a failed OUTBOUND push with a board outcome standing writes one non-accusatory EventType.AUDIT_INCOMPLETE record naming OUR OWN send and FALLS THROUGH to the receive+audit steps instead of returning TECHNICAL_LOSS (rules 16/22 -- machine A's peer_audit carried machine B's five ledger hashes byte-for-byte at the exact moment B declared A unresponsive). All three genuine sanctions survive, each with a paired fairness control: no board outcome -> TECHNICAL_LOSS, a peer withholding its nonces (rule 36) -> TECHNICAL_LOSS, a genuine AUDIT_HASH_MISMATCH (D-67) -> TECHNICAL_LOSS, and the except ToolError branch stays accusatory on purpose (06-06). record_technical_loss now appends a CORRECTED game_over so the log's last outcome and main.py's exit code can never disagree; record_audit_verdict's mismatch tail DELEGATES to it rather than keeping a second copy. New sibling agent_teardown.linger_for_peer (64/150) is the bounded post-audit grace window -- total cap NetworkParams.response_timeout, quiet interval NetworkParams.backoff_seconds (Table 19 rows 6 and 3), ZERO numeric literals in the module and ZERO new keys in any config/*/network.json; watchdog_threshold deliberately not borrowed. shutdown_cleanly split into stop_watchdog/stop_runtime and KEPT as their composition; run_agent stops the watchdog BEFORE the linger (NET-07: touch() appears nowhere in the audit path -- PRE-EXISTING, FOUND here not introduced here -- and the freeze action is os._exit(1)) and the runtime AFTER it inside a try/finally (CancelledError is a BaseException; the three-bare-statement shape provably leaks the bound port). Capture mechanism: option (b), module-level helpers, so the unit order list and the integration harness name the SAME three steps. Task 3 shipped the first two-peer harness in this repo that binds REAL loopback sockets, SEQUENCES the two sides and actually tears down (tests/integration/late_peer_harness.py + test_late_peer_teardown.py) -- the in-memory Client(server) transport makes runtime.stop() a no-op, which is structurally why nothing caught this. Revert probes all recorded verbatim in the SUMMARY: Task 1 case 1 fails pre-fix on the substantive assertion (old code really returned TECHNICAL_LOSS for our own failed send) while controls 2 and 4 were already green; Task 2's cancellation test fails against three bare statements (order[-1] == 'linger_for_peer', stop_runtime never ran); Task 3's linger=False probe raises httpx.ConnectError out of B's run_final_audit so B ends with NO verdict at all -- the 2026-08-13 artifact reproduced on loopback -- and the reverse probe (linger=True) fails too, so the harness genuinely distinguishes the shapes. Measured: full suite 1262 passed / 96.30% coverage (baseline 1251 / 96.26%), ruff 0, line-limit exit 0, check_no_llm_in_strategy OK, GATE-6 re-run twice with all three book Sec10.4 criteria PASS (evidence JSON differs in exactly 3 timestamp lines, every verdict field byte-identical; restored so the diff stays code-only). Linger cost measured on a clean loopback game: dev_launch 17.44/17.64 s exit 0 with both sides recording audit_verdict matched=true, vs 14.4-14.7 s exit 1 without -- +2.8 to +3.0 s for the pair against a 5 s per-side quiet interval. ONE DEFERRED FINDING, logged not fixed (.planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md #1): httpx.ConnectError escapes call_with_retry (RETRYABLE_TRANSPORT_ERRORS is exactly (McpError, DeadlineExpired), no catch-all by design) and KILLS the process on teardown, making US the side that published no nonces (rule 36). Pre-existing, measured 4/4 runs, closed on loopback by the linger but not in general; deadline.py is outside this plan's files and 06-06 affirmed its no-retry contract, so the fix needs its own plan -- route it to record_audit_incomplete, never to a technical win. Knowledge graph refreshed (05-96: 6827 nodes / 12372 edges / 429 communities). agent_lifecycle.py now 144/150 and tests/unit/test_agent_entrypoint.py 142/150 -- no headroom left in either. NOTHING TICKED in ROADMAP.md (standing convention); docs/phases/phase-5/TODO.md row 05-04 marked in-progress with the three commit hashes. NEXT -- plan/execute 05-05 (negotiated game_uid, G2), then 05-06 (G3+G4 hint flow + the 17.4 s responder stagger), 05-07 (G5), then 05-08 (human remote round attempt 2, the only thing that can close GATE-5 criterion 2). PRIOR: PHASE 6 CLOSED -- gate met, UAT 11/11, and ALL FOUR security findings from the two adversarial audits fixed: plan 06-05 (audit join key bound to local turn truth; caught mismatch made durable) and plan 06-06 (peer ToolError contained so it can no longer kill us before FINAL_REVEAL, rule 36; inbound envelope.sender validated, handshake exempt by design). Final measured state: full suite 1251 passed / 0 failed, 99.29% coverage, ruff 0, line-limit exit 0, GATE-6 re-run with all three Sec10.4 criteria PASS. deferred-items.md #1-#2 remain open by design (logging-granularity gap with equivalent evidence; correct rule-37 counter behaviour) -- neither a gate criterion. NEXT: plan Phase 7. PRIOR: (/gsd:verify-work 6, 2026-08-09) -- 9/11 UAT tests pass on evidence re-measured this session at HEAD=b3655348; tests 8 and 9 are ISSUES. A 5-lens adversarial audit found the mutual audit's join key is the peer's own declared envelope.turn, which nothing validates -- turn-skew converts every D-67 forgery into a benign "trailing commit" AND empties the rule-36 coverage intersection, reopening the empty-{"records": []} evasion; separately, a caught mismatch never reaches a durable outcome record (game_over is written before the audit and never corrected; main.py discards the overridden outcome). Both reproduced by hand against the shipped functions with paired controls. Detail in 06-UAT.md Gaps (measure_gate6.py re-run exit 0, all three Sec10.4 criteria PASS, evidence JSON differs from the committed one in exactly 3 timestamp lines with every verdict field byte-identical; full suite 1226 passed + the known load-sensitive timing flake re-confirmed passing in isolation at 0.18s; coverage 99.33%; ruff 0; line-limit exit 0; no-llm-in-strategy OK; security.json pair diff-confirmed byte-identical; 13 Phase-6 proof tests re-run green). ROADMAP.md Phase 6 + docs/phases/phase-6/TODO.md + root docs/TODO.md all ticked; graph refreshed at verify-work (6577 nodes / 11972 edges / 413 communities). UAT record: .planning/phases/06-security-and-cryptography/06-UAT.md. NEXT -- plan Phase 7 (reporting-and-visualization-shell). PRIOR: PHASE 6 PLAN 04 EXECUTED (216eec4, 2026-08-09) -- GATE-6 measured, all three Sec10.4 criteria PASS with real localhost evidence, zero env vars (scripts/measure_gate6.py + 6 gate6_*.py helpers), docs/PRD_commit_reveal.md written, GATE-6-MEASUREMENT.md written, knowledge graph refreshed (06-96). PHASE 6 IS NOW CODE+TEST+GATE COMPLETE (4 of 4 plans) and GOAL-VERIFIED (06-VERIFICATION.md status passed, 11/11 must_haves, gsd-verifier 2026-08-09) -- verify-work (triplet/ROADMAP ticking) still pending per house convention. Full suite 1226 passed / 1 pre-existing timing flake (confirmed passing in isolation) -- 1227 when the flake doesn't fire, matching the baseline exactly -- 96.27% coverage, ruff/line-limit/no-llm-in-strategy all clean. Two minor, non-blocking, out-of-scope findings logged (not fixed) in .planning/phases/06-security-and-cryptography/deferred-items.md (FINAL_REVEAL envelope-logging symmetry gap in agent_audit_exchange.py from 06-03; the measurement-vs-league games_played.json counter distinction). NEXT -- /gsd:verify-work 6 (tick ROADMAP.md Phase 6 + docs/phases/phase-6/TODO.md, confirm the phase triplet), then Phase 7 (reporting-and-visualization-shell) planning.
last_updated: "2026-08-14T12:55:00.000Z"
last_activity: 2026-08-14 -- Phase 05 plan 04 executed (05-04: G1 gap closure -- verdict honesty + bounded teardown grace, wave 1, depends_on []). Task 1 (8f35721, fix): EventType.AUDIT_INCOMPLETE added additively exactly as AUDIT_VERDICT was (stable field set untouched); agent_audit_verdict.record_audit_incomplete reuses _verdict_record, the field assembly _technical_win_record now also calls -- one copy, two event types -- and carries the ladder's genuinely measured attempts/timeout/elapsed/last_error with a reason constant (_OWN_SEND_FAILED) deliberately NOT added to TechnicalWinReason, because the record is not a technical win and its subject is our own send; record_technical_loss appends the corrected game_over and record_audit_verdict's mismatch tail delegates to it; run_final_audit(ctx, *, board_outcome) with the four-way control flow; agent_entrypoint.py:101 passes board_outcome=outcome from run_turn_loop at :91 with an explicit comment on why the sibling except ToolError branch must STAY accusatory; test_step0_and_audit._run_audit_and_merge threads both outcomes so the tamper sibling and the four gate6_*.py scripts inherit the production shape unchanged; test_agent_audit_wiring.py's two cases re-specified (not loosened) as the board_outcome-is-None branch. Task 2 (6fd4fb9, feat): agent_teardown.py, linger_for_peer pulling through deadline.wait_for_opponent so deadline._bounded stays the ONE asyncio.wait_for site (QUAL-02), clock injected as a DI seam; agent_lifecycle gains stop_watchdog/stop_runtime with shutdown_cleanly kept as their COMPOSITION (its only remaining callers are three test files); run_agent's finally is stop_watchdog -> try linger finally stop_runtime. Task 3 (142c4b4, test): late_peer_harness.py + test_late_peer_teardown.py, real loopback sockets via test_secret_channel's own _free_port/_wait_until_accepting (imported, not re-copied), A audits then performs run_agent's three steps while B arrives late; the non-vacuity probe PINNED as a permanent second test asserting the durable property ("B's own push did not land") rather than today's exception type, so it survives the deferred ConnectError fix. Three Rule-2 test-strength additions beyond the plan's literal text, all documented. 05-04-SUMMARY.md written; self-check PASSED (17 files + 3 hashes verified, one line-number citation corrected by re-measurement rather than carried over). PRIOR (2026-08-09) -- Phase 06 plan 04 executed (06-04: GATE-6 measurement + docs, wave 4 of 4, depends on 06-03 -- the LAST plan in Phase 6). Task 1 (77eafff): scripts/measure_gate6.py + 6 gate6_*.py helper modules (gate6_common/gate6_clean_game/gate6_declarations/gate6_tamper/gate6_step0/gate6_report, each under the 150-code-line house limit, mirroring the gate4_*/gate5_* precedent -- scripts/ is outside the coverage gate but the limit is still honored by hand). Reuses the SAME real two-peer harness 06-03's own tests already use (tests/integration/test_step0_and_audit.py's _play_to_turn_loop_end/_run_audit_and_merge, imported directly -- the ALREADY-established sibling-test-import precedent test_step0_and_audit_tamper.py itself uses) rather than the plan's own stale key_link (two_peer_game.py's play_two_peer_game cannot carry the Step-0 params 06-03 added). Criterion 1 (clean game): commit/ack/reveal counted 5/5/5 both sides, zero nonce occurrences in either wire-mirroring JSONL against 5 nonce-bearing ledger records per side, the D-58 both-locked-gate ordering holding with zero violations, both declaration files present and predating first move content, an honest barrier count (1 this run, not forced). Criterion 2 (tamper): both D-67 tamper classes re-run live -- (a) corrupted ledger payload fails the re-hash check, caught on both sides' own self-audit too; (b) THE D-67 case, hash/payload untouched (independently re-verified) but the observed action differs, caught by check 3 alone. Criterion 3 (Step-0): a live digest forgery, evaluated through the real respond_to_handshake against a real default_context-built AgentContext (not a full two-server round trip, since a forged digest is only detectable from the RECEIVING side's own evaluation -- documented in gate6_step0.py's own docstring) -- HandshakeOutcome.STEP0_MISMATCH fires, State.ERROR, move 1 confirmed unreachable via an explicit post-abort machine.attempt(State.MY_TURN) call. All three criteria PASS, evidence in docs/phases/phase-6/gate6_measurement_evidence.json; script confirmed idempotent across two consecutive runs, zero env vars set (ANTHROPIC_API_KEY explicitly cleared, mirroring the test suite's own monkeypatch.delenv). Task 2 (1de0dcf): docs/PRD_commit_reveal.md, mirroring docs/PRD_mcp_transport.md's house structure exactly -- mechanism/scope with the SEC-01..08 requirements table (grep-confirmed all eight IDs present), topology/design (D-58 four phases + initiator/responder asymmetry, D-59/D-66 composite action dict + hash recipe, D-64 nonce ledger, D-62/D-63 Step-0 two-layer verification, D-67 audit design), interfaces copied verbatim from the 06-01/02/03 SUMMARY files, out-of-scope future-phase extensions, parameters traced to 06-PLAN-OUTLINE.md Sec2. Task 3 (216eec4): docs/phases/phase-6/GATE-6-MEASUREMENT.md (the three Sec10.4 criteria quoted verbatim, one section per criterion with method/run-command/what-a-PASS-looks-like/measured evidence, every claim pointing at a named evidence-JSON field; two honest findings documented rather than smoothed over -- FINAL_REVEAL is not itself logged as a message_sent/message_received envelope record, audit_verdict is the correct evidence instead; measurement games advance the real games_played.json counter, same as 06-03's own pytest runs) + knowledge graph refresh (06-96: graphify update ., 6510 nodes/11909 edges/408 communities, built at commit 1de0dcf7, graph.html skipped over the 5000-node viz limit matching the 04-12/05-03 precedent -- gitignored regardless, only the committed GRAPH_REPORT.md moved, 566 lines changed, git diff --stat confirms a real change). Two minor, non-blocking findings logged (not fixed, out of this plan's scope per the SCOPE BOUNDARY rule) in .planning/phases/06-security-and-cryptography/deferred-items.md. All 3 tasks committed atomically, pre-commit hook passing every time, never bypassed. Full suite re-measured: 1226 passed / 1 pre-existing timing flake (test_belief_policy.py's own per-turn-budget test, confirmed passing in isolation, 0.22s, unrelated to this plan) -- 96.27% coverage, ruff/line-limit/no-llm-in-strategy all clean. 06-04-SUMMARY.md written. Self-check PASSED (all 11 files + 3 commit hashes verified present). NOTHING TICKED anywhere -- ROADMAP.md Phase 6 checkboxes and docs/phases/phase-6/TODO.md left unchecked, per this project's own standing convention (05-03/06-01/06-02/06-03 all did the same) -- that is /gsd:verify-work 6's job. PHASE 6 IS NOW FULLY CODE+TEST+GATE COMPLETE. PRIOR (2026-08-09) -- Phase 06 plan 03 executed (06-03: Step-0 + Final-Reveal mutual audit, wave 3 of 4, depends on 06-02). Task 1 (54048e3): uv add psutil; step0_collect.py's collect_declaration gathers the full book Sec5.5 field set (OS/CPU/RAM via platform+psutil, GPU best-effort via nvidia-smi subprocess with an honest not-detected on any failure, LLM name/code version/team code/games-played-so-far, exact git commit hash via subprocess, raising loudly on failure) plus read_games_played/record_game_played over durable_write's crash-safe pair (rule 37/38); step0_sign.py's digest_declaration/sign_declaration/verify_declaration (D-62 -- digest always, HMAC only when a shared secret exists, explicit signed:false never silently verified). Task 2 (7bb130b): HandshakeKey.STEP0_DIGEST/GAME_ID extend build_offer's payload the same omit-dont-null way SCENT_DIGEST does; HandshakeOutcome.STEP0_MISMATCH aborts before move 1 via the SAME State.ERROR seam (state_machine.py untouched); HandshakeResult.peer_game_id read unconditionally (D-61). A REAL DESIGN CORRECTION (Rule 1) made here: the plan's own literal text specified comparing local vs remote step0 digest for EQUALITY via compare_named_digest, mirroring SCENT_DIGEST -- but a Step-0 declaration is inherently per-agent (digests role among other fields), so two different roles' declarations can never hash equal; implementing this literally would abort EVERY real two-role game the instant both sides opt in. Fixed: _step0_present() checks PRESENCE only, matching rule 24's actual failure mode (Step-0 never ran on the peer's side). test_handshake_step0.py's own load-bearing D-61 test uses deliberately different local_game_id values on both sides, proving negotiation genuinely resolves to the initiator's value. Task 3 (ed48ee4): audit.py's audit_peer_records/AuditRecord/all_matched -- three ordered checks per turn (observed commit present, re-hash matches H_commit, revealed action equals what THIS side actually saw played in-game); TechnicalWinReason.AUDIT_HASH_MISMATCH and EventType.AUDIT_VERDICT added (both additive). Unit tests prove BOTH D-67 tamper classes distinctly: a flipped payload field fails the hash check, and -- the D-67 case itself -- hash/payload left completely untouched (independently confirmed still verifies) but the claimed action differs from what was actually played, caught by check 3 alone. Task 4 (be75519): agent_audit_wiring.py (declare_step0/write_declaration/run_final_audit) + agent_audit_exchange.py (a THIRD sibling, pre-authorized: FINAL_REVEAL push/receive via the existing call_with_retry ladder, observed-history extraction from the wire log, verdict recording reusing the EXISTING TechnicalWin dataclass, never a parallel verdict type) wired into agent_entrypoint.run_agent's three new call sites -- stays a thin caller. agent_lifecycle.py ALSO needed editing (Rule 3, not pre-authorized in this plan's files list): default_context had to thread local_step0_digest/local_game_id into make_handshake_responder, the SAME seam local_scent_digest already uses, or Step-0 would never reach the real inbound responder path. tests/unit/test_agent_entrypoint.py fixed for the new call-site fallout (Rule 3). games_played.json gitignored (mutable per-role runtime counter, not fixed config). Full real two-peer integration proof: declaration files land on both sides sharing the game_id BEFORE any move content is logged, a clean game's audit_verdict record shows matched:true on both sides, and BOTH D-67 tamper classes are caught live -- corrupting police's own ledger payload makes thief's audit fail (AND police's own self-audit also fails, symmetric honesty proven, not just asserted) while corrupting only what thief itself observed played in-game (ledger/hash left genuinely untouched, independently confirmed) fails via check 3 specifically, proving the hash-only bypass is genuinely closed. Rule-2 coverage-closing tests added for every new module's untested branch (agent_audit_exchange.py/agent_audit_wiring.py/step0_collect.py all reach 100%). All 4 tasks committed atomically, pre-commit hook passing every time, never bypassed. 06-03-SUMMARY.md written carrying the declaration filename convention, HandshakeResult.peer_game_id contract, and the AuditRecord shape verbatim for 06-04. Self-check PASSED (all 13 files + 4 commit hashes verified present). NOTHING TICKED anywhere -- ROADMAP.md Phase 6 checkboxes left unchecked, docs/phases/phase-6/TODO.md not yet created. Knowledge graph refresh (06-96) still pending -- not run this plan. handshake_evaluate.py (149/150) and agent_wiring.py (146/150) now have essentially no line-count margin left, flagged for 06-04. FOLLOW-UP (10f3a26, coordinator-directed post-review): the presence-only digest fix left step0_sign.verify_declaration with ZERO production callers -- only the digest crossed the wire, so a peer sending any 64-char string passed Step-0. Closed: HandshakeKey.STEP0_DECLARATION (a fifth, opt-in payload key) now carries the FULL published declaration (book Sec5.5 -- there is no secrecy reason to withhold OS/CPU/RAM/GPU/model/code-version/commit-hash); handshake_step0.py (new sibling -- handshake_evaluate.py had zero line-count room left, now sits EXACTLY at 150/150) verifies the peer's content against its own claimed digest (+ HMAC when both sides hold the shared secret) via step0_sign.verify_declaration whenever the peer opts in to send it. A digest-only peer (an opponent's own implementation we cannot force to publish content) still agrees; a declaration mutated AFTER its digest was computed aborts before move 1 with a non-accusing report. HandshakeResult gains peer_step0_declaration (read unconditionally); write_declaration also persists the peer's own declaration (declaration_<game_id>_peer.json) for Phase-7 auditability. agent_lifecycle.py's default_context now resolves the shared secret ONCE and reuses the same tuple for both PeerRuntime's middleware and the responder's Step-0 verification. 4 new tests (content matches digest agrees; content tampered after its digest was computed aborts before move 1, house style checked against accusing language; digest-only peer still agrees; HMAC mismatch on a wrong local secret also aborts) plus the integration harness now threads real declaration content end to end and asserts the peer file is persisted. grep confirms verify_declaration now has exactly one production call site. Full suite re-measured: 1222 passed, 96.26% coverage. 06-03-SUMMARY.md updated to describe the exchange-and-verify design, superseding its presence-only-only description. FOLLOW-UP 2 (4ac475a, coordinator-directed post-review): all_matched([]) is vacuously True and audit_peer_records only ever audited entries the PEER chose to include -- nothing checked that peer_records COVERED the turns actually watched played, so an opponent sending FINAL_REVEAL {"records": []} (the cheapest possible rule-36 evasion) passed the mutual audit and kept its board outcome; run_final_audit had no coverage check anywhere. Closed: audit_peer_records now requires every turn present in BOTH observed_commits AND observed_reveals (fully exchanged -- committed AND revealed in-game) to appear in peer_records; a missing turn is a named mismatch. The SAME change fixed a real false-accusation bug in the opposite direction: a turn with an observed commit but no observed reveal is a legitimately TRAILING turn (CommitLedger.append runs BEFORE the REVEAL send, so an honest peer's own final reveal can contain a committed-never-revealed entry from an abnormal ending) -- now matched=True once commit+hash check out, never misbranded a forger. A genuinely turn-less game stays vacuously matched. No caller-side change needed; the self-audit direction gets identical semantics automatically. handshake_evaluate.py confirmed untouched (git diff empty), per the coordinator's own constraint. Tests: omitting one fully-exchanged turn mismatches exactly that turn; sending empty records while N turns were observed produces N mismatches (the evasion closed); an honest trailing commit-without-reveal is now matched=True (the false-accusation case fixed); a real two-peer integration case truncates one turn out of one side's ledger before the Final-Reveal exchange and confirms the other side's audit reports AUDIT_HASH_MISMATCH and Outcome.TECHNICAL_LOSS. Full suite re-measured: 1227 passed, 96.27% coverage. 06-03-SUMMARY.md updated again to describe the coverage check and the trailing-commit fairness fix.
progress:
  total_phases: 8
  completed_phases: 4
  total_plans: 61
  completed_plans: 43
  percent: 33
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-27)

**Core value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.
**Current focus:** Phase 05 gap closure (05-04 done, 05-05..05-08 open) — the 2026-08-13 remote round exposed five gaps; GATE-5 criterion 2 stays PENDING until they land and attempt 2 runs. Phase 07 waits.

## Current Position

Phase: 05 (cloud-exposure-and-tunneling) — **IN PROGRESS, gap closure.**
  4 of 8 plans executed (05-01..05-03 + 05-04). 05-04 closed G1 on the code
  side (see .planning/phases/05-cloud-exposure-and-tunneling/05-04-SUMMARY.md
  and the frontmatter `stopped_at`/`last_activity` above for the full
  task-by-task account, every revert probe recorded verbatim, and the one
  deferred finding). Measured at that plan's end: full suite 1262 passed /
  96.30% coverage, ruff 0, line-limit exit 0, no-llm-in-strategy OK, GATE-6
  re-run with all three book Sec10.4 criteria PASS, knowledge graph refreshed
  (6827 nodes / 12372 edges / 429 communities).
  STILL OPEN in this phase: 05-05 (G2 — one negotiated game id across log,
  ledger, declaration AND the committed state.game_id, plus an audit that
  validates the peer's committed role/turn), 05-06 (G3+G4 — inbound HINTs on
  the wire log; the relaxed receive window and the responder pending.turn
  stamp landing TOGETHER; no hint composed for an already-resolved turn, which
  is the other 17.4 s half of G1's stagger), 05-07 (G5 — keyless LLM made
  legible), 05-08 (HUMAN-RUN remote round attempt 2, the only thing that can
  close GATE-5 criterion 2).
  ONE DEFERRED ITEM opened by 05-04, not fixed by design:
  .planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md #1 —
  httpx.ConnectError escapes call_with_retry and kills the process on
  teardown, making US the side that published no nonces (rule 36).
  Pre-existing, measured, closed on loopback by 05-04's linger but not in
  general; needs its own plan because deadline.py's no-retry contract was
  affirmed in 06-06.

## Prior Position (Phase 6, retained)

Phase: 06 (security-and-cryptography) — **CLOSED.** 5 of 5 plans executed
  (06-01..06-04 + the 06-05 gap closure); all three §10.4 criteria measured
  PASS and RE-measured after the fix; UAT 11/11.
  (See .planning/phases/06-security-and-cryptography/06-04-SUMMARY.md.
  06-04 measures GATE-6 (book Sec10.4 milestone 6) end to end via
  `uv run python scripts/measure_gate6.py` -- all three criteria PASS
  with real, localhost-only, zero-env-var evidence
  (docs/phases/phase-6/gate6_measurement_evidence.json), writes
  docs/phases/phase-6/GATE-6-MEASUREMENT.md and docs/PRD_commit_reveal.md,
  and refreshes the knowledge graph (06-96).
  /gsd:verify-work 6 RAN 2026-08-09: 11/11 UAT tests pass on evidence
  RE-MEASURED this session at HEAD=b3655348, never copied from the SUMMARY
  files -- measure_gate6.py re-run (exit 0, all three criteria PASS, evidence
  JSON differs from the committed one in exactly 3 timestamp lines, every
  verdict field byte-identical); full suite 1226 passed + the known
  load-sensitive timing flake (test_belief_policy.py's per-turn-budget test,
  re-confirmed passing in isolation in 0.18s); coverage 99.33%; ruff 0
  violations; check_line_limit.sh exit 0; check_no_llm_in_strategy.py OK;
  security.json pair diff-confirmed byte-identical; the 13 Phase-6 proof
  tests (barrier round-trip, toggle-off byte-equivalence, audit coverage,
  Step-0 declaration tamper, all three tamper classes) re-run green.
  Plan rows ticked in ROADMAP.md / docs/phases/phase-6/TODO.md / root
  docs/TODO.md; knowledge graph refreshed again at verify-work (6577 nodes /
  11972 edges / 413 communities). UAT record:
  .planning/phases/06-security-and-cryptography/06-UAT.md.

  A 5-lens adversarial security audit (vacuous-pass, dead-verification,
  protocol-bypass, honesty-rules, secret-leakage) was run over the shipped
  Phase-6 code during verify-work, each lens's findings attacked by an
  independent skeptic. ALL FIVE lenses converged independently on the same
  root cause and all five skeptics failed to refute it; it was then
  reproduced by hand against the shipped functions with paired controls:

  GAP 1 (BLOCKER) -- the mutual audit's join key is attacker-controlled.
  agent_audit_exchange.observed():78 keys BOTH observed_commits and
  observed_reveals on envelope.get(TURN), the peer's own declared turn
  number. Nothing in src/ ever compares an inbound envelope's turn to
  ctx.state.turn (grep for `.turn ==` / `envelope.turn` returns only sites
  that CONSUME it as a key; all four D-58 waits in turn_commit_wait.py
  match on MessageType + payload h_commit only). A peer that stamps its
  COMMIT and REVEAL envelopes with disjoint turns empties
  audit.py:82's `set(commits) & set(reveals)` -- killing the rule-36
  coverage check -- and sends every entry down audit.py:62's
  `turn not in observed_reveals` trailing-commit exemption, which returns
  matched=True. Reproduced: commit A / play B / stamp the REVEAL turn=1001
  gives all_matched=True ("trailing commit ... hash verified") where honest
  stamping correctly gives "revealed action does not match what was
  actually played (D-67)"; and 3 fully-exchanged turns + `{"records": []}`
  gives all_matched=True with 0 records where honest stamping gives 3
  "absent from final reveal" mismatches. Cheapest variant stamps everything
  turn=0, so ONE valid record satisfies an N-turn game's audit and N-1
  nonces stay secret forever. Every existing test hard-codes matching keys
  in both dicts, so none can see this.

  GAP 2 (MAJOR) -- a caught mismatch is not durable. game_over_record has
  exactly one call site (orchestrator.py:105) INSIDE run_turn_loop, so the
  JSONL's only outcome-bearing line is written with the board outcome
  BEFORE run_final_audit runs (agent_entrypoint.py:73-77); it is never
  corrected. run_agent's overridden Outcome.TECHNICAL_LOSS is then
  discarded by main.py:51 (`asyncio.run(...)`, then unconditional
  `return 0`). A Phase-7 reporter reading the outcome field reads the
  cheater's win.

  BOTH CLOSED by plan 06-05 (2026-08-09): log_received takes a required
  local_turn; wait_for_opponent_commit takes the responder's pre-resolve
  turn; await_opponent_turn captures ctx.state.turn BEFORE maybe_resolve
  advances it; observed() keys both dicts on the record's own top-level
  turn (the nested envelope is stored unchanged, so the peer's claimed
  turn survives as evidence). security/audit.py deliberately NOT modified
  -- its checks were correct and were being fed attacker-controlled keys.
  The in-game rejection of a disagreeing turn stamp was considered and
  DECLINED: local-keying already closes both paths, and rejecting risks a
  false accusation (rules 16/22), the same trap as 06-03's Step-0
  digest-equality check; recorded in docs/PRD_commit_reveal.md Sec2.6.1.
  record_audit_verdict appends a corrected game_over; main.py maps
  TECHNICAL_LOSS to a non-zero exit. Two 150-line splits
  (turn_commit_ledger.py, agent_audit_verdict.py), the first of which also
  removed a real duplicated ledger_path definition; turn_actions.py's
  inline technical-win block was a byte-for-byte copy of
  turn_commit_send.technical_loss and became the call. Proven by
  tests/unit/test_audit_turn_binding.py (5 cases whose two observed dicts
  DISAGREE, incl. an honest-peer fairness control), tamper (e), and
  test_outcome_durability.py; non-vacuous by revert-probe (4 of 5 fail
  against pre-fix code, the 5th being the fairness control). Full suite
  1238 passed / 99.38% coverage; GATE-6 re-measured, all three PASS.

  ALSO CLOSED, by plan 06-06 (2026-08-09): deferred-items.md #3-#4.
  (#3) An uncaught ToolError escaped call_with_retry and killed the agent
  mid-game AFTER its ledger append but BEFORE any FINAL_REVEAL, making US
  the side that published no nonces (rule 36) -- and since tools.py itself
  raises ToolError at the peer for a malformed envelope, two honest copies
  of this codebase would have killed each other. run_turn_loop and the
  audit boundary now catch it and route it through the existing
  technical-loss pathway (TechnicalWinReason.PEER_PROTOCOL_ERROR,
  additive; peer_protocol_verdict measures elapsed_seconds genuinely).
  deadline.py NOT changed -- its no-retry contract is correct, the defect
  was the missing catch. Premise proven with a REAL FastMCP round trip
  against a hostile tool body before the fix was written.
  (#4) tools.py::_accept took `sender` off the wire and enqueued it, so a
  peer stamping OUR role landed in our own turn-buffer half where
  maybe_resolve can never fire (a silent stall). Every game-message
  handler now rejects a non-opponent sender with the same descriptive
  ToolError a malformed envelope gets, enqueuing nothing; expected_sender
  threads from agent_lifecycle and defaults to None so no existing caller
  changed. The handshake tool is DELIBERATELY exempt (it negotiates the
  peer's role) with its own test. orchestrator.opponent_role is the single
  definition of the role literals, beside engine_agent.
  Measured with both fixes live: full suite 1251 passed / 0 failed
  (the timing flake did not even fire), coverage 99.29%, GATE-6 re-run
  with all three criteria PASS. Honest play never trips the sender check.

  deferred-items.md #1-#2 remain open BY DESIGN: #1 FINAL_REVEAL is not
  itself an envelope record (equivalent evidence exists via audit_verdict);
  #2 measurement runs advance the real games_played.json counter (correct
  rule-37 behaviour). Neither affects a Sec10.4 criterion.

  NEXT: plan Phase 7 (reporting-and-visualization-shell).)
Plan: 4 of 4 (06-01, 06-02, 06-03, 06-04 all done -- Phase 6 complete)

Phase 05 (cloud-exposure-and-tunneling) status carried forward unchanged:
  EXECUTED, NOT VERIFIED (all 3 plans code+test complete). GATE-5 (book
  Sec10.4 milestone 5) still has TWO human-pending items before
  /gsd:verify-work 5 can run: (1) the smoke run
  (`uv run python scripts/gate5_tunnel_smoke.py`, needs NGROK_AUTHTOKEN/
  PURSUIT_NGROK_DOMAIN/PURSUIT_TUNNEL_SECRET, absent on this machine) and
  (2) the genuine remote round (CLOUD-02, needs a second machine on a
  different network -- full procedure in
  docs/phases/phase-5/GATE-5-MEASUREMENT.md). Per CLAUDE.md's autonomy
  directive, Phase 6 proceeds ahead of GATE-5's human-pending items since
  Phase 6 depends on Phase 5's shipped CODE, not on GATE-5's measurement.

06-04 delivered: GATE-6 (book Sec10.4 milestone 6) measured end to end,
  all three criteria PASS with real, localhost-only, zero-env-var
  evidence -- closing Phase 6. scripts/measure_gate6.py + 6 gate6_*.py
  helper modules (each under the 150-code-line house limit, mirroring
  the gate4_*/gate5_* precedent), reusing the SAME real two-peer harness
  06-03's own tests already use (tests/integration/test_step0_and_audit.py's
  _play_to_turn_loop_end/_run_audit_and_merge, imported directly --
  the ALREADY-established sibling-test-import precedent
  test_step0_and_audit_tamper.py itself uses) rather than the plan's own
  stale key_link (two_peer_game.py's play_two_peer_game cannot carry the
  Step-0 params 06-03 added). Criterion 1: one clean game shows
  commit/ack/reveal counted 5/5/5 both sides, zero nonce occurrences in
  either wire-mirroring JSONL against 5 nonce-bearing ledger records per
  side, the D-58 both-locked-gate ordering holding with zero violations,
  both declaration files present and predating first move content, an
  honest barrier count (1, not forced). Criterion 2: both D-67 tamper
  classes re-run live end to end through the script itself -- a corrupted
  ledger payload fails the re-hash check (caught on both sides' own
  self-audit too); THE D-67 case -- hash/payload untouched, independently
  re-verified, but the observed action differs -- caught by the
  revealed-vs-played cross-check alone. Criterion 3: a live Step-0 digest
  forgery evaluated through the real respond_to_handshake against a real
  default_context-built AgentContext (not a full two-server round trip --
  a forged digest is only detectable from the RECEIVING side's own
  evaluation, D-62's per-agent design) -- HandshakeOutcome.STEP0_MISMATCH
  fires, State.ERROR, move 1 confirmed unreachable via an explicit
  post-abort machine.attempt(State.MY_TURN) call, run_turn_loop never
  called. docs/PRD_commit_reveal.md mirrors docs/PRD_mcp_transport.md's
  house structure exactly, all eight SEC-01..08 IDs present (grep-
  confirmed). docs/phases/phase-6/GATE-6-MEASUREMENT.md quotes the three
  criteria verbatim with method/evidence/PASS per criterion, and honestly
  documents two findings rather than smoothing them over: FINAL_REVEAL is
  not itself logged as a message_sent/message_received envelope record
  (audit_verdict is the correct evidence instead); measurement games
  advance the real games_played.json counter (same as 06-03's own pytest
  runs). Knowledge graph refreshed (06-96: 6510 nodes/11909 edges/408
  communities, GRAPH_REPORT.md moved 566 lines, graph.html skipped over
  the 5000-node viz limit matching the 04-12/05-03 precedent). Two minor,
  non-blocking findings logged, not fixed (out of this plan's scope), in
  .planning/phases/06-security-and-cryptography/deferred-items.md. All 3
  tasks committed atomically. Full suite re-measured: 1226 passed / 1
  pre-existing timing flake (confirmed passing in isolation, unrelated),
  96.27% coverage, ruff/line-limit/no-llm-in-strategy all clean. Nothing
  ticked anywhere -- that is /gsd:verify-work 6's job.

06-01 delivered: src/pursuit/security/ (new package, 100% covered) --
  commit_pack.py (build_commit_payload/commit/verify_reveal, D-59: the ONE
  payload-builder both commit and audit-time re-hash call, never rebuilt ad
  hoc; SHA-256 via the reused config_hash.canonical_json, secrets.token_hex(16)
  nonce generated inside commit() only, digests_match/secrets.compare_digest
  for verification; move stays completely shape-opaque so 06-02's composite
  {move,barrier} action dict passes through untested-but-untouched -- proven
  by a round-trip test using both a move-only and a barrier-bearing example,
  including a nested-"barrier"-key-only tamper case), state_record.py
  (build_state_record, D-60's exact five-field set with a local non-bool-int
  guard mirroring envelope.py's own), ledger.py (CommitLedger.append/read_all,
  D-64's fsync durability mirroring event_log.append_event exactly, nonce
  never on any wire-mirroring log). src/pursuit/shared/security_config.py
  (SecurityKey/SecurityParams/load_security_config, the 11th per-agent config
  block) + config/{police,thief}/security.json (byte-identical, commit_reveal
  default true + team_code khm-mn17, D-65). See frontmatter last_activity for
  the full task-by-task account. 34 new tests, security/ package 100%
  coverage (77/77 statements). Full suite 1150 passed, 1 pre-existing timing
  flake (isolated re-run confirms it passes; unrelated to this plan, not
  touched), 95.81% coverage, ruff/line-limit/no-llm-in-strategy all clean.
  Knowledge graph refreshed (6035 nodes/10756 edges/384 communities). Nothing
  ticked anywhere. Purely additive -- zero wiring into turn_actions.py,
  handshake, or any existing network file (that is 06-02/06-03's scope).

06-03 delivered: Step-0 declaration auto-collect+sign (D-63/D-62) and the
  D-67 Final-Reveal mutual audit, both wired live into run_agent.
  src/pursuit/security/step0_collect.py (collect_declaration -- full book
  Sec5.5 field set, platform+psutil for OS/CPU/RAM, best-effort nvidia-smi
  for GPU with an honest not-detected on any failure, git rev-parse HEAD
  for the commit hash raising loudly on failure; read_games_played/
  record_game_played over durable_write's crash-safe pair, rule 37/38) +
  step0_sign.py (digest_declaration/sign_declaration/verify_declaration --
  digest always, HMAC only when a shared secret exists, explicit
  signed:false never silently verified). src/pursuit/security/audit.py
  (audit_peer_records/AuditRecord/all_matched -- D-67's three ordered
  checks: observed commit present, re-hash matches H_commit, revealed
  action equals what THIS side actually saw played in-game; the SAME
  function also runs as the symmetric self-check). Handshake gains a third
  digest slot (HandshakeKey.STEP0_DIGEST/GAME_ID, HandshakeOutcome.
  STEP0_MISMATCH, HandshakeResult.peer_game_id) -- state_machine.py
  untouched. A REAL DESIGN CORRECTION found and fixed (Rule 1): the plan's
  own literal text specified an EQUALITY comparison for step0 (mirroring
  SCENT_DIGEST), which would abort every real two-role game the instant
  both sides opt in, since a Step-0 declaration is inherently per-agent
  (digests role among other fields) -- corrected to a PRESENCE check,
  documented prominently in source and the SUMMARY. src/pursuit/network/
  agent_audit_wiring.py (declare_step0/write_declaration/run_final_audit)
  + agent_audit_exchange.py (a THIRD sibling, pre-authorized: FINAL_REVEAL
  push/receive, observed-history extraction, verdict recording reusing the
  EXISTING TechnicalWin dataclass) wired into agent_entrypoint.run_agent's
  three new call sites -- stays a thin caller. agent_lifecycle.py ALSO
  needed editing (Rule 3, not pre-authorized in this plan's files list):
  default_context threads local_step0_digest/local_game_id into
  make_handshake_responder, the same seam local_scent_digest already uses.
  Full real two-peer integration proof: declaration files land on both
  sides sharing the game_id BEFORE any move content is logged, a clean
  game's audit_verdict shows matched:true on both sides, and BOTH D-67
  tamper classes are caught live (a corrupted ledger payload fails the
  OTHER side's audit AND the tampering side's own self-audit; corrupting
  only what the other side actually observed played in-game -- ledger/hash
  independently confirmed still verifying -- fails via check 3 alone,
  proving the hash-only bypass is genuinely closed). Rule-2 coverage-
  closing tests close every new module to 100%. Full suite 1218 passed
  (+34 vs the 1184 baseline), 1 pre-existing timing flake (unrelated,
  confirmed passes in isolation), 96.24% coverage (+0.17pp), ruff/line-
  limit/no-llm-in-strategy all clean. Knowledge graph refresh (06-96)
  still pending -- not run this plan. Nothing ticked anywhere.
  handshake_evaluate.py (149/150) and agent_wiring.py (146/150) now have
  essentially no remaining line-count margin, flagged for 06-04.

06-02 delivered: the D-58 both-locked Commit-Ack-Reveal exchange, wired
  live into the turn loop for both roles, plus D-66/SEC-07's barrier-over-
  the-wire. src/pursuit/network/envelope.py (MessageType gains COMMIT/ACK/
  REVEAL/FINAL_REVEAL, nine members) + tools.py (four matching handlers).
  agent_context.py (new, split from orchestrator.py/agent_lifecycle.py at
  the 150-line gate) + commit_state.py (new, PendingAction/CommitTurnState)
  -- AgentContext.security: SecurityParams (required) + commit_state:
  CommitTurnState (defaulted). turn_commit.py + turn_commit_wait.py +
  turn_commit_send.py (a THIRD sibling forced by the line count, mirroring
  handshake.py's own 3-file split) -- initiate/await_and_respond/
  reveal_pending, the three D-58 entry points; turn_language.py's
  choose_destination stashes Decision.barrier; turn_resolve.py's
  record_action gains an optional barrier plus a new shape-aware
  decode_revealed_action. A REAL MEASURED DEADLOCK found and fixed (Rule 1):
  the plan's own literal unconditional await_and_respond spec hung a real
  two-peer game 136.00s (retry-ladder exhaustion into a false technical
  loss) before a ctx.role branch fixed it -- police (the fixed first-mover,
  design note 7) already committed+revealed its own action inside
  initiate() by the time its own await_opponent_turn runs, so it must only
  WAIT for the opponent's REVEAL, never decide again; re-measured 1.15s.
  PendingAction carries 3 fields beyond the plan's literal 5-field sketch
  (action_payload, h_commit, turn) since ctx.state advances past
  resolve_turn before reveal_pending runs. Proven end to end on REAL
  two-peer games (test_commit_reveal_protocol.py + _barrier + _jitter,
  split at the 150-line gate): commit/ack/reveal types present, zero
  move-typed envelopes, zero nonce text in the wire log, a matching ledger
  record count, the both-locked-gate ordering itself, a forced barrier
  round-tripping identically on both engines (quota respected), toggle-off
  byte-equivalence, duplicate-ACK jitter tolerance. test_gate4.py's
  _moves()/intent-order check and test_language_pipeline.py's inline
  check/_replay_from_log fixed exactly per the plan's own
  critical_correctness_3 spec (split into test_language_pipeline_replay.py);
  the identity-based intent-before-text check verified via a throwaway
  probe to still catch a real violation. Rule-2 coverage-closing tests for
  every new technical-loss branch this plan's source introduced
  (test_turn_commit_initiate_failures.py, test_turn_commit_respond_
  failures.py, test_turn_resolve.py) plus a shared FailAfterClient test
  fake. Full suite 1184 passed, 1 pre-existing timing flake (isolated
  re-run confirms it passes; unrelated, not touched), 96.07% coverage
  (+0.26pp over the pre-plan baseline), ruff/line-limit/no-llm-in-strategy
  all clean. Knowledge graph refresh (06-96) still pending -- not run this
  plan. Nothing ticked anywhere. game_id/game_uid reconciliation (D-61)
  still open, flagged for 06-03; FINAL_REVEAL's wire type/tool handler
  exist but carry no body yet (06-03's job).

05-03 delivered: scripts/gate5_tunnel_smoke.py (env-gated smoke script
  driving the REAL TunnelManager/SharedSecretMiddleware through a public
  ngrok URL, JSON evidence writer) + scripts/gate5_smoke_checks.py (the
  offline-testable core) + docs/phases/phase-5/GATE-5-MEASUREMENT.md (both
  Sec10.4 criteria PENDING, honestly, with exact procedures) +
  docs/phases/phase-5/LOCALTONET-FALLBACK.md (D-57, zero code) + graph
  refresh (05-96). See frontmatter last_activity for the full account.
  Full suite 1116 passed, 95.70% coverage, ruff/line-limit/no-llm-in-strategy
  all clean. Nothing ticked anywhere.

05-02 delivered: src/pursuit/network/secret_guard.py
  (SharedSecretMiddleware -- pure ASGI callable, secrets.compare_digest,
  403 before any FastMCP session/tool dispatch, rejection logged by fact
  only never the value; build_middleware()/client_headers() factories);
  PeerRuntime gains shared_secret=(header_name, value) -- _run_http() wires
  middleware=build_middleware(...) into the SAME run_async() call that
  already passes sockets= (D-57 comment on host_origin_protection staying
  off sits there), client() ALWAYS builds an explicit
  StreamableHttpTransport (never a bare URL string) carrying
  ngrok-skip-browser-warning unconditionally plus the secret header when
  configured; src/pursuit/network/secret_wiring.py (new) --
  resolve_shared_secret(config_dir), the factory-function seam
  agent_lifecycle.default_context calls (landed in a new module, not
  agent_wiring.py -- Rule 3 deviation, agent_wiring.py had no room at
  135/150 lines); tests/integration/test_secret_channel.py proves all
  three cases over REAL loopback sockets (correct secret succeeds, missing
  header gets a plain-text 403 proving it never reached MCP routing, wrong
  secret fails on two independent attempts). .env-example gains
  NGROK_AUTHTOKEN/PURSUIT_NGROK_DOMAIN/PURSUIT_TUNNEL_SECRET.
  Full suite 1105 passed (+18), 95.70% coverage (+0.06pp),
  ruff/line-limit/no-llm-in-strategy all clean.

05-01 delivered: pyngrok>=8.1.2 (D-54, uv add, never ngrok-python --
  requires-python >=3.12 vs this project's 3.11.9);
  config/{police,thief}/tunnel.json (byte-identical, five string fields --
  provider/secret_header/authtoken_env/domain_env/secret_env -- zero
  numeric leaf, D-55) + src/pursuit/shared/tunnel_config.py
  (TunnelKey/TunnelParams/load_tunnel_config/require_env, the Phase-4
  *Key-beside-loader convention); src/pursuit/network/tunnel_manager.py
  (TunnelManager -- start/healthy/ensure_connected/stop, every pyngrok
  call (connect/disconnect/kill/get_process) plus sleep/clock injected,
  real pyngrok defaults bound in one place, matching Gatekeeper/Watchdog's
  DI style; reconnect to the SAME domain bounded by NetworkParams'
  existing retry_count/backoff_seconds, zero new numbers);
  src/pursuit/network/tunnel_wiring.py (build_tunnel_manager -- tunnel-off
  unless the static-domain env var is set, the structural default every
  existing test/dev flow relies on; exchange_block -- the paste-ready
  URL+secret-env-NAME block, never a value; run_with_tunnel -- start
  before/stop after, a start failure aborts before the wrapped body runs
  at all) + src/pursuit/network/agent_entrypoint.py (run_agent moved out
  of agent_lifecycle.py wholesale, wrapped in run_with_tunnel, once
  wrapping it in place would have pushed agent_lifecycle.py -- already AT
  its 150-code-line ceiling -- over the gate; agent_lifecycle.py resolves
  run_agent back lazily via PEP 562 __getattr__, the same
  one-directional-dependency fix orchestrator.py/turn_actions.py already
  proved). Existing lifecycle tests (test_agent_lifecycle.py,
  test_agent_lifecycle_resilience.py) pass byte-unmodified. Full suite
  1087 passed (+36 vs the 1051 baseline), 95.64% coverage (+0.43pp),
  ruff/line-limit/no-llm-in-strategy all clean. ROADMAP.md's Phase 5 row
  updated programmatically (gsd-tools roadmap update-plan-progress: 1/3
  plans, In Progress).

<!-- The narrative below this line is Phase 4 history, retained deliberately. -->

04-14 delivered: scripts/measure_gate4.py + 7 helper modules (gate4_games,
  gate4_beliefspy, gate4_scent, gate4_mockprovider, gate4_fixtures,
  gate4_report, gate4_runner) -- a seeded two-peer GATE-4 runner reusing
  04-12's tests/integration/two_peer_game.play_two_peer_game (RESUME.md
  carry-over W) rather than hand-rolling a second harness. --mocked (the
  default, no key, reproducible: two runs with GATE4_SEEDS = (30260801,
  30260802, 30260803) produce byte-identical criterion numbers, verified
  by diff) feeds tests/fixtures/hints_{en,he}.json's own recorded
  responses through a provider that never touches a network; --live
  refuses to attempt ANYTHING when ANTHROPIC_API_KEY is absent, verified
  by actually invoking it and confirming zero network calls plus a clean
  PENDING JSON. Criterion 1 (hint -> inference) is measured by spying
  BeliefAdapter.decide -- the real, UNMODIFIED method -- reading
  self.belief.posterior() before/after each call (22/136 turns carried
  evidence, mean L1 posterior shift 1.171 on exactly those turns).
  Criterion 2 (scent decay, locked) drives the shipped ScentField/scent.py
  with the loaded scent.json directly (max deviation 1.11e-16 from the
  closed form over 12 turns) since 04-12 never logs a per-turn scent
  snapshot to the JSONL, plus a real scent_digest() comparison (both
  peers hash to c0e6322..., matching 04-01/RESUME.md's own wave-1 record).
  Criterion 3 (hint every turn) reads the police-side JSONL directly:
  68/68 turns carried a hint, max 11 words (limit 15), both intents
  occurred (55 lie / 13 truth), zero outgoing coordinate leaks across
  hint text AND move payloads, intent-before-text proven STRUCTURALLY
  (compose_outgoing requires plan.intent as a positional argument, so no
  call can exist without it) rather than by a log timestamp the JSONL
  does not carry. docs/phases/phase-4/GATE-4-MEASUREMENT.md quotes all
  three ROADMAP.md criteria verbatim with these numbers and PASS
  verdicts, reports decode-fixture accuracy 1.0/1.0 EN/HE (explicitly
  labelled a re-validation-logic check, not a live-model proof), and
  reports the belief-on/off comparison HONESTLY: measured 1.0 vs 0.0 cop
  win rate does NOT match Outline Sec1's "no gain" prediction, and the
  doc explains why rather than smoothing it over -- belief.enabled=false's
  own fallback path (turn_language.py, pre-dating D-48/D-43) hands the
  raw brain the omniscient TRUE opponent cell, not a blind one, so the
  comparison is confounded and the honesty clause's actual claim was not
  cleanly tested. tests/integration/test_gate4.py freezes the structural
  absolutes (handshake digest match, hint every turn + zero coordinates,
  intent-before-text via a live call-order spy) as 3 mocked, no-key,
  no-network tests; empirically verified via a throwaway (discarded)
  probe that silencing one side's hint channel trips the exact assertion
  this suite makes. NOTHING TICKED anywhere. Full suite 1051 passed
  (1048 + 3), 95.21% coverage, ruff/line-limit/no-llm-in-strategy all
  clean.

04-13 delivered: docs/phases/phase-4/RULES-RESOLUTION-LANG.md (both sides of
  the Sec5.3.2 per-turn-Reveal vs Sec6.4 blindness contradiction, quoted with
  book+PDF pages VERIFIED DIRECTLY against police_thief_p2p.pdf this session
  -- pages 5/50-53/62-64 read via the Read tool, not re-copied from a prior
  extract unchecked; D-48's four reasons, D-49's rule-23 argument, an 18-row
  BOOK/NEGOTIATED/DERIVED table); docs/PRD_{scent_map,belief_map,deception}.md
  (three per-mechanism PRDs, every number traced to a plan SUMMARY -- the
  shipped scent digest verbatim, the reliability trajectory and Sec4.4
  0.9->0.81 reproduction, both role lie-rate curves, the D-39 style guide
  verbatim; PRD_belief_map.md states the Regime-A honesty clause in plain
  words and records D-51 as a DISCLOSED REVISION of D-40, not an extension);
  docs/phases/phase-4/{PRD,PLAN,TODO}.md (the phase triplet, PLAN.md
  references 04-PLAN-OUTLINE.md Sec2 for D-32..D-53 rather than copying it,
  TODO.md states its row-ID = plan-ID namespace convention explicitly);
  docs/STRATEGY.md's three TBD - Phase 4 rows filled (TBD - Phase 3 rows
  untouched); .planning/ROADMAP.md's Phase 4 plan list replaced with the
  real fourteen (was four stale placeholder rows), plans-complete corrected
  6/14 -> 13/14; knowledge graph refreshed (5320 nodes/9778 edges/333
  communities) with a PROGRAMMATIC layering check against graph.json's raw
  edges (not the rendered report): zero edges services/llm<->strategy in
  either direction, corroborating scripts/check_no_llm_in_strategy.py
  independently. Zero source/config/test files touched (docs-only plan);
  full suite re-confirmed byte-identical: 1048 passed, 95.21% coverage,
  ruff/line-limit/no-llm-in-strategy all clean. NOTHING TICKED anywhere --
  every ROADMAP checkbox and every phase-4 TODO status stayed unticked
  (half-circle for executed-not-verified work, empty box for 04-14/04-99);
  /gsd:verify-work 4 ticks, after 04-14 measures GATE-4.

04-12 delivered: the real Figure-7 pipeline (book Sec6.2) wired live into
  network/turn_actions.py's take_my_turn/await_opponent_turn -- decode the
  opponent's last-revealed hint -> choose the move (BeliefAdapter.decide()
  when belief.enabled, else the raw brain, else first_legal_move) ->
  buffer + resolve -> send the direction-token move -> plan the claim
  AFTER the move (so it can reference what was actually committed to) ->
  compose -> send the hint; 04-04's PLACEHOLDER_HINT_TEXT is gone (grep
  confirms). agent_lifecycle.default_context now builds a REAL registry
  brain (BeliefAdapter-wrapped when enabled), one ScentField per role, and
  one LanguageRuntime (gatekeeper + provider + HintBank + deception RNG)
  per process/game -- the first plan in the project that wires Phase 3's
  strategy and Phase 4's language layer into the actual live two-process
  turn loop (every prior phase only exercised them via direct engine
  calls or single-sided injected tests). D-48's regime decision
  (known_opponent_cell) lives in one place, logged per turn via new
  turn_events.language_turn_record (regime, belief entropy/argmax,
  reliability, token spend, incoming/outgoing hint). The live handshake
  now sends a real local_scent_digest (closes 04-02's carry-over 1).
  [Rule 1 - Bug] A real two-peer CONCURRENT game (tests/integration/
  two_peer_game.py, never run before this plan) found 04-04's own
  "late hint"/"duplicate hint" HintProtocolError checks turning ordinary
  network/processing jitter into a spurious TECHNICAL_LOSS -- fixed: a
  late hint drops silently, a duplicate overwrites, only await_move's
  separate two-hints-no-move liveness cap still raises. Four full
  two-peer degradation games (no key, all calls failing, budget
  exhausted, silent peer) all finish correctly scored; measured per-turn
  wall time 37ms/turn language-ON vs 18ms/turn OFF against a 60s
  watchdog_threshold. Full gates green: 1048 passed, 95.21% coverage,
  ruff/line-limit/no-llm-in-strategy all clean. Knowledge graph refreshed
  (5221 nodes / 9687 edges / 336 communities; graph.html skipped this
  pass, over graphify's 5000-node HTML limit).

04-11 delivered: strategy/beliefadapter.py (BeliefAdapter -- Figure 7's
  per-turn order: observe -> predict -> update(scent) -> update(hint) ->
  sample -> decide; Option A believed-state substitution via
  dataclasses.replace; D-43 samples the target cell, never argmax),
  shared/belief_toggle_config.py (BeliefToggleParams: enabled/seed, a null
  seed derives + logs a fallback rather than being non-deterministic),
  registry.build_brain(..., belief_config=, scent_model=) wiring the
  adapter in behind belief.enabled with zero impact on existing
  3-positional callers. Regime A identity proven exactly (boxed-in
  fixture, holds for any RNG draw); Regime B proven to differ from truth
  only in the opponent's coordinate. target_cell is no longer vestigial:
  same true state + different belief -> different Decision. Per-turn
  decision time measured with belief enabled: cop max 4.99ms, thief max
  ~3.7-4.99ms, against a 50ms budget. valuebrain.py/matrix.py/features.py/
  equilibrium.py untouched (git diff --stat empty on all four). Full gates
  green: 1020 passed, 94.94% coverage, ruff/line-limit/no-llm-in-strategy
  all clean. Issue found (not a regression): tests/integration/
  test_beats_baseline.py, named in the plan's own verification block,
  does not exist -- deleted in Phase 3's run-2 rebuild (commit f3d9847),
  before this session. test_strategy_pluggable.py confirmed present,
  passing, and byte-unmodified.

04-10 delivered: services/llm/wordcount.py (count()/truncate(), one
  whitespace-splitting rule), services/llm/hintbank.py +
  hintbank_templates.py (HintBank, a seeded per-game template bank keyed
  by ClaimKind/Intent, import-time validated against the REAL shipped
  language.json word limit), services/llm/bluff.py + bluff_prompt.py
  (BluffContext + compose(), the total 5-step hint composer: one call,
  one retry on overflow, truncate, assert_no_coordinates, bank fallback
  on every failure path; D-39's style guide never reveals `intent` to the
  model, D-36). Deviation: the word limit's config home is language.json's
  model group (not deception.json as the plan's files_modified listed) --
  reasoning in 04-10-SUMMARY.md, RESUME.md carry-over A closed / J opened.
  assert_no_coordinates moved network/hint_payload.py -> new
  shared/hint_guard.py (re-exported), matching 04-08's Intent precedent.
  Full gates green: 1001 passed, 94.81% coverage, ruff/line-limit/
  no-llm-in-strategy all clean. Knowledge graph refreshed this session
  (4917 nodes / 8593 edges / 311 communities).

04-09 delivered: strategy/scent_check.py (contradicts(), the Sec4.4 lie
  detector reproducing the book's 0.9 -> 0.81 worked example exactly),
  strategy/reliability.py (Reliability, a bounded [r_min, r_max] adaptive
  coefficient, D-51 — a disclosed revision of D-40's "fixed" framing),
  strategy/belief_hint.py (hint_likelihood(), the D-40 Bayes mix weighted
  well below scent and never zeroing a cell), plus two new belief.json
  config groups (reliability, hint_likelihood). End-to-end Sec4.4
  reproduction measured and committed: a fully-lying opponent's reliability
  collapses 0.5 -> 0.2 -> 0.05 (r_min) within two turns; a fully-truthful
  one holds at 0.5 for all ten; both regimes' fused-posterior argmax
  tracks the real scent trail, not the claim. Full gates green: 903
  passed, 94.55% coverage, ruff/line-limit/no-llm-in-strategy all clean.

<!-- The narrative below this line is Phase 3 history, retained deliberately: it
     records why the run-2 architecture exists. It is NOT the current position. -->

  completion but FAILED GATE-4 for both roles on real, measured evidence (see
  docs/phases/phase-3/RUN-1-POSTMORTEM.md) — no bar was lowered, no table was promoted.
  That diagnosis plus a 3-agent literature review produced D-09-superseded (distance is
  the wrong objective for both roles; cop-win iff the thief's free component is a
  forest) and a validated 15-plan run-2 build order (03-11..03-25, 7 waves, RL demoted
  from mover to a ~60-weight linear evaluator under alpha-beta search, D-26). Wave 1's
  first plan, **03-11 (graph primitives), is fully executed**: `pursuit.strategy.graph`
  (components/cycles/territory — free_cells, neighbors, component_of, degree,
  edge_count, articulation_points, cycle_rank, is_forest, reduction_value,
  voronoi_split, territory_diff), 3 tasks + 1 coverage-gap fix, 4 commits
  (12be2e4/52c85f2/b4b06fa/af5f0de), 100% package coverage. Wave 1's second plan,
  **03-12 (thief safety rule -- never step into N[cop]), is now also fully executed**:
  `src/pursuit/strategy/safety.py` (`closed_neighbourhood`/`safe_moves`, D-31's measured
  296/300=0.987 vs 283/300=0.943 free win, pure/D-03, never-empty guarantee) wired into
  `fallback.py::_evade` (filter-then-rank, `_pursue` untouched) and guarded by a
  non-vacuous 160-game regression test, 2 commits (71b201d/20d87f6). Wave 1's third
  plan, **03-13 (turns_remaining + the whole run-2 config surface), is now also fully
  executed**: `encoding.py`'s key field 5 is exact `turns_remaining` (turn_bucket
  deleted, D-06 superseded); every knob 03-14..03-25 need is declared once across
  `StrategyKey`/`TrainingKey` + new `strategy_schema.py` + both role `strategy.json`
  files (15 added, 1 removed); `QTable.SCHEMA_VERSION` bumped 1->2 so a run-1-format
  table fails loud instead of loading wrong, 3 commits (da27684/050d95d/dd7384e).
  Next: 03-14 (terminal signal, R2+R4) finishes wave 1.
Status: Executing Phase 04
  pending). Phase 3 run 2 wave 1 is underway: 3 of 15 run-2 plans done. Waves 1-6 are
  autonomous; wave 7 (03-25) is a human-operator checkpoint (the overnight training run
  and the real GATE-4 remeasurement) — do not run verify-work 3 until it passes. Three
  standing constraints carried into every remaining plan: 03-23's pre-flight gate must
  exit 0 before any training job starts; the 0.55 GATE-4 bar is NOT lowered (D-28); and
  03-21 stops and asks rather than inventing a number if its two target checks conflict.
  5 phases remain after Phase 3 closes.
Last activity: 2026-08-08 -- Phase 04 execution started
  config surface). Full account is in the frontmatter `last_activity` field above;
  condensed here: 3 tasks (encode_state's turns_remaining field, the full run-2
  StrategyKey/TrainingKey + strategy_schema.py + both config files, qtable
  schema-version fail-loud), 1 mechanical deviation (Rule 3 — test_strategy_config.py
  split at the 150-line gate into a new test_strategy_config_run2.py, the exact
  contingency the plan's own context section named in advance). Two known stale
  references deliberately left untouched, out of this plan's file-ownership scope
  (docs/PRD_rl_strategy.md Sec2 — 03-22's; training/harness.py's docstring — 03-14's
  this wave) — both flagged in 03-13-SUMMARY.md for the owning plan to fix in passing.
  Full repo gates green: `ruff check .` 0 violations, line-limit clean,
  474 passed / 2 skipped (same 2 pre-existing skips). Graphify rebuilt (3583
  nodes/6484 edges/234 communities) and `GRAPH_REPORT.md` refreshed.
  `docs/phases/phase-3/TODO.md` deliberately not touched — same rationale as 03-11/03-12.

Progress: [█░░░░░░░░░] 13%  (1 of 8 phases; Phase 2 code complete pending verify-work;
  Phase 3 run 2: 3 of 15 plans (03-11, 03-12, 03-13) done, 12 remain across waves 1-7,
  wave 7 is a human-operator checkpoint)

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-base-logic P00 | 9min | 3 tasks | 23 files |
| Phase 01-base-logic P01 | 15min | 3 tasks | 9 files |
| Phase 01 P02 | 10min | 3 tasks | 6 files |
| Phase 01 P03 | 5min | 3 tasks | 4 files |
| Phase 01-base-logic P04 | 9min | 4 tasks | 8 files |
| Phase 02-fastmcp-infrastructure P00 | 12min | 3 tasks | 20 files |
| Phase 02-fastmcp-infrastructure P01 | 18min | 3 tasks | 6 files |
| Phase 02-fastmcp-infrastructure P02 | 12min | 3 tasks | 4 files |
| Phase 02-fastmcp-infrastructure P03 | 12min | 3 tasks | 3 files |
| Phase 02-fastmcp-infrastructure P04 | 13min | 3 tasks | 6 files |
| Phase 02-fastmcp-infrastructure P05 | 10min | 3 tasks | 1 file |
| Phase 02-fastmcp-infrastructure P06 | 25min | 3 tasks | 5 files |
| Phase 02-fastmcp-infrastructure P07 | 20min | 3 tasks | 4 files |
| Phase 02-fastmcp-infrastructure P08 | 30min | 3 tasks | 5 files |
| Phase 02 P09 | 75min | 3 tasks | 15 files |
| Phase 02 P10 | 110min | 4 tasks | 10 files |
| Phase 03 P00 | 19min | 3 tasks | 23 files |
| Phase 03 P01 | 6min | 2 tasks | 2 files |
| Phase 03 P02 | 12min | 3 tasks | 5 files |
| Phase 03 P03 | 18min | 2 tasks | 4 files |
| Phase 03 P04 | ~35min | 3 tasks | 11 files |
| Phase 03 P05 | ~25min | 2 tasks | 6 files |
| Phase 03 P06 | ~20min | 2 tasks | 5 files |
| Phase 03 P07 | ~70min | 2 tasks | 19 files |
| Phase 03 P08 | ~50min (this session; Tasks 1-3 committed in a prior, interrupted session) | 1 task (Task 4) | 11 files |
| Phase 03 P09 | ~20min | 2 tasks | 6 files |
| Phase 03 P10 | ~40min (Tasks 1-3 only; Task 4 pending operator) | 3 of 4 tasks | ~20 files |
| Phase 03 P11 (run-2 wave 1) | ~25min | 3 tasks + 1 coverage-gap fix | 8 files |
| Phase 03 P13 | 45min | 3 tasks | 12 files |
| Phase 04 P11 | ~65min | 3 tasks | 13 files |
| Phase 04 P12 | ~110min | 4 tasks | 25 files |
| Phase 04 P13 | ~35min | 4 tasks | 10 files |
| Phase 05-cloud-exposure-and-tunneling P01 | ~50min | 3 tasks | 11 files |
| Phase 05-cloud-exposure-and-tunneling P02 | ~30min | 3 tasks | 11 files |
| Phase 05-cloud-exposure-and-tunneling P03 | ~35min | 3 tasks | 7 files |
| Phase 06 P02 | 100min | 4 tasks | 33 files |
| Phase 06 P03 | 50min | 4 tasks | 25 files |
| Phase 06 P04 | 90min | 3 tasks | 12 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Init: RL (tabular Q-learning) with a Bayes+Manhattan fallback as the strategy
- Init: Fixed 8-phase build order (book §10.3 stages 1–7 + submission phase 8) — phases are not re-derived
- Init: Real `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` (Segal §2.2), not `.planning/` pointers
- Init: GSD config — Balanced models, Interactive mode, branching none, TDD on, UI phases off
- [Phase ?]: D-05: all game numerics in game_params.json — zero hardcoded values in any src/ file (Appendix F §2 rule 1)
- [Phase ?]: D-06: game_params.json duplicated byte-for-byte in config/police/ and config/thief/ for Phase-2 NET-09 identity check
- [Phase ?]: D-04: package name is pursuit — neutral, usable by both cop and thief repos at Phase 8 split
- [Phase 01-01]: D-07: constants.py/Enum hold only structural non-numeric values; zero game numbers hardcoded
- [Phase 01-01]: D-08: barriered cell is impassable; get_legal_moves excludes it (prerequisite for BASE-05)
- [Phase 01-01]: D-12: GameState @dataclass(frozen=True); immutable snapshot pattern; dataclasses.replace for transitions
- [Phase 01-01]: D-13: STAY (current position) always in legal moves; agent can always pass even surrounded by barriers
- [Phase 01-01]: D-14: Outcome enum names all four outcomes; only CAPTURE/SURVIVAL produced in Phase 1
- [Phase 01-02]: D-10: barrier-on-thief IS accepted; capture consequence owned by detect_capture (01-03)
- [Phase 01-02]: D-11: quota enforced via params.barrier_quota only; zero numeric literals in barrier.py (AST verified)
- [Phase 01-02]: Validate-first order in place_barrier prevents Pitfall 2 (spurious quota consumption on invalid placements)
- [Phase 01-03]: D-12 check order: BASE-03 (cop==thief) -> BASE-04 (thief in barriers) -> BASE-05 (no legal moves) -> None
- [Phase 01-03]: D-13 note: BASE-05 independent trigger geometrically impossible; STAY always legal unless BASE-04 fires first
- [Phase 01-03]: D-14: score_outcome reads exclusively from params.score_* fields; only literal 0 for TECHNICAL_LOSS
- [Phase 01-03]: D-15: Phase 1 produces only CAPTURE/SURVIVAL; TIE/TECHNICAL_LOSS unreachable but scored for completeness
- [Phase 01-03]: D-16: evaluate_turn_end uses params.survival_threshold (no hardcoded value)
- [Phase Phase 01-04]: D-09: engine.apply_cop_action wires cop move + barrier placement in one cop action
- [Phase Phase 01-04]: D-12: engine wires the turn boundary: apply_cop_action does cop-acts + capture-check, apply_thief_move does thief-move + turn-increment + survival-check
- [Phase Phase 01-04]: increment_turn() added to state.py so engine.py has zero non-zero numeric literals (AST scan clean)
- [Phase 02-00]: D-04/D-16/D-17/D-18: config/{police,thief}/network.json holds every network number; ports 8001/8002 and watchdog_poll_seconds=1 are engineering defaults not traced to PARAMETERS.md; retry_count=3/backoff_seconds=5 reused from Table 19 Gatekeeper rows
- [Phase 02-01]: QUAL-02: require_key/require_int/require_str extracted to src/pursuit/shared/loader_helpers.py at the second consumer (network_config.py); config.py re-pointed at it, zero private validator copies remain
- [Phase 02-01]: NET-02 guaranteed by construction: load_network_config returns a fresh NetworkParams every call, no module-level cache/singleton; verified by identity checks in both directions (police vs thief, and two calls to the same file)
- [Phase 02-01]: Reused 02-00's NetworkConfigKey.ENV_HOST/ENV_PORT/ENV_OPPONENT_URL for the D-16 override names instead of adding a duplicate NetworkEnvVar class
- [Phase 02-02]: D-06: Envelope frozen dataclass fixed at exactly four keys {type, turn, sender, payload}; from_dict accepts wire `type` as a string only, never a MessageType instance; Phase-4 hint / Phase-6 commit arrive as new MessageType members, never new envelope keys
- [Phase 02-02]: D-08/D-15: config_digest hashes canonically re-serialized JSON (sort_keys=True, separators=(",", ":")), never raw file bytes, so formatting drift can never fake a NET-09 config mismatch; canonical_json() is the single project-wide canonicalisation Phase 6's commit-reveal hash must reuse (QUAL-02)
- [Phase 02-02]: digests_match uses secrets.compare_digest per CLAUDE.md's standing digest-comparison idiom, ahead of Phase 6 where it becomes security-critical
- [Phase 02-03]: D-09/D-12: State enum fixed at exactly six members; ALLOWED_TRANSITIONS is an explicit dict[State, frozenset[State]] keyed by every member, GAME_OVER/ERROR terminal (empty frozenset) — no FSM library imported or installed
- [Phase 02-03]: D-10: RECOVERABLE_ATTEMPTS is exactly six pairs (four self-transition duplicates + two late-handshake pairs); every other illegal pair — including anything out of ERROR and any backwards jump to INIT — is PROTOCOL_VIOLATION and escalates to State.ERROR
- [Phase 02-03]: NET-05: transition() calls the injected reporter from a single call site before the outcome branch, guaranteeing every illegal attempt is reported exactly once and a legal transition reports zero times
- [Phase 02-03]: reporter is injected as a TransitionReporter Protocol parameter, not imported — state_machine.py has zero dependency on 02-04's event log, keeping 02-03/02-04 same-wave-safe; 02-04's adapter must match the exact keyword-only __call__(*, current, target, severity, reason) -> None shape
- [Phase 02-03]: NET-02: TurnStateMachine keeps state on the instance only (self._state); no module-level mutable current-state variable anywhere in state_machine.py
- [Phase 02-04]: D-11/NET-05/NET-07: append_event() enforces validate->serialize->write->flush->os.fsync->echo, in that literal order — a rejected record never creates/grows the log, durability always precedes the console echo
- [Phase 02-04]: D-14/D-18/NET-07 (RESEARCH Pitfall 6): Watchdog.check_once() runs on_freeze (suppressing exceptions) THEN the injected exit_action, verified by reading the incident file from inside the exit callable itself; threshold_seconds/poll_seconds are required keyword-only constructor args with no default in source
- [Phase 02-04]: watchdog_poll_seconds was already present in NetworkParams/network.json (=1, D-18) before this plan ran — no hand-off gap to close at 02-09
- [Phase 02-04]: Plan-internal tension (same category as 02-03's event_log substring issue): EventType.WATCHDOG_INCIDENT = "watchdog_incident" is required verbatim by the interfaces contract, but the plan's own verify/decoupling-audit scripts substring-scan for "watchdog" in event_log.py and flag it. Resolved by rewording every avoidable docstring mention (in both event_log.py and watchdog.py) and documenting the one irreducible, schema-required occurrence in the SUMMARY; true import-level decoupling (no `import` of watchdog in event_log.py or vice versa) independently re-verified and holds
- [Phase 02-05]: DOC-02: docs/PRD_mcp_transport.md written and approved in Wave 1, before any transport source exists (SEGAL §2.5 step 5) — documentation-only plan, zero source/config touched
- [Phase 02-05]: D-16/D-18 category separation enforced structurally: §10.1 (PARAMETERS.md-traced: 30s/60s/3/5s, Table 19 rows 6/7/4/3) and §10.2 (engineering defaults: ports 8001/8002, watchdog_poll_seconds=1) are two visually distinct tables so neither reader nor future phase can conflate them
- [Phase 02-05]: D-17 reuse of Table 19 Gatekeeper rows 3-4 for the NET-06 retry/backoff pair documented in prose as a deliberate, auditable reuse (both minimum status, may be raised never lowered) rather than an invented second pair of numbers
- [Phase 02-06]: NET-09 seam: register_tools/build_server/PeerRuntime all accept a keyword-only handshake_handler; None keeps the D-05 generic ack (pinned so 02-08's fake-peer tests stay valid), a supplied async handler's reply is returned verbatim and nothing is enqueued -- the exact hook 02-09 uses to bind 02-08's respond_to_handshake without editing tools.py
- [Phase 02-06]: QUAL-02: all four D-05 handlers share one _accept(queue, message_type, turn, sender, payload) helper that translates Envelope.from_dict's TypeError/KeyError/ValueError into fastmcp.exceptions.ToolError, decode-before-enqueue so nothing half-parsed ever reaches the queue
- [Phase 02-06]: RESEARCH Open Question 2 resolved by measurement, not assumption: task.cancel() alone left the listening port bound (FastMCP 3.4.5's run_http_async has no exposed uvicorn should_exit handle); PeerRuntime now binds its own listening socket and hands it to run_async via sockets=[...] so stop() closes the real OS socket directly -- re-measured SHUTDOWN CLEAN
- [Phase 02-06]: fastmcp 3.4.5 API shape notes for later plans -- no plural mcp.get_tools(); use (await mcp.get_tool(name)).fn for the coroutine-function guard; Client has no public timeout attribute, only the private _session_kwargs['read_timeout_seconds'], but client.transport.url is public
- [Phase 02-07]: Exception-surface correction for all later plans touching NET-06/transport errors: the installed fastmcp 3.4.5/mcp packages spell the transport exception `McpError` (mixed case), NOT `MCPError` as 02-RESEARCH.md's cited snippet spells it -- `from mcp import MCPError` raises ImportError; `from mcp import McpError` is correct. issubclass(ToolError, McpError) is False, so RESEARCH Pitfall 4's except-clause design (ToolError excluded from the retryable set) is unaffected, only the import spelling
- [Phase 02-07]: D-13/D-17 implemented: RETRYABLE_TRANSPORT_ERRORS = (McpError, DeadlineExpired); except ToolError: raise placed BEFORE except RETRYABLE_TRANSPORT_ERRORS inside call_with_retry so an application-level tool rejection can never become an unearned technical win; exhausted retries return a CallOutcome carrying a TechnicalWin (reason, attempts, timeout_seconds, backoff_seconds, elapsed_seconds, last_error) as a returned value only -- deadline.py never ends the game, scores, or logs
- [Phase 02-07]: __all__ written as an immutable tuple, not a list, in deadline.py -- satisfies both the plan's literal "export the seven public names" instruction and the NET-02 AST guard that forbids module-level list/dict/set literals
- [Phase 02-09]: Design note 8 resolved: call_with_retry DOES retry DeadlineExpired (RETRYABLE_TRANSPORT_ERRORS includes it), so await_opponent_turn wraps wait_for_opponent in call_with_retry rather than declaring a technical win on the first inbound timeout; retries_attempted is always the measured attempt count, never a constant
- [Phase 02-09]: Two 150-line-gate splits: orchestrator.py -> {orchestrator.py, turn_actions.py} (not pre-authorised by the plan, done anyway per Segal's hard line limit) and agent_lifecycle.py -> {agent_lifecycle.py, agent_wiring.py} (pre-authorised). The orchestrator/turn_actions re-export needed a PEP 562 module __getattr__ instead of an eager import -- an eager cross-import was reproduced as a genuine circular import when turn_actions.py was imported first, verified fixed under both import orders
- [Phase 02-09]: fastmcp.Client is a required async context manager (Client.__aenter__ calls self._connect()) -- take_my_turn/run_agent always enter it via `async with` before calling a tool; the plan's own pseudocode omitted this and was adapted accordingly
- [Phase 02-10]: Real production bug found and fixed via 02-10's GATE-3 test, not by 02-10 itself: turn_actions.py's take_my_turn unconditionally re-attempted State.MY_TURN every call, but await_opponent_turn's own final line legitimately leaves the machine at MY_TURN at the end of every cycle after the first -- colliding as an illegal self-transition, silently no-opping every second-and-later turn and starving await_opponent_turn into a FALSE technical win. No 02-09 unit test ever drove a real second cycle to catch it. Fixed by guarding take_my_turn's entry attempt on `current is not State.MY_TURN`, symmetric to await_opponent_turn's own guarded HANDSHAKE entry. A second, related bug (await_opponent_turn calling Envelope.from_dict on an already-decoded Envelope -- tools.py's real _accept enqueues an Envelope instance, never a dict) was fixed the same way. Both confirmed via standalone probe scripts and re-verified at real two-process scale (Task 4: a full 35-turn game completed cleanly to SURVIVAL)
- [Phase 02-10]: NET-05's RECOVERABLE severity coverage was never uniquely provided by the orchestrator-level test that assumed the now-fixed buggy behavior -- it was always independently covered by tests/unit/test_state_machine.py::test_recoverable_attempt_keeps_machine_usable (QUAL-02); the orchestrator-level test was corrected to assert the fixed behavior instead of the bug
- [Phase 02-10]: A three-way split was needed for the integration gate modules (test_peer_roundtrip.py, test_turn_isolation.py, test_turn_lifecycle.py, test_turn_resilience.py), one level deeper than the plan's own two-way split anticipation -- test_turn_lifecycle.py still exceeded 150 lines after the first split, so the two GATE-2 tests moved to test_turn_isolation.py, exactly the contingency the plan named in advance
- [Phase 03-00]: StrategyKey/TrainingKey Enums address every Phase-3 hyperparameter; strategy_config.py is loader_helpers' 3rd consumer
- [Phase 03-00]: artifacts_dir empty-defaults under LOCALAPPDATA (D-22); reward_capture/reward_survival/reward_step/reward_barrier_gain and alpha_floor/alpha_decay_episodes/eval_seed_offset are engineering defaults not sourced from AI-SPEC
- [Phase 03-01]: docs/PRD_rl_strategy.md v1.00 written before any src/pursuit/strategy/ code (DOC-02): reward function does NOT reuse game_params.json Table 17 scoring; STRAT-02's Manhattan fallback wording is implemented as barrier-aware BFS, documented as a deliberate deviation
- [Phase 03-02]: BrainBase ABC + frozen Observation/Decision seam; Action IntEnum order frozen and pinned by test (STRAT-01); build_brain resolves via an explicit dict, never eval/exec/importlib (STRAT-03, D-07); AST-walk structural tests prove no pursuit.network or LLM/HTTP/subprocess/socket import is reachable from src/pursuit/strategy/ (STRAT-07), demonstrated to actually fail when triggered
- [Phase 03-03]: bfs(state, start, goal, agent, params) is the single barrier-aware distance oracle for the phase (QUAL-02); adjacency comes entirely from board.get_legal_moves via a per-step probe state (dataclasses.replace), never reimplemented; UNREACHABLE=-1 sentinel (not math.inf) for a walled-off goal, never raises; neighbours sorted ascending (row, col) at every expansion for deterministic tie-breaking; no walk() helper added since gameplay calls bfs() fresh every turn and a multi-step walk is a test-time concern only
- [Phase 03-04]: prior.spread() is the Bayes PREDICTION step only (no evidence term, Phase-4 seam); mass invariant asserted inside the function on both entry and exit, not spot-checked in tests; fallback.pick() ranks candidates via bfs() distance only (cop minimizes, thief maximizes tie-breaking toward more onward legal moves), unreachable target never raises; HeuristicBrain is fully playable for both roles, instance state only (D-03), and is the single heuristic implementation fallback.py owns (QUAL-02)
- [Phase 03-04]: Deviation -- registry.build_brain(role, params, game_params) now REQUIRES GameParams threaded to every brain constructor (BrainBase._pick_move/_decide_move deliberately carry none, per 03-02); this is now the fixed calling convention 03-06's QLearningBrain must also match
- [Phase 03-05]: encode_state/turn_bucket take (obs, params: StrategyParams, game_params: GameParams) as two explicit typed parameters, matching 03-04's build_brain(role, params, game_params) convention; blocked_mask bit order frozen to Action's own IntEnum order (NORTH=bit0..WEST=bit3, STAY excluded); QTable JSON schema nests values+visits inside one per-key object so they can never desynchronize; durable_write.py's retries/backoff stay required keyword-only args with no defaults, QTable.save() supplies its own module-level structural constants (_SAVE_RETRIES=3/_SAVE_BACKOFF_SECONDS=0.1s)
- [Phase 03-05]: Deviation (Rule 3 - blocking) -- tests/unit/strategy/test_qtable.py split into test_qtable.py (API + fail-loud load) and test_qtable_durability.py (crash/retry mechanics) after hitting 152 code lines against the 150-line gate; no test weakened or removed
- [Phase 03-06]: QLearningBrain(role, params, game_params, rng=None) matches the fixed build_brain calling convention; rng is optional/keyword-only (unseeded random.Random() default) so the registry path still constructs a working brain, while 03-08 injects a seeded one by constructing directly; epsilon is a mutable instance attribute initialized from params.epsilon_eval, reassigned per-episode by 03-08's own decay schedule rather than re-read from config per decision; exploration is legal-move-filtered per PRD Sec5's literal wording, the greedy/argmax branch is deliberately NOT filtered (matches the PRD; any legal-move guardrail is AI-SPEC Sec6's distinct, not-yet-owned "Legal-move filter" online guardrail); both explore and exploit inside the visited region tag source=QTABLE, per the plan's own literal task text
- [Phase 03-06]: Deviation (Rule 3 - blocking, repeat of 03-05's pattern) -- test_qlearning.py split into test_qlearning.py + test_qlearning_learning.py + non-collected _qlearning_fixtures.py helper (mirrors tests/unit/_fakes_agent.py) after hitting 174 code lines; Deviation (Rule 2 - missing coverage) -- added a _decide_move barrier=None test mirroring HeuristicBrain's, closing qlearning.py to 100% coverage
- [Phase 03-07]: choose_barrier(state, game_params, believed_thief_cell, min_gain) scores candidates by BFS-distance increase to a fixed anchor (the board corner diagonally farthest from the cop's own cell) -- an autonomous scoring-metric decision since the plan left the exact metric open; bfs() is provably symmetric between cop/thief in this codebase, so a direct cop-thief-distance metric could not discriminate a cop-favoring placement, and the anchor cell itself is excluded from candidates to close a trivial self-referential exploit found before any test was written
- [Phase 03-07]: min_gain is a 4th explicit parameter (not folded into game_params) because barrier_quota (PARAMETERS.md, D-05) and barrier_min_gain (engineering default, D-18) live in two different config objects (GameParams vs StrategyParams) by this codebase's established architecture; both _decide_move implementations build a post-move probe state before calling choose_barrier, matching sdk.engine.apply_cop_action's real move-then-barrier order so declared==applied holds by construction
- [Phase 03-07]: Deviation (Rule 2/3 - blocking) -- strategy.barrier_min_gain (value 1) added to StrategyParams/both strategy.json files; required first splitting src/pursuit/constants.py (at the exact 150-code-line ceiling) into constants.py (game-domain enums) + new src/pursuit/config_keys.py (ConfigKey/NetworkConfigKey/StrategyKey/TrainingKey), 5 import sites updated mechanically. Deviation (Rule 3 - blocking, repeat of 03-05/03-06) -- test_barriers.py split into test_barriers.py + test_barriers_integration.py at the 150-line gate
- [Phase 03-08]: run_training(config: TrainingRunConfig) bundles game_params+cop_params+thief_params into one object rather than the plan's literal single-StrategyParams run_training(params) sketch -- one run trains BOTH roles' tables together under two configs that legitimately differ in brain_class/qtable_path/reward_*, matching the EpisodeConfig precedent (game_params+learner_params) already established by this plan's own inherited harness.py; run-level scalars (seed/episodes/checkpoint_every/pool_snapshot_every/artifacts_dir) are validated equal between cop.json/thief.json up front (require_shared_run_fields), raising loud on drift rather than silently picking one side
- [Phase 03-08]: A single shared random.Random(seed) instance drives opponent sampling AND both QLearningBrains' own epsilon-greedy exploration -- not a per-brain sub-seed -- matching docs/PRD_rl_strategy.md Sec5's D-19 wording verbatim ("epsilon-greedy action selection and opponent sampling use a seeded random.Random(training.seed) instance"); this is what makes RunState.rng_state's one getstate() reproduce the whole run, and is a training-pipeline determinism choice unrelated to project rule 2 (which governs the two DEPLOYED match-time processes, not this offline single-process harness)
- [Phase 03-08]: Training checkpoints Q-tables under StrategyParams.artifacts_dir using the qtable_path's basename, never at the repo-relative qtable_path itself -- that path is reserved for the FINAL BLESSED table a later plan copies in at run end (RESEARCH Sec3), and rewriting a multi-MB table there every checkpoint_every episodes would churn OneDrive on every interval (D-22); checkpoint_every/pool_snapshot_every read as global (both-roles) cadences, curve_log_every reads per-role, matching each cadence's own purpose (crash recovery/anti-collapse vs. per-role learning curves, D-25); winrate_vs_baseline is scoped to opponent_kind=="heuristic" episodes specifically so the column means what its name says
- [Phase 03-08]: Deviation (Rule 3 - blocking, repeat of 03-05/06/07) -- run_training's setup/orchestration split into training/loop.py (episode-loop orchestration) + loop_setup.py (once-per-run resume/checkpoint/pool-build/Windows-guard helpers) + progress.py (pure mutable bookkeeping) + run_config.py (shared TrainingRunConfig/RunResult, breaking a would-be import cycle) at the 150-line gate. Deviation (Rule 2 - missing coverage) -- added a direct test for harness.py's previously-uncovered _role_won(role, None) branch, closing it to 100%
- [Phase 03-09]: final_slope(rows, role, window) returns a total win-rate drift over the trailing window (least-squares regression rate x window span), not a raw per-episode rate -- makes it directly comparable to convergence_tolerance (a win-rate delta, 0.02), since a 0.02-per-episode bound would be nonsensical over a 20000-episode window; numerically verified against three synthetic curves before implementation
- [Phase 03-09]: training/curve_analysis.py split out of plot_curves.py at the 150-line gate (QUAL-08), the exact contingency the plan's own text named; plot_curves.py re-exports the analysis names so `training.plot_curves` still satisfies the plan's literal decile_gain/final_slope/check_convergence spec, and stays the repo's only matplotlib importer (D-20, verified repo-wide, not just src/)
- [Phase 03-09]: Deviation (Rule 3 - blocking) -- the plan's literal `uv run python training/plot_curves.py <csv> <outdir>` invocation failed (direct-path execution puts training/ on sys.path[0], not the repo root); fixed with a guarded sys.path bootstrap gated on `__package__ in (None, "")`, regression-tested via a subprocess pytest test
- [Phase 03-09]: README.md did not exist anywhere in the repo before this plan (confirmed via git log); created it now with a project overview borrowing .planning/PROJECT.md's framing, plus the mandatory rule-42 learning-curves section; every figure and measured win-rate is explicitly marked "pending (03-10)" since no training run has executed yet -- zero fabricated numbers, only configured bars (win_rate_margin/eval_games/seed/etc.) read from config/police/strategy.json
- [Phase 03-10]: Held-out eval seeds (D-23) are asserted disjoint from training seeds by an executable check (assert_seeds_held_out), not a comment -- this is the one assumption that, if silently wrong, makes the whole GATE-4 number meaningless (the heuristic is both sparring partner and eval opponent, so training-set contamination would let a table "beat" the baseline on positions it already trained against); the win-rate margin is compared against the measured heuristic-vs-heuristic baseline per role, never an assumed 50%, since the game is not role-symmetric
- [Phase 03-10]: test_beats_baseline.py's GATE-4 test SKIPS (not passes, not xfails) with a stated reason while no trained table exists -- a green GATE-4 that never loaded a table would be the single worst outcome for the phase's central claim; the skip is intentionally left for Task 4 (the human operator's training run) to close, never faked or bypassed by the automated executor
- [Phase 03-10]: 03-10 Task 4 (`checkpoint:human-action gate="blocking"`) was executed only through Tasks 1-3 in this automated run; Task 4 itself -- the overnight training run, GATE-4 measurement, and table promotion -- was deliberately left untouched per the phase's own design (it needs a human watching a real Windows machine for console QuickEdit suspension, OneDrive/Defender interference, and sleep). No qtable file, no README number, and no 03-10-SUMMARY.md exist yet as a direct, verified consequence

- [Phase 03-10 post-mortem]: **T4-followup-1 and T4-followup-2 are WITHDRAWN, both premises measured false.** The cop was not undertrained (0.900 training win rate); it was evaluated on states it never trained on. The thief's `fallback_rate` collapse was a symptom; the cause is that it never receives a capture update at all
- [Phase 03-10 post-mortem]: **Distance is the wrong objective for both roles.** cop-win ⟺ the thief's free component is a forest; the cop destroys cycles and the thief preserves one. Both current brains optimise BFS distance, and the cop's barrier rule (max distance to a fixed corner anchor) has no literature support
- [Phase 03-10 post-mortem]: **RL is demoted from "the strategy" to "weight tuning"** — alpha-beta over a cycle-based evaluation is the policy; ~60 weights replace a 1.7M-entry table. Reverses the init-time framing of tabular Q-learning as the strategy, without changing the phase breakdown
- [Phase 03-10 post-mortem]: **γ must differ by role** — cop 0.99 (discounting IS its capture-sooner incentive), thief 1.0 (discounting attenuates its only good outcome). Terminal rewards come from the real scoring table (cop 20/5, thief 10/5), reversing `docs/PRD_rl_strategy.md` §4's decision to hand-tune symmetric 1.0/1.0 with no capture penalty — that decision is the direct origin of the degenerate thief
- [Phase 03-10 post-mortem]: `min_win_rate_absolute = 0.55` is **ours (D-14, `docs/PRD_rl_strategy.md` §8), not a Segal fixed value** — it appears nowhere in `docs/PARAMETERS.md`. Re-arguable on evidence; must not be moved merely because a run failed
- [Phase 03-10 post-mortem]: Subagent output is **not** taken at face value — the algorithms researcher's headline depth benchmark failed independent replication against the real engine, and an earlier cop-number attribution in this session was wrong and is corrected in `last_activity`

- [Phase 03-11]: No new decisions -- every contract (adjacency-equivalence proof, the
  never-raise convention for out-of-set cells, `cycle_rank`'s connected-only
  precondition, `voronoi_split`'s neither-side tie rule) was already fully specified by
  the plan and the cited research doc. One implementation note worth recording:
  `voronoi_split` advances both source frontiers one BFS layer per round inside a
  single loop rather than running two independently-timed BFS passes and comparing
  distances afterward, so "reached on the same round" is the literal definition of a tie

- [Phase 03-11]: STATE.md's own YAML frontmatter does not parse (`yaml.safe_load`
  raises `ScannerError`, confirmed pre-existing on `HEAD` before this session touched
  the file) -- long unquoted plain scalars containing natural-language colons break
  YAML's plain-scalar grammar. ~85 occurrences repo-wide; full fix is out of scope for
  a single plan (would mean reformatting the whole historical narrative). Logged in
  Deferred Items, not fixed, per the deviation rules' scope boundary

- [Phase 03-12]: No new decisions beyond what D-31 and the plan already specified. Two
  implementation notes worth recording: (1) the two-arm regression test differs ONLY by
  monkeypatching `fallback.safe_moves` (real spy vs a no-op) inside `monkeypatch.context()`
  blocks against the production call site, rather than adding a production toggle
  parameter to `_evade`/`pick` just for testability; (2) the plan's own ~100ms/game
  timing assumption did not reproduce (measured ~34-38s for the 160-game suite,
  cProfile-traced to 03-07's pre-existing `choose_barrier`, not this plan's code) --
  recorded honestly in the test module's docstring rather than shrinking `n=60` or
  disabling barrier placement to hit the stale target

- [Phase 03-13]: Every seeded value is labelled by provenance in 03-13-SUMMARY.md
  (measured / sourced / engineering default), none claimed as a PARAMETERS.md value:
  `search_depth_cap=5` is D-26's own measured real-engine figure; `min_distinct_starts`,
  `terminal_spread_min/ratio_max`, `floor_episode_fraction_max` are copied verbatim from
  `TRAINING-METHODOLOGY.md` SF.3; `pfsp_exponent=1.0` follows AlphaStar's
  `f_var(x)=x(1-x)` but the exact exponent is flagged secondary-sourced only; the four
  `barrier_weight_*` values fix only the strict ordering `cycle_rank > component_size >
  territory > distance`, magnitudes are 03-21's to set. `docs/PRD_rl_strategy.md` Sec2
  and `training/harness.py`'s docstring both still reference the deleted `turn_bucket`
  by name -- left untouched deliberately (03-22's and 03-14's files respectively, per
  outline SS7 file-ownership), flagged for the owning plan to correct in passing

- [Phase 04-09]: D-51 implemented as a literal DISCLOSED REVISION of D-40, not an
  extension: `belief.json`'s `hint_likelihood.weight` (fixed, validated below
  `scent_likelihood.weight` by name) and `reliability.prior` (the adaptive
  coefficient's starting point) are two INDEPENDENT config fields, not the same
  number reused twice -- resolves an ambiguous reading in 04-09-PLAN.md's own
  prose, documented in 04-09-SUMMARY.md's Decisions Made for 04-13 to carry into
  `PRD_belief_map.md`/`RULES-RESOLUTION-LANG.md`. `strategy/scent_check.py::contradicts()`
  reproduces the book's Sec4.4 worked example (0.9 -> 0.81) exactly;
  `strategy/reliability.py::Reliability.observe()` is measured to settle EXACTLY at
  `r_min`/`prior` under 1000 extreme observations, not just bounded;
  `strategy/belief_hint.py::hint_likelihood()` returns an all-zero grid at
  confidence=0 specifically so `BeliefMap.update()`'s own zero-guard buys an EXACT
  (not approx) no-op for `NO_EVIDENCE`, per the plan's own stricter verify wording

- [Phase 04-11]: Option A (believed-state substitution) shipped over Option B
  (expectation over the belief's support) per docs/phases/phase-3/PRD.md
  Sec8's own cost argument, now measured rather than merely asserted:
  belief-enabled decisions stay under 5ms against the 50ms
  strategy.max_decision_ms budget. D-43 (sample, not argmax) implemented
  literally -- BeliefMap.sample(rng) feeds Observation.target_cell and the
  believed GameState both. Reliability is constructed inside
  BeliefAdapter.__init__ (not externally by 04-12 as 04-09's carry-over F
  literally proposed) and exposed as a public attribute so 04-12 can still
  drive .observe() on the same instance -- constructing BeliefAdapter IS
  the "handshake time" moment carry-over F meant. decide()'s known_cell:
  Coord | None keyword is new beyond the plan's literal prose: Regime A/B
  cannot be read off GameState alone since state always carries the
  engine's true joint position (needed by resolve_turn regardless of
  blindness), so the regime has to be told to the adapter, not inferred

- [Phase 04-12]: Hint-sending is now CONDITIONAL on AgentContext.language
  (None -> move-only, matching pre-04-04 mechanics) rather than 04-04's
  unconditional placeholder -- every real game (agent_lifecycle.
  default_context) always wires it, so LANG-01 holds for actual play;
  bare test fixtures that never opt in are unaffected in behaviour except
  the hint call itself. [Rule 1 - Bug] record_hint's "late"/"duplicate"
  hint checks (04-04's own design) both raised HintProtocolError and
  ended the game as a spurious TECHNICAL_LOSS -- found only by running a
  TRUE two-peer concurrent game for the first time in this project
  (tests/integration/two_peer_game.py); fixed to silently drop/overwrite,
  since the move and the hint are independent, variable-latency
  round-trips and neither timing pattern is a real protocol violation.
  D-48's regime decision (known_opponent_cell) is computed ONCE, before
  record_action/maybe_resolve can mutate the state it reads, and threaded
  explicitly rather than recomputed. agent_lifecycle.default_context is
  now the first place in the whole project that constructs a REAL
  registry brain + ScentField + LanguageRuntime for the LIVE network
  turn loop (every prior phase/plan only exercised strategy/language code
  via direct engine calls or single-sided injected tests)

- [Phase 04-13]: Documentation-only plan, zero source/config/test files touched.
  D-51 recorded, in both PRD_belief_map.md and RULES-RESOLUTION-LANG.md, as a
  DISCLOSED REVISION of D-40 -- not an extension -- per 04-09's own carry-over
  instruction. Every book+PDF page pair quoted in RULES-RESOLUTION-LANG.md was
  verified directly against police_thief_p2p.pdf this session (pages 5, 50-53,
  62-64), not re-copied from 04-PLAN-OUTLINE.md Sec1 without checking; the
  preface's PDF page (5, roman-numbered front matter) had never been cited
  anywhere in this repo before. ROADMAP.md's Phase 4 "Plans:" checkboxes were
  left unticked for ALL fourteen real plans, including the twelve
  (04-01..04-12) with real SUMMARY.md files already on disk -- read broadly,
  this plan's "TICK NOTHING" environment rule applies to every tick mark in
  every touched file, not narrowly to the sq/half-circle/checkmark TODO.md
  convention alone. The Plans-Complete NUMERIC count was still corrected to
  13/14, since a plain number is not a tick. Knowledge-graph layering check
  (services/llm <-> strategy) run programmatically against graph.json's raw
  node/edge data, not by reading the rendered GRAPH_REPORT.md: zero violations
  either direction

- [Phase 04-14]: GATE-4 measured mocked, PASSING on all three Sec10.4
  criteria; live confirmation PENDING (no ANTHROPIC_API_KEY on this
  machine). The scent decay law (criterion 2) is verified by driving the
  shipped ScentField/scent.py directly with the locked config, NOT mined
  from the network JSONL -- 04-12 never logs a per-turn scent snapshot,
  only belief entropy/argmax/reliability, so "extracted from the event
  log" for this one criterion means "the same production objects a real
  game mutates", not literally a JSONL field. "Intent committed before
  text" (criterion 3) is likewise a STRUCTURAL proof (compose_outgoing
  requires the already-decided DeceptionPlan as a positional argument),
  not a timestamp diff, since the JSONL fuses text+intent into one record
  once both exist. Both deviations from a literal "read it off the JSONL"
  reading are documented in GATE-4-MEASUREMENT.md and are stronger
  guarantees than a log-timestamp comparison would give, not weaker ones.
  The belief-on/off comparison surfaced a genuine, unplanned finding:
  network/turn_language.py's belief.enabled=false fallback (pre-dating
  D-48/D-43) hands the raw brain the TRUE current opponent cell, not a
  blind one -- so it measures "belief vs omniscience", not "belief vs
  blindness", and the measured 1.0/0.0 win-rate gap is reported with that
  caveat rather than read as evidence about the belief layer's value.
  Anthropic's published Haiku 4.5 rate (### Decisions

/$5 per MTok input/output,
  scripts/gate4_report.py) is cited, not sourced from PARAMETERS.md --
  flagged for reconfirmation before Phase 7's league spend email.

- [Phase 05-01]: D-54: pyngrok (8.1.2), not ngrok-python -- ngrok-python
  1.7.0 requires Python >=3.12, this project runs 3.11.9. D-55: zero new
  numeric parameters -- tunnel.json is five strings only; reconnect
  retry_count/backoff_seconds and the liveness cadence are reused straight
  from NetworkParams (Table 19 + the D-18 precedent), never redeclared.
  Tunnel-on/off is decided by the static-domain env var's PRESENCE, not a
  tunnel.json boolean -- keeps D-55's "strings only" contract literal and
  makes tunnel-off the structural default for every existing test. run_agent
  moved out of agent_lifecycle.py entirely into a new agent_entrypoint.py
  (re-exported via a PEP 562 __getattr__, the same one-directional-
  dependency fix orchestrator.py/turn_actions.py already use) once
  agent_lifecycle.py -- already at exactly 150 code lines -- had no room
  left to absorb the tunnel wrapping in place.

- [Phase 05-02]: D-56 implemented exactly as 05-PLAN-OUTLINE.md/
  05-RESEARCH.md specified: SharedSecretMiddleware as a pure ASGI callable
  wired via run_async(middleware=[...]) -- the SAME call that already
  passes sockets= -- never a check inside an @mcp.tool handler; client()
  always builds an explicit StreamableHttpTransport (a bare Client(url)
  string infers headers={}, verified by direct probe against the installed
  fastmcp 3.4.5 source); secrets.compare_digest for the comparison, the
  same idiom config_hash.digests_match already established. D-57: verified
  by reading fastmcp.settings.http_host_origin_protection directly --
  already False/off by default, so no code change was needed, only the
  comment at the run_async call site. Two Rule-3 (blocking) file-location
  deviations from the plan's literal file list, both forced by the
  150-code-line gate: resolve_shared_secret landed in a new
  secret_wiring.py (not agent_wiring.py, which was already at 135/150) and
  build_middleware()/client_headers() landed in secret_guard.py (not
  inlined in peer_runtime.py, which had no room left). .gitignore's broad
  *_secret*/*-secret* rule-4 guard silently dropped every D-56 test file
  by NAME (test_secret_guard.py, test_secret_wiring.py,
  test_peer_runtime_secret.py, test_secret_channel.py) -- fixed with four
  explicit negations, same precedent as the existing !.env-example line;
  none of the four holds a real secret value.

- [Phase 05-03]: GATE-5-MEASUREMENT.md records BOTH Sec10.4 criteria
  PENDING, not one mocked/one live like GATE-4 -- nothing in Phase 5 can
  execute without a real ngrok account this machine lacks, so criterion 1
  has no numbers to report either; stated honestly rather than filled with
  a description of what would happen. D-57 (Localtonet) stays
  documentation-only: a second TunnelManager-equivalent integration would
  double the engineering surface for a path whose only job is standing by
  if ngrok is unusable on league day; LOCALTONET-FALLBACK.md satisfies
  rule 10 with zero lines of code. The smoke script's env preflight
  (`preflight()`) is deliberately split into its own synchronous,
  dependency-free function so a test can assert the refusal message
  without faking pyngrok/sockets/asyncio at all -- the live network path
  (`run_smoke()`) stays reviewed-logic-only, per the must_haves' own
  stated split. First time this project writes offline tests importing
  FROM scripts/ (gate5_smoke_checks.py, gate5_tunnel_smoke.py's preflight),
  closing a gap the gate4_* precedent itself left open.

- [Phase 06-01]: D-59/D-60/D-64/D-65 implemented exactly as
  06-PLAN-OUTLINE.md specified -- no re-derivation, no invented number.
  commit_pack.py imports canonical_json/digests_match from
  pursuit.network.config_hash -- the plan's own pre-authorized, documented
  exception to the security/ package's "sdk/shared only" boundary (a pure,
  dependency-free hashing leaf, no AgentContext/turn-loop coupling).
  build_commit_payload's `move` parameter stays completely shape-opaque
  (isinstance(move, dict) only) -- commit_pack.py never imports
  move_payload and never validates the composite {"move":...,"barrier":...}
  action dict's internal shape, by design, so 06-02 is free to build that
  shape however turn_commit.py needs. state_record.py's non-bool-int guard
  is a local 4-line duplicate of envelope.py's own (Pitfall 3's existing
  3-site precedent), not a cross-package import.
- [Phase 06-02]: D-58 role branch (Rule 1 bug fix, measured): await_and_respond checks ctx.role -- the fixed first-mover already committed+revealed this turn, so it only waits for the opponent's REVEAL, never decides again (a naive unconditional reading hung a real game 136s before a false technical loss)
- [Phase 06-02]: D-66/SEC-07 closed: barrier placement travels over the wire inside the committed composite {move,barrier} action dict for the first time; toggle-off (security.commit_reveal=false) proven byte-equivalent to pre-Phase-6 by a dedicated integration test
- [Phase 06-02]: turn_commit.py needed a third sibling (turn_commit_send.py) beyond the plan's two pre-authorized files -- mirrors the already-cited handshake.py/handshake_wire.py/handshake_evaluate.py 3-file precedent
- [Phase 06]: D-62 corrected: Step-0's handshake digest is a presence check, never equality -- a literal SCENT_DIGEST-style comparison would abort every real two-role game
- [Phase 06]: D-62 follow-up (coordinator-directed): Step-0 declaration CONTENT now travels the wire and is verified against its own claimed digest -- presence-only digest checking alone left verify_declaration with zero production callers
- [Phase 06]: Rule-36 audit coverage check (coordinator-directed): audit_peer_records now requires every fully-exchanged turn to appear in the peer's own FINAL_REVEAL, closing the empty-records evasion, while fixing a false-accusation bug for legitimately trailing commit-without-reveal turns
- [Phase 06]: GATE-6 measured: all three Sec10.4 criteria PASS with real, localhost-only, zero-env-var evidence (scripts/measure_gate6.py)

### Pending Todos

- 03-13..03-16 in `docs/phases/phase-3/TODO.md` (pre-flight assertions, cycle-based eval +
  alpha-beta, barrier rewrite, run-2 config, exact `turns_remaining` -- 03-11/03-12/03-13's
  rows are now code-complete, still unticked pending 03-24's reconciliation pass)

- Two subagent correction passes were cut off by API limits and never finished: re-measure the
  alpha-beta depth table against the real engine, and pin exact page/section for the Bansal
  δ-uniform ablation numbers and the ε-floor figures. Until then those specific numbers in
  `ALG-COMPARISON.md` and `TRAINING-METHODOLOGY.md` are UNVERIFIED — the qualitative findings
  and the independently-checked citations stand

### Blockers/Concerns

- ~~Team code (SUB-06)~~ **Decided: `khm-mn17`** (08-CONTEXT.md); per-game config naming still a league prerequisite
- Reporting (REPORT-01) is submission-critical: a missing/contradictory report zeroes both teams
- League opponents must be contacted early (this week) — scored games realistically Aug 11–12 post-exam
- **GATE-4 live confirmation (D-32) is blocked on `ANTHROPIC_API_KEY`** — not set on any machine
  this phase has run on. Phase 4 cannot be declared fully measured, and `/gsd:verify-work 4` must
  not run, until a human sets the key and runs `uv run python scripts/measure_gate4.py --live`,
  then updates `docs/phases/phase-4/GATE-4-MEASUREMENT.md`'s Live status section from that run.
- **GATE-5 (book Sec10.4 milestone 5) has TWO human-pending items, neither closeable from this
  machine** — Phase 5's code (05-01/05-02/05-03) is fully executed and tested, but
  `/gsd:verify-work 5` must not run until both close:
  1. **The smoke run** — `NGROK_AUTHTOKEN` / `PURSUIT_NGROK_DOMAIN` / `PURSUIT_TUNNEL_SECRET`
     are unset on every machine this phase has run on; a human with a real ngrok account runs
     `uv run python scripts/gate5_tunnel_smoke.py` and updates criterion 1 in
     `docs/phases/phase-5/GATE-5-MEASUREMENT.md` from the resulting evidence JSON.
  2. **The genuine remote round (CLOUD-02)** — inherently needs a second machine on a different
     network and a human operator; the full seven-step procedure is already written in
     `docs/phases/phase-5/GATE-5-MEASUREMENT.md`'s criterion 2 section.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Tooling correctness (pre-existing, out of scope for 03-11) | This file's YAML frontmatter does not actually parse (`yaml.safe_load` on `.planning/STATE.md`'s frontmatter raises `ScannerError: mapping values are not allowed here`) — the narrative fields (`stopped_at`, `last_activity`) are long unquoted plain scalars containing many `word: word` sequences, and a bare `: ` inside a plain YAML scalar always terminates it. Confirmed pre-existing: `git show HEAD:.planning/STATE.md` (the commit before this session touched the file) already fails the same way. ~85 colon-space occurrences repo-wide in this file make a full fix (block-scalar or quoted-string conversion of every long field) out of scope for a single plan's execution — it would mean rewriting the whole historical narrative's formatting. Consistent with this file's own established note ("`gsd-tools.cjs state advance-plan`/`update-progress` are NOT used on this file — hand-authored"), no tooling in this project currently parses this frontmatter as YAML, so the impact today is cosmetic/latent, not functional. One trivial, in-place instance was fixed while editing this session's own `stopped_at` text (`` `autonomous: false` `` → `` `autonomous=false` ``); no other pre-existing instance was touched. | ☐ open, latent (not blocking) | 2026-08-04, discovered during 03-11's STATE.md update |

## Session Continuity — READ THIS FIRST

**Next command: `/gsd:execute-phase 3`** (resumes at 03-13 — 03-11 and 03-12 are done and
committed). If the SessionStart banner reports the graph STALE, run
`graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/`
first, per CLAUDE.md (this session already did so after 03-12 landed: 3523 nodes/6406
edges/233 communities). **Do not run `/gsd:verify-work 3`** — GATE-4 stays unmet until
03-25 (the wave-7 human-operator checkpoint) remeasures it. **Do not run another training
job** until 03-13's pre-flight assertions are in place — 03-13 is next, not skippable.

Wave 1 status: 03-11 (graph primitives) and 03-12 (thief safety rule) done. 03-13
(turns_remaining + config surface), 03-14 (terminal signal) remain to finish wave 1.
Each subsequent execute-phase invocation should just pick up the next undone plan file
under `.planning/phases/03-blind-strategy-module-rl-policy/03-1[3-9]-PLAN.md` /
`03-2[0-5]-PLAN.md` in order — no further reading of the planning inputs below is needed,
they were only for authoring the 15 plans, which is already done.

Inputs the planner read before writing 03-11..03-25 (kept for reference, not re-reading
needed during execution):

| Document | What it settles |
|---|---|
| `docs/phases/phase-3/RUN-1-POSTMORTEM.md` | Why GATE-4 failed, measured; withdraws T4-followup-1/2 |
| `docs/research/PURSUIT-AND-EVASION-STRATEGY.md` | Thief design; cop-win ⟺ forest; barrier placement rules |
| `docs/research/TRAINING-METHODOLOGY.md` | Per-role γ, rewards, start states, self-play, pre-flight checks |
| `docs/research/ALG-COMPARISON.md` | Algorithm per role, features, state representation |

**Design decision that session changed:** RL is demoted from "the strategy" to "tuning ~60
evaluation weights". Strength comes from alpha-beta search over a cycle-based evaluation
(D-26) — 03-11's `pursuit.strategy.graph` package (this session) is the measurement layer
that evaluation is built on. This does NOT re-derive the phase breakdown (CLAUDE.md) — it
is still Phase 3, stage 3 of the book's seven.

**Uncommitted at session end:** `training/eval_aggregate.py` + edits to
`eval_stats.py`/`eval_report.py`/`evaluate.py` and two test files (the T4-followup-3
eval-honesty fix, tests green: 97 passed / 1 skipped); the four new docs above;
`.planning/phases/02-fastmcp-infrastructure/02-UAT.md`; `.pytest-tmp/` (scratch, should be
gitignored — it is the only `ruff` hit in the tree).

**Carried forward unchanged:** Phase-01 code review CR-01 still deferred; Phase-2 verify-work
(docs/phases/phase-2/TODO.md row 2-99 + root docs/TODO.md) still pending.

---

Last session: 2026-08-01T22:10:00+03:00
Stopped at: Completed 03-10-PLAN.md Tasks 1-3 (`tests/integration/{test_shortest_path,
  test_policy_fallback,test_strategy_pluggable,test_beats_baseline}.py`,
  `scripts/check_no_llm_in_strategy.{py,sh}`, `training/evaluate.py` +
  `training/eval_{scenarios,arms,stats,report}.py`, `artifacts/eval_scenarios.json`, and the
  STRAT-01..07 coverage audit in `docs/phases/phase-3/TODO.md` -- the §10.4 GATE-1/2/3
  integration tests, the GATE-4 evaluation CLI and committed eval scenario set, and the
  phase-wide requirements-coverage audit, STRAT-01..07). **Task 4 (blocking human-action
  checkpoint) intentionally NOT executed** — it is the overnight training run, and this
  automated session correctly stopped rather than attempting it. No SUMMARY.md exists for
  03-10 because the plan is genuinely incomplete.
  Carried forward: Phase-01 code review CR-01 still deferred; Phase-2 verify-work
  (docs/phases/phase-2/TODO.md row 2-99 + root docs/TODO.md) still pending — Phase 3
  planning/execution proceeded ahead of it per this session's instructions.
  docs/phases/phase-3/TODO.md rows 03-00..03-09 ticked, 03-10 row marked in-progress with
  Task 4 called out as the remaining blocker, plus 3 new unticked operator-step rows from
  03-RESEARCH.md Sec3; 03-96, 03-99 remain untouched (03-99 is /gsd:verify-work 3's job).
Resume file: None — Tasks 1-3 are fully committed (3 task commits: 1dea409, 8c8471f,
  b15d033) but 03-10 as a PLAN is not done. **Next step is the human operator running 03-10
  Task 4** (see docs/phases/phase-3/TODO.md's new operator-step rows, or
  03-10-PLAN.md's Task 4 block, for the exact commands and Windows setup: redirect output to
  a file since console QuickEdit suspends the process on click, confirm
  training.artifacts_dir resolves outside OneDrive, exclude that directory from Defender
  real-time scanning, confirm sleep is disabled, then `uv run python -m training.loop
  2>&1 | tee run.log`, inspect curves via `training/plot_curves.py`, measure the gate via
  `uv run python training/evaluate.py --full --assert-gate`, and only on a pass promote the
  tables + fill README's placeholder numbers). Once that lands, either re-run
  /gsd:execute-phase 3 to have it write 03-10-SUMMARY.md and close the phase, or write the
  SUMMARY directly — either closes out Phase 3's final plan.
  **Post-session fix (commit 89ddcbb)**: the operator tried
  `uv run python -m training.harness` per 03-10-PLAN.md's literal Task 4 text and it exited
  immediately doing nothing -- 03-08 built `run_training()` (in `training/loop.py`, not
  `harness.py`) but never wired a runnable entry point to it anywhere in `training/`.
  Added `main()`/`_load_run_config()` to `training/loop.py` (not `harness.py`, to avoid a
  circular import since `loop.py` already imports from `harness.py`); the real command is
  `uv run python -m training.loop`. Verified with a 6-episode run in an isolated temp dir
  before adding `tests/unit/training/test_loop.py::test_load_run_config_reads_the_real_
  committed_config_files` and `::test_main_runs_training_via_load_run_config_and_prints_
  the_final_episode` (the latter mocks only `run_training` itself, so `_load_run_config`'s
  real config-file resolution stays covered). `docs/phases/phase-3/TODO.md`'s op-1 row
  corrected to match. Full gates re-verified green after the fix: ruff 0, line-limit clean,
  427 passed / 2 skipped, coverage 96.43%.
  Per-day sequence from Phase 3 on: /gsd:graphify → [/gsd:ai-integration-phase N for 3 & 4]
  → /gsd:plan-phase N --chunked → /gsd:execute-phase N → /gsd:verify-work N. Note: the
  CLAUDE.md-mandated graphify refresh for this plan's new code already ran this session
  (graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md}
  .planning/graphs/) -- 3190 nodes / 5849 edges / 201 communities, GRAPH_REPORT.md committed
  alongside the Task-3 docs commit.
  Note on tooling: per 03-03's finding, `gsd-tools.cjs state advance-plan`/`update-progress`
  are NOT used on this file -- this update was hand-authored, matching the established
  per-plan narrative format.

---

Last session: 2026-08-04T12:31:00+03:00
Stopped at: Completed 03-11-PLAN.md (graph primitives, run-2 wave 1's first plan) in
  full. All 3 tasks executed TDD (tests written and confirmed red before each
  implementation went green), each committed atomically: Task 1 `components.py`
  (`12be2e4`), Task 2 `cycles.py` (`52c85f2`), Task 3 `territory.py` (`b4b06fa`). A
  4th commit (`af5f0de`) closed a Rule-2 coverage gap found during final verification
  (two documented contract branches -- the DFS-root cut-vertex case and
  `cycle_rank(frozenset())==0` -- had no direct test; 2 tests added, package coverage
  98%->100%). `03-11-SUMMARY.md` written. Full repo gates green: `ruff check .` 0
  violations, line-limit clean (new files 100/37/55/32 code lines), 456 passed / 2
  skipped (the pre-existing GATE-4 skip, untouched), coverage 97.05% (>=85% floor).
  Graphify rebuilt and `GRAPH_REPORT.md` refreshed (3457 nodes/6273 edges/234
  communities). `docs/phases/phase-3/TODO.md` deliberately not touched -- its
  03-11..03-16 row numbering predates the 15-plan wave breakdown and reconciling it is
  03-24's ("triplet refresh") explicit job.
Resume file: None -- 03-11 is fully committed and closed. **Next step is
  `/gsd:execute-phase 3`**, which resumes at **03-12** (thief safety rule — never step
  into `N[cop]`; see `.planning/phases/03-blind-strategy-module-rl-policy/03-12-PLAN.md`).
  Waves 1-6 remain autonomous; wave 7 (`03-25`) is the human-operator checkpoint (the
  overnight training run and the real GATE-4 remeasurement) -- do not run
  `/gsd:verify-work 3` before it passes.

---

Last session: 2026-08-04T13:00:00+03:00
Stopped at: Completed 03-12-PLAN.md (thief safety rule -- never step into N[cop], run-2
  wave 1's second plan) in full. Both tasks committed atomically: Task 1 `safety.py`
  (`71b201d`, test-first: `test_safety.py` confirmed red against a `ModuleNotFoundError`
  before the module existed, green after -- 7 unit tests), Task 2 wiring + regression
  guard (`20d87f6`). `src/pursuit/strategy/safety.py` -- `closed_neighbourhood`/
  `safe_moves`, pure (D-03), never-empty guarantee, docstring carries the full D-31
  296/300=0.987 vs 283/300=0.943 provenance plus the unsoftened "did not fully
  reproduce, lost 3/20, flawed control" caveat. `fallback.py::_evade` filters legal
  moves through `safe_moves` before ranking with the UNCHANGED
  `(unreachable?, distance, onward)` key -- filter-then-rank, `_pursue` byte-identical.
  `tests/unit/strategy/test_fallback.py` needed zero changes (verified before/after,
  all 6 cases hold under the filtered behaviour). New
  `tests/integration/test_thief_safety.py`: non-vacuous 160-game regression guard, two
  arms differing ONLY by `monkeypatch.context()`-scoped patches of `fallback.safe_moves`
  (real spy vs no-op) against the same 20 committed GATE-4 scenarios + 60 seeded random
  starts (`n=60`, `REGRESSION_TOLERANCE=0.05`, `seed=314159`, named test-local
  constants, D-19); asserts grid filtered-survival >= unfiltered, random-start rate
  within one noise band, filter-bound counter > 0 (non-vacuous), and the per-turn
  N[cop] invariant across all 160 games via a spy wrapper. Does not reproduce D-31's
  own flawed disabled-barrier control. `03-12-SUMMARY.md` written (self-check PASSED).
  One deviation, a documentation correction (not a code fix): the plan's own
  ~100ms/game timing estimate did not reproduce -- measured ~34-38s for the 160-game
  suite, `cProfile`-traced to 03-07's pre-existing `choose_barrier` (out of this plan's
  scope), not this plan's own code. Recorded honestly in the test module's own
  docstring; `n=60` was NOT reduced and barrier placement was NOT disabled to chase the
  stale target. Full repo gates green: `ruff check .` 0 violations, line-limit clean
  (new files 50/76/157 code lines, `fallback.py` still well inside its own ceiling),
  464 passed / 2 skipped (same 2 pre-existing skips as 03-11), coverage 97.95%
  (>=85% floor), `safety.py`/`fallback.py` both individually 100% covered. Full-repo
  `--cov` run took 7m47s on this Windows machine, confirmed genuinely CPU-bound
  throughout (`Get-Process ... CPU`), not the known Windows stdio-hang pattern.
  Graphify rebuilt (3523 nodes/6406 edges/233 communities) and `GRAPH_REPORT.md`
  refreshed and committed. `docs/phases/phase-3/TODO.md` deliberately not touched --
  same rationale as 03-11 (03-24's "triplet refresh" job).
Resume file: None -- 03-12 is fully committed and closed. **Next step is
  `/gsd:execute-phase 3`**, which resumes at **03-13** (turns_remaining + config
  surface; see `.planning/phases/03-blind-strategy-module-rl-policy/03-13-PLAN.md`).
  Waves 1-6 remain autonomous; wave 7 (`03-25`) is the human-operator checkpoint (the
  overnight training run and the real GATE-4 remeasurement) -- do not run
  `/gsd:verify-work 3` before it passes.
  Note on tooling: per 03-03's finding and 03-11's precedent, `gsd-tools.cjs state
  advance-plan`/`update-progress` are NOT used on this file -- this update was
  hand-authored, matching the established per-plan narrative format.
