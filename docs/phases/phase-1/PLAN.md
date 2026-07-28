# Phase 1 PLAN — Base Logic

**Version:** 1.00 · **Updated:** 2026-07-28

> Phase-scoped architecture. Inherits the project [PLAN.md](../../PLAN.md); captures only
> the design specific to Phase 1.

## Components & files

| Module / file (≤150 lines each) | Responsibility |
|---|---|
| `src/pursuit/constants.py` | Direction/CellState/Outcome/ConfigKey enums; zero numeric game values (D-07) |
| `src/pursuit/shared/config.py` | `load_game_params(path)` → `GameParams`; fail-loud validation at startup (D-05) |
| `src/pursuit/shared/state.py` | `GameState` frozen dataclass (cop, thief, barriers, barriers_placed, turn); `increment_turn` helper (D-12) |
| `src/pursuit/shared/board.py` | `get_legal_moves(state, agent, params)`; `apply_move(state, agent, dest)` (D-08, D-13) |
| `src/pursuit/shared/barrier.py` | `place_barrier(state, cell, params)` → `GameState`; validate-first order (D-10, D-11) |
| `src/pursuit/shared/capture.py` | `detect_capture(state, params)`; `evaluate_turn_end(state, params)` (D-12, D-14, D-15) |
| `src/pursuit/shared/outcome.py` | `score_outcome(outcome, params)` → `tuple[int, int]`; all values from params (D-14) |
| `src/pursuit/sdk/engine.py` | SDK facade: `make_state`, `legal_moves`, `apply_cop_action`, `apply_thief_move`, `check_capture`, `score` (QUAL-01) |
| `src/pursuit/shared/version.py` | `VERSION = "1.00"` |
| `config/police/game_params.json` | Numeric truth root; duplicated byte-for-byte in `config/thief/` (D-05, D-06) |

## Interfaces & contracts

```python
# engine.py — sole public entry point for Phase 2+
make_state(params: GameParams) -> GameState
legal_moves(state: GameState, agent: str, params: GameParams) -> list[tuple[int, int]]
apply_cop_action(state, move_to, barrier_at, params) -> tuple[GameState, Outcome | None]
apply_thief_move(state: GameState, move_to: tuple, params: GameParams) -> tuple[GameState, Outcome | None]
check_capture(state: GameState, params: GameParams) -> Outcome | None
score(outcome: Outcome, params: GameParams) -> tuple[int, int]

# shared/state.py
@dataclass(frozen=True)
class GameState:
    cop: tuple[int, int]; thief: tuple[int, int]
    barriers: frozenset; barriers_placed: int; turn: int

def increment_turn(state: GameState) -> GameState

# shared/board.py
def get_legal_moves(state, agent, params) -> list[tuple[int, int]]
def apply_move(state, agent, dest) -> GameState

# shared/barrier.py
def place_barrier(state, cell, params) -> GameState  # returns original on rejection

# shared/capture.py
def detect_capture(state, params) -> Outcome | None
def evaluate_turn_end(state, params) -> Outcome | None

# shared/outcome.py
def score_outcome(outcome, params) -> tuple[int, int]
```

## Phase ADRs

| # | Decision | Rationale | Alternative / trade-off |
|---|----------|-----------|-------------------------|
| P1-1 | `GameState` as frozen dataclass (immutable snapshot) | Prevents shared-mutable-state disqualification (rule 2); enables replay; `dataclasses.replace` for transitions | Mutable object: rejected — shared state risk between cop/thief at Phase 8 split |
| P1-2 | All numeric params in `game_params.json`, not `constants.py` | Appendix F §2 rule 1 (all values in config); rule 11 (byte-for-byte crypto lock in Phase 6); values must be per-game-attachable | `constants.py` values: rejected — cannot be cryptographically locked or per-game-verified |

## Test plan (TDD)

- **Unit:** `tests/unit/` — one file per module; happy path + error case per public function;
  all Phase 1 modules are pure computation (no external service mocking needed).
  Files: `test_config.py`, `test_board.py`, `test_barrier.py`, `test_capture.py`, `test_sdk_engine.py`.
- **Integration:** `tests/integration/test_game_loop.py` — three §10.4 gate tests:
  `test_legal_turn_sequence` (GATE-1), `test_barrier_quota_gate` (GATE-2),
  `test_all_capture_types` (GATE-3).
- **Coverage target:** ≥85% (`fail_under=85` in pyproject.toml).

## Per-mechanism PRDs written this phase

None — Phase 1 is foundational scaffolding with no single algorithmic mechanism complex
enough to warrant a dedicated `docs/PRD_<mechanism>.md`. Per-mechanism PRDs begin at
Phase 2 (FastMCP protocol) and Phase 3 (RL strategy).
