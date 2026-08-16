---
phase: 05-cloud-exposure-and-tunneling
plan: "12"
subsystem: security
tags: [handshake, peer-input-boundary, path-traversal, digest, game-id, rule-36, false-accusation]

# Dependency graph
requires:
  - phase: 05-cloud-exposure-and-tunneling
    provides: "05-05's D-61 game identity (the code G7 is a defect IN) and 05-10's boundary rule at security/audit.py:56-90 (the rule G9 is instance 7 of)"
provides:
  - "config_hash.unusable_peer_digest -- the ONE gate every peer-supplied digest slot passes through; a non-str remote digest is a named non-agreement, not a TypeError"
  - "game_identity_validate.usable_peer_game_id -- the ONE absence rule shared by the thief's fallback, the candidate set and the declaration filename"
  - "game_identity_validate.relocate_log -- the only place a game id becomes a Path, total over (OSError, ValueError)"
  - "handshake_step0 containment for a non-str step0_digest and a non-str declaration hmac (instance 9, found by probe, not by the plan)"
  - "security/audit.py's boundary rule extended with instances 7, 8, 9 and the handshake-corridor note"
affects: [05-13, 05-14, 05-15, 07-reporting-and-visualization-shell, league-day]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SAFETY-only validation of peer input, never convention-conformance -- any str reaches the real comparison as evidence"
    - "Rejection is not accusation: an unusable peer id yields candidate_game_ids=None, which audit_state SKIPS rather than rejects"
    - "Downgrade over abort on an OPTIONAL peer field whose absence already agrees"
    - "Structural source constants with their derivation written beside them (the _DECLARE_RETRIES precedent), never a new config leaf"

key-files:
  created:
    - src/pursuit/network/game_identity_validate.py
    - tests/unit/test_config_hash_peer.py
    - tests/unit/test_handshake_peer_digest.py
    - tests/unit/test_game_identity_validate.py
    - tests/unit/test_game_identity_adopt.py
  modified:
    - src/pursuit/network/config_hash.py
    - src/pursuit/network/handshake_step0.py
    - src/pursuit/network/game_identity.py
    - src/pursuit/security/audit.py
    - tests/unit/test_config_hash.py
    - tests/unit/test_game_identity.py
    - docs/phases/phase-5/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "A non-str step0_digest and a non-str declaration hmac are DOWNGRADED, not aborted -- a first draft that aborted was reversed by its own no-new-accusation control"
  - "An unusable peer game_id sets candidate_game_ids to None (check skipped) rather than to a set excluding the peer -- rejection must never become accusation"
  - "digests_match keeps its strict raising contract; containment lives one level up at the peer boundary"
  - "_MAX_PEER_GAME_ID = 128 is a source constant derived from the 255-byte path-component limit minus the longest affix, never a config field"
  - "relocate_log is total over (OSError, ValueError) as belt-and-braces; on failure we keep our own uid but the peer's id STAYS on the table"

patterns-established:
  - "Corridor sweep, not door-by-door: enumerate EVERY peer-controlled value a boundary reads, rather than closing the one that was reported"
  - "Every hardening gate ships a paired fairness control that FAILS against the tempting stricter rule"
  - "Anti-vacuity guard on parametrised evidence sets -- pytest treats an empty parametrize as a skip, not an error"

# Metrics
duration: 95min
completed: 2026-08-16
---

# Phase 5 Plan 12: A Malformed Peer Cannot Kill Us At The Handshake Summary

**Nine peer-controlled values that each killed this process before move 1 -- four digest slots and five game_id sinks -- now every one resolves to a named outcome, while eight honest foreign id conventions still MATCH along the whole chain to the audit's membership check.**

## Performance

- **Duration:** ~95 min
- **Tasks:** 3 (plus 2 follow-on test commits from the self-audit)
- **Commits:** 5
- **Files created:** 5 · **Files modified:** 8
- **Suite:** 1478 passed / 0 failed / **96.57%** (baseline 1374 / 96.54%) -- +104 tests, +0.03pp

## Accomplishments

- **G9 closed, and it was BIGGER than reported.** The plan named two digest slots (config, scent). A sweep of the whole corridor found **four**: `step0_digest` and the declaration `hmac` reach `digests_match` inside `verify_declaration` and raised identically. All four contained.
- **G7 closed.** `peer_game_id` now passes one safety gate before it reaches a set constructor, a `Path`, or the audit's membership key -- and the `''` split, where `:71` said "absent" while `:157-158` said "present", is closed by making both consume one answer.
- **The fairness half, which is the half that could have gone wrong.** Eight honest foreign conventions are still adopted verbatim and still audit clean end to end. Revert probe P3 -- our own 16-lower-hex convention used as the rule -- fails 18 of them.
- **The boundary rule now names instances 7, 8 and 9** and raises its own bar: a TENTH is a review failure, with the reason stated (instance 7 had a *green test certifying the crash as intended*).

## Task Commits

1. **Task 1: contain a non-str peer digest** — `52a6b47` (fix)
2. **Task 2: one safety gate for `peer_game_id`** — `11e9978` (fix)
3. **Task 3: adversarial suite + fairness control + the rule comment** — `2826d3a` (test)
4. *Self-audit follow-on:* coverage-close the belt-and-braces branch — `5c92ec7` (test)
5. *Self-audit follow-on:* anti-vacuity guard on the evidence sets — `765d8a6` (test)

## The before/after probes, verbatim

### G9 — a non-str peer digest through `handshake_evaluate.evaluate()`

**BEFORE** (live source at `0437559`):

```
  digest=int   -> RAISED TypeError: digests_match requires two str arguments
  digest=list  -> RAISED TypeError: digests_match requires two str arguments
  digest=dict  -> RAISED TypeError: digests_match requires two str arguments
  digest=bool  -> RAISED TypeError: digests_match requires two str arguments

  CONTROLS (must stay contained after the fix):
  wrong-but-str  -> outcome=config_mismatch detail='config digest mismatch: local=aaaa... remote=bbbb...'
  absent         -> outcome=malformed_reply detail="malformed handshake reply: 'digest'"

  SCENT slot (live via agent_entrypoint's local_scent_digest):
  scent=int      -> RAISED TypeError: digests_match requires two str arguments
```

**AFTER:**

```
  digest=int   -> outcome=config_mismatch detail='config digest present in peer payload but not a string: int; aborting before move 1 ...'
  digest=list  -> outcome=config_mismatch detail='config digest present in peer payload but not a string: list; ...'
  digest=dict  -> outcome=config_mismatch detail='config digest present in peer payload but not a string: dict; ...'
  digest=bool  -> outcome=config_mismatch detail='config digest present in peer payload but not a string: bool; ...'

  CONTROLS:
  wrong-but-str  -> outcome=config_mismatch detail='config digest mismatch: local=aaaa... remote=bbbb...'   [UNCHANGED]
  absent         -> outcome=malformed_reply detail="malformed handshake reply: 'digest'"                    [UNCHANGED]

  scent=int      -> outcome=scent_mismatch detail='scent digest present in peer payload but not a string: int; ...'
```

### Instance 9 — the two slots the plan did not name, found by probe

**BEFORE:**

```
  step0_digest=int, declaration sent    -> RAISED TypeError: digests_match requires two str arguments
  step0_digest=list, declaration sent   -> RAISED TypeError: digests_match requires two str arguments
  step0_digest=int, NO declaration      -> agreed: 'config digests agree; step0 digest present (declaration content not sent, digest-only)'

  verify_declaration(d, digest=<correct>, hmac_value=99,  secret='s') -> RAISED TypeError
  verify_declaration(d, digest=<correct>, hmac_value=[1], secret='s') -> RAISED TypeError
  verify_declaration(d, digest=<correct>, hmac_value='zz', secret='s') -> returned False
```

**AFTER:**

```
  step0_digest=int, declaration sent    -> agreed: '... step0 digest present but not a string -- unreadable, nothing to verify content against, treated as digest-only'
  step0_digest=list, declaration sent   -> agreed: '... unreadable, nothing to verify content against, treated as digest-only'
  step0_digest=int, NO declaration      -> agreed: 'config digests agree; step0 digest present (declaration content not sent, digest-only)'   [BYTE-IDENTICAL to before]
  hmac non-str                          -> agreed: '... verified against its digest (declaration hmac unreadable -- treated as unsigned)'
```

### G7 — `peer_game_id` into `adopt_negotiated_game_id`

**BEFORE:**

```
  unhashable {}        -> RAISED TypeError: unhashable type: 'dict'
  unhashable []        -> RAISED TypeError: unhashable type: 'list'
  traversal            -> uid='../../evil'
                          candidates={'../../evil', 'own1111own1111aa'}
                          log_path='...\logs\..\..\evil.jsonl'  exists=True  old_exists=False
  empty str            -> uid='own1111own1111aa'
                          candidates={'', 'own1111own1111aa'}          <-- the SPLIT
  over-long            -> RAISED FileNotFoundError: [WinError 3] ... 'xxxx...xxxx.jsonl'
  non-str int          -> uid=7   candidates={'own1111own1111aa', 7}   log_path='...\logs\7.jsonl'
  nul byte             -> RAISED ValueError: replace: embedded null character in dst
  honest foreign uuid  -> uid='3f2504e0-4f89-11d3-9a0c-0305e82c3301'   [correct]

  negotiated_game_id() alone, the ':71' fallback:
  empty str      -> thief resolves to 'own1111own1111aa'      <-- ABSENT
  unhashable {}  -> thief resolves to 'own1111own1111aa'
  int 7          -> thief resolves to 7                       <-- a non-str id ADOPTED
```

**AFTER** (every hostile shape, identically):

```
  <each of the 8 hostile shapes> -> uid='own1111own1111aa'
                                    candidates=None
                                    log_path unchanged, old file still in place
  honest foreign uuid            -> uid='3f2504e0-4f89-11d3-9a0c-0305e82c3301'
                                    candidates={'3f2504e0-...', 'own1111own1111aa'}
                                    log_path='...\logs\3f2504e0-....jsonl'  exists=True

  negotiated_game_id() alone:
  empty str      -> 'own1111own1111aa'
  unhashable {}  -> 'own1111own1111aa'
  int 7          -> 'own1111own1111aa'      <-- was 7
```

`candidates=None` is the load-bearing detail: `audit_state.state_binding_detail` **SKIPS** the membership check on None (its own stated limitation (a)), so a rejected id accuses nobody.

## Revert probes (non-vacuity)

| Probe | Change | Result |
|---|---|---|
| **P1** | `usable_peer_game_id` -> pre-05-12 passthrough | **41 fail** |
| **P2** | traversal clause removed | **7 fail** |
| **P3** | replace the safety rule with OUR OWN 16-lower-hex convention | **18 fail** -- every fairness control |
| **P4** | `compare_named_digest` back to its None-only branch | **18 fail** |
| **P5** | both step0-corridor guards removed | **10 fail** |

P3 is the one that matters: it is the tempting wrong rule, and the fairness controls refute it. That is the discrimination this plan owes, and it is the same discrimination 05-10 recorded when it refused `isinstance(turn, int)`.

## Files Created/Modified

- `src/pursuit/network/config_hash.py` — `unusable_peer_digest` (the shared gate); `compare_named_digest` consumes it; `digests_match` **untouched**
- `src/pursuit/network/handshake_step0.py` — instance 9 contained; both new cases downgraded, not aborted
- `src/pursuit/network/game_identity.py` — both call sites consume one absence answer; 162/150 -> **split**
- `src/pursuit/network/game_identity_validate.py` *(new)* — `usable_peer_game_id`, `_is_safe_filename_stem`, `relocate_log`, `_MAX_PEER_GAME_ID`
- `src/pursuit/security/audit.py` — boundary rule + instances 7/8/9 + the corridor note (**comment only**, count unchanged at 142)
- `tests/unit/test_config_hash.py` — `:131-135` **re-specified**, then split at 161/150
- `tests/unit/test_config_hash_peer.py` *(new)* — the peer half + the strict-contract pin
- `tests/unit/test_handshake_peer_digest.py` *(new)* — the corridor sweep through the real entry points
- `tests/unit/test_game_identity_validate.py` *(new)* — 20 unsafe shapes, 8 honest foreign conventions, the anti-vacuity guard
- `tests/unit/test_game_identity_adopt.py` *(new)* — the adversarial adopt suite + the whole-chain fairness control
- `tests/unit/test_game_identity.py` — pins that `negotiated_game_id` shares the gate
- `docs/phases/phase-5/TODO.md` — 05-12 row carries its execution record (box left ☐ for verify-work, per the 05-10 precedent)

## Decisions Made

1. **The two new step0 escapes are DOWNGRADED, never aborted.** The first draft routed the step0 digest through `unusable_peer_digest`, which turned `step0_digest=1234` with no declaration from `AGREED` into `STEP0_MISMATCH`. That is a peer this codebase agreed with at `0437559`, lost to a JSON type on a field never compared on that path -- a false accusation (rules 16/22) bought for no evasion closed, since a peer reaches the same outcome by sending no declaration at all. Reversed, and the reversal is now pinned by `test_a_non_str_step0_digest_alone_agrees_exactly_as_it_did_before`, which asserts the pre-fix detail string **byte for byte**.
2. **An unusable peer id yields `candidate_game_ids = None`, not a set excluding the peer.** The excluding set is precisely the `''` defect: every honest peer record then fails membership and we self-declare a technical loss. None disables an optional anti-replay binding and accuses no one.
3. **`digests_match` keeps its strict contract.** The peer boundary is `compare_named_digest`; internal misuse still raises, and is now pinned on **both** argument positions.
4. **`_MAX_PEER_GAME_ID = 128` is a source constant with its derivation beside it.** 255-byte path-component limit minus the longest derived affix (`declaration_{id}_peer.json`, 22 chars) gives a hard ceiling of 233; 128 sits below it and still admits a 16-hex uid, a 36-char UUID and a 64-hex digest. Zero new config leaves (CLAUDE.md rule 1).
5. **`relocate_log` catches `(OSError, ValueError)`.** `ValueError` is not academic -- an embedded NUL raises `ValueError: replace: embedded null character in dst`, measured. On failure we keep our own uid, and the peer's id **stays** on the table so the audit still accepts it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Two more digest escapes in the same corridor (instance 9)**
- **Found during:** Task 1, sweeping the corridor rather than the two slots the plan named
- **Issue:** `step0_sign.verify_declaration` hands the peer's `step0_digest` and the peer's declaration `hmac` straight to `digests_match`. Both raised `TypeError` on a non-str, both reachable in production (`agent_entrypoint` always supplies `local_step0_digest`; the hmac path is live whenever a shared secret is configured -- i.e. exactly the league-day cloud setup). Leaving them would have made this plan's own first truth ("no peer-controlled value reaching the handshake can raise out of `run_agent`") **false**.
- **Fix:** Contained at the `_step0_verified` boundary, both **downgraded** with distinct named details.
- **Files modified:** `src/pursuit/network/handshake_step0.py` (not in the plan's file list — Rule 3 precedent: 05-10 edited this same module for instance 6, 06-03 edited `agent_lifecycle.py` the same way)
- **Verification:** probe before/after above; revert probe P5 fails 10 cases.
- **Committed in:** `52a6b47`

**2. [Rule 1 - Bug] The first draft of fix #1 created a new false-accusation path**
- **Found during:** Task 1, comparing the AFTER probe against the BEFORE probe line by line
- **Issue:** Routing the step0 digest through `unusable_peer_digest` changed `step0_digest=<non-str>` with no declaration from `AGREED` to `STEP0_MISMATCH`.
- **Fix:** Reversed to the module's own lenient precedent for unreadable-but-optional structures; the pre-fix detail string is now pinned byte for byte.
- **Committed in:** `52a6b47`

**3. [Rule 3 - Blocking] `game_identity.py` breached the 150-line gate at 162**
- **Fix:** Split into the **pre-authorized** `game_identity_validate.py` (`usable_peer_game_id`, `_is_safe_filename_stem`, `relocate_log`, the constant). Nothing compressed; the module docstring names the split.
- **Committed in:** `11e9978`

**4. [Rule 3 - Blocking] `tests/unit/test_config_hash.py` breached the gate at 161**
- **Fix:** Split into `test_config_hash_peer.py`. The re-specified `test_compare_named_digest_uses_constant_time_compare` and every pre-05-12 case **stay in the original file**, so the line reference the plan cites still resolves.
- **Committed in:** `52a6b47`

**5. [Rule 2 - Missing Critical] `relocate_log`'s guard had no covering test** (self-audit)
- **Issue:** `game_identity_validate.py` sat at 93% with `130-133` unreached -- an untested exception guard proves nothing.
- **Fix:** A `monkeypatch`ed OS refusal, pinning **both** halves of the contract (we keep our uid **and** the peer's id stays on the table). Module now 100%.
- **Committed in:** `5c92ec7`

**6. [Rule 2 - Missing Critical] The parametrised evidence sets could empty out silently** (self-audit)
- **Issue:** pytest treats an empty `parametrize` argument as a **skip**, not an error, so emptying `UNSAFE` or `HONEST_FOREIGN` would turn most of this plan's evidence green and silent.
- **Fix:** A guard asserting both sets' minimum size and that no value is claimed both safe and unsafe.
- **Committed in:** `765d8a6`

---

**Total deviations:** 6 auto-fixed (2 bug/first-draft-correction, 3 missing-critical, 2 blocking line-gate splits — #2 counted once under Rule 1).
**Impact on plan:** No scope creep. Every one is inside the plan's own stated truths; the two splits are exactly the outcome the plan pre-budgeted for.

## Self-audit (the 05-VERIFICATION lens, applied to my own change)

**Every new validation function has PRODUCTION callers** (grep, not assertion):

| Function | Production caller chain |
|---|---|
| `unusable_peer_digest` | `config_hash.py:120` -> `_compare_offer:118,125` -> `evaluate` -> `perform_handshake`/`respond_to_handshake` -> `run_agent` |
| `usable_peer_game_id` | `game_identity.py:84` (-> `agent_audit_wiring.write_declaration:87`) **and** `game_identity.py:170` -> `agent_entrypoint.run_agent:98` |
| `relocate_log` | `game_identity.py:180` -> `adopt_negotiated_game_id` -> `run_agent:98` |
| `_is_safe_filename_stem` | `game_identity_validate.py:108` |

None is test-only. No dead validator shipped.

**Vacuous-pass probes:** the hostile suites assert `is None` and would pass against an always-reject rule -- refuted by the fairness suites, which assert `== value`; P1 and P3 fail 41 and 18 cases respectively. The whole-chain control carries a third-game **negative** control so `state_binding_detail` cannot be trivially returning None. The empty-parametrize hole is closed by deviation #6.

## Gate output (real, this session)

```
===== RUFF =====        All checks passed!            ruff exit=0
===== LINE LIMIT =====                                line-limit exit=0
===== NO LLM IN STRATEGY =====  OK: no forbidden imports   no-llm exit=0

src\pursuit\network\config_hash.py                  26      0   100%
src\pursuit\network\game_identity.py                44      0   100%
src\pursuit\network\game_identity_validate.py       27      0   100%
src\pursuit\network\handshake_step0.py              29      0   100%
Required test coverage of 85.0% reached. Total coverage: 96.57%
====================== 1478 passed in 157.17s (0:02:37) =======================

GATE-6:  criterion_1_four_phases_commit_reveal: PASS
         criterion_2_hash_nonce_mismatch_technical_loss: PASS
         criterion_3_step0_verified_before_move_1: PASS      exit=0

dev_launch.py exit=0
  police 57db320c3383f405.jsonl  game_over outcome=capture  verdict matched=True  mismatches=0
  thief  57db320c3383f405.jsonl  game_over outcome=capture  verdict matched=True  mismatches=0
  -> ONE shared uid across both sides' log AND ledger; zero technical_win
```

**Against the orchestrator's baseline (1374 passed / 96.54%): +104 tests, +0.03pp, zero failures.** `test_belief_policy.py`'s per-turn budget test — the documented deferred item #9 flake — **passed in all three full-suite runs** this session, under `0437559`'s rewritten clock. It was not touched.

**Untouched, verified by `git diff HEAD`:** `tests/integration/test_secret_channel.py`, `tests/integration/test_game_id_negotiation.py`, `tests/integration/test_belief_policy.py` — all byte-unedited and all passing.

## Issues Encountered

- `scripts/measure_gate6.py` rewrote `docs/phases/phase-6/gate6_measurement_evidence.json`. Diff inspected: **exactly 3 timestamp lines**, every verdict field byte-identical -- the same re-measurement artifact `/gsd:verify-work 6` recorded. **Restored, not committed**: a Phase-5 plan should not churn a Phase-6 evidence file.
- `graph.html` skipped again over the 5000-node viz limit (7524 nodes), matching the 04-12 / 05-03 / 05-08 precedent. `graph.json` stayed unstaged (gitignored build artifact).

## Knowledge graph

Refreshed (05-96): **7524 nodes / 13490 edges / 466 communities** (was 7411 / 13317 / 470). New modules confirmed present in `graph.json`: `game_identity_validate` 21 nodes, `test_game_identity_adopt` 21, `test_handshake_peer_digest` 19, `test_config_hash_peer` 12.

## User Setup Required

None.

## Next Phase Readiness

- **05-13 (G6)** is unblocked and untouched by this plan: it owns the audit/watchdog interaction, and nothing here changed `agent_audit_wiring` or `deadline`.
- **Carry-forward for the next hardening pass:** the boundary rule's bar is now "a TENTH is a review failure". The method that found instances 7-9 is written into `audit.py` and should be the method used again -- enumerate every peer-controlled value a boundary function reads and state what it returns for each shape, rather than closing the one door that was reported.
- **No new deferred items.** The pre-existing open set (#2, #3, #4, #5, #8, #9) is unchanged; note that **#3** (`commit_pack.verify_reveal` is shape-fragile against peer data, contained at its one production call site) is the same pattern as instance 9 and is now the most likely source of a tenth.

## Self-Check: PASSED

All 14 files this summary claims exist on disk. All 5 commit hashes resolve in
`git log`. Every source line number cited above was re-read and confirmed:
`config_hash.py:120`, `game_identity.py:84/170/180`,
`game_identity_validate.py:108`, `agent_audit_wiring.py:87`,
`agent_entrypoint.py:98`. `audit.py` re-measured at **142** code lines, so the
"comment only, count unchanged" claim is measured rather than asserted.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-16*
