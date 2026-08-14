---
phase: 05-cloud-exposure-and-tunneling
plan: "05"
subsystem: network+security
tags: [game-id, d-61, negotiated-identity, state-record, anti-replay, rules-16-22, sec-05, sec-08, cloud-02]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography
    provides: HandshakeResult.peer_game_id (D-61, 06-03), build_state_record / D-60's five fields (06-01), audit_peer_records + _audit_one's four checks (06-03/06-05), turn_commit_ledger.ledger_path
  - phase: 05-cloud-exposure-and-tunneling
    provides: run_final_audit(ctx, *, board_outcome) and the three-step teardown (05-04)
provides:
  - "game_identity.GameIdentity: the MUTABLE (game_uid, log_path) binding a construction-time closure can follow across a one-off rename"
  - "game_identity.negotiated_game_id: D-61's ONE policy definition (agent_audit_wiring._declared_game_id deleted, not copied)"
  - "game_identity.adopt_negotiated_game_id: makes the negotiated id govern log, ledger stem and every hashed commit -- and captures the audit's candidate id set BEFORE its own rebind"
  - "AgentContext.identity / .negotiated_game_id / .candidate_game_ids, all optional and defaulted"
  - "security/audit_state.state_binding_detail: the D-60 record's turn/role/game_id checks, with membership-not-equality and all THREE limitations stated in source"
  - "audit_peer_records(..., *, candidate_game_ids=None, forbidden_role=None) -- both supplied per-direction by run_final_audit"
  - "_audit_one contains a malformed peer payload as a named mismatch instead of a TypeError that killed the process (rule 36)"
affects: [05-06, 05-08, 07-reporting-and-visualization-shell]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Relocate-and-re-export at the 150-line gate: the closures move, every importer resolves unchanged (secret_wiring 05-02 -> game_identity 05-05)"
    - "A mutable value object as a plain parameter, where a construction-time closure cannot close over a context that does not exist yet (design note 12)"
    - "NEGATIVE identity checks (forbidden_role) instead of equality, so a peer's own vocabulary is never imposed on"
    - "Capture-before-rebind: the audit's evidence set is built at the one instant both values are still distinct"
    - "A WIRING assertion beside the unit controls, asserting on the set the production path really builds"

key-files:
  created:
    - src/pursuit/network/game_identity.py
    - src/pursuit/security/audit_state.py
    - tests/unit/test_game_identity.py
    - tests/unit/test_audit_state_binding.py
    - tests/unit/test_audit_state_wiring.py
    - tests/integration/test_game_id_negotiation.py
  modified:
    - src/pursuit/network/agent_wiring.py
    - src/pursuit/network/agent_context.py
    - src/pursuit/network/agent_lifecycle.py
    - src/pursuit/network/agent_entrypoint.py
    - src/pursuit/network/agent_audit_wiring.py
    - src/pursuit/security/audit.py
    - tests/unit/test_agent_entrypoint.py
    - tests/unit/test_audit.py
    - tests/unit/test_audit_coverage.py

key-decisions:
  - "state.game_id is validated by MEMBERSHIP in {our minted uid, the id the peer published}, captured INSIDE adopt_negotiated_game_id BEFORE its rebind -- never equality, because both equality shapes false-accuse an honest peer (rules 16/22)"
  - "state.role is a NEGATIVE check (state.role != forbidden_role), never equality with our expected token -- book Sec5.3.1 shares the RECIPE, not the contents, and this repo alone carries two role vocabularies"
  - "state.turn == entry.turn is ALWAYS enforced, no parameter: commit_own_action passes ONE turn to both the record and the append"
  - "write_declaration calls negotiated_game_id rather than reading ctx.game_uid, so a caller that has NOT adopted (the integration harnesses) keeps exactly the pre-05-05 filename"
  - "security/audit.py was SPLIT (audit_state.py) at the 150-line gate rather than compressed; audit.py's docstring names the sibling so the reasoning stays findable"
  - "A malformed peer payload is contained at audit._audit_one, the one production call site that sees peer data -- not by loosening commit_pack, which D-59 deliberately keeps strict"

patterns-established:
  - "Two revert probes per structural fix: one for 'the fix absent', one for 'the fix present but built in the wrong place'"
  - "The candidate set may legitimately hold ONE element; nothing asserts len == 2 in production"

# Metrics
duration: 80min
completed: 2026-08-14
---

# Phase 5 Plan 05: One Negotiated Game Id, and a State Record With Readers Summary

**The handshake-negotiated game id now governs the whole match — a real loopback game produces one stem `f21a1071045f801c` across BOTH sides' log, ledger and declaration, and both sides commit that same `state.game_id` — and the audit finally reads that record, rejecting a replayed turn, role or game id without ever imposing our own vocabulary or our own id convention on an honest opponent.**

## Performance

- **Duration:** ~80 min
- **Tasks:** 3 of 3
- **Files created:** 6 · **Files modified:** 9
- **Tests:** +20 (plan predicted +10 to +14; the excess is the two 150-line-gate test splits plus two payload-robustness cases)

## Accomplishments

- **The four criterion-2 artifacts join.** `adopt_negotiated_game_id` runs in `run_agent`
  after `result.agreed` and before `write_declaration`/`run_turn_loop`, renames the log,
  and rebinds `ctx.log_path` / `ctx.game_uid` / `ctx.identity` together. The D-64 ledger
  needs no separate handling — `ledger_path` derives from `log_path.stem` and
  `commit_own_action` first runs inside the turn loop, after this point.
- **The construction-time wiring survives the rename.** `make_transition_reporter` and
  `make_freeze_handler` read a mutable `GameIdentity` at CALL time. They cannot close over
  an `AgentContext` (design note 12: they are handed to `TurnStateMachine`/`Watchdog`
  before one exists), which is precisely why the naive fix leaves them writing to the
  pre-negotiation path forever, silently.
- **D-60's state record stops being write-only.** `_audit_one` now validates
  `state.turn`, `state.role` and `state.game_id`. The 05-UAT.md probe that reported a
  forged `{game_id: OTHER-GAME, turn: 99, role: police}` record as **matched** now
  reports a mismatch.
- **No honest peer is accused.** Five paired controls, including the two that a
  vocabulary-blind or convention-blind implementation would fail: a peer whose record
  says `"cop"` where we say `"thief"`, and a peer that adopted OUR id while we adopted
  theirs.
- **A rule-36 process-death hole closed on the way past** (Rule 2): a malformed peer
  payload used to raise `TypeError` out of `verify_reveal(**payload)`, uncaught by
  `agent_entrypoint`'s `except ToolError`, killing us before any verdict.
- **`agent_wiring.py` came DOWN 148 → 122**, as the plan required.

## Task Commits

1. **Task 1: a game id the construction-time wiring can follow** — `ead48df` (feat)
2. **Task 2: adopt the negotiated id before the ledger exists** — `b06b4b3` (feat)
3. **Task 3: the audit reads the committed state record** — `01ff8ed` (feat)

## The exact adoption call-site ordering inside `run_agent`

Recorded verbatim, because the next plan touching this function needs it
(`agent_entrypoint.py`, inside `_play`):

```
perform_handshake(...)            -> result
if not result.agreed: return None
adopt_negotiated_game_id(ctx, result)     <-- HERE
write_declaration(ctx, cfg, result, declaration_envelope)
outcome = await run_turn_loop(ctx)
run_final_audit(ctx, board_outcome=outcome)
```

`test_agent_entrypoint.py`'s three exact order lists pin this. The
handshake-does-not-agree list deliberately does NOT contain
`adopt_negotiated_game_id` — there is no negotiated id without an agreement.

## Measured `ctx.candidate_game_ids`, BOTH roles

Driven through the real `adopt_negotiated_game_id`, with `O = "our-uid"` (our minted
id) and `P = "peer-uid"` (the id the peer published):

| our role | after adoption `ctx.game_uid` | `ctx.negotiated_game_id` | **`ctx.candidate_game_ids`** |
|---|---|---|---|
| police | `O` (never adopts) | `P` | **`{O, P}` — two elements** |
| thief  | `P` (adopted) | `P` | **`{O, P}` — two elements** |
| thief, peer published none | `O` | `None` | `None` (check skipped) |
| police, ids already equal | `O` | `O` | `{O}` — legitimately ONE element |

**Two elements on the thief as well as the police** — the success criterion. One element
there would have meant the set was built after the rebind, where
`negotiated_game_id('thief', O, P) == P` and `ctx.game_uid` has just become `P`, so
`{P, P}` is `{P}` and the membership check degenerates to equality.

Confirmed on the live integration path too: `test_game_id_negotiation.py` handshakes two
real contexts with `UID_A`/`UID_B` and asserts `{UID_A, UID_B}` on both sides.

**Which candidate id each side's own records carried:** both. In the measured loopback
game the police kept `f21a1071045f801c` and the thief adopted it, so every record on
both sides carries the police's minted id — the first candidate on the police, the
second on the thief. That asymmetry is exactly why the self direction cannot be checked
by equality either; membership covers both.

## The three stated limitations (in `src/pursuit/security/audit_state.py`, not just here)

1. **(a) A peer that publishes NO `game_id` at handshake is not bound cross-game at
   all.** The caller passes `None` and the check is skipped rather than accusing.
2. **(b) A peer that publishes a PRIOR GAME'S id makes that game's records satisfy
   membership**, so check 3 does not stop a determined cross-game replay. What contains
   the residue is `_audit_one`'s LAST check, `payload.move != observed_reveals[turn]`: a
   replayed record obliges the attacker to have actually played the old move, which
   `decode_revealed_action` already validated as legal from their current position — a
   handicap, not an exploit. **It is NOT contained by `verify_reveal`**, which re-hashes
   the peer's payload against whatever `h_commit` the peer chose to send this game, so
   an attacker commits `h_old`, presents the matching old payload, and the re-hash
   passes.
3. **(c) A peer deriving a THIRD id** (a hash of both, the lexicographic min) is accused
   under any candidate-set rule. Considered and DECLINED: no mechanism covers an
   unbounded space of conventions. Recorded so the next reader knows it was weighed.

## Verification (measured, not claimed)

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed!** — 0 violations |
| `uv run pytest tests/ --cov` | **1293 passed, 96.35%** (05-04 closed at 1262 / 96.30%) |
| `bash scripts/check_line_limit.sh` | exit **0** |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `uv run python scripts/measure_gate6.py` | **exit 0 — all three book §10.4 criteria PASS** |
| Item 6 — `grep "def _declared_game_id" src/` | **no hits** — the D-61 policy has exactly one home |
| Item 7 — `candidate_game_ids` / `forbidden_role` | **SUPPLIED**, not merely accepted: `agent_audit_wiring.py:148` (peer direction) and `:152` (self direction); the set is BUILT at `game_identity.py:157`, above the rebind; `run_final_audit` passes `ctx.candidate_game_ids` through and never reconstructs it |
| Item 8 — real loopback game | **one stem on BOTH sides**, see below |

**Caveat on the suite count, stated honestly:** another agent was executing plan **05-06
concurrently in this same worktree** throughout (see Issues). The 1293 total therefore
includes their new hint-flow tests. This plan's own contribution is **+20**, measured
directly: `test_game_identity.py` 4, `test_game_id_negotiation.py` 3,
`test_audit_state_binding.py` 10, `test_audit_state_wiring.py` 3. No test failed at any
point after the fixture correction below.

Coverage of the files this plan touched: `game_identity.py` **100%**, `audit.py`
**100%**, `agent_audit_wiring.py` **100%**, `agent_context.py` **100%**,
`agent_lifecycle.py` 98%, `agent_wiring.py` 98%, `audit_state.py` 94% (the single
uncovered line is the documented unreachable `isinstance` backstop),
`agent_entrypoint.py` 87%.

### GATE-6 re-run verdict

```
GATE-6 measurement -- localhost, zero env vars
  criterion_1_four_phases_commit_reveal: PASS
  criterion_2_hash_nonce_mismatch_technical_loss: PASS
  criterion_3_step0_verified_before_move_1: PASS
```

`exit 0`. The regenerated `docs/phases/phase-6/gate6_measurement_evidence.json` differs
from the committed one in the two `predates_detail` mtimes, `generated_at`, and the
per-side `hint` envelope counts (4/5 swapped — that last one is 05-06's concurrent hint
work, not this plan's). Every verdict field is byte-identical. Restored with
`git checkout --`, the same convention 05-04 and `/gsd:verify-work 6` used.

### Item 8 — a real loopback game (`uv run python scripts/dev_launch.py`, exit 0)

```
logs/police/  f21a1071045f801c.jsonl  f21a1071045f801c.ledger.jsonl  declaration_f21a1071045f801c.json
logs/thief/   f21a1071045f801c.jsonl  f21a1071045f801c.ledger.jsonl  declaration_f21a1071045f801c.json
```

One stem per side, and the two sides' stems EQUAL. Read back from the two ledgers:

| side | `state.game_id` | `state.role` | `state.turn == record turn` | records | last event |
|---|---|---|---|---|---|
| police | `{f21a1071045f801c}` | `{police}` | True | 5 | `audit_verdict matched=True` |
| thief | `{f21a1071045f801c}` | `{thief}` | True | 5 | `audit_verdict matched=True` |

Before this plan the thief's log and ledger carried its own process-local uid — the
2026-08-13 artifact, reproduced on loopback every run.

## Revert-probe results (recorded verbatim)

### Task 2 — two probes, because "absent" and "in the wrong place" are different bugs

**Probe A — adoption absent** (`adopt_negotiated_game_id` neutered to a no-op):

```
2 failed, 1 passed
FAILED test_all_four_artifacts_join_on_one_negotiated_id
E   AssertionError: the four artifacts do not join: {'bbbb2222bbbb2222', 'aaaa1111aaaa1111'}
FAILED test_the_candidate_set_has_two_elements_on_both_roles
E   AssertionError: assert None == {'aaaa1111aaaa1111', 'bbbb2222bbbb2222'}
```

So the harness genuinely proves the adoption, and is not vacuous through the shared-uid
pitfall the plan warned about.

**Probe B — adoption present, candidate set built AFTER the rebind** (the pass-2
blocker's shape):

```
1 failed, 2 passed
FAILED test_the_candidate_set_has_two_elements_on_both_roles
E   AssertionError: assert {'aaaa1111aaaa1111'} == {'aaaa1111aaaa1111', 'bbbb2222bbbb2222'}
E     Extra items in the right set: 'bbbb2222bbbb2222'
```

Read carefully: the artifact-joining test still PASSES and the POLICE side of the
wiring assertion still passes — only the THIEF side collapses to one element. That is
the plan's warning measured: a control that hand-built its own two-element set would
have exercised the police shape only and shipped a check that accuses on the thief.

### Task 3 — the state checks disabled (`state_binding_detail` returning None, and the
malformed-payload containment reverted)

```
7 failed, 6 passed
FAILED test_a_state_record_naming_another_turn_is_a_mismatch
FAILED test_our_own_role_replayed_back_at_us_is_a_mismatch
FAILED test_a_state_record_naming_another_game_is_a_mismatch_as_police
FAILED test_a_state_record_naming_another_game_is_a_mismatch_as_thief
FAILED test_a_trailing_commit_that_fails_a_state_check_is_still_a_mismatch
FAILED test_a_malformed_payload_is_a_named_mismatch_not_a_process_death
FAILED test_a_state_record_missing_its_d60_fields_is_a_named_mismatch
```

The 6 that pass pre-fix are exactly the five fairness controls plus the wiring
assertion (which exercises `game_identity`, not `audit`). Every substantive case fails
pre-fix; every control passes pre-fix. That is the discrimination a control owes.

### The 05-UAT.md G2 forged-record probe, re-run against shipped code

```
unwired (both args omitted, i.e. every pre-05-05 caller):
   all_matched = False | turn 1: committed state record names turn 99 (replay)
WIRED as run_final_audit now calls it:
   all_matched = False | turn 1: committed state record names turn 99 (replay)
```

Previously **"matched"**. It now fails even with both optional arguments omitted,
because the `state.turn` check needs no parameter.

## Deviations from Plan

### 1. [Rule 3 - Blocking] `security/audit.py` was SPLIT, not compressed

- **Found during:** Task 3, at the line gate.
- **Issue:** With the three checks and the mandated in-source reasoning, `audit.py`
  measured **168/150**.
- **Fix:** `src/pursuit/security/audit_state.py` — `state_binding_detail` plus the whole
  membership-vs-equality note and all three limitations. `audit.py` (now **122**) imports
  it back and its module docstring names the sibling explicitly, so verification item 7's
  reasoning stays findable from `audit.py`. The seam is real: `audit.py` owns D-67's
  payload/coverage audit, `audit_state.py` owns D-60's anti-replay step binding.
- **Same at the test gate:** `test_audit_state_binding.py` measured 153 and was split
  into it (99, the checks and controls) plus `test_audit_state_wiring.py` (71, the
  wiring assertion and the two controls that ride the real set), importing the shared
  helpers rather than copying them.
- **Committed in:** `01ff8ed`

### 2. [Rule 3 - Blocking] `test_audit.py` / `test_audit_coverage.py` fixtures made faithful

- **Found during:** Task 3, when the always-on `state.turn` check turned 6 pre-existing
  tests red.
- **Issue:** Both `_genuine_records` helpers reused ONE turn-1 state record for turns
  1, 2 and 3. No honest ledger can produce that — `commit_own_action` passes ONE `turn`
  to both `build_state_record` and `CommitLedger.append`. The fixtures, not the check,
  were wrong.
- **Fix:** `state = dict(_STATE, turn=turn)` per turn, the exact shape
  `test_audit_turn_binding._honest_turn` already used. **No assertion was weakened and
  no test was deleted** — every original assertion is untouched and still green.
- **Committed in:** `01ff8ed`

### 3. [Rule 2 - Missing Critical] A malformed peer payload no longer kills the process

- **Found during:** Task 3, writing the malformed-state case the plan asked for.
- **Issue:** The plan requires "a missing or malformed `state` key is a mismatch with a
  named detail, never a KeyError". With the plan's exact placement that is unreachable:
  `verify_reveal(h, **entry["payload"])` runs FIRST and raises `TypeError` on any other
  shape. Nothing upstream catches it (`agent_entrypoint`'s guard is `except ToolError`),
  so a peer's malformed FINAL_REVEAL killed us before any verdict — making **us** the
  side that published no nonces (rule 36), the class 06-06 fixed for `ToolError`.
- **Fix:** the `verify_reveal` call in `_audit_one` — the ONLY production call site that
  sees peer data (grep-confirmed) — is wrapped, and a malformed payload becomes a named
  mismatch. The plan's placement of the three state checks is UNCHANGED.
- **Not fixed:** `commit_pack` itself stays strict (D-59, and it is not in this plan's
  files). Logged as deferred item #3.
- **Committed in:** `01ff8ed`

---

**Total deviations:** 3, all auto-fixed. Two were the line gate and a pre-existing
fixture; one closed a real rule-36 hole. **No production behaviour beyond the plan's
text was changed** other than that containment, and no gate was weakened.

## Issues Encountered

### Another agent executed plan 05-06 in this worktree at the same time

Discovered mid-Task-1: `HEAD` had moved from `384da44` to `7619758` and the worktree
carried uncommitted edits to `turn_actions.py` / `turn_hint_buffer.py` that this plan
did not make. Consequences, recorded honestly:

1. **A `git stash -u` I ran to check whether two failing hint tests pre-existed briefly
   stashed their in-flight work.** `git stash pop` restored it intact and `git status`
   confirmed every file back. **No work was lost.** No stash was used again.
2. **The Task-1 commit `ead48df` swallowed their staged files.** The pre-commit hook
   blocked my first attempt (their `test_turn_hint_buffer.py` was transiently 155/150);
   between my `git add` and my retry they staged their own files into the SHARED index,
   and `git commit` commits the index. `ead48df` therefore also contains
   `turn_actions.py`, `turn_hint_buffer.py`, `test_hint_delivery.py`, `_hint_fixtures.py`
   and `test_hint_freshness.py`. **Nothing is lost or duplicated** — the content is
   committed exactly once — but that commit's message describes only half of it. Tasks 2
   and 3 were committed with `git commit -- <paths>`, which ignores the shared index, and
   contain exactly 5 and 7 files respectively.
3. **The 1293 suite total is a joint number.** This plan's own +20 is stated above,
   measured file by file.
4. The regenerated GATE-6 evidence's `hint` envelope counts moved (4↔5) because of their
   change, not this one. Every verdict field is byte-identical.

A single-writer worktree is an assumption this workflow makes and the environment broke.
Recommendation for the next parallel wave: give concurrent executors separate worktrees,
or serialise them.

### Two known-benign observations

- `agent_lifecycle.py` is now **148/150**. Legal, but two lines of headroom. Logged as
  deferred item #2 with the suggested split (teardown into `agent_teardown.py`).
- `audit_state.py`'s `isinstance(state, dict)` guard is unreachable with the current call
  order and is documented in source as a BACKSTOP, kept so a future reordering degrades
  to a mismatch rather than an `AttributeError`. It is the file's one uncovered line.

## Knowledge graph

Refreshed after the code landed (05-96): **6982 nodes / 12704 edges / 432 communities**
(was 6827/12372/429). `GRAPH_REPORT.md` moved 416 lines. `graph.html` skipped over
graphify's 5000-node viz limit, matching the 04-12/05-03/05-04/06-04 precedent
(gitignored regardless). `graphify explain "adopt_negotiated_game_id"` confirms the node
at `src/pursuit/network/game_identity.py L125` with 7 edges.

## User Setup Required

None — every measurement in this summary ran offline with zero environment variables set
(`ANTHROPIC_API_KEY` explicitly cleared in every test that could reach a provider).

## Next Phase Readiness

- **G2 is closed on the code side.** Criterion 2's "four joinable artifacts" clause now
  holds on loopback; the remote round (05-08) is what proves it across two machines.
- **05-06** (hint flow + the 17.4 s responder stagger) was landing concurrently; **05-07**
  (G5) remains.
- **05-08** — the human remote round, attempt 2 — should run only after 05-06 and 05-07
  land. It is the only thing that can close GATE-5 criterion 2.
- **Carry-forward for 05-08's operator:** the two machines' logs, ledgers and
  declarations will now all carry the POLICE side's minted id. Join the evidence on that
  one stem; a differing stem on machine B is now a real defect, not the expected state.
- **Nothing is ticked in ROADMAP.md**, per this project's standing convention;
  `docs/phases/phase-5/TODO.md` row 05-05 is marked ◐ with the three commit hashes, to
  be ☑'d at `/gsd:verify-work 5`.

---
*Phase: 05-cloud-exposure-and-tunneling*
*Completed: 2026-08-14*

## Self-Check: PASSED

All 16 claimed files verified present on disk; all 3 task commit hashes verified in
`git log`. Verification items 6 and 7 re-run as greps at self-check time, not carried
over from the Task-3 measurement: `grep "def _declared_game_id" src/` returns nothing,
and `candidate_game_ids`/`forbidden_role` are supplied at `agent_audit_wiring.py:148`
and `:152` with the set built at `game_identity.py:157`, above its own rebind.
