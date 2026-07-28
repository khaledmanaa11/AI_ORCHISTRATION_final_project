# Phase 1 PRD — Base Logic

**Version:** 1.00 · **Status:** ◐ approved · **Updated:** 2026-07-28

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); captures only what is
> specific to Phase 1. Numbers come from [PARAMETERS.md](../../PARAMETERS.md).

## Goal

Deliver the pure game engine: 7x7 grid with orthogonal movement, barrier quota enforcement,
capture/end-condition detection, and the full scoring table — all numeric values loaded from
game_params.json with no hardcoded values in source.

## Requirements covered

- BASE-01: Orthogonal movement (4 directions + stay); diagonal always rejected
- BASE-02: Barrier placement with quota enforcement (quota from PARAMETERS Table 15)
- BASE-03: Cop-on-thief capture
- BASE-04: Barrier-on-thief capture
- BASE-05: No-legal-move capture; 1+ open neighbor means no capture
- BASE-06: Survival at move_ceiling turns without capture
- BASE-07: Correct scores for CAPTURE (20/5) and SURVIVAL (5/10) from scoring table
- BASE-08: Config loader: loads typed GameParams; raises at load time on missing key or wrong type
- QUAL-01: All business logic behind the SDK layer; thin shells only
- QUAL-06: uv-only workflow; pyproject.toml as single source of dependency truth

## Acceptance criteria (= §10.4 milestone gate)

1. `uv run pytest tests/unit/ -x -q` exits 0 — all unit tests pass
2. `uv run pytest --cov=pursuit --cov-report=term-missing` shows coverage >= 85% for all modules in this phase
3. `uv run ruff check .` exits 0 — zero lint violations across repo
4. `bash scripts/check_line_limit.sh` passes — all files <= 150 code lines
5. `grep -rn "[0-9]" src/pursuit/constants.py` finds only Direction tuple components (-1, 0, 1)
6. GameState frozen: attempting attribute assignment raises FrozenInstanceError
7. `uv run pytest tests/integration/test_game_loop.py -x` passes (end-to-end game loop, Plan 01-04)

## In scope / Out of scope (this phase)

- **In:** Grid model, orthogonal movement, barrier placement + quota, all three capture types, end-condition detection, scoring, config loader, SDK facade (plan 01-04)
- **Out:** FastMCP networking, Q-learning/RL strategy, language hints, scent/pheromones, cryptography, reporting/GUI, league aggregation

## Dependencies

- Depends on: None (this is Phase 1 — greenfield)
- External: pytest, pytest-cov, ruff (all via uv dev dependencies)

## Success metrics and test scenarios

- test_config.py: 6 tests covering happy load, missing key, wrong type, int check
- test_board.py: 7 tests covering orthogonal, diagonal rejection, stay, OOB, barrier, immutability
- test_barrier.py: barrier quota enforcement tests (plan 01-02)
- test_capture.py: all 3 capture types + survival + scoring (plan 01-03)
- test_sdk_engine.py: SDK facade integration (plan 01-04)
