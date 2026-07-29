---
phase: 02-fastmcp-infrastructure
plan: "08"
subsystem: network
tags: [fastmcp, mcp, handshake, config-digest, state-machine, net-03, net-09, tdd]

# Dependency graph
requires:
  - phase: 02-fastmcp-infrastructure (02-02)
    provides: Envelope/EnvelopeKey/MessageType, config_digest/digests_match (canonical-JSON SHA-256)
  - phase: 02-fastmcp-infrastructure (02-03)
    provides: State/TurnStateMachine/TransitionReporter/TransitionSeverity, ALLOWED_TRANSITIONS
  - phase: 02-fastmcp-infrastructure (02-06)
    provides: register_tools/build_server with the handshake_handler seam, (turn, sender, payload) wire signature
provides:
  - "src/pursuit/network/handshake.py -- perform_handshake (outbound) and respond_to_handshake (inbound): D-08 connectivity proof + config-digest exchange in one call, D-15 abort before move 1 on mismatch; HandshakeOutcome/HandshakeResult/HandshakeCaller"
  - "src/pursuit/network/handshake_wire.py -- HANDSHAKE_TOOL/HANDSHAKE_TURN/HandshakeKey/build_offer/make_client_caller (wire adapter, split at the 150-line gate), re-exported verbatim from handshake.py"
affects: [02-09, verify-work-phase-2]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_evaluate() shared decode-then-compare helper collapses perform_handshake's and respond_to_handshake's digest-comparison paths into one call site (QUAL-02) -- the two directions cannot diverge in evidence or escalation policy"
    - "_result()/_abort() shared HandshakeResult/escalation constructors: one shape, one escalation sequence, reused by every return path"
    - "Policy-vs-wire file split: handshake.py holds perform_handshake/respond_to_handshake/_abort/_evaluate (the D-08/D-15 decision logic); handshake_wire.py holds the envelope-shape/fastmcp.Client adapter -- mirrors 02-07's verdict.py/deadline.py split"

key-files:
  created: [src/pursuit/network/handshake.py, src/pursuit/network/handshake_wire.py, tests/unit/test_handshake_abort.py, tests/unit/test_handshake_client.py]
  modified: [tests/unit/test_handshake.py]

key-decisions:
  - "handshake_wire.py split was REQUIRED, not optional: a single-file draft (with the plan's own function/field layout) measured 247 code lines even after full docstring compaction, and after moving build_offer/make_client_caller out and extracting the _evaluate/_result/_abort helpers to kill duplication, still needed the split to reach 144. Constants (HANDSHAKE_TOOL, HANDSHAKE_TURN, HandshakeKey) moved to handshake_wire.py ALONGSIDE build_offer/make_client_caller rather than staying in handshake.py as the plan's <interfaces> block shows -- build_offer needs HANDSHAKE_TURN and HandshakeKey, and having handshake.py import build_offer FROM handshake_wire.py while handshake_wire.py imported those constants FROM handshake.py would be a genuine circular import (not just an ordering nuisance: ruff's import-sorter would hoist the constants above the classes that a same-file layout requires, and there is no fix that keeps both directions of a real cross-module cycle safe). handshake_wire.py is therefore fully self-contained (depends only on 02-02's envelope.py), and handshake.py imports all five wire names from it -- the dependency is one-directional. Practical effect on the must_haves prose ('handshake.py contains exactly one numeric literal, HANDSHAKE_TURN = 0'): the AST audit script itself only forbids literals OTHER than 0 (`n.value not in (0,)`), so handshake.py now correctly reporting ZERO numeric literals still satisfies the automated gate (`forbidden numeric literals: []` -- an empty list is compliant whether it contains a permitted 0 or nothing at all); the module-layout choice is exactly the discretion CONTEXT.md delegates ('module layout, naming, and file split')."
  - "HANDSHAKE_TOOL/HANDSHAKE_TURN/make_client_caller are imported into handshake.py purely for re-export (never referenced by this file's own body -- HandshakeKey IS referenced, by _evaluate's payload lookup). Marked with inline `# noqa: F401` rather than an `__all__` list: an `__all__` block was tried first but cost ~12 lines for no functional gain over three targeted noqa comments, and this file is already fighting the line-count gate."
  - "The plan's own `<interfaces>` sketch shows perform_handshake decoding via a private `_decode_digest` step 3 then branching on `digests_match` in step 4, duplicated verbatim (per the sketch) inside respond_to_handshake. Implemented instead as a single shared `_evaluate(machine, reporter, local_digest, raw)` used by BOTH functions: this is a direct application of the plan's own duplication-audit instruction ('the evidence-line format appears ONCE... if there are two f-strings with the same shape, extract them') extended one level further, from just the mismatch string to the whole decode+compare+outcome sequence -- and was the single largest lever in reaching the 150-line gate honestly (vs. compressing prose)."
  - "The 02-03 precedent (design note 3): the 'if machine.state is not State.HANDSHAKE: return ... no peer contact' guard in both perform_handshake and respond_to_handshake maps to HandshakeOutcome.UNREACHABLE (remote_digest=None, detail naming the machine's actual state) -- the plan's pseudocode specifies the guard's SHAPE ('reflecting the machine's state with no peer contact') but not which of the four outcomes to use, and UNREACHABLE was chosen as the closest existing fit (no digest exchange attempted) rather than inventing a fifth outcome. This branch is not independently exercised by any named test (it only fires if perform_handshake/respond_to_handshake is called while the machine is already in MY_TURN/WAIT_OPPONENT/ERROR/GAME_OVER, which none of the eleven specified tests do) -- documented here per the plan's own instruction to record such adaptations, not silently."

patterns-established:
  - "make_client_caller's argument mapping against 02-06's landed tool: `{k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}` sent as call_tool(HANDSHAKE_TOOL, args) -- verified against tools.py's actual `async def handshake(turn: int, sender: str, payload: dict) -> dict` signature (confirmed via test_handshake_tool_name_matches_02_06 and test_agreed_over_in_memory_client, both passing over the real in-memory FastMCP transport). No adaptation was needed; the interfaces sketch matched what actually landed in 02-06."

# Metrics
duration: ~30min
completed: 2026-07-29
---

# Phase 02 Plan 08: Handshake Connectivity + Config-Digest Exchange Summary

**`perform_handshake`/`respond_to_handshake` prove reachability and exchange a SHA-256 config digest in one symmetric call, aborting BOTH peers' state machines to `State.ERROR` before move 1 the instant the digests disagree -- while an unreachable peer stays a distinct, retryable outcome that never touches `State.ERROR`.**

## Performance

- **Duration:** ~30 min
- **Tasks:** 3 (RED, GREEN, REFACTOR)
- **Files modified:** 5 (2 created in `src/`, 2 created + 1 modified in `tests/`)

## Accomplishments
- `src/pursuit/network/handshake.py` exports `HandshakeOutcome` (AGREED/CONFIG_MISMATCH/UNREACHABLE/MALFORMED_REPLY), `HandshakeResult` (with `.agreed`/`.aborted` properties), `HandshakeCaller`, and the two public entry points: `perform_handshake` (outbound, async, exactly one attempt -- no retry/timeout/sleep) and `respond_to_handshake` (inbound, sync, NET-03 symmetric, never raises).
- Matching digests reach `HandshakeOutcome.AGREED` with the machine sitting in `State.HANDSHAKE`, ready for 02-09 to choose `MY_TURN`/`WAIT_OPPONENT` by role; `machine.attempt(State.MY_TURN)` is then accepted, proving the path to move 1 is open (D-08).
- Mismatched digests escalate to `HandshakeOutcome.CONFIG_MISMATCH` / `State.ERROR` via a single `_abort()` helper that writes BOTH digests through the injected reporter (a legal `HANDSHAKE -> ERROR` transition is silent in 02-03, so this is the only place the D-15 evidence gets written) and names no side as wrong (rule 11, "truthful declarations").
- An unreachable peer (`McpError`, never `ToolError`) is a distinct `UNREACHABLE` outcome that leaves the machine out of `State.ERROR`; a retry on the SAME machine correctly falls through the duplicate-`(HANDSHAKE, HANDSHAKE)` `RECOVERABLE` transition to reach `AGREED` (design note 3), pinned by `test_retry_after_unreachable_still_agrees`.
- `respond_to_handshake` verifies independently, escalates its OWN machine on mismatch, and always returns its own digest even while aborting (never raises) -- `test_responder_replies_with_its_digest_even_on_mismatch` and `test_responder_aborts_symmetrically` pin both halves of NET-03 symmetry.
- All 12 named tests pass; full repo suite green (148 passed, 12 skipped, no regression); `handshake.py` coverage 94% (100% on `handshake_wire.py`, 95% combined) with all four `HandshakeOutcome` branches and both directions exercised; `ruff check .` and `scripts/check_line_limit.sh` both exit 0 repo-wide; the AST literal audit (only `0` in `handshake_wire.py`, none at all in `handshake.py`) and the forbidden-import audit (no `deadline`/`event_log`/`peer_runtime`/`tools`/`network_config` import) both print empty lists; the standalone D-15 behavioural script prints `D-15 audit OK`.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Fill test_handshake.py and create test_handshake_abort.py with failing assertions** - `f6f9183` (test)
2. **Task 2 GREEN: Implement handshake.py (+ pre-authorised handshake_wire.py split)** - `75fadaa` (feat)
3. **Task 3 REFACTOR: Full suite, coverage, static/behavioural audits** - no additional commit; every gate (coverage, whole-suite regression, ruff, line-limit, both static audits, the D-15 standalone script, decision-trace greps, `git status --porcelain` parallel-safety check) passed against the Task 2 commit with zero further code changes needed

## Files Created/Modified
- `src/pursuit/network/handshake.py` - `HandshakeOutcome`, `HandshakeResult`, `HandshakeCaller`, `_result`/`_mismatch_detail`/`_not_attempted`/`_abort`/`_evaluate` (private helpers), `perform_handshake`, `respond_to_handshake`; re-exports `HANDSHAKE_TOOL`/`HANDSHAKE_TURN`/`HandshakeKey`/`build_offer`/`make_client_caller` from `handshake_wire.py`
- `src/pursuit/network/handshake_wire.py` - `HANDSHAKE_TOOL`, `HANDSHAKE_TURN` (the module's one numeric literal), `HandshakeKey`, `build_offer`, `make_client_caller` (the `fastmcp.Client` adapter) -- self-contained, depends only on `envelope.py`
- `tests/unit/test_handshake.py` - replaced the four Wave-0 `pytest.skip` stubs with the fake-caller agreement/unreachable/retry suite (4 tests) plus the shared `FakeReporter`/`fake_caller`/`raising_caller`/`peer_reply` test doubles
- `tests/unit/test_handshake_client.py` - new file: the in-memory real-FastMCP-transport test and the 02-06 tool-name contract pin (2 tests) -- split from `test_handshake.py` at the 150-code-line gate
- `tests/unit/test_handshake_abort.py` - new file: the D-15 abort suite (6 tests) -- mismatch aborts before move 1, evidence records both digests non-accusatorily, responder replies with its own digest and aborts symmetrically, malformed replies are protocol violations, `ToolError` is never swallowed as unreachable

## Decisions Made
See `key-decisions` in the frontmatter for full detail on: why the `handshake_wire.py` split moved the constants too (avoiding a genuine circular import, not just a formatting nuisance); the `_evaluate()` consolidation that collapsed the plan's duplicated outbound/inbound decode-compare sketch into one call site; the `# noqa: F401` re-export choice over `__all__`; and the `_not_attempted` -> `UNREACHABLE` outcome mapping for the (untested-by-name) duplicate-handshake-attempt guard.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Single-file `handshake.py` exceeded the 150-code-line gate (247 lines on first draft)**
- **Found during:** Task 2, running `bash scripts/check_line_limit.sh` after the initial implementation (note: `check_line_limit.sh` uses `git ls-files`, so it silently skips untracked files -- the gate only fired once the file was `git add`-ed, which is worth flagging for future plans on this box: run `git add` before trusting a "clean" line-limit result)
- **Issue:** The full policy+wire implementation, even with compact docstrings, measured well over the limit; docstring compaction alone (matching handshake.py's every sentence to 02-07's "fewer, fuller lines" precedent) only reached ~190-205 lines.
- **Fix:** Applied the plan's own pre-authorised split (Task 3 "Split decision"): moved `build_offer`, `make_client_caller`, and the constants they depend on (`HANDSHAKE_TOOL`, `HANDSHAKE_TURN`, `HandshakeKey`) into `src/pursuit/network/handshake_wire.py`. Additionally extracted a shared `_evaluate()` helper (not explicitly named in the plan, but a direct application of its own QUAL-02 duplication-audit instruction) that collapsed the near-identical decode-then-compare logic duplicated across `perform_handshake` and `respond_to_handshake` in the plan's `<interfaces>` sketch into one call site. Combined, this reached 144 code lines with zero content dropped -- same branches, same evidence lines, same escalation policy, only less repeated code and less prose per docstring line.
- **Files modified:** `src/pursuit/network/handshake.py`, `src/pursuit/network/handshake_wire.py` (new)
- **Verification:** `bash scripts/check_line_limit.sh` exits 0 for both files; all 12 tests still pass; `ruff check .` exits 0; the AST literal and forbidden-import audits both print empty lists.
- **Committed in:** `75fadaa` (Task 2 GREEN)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking issue that prevented completing Task 2 as literally structured; the fix is the exact split the plan itself pre-authorised, plus one additional duplication-elimination refactor within the executor's delegated discretion over "module layout... and test structure")
**Impact on plan:** No change to the D-08/D-15/NET-03/NET-09 decision logic, evidence format, or escalation policy -- only to which file each piece of policy-neutral code lives in, and how many times the decode-compare shape is written out. No scope creep.

## Issues Encountered
- The line-limit gate's `git ls-files`-based file discovery silently skips untracked files, which produced a false "exit 0" the first time `check_line_limit.sh` ran against the freshly-created (not yet `git add`-ed) `handshake.py` -- the real 247-line violation only surfaced once the file was staged, at commit time via the pre-commit hook. No repo change made; documented here so a future plan on this box stages files before trusting an early line-limit check.
- No other issues; both GREEN and REFACTOR gates passed cleanly (after the split) with zero test failures and coverage comfortably above the 85% floor.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `perform_handshake`/`respond_to_handshake`/`HandshakeOutcome`/`HandshakeResult`/`HandshakeCaller`/`HANDSHAKE_TOOL`/`HANDSHAKE_TURN`/`HandshakeKey`/`build_offer`/`make_client_caller` are all in place with the exact three-kwarg `(turn, sender, payload) -> dict` responder shape commit 93bccbf already anticipated -- 02-09 can bind `respond_to_handshake` directly as the `handshake_handler` passed to `build_server`/`register_tools` via `make_handshake_responder()`, and wrap `make_client_caller(client)` in 02-07's `call_with_retry` for the outbound side.
- No blockers. `git status --porcelain src/pursuit/network/` is empty (all of this plan's files committed); the only pre-existing, unrelated changes in the working tree are `docs/KHALED_PERSONAL_PLAN.md` and the untracked `.claude/`/`.codex/` directories that predate this session.
- Carried forward from 02-07: the Phase-2 doc triplet (`docs/phases/phase-2/TODO.md`) still needs its 02-07 and 02-08 rows ticked, plus 02-09/02-10 as those land, with the full sweep (and root `docs/TODO.md`) at `/gsd:verify-work 2` time.

## Self-Check: PASSED

- FOUND: `src/pursuit/network/handshake.py`
- FOUND: `src/pursuit/network/handshake_wire.py`
- FOUND: `tests/unit/test_handshake_abort.py`
- FOUND: `tests/unit/test_handshake_client.py`
- FOUND: commit `f6f9183` (Task 1 RED)
- FOUND: commit `75fadaa` (Task 2 GREEN)

---
*Phase: 02-fastmcp-infrastructure*
*Completed: 2026-07-29*
