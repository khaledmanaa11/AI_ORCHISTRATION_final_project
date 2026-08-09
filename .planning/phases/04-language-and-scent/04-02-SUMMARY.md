---
phase: 04-language-and-scent
plan: "02"
subsystem: network
tags: [handshake, scent-digest, sha256, canonical-json, rule-23, secrets-compare-digest, d-46, config-hash]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plan 04-01)
    provides: >
      shared/scent_config.py's load_scent_model()/scent_digest() -- the locked, deterministic
      SHA-256 digest of the whole Table-16 payload (kernel + source/decay/window + worked
      example) this plan exchanges at handshake time
provides:
  - "handshake_wire.py: HandshakeKey.SCENT_DIGEST + build_offer(local_digest, local_role, *, local_scent_digest=None) -- the payload carries exactly two keys once a scent digest is supplied, and omits (never nulls) the key otherwise"
  - "config_hash.py: compare_named_digest(name, local, remote) -- a generic named-pair digest comparison (secrets.compare_digest, remote=None counts as 'absent') reused by both the config and scent checks so neither hand-rolls '=='"
  - "handshake_evaluate.py (NEW): HandshakeOutcome (+SCENT_MISMATCH) / HandshakeResult / evaluate() -- config checked first, then scent only when local_scent_digest is supplied, one call site shared by perform_handshake and respond_to_handshake so neither direction can diverge"
  - "handshake.py stays the single public seam (perform_handshake/respond_to_handshake), now accepting an optional local_scent_digest keyword and re-exporting HandshakeOutcome/HandshakeResult from the new split module unchanged for every existing caller"
affects: [04-12-turn-pipeline-integration (must pass a real local_scent_digest into agent_lifecycle.py/agent_wiring.py's call sites to actually enforce the lock on the live path), 04-13-rules-resolution-lang (cites D-46/rule 23), any later plan reading HandshakeOutcome.SCENT_MISMATCH]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "handshake.py split into handshake.py (public seam) + handshake_evaluate.py (decode/compare/abort internals) at the 150-code-line gate -- same one-directional shape as the pre-existing handshake.py/handshake_wire.py split and 04-01's scent_config.py/scent_kernel.py split: the lower-level module has zero import of the higher-level one, so handshake.py imports HandshakeOutcome/HandshakeResult back and re-exports them"
    - "compare_named_digest(name, local, remote) -> (bool, str) as the one shared digest-comparison shape: any later digest exchanged at handshake (Phase 6's Step-0 declaration) reuses this instead of hand-rolling a new compare"
    - "local_scent_digest: str | None = None as a staged-rollout default across build_offer/perform_handshake/respond_to_handshake -- None means THIS call site has not opted into the scent lock yet and skips only its own scent check (never the config check); a remote peer can never use this to opt itself out of OUR check once we have opted in"
    - "tests/unit/test_handshake_scent.py split from test_handshake.py at the same 150-line gate, mirroring the pre-existing test_handshake_abort.py/test_handshake_client.py split -- imports FakeReporter/fake_caller/peer_reply rather than duplicating them (QUAL-02)"

key-files:
  created:
    - src/pursuit/network/handshake_evaluate.py
    - tests/unit/test_handshake_wire.py
    - tests/unit/test_handshake_scent.py
  modified:
    - src/pursuit/network/handshake_wire.py
    - src/pursuit/network/handshake.py
    - src/pursuit/network/config_hash.py
    - tests/unit/test_handshake.py
    - tests/unit/test_config_hash.py

key-decisions:
  - "local_scent_digest defaults to None everywhere (build_offer/perform_handshake/respond_to_handshake) rather than being required -- the ONLY way to satisfy Task 2 without editing agent_lifecycle.py/agent_wiring.py (owned by 04-12, wave 6) or breaking tests in files this plan does not list (test_agent_lifecycle.py, test_handshake_abort.py, test_handshake_client.py, tests/integration/test_turn_lifecycle.py). See Deviations for the full reasoning and why this does not contradict the plan's 'backwards compatibility is a non-goal' truth."
  - "handshake.py split into handshake.py + handshake_evaluate.py at the 150-code-line ceiling (not in the plan's files_modified list, but CLAUDE.md's line-limit rule takes precedence -- see Deviations), mirroring this exact codebase's own precedent twice over (handshake_wire.py's existing split, and 04-01's scent_config.py/scent_kernel.py split)"
  - "Config is compared before scent, short-circuiting on a config failure -- both are still 'checked in the same _evaluate call' (now evaluate(), in handshake_evaluate.py) per the plan's must_haves, but when both would fail, the config mismatch is what gets named, since a config difference is the more fundamental failure"
  - "HandshakeOutcome gained a fifth member, SCENT_MISMATCH, parallel to CONFIG_MISMATCH -- both the human-readable detail AND the machine-readable outcome now distinguish which commitment broke, not just the message text"
  - "tests/unit/test_handshake_scent.py created as a new sibling file (not in files_modified) rather than cramming the four-cases coverage into test_handshake.py's remaining ~15-line budget -- mirrors the pre-existing test_handshake_abort.py/test_handshake_client.py split of the exact same parent file"

requirements-completed: [LANG-07, SEC-01]

# Metrics
duration: ~25min
completed: 2026-08-08
---

# Phase 4 Plan 02: Handshake Carries the Scent Digest Summary

**The Table-16 scent-emission model's SHA-256 digest now rides as a second key in the existing Phase-2 handshake offer, verified by a shared `compare_named_digest` helper (`secrets.compare_digest`, never `==`), aborting to `State.ERROR` and naming which commitment — config or scent — broke.**

## League Opponent Handshake Contract

Per this plan's `<output>` spec, the two payload keys and the shipped digest value an
opponent team must be sent before a match:

| Payload key | Constant | Value (this repo, both `config/police` and `config/thief`) |
|---|---|---|
| `digest` | `HandshakeKey.DIGEST` | `config_digest("game_params.json")` — game-specific, computed per match |
| `scent_digest` | `HandshakeKey.SCENT_DIGEST` | `c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e` (fixed — Table 16 is locked, not game-specific) |

The scent digest is pinned by `tests/unit/test_handshake_scent.py::test_real_scent_config_pair_agrees_and_pins_shipped_digest`, matches plan 04-01's shipped value exactly, and is re-derived (not hardcoded) via `scent_digest(load_scent_model(...))` everywhere else in the codebase.

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-08T22:11:00Z
- **Tasks:** 2 planned tasks (2 commits, one per task)
- **Files modified:** 8 (3 created, 5 modified)

## Accomplishments

- `build_offer` carries both commitments in one message: `HandshakeKey.SCENT_DIGEST` added, payload holds exactly the two documented keys when a scent digest is supplied and omits (never nulls) the key otherwise — pinned by `test_handshake_wire.py`'s round-trip-through-`Envelope.to_dict`/`from_dict` tests.
- `evaluate()` (the renamed, relocated `_evaluate`) checks config, then scent, in one shared call site used by both `perform_handshake` and `respond_to_handshake` — a peer cannot pass one digest and fail the other silently. All four required cases are tested end to end: both agree → `AGREED`; config differs → `CONFIG_MISMATCH` named; scent differs → `SCENT_MISMATCH` named; scent absent from the peer's payload → `SCENT_MISMATCH` worded "absent" (not "differed").
- A one-cell-family kernel mutation (all four symmetric corners) on either side's locally-derived `ScentModel` aborts **both** `perform_handshake` (initiator) and `respond_to_handshake` (responder) to `State.ERROR` before move 1 — `test_mutated_scent_kernel_aborts_via_perform_handshake` / `..._via_respond_to_handshake`.
- Every comparison goes through `secrets.compare_digest` (`compare_named_digest` → `digests_match`); `grep -n "==" src/pursuit/network/handshake.py src/pursuit/network/handshake_evaluate.py` returns nothing.
- Zero regressions: all 29 pre-existing handshake/config-hash tests (in files this plan does not own — `test_handshake_abort.py`, `test_handshake_client.py`, `test_agent_lifecycle.py`) pass **unmodified**, plus `tests/integration/test_turn_lifecycle.py` and `tests/unit/test_tools_dispatch.py`. Full repo suite: 537 passed, 92.82% coverage (gate ≥85%); `ruff check .` and `scripts/check_line_limit.sh` both exit 0 repo-wide.

## Task Commits

Each task was committed atomically:

1. **Task 1: carry a second digest in the offer** - `ba67e63` (feat) — `handshake_wire.py` (`HandshakeKey.SCENT_DIGEST`, `build_offer`), `config_hash.py` (`compare_named_digest`), `tests/unit/test_handshake_wire.py` (new), `tests/unit/test_config_hash.py`
2. **Task 2: verify both, abort naming the failure** - `830eafc` (feat) — `handshake.py`, `handshake_evaluate.py` (new, see Deviations), `tests/unit/test_handshake.py`, `tests/unit/test_handshake_scent.py` (new, see Deviations)

_Note: no task in this plan was tagged `tdd="true"`; tests were written alongside each task's implementation and committed together, per CLAUDE.md's "tests before or alongside code."_

## Files Created/Modified

- `src/pursuit/network/handshake_wire.py` — `HandshakeKey.SCENT_DIGEST`; `build_offer` gains keyword-only `local_scent_digest=None`
- `src/pursuit/network/config_hash.py` — `compare_named_digest(name, local, remote)`, the shared named-pair comparison Task 1 asked for
- `src/pursuit/network/handshake_evaluate.py` (NEW) — `HandshakeOutcome` (+`SCENT_MISMATCH`), `HandshakeResult`, `build_result`, `not_attempted`, `_abort`, `_compare_offer`, `evaluate` — the decode/compare/abort internals split out of `handshake.py`
- `src/pursuit/network/handshake.py` — now the thin public seam: `HandshakeCaller`, `perform_handshake`, `respond_to_handshake`, both gaining `local_scent_digest=None`; re-exports `HandshakeOutcome`/`HandshakeResult`/`HandshakeKey`/wire constants unchanged
- `tests/unit/test_handshake_wire.py` (NEW) — wire-shape suite: fixed vocabulary, exactly-two-keys, round-trip
- `tests/unit/test_handshake_scent.py` (NEW) — the four D-46 cases + mutated-kernel end-to-end + shipped-digest pin + explicit skip-path test
- `tests/unit/test_handshake.py` — `peer_reply` gains optional `peer_scent_digest`; docstring points to the new split file
- `tests/unit/test_config_hash.py` — `compare_named_digest` coverage: agrees, differs, remote-absent, non-str raises

## Decisions Made

See `key-decisions` in the frontmatter for the full list. The two decisions requiring the most justification are expanded in **Deviations from Plan** below, since both diverge from a literal reading of the plan text (in service of the plan's own "no assertion is deleted or weakened" and CLAUDE.md's line-limit gate).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `local_scent_digest` defaults to `None` instead of being required**

- **Found during:** Task 2, while designing `_evaluate`'s new signature.
- **Issue:** `perform_handshake`/`respond_to_handshake`/`build_offer` are called from production code this plan does not own — `src/pursuit/network/agent_lifecycle.py`'s `run_agent()`/`default_context()` and `agent_wiring.py`'s `make_handshake_responder()` — neither file is in this plan's `files_modified`, and both are explicitly owned by plan **04-12** (wave 6, "Turn-pipeline integration"), which depends on 04-02 and is where the live path gets wired to send a real scent digest. Those call sites use only keyword arguments and never mention a scent digest. Several tests outside this plan's scope call these same functions directly or indirectly with no scent digest: `tests/unit/test_agent_lifecycle.py::test_handshake_tool_answers_a_real_peer` (calls `handshake.build_offer(digest, role)` **positionally** with exactly 2 args), `tests/unit/test_handshake_abort.py` (5 tests), `tests/unit/test_handshake_client.py` (2 tests), `tests/integration/test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over`, `tests/unit/test_tools_dispatch.py`. Making `local_scent_digest` a required parameter would raise `TypeError` in every one of these; making it required but treating an absent LOCAL digest as an automatic mismatch (rather than skipping) would instead leave every one of them aborting to `State.ERROR` where they currently assert success — either way a regression this plan has no mandate to cause, and the "stay strictly inside your plan's `files_modified` list" instruction forbids editing `agent_lifecycle.py`/`agent_wiring.py` to fix it forward.
- **Fix:** `local_scent_digest: str | None = None` on `build_offer`, `perform_handshake`, and `respond_to_handshake`. `build_offer` omits the `SCENT_DIGEST` key entirely when `None` (never sends it as `null`). `_compare_offer` skips **only** the scent comparison when **our own** `local_scent_digest is None` — the config comparison always runs regardless. This is a *local, our-own-opt-in* concept, deliberately kept separate from the plan's "backwards compatibility is a non-goal" truth, which is about a **remote peer's** wire payload: once a call site *has* supplied `local_scent_digest` (every test this plan owns does), a remote peer that omits the key is still unconditionally a mismatch, worded "absent" — exactly as the plan requires. The two axes are independent: remote-peer wire compatibility (non-goal, enforced) vs. internal not-yet-migrated Python call sites within this same multi-plan phase (a scheduling reality of the wave graph, not a specification question the plan's must_haves address).
- **Files modified:** `src/pursuit/network/handshake_wire.py`, `src/pursuit/network/handshake.py`, `src/pursuit/network/handshake_evaluate.py`
- **Verification:** `tests/unit/test_handshake_scent.py::test_local_not_opted_in_skips_scent_even_if_peer_sends_one` asserts the skip explicitly. Every out-of-scope test enumerated above was re-run and passes unmodified (see Accomplishments). `tests/unit/test_handshake_scent.py`'s other 8 tests prove that once both sides DO supply a scent digest, all four required cases (agree / config differs / scent differs / scent absent) behave exactly per the plan.
- **Committed in:** `830eafc` (Task 2 commit)

**2. [Rule 3 - Blocking] Split `handshake.py` into `handshake.py` + `handshake_evaluate.py`**

- **Found during:** Task 2, first line-limit check after adding the scent-comparison logic.
- **Issue:** `handshake.py` measured 144 code lines *before* this plan (only 6 lines of headroom against the 150-line hard gate). Adding `HandshakeOutcome.SCENT_MISMATCH`, the `local_scent_digest` parameter across three functions, and the config-then-scent comparison cascade pushed it to 160 code lines — a violation of `scripts/check_line_limit.sh` (CLAUDE.md-mandated pre-commit/CI gate). The plan's `files_modified` names only `src/pursuit/network/handshake.py` for Task 2, but CLAUDE.md states the line-limit rule "OVERRIDES any default behavior" and takes precedence over plan instructions.
- **Fix:** Extracted `HandshakeOutcome`, `HandshakeResult`, `build_result` (was `_result`), `not_attempted` (was `_not_attempted`), `_abort`, `_compare_offer`, and `evaluate` (was `_evaluate`) into a new sibling module `src/pursuit/network/handshake_evaluate.py` — the same one-directional split shape `handshake_wire.py` already uses (lower-level module has zero dependency on the higher-level one) and the same pattern 04-01 used for `scent_config.py`/`scent_kernel.py`. `handshake.py` imports `HandshakeOutcome`/`HandshakeResult`/`evaluate`/`not_attempted`/`build_result` back and re-exports `HandshakeOutcome`/`HandshakeResult`, so every existing `from pursuit.network.handshake import HandshakeOutcome` (used directly by `test_handshake_abort.py`, `test_handshake_client.py`, and this plan's own `test_handshake.py`/`test_handshake_scent.py`) keeps working with zero changes to those call sites. `_compare_offer` stayed underscore-private (only `evaluate` calls it); `build_result`/`not_attempted`/`evaluate` dropped their underscore since they are now this new module's cross-file API surface.
- **Files modified:** `src/pursuit/network/handshake.py`, `src/pursuit/network/handshake_evaluate.py` (new)
- **Verification:** `handshake.py` is 61 code lines, `handshake_evaluate.py` is 99 — both comfortably under 150. `uv run ruff check .` and `bash scripts/check_line_limit.sh` both exit 0 repo-wide. All 537 repo tests pass.
- **Committed in:** `830eafc` (Task 2 commit)

**3. [Rule 3 - Blocking] New sibling test file `tests/unit/test_handshake_scent.py`**

- **Found during:** Task 2, while writing the four-cases + mutated-kernel test coverage the plan's `<verify>` requires.
- **Issue:** `tests/unit/test_handshake.py` had only ~15 lines of headroom left after the shared-fixture updates (docstring, `peer_reply`'s new optional parameter) needed by every sibling file. The plan's `<verify>` for Task 2 requires at minimum 4 distinct end-to-end scenarios (agree / config differs / scent differs / scent absent) plus "a mutated kernel entry ... produces the scent-mismatch abort end-to-end" — that coverage does not fit in the remaining budget without either weakening the existing tests or exceeding the line-limit gate.
- **Fix:** Created `tests/unit/test_handshake_scent.py`, importing `FakeReporter`/`fake_caller`/`peer_reply` from `test_handshake.py` rather than duplicating them (QUAL-02) — the exact split pattern `test_handshake_abort.py` and `test_handshake_client.py` (both pre-existing, both undeclared in *their own* originating plan's `files_modified`) already established for this same parent file.
- **Files modified:** `tests/unit/test_handshake_scent.py` (new)
- **Verification:** 130 code lines (under 150); all 9 tests pass; `uv run ruff check .` clean.
- **Committed in:** `830eafc` (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (all Rule 3 — blocking; two are direct consequences of the CLAUDE.md line-limit gate, one is a compatibility default forced by out-of-scope call sites this plan is not permitted to edit).
**Impact on plan:** All three are structural/mechanical, required by CLAUDE.md's hard gates or by the "stay inside files_modified" execution constraint, not by any behavioral gap in the plan itself. No scope creep beyond the two-module split and one new test file; every one of the plan's `must_haves` and `<verify>` criteria is met exactly, and no existing assertion anywhere in the repo was deleted or weakened.

## Issues Encountered

- **Two pre-existing, out-of-scope coverage gaps relocated (not introduced) by the Task-2 split:** `handshake.py:67,90` (the `not_attempted(...)` return when `machine.attempt(State.HANDSHAKE)` finds the machine already past `HANDSHAKE`) and `handshake_evaluate.py:128` (`raise ValueError` when a well-formed envelope carries the wrong `type`). Neither branch was exercised by any test before this plan (confirmed: no test anywhere references `"handshake not attempted"` or `"expected a handshake message"`), and this plan changed neither branch's behavior — only its file location. Per the Scope Boundary rule ("only auto-fix issues directly caused by the current task's changes"), these were left as-is rather than "fixed" with new tests; `handshake.py` and `handshake_evaluate.py` still measure 92%/97% file coverage respectively, and the repo gate (≥85%) clears at 92.82% overall.

## User Setup Required

None — no external service configuration required. No new environment variables, no new dependencies.

## Next Phase Readiness

- **Plan 04-05** (belief map core) and **04-06** (provider layer) are unaffected — neither touches `handshake*.py` or `config_hash.py` (verified: no overlap with this plan's wave-2 siblings' `files_modified`).
- **Plan 04-12** (turn-pipeline integration, wave 6) has the explicit job this plan's default-parameter design defers: pass a real `local_scent_digest=scent_digest(load_scent_model(...))` into `agent_lifecycle.py`'s `default_context()`/`run_agent()` and `agent_wiring.py`'s `make_handshake_responder()` call sites so the LIVE two-peer path actually enforces rule 23, not just the unit-tested `perform_handshake`/`respond_to_handshake` API. Until 04-12 lands, a real game between two `run_agent()` processes completes its handshake on config alone (Phase-2 behavior, unchanged) — this is intentional staging, not a regression, and is exactly what plan 04-02's own scope (`files_modified: handshake_wire.py, handshake.py, config_hash.py` + their tests) allows without touching 04-12's files.
- **Plan 04-13** (`RULES-RESOLUTION-LANG.md`, phase triplet) can cite `HandshakeOutcome.SCENT_MISMATCH` and the shipped digest value (recorded above) directly.
- No blockers identified for the next wave.

## Known Stubs

None — every function shipped in this plan is fully wired and tested (protocol/config code, no UI or rendered data involved). The `local_scent_digest=None` staged-rollout default (see Deviations #1 and Next Phase Readiness) is a tested, intentional design for cross-plan sequencing, not a stub: it has explicit test coverage of both the skip path and the fully-opted-in path, and does not silently drop functionality anywhere within this plan's own scope.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-08*

## Self-Check: PASSED
