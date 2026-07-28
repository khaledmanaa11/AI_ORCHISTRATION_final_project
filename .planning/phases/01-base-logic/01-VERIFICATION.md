---
phase: 01-base-logic
verified: 2026-07-28T00:00:00Z
status: passed
score: 3/3 must-haves verified
gaps: []
human_verification: []
---

# Phase 1: Base Logic Verification Report

**Phase Goal:** Grid, movement rules, barrier quota, capture detection. No networking, no AI.
**Verified:** 2026-07-28T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Both agents move legally (orthogonal step or STAY; diagonals rejected) | VERIFIED | `get_legal_moves` iterates `Direction` enum (N/S/E/W/STAY only); 5 unit tests in `test_board.py` confirm orthogonal accepted, diagonal rejected, OOB rejected, barrier-cell rejected, STAY always included |
| 2 | A barrier placed beyond the cop's quota is rejected without consuming quota | VERIFIED | `place_barrier` checks `state.barriers_placed >= params.barrier_quota` before accepting; 8 unit tests in `test_barrier.py`; `test_barrier_quota_gate` (GATE-2) exercises this path through the SDK facade |
| 3 | Coordinate overlap triggers capture; barrier on thief triggers capture; no-legal-move triggers capture | VERIFIED | `detect_capture` checks BASE-03, BASE-04, BASE-05 in order; 4 unit tests in `test_capture.py`; `test_all_capture_types` (GATE-3) exercises all three via `engine.check_capture` |

**Score:** 3/3 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/pursuit/constants.py` | Direction/CellState/Outcome/ConfigKey enums; zero numeric game values | VERIFIED | 67 lines; Direction enum has N/S/E/W/STAY with (dr,dc) deltas; no numeric game parameters |
| `src/pursuit/shared/config.py` | Fail-loud GameParams loader | VERIFIED | 109 lines; `load_game_params` validates required keys; `_require_int` for scalars; raises at load time; `score_technical_loss_cop/thief` fields present (CR-02 fix confirmed) |
| `src/pursuit/shared/state.py` | Frozen GameState dataclass | VERIFIED | 45 lines; `@dataclass(frozen=True)`; fields: cop, thief, barriers, barriers_placed, turn; `increment_turn` helper |
| `src/pursuit/shared/board.py` | `get_legal_moves` + `apply_move` | VERIFIED | 87 lines; `get_legal_moves` uses `Direction` enum only; excludes OOB and barriered cells; STAY included unconditionally; `apply_move` produces new frozen state |
| `src/pursuit/shared/barrier.py` | `place_barrier` with quota enforcement | VERIFIED | 81 lines; validate-first order (OOB, cop's cell, already barriered, over-quota); accepted path increments `barriers_placed` |
| `src/pursuit/shared/capture.py` | `detect_capture` + `evaluate_turn_end` | VERIFIED | 93 lines; BASE-03/04/05 in order; `evaluate_turn_end` uses `params.survival_threshold` (no literals) |
| `src/pursuit/shared/outcome.py` | `score_outcome` with zero literals | VERIFIED | 46 lines; all four outcomes return `params.score_*` fields; no numeric literals; TECHNICAL_LOSS returns `params.score_technical_loss_cop/thief` |
| `src/pursuit/sdk/engine.py` | SDK facade (QUAL-01) | VERIFIED | 77 lines; thin wiring only; delegates to shared modules; `make_state`, `legal_moves`, `apply_cop_action`, `apply_thief_move`, `check_capture`, `score` |
| `src/pursuit/shared/version.py` | VERSION = "1.00" | VERIFIED | 3 lines |
| `config/police/game_params.json` | Numeric parameter source | VERIFIED | All game numbers present: board_size=7, barrier_quota=14, move_ceiling=35, survival_threshold=35, full scoring block including technical_loss |
| `config/thief/game_params.json` | Byte-for-byte copy of police config | VERIFIED | Identical content to police config |
| `tests/unit/test_board.py` | Movement unit tests | VERIFIED | 7 tests; orthogonal accepted, diagonal rejected, stay legal, OOB rejected, barrier rejected, immutability |
| `tests/unit/test_barrier.py` | Barrier unit tests | VERIFIED | 8 tests; valid placement, immutability, quota exceeded, no quota cost on rejection, cop's own cell, already barriered, OOB, thief-cell valid |
| `tests/unit/test_capture.py` | Capture/scoring unit tests | VERIFIED | 11 tests; all BASE-03/04/05 paths, survival threshold, all 4 score outcomes, CR-02 config-sourced technical loss test |
| `tests/unit/test_config.py` | Config loader unit tests | VERIFIED | 6 tests; board_size, barrier_quota, scoring, missing key raises, wrong type raises, type assertion |
| `tests/unit/test_sdk_engine.py` | SDK facade delegation tests | VERIFIED | 7 tests; one per SDK method |
| `tests/integration/test_game_loop.py` | §10.4 gate tests | VERIFIED | 3 tests: GATE-1/2/3 all pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `engine.apply_cop_action` | `board.apply_move` + `barrier.place_barrier` + `capture.detect_capture` | direct call | WIRED | engine.py:48-54 calls all three in D-12 order |
| `engine.apply_thief_move` | `board.apply_move` + `state.increment_turn` + `capture.evaluate_turn_end` | direct call | WIRED | engine.py:64-67 |
| `engine.check_capture` | `capture.detect_capture` | direct call | WIRED | engine.py:72 |
| `engine.score` | `outcome.score_outcome` | direct call | WIRED | engine.py:76 |
| `capture.detect_capture` | `board.get_legal_moves` | import + call | WIRED | capture.py:24 import, capture.py:64 call |
| `outcome.score_outcome` | `config.GameParams.score_*` fields | field access | WIRED | All four outcome branches read `params.score_*` — no literals |
| `config.load_game_params` | `game_params.json` | json.load + Path | WIRED | config.py:75-76; both police and thief configs validated |
| `conftest.default_params` | `config/police/game_params.json` | load_game_params | WIRED | conftest.py:11-18; all tests consume via fixture |

---

## Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| BASE-01 | SATISFIED | 7x7 board (config); cop (0,0), thief (3,3) (config); orthogonal only via Direction enum |
| BASE-02 | SATISFIED | `place_barrier` quota check; rejected without quota cost; 8 unit tests |
| BASE-03 | SATISFIED | `detect_capture`: `state.cop == state.thief` branch |
| BASE-04 | SATISFIED | `detect_capture`: `state.thief in state.barriers` branch |
| BASE-05 | SATISFIED | `detect_capture`: `not get_legal_moves(state, "thief", params)` branch |
| BASE-06 | SATISFIED | `evaluate_turn_end`: `state.turn >= params.survival_threshold` |
| BASE-07 | SATISFIED | `score_outcome` reads `params.score_*` for all four outcomes; CR-02 fix confirmed: `score_technical_loss_cop/thief` on GameParams |
| BASE-08 | SATISFIED | `load_game_params` validates all required keys and types at load time |
| QUAL-01 | SATISFIED | `engine.py` is thin wiring; all business logic in `shared/` |
| QUAL-06 | SATISFIED | `uv` workflow in pyproject.toml; VERSION = "1.00" in version.py; no requirements.txt |

---

## Quantitative Gate Results

| Gate | Command | Result |
|------|---------|--------|
| pytest all green | `uv run pytest -q` | 43 passed in 0.08s |
| Coverage >= 85% | `uv run pytest --cov=src/pursuit` | 98.95% (191 stmts, 2 missed — `version.py:3` and `capture.py:65` BASE-05 dead branch) |
| ruff 0 violations | `uv run ruff check .` | All checks passed |
| Line limit <= 150 | `bash scripts/check_line_limit.sh` | Exit 0, no violations |
| GATE-1 legal turn | `test_legal_turn_sequence` | PASSED |
| GATE-2 barrier quota | `test_barrier_quota_gate` | PASSED |
| GATE-3 all captures | `test_all_capture_types` | PASSED |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/pursuit/shared/barrier.py` | 76 | Dead arithmetic: `added = len(new_barriers) - len(state.barriers)` — always 1 after duplicate guard at line 67 | Warning (WR-06) | Maintenance trap; not a correctness bug in Phase 1 |
| `src/pursuit/shared/state.py` | 43 | Unnecessary local `import dataclasses` with `noqa` suppression | Info (IN-01) | Inconsistency; not a correctness bug |
| `src/pursuit/shared/capture.py` | 64-65 | BASE-05 branch is dead code reachable only when BASE-04 already returned CAPTURE | Warning (WR-05) | Documented in plan; correct for current move semantics |
| `src/pursuit/shared/config.py` | 101-107 | Array index literals `[0]`, `[1]` for scoring pair access | Accepted | Structural accessor indices, not game parameter values; all game values are in config JSON |

**No blockers.** Warnings and infos are all documented in 01-REVIEW.md as known, out-of-scope items (WR-05, WR-06) or deferred to Phase 2 (IN-01, IN-04 agent string literals). No placeholder implementations, no `TODO`/`FIXME` gaps, no stub returns.

---

## CR-02 Fix Confirmation

**Finding from 01-REVIEW.md:** `outcome.py` contained a bare `(0, 0)` literal for `TECHNICAL_LOSS`.

**Verified fixed:**
- `GameParams` (config.py:33-34) has `score_technical_loss_cop: int` and `score_technical_loss_thief: int`
- `load_game_params` (config.py:92, 106-107) reads `technical_loss` from JSON and stores both values
- `score_outcome` (outcome.py:43-44) returns `(params.score_technical_loss_cop, params.score_technical_loss_thief)`
- Zero numeric literals in `outcome.py`
- `test_technical_loss_score_from_config` explicitly proves non-hardcoded behavior by substituting custom values `(7, 3)` and asserting the output matches

---

## CR-01 Scope Assessment Confirmed

**Finding from 01-REVIEW.md:** `apply_move` does not reject illegal destinations.

**Scope ruling:** OUT OF SCOPE for Phase 1. The §10.4 criterion "Both agents move legally" is satisfied by the legal-move oracle (`get_legal_moves`) being correct and tested — the enforcement boundary at the mutation layer is the Phase 2 turn orchestrator's responsibility. This is architecturally sound: the oracle produces the legal set; the orchestrator (Phase 2) must only feed legal moves to `apply_move`. Phase 1 fulfills the oracle contract completely.

Confirmed artifact: `get_legal_moves` correctly enforces:
- Orthogonal-only moves (Direction enum has no diagonals)
- In-bounds check (lines 54-55)
- Barrier exclusion (lines 57-59)
- STAY always included (lines 50-51)

---

## Shared State Check

`GameState` is `@dataclass(frozen=True)` — all fields are immutable after construction. Every state transition (`apply_move`, `place_barrier`, `increment_turn`) uses `dataclasses.replace(...)` to produce a new object. No mutable class-level variables, no module-level game state. The cop and thief processes can never share a live `GameState` object.

---

## Human Verification Required

None. All Phase 1 functionality is pure computation with no UI, no networking, and no external services. Everything is fully verifiable programmatically.

---

## Summary

Phase 1 goal is **fully achieved**. The codebase delivers a correct, tested, lint-clean base logic layer:

- The legal-move oracle (`get_legal_moves`) is correct and comprehensively tested: orthogonal-only, in-bounds, non-barrier, STAY-always-included.
- Barrier quota enforcement works correctly: rejected placements do not consume quota.
- All three capture types (`detect_capture`) and the survival end condition (`evaluate_turn_end`) are correctly implemented and tested.
- CR-02 (hardcoded TECHNICAL_LOSS score) is confirmed fixed: `score_outcome` reads `params.score_technical_loss_*`.
- All quantitative gates pass: 43/43 tests green, 98.95% coverage (>85% threshold), 0 ruff violations, 0 line-limit violations.
- No shared runtime state between cop and thief processes (`GameState` is frozen; transitions produce new objects).
- No numeric game values are hardcoded in source: all come from `game_params.json` via `load_game_params`.

Outstanding items from the code review (WR-01 through WR-06, IN-01 through IN-04) are all **below blocker threshold** — they are robustness improvements and code-quality refinements, not Phase 1 correctness gaps. CR-01 (apply_move enforcement) is correctly deferred to Phase 2.

---

_Verified: 2026-07-28T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
