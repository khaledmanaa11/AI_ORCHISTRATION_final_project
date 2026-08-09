---
phase: 06-security-and-cryptography
plan: "03"
subsystem: security
tags: [step0, hmac, sha256, handshake, final-reveal, mutual-audit, psutil, hardware-declaration]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography plan 01
    provides: "src/pursuit/security/commit_pack.py (verify_reveal), canonical_json exception precedent"
  - phase: 06-security-and-cryptography plan 02
    provides: "MessageType.FINAL_REVEAL wire type + stub tool handler, CommitLedger filename convention (<log-stem>.ledger.jsonl), AgentContext.security"
provides:
  - "src/pursuit/security/step0_collect.py + step0_sign.py: full Sec5.5 declaration auto-collect (D-63), digest-always/HMAC-when-secret signing (D-62)"
  - "src/pursuit/security/audit.py: audit_peer_records/AuditRecord/all_matched -- the D-67 three-check re-hash + revealed-action cross-check"
  - "Handshake's third digest slot (STEP0_DIGEST, presence-required) PLUS a fifth key (STEP0_DECLARATION) carrying the full published content, content-verified against its own claimed digest via step0_sign.verify_declaration when sent -- + D-61 game_id negotiation (HandshakeResult.peer_game_id/peer_step0_declaration)"
  - "src/pursuit/network/agent_audit_wiring.py + agent_audit_exchange.py: declare_step0/write_declaration/run_final_audit wired live into run_agent"
affects: [06-04-gate-and-docs]

# Tech tracking
tech-stack:
  added: [psutil>=7.2.2]
  patterns:
    - "D-62, two-layer verification: the DIGEST is checked for PRESENCE, not equality (unlike CONFIG/SCENT, a Step-0 declaration is inherently per-agent; a literal compare_named_digest equality check would abort every real two-role game). The CONTENT (STEP0_DECLARATION, book Sec5.5's own 'published' declaration) is, when the peer opts in and sends it, verified via step0_sign.verify_declaration against that same claimed digest -- closing the gap where a peer sending a random 64-char string would otherwise pass. A digest-only peer (an opponent team's own implementation we cannot force to publish content) still agrees, logged as digest-only, never a hard failure."
    - "4-way sibling split for the handshake, one beyond the original 3 (handshake.py/handshake_wire.py/handshake_evaluate.py): handshake_step0.py holds Step-0 content verification alone, split out because handshake_evaluate.py was already AT its 150-line ceiling before this follow-up -- mirrors the turn_commit.py 3-to-more-siblings precedent"
    - "3-way sibling split for the D-67 audit wiring, mirroring handshake.py/handshake_wire.py/handshake_evaluate.py and turn_commit.py/turn_commit_wait.py/turn_commit_send.py: agent_audit_wiring.py (2 public entry points + policy) / agent_audit_exchange.py (wire mechanics: push/receive FINAL_REVEAL, observed-history extraction, verdict recording)"
    - "AUDIT_HASH_MISMATCH reuses the EXISTING TechnicalWin dataclass/technical_win event shape -- never a second, parallel verdict type; attempts=1/timeout=0.0/backoff=0.0 are structural (no retry ladder governs an audit mismatch), elapsed_seconds is genuinely measured"
    - "games_played.json: mutable per-role runtime counter persisted BESIDE config/{police,thief}/ by design (rule 37), gitignored like *.qtable/nonces/ -- not version-controlled config"
    - "The shared secret used to verify a PEER's HMAC is OUR OWN resolved value (resolve_shared_secret), never a second peer-specific secret -- correct because D-62's 'pre-supplied key' is ONE value both match participants configure identically (config/police/tunnel.json and config/thief/tunnel.json share the same secret_env name by design); agent_lifecycle.py resolves it once and reuses the SAME tuple for both PeerRuntime's middleware and the responder's Step-0 verification"

key-files:
  created:
    - src/pursuit/security/step0_collect.py
    - src/pursuit/security/step0_sign.py
    - src/pursuit/security/audit.py
    - src/pursuit/network/agent_audit_wiring.py
    - src/pursuit/network/agent_audit_exchange.py
    - src/pursuit/network/handshake_step0.py
    - tests/unit/test_step0_collect.py
    - tests/unit/test_step0_sign.py
    - tests/unit/test_audit.py
    - tests/unit/test_handshake_step0.py
    - tests/unit/test_handshake_step0_declaration.py
    - tests/unit/test_agent_audit_exchange.py
    - tests/unit/test_agent_audit_wiring.py
    - tests/integration/test_step0_and_audit.py
    - tests/integration/test_step0_and_audit_tamper.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/pursuit/network/handshake_wire.py
    - src/pursuit/network/handshake_evaluate.py
    - src/pursuit/network/handshake.py
    - src/pursuit/network/agent_wiring.py
    - src/pursuit/network/agent_lifecycle.py
    - src/pursuit/network/agent_entrypoint.py
    - src/pursuit/network/verdict.py
    - src/pursuit/network/event_log.py
    - tests/unit/test_agent_entrypoint.py
    - .gitignore

key-decisions:
  - "D-62 REVISED (Rule 1 - bug prevention, not a re-derivation of the book): Step-0's handshake DIGEST is a PRESENCE check, never an equality check. See tech-stack pattern above for the full reasoning; documented in handshake_evaluate.py's own module docstring."
  - "D-62 FOLLOW-UP (coordinator-directed, post-review): digest-presence alone left step0_sign.verify_declaration with ZERO production callers and let a peer pass Step-0 by sending any 64-char string -- gate criterion 3 ('verified before move 1') was only true of OUR OWN declaration. Fixed by ALSO sending the full declaration CONTENT (book Sec5.5: the declaration is meant to be PUBLISHED, no secrecy reason to withhold it) and verifying it against its own claimed digest when the peer opts in to send it. A content-tampered declaration (digest computed, THEN content mutated) now aborts before move 1; a digest-only peer still agrees. handshake_step0.py (new sibling) holds this logic since handshake_evaluate.py had zero line-count room left."
  - "declare_step0(cfg) simplified to a single-arg signature (the plan's own draft sketch carried a local_game_id parameter never actually consumed by the function body -- Step-0's own field set has no game_id field); game_id resolution stays entirely inside write_declaration/_declared_game_id, exactly as D-61 specifies"
  - "agent_lifecycle.py touched (Rule 3 - blocking, NOT pre-authorized in this plan's files_modified): default_context needed to thread local_step0_digest/local_game_id/local_step0_declaration into make_handshake_responder for Step-0 to reach the REAL responder path at all -- the exact same seam local_scent_digest already uses in that same function. All default None; every pre-existing call site is byte-unmodified."
  - "Both directions of perform_handshake are exercised in the integration harness (each side calls it as ITS OWN outbound client, matching real production symmetry) -- this causes one harmless RECOVERABLE (HANDSHAKE, HANDSHAKE) self-transition log line per side (the other side's own responder also attempts HANDSHAKE on an already-HANDSHAKE machine), asserted around via a content-aware check (no message_sent/message_received event yet) rather than a byte-empty-file assertion"
  - "games_played.json's counter path is derived from cfg.config_dir directly (the REAL config/{police,thief}/ dirs) -- not redirected to a test tmp_path -- because config_dir also resolves game_params.json/tunnel.json and cannot be swapped wholesale without breaking config_digest/resolve_shared_secret. Gitignored so this never pollutes git status; functionally correct since rule 37 requires exactly this persisted-in-place behavior."

patterns-established:
  - "The full Step-0 declaration now crosses the wire (STEP0_DECLARATION, opt-in) alongside its digest (STEP0_DIGEST, presence-required) -- book Sec5.5's declaration IS meant to be published, so sending content is strictly more faithful than a bare digest. Each side ALSO writes its own to disk (declaration_<game_id>.json) plus the PEER's own (declaration_<game_id>_peer.json) for Phase-7 auditability. verify_declaration (step0_sign.py) has a real production caller (handshake_step0._step0_verified) -- confirmed via grep and via tests that exercise perform_handshake directly, not just the unit-level API."

# Metrics
duration: ~65min
completed: 2026-08-09
---

# Phase 6 Plan 3: Step-0 Declaration + D-67 Final-Reveal Mutual Audit Summary

**Auto-collected, HMAC-signable Step-0 declarations whose full content (book Sec5.5's own "published" fields) is exchanged and verified against its own claimed digest at handshake before move 1 -- digest presence alone is required, content verification runs whenever the peer opts in to send it -- plus a game-end mutual audit that closes the hash-only bypass by cross-checking the revealed action against what was actually observed played in-game.**

## Performance

- **Duration:** ~65 min (includes a coordinator-directed follow-up closing a content-verification gap)
- **Tasks:** 4 + 1 follow-up
- **Files created:** 15 (6 source, 9 test)
- **Files modified:** 12

## Accomplishments

- **Step-0 (D-63) is fully auto-collected, never hand-typed.** `collect_declaration()` gathers the complete book §5.5 field set (role, team_code, OS via `platform`, CPU cores+frequency and RAM via `psutil`, GPU best-effort via `nvidia-smi` subprocess with an honest `{"present": False, "detail": "not detected"}` on ANY failure -- never a fabricated GPU/VRAM figure, LLM name from the agent's own `language.json`, code version, games-played-so-far, and the exact git commit hash via `git rev-parse HEAD`, raising loudly if that fails). The sanity display is one non-blocking `print` line -- never `input()`.
- **D-62 signing: digest always, HMAC when a shared secret exists.** `step0_sign.sign_declaration()` returns an explicit `signed: False`/`hmac: None` when `resolve_shared_secret` finds nothing -- never silently treated as verified. `verify_declaration()` checks the digest and (when present) the HMAC independently; a complete, 100%-tested API ready for a future consumer (see key-decisions).
- **D-62 CORRECTED, not literally implemented: Step-0's handshake digest is a presence check, never equality.** The plan's own literal text ("the same opt-in step0 comparison SCENT_DIGEST already has... via compare_named_digest") would have made `_compare_offer` reject EVERY real two-role game the instant both sides opted in, because a Step-0 declaration is inherently per-agent (role/hardware/identity) -- two roles' digests are never expected to match, unlike CONFIG_DIGEST/SCENT_DIGEST (digests of files deliberately kept byte-identical across both config dirs). `HandshakeOutcome.STEP0_MISMATCH` fires exactly when the digest is absent (rule 24's actual failure mode -- Step-0 never ran on the peer's side), never when it merely differs from ours. Documented prominently in both `handshake_evaluate.py`'s module docstring and this SUMMARY, per the critical-honesty requirement that this interpretation choice never be silently reinterpreted.
- **D-62 FOLLOW-UP, coordinator-directed: the digest-only design left `verify_declaration` with zero production callers and no real verification.** Digest-presence alone means a peer sending ANY 64-char string passes -- the content was never checked against anything. Fixed: `HandshakeKey.STEP0_DECLARATION` carries the FULL declaration content (book §5.5: the declaration is meant to be **published** -- OS/CPU/RAM/GPU/model/code-version/commit-hash carry no secrecy reason to be withheld, so sending it is strictly more faithful to the book than a bare digest). `handshake_step0.py` (new sibling -- `handshake_evaluate.py` was already AT its 150-line ceiling) verifies, when the peer sends one, that the declaration's content hashes to its own claimed `STEP0_DIGEST` (plus the HMAC, when both sides hold the shared secret) via `step0_sign.verify_declaration` -- now genuinely wired into production, not a dead API. A digest-only peer (an opponent team we cannot force to publish content) still agrees, logged as digest-only. A declaration mutated AFTER its digest was computed fails before move 1, with a report that names the fact ("does not hash to its own claimed digest") without accusing language, mirroring `test_handshake_abort.py`'s own house style.
- **D-61 game_id negotiation.** `HandshakeResult.peer_game_id` is read UNCONDITIONALLY from the peer's envelope (present even on a mismatch -- evidence, not just success). The LOAD-BEARING proof is `test_handshake_step0.py::test_game_id_negotiation_resolves_to_the_initiators_value`, which constructs the two sides with DELIBERATELY DIFFERENT `local_game_id` values ("police-uid-aaa" vs "thief-uid-bbb") and confirms the responder's own `peer_game_id` resolves to the INITIATOR's value, not its own -- a harness sharing one `game_uid` by construction (as the integration test does) could pass even with negotiation entirely broken, so that assertion is corroboration only.
- **D-67's hash-only bypass is genuinely closed, proven with both tamper classes distinctly.** `audit_peer_records()` runs three checks in order per turn: (1) an observed commit exists for that turn, (2) the re-hash matches the `H_commit` observed at Commit time, (3) the revealed composite action dict equals what THIS side actually saw played in that turn's in-game REVEAL. `tests/unit/test_audit.py` proves case (a) -- a flipped payload field fails check 2 -- and separately proves case (b) -- the D-67 case itself: hash and payload left completely untouched (still verifies against `verify_reveal` directly, asserted explicitly), but the claimed action differs from what was actually played, failing check 3 alone. The SAME function also runs as a symmetric self-check (this side's own ledger against what it actually sent) -- a self-mismatch is reported with the identical `AUDIT_HASH_MISMATCH` label, never suppressed.
- **The whole flow proven live, at the real two-peer integration level.** `tests/integration/test_step0_and_audit.py` plays a full real game (both sides' own outbound `perform_handshake` calls, matching true production symmetry) and shows `declaration_<game_id>.json` written on BOTH sides before any move/commit/hint content is logged, and a clean game's `audit_verdict` record showing `matched: true` on both sides. `test_step0_and_audit_tamper.py` proves both D-67 tamper classes end-to-end: (a) corrupting one entry's payload in police's own ledger makes THIEF's audit of police's claims report `AUDIT_HASH_MISMATCH` and return `Outcome.TECHNICAL_LOSS` (and, as a genuine consequence of the same symmetric-honesty design, police's OWN self-audit also catches its now-corrupted ledger); (b) leaving the ledger entirely untouched (independently confirmed still hash-verifies) but corrupting only what thief actually observed played in-game for that turn makes thief's audit fail via check 3 specifically -- the exact bypass D-67 exists to close.
- **`agent_entrypoint.run_agent` stays a thin caller.** Three new call sites (`declare_step0` before the handshake, `write_declaration` after agreement, `run_final_audit` after `run_turn_loop`, gated on `security.commit_reveal`) -- all logic lives behind `agent_audit_wiring.py`/`agent_audit_exchange.py`. `git diff -- src/pursuit/network/state_machine.py` is empty: the Step-0 abort reuses the existing `HandshakeOutcome`/`State.ERROR` seam, no new State member, no new transition row (D-58 still holds).
- **`step0_sign.verify_declaration` now has a real, confirmed production caller.** `grep -rn "verify_declaration(" src/` returns exactly one non-definition call site: `handshake_step0.py`, reached from real `perform_handshake`/`respond_to_handshake` calls (proven by tests that call those functions directly, not mocks). The peer's own full declaration is ALSO persisted (`declaration_<game_id>_peer.json`), when sent, for Phase-7 auditability.

## Task Commits

Each task was committed atomically:

1. **Task 1: Step-0 collection, signing, and the games-played counter** - `54048e3` (feat)
2. **Task 2: the handshake's third digest and game_id** - `7bb130b` (feat)
3. **Task 3: the Final-Reveal audit function** - `ed48ee4` (feat)
4. **Task 4: agent_audit_wiring.py + agent_audit_exchange.py, run_agent as thin caller** - `be75519` (feat)
5. **Follow-up: exchange and verify Step-0 declaration CONTENT, not just its digest** - `10f3a26` (feat, coordinator-directed)

**Plan metadata:** (this commit, appended after STATE.md/graph update)

## Files Created/Modified

- `src/pursuit/security/step0_collect.py` - `collect_declaration`/`read_games_played`/`record_game_played`, the full §5.5 field set + rule 37/38 counter
- `src/pursuit/security/step0_sign.py` - `digest_declaration`/`sign_declaration`/`verify_declaration` (D-62)
- `src/pursuit/security/audit.py` - `AuditRecord`/`audit_peer_records`/`all_matched` (D-67)
- `src/pursuit/network/handshake_wire.py` - `HandshakeKey.STEP0_DIGEST`/`GAME_ID`/`STEP0_DECLARATION`, `build_offer`'s three new optional params
- `src/pursuit/network/handshake_evaluate.py` - `HandshakeOutcome.STEP0_MISMATCH`, `HandshakeResult.peer_game_id`/`peer_step0_declaration`, `evaluate()`/`_compare_offer` thread `shared_secret`, both read unconditionally
- `src/pursuit/network/handshake_step0.py` (new) - `_step0_verified` (digest presence + opt-in content verification via `step0_sign.verify_declaration`)
- `src/pursuit/network/handshake.py` - both public entry points thread `local_step0_declaration`/`shared_secret` through
- `src/pursuit/network/agent_wiring.py` - `make_handshake_responder` gains the same two params
- `src/pursuit/network/agent_lifecycle.py` - `default_context` threads them into the responder, reusing the SAME resolved shared-secret tuple already built for `PeerRuntime` (Rule 3 deviation)
- `src/pursuit/network/agent_entrypoint.py` - `run_agent`'s three new call sites plus the declaration/secret threading, stays a thin caller
- `src/pursuit/network/agent_audit_wiring.py` (new) - `declare_step0`/`write_declaration` (now also persists the peer's own declaration)/`run_final_audit`
- `src/pursuit/network/agent_audit_exchange.py` (new) - FINAL_REVEAL push/receive, `observed()`, verdict recording
- `src/pursuit/network/verdict.py` - `TechnicalWinReason.AUDIT_HASH_MISMATCH` (additive)
- `src/pursuit/network/event_log.py` - `EventType.AUDIT_VERDICT` (additive)
- `.gitignore` - `config/*/games_played*.json` (mutable runtime state, not config)
- 15 test files (see frontmatter `key-files`) - 59 new tests total across unit + integration (55 from Tasks 1-4, +4 from the follow-up's `test_handshake_step0_declaration.py`)

## Exact Contracts for 06-04 (verbatim, do not re-derive)

```python
# src/pursuit/security/step0_sign.py
def digest_declaration(declaration: dict) -> str: ...
def sign_declaration(declaration: dict, *, secret: str | None) -> dict:
    ...  # {"digest": ..., "signed": bool, "hmac": str | None}
def verify_declaration(
    declaration: dict, *, digest: str, hmac_value: str | None, secret: str | None,
) -> bool: ...

# src/pursuit/security/audit.py
@dataclass(frozen=True)
class AuditRecord:
    turn: int; matched: bool; detail: str

def audit_peer_records(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
) -> list[AuditRecord]: ...
def all_matched(records: list[AuditRecord]) -> bool: ...

# src/pursuit/network/handshake_evaluate.py
class HandshakeOutcome(Enum):
    AGREED = "agreed"; CONFIG_MISMATCH = "config_mismatch"; SCENT_MISMATCH = "scent_mismatch"
    STEP0_MISMATCH = "step0_mismatch"; UNREACHABLE = "unreachable"; MALFORMED_REPLY = "malformed_reply"

@dataclass(frozen=True)
class HandshakeResult:
    outcome: HandshakeOutcome; state: State; local_digest: str; remote_digest: str | None
    peer_role: str | None; detail: str
    peer_game_id: str | None = None
    peer_step0_declaration: dict | None = None  # None = peer sent digest-only, or none at all

# src/pursuit/network/handshake_step0.py
def _step0_verified(shared_secret: str | None, envelope: Envelope) -> tuple[bool, str]: ...
    # digest absent -> (False, "...absent..."); declaration absent -> (True, "...digest-only");
    # declaration present -> verify_declaration(...) result, detail names which happened

# src/pursuit/network/agent_audit_wiring.py
async def declare_step0(cfg: AgentConfig) -> tuple[str, dict]: ...  # (step0_digest, declaration_envelope)
def write_declaration(ctx, cfg, result: HandshakeResult, declaration_envelope: dict) -> None: ...
    # ALSO writes declaration_<game_id>_peer.json when result.peer_step0_declaration is not None
async def run_final_audit(ctx: AgentContext) -> Outcome | None: ...  # None = clean, else TECHNICAL_LOSS

# Declaration filename convention (D-61):
# <ctx.log_path.parent>/declaration_<declared_game_id>.json            (ours)
# <ctx.log_path.parent>/declaration_<declared_game_id>_peer.json       (theirs, when sent)
# declared_game_id = ctx.game_uid if role == "police" else (result.peer_game_id or ctx.game_uid)
```

**What 06-04 needs to know:**

- **`measure_gate6.py` should drive `run_agent` end to end (not hand-roll a second harness)** -- `declare_step0`/`write_declaration`/`run_final_audit` are ALREADY wired live into `agent_entrypoint.run_agent`, and it now sends+verifies the FULL declaration content (not just a digest); a real two-peer localhost game via `config/police`/`config/thief` exercises the WHOLE Phase-6 flow (commit-reveal + Step-0 exchange-and-verify + audit) with zero extra wiring.
- **GATE-6 criterion 3 ("Step-0 verified before move 1")** is now genuinely satisfied both ways: digest PRESENCE is required (never equality -- see the D-62 correction), and declaration CONTENT is verified against its own claimed digest whenever the peer opts in to send it (the real production path both `config/police`/`config/thief` exercise against each other). `measure_gate6.py`'s own report should state both halves explicitly, and can quote `handshake_step0._step0_verified`'s docstring for why digest equality was never the right check.
- **The tamper-harness proof 06-04's own plan calls for** (`06-PLAN-OUTLINE.md` §4: "a forged reveal ⇒ `AUDIT_HASH_MISMATCH` technical loss") is ALREADY fully proven by `tests/integration/test_step0_and_audit_tamper.py` for the D-67 commit-reveal case, and by `tests/unit/test_handshake_step0_declaration.py::test_declaration_tampered_after_its_digest_was_computed_fails_before_move_1` for the Step-0 declaration case -- 06-04 can point `GATE-6-MEASUREMENT.md` at these directly rather than re-deriving a third tamper harness.
- **`handshake_evaluate.py` is now EXACTLY at 150/150 lines, zero margin** -- any further handshake-payload extension in 06-04 (there should be none planned) needs a fresh split before it can land, not an inline addition. `agent_wiring.py` (148/150) is similarly tight.
- **`declaration_<game_id>.json` lands under `ctx.log_path.parent`** (i.e., `logs/{role}/` in real deployment) -- `.gitignore`'s existing note ("the four required JSON artifacts... MUST be committed per rule 50... keep them out of this ignore list") is currently in tension with the blanket `logs/` ignore rule already in place BEFORE this plan; flagged for 06-04/Phase 7/8, not resolved here (out of this plan's scope). The new `_peer.json` sibling file inherits the same tension.
- **The shared secret used for Step-0 HMAC verification is always OUR OWN `resolve_shared_secret(cfg.config_dir)` value** -- correct for this project's setup (both `config/police/tunnel.json` and `config/thief/tunnel.json` name the SAME `secret_env`, i.e. it is one match-negotiated value both sides configure identically), not a peer-specific secret we have no way to obtain.

## Decisions Made

See frontmatter `key-decisions` for the full list with rationale. The single most consequential one: **D-62's presence-only Step-0 comparison**, a genuine, reasoned correction to what the plan's own literal text specified (a `compare_named_digest` equality check mirroring `SCENT_DIGEST` verbatim). Implementing it literally would have aborted every real two-role game the instant both sides opted in -- verified by direct reasoning about `digest_declaration`'s inputs (the `role` field alone guarantees two different roles' declarations, and therefore their digests, are never equal), not assumed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug prevention] Step-0's handshake digest corrected to presence-only, not equality**
- **Found during:** Task 2, while implementing `_compare_offer`'s step0 branch per the plan's own literal "mirror SCENT_DIGEST via compare_named_digest" instruction
- **Issue:** A Step-0 declaration digests `role` among other per-agent fields (D-63's own field set). Two different roles' declarations can never hash equal, even on identical hardware. A literal equality check would make `HandshakeOutcome.STEP0_MISMATCH` fire on EVERY real two-role game the instant both sides supply `local_step0_digest` -- exactly what Task 4 requires in real play ("Every real caller (Task 4) will always supply both").
- **Fix:** `_step0_present()` checks presence only (a missing remote digest is the actual failure mode, matching rule 24's "Step-0 crypto before game start" framing); a present-but-different digest still agrees.
- **Files modified:** `src/pursuit/network/handshake_evaluate.py` (+ its own module docstring), documented again in `handshake_wire.py`'s docstring
- **Verification:** `tests/unit/test_handshake_step0.py::test_a_present_but_different_step0_digest_still_agrees` (the corrected behavior) + `test_missing_step0_digest_aborts_before_move_1` (the real failure mode); the full two-peer integration suite (`test_step0_and_audit.py`) reaches a completed, audited game with both sides genuinely opted into Step-0.
- **Committed in:** `7bb130b` (Task 2 commit)

**2. [Rule 3 - Blocking] `agent_lifecycle.py` needed editing, though not listed in this plan's `files_modified`**
- **Found during:** Task 4, wiring `declare_step0`'s digest into the REAL inbound responder path
- **Issue:** `make_handshake_responder` (Task 2, `agent_wiring.py`) gained the two new params, but the ONE real call site that constructs it for live play -- `agent_lifecycle.default_context` -- was not in this plan's file list, and without editing it Step-0 would never reach the responder side of a real game (only the outbound `perform_handshake` call would carry it, an asymmetric and incomplete wiring).
- **Fix:** `default_context` gained the same two optional params (default `None`), threaded straight into `make_handshake_responder`, exactly mirroring how `local_scent_digest` already flows through that same function.
- **Files modified:** `src/pursuit/network/agent_lifecycle.py`
- **Verification:** Full suite re-run green; `tests/integration/test_step0_and_audit.py` exercises the REAL `default_context` (not a fake) end to end with both sides opted into Step-0.
- **Committed in:** `be75519` (Task 4 commit)

**3. [Rule 3 - Blocking] `tests/unit/test_agent_entrypoint.py` fallout from `run_agent`'s new call sites**
- **Found during:** Task 4's full-suite verification run (not caused by Task 4's own scope directly -- caused by `run_agent`'s new imports/calls, only surfaced once the full suite ran)
- **Issue:** The existing fake-driven `_patch_common` helper monkeypatches `agent_entrypoint`'s bound names; it had no fakes for the three newly-imported `declare_step0`/`write_declaration`/`run_final_audit`, and `_FakeCtx` had no `.security` attribute for the new `if ctx.security.commit_reveal:` branch.
- **Fix:** Added `_FakeSecurity`/`_FakeCtx.security` (`commit_reveal=False` by default, so `run_final_audit` never fires in these three pre-existing tests) and fakes for the three new functions; updated the three order-list assertions to include `declare_step0`/`write_declaration` in the expected sequence.
- **Files modified:** `tests/unit/test_agent_entrypoint.py`
- **Verification:** All 3 tests pass; full suite re-run green.
- **Committed in:** `be75519` (Task 4 commit)

**4. [Rule 3 - Blocking] `.gitignore` needed `config/*/games_played*.json`**
- **Found during:** Task 4, while writing the integration test harness
- **Issue:** `declare_step0`/`write_declaration` read/write the games-played counter at `cfg.config_dir / "games_played.json"` -- necessarily the REAL `config/police/`/`config/thief/` directories (that path also resolves `game_params.json`/`tunnel.json`, so it cannot be redirected to a test `tmp_path` without breaking `config_digest`/`resolve_shared_secret`). Running the integration tests would otherwise leave untracked files in `git status`.
- **Fix:** Added a targeted `.gitignore` entry, matching the existing `*.qtable`/`nonces/` precedent for mutable runtime state that is NOT version-controlled config.
- **Files modified:** `.gitignore`
- **Verification:** `git status --short` clean after a full test run that exercises the real counter path.
- **Committed in:** `be75519` (Task 4 commit)

**5. [Rule 2 - Missing coverage] Coverage-closing tests for every new module's untested branch**
- **Found during:** Task 4's own coverage measurement pass
- **Issue:** `agent_audit_exchange.py`/`agent_audit_wiring.py`/`step0_collect.py` each had 2-5 uncovered lines (FINAL_REVEAL push/receive failure paths, `observed()`'s no-envelope skip, `_collect_cpu`'s exception path, `_collect_gpu`'s success path -- none exercised by the earlier task's own happy-path tests).
- **Fix:** Added `tests/unit/test_agent_audit_exchange.py`, `tests/unit/test_agent_audit_wiring.py`, and two more cases in `tests/unit/test_step0_collect.py`.
- **Files modified:** see above
- **Verification:** All three modules independently confirmed at 100% coverage in isolation; full suite coverage 96.24% (well above the 85% floor).
- **Committed in:** `be75519` (Task 4 commit)

**6. [Coordinator-directed follow-up, not a Rule 1-4 auto-fix -- an explicit external review finding] Step-0 declaration content is now exchanged and verified, not just its digest**
- **Found during:** post-Task-4 review (coordinator inspected the shipped code directly and confirmed `step0_sign.verify_declaration` had zero production callers)
- **Issue:** The presence-only correction (deviation #1) was necessary and remains correct for the DIGEST, but it left the CONTENT unverifiable: only `STEP0_DIGEST` crossed the wire, never the declaration itself, so a peer sending a random 64-char string satisfied `_step0_present`. Gate criterion 3 ("verified before move 1") was only genuinely true of our OWN declaration.
- **Fix:** `HandshakeKey.STEP0_DECLARATION` (a fifth, opt-in payload key) carries the FULL declaration+signature envelope. `handshake_step0.py` (new sibling, `handshake_evaluate.py` had zero line-count room left) verifies the peer's content against its own claimed digest -- and HMAC, when both sides hold the shared secret -- via `step0_sign.verify_declaration`, whenever the peer sends one. A digest-only peer still agrees (we cannot force an opponent's implementation to publish content); a content-tampered declaration aborts before move 1. `write_declaration` also persists the peer's own declaration for audit.
- **Files modified:** `handshake_wire.py`, `handshake_evaluate.py`, `handshake_step0.py` (new), `handshake.py`, `agent_wiring.py`, `agent_lifecycle.py`, `agent_entrypoint.py`, `agent_audit_wiring.py`, plus `test_handshake_step0_declaration.py` (new, 4 tests), `test_handshake_step0.py` (docstring), `test_step0_and_audit.py` (harness now threads real content), `test_agent_entrypoint.py` (fake fallout)
- **Verification:** 4 new unit tests (content-matches-digest agrees; content-tampered-after-digest aborts before move 1 with a non-accusing report, mirroring `test_handshake_abort.py`'s house style; digest-only peer still agrees; HMAC mismatch on a wrong local secret also aborts) + the full integration suite now asserts `result.peer_step0_declaration` is the genuine peer envelope and that `declaration_<id>_peer.json` is persisted. `grep -rn "verify_declaration(" src/` confirms exactly one non-definition call site. Full suite re-run: 1222 passed, 96.26% coverage.
- **Committed in:** `10f3a26`

---

**Total deviations:** 6 (5 auto-fixed under Rules 1-3 during the plan's own 4 tasks, plus 1 coordinator-directed follow-up closing a genuine design gap the presence-only fix left open)
**Impact on plan:** All six were necessary for correctness or the standing gates. The two Step-0 comparison decisions (deviations #1 and #6) together are the substantive design story: #1 established that digest EQUALITY is wrong for a per-agent value; #6 closed the resulting gap by verifying CONTENT instead, restoring genuine verification without reintroducing the equality bug. Neither was assumed -- both reasoned from the actual data (declarations digest `role`, so equality can never hold; content-hashing is possible and was simply never wired) and reversed only what needed reversing.

## Issues Encountered

None beyond the deviations above -- no blockers, no external service configuration needed.

## User Setup Required

None. Every primitive is stdlib (`hashlib`/`hmac`/`secrets`/`subprocess`) plus `psutil` (added via `uv add`, no config). `resolve_shared_secret` degrades to `signed: False` gracefully when no secret is configured, exactly as every existing local/CI run already exercises.

## Next Phase Readiness

- `run_agent` (agent_entrypoint.py) now drives the COMPLETE Phase-6 flow end to end: Step-0 declare -> sign -> handshake (digest presence required, content verified against its own digest when sent) -> declare ours + the peer's to disk -> commit-reveal turn loop -> Final-Reveal mutual audit -> outcome (possibly overridden to `TECHNICAL_LOSS`). 06-04's `measure_gate6.py` needs no new wiring, only to call `run_agent` (or mirror `test_step0_and_audit.py`'s harness) and report the real numbers.
- Both required tamper-harness proofs for GATE-6's own milestone text are ALREADY committed and passing: `test_step0_and_audit_tamper.py` (D-67, commit-reveal) and `test_handshake_step0_declaration.py` (Step-0 declaration content), ready for 06-04 to cite directly.
- `handshake_evaluate.py` is now EXACTLY at 150/150 lines -- zero margin, flagged explicitly for 06-04. `agent_wiring.py` (148/150) is similarly tight.
- `verify_declaration` (step0_sign.py) is confirmed wired to production (one real call site, `handshake_step0.py`) -- no longer a dead, unit-tested-only API.
- Full repo gates green: 1222 passed (+38 net new vs the 1184 baseline; pre-existing timing flake independently re-confirmed passing in isolation, unrelated to this plan), 96.26% coverage, `ruff check .` 0 violations, `scripts/check_line_limit.sh` clean, `scripts/check_no_llm_in_strategy.py` OK, `git diff -- src/pursuit/network/state_machine.py` empty.
- Knowledge graph NOT refreshed this plan (06-96 still pending, same as 06-02 left it) -- flagged for 06-04 or a dedicated pass before `/gsd:verify-work 6`.
- No blockers for 06-04.

---
*Phase: 06-security-and-cryptography*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 15 created files verified present on disk; all 5 commits
(`54048e3`, `7bb130b`, `ed48ee4`, `be75519`, `10f3a26`) verified present in
`git log --oneline --all`. Full gate suite independently re-confirmed:
1222 passed, 96.26% coverage, `ruff check .` 0 violations,
`scripts/check_line_limit.sh` clean, `scripts/check_no_llm_in_strategy.py`
OK, `git diff -- src/pursuit/network/state_machine.py` empty. Pre-existing
timing flake (`test_belief_enabled_completes_within_the_per_turn_time_budget`)
re-confirmed passing in isolation, unrelated to this plan.
`grep -rn "verify_declaration(" src/` confirms exactly one non-definition
production call site (`handshake_step0.py`), closing the coordinator's own
stated gap.
