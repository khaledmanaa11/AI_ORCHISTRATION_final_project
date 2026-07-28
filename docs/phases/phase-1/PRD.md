# Phase 1 PRD — Base Logic

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-07-28

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); captures only what is
> specific to Phase 1. Numbers come from [PARAMETERS.md](../../PARAMETERS.md).

## Goal

Implement the pure game engine: 7×7 grid board model, orthogonal movement,
barrier quota enforcement, and all three capture types with scoring.

## Requirements covered

| REQ-ID | Description |
|--------|-------------|
| BASE-01 | 7×7 grid; cop starts (0,0); thief starts (3,3); orthogonal movement only; diagonal always rejected |
| BASE-02 | Barrier quota (14 minimum, from PARAMETERS Table 15); over-quota placement rejected without consuming quota |
| BASE-03 | Capture type 1: cop moves onto the thief's cell (coordinate overlap) |
| BASE-04 | Capture type 2: cop places a barrier on the thief's current cell |
| BASE-05 | Capture type 3: thief has no legal move at the start of its turn |
| BASE-06 | Survival end condition: thief reaches survival_threshold (35) turns uncaptured |
| BASE-07 | Scoring table: CAPTURE 20/5, SURVIVAL 5/10, TIE 2/2, TECHNICAL_LOSS 0/0 (all from config) |
| BASE-08 | Config loader loads typed GameParams; raises at load time on missing key or wrong type |
| QUAL-01 | All business logic behind the SDK layer (src/pursuit/sdk/engine.py); thin shells only |
| QUAL-06 | uv-only workflow; pyproject.toml as single source of dependency truth; versioning at 1.00 |

## Acceptance criteria (= §10.4 milestone gate)

1. **GATE-1 — Legal turn sequence:** A legal cop-then-thief turn sequence runs without
   error via `engine.apply_cop_action` + `engine.apply_thief_move`; game continues
   (`Outcome` is `None`) when no capture condition is met
   (`test_game_loop.py::test_legal_turn_sequence`).

2. **GATE-2 — Barrier quota enforcement:** A barrier placement attempted when
   `barriers_placed >= barrier_quota` is rejected: the barrier does not appear in
   `state.barriers` and `barriers_placed` is unchanged
   (`test_game_loop.py::test_barrier_quota_gate`).

3. **GATE-3 — All capture types:** All three capture types each yield `Outcome.CAPTURE`
   when routed through the engine facade:
   - BASE-03: cop's cell == thief's cell (coordinate overlap)
   - BASE-04: barrier placed on thief's cell
   - BASE-05: thief has no legal move (own cell in barriers, STAY blocked)
   (`test_game_loop.py::test_all_capture_types`).

## In scope / Out of scope (this phase)

- **In:** Game engine modules (board, barrier, capture, outcome, SDK facade, config
  loader), project scaffolding (uv project, pyproject.toml, config dirs, version.py),
  unit + integration tests for all engine modules, per-phase documentation triplet,
  root docs/TODO.md update.

- **Out:** Networking/FastMCP (Phase 2), AI/RL/strategy (Phase 3), language/scent
  (Phase 4), cloud/tunneling (Phase 5), cryptography/commit-reveal (Phase 6),
  GUI/reporting (Phase 7), submission/league (Phase 8). No adjacency-restricted
  barrier placement (requires undocumented parameter), no tie-aggregation function
  (Phase 8), no technical-loss production path (Phase 6–7).

## Dependencies

- Depends on: none (first code phase; greenfield project scaffold)
- External: `pytest`, `pytest-cov`, `ruff` (dev-only via `uv`)

## Success metrics & test scenarios

- `test_game_loop.py::test_legal_turn_sequence` passes (GATE-1)
- `test_game_loop.py::test_barrier_quota_gate` passes (GATE-2)
- `test_game_loop.py::test_all_capture_types` passes (GATE-3)
- `uv run pytest --cov=pursuit` — full unit suite green with ≥85% coverage
- `uv run ruff check .` — 0 violations across entire repo
- `bash scripts/check_line_limit.sh` — all source files ≤150 lines
