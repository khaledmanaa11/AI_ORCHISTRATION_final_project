---
phase: 05-cloud-exposure-and-tunneling
verified: 2026-08-14T15:20:00Z
status: human_needed
score: 18/19 truths verified; §10.4 criterion 2 PENDING a second physical machine (05-08 not yet run)
re_verification:
  replaces: "05-VERIFICATION.md dated 2026-08-09T05:58:21Z (status human_needed, 16/16). That
    report predates BOTH §10.4 criteria carrying real evidence: criterion 1 was PENDING then
    and PASSED on 2026-08-09T09:41:20Z; criterion 2 was PENDING-untried then and has since
    been ATTEMPTED (2026-08-13, two machines, two networks) and FAILED on the verdicts-agree
    clause. That failure produced 05-UAT.md gaps G1-G5 plus deferred items, and six
    gap-closure plans (05-04, 05-05, 05-06, 05-07, 05-09) have landed since. None of that
    existed in the 2026-08-09 report, whose 16 truths covered only plans 05-01..05-03."
  previous_status: human_needed
  previous_score: "16/16 automated must-haves"
  previous_truths_regression_checked: true
  gaps_closed:
    - "G1 (05-04) -- a failed OWN final-reveal send records audit_incomplete and accuses nobody when a board outcome exists; the audit continues; corrected game_over; bounded Table-19 linger"
    - "G2 (05-05) -- one negotiated game id across log stem, ledger stem, declaration filenames and committed state.game_id; the audit reads the committed state record; candidate set captured before the rebind, on both roles"
    - "G3 (05-06) -- inbound HINT envelopes are written to the wire log with our turn on top and the peer's turn nested"
    - "G4 (05-06) -- both sides stamp the turn actually played, the responder actually decodes, and no hint is composed for an already-resolved turn"
    - "G5 (05-07) -- startup WARNING names the env var only, llm_name reflects real capability, declaration still exactly 10 fields, fallback behaviour unchanged"
    - "Deferred #1 (05-09) -- transport failures contained including the WRAPPED connect shape; LocalProtocolError/UnsupportedProtocol still raise; no catch-all"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "GATE-5 criterion 2 (CLOUD-02) -- remote round ATTEMPT 2, the human-run plan 05-08.
      Follow docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md: machine A starts with the tunnel and
      shared secret, machine B on a different network points PURSUIT_OPPONENT_URL at A's public
      URL, play one full round to a real outcome, retain both logs, both ledgers, both
      declaration pairs, and BOTH consoles."
    expected: "Both sides' logs/<role>/<game_uid>.jsonl exist under ONE shared game uid, both
      ledgers and both declaration filenames carry that same uid, and the two sides' final
      verdicts AGREE (no technical_win on a side whose peer answered). Then record the run
      field-by-field in GATE-5-MEASUREMENT.md as Attempt 2 and tick the gate."
    why_human: "Requires a second physical machine on a different network and a human operator
      on each side. Confirmed again this pass: no simulated-remote-machine path exists anywhere
      in scripts/ or tests/, by design. The local two-peer proof (scripts/dev_launch.py) now
      passes cleanly, which is a necessary but NOT sufficient condition -- attempt 1 also
      passed locally before it failed remotely."
open_deferred_items:
  - id: 2
    summary: "agent_lifecycle.py has two lines of headroom (measured 148/150 at this HEAD)"
    severity: minor
  - id: 3
    summary: "commit_pack.verify_reveal is shape-fragile against peer data; contained only at
      audit._audit_one's verify_reveal call. AMENDED THIS PASS: the note's claim that 'nothing
      is exposed today' is an over-claim -- see new item 7."
    severity: major
  - id: 4
    summary: "test_late_peer_teardown.py's non-vacuity probe is load-sensitive and flakes under
      concurrent pytest; not reproduced on a quiet box this pass"
    severity: minor
  - id: 5
    summary: "An in-game ladder exhaustion accuses the peer even when the fault was ours
      (examined and accepted; pre-existing NET-06 policy)"
    severity: accepted-residual
  - id: 6
    summary: "A 5xx/429 from the peer or the tunnel is an uncaught httpx.HTTPStatusError
      mid-game; needs a status-code policy decision"
    severity: major
  - id: 7
    summary: "NEW, found this pass: audit_peer_records raises (KeyError/TypeError) on a
      malformed peer FINAL_REVEAL records payload -- at entry['turn'], _missing_turns and the
      final sort, all OUTSIDE 05-05's verify_reveal containment. Measured by probe. A foreign
      league implementation whose record shape differs kills our process before any verdict is
      written: rule 36 against US, the exact artifact 05-04/05-09 exist to prevent. Not a
      false-accusation path and not one of G1-G5."
    severity: major
---

# Phase 5: Cloud Exposure and Tunneling — Verification Report (re-verification)

**Phase Goal:** Expose the local FastMCP server publicly via ngrok or Localtonet.
**Verified:** 2026-08-14
**Status:** human_needed
**Re-verification:** Yes — this file REPLACES `05-VERIFICATION.md` dated 2026-08-09T05:58:21Z.

## What changed since the 2026-08-09 report

The superseded report verified plans 05-01..05-03 and recorded **both** §10.4 criteria as
PENDING. Three things have happened since, none of which that report could have known:

| | 2026-08-09 report | Now |
|---|---|---|
| §10.4 criterion 1 | PENDING (no ngrok account on this box) | **PASS** — real run 2026-08-09T09:41:20Z, `gate5_smoke_evidence.json` `verdict: PASS` |
| §10.4 criterion 2 | PENDING, never attempted | **PENDING, attempt 1 RAN 2026-08-13 and FAILED** the verdicts-agree clause |
| Code under verification | 05-01..05-03 (tunnel, secret, gate script) | + 05-04, 05-05, 05-06, 05-07, 05-09 — six gap-closure plans, 14 new/relocated source modules |
| Verified truths | 16 (all transport/config-level) | 19 (11 of them about behaviour the remote round broke) |

Attempt 1 is the reason this file exists. The transport worked — a full 5-turn game to a real
capture across two networks through two ngrok tunnels — but the two sides recorded
**disagreeing verdicts** and their logs carried **different game UIDs**. That produced
`05-UAT.md` gaps G1–G5. Every claim in the six gap-closure SUMMARYs was re-checked against
source and against live runs below; none was taken on trust.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence (measured, not quoted) |
|---|---|---|---|
| 1 | **G1** A failed OWN final-reveal send, with a board outcome standing, records a non-accusatory `audit_incomplete` — never an accusation | ✓ VERIFIED | `agent_audit_wiring.py:129-133`: `if send_verdict is not None: if board_outcome is None: return record_technical_loss(...)` / `record_audit_incomplete(...)`. `agent_audit_verdict.py:59-76` writes `EventType.AUDIT_INCOMPLETE` with reason `own_final_reveal_send_failed`, a string deliberately **not** a `TechnicalWinReason` member. Returns `None`, so the board outcome stands |
| 2 | **G1** The fix reaches PRODUCTION, not just the harness | ✓ VERIFIED | `agent_entrypoint.py:110` — `audit_outcome = await run_final_audit(ctx, board_outcome=outcome)`, where `outcome` is `run_turn_loop`'s own return from `:100`. Read in source, not inferred. Repo-wide grep for `board_outcome` shows the production call site plus 6 test files. *(See Anti-Patterns: no test pins this kwarg — a regression here would ship green.)* |
| 3 | **G1** The audit CONTINUES after a failed push instead of bailing | ✓ VERIFIED | `agent_audit_wiring.py:133-160` — `record_audit_incomplete` has no `return`; control falls through to `receive_final_reveal`, both `observed()` extractions and both `audit_peer_records` directions |
| 4 | **G1** Every technical loss recorded after the turn loop appends a CORRECTED `game_over` | ✓ VERIFIED | `agent_audit_verdict.py:93-100` — `record_technical_loss` appends the technical-win record **and** `turn_events.game_over_record(outcome=Outcome.TECHNICAL_LOSS)`. The mismatch path (`:142`) delegates here rather than re-implementing, so the two paths cannot drift |
| 5 | **G1** The linger is bounded by `NetworkParams.response_timeout`/`backoff_seconds` with **zero** new config keys; watchdog stopped first; runtime stopped in a `finally` | ✓ VERIFIED | `agent_teardown.py:66-76` — total cap `ctx.net.response_timeout`, quiet interval `min(ctx.net.backoff_seconds, remaining)`, **no numeric literal in the file**. `agent_entrypoint.py:134-138` — `stop_watchdog(ctx)` then `try: await linger_for_peer(ctx) finally: await stop_runtime(ctx)`. `git diff 950b0ed..HEAD -- config/` is **empty** — no new leaf in any `network.json` |
| 6 | **G2** ONE negotiated id governs log stem, ledger stem, declaration filenames AND committed `state.game_id` | ✓ VERIFIED (live) | `scripts/dev_launch.py` run this pass: `logs/police/` and `logs/thief/` each hold `59cbf70cf98842bd.jsonl`, `59cbf70cf98842bd.ledger.jsonl`, `declaration_59cbf70cf98842bd.json` — **one stem, both sides, all four artifact classes**. Both ledgers' committed `state.game_id` sets are `{'59cbf70cf98842bd'}` (5 entries each) |
| 7 | **G2** `_audit_one` validates the peer's committed `state.turn`, `state.role` and `state.game_id` | ✓ VERIFIED | `audit.py:94-98` calls `state_binding_detail` **after** the re-hash and **before** the trailing-commit early return (placement is the exact bug shape 06-05 fixed once). `audit_state.py:101-118`: `claimed_turn != turn`; `state.role == forbidden_role` (a NEGATIVE check, never equality with our vocabulary); `claimed_game not in candidate_game_ids`. Every field read with `.get()`, so peer data yields a named mismatch, not a `KeyError` |
| 8 | **G2** The candidate set is captured INSIDE `adopt_negotiated_game_id` BEFORE it rebinds `ctx.game_uid`, and a test pins it for BOTH roles | ✓ VERIFIED | `game_identity.py:157-159` builds `{ctx.game_uid, result.peer_game_id}`; the rebind is at `:166`, **seven lines later**. Pinned twice: `tests/integration/test_game_id_negotiation.py:127` asserts `ctx_a.candidate_game_ids == ctx_b.candidate_game_ids == {UID_A, UID_B}` after a real two-peer handshake, and `tests/unit/test_audit_state_wiring.py:53/72` re-derives it through the production path plus a convention-swap control. Both pass |
| 9 | **G3** Inbound HINT envelopes are on the wire log, our turn on top, the peer's turn nested | ✓ VERIFIED (live) | `turn_hint_buffer.py:147-153` calls `turn_commit_send.log_received(...)` **before** the drop guard at `:154`. Live `dev_launch` log: police holds `message_received`+`hint` at `log_turn 1..4` with `env_turn 0..3`; thief holds five, `log_turn 1..5` / `env_turn 0..4`. Pre-fix both were zero |
| 10 | **G4** Both sides stamp the turn actually played, and a responder actually decodes | ✓ VERIFIED (live) | `turn_actions.py:92` stamps `pending.turn` on the responder branch (not the post-`maybe_resolve` `ctx.state.turn`). Live log: police hints `0,1,2,3,4`, thief hints `0,1,2,3` — each equal to the turn played. The **thief** (responder) now shows `incoming_hint.text` non-null on 3 of 4 `language_turn` records (`hint decoded to no evidence` — decode ran; `no_evidence` is the honest keyless-box outcome). Pre-fix the thief was 0-of-5 `no_hint` in every game |
| 11 | **G4** No hint is composed for an already-resolved turn | ✓ VERIFIED | `turn_actions.py:88` and `:127` — `if ctx.language is not None and outcome is None:` on **both** branches, with the initiator branch documented as behaviour-neutral so the two read as one rule |
| 12 | **G5** Startup WARNING when the LLM is off for lack of a key — env var NAME only, never its value | ✓ VERIFIED (live) | `language_wiring.py:132-137` — `_log.warning` interpolates `API_KEY_ENV_VAR` twice and `provider_cls.__name__`; `has_api_key()` (`client.py:28-36`) returns a bare `bool` and the value is never in scope. Observed live on this keyless box during `measure_gate6.py`: the warning reached bare stderr with no `logging.basicConfig` anywhere |
| 13 | **G5** `llm_name` reflects real capability; the declaration is still **exactly 10 fields**; fallback behaviour unchanged | ✓ VERIFIED (live) | `language_wiring.declared_llm_name:77-80` returns `LLM_NAME_TEMPLATE_FALLBACK` for a template provider **or** no key. Live Step-0 print from `measure_gate6.py`: `llm_name: 'template-fallback (no LLM calls)'` inside a declaration with exactly the 10 `DeclarationField` keys. The four Phase-4 `test_llm_degradation.py` cases pass **unedited**. `docs/PRD_deception.md:186` carries the new first-person STYLE_GUIDE line verbatim from `bluff_prompt.py:26-28` |
| 14 | **Deferred #1** Transport failures contained, including the WRAPPED connect shape; `LocalProtocolError`/`UnsupportedProtocol` still RAISE; no catch-all | ✓ VERIFIED | `deadline_errors.py:118-122` `RETRYABLE_TRANSPORT_ERRORS = (McpError, DeadlineExpired, httpx.TransportError)`; `:131-135` `RAISE_UNRETRIED_ERRORS = (ToolError, httpx.LocalProtocolError, httpx.UnsupportedProtocol)`; `unwraps_to_retryable:142-153` decides on the **direct cause** only. `deadline.py:146-157` spells the raise-first clause out **before** the retryable one and narrows `RuntimeError` by cause, never by class. Read both files end-to-end: **no bare `except:` and no `except Exception` anywhere in either**. `httpx>=0.28.1` is a declared dependency (`pyproject.toml` diff) |
| 15 | **Rules 16/22** No honest peer can be falsely accused by anything added in this phase | ✓ VERIFIED, with three named residuals | See the dedicated section below — this got the deepest pass |
| 16 | **Rule 38** No fabricated numbers; GATE-5-MEASUREMENT.md records criterion 1 PASS and criterion 2 PENDING-with-attempt-1-failed | ✓ VERIFIED | `GATE-5-MEASUREMENT.md` header states criterion 1 PASS with the evidence link and criterion 2 PENDING, has a full "Attempt 1 — 2026-08-13, completed round, criterion NOT yet closed" section naming the disagreement and the two differing UIDs, and keeps "the phase is not fully measured while either row reads PENDING". Every SUMMARY test count re-measured and matched (05-07 claims 1327/96.37%; measured **1327 passed, 96.37%**). `config/*/games_played*.json` is gitignored and untouched by any plan; the counters advanced only by genuinely playing games |
| 17 | Phase 6 does not regress | ✓ VERIFIED (live) | `uv run python scripts/measure_gate6.py` → `criterion_1_four_phases_commit_reveal: PASS`, `criterion_2_hash_nonce_mismatch_technical_loss: PASS`, `criterion_3_step0_verified_before_move_1: PASS` |
| 18 | **§10.4 criterion 1** — each peer reachable on the public internet | ✓ VERIFIED | `docs/phases/phase-5/gate5_smoke_evidence.json`, real run 2026-08-09T09:41:20Z: `verdict: PASS`, `public_url: https://perdurable-mireille-nonzoologically.ngrok-free.dev`, `url_is_https_and_matches_domain: true`, `authorized_request_reached_mcp: true`, `unauthorized_request_rejected_403: true`, `round_trip_seconds: 1.859` |
| 19 | **§10.4 criterion 2** — a remote agent plays a full round through the tunnel | ? HUMAN NEEDED | Attempt 1 (2026-08-13) played the round but failed the verdicts-agree clause. All five diagnosed causes are now closed (truths 1–13) and the local two-peer proof is clean, but **only a second physical machine can close this**. Plan 05-08 has not been run |

**Score: 18/19 truths verified.** The one open item is the phase's own book criterion, not an
implementation gap.

### The local two-peer proof (`scripts/dev_launch.py`), run this pass

Exit **0**. Both sides on the same stem `59cbf70cf98842bd`:

| Side | Records | Event mix | Last three records |
|---|---|---|---|
| police | 42 | 20 sent / 14 received / 5 language_turn / 1 illegal_transition / 1 game_over / 1 audit_verdict | `message_received`, `game_over capture`, `audit_verdict matched=True` |
| thief | 41 | 19 sent / 15 received / 4 language_turn / 1 illegal_transition / 1 game_over / 1 audit_verdict | `game_over capture`, `message_received`, `audit_verdict matched=True` |

**Zero `technical_win` records and zero `audit_incomplete` records on either side.** This is the
exact artifact class attempt 1 failed to produce, now produced locally. (The trailing Windows
`WinError 995` / lifespan `CancelledError` tracebacks are the documented proactor teardown
noise, after exit code 0 was computed.)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pursuit/network/agent_teardown.py` | bounded post-audit grace window | ✓ VERIFIED | 77 lines, zero numeric literals, pulls through `deadline.wait_for_opponent` so `deadline._bounded` stays the one `asyncio.wait_for` site (QUAL-02) |
| `src/pursuit/network/agent_audit_verdict.py` | `record_audit_incomplete` + corrected `game_over` | ✓ VERIFIED | `_OWN_SEND_FAILED` deliberately not a `TechnicalWinReason`; `_verdict_record` shared by both record shapes (no duplication) |
| `src/pursuit/network/agent_audit_wiring.py` | `run_final_audit(board_outcome=...)`, candidate set passed through | ✓ VERIFIED | 134 code lines after 05-07 split `declared_llm_name` out; the same candidate set serves both directions, `forbidden_role` the only per-direction difference |
| `src/pursuit/network/game_identity.py` | `GameIdentity`, `negotiated_game_id`, `adopt_negotiated_game_id`, relocated sinks | ✓ VERIFIED | Mutable binding read at CALL time by both JSONL sinks; `identity is None` keeps every pre-existing caller byte-identical |
| `src/pursuit/security/audit_state.py` | D-60 state record, READ | ✓ VERIFIED | 119 lines; the membership rationale and its **three** limitations are in source, not implied |
| `src/pursuit/network/turn_hint_buffer.py` | inbound HINT logging + lookback window | ✓ VERIFIED | `_HINT_LOOKBACK_TURNS = 1` with its derivation in source; `_usable_stamp` refuses non-int peer stamps (bool included) so `record_hint` cannot raise into a caller that catches nothing |
| `src/pursuit/network/deadline_errors.py` | NET-06 exception taxonomy | ✓ VERIFIED | Both tuples immutable; `unwraps_to_retryable` narrows by cause; every member's inclusion argued in source |
| `src/pursuit/services/llm/client.py` | `has_api_key()` presence-only | ✓ VERIFIED | Returns `bool(os.environ.get(API_KEY_ENV_VAR))`; empty string counts as absent, agreeing with `build_client` by construction |
| `tests/integration/test_late_peer_teardown.py` + `late_peer_harness.py` | sequenced two-peer proof over real sockets | ✓ VERIFIED | Real loopback sockets, real `write_declaration`, A's teardown mirrors `run_agent`'s three steps exactly; the `linger=False` revert probe lives in the harness, not by editing source |
| `tests/integration/test_hint_delivery.py` | two-peer stamp + decode proof | ✓ VERIFIED | Asserts police hints == police reveals, thief hints == thief reveals[:-1], and that **both** sides carry ≥1 non-`no_hint` incoming hint |
| `tests/unit/test_audit_state_binding.py` / `test_audit_state_wiring.py` | forgery cases + fairness controls | ✓ VERIFIED | 4 forgery cases; controls for an honest peer, a peer using the `cop` vocabulary, a peer that published no game_id, and a convention-swapping peer through the REAL set builder |
| `docs/phases/phase-5/GATE-5-MEASUREMENT.md` | both criteria, honest statuses | ✓ VERIFIED | Criterion 1 PASS field-by-field; criterion 2 PENDING with attempt 1 recorded in full, including the two differing UIDs |
| `.planning/graphs/GRAPH_REPORT.md` | refreshed after the phase's code landed | ✓ VERIFIED | Committed in `460304f` (2026-08-14 17:43); `linger_for_peer`, `adopt_negotiated_game_id`, `state_binding_detail`, `has_api_key` all present |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `agent_entrypoint.py:110` | `agent_audit_wiring.run_final_audit` | `board_outcome=outcome` — **the production wiring** | ✓ WIRED (source-read; not test-pinned, see below) |
| `agent_entrypoint.py:134-138` | `agent_teardown.linger_for_peer` | `stop_watchdog` → `try: linger finally: stop_runtime` | ✓ WIRED |
| `agent_teardown.py:66-73` | `shared/network_config.NetworkParams` | `ctx.net.response_timeout` / `ctx.net.backoff_seconds`, no literals | ✓ WIRED |
| `agent_entrypoint.py:98` | `game_identity.adopt_negotiated_game_id` | after `result.agreed`, before `write_declaration`/`run_turn_loop` | ✓ WIRED |
| `game_identity.py:162-169` | `turn_commit_ledger.ledger_path` | renaming `ctx.log_path` moves the D-64 ledger stem (`log_path.stem`) | ✓ WIRED (measured: one stem across all four artifacts) |
| `agent_audit_wiring.py:153-159` | `security/audit.audit_peer_records` | `candidate_game_ids=ctx.candidate_game_ids`, `forbidden_role` per direction | ✓ WIRED |
| `turn_hint_buffer.py:147` | `turn_commit_send.log_received` | inbound hint uses the commit path's own record shape with `local_turn` | ✓ WIRED (measured in both live logs) |
| `turn_actions.py:92` | `commit_state.pending_action.turn` | responder stamps the turn it committed under | ✓ WIRED |
| `language_wiring.py:124` and `:78` | `services/llm/client.has_api_key` | warning and declared name key off the same probe | ✓ WIRED |
| `deadline.py:146-157` | `deadline_errors` tuples | raise-first clause before the retryable one; `RuntimeError` narrowed by cause | ✓ WIRED |
| `bluff_prompt.STYLE_GUIDE` | `docs/PRD_deception.md:186` | quoted verbatim, changed in the same commit | ✓ WIRED |

### Rules 16/22 — the false-accusation sweep

This got the hardest look, as instructed. Every accusatory path reachable from this phase's
changes was traced from the accusing statement backwards to the peer behaviour that triggers it.

**Clean:**

- **`state.role`** is a NEGATIVE check (`state.role == forbidden_role`), never equality with our
  vocabulary. An honest opponent writing `"cop"` instead of `"thief"` is matched — pinned by
  `test_control_a_peer_using_a_different_role_vocabulary_is_still_matched`.
- **`state.game_id`** is checked by MEMBERSHIP in `{our minted uid, the id the peer published}`,
  captured before the rebind. Traced on both roles by hand: police keeps its own id and the set
  is `{own, peer}` → a thief that adopts ours passes, a thief that keeps its own passes; thief
  adopts the peer's id and the set is still `{own_pre_adoption, peer}` → a police that keeps its
  own passes, a police that adopted ours passes. A peer that published **no** id sets the whole
  check to `None` (skipped) — no accusation. Our own records are in the set on both roles by
  construction, so `self_audit` cannot mis-fire either.
- **`state.turn`** compares two numbers the **peer itself** supplied (its ledger entry's turn vs
  its own committed state's turn). Internal consistency, imposing nothing.
- **A failed own push** is now the non-accusatory `audit_incomplete` (truth 1), and the deliberate
  accusatory branches (`ToolError` → `PEER_PROTOCOL_ERROR`, a withheld peer reveal → rule 36, a
  real `AUDIT_HASH_MISMATCH`) are each about an act the peer actually performed.
- **`LocalProtocolError`/`UnsupportedProtocol`** now raise instead of burning the ladder and ending
  in a `TechnicalWin` against a peer that never received a valid request — this phase **removed** a
  false-accusation path here.
- **Hints** never produce a verdict: 04-12's deviation made late/duplicate hints a silent drop, and
  05-06 widened the window rather than narrowing it, so no hint timing can forfeit a game.

**Three residuals, stated rather than hidden:**

1. *(Documented, limitation (c) in `audit_state.py`)* A peer deriving a **third** id — a hash of
   both, the lexicographic min — is accused under any candidate-set rule. Weighed and declined in
   source; no mechanism covers an unbounded space of conventions.
2. *(Documented, limitation (b))* A peer that publishes a **prior game's** id at handshake satisfies
   membership. Contained only by the move cross-check, never by the hash.
3. *(Deferred item #5, examined and accepted)* An in-game ladder exhaustion still names the peer
   `OPPONENT_UNRESPONSIVE` when the fault was our own uplink. Pre-existing NET-06 policy; 05-09
   makes an accidental gap consistent with it rather than widening it, and the alternative it
   replaced was a crash that loses under rule 36 with no verdict at all.

**Verdict: no false-accusation path is introduced by this phase, and one is removed.**

### Requirements Coverage

| Requirement | Status | Blocking issue |
|---|---|---|
| CLOUD-01 (each peer reachable via tunnel) | ✓ SATISFIED | None — code complete and criterion 1 carries a real measured PASS |
| CLOUD-02 (remote agent plays a full round) | ? NEEDS HUMAN | Code complete; all five attempt-1 causes closed and locally proven. Needs attempt 2 on a second machine (plan 05-08) |

### Anti-Patterns / Findings

| File | Severity | Finding |
|---|---|---|
| `src/pursuit/security/audit.py:67`, `:118`, `:158` | 🛑 **Blocker for league day, not for this phase's gaps** | `audit_peer_records` **raises** on a malformed peer FINAL_REVEAL payload. Measured by probe against the shipped function: missing `turn` key → `KeyError: 'turn'`; `records` a string → `TypeError`; an entry that is a string → `TypeError`; `turn` a string → `TypeError` at the final `sort`. All three sites sit **outside** 05-05's `verify_reveal` try/except. `agent_entrypoint`'s guard is `except ToolError`, so this kills the process before any verdict is written — rule 36 against US, the exact artifact 05-04/05-09 exist to prevent. **Not** a false accusation, and **not** one of G1–G5, so it is logged as new deferred item **7** rather than a gap against this phase's must_haves |
| `.planning/phases/05-cloud-exposure-and-tunneling/deferred-items.md` item 3 | ⚠️ Warning | The note's closing claim — *"The containment above means nothing is exposed today"* — is an **over-claim**, refuted by the probe above. The containment covers the `verify_reveal(...)` call only. The note needs amending; recorded here so the correction is not lost |
| `src/pursuit/network/agent_entrypoint.py:110` | ⚠️ Warning | The production `board_outcome=outcome` wiring is **not pinned by any test**. `tests/unit/test_agent_entrypoint.py`'s four cases never assert the kwarg, and `dev_launch.py` would still pass without it (the linger prevents the failure locally). This is precisely the "wired through tests only" hazard the plan called out, inverted: the production wiring is present, but nothing would catch its removal. Recommend one assertion on the kwarg |
| `docs/PRD_commit_reveal.md` | ℹ️ Info | Describes the D-60 state record as written (`:110-123`) but was not updated with the **read** side. The membership choice and its three limitations exist only in `audit_state.py`'s source comment. Root `docs/{PRD,PLAN,TODO}.md` are also unchanged since `950b0ed` — doc debt for verify-work, not a code gap |
| `src/pursuit/network/turn_commit_wait.py:146`, `:119-126` | ℹ️ Info (pre-existing) | "A duplicate/unexpected arrival is tolerated jitter — dropped." A peer's FINAL_REVEAL arriving while we are still mid-turn-loop would be consumed and discarded, after which our own `receive_final_reveal` would exhaust and accuse. Narrow and pre-existing (Phase 6), not reachable in the runs measured here; noted so it is on record |
| All Phase-5 source files | — | Scanned for `TODO`/`FIXME`/`XXX`/`HACK`/`PLACEHOLDER`/`return null`-shaped stubs: **zero matches**. No stub, no placeholder, no console-log-only implementation anywhere in the 14 modules this phase touched |

### Standing Gates — re-run fresh on this machine

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed!** (0 violations) |
| `uv run pytest tests/ --cov` | **1327 passed, 0 failed, 96.37% coverage**, 127.94 s (quiet box). Matches 05-07-SUMMARY's claim exactly. A first run, launched concurrently with the ruff/line-limit/no-LLM checks, showed 1326 passed + 1 failed (`test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`, a per-turn **time budget** assertion); re-run alone it passes in 0.35 s. Load flake, attribution measured, nothing relaxed |
| `bash scripts/check_line_limit.sh` | exit **0**, no output (clean). `agent_lifecycle.py` measured **148/150** — deferred item 2 is accurate |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `uv run python scripts/measure_gate6.py` | **all three criteria PASS** — Phase 6 has not regressed |
| `uv run python scripts/dev_launch.py` | exit **0**; both sides end on `audit_verdict matched=true`; one shared game uid; zero technical wins |
| Targeted gap-closure suites (8 files) | **33 passed** in 35.46 s |
| `git diff 950b0ed..HEAD -- config/` | **empty** — no new numeric leaf, no new key, no secret |

Baseline check requested: the last independently-measured figure was **1308 passed / 96.36%**
before 05-07 landed. Measured now: **1327 / 96.37%** — **+19 tests**, coverage up 0.01 pp,
which is exactly what 05-07-SUMMARY claims.

### Human Verification Required

#### 1. GATE-5 criterion 2 — remote round, attempt 2 (plan 05-08)

**Test:** `docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md`. Machine A starts with the tunnel and
shared secret; machine B, on a different network, points `PURSUIT_OPPONENT_URL` at A's public
URL; play one full round to a real outcome; retain both logs, both ledgers, both declaration
pairs **and both consoles** (attempt 1 lacked machine B's console, its ngrok agent log, and a
clock-skew note).

**Expected:** all four artifacts under **one** shared game uid; the two sides' final verdicts
**agree**; no `technical_win` on a side whose peer answered. Then record it in
GATE-5-MEASUREMENT.md as Attempt 2 and tick the gate.

**Why human:** needs a second physical machine on a different network with a human operator.
Re-confirmed this pass: nothing in `scripts/` or `tests/` simulates a remote machine, by design.
The clean local `dev_launch.py` run above is necessary but **not** sufficient — attempt 1 also
passed locally before it failed remotely.

### Gaps Summary

**No gap remains against this phase's own must_haves.** All five UAT gaps and deferred item #1
were re-verified against source and against live runs, not against SUMMARY prose:

- **G1** — the non-accusatory branch exists *and* `board_outcome=outcome` is present at the
  production call site (`agent_entrypoint.py:110`), which was the specific thing to confirm; the
  audit falls through instead of bailing; `record_technical_loss` appends a corrected `game_over`;
  the linger reuses two existing Table-19 fields with zero literals and zero config keys, inside a
  `finally`, with the watchdog stopped first.
- **G2** — one negotiated id now governs all four artifact classes on both sides (measured on a
  real loopback game, including every committed `state.game_id`), and the candidate set is built
  seven lines before the rebind, pinned for both roles by two independent tests.
- **G3+G4** — both live logs now carry `message_received`+`hint` records with the correct turn
  split, both sides stamp the turn actually played, the responder decodes for the first time, and
  no hint is composed for a resolved turn.
- **G5** — the startup warning fires on a keyless box with the env var **name** only, the
  declaration honestly says `template-fallback (no LLM calls)` and still carries exactly its ten
  HMAC'd fields, and the four Phase-4 degradation tests pass unedited.
- **Deferred #1** — both httpx shapes (raw and the `RuntimeError from httpx.ConnectError` connect
  wrapper) are contained, the two local-fault classes still raise, and neither `deadline.py` nor
  `deadline_errors.py` contains a catch-all.

**What is still open is the phase's own §10.4 criterion 2**, which cannot be produced by any
script here. Plus one new finding worth a follow-up plan before league day (deferred item **7**:
a malformed peer FINAL_REVEAL still kills us at the audit boundary — the last uncontained door in
the same corridor 05-04 and 05-09 closed), and the amendment it forces on deferred item 3's
"nothing is exposed today".

**GATE-5 is NOT ticked. `docs/phases/phase-5/TODO.md` and `.planning/ROADMAP.md` are correctly
left unticked for 05-08 and for the criterion-2 gate row.**

---

*Verified: 2026-08-14 — replaces the 2026-08-09T05:58:21Z report*
*Verifier: Claude (gsd-verifier)*
