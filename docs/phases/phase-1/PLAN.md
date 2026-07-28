# Phase 1 PLAN — Base Logic

**Version:** 1.00 · **Updated:** 2026-07-28

> Phase-scoped architecture. Inherits the project [PLAN.md](../../PLAN.md); captures only
> the design specific to Phase 1.

## Components and files

| Module / file (<=150 lines each) | Responsibility |
|---|---|
| `src/pursuit/constants.py` | Direction(Enum), CellState(Enum), Outcome(Enum), ConfigKey class; zero numeric game values (D-07) |
| `src/pursuit/shared/config.py` | load_game_params(path) -> GameParams; fail-loud validation (D-05) |
| `src/pursuit/shared/state.py` | GameState @dataclass(frozen=True) — immutable snapshot (D-12) |
| `src/pursuit/shared/board.py` | get_legal_moves + apply_move pure functions (D-08, D-13) |
| `src/pursuit/shared/barrier.py` | place_barrier; quota enforcement; capture-on-placement (D-10, D-11) |
| `src/pursuit/shared/capture.py` | detect_capture; compute_score; all three capture types (D-14, D-15) |
| `src/pursuit/sdk/engine.py` | SDK facade: one-turn step, full game loop, result aggregation (QUAL-01) |
| `config/police/game_params.json` | Numeric truth root; duplicated in config/thief/ (D-05, D-06) |
| `tests/unit/test_config.py` | 6 tests for BASE-08 |
| `tests/unit/test_board.py` | 7 tests for BASE-01 |
| `tests/unit/test_barrier.py` | Tests for BASE-02 |
| `tests/unit/test_capture.py` | Tests for BASE-03..BASE-07 |
| `tests/unit/test_sdk_engine.py` | Tests for QUAL-01 |
| `tests/integration/test_game_loop.py` | Integration tests for §10.4 gate |

## Interfaces and contracts

```python
# config.py
load_game_params(path: Path | str) -> GameParams

# state.py
@dataclass(frozen=True)
class GameState:
    cop: tuple[int, int]
    thief: tuple[int, int]
    barriers: frozenset
    barriers_placed: int
    turn: int

# board.py
get_legal_moves(state: GameState, agent: str, params: GameParams) -> list[tuple]
apply_move(state: GameState, agent: str, dest: tuple) -> GameState

# barrier.py (plan 01-02)
place_barrier(state: GameState, cell: tuple, params: GameParams) -> tuple[GameState, bool]

# capture.py (plan 01-03)
detect_capture(state: GameState, params: GameParams) -> Outcome | None
compute_score(outcome: Outcome, params: GameParams) -> tuple[int, int]
```

## Phase ADRs

| # | Decision | Rationale | Alternative / trade-off |
|---|----------|-----------|-------------------------|
| D-05 | All numeric game params in game_params.json | Appendix F §2 rule 1 requires config file; Phase 6 crypto lock needs a file | Hardcoded constants would fail the crypto lock and be unverifiable per game |
| D-07 | constants.py/Enum hold only structural non-numeric values | Complements D-05; Direction deltas (-1,0,1) are structural, not game parameters | Could put everything in config, but structural values like enum labels are code |
| D-08 | Barriered cell is impassable (get_legal_moves excludes it) | Prerequisite for BASE-05 "no legal move" capture to be reachable | Traversable barriers would require a different game mechanic |
| D-12 | GameState is frozen dataclass; immutable snapshot pattern | Project rule 2 — no shared mutable state between cop and thief | Mutable state would risk information leakage at Phase 8 repo split |
| D-13 | STAY (current position) always in legal moves | Agent can always pass even if surrounded by barriers; prevents impossible stuck states | Without STAY, surrounded agent would have no moves, which would always trigger capture |

## Test plan (TDD)

- Unit: all src modules covered with happy path and error cases; no external service mocking needed (Phase 1 is pure computation)
- Integration: `tests/integration/test_game_loop.py` — full single-game loop exercising all three capture types and survival (plan 01-04)
- Coverage target: >= 85% (`fail_under=85`)
- TDD discipline: RED commit (failing tests) before GREEN commit (implementation)

## Per-mechanism PRDs written this phase

None — Phase 1 is foundational scaffolding. Per-mechanism PRDs will be needed from Phase 2 onward (FastMCP protocol, Q-learning strategy, commit-reveal).
