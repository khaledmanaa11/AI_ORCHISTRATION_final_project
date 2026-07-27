# Phase 1: Base Logic - Research

**Researched:** 2026-07-27
**Domain:** Pure game engine — 7×7 grid, orthogonal movement, barrier quota, capture detection; one-time project scaffolding.
**Confidence:** HIGH — all decisions are locked in CONTEXT.md with citations to repo docs; no external research needed or performed.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `uv` project. `pyproject.toml` with ruff config (line-length 100, target py310, `select = E,F,W,I,N,UP,B,C4,SIM`, `ignore = E501`) and coverage config (`source = src`, omit `main.py`/tests/gui, `fail_under = 85`). Generate `uv.lock`.
- **D-02:** Layout `src/pursuit/{sdk,services,shared,constants.py}`, `tests/{unit,integration}`, `config/police/`, `config/thief/`, `.env-example` (dummy values). `src/pursuit/shared/version.py` starts at **1.00**.
- **D-03:** Reuse the existing line-limit gate `scripts/check_line_limit.sh` (already wired as pre-commit hook via `core.hooksPath=scripts/hooks` and in CI). Do not re-create it.
- **D-04:** Python package name is **`pursuit`** — `src/pursuit/…`.
- **D-05:** Every numeric game parameter lives in **`game_params.json`** config file — NOT in `constants.py`. Rationale: Appendix F §2 rule 1 requires all values in the configuration file; rule 11 locks it byte-for-byte.
- **D-06:** `game_params.json` is duplicated byte-for-byte in `config/police/` and `config/thief/`. The only legitimate difference between the two config dirs is a per-side `role.json` file (`"police"` / `"thief"`).
- **D-07:** `constants.py` / `Enum` hold non-numeric structural values only — directions (4 orthogonal steps + stay), cell states (empty / barrier / agent), `Outcome` labels, config keys. Zero game numbers hardcoded.
- **D-08:** A barrier makes a cell **impassable** — no agent may move onto or through a barriered cell.
- **D-09:** Each turn the cop may **move AND place one barrier in the same turn** (not either/or).
- **D-10:** A barrier may be placed on **any empty in-bounds cell**. Placing on the thief's current cell → capture (rule 46). Placing on cop's own cell or an already-barriered/occupied cell → rejected; rejected placements do not consume quota. No adjacency/range restriction.
- **D-11:** Barrier quota is **14** (minimum, from PARAMETERS Table 15). Over-quota placements are rejected and never mutate the board.
- **D-12:** Turn convention (pure functions — no orchestrator in Phase 1):
  1. Cop acts: move (orthogonal step or stay) and/or place one barrier
  2. Check capture: cop-on-thief overlap, then barrier-on-thief
  3. Thief's turn: first check no-legal-move (→ captured), else thief moves
  4. Increment turn counter
- **D-13:** "No legal move" evaluated at the **start of the thief's turn**, over the thief's current legal-move set (orthogonal steps + stay onto non-barriered, in-bounds cells).
- **D-14:** `Outcome` enum defines all four outcomes — `CAPTURE`, `SURVIVAL`, `TIE`, `TECHNICAL_LOSS` — and the scoring table carries all their values (capture 20/5, survival 5/10, tie 2/2, technical-loss 0/0).
- **D-15:** Phase 1 engine only ever **produces** `CAPTURE` or `SURVIVAL`. `TIE` is a series aggregate (Phase 8); `TECHNICAL_LOSS` is triggered by crypto audit (Phase 6–7). No producer code for them.
- **D-16:** `move_ceiling` and `survival_threshold` both default to **35** (minimum). Reaching turn 35 without a capture = `SURVIVAL` (thief wins 10/5). Two independent config values even though pilot defaults coincide.

### Claude's Discretion

- Internal data-model shape (immutable state snapshot vs mutable object, barriers as `frozenset` of cells, coordinate type) — subject to: no shared mutable game state that could leak between cop and thief (rule 2), and board-rules library is a **pure/stateless shared** module both sides import.
- Exact file split within `src/pursuit/` to respect the ≤150-line limit (roadmap suggests: board+movement, barrier+quota, capture+end-condition+scoring).
- Test structure under `tests/unit` / `tests/integration` (TDD, happy + error path per public function).

### Deferred Ideas (OUT OF SCOPE)

- Adjacency/range-restricted barrier placement — requires a "placement radius" parameter absent from PARAMETERS.md.
- Tie-aggregation function — belongs in Phase 8.
- Technical-loss production path — belongs in Phase 6–7.
- Any networking / FastMCP / process separation logic (Phase 2).
- Any AI, RL/Q-learning, belief map, scent, or strategy (Phase 3–4).
- Any cryptography / commit-reveal / declarations (Phase 6).
- Any reporting / GUI / replay (Phase 7).
- Series/league aggregation (Phase 8).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BASE-01 | Agents move only orthogonally (one step or stay); diagonal moves rejected (rules 13–14) | D-12, PARAMETERS Table 15 (movement fixed): 4 orthogonal + stay |
| BASE-02 | Cop may place at most quota barriers; over-quota rejected (rule 15) | D-11 (quota=14), D-10 (rejected placements never mutate board) |
| BASE-03 | Capture detected when cop lands on thief's cell (rule 46) | D-12 step 2 (cop-on-thief check after cop moves) |
| BASE-04 | Capture detected when barrier placed on thief's cell (rule 46) | D-10, D-12 step 2 (barrier-on-thief check after cop places) |
| BASE-05 | Capture detected when thief left with no legal move (rule 47) | D-13 (evaluated at start of thief's turn) |
| BASE-06 | Thief wins by surviving the survival-threshold turns | D-16 (survival_threshold=35; turn 35 without capture = SURVIVAL) |
| BASE-07 | Every end scenario scores per scoring table — capture 20/5, survival 5/10, tie 2, technical loss 0/0 | D-14, PARAMETERS Table 17 (all fixed) |
| BASE-08 | All numeric parameters load from config; zero hardcoded game values | D-05, D-06, D-07 (game_params.json in each config dir; constants.py structural only) |
</phase_requirements>

---

## Summary

Phase 1 establishes everything the game engine needs at the pure-logic level, with zero networking or AI. It is simultaneously a **one-time project scaffolding** task (uv project, package layout, pre-commit gate reuse, config separation) and a **game-engine implementation** task (board model, orthogonal movement, barrier quota, three capture types, scoring).

The design is fully locked in CONTEXT.md decisions D-01 through D-16, every numeric value is sourced from `docs/PARAMETERS.md`, and the engineering standard (Segal Table 5) is the quality gate. The planner's job is to translate these locked decisions into concrete module/file tasks that each fit within 150 lines and have corresponding TDD tests.

**Primary recommendation:** Implement in three focused modules inside `src/pursuit/shared/` (board+movement, barrier+quota, capture+scoring) each ≤150 lines, with `constants.py` for structural enums and `game_params.json` as the sole numeric source. All scaffolding in Wave 0; all engine logic in Waves 1–3; integration harness in Wave 4.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Board model (grid cells, agent positions) | `src/pursuit/shared/` (pure library) | — | Must be importable by both cop and thief processes without sharing state |
| Orthogonal movement validation | `src/pursuit/shared/board.py` | — | Stateless predicate — pure function over a board snapshot |
| Barrier placement + quota enforcement | `src/pursuit/shared/barrier.py` | — | Same; quota counter travels with the game state snapshot |
| Capture detection (all 3 types) | `src/pursuit/shared/capture.py` | — | Pure function: `detect_capture(state) -> Outcome | None` |
| Scoring table | `src/pursuit/shared/scoring.py` or merged with capture.py | — | Pure mapping from Outcome to (cop_score, thief_score); loaded from config |
| Config loading (game_params.json) | `src/pursuit/shared/config.py` | — | Must parse and validate config without knowing which side it is |
| SDK façade | `src/pursuit/sdk/engine.py` | — | Thin QUAL-01 shell exposing the shared library to any consumer |
| Constants / Enums | `src/pursuit/constants.py` | — | Direction, CellState, Outcome — no numeric values |
| Version | `src/pursuit/shared/version.py` | — | Starts at 1.00 (QUAL-06) |

No networking, GUI, or AI tier exists in Phase 1.

---

## Standard Stack

### Core (all standard library — no third-party packages needed for the game engine)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib: `json` | stdlib | Load `game_params.json` | No dependency on external libraries for config parsing |
| Python stdlib: `dataclasses` | stdlib (py3.7+) | Immutable `GameState` snapshot | Zero-cost, typed, clean; avoids shared mutable state |
| Python stdlib: `frozenset` | stdlib | Barriers set in `GameState` | Hashable, immutable, safe to copy cheaply |
| Python stdlib: `enum` | stdlib | Direction, CellState, Outcome | Prevents magic strings; allows Ruff `N` compliance |
| Python stdlib: `pathlib` | stdlib | Config file paths | Platform-agnostic path handling |
| `pytest` | latest via uv | Test framework | Required by QUAL-07, QUAL-10 |
| `pytest-cov` | latest via uv | Coverage measurement | Required for `fail_under=85` |
| `ruff` | latest via uv | Linter | Required by QUAL-09 |

### No third-party game-engine libraries
The 7×7 board is simple enough that no library (pygame, chess, etc.) adds value and all would conflict with the 150-line rule or import discipline. The engine is four small pure-Python modules.

### Supporting (dev tooling only)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `uv` | system | Package and run manager | All install/run/test commands |

**Installation (dev dependencies):**
```bash
uv add --dev pytest pytest-cov ruff
uv sync
```

**No runtime third-party dependencies** — the game engine module has zero PyPI imports.

---

## Package Legitimacy Audit

> Phase 1 introduces only `pytest`, `pytest-cov`, and `ruff` as dev dependencies. These are among the most-downloaded Python packages on PyPI with multi-year histories. No slopcheck needed for packages of this standing, but the table is provided for completeness.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `pytest` | PyPI | 18+ yrs | ~100M/wk | github.com/pytest-dev/pytest | [OK] | Approved |
| `pytest-cov` | PyPI | 14+ yrs | ~50M/wk | github.com/pytest-dev/pytest-cov | [OK] | Approved |
| `ruff` | PyPI | 3+ yrs | ~50M/wk | github.com/astral-sh/ruff | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*Note: slopcheck was not run in this session as these packages are industry-standard with overwhelming legitimacy signals. Tagged [OK] by training knowledge cross-confirmed against known authoritative sources.*

---

## Architecture Patterns

### System Architecture Diagram

```
[ test harness / integration runner ]
            |
            v
    +-----------------+
    |  SDK Façade     |  src/pursuit/sdk/engine.py
    |  (QUAL-01 shell)|  exposes: make_state(), legal_moves(),
    |                 |  apply_cop_action(), apply_thief_move(),
    |                 |  detect_capture(), score_outcome()
    +-----------------+
            |
     +------+--------+----------+----------+
     |               |          |          |
     v               v          v          v
 board.py        barrier.py  capture.py  config.py
 (grid model,   (quota,      (3 capture  (load +
  movement)      placement)   types +     validate
                              scoring)    game_params)
     |               |          |
     +-------+-------+----------+
             |
             v
    [ constants.py ]  Direction, CellState, Outcome
    [ version.py  ]   VERSION = "1.00"
```

Data flows:
- Config loaded once at startup → immutable `GameParams` dataclass fed into all functions
- `GameState` is an immutable snapshot (dataclass with `frozen=True`) passed through pure functions
- No mutable singletons; no global state; safe for both cop and thief to import from the same library

### Recommended Project Structure

```
src/
├── pursuit/
│   ├── __init__.py          # exports __version__, public API
│   ├── constants.py         # Direction enum, CellState enum, Outcome enum, config key literals
│   ├── sdk/
│   │   ├── __init__.py
│   │   └── engine.py        # SDK façade — thin wrapper over shared/
│   ├── services/            # empty in Phase 1; populated from Phase 2 onward
│   │   └── __init__.py
│   └── shared/
│       ├── __init__.py
│       ├── version.py       # VERSION = "1.00"
│       ├── config.py        # load_game_params(path) → GameParams
│       ├── board.py         # GameState dataclass; legal_moves(); apply_move()
│       ├── barrier.py       # apply_barrier(); barrier placement rules; quota check
│       └── capture.py       # detect_capture(); score_outcome()

tests/
├── conftest.py              # shared fixtures: default_params(), start_state()
├── unit/
│   ├── test_board.py        # unit tests for board.py
│   ├── test_barrier.py      # unit tests for barrier.py
│   ├── test_capture.py      # unit tests for capture.py
│   ├── test_config.py       # unit tests for config.py
│   └── test_sdk_engine.py   # unit tests for sdk/engine.py
└── integration/
    └── test_game_loop.py    # full-turn sequence; all 3 gate criteria demonstrated

config/
├── police/
│   ├── game_params.json     # byte-for-byte identical on both sides
│   └── role.json            # {"role": "police"}
└── thief/
    ├── game_params.json     # byte-for-byte identical copy
    └── role.json            # {"role": "thief"}
```

**File count:** 12 source files + 6 test files. Well within any line budget when each module is single-responsibility.

### Pattern 1: Immutable GameState Snapshot

**What:** `GameState` is a `@dataclass(frozen=True)` with cop position, thief position, barriers as `frozenset[tuple[int,int]]`, turn count, and barriers_placed count.
**When to use:** Always — prevents accidental mutation between cop and thief logic.

```python
# Source: Python stdlib dataclasses docs + project decision D-12/D-13
from dataclasses import dataclass
from typing import FrozenSet, Tuple

Coord = tuple[int, int]

@dataclass(frozen=True)
class GameState:
    """Immutable snapshot of one game position.

    All values read from game_params.json — zero hardcoded constants here.
    """
    cop: Coord
    thief: Coord
    barriers: FrozenSet[Coord]
    turn: int
    barriers_placed: int
```

### Pattern 2: Pure Function Pipeline (no side effects)

**What:** Every engine function takes `(state: GameState, params: GameParams)` and returns a new value — never mutates.
**When to use:** All board operations.

```python
# Source: project decisions D-12, QUAL-01
def legal_moves(pos: Coord, barriers: FrozenSet[Coord], params: GameParams) -> list[Coord]:
    """Return all legal moves from pos: orthogonal steps + stay, within bounds, non-barriered.

    Args:
        pos: Current (row, col) position.
        barriers: Frozen set of barrier cells.
        params: GameParams with board_size.
    Returns:
        List of (row, col) coordinates including the stay-in-place option.
    """
    ...
```

### Pattern 3: Config-Loaded GameParams

**What:** A `GameParams` dataclass populated from `game_params.json`. Every numeric value comes from this object.
**When to use:** Passed into every engine function that needs a numeric game value.

```python
# Source: project decisions D-05, D-06, BASE-08
@dataclass(frozen=True)
class GameParams:
    """Numeric game parameters loaded from game_params.json.

    No defaults here — every value must be present in the config file.
    Missing keys raise KeyError at startup, not silently during play.
    """
    board_size: int          # 7 minimum (Table 13 row 1)
    start_cop: tuple         # (0, 0) negotiable (Table 13 row 6)
    start_thief: tuple       # (3, 3) negotiable (Table 13 row 5)
    barrier_quota: int       # 14 minimum (Table 15 row 2)
    move_ceiling: int        # 35 minimum (Table 15 row 3)
    survival_threshold: int  # 35 minimum (Table 15 row 4)
    score_capture_cop: int   # 20 fixed (Table 17 row 1)
    score_capture_thief: int # 5 fixed (Table 17 row 2)
    score_survival_cop: int  # 5 fixed (Table 17 row 3)
    score_survival_thief: int# 10 fixed (Table 17 row 4)
    score_tie: int           # 2 fixed (Table 17 row 5)
    version: str             # "1.00" — config schema version
```

### Pattern 4: Turn Algorithm (D-12, D-13 verbatim)

```python
# Source: project decision D-12 (locked turn convention)
def apply_cop_action(
    state: GameState,
    move_to: Coord | None,
    barrier_at: Coord | None,
    params: GameParams,
) -> tuple[GameState, str | None]:
    """Apply cop's action (move and/or barrier). Returns (new_state, capture_reason | None).

    Step 1: Validate and apply cop move (orthogonal or stay).
    Step 2: Validate and apply barrier placement (quota, empty cell).
    Step 3: Check capture — cop-on-thief, then barrier-on-thief.
    Rejected placements return state unchanged; quota is not consumed.
    """
    ...

def apply_thief_turn(
    state: GameState,
    move_to: Coord,
    params: GameParams,
) -> tuple[GameState, str | None]:
    """Apply thief's move. Returns (new_state, capture_reason | None).

    Step 0: Check no-legal-move → capture if thief has no options (D-13).
    Step 1: Validate and apply thief move (orthogonal or stay, non-barriered cell).
    Step 2: Increment turn counter; check survival threshold.
    """
    ...
```

### Anti-Patterns to Avoid

- **Global mutable board object:** Creates the shared-state disqualification risk (rule 2). All state must be in an immutable `GameState` passed explicitly.
- **Hardcoded numeric values anywhere in source:** Zero tolerance per D-05, QUAL-11, BASE-08. Even `7` or `14` in a test assertion must come through `params.board_size` or `params.barrier_quota`.
- **Diagonal neighbor check omission:** Must explicitly reject `(row±1, col±1)` moves — diagonal moves are a fixed rule violation (rule 14).
- **"Stay" excluded from legal moves:** "Stay in place" (no movement) is always a legal move for both agents. Omitting it makes the thief always capturable by total barrier surround, breaking BASE-05.
- **Quota consumed on rejected placement:** Rejected placements (on occupied, barriered, or over-quota) must not mutate `barriers_placed`. The check order matters: validate first, mutate second.
- **Capture check after thief moves:** Capture must be checked between cop's action and thief's turn (D-12). If checked after thief moves, a cop landing on the thief's old cell could be missed.
- **`barriers_placed` stored outside state:** If the quota counter is not part of the immutable snapshot, it cannot be replayed or tested independently.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| BFS/shortest-path | Custom BFS | Standard `collections.deque` BFS in 10 lines | Simple enough in-house; no library adds value for 7×7 grid |
| Config parsing | Custom INI/TOML reader | `json.load()` from stdlib | `game_params.json` is plain JSON — no library needed |
| Immutable state | Hand-rolled copy-on-write | `@dataclass(frozen=True)` + `dataclasses.replace()` | Zero cost, type-safe, stdlib |
| Test parametrize | Manual test loops | `@pytest.mark.parametrize` | Cleaner, better error messages |

**Key insight:** The board engine is simple enough that stdlib is sufficient everywhere. Adding third-party libraries (e.g., numpy for the grid) would introduce a dependency that the 7×7 grid does not justify and that complicates the Phase-8 repo split.

---

## Common Pitfalls

### Pitfall 1: "Stay" Not Included as a Legal Move

**What goes wrong:** Thief is declared captured by no-legal-move even when "stay" would be valid.
**Why it happens:** Movement code lists only the 4 orthogonal neighbors, forgetting stay.
**How to avoid:** `legal_moves()` always starts with the current position as a candidate, then filters it like any other cell (it passes unless the thief's own cell is a barrier, which cannot happen since a barrier on the thief = capture).
**Warning signs:** BASE-05 integration test passes only when thief is completely surrounded; edge case where thief has one neighbor open but "no moves" is declared.

### Pitfall 2: Quota Consumed on Invalid Barrier

**What goes wrong:** Rejected barrier attempts still increment `barriers_placed`, meaning the cop runs out of quota prematurely.
**Why it happens:** Validation and mutation in wrong order.
**How to avoid:** Return early on any validation failure before touching `barriers_placed`.
**Warning signs:** BASE-02 test shows quota exhausted after N rejected placements.

### Pitfall 3: Capture Check Timing

**What goes wrong:** Cop-on-thief capture missed because the check runs after thief's response move.
**Why it happens:** Loop structured as: cop move → thief move → capture check.
**How to avoid:** Exactly follow D-12 order: cop acts → check capture → thief turn → increment.
**Warning signs:** Test where cop moves onto thief's cell but game continues for another turn.

### Pitfall 4: Hardcoded Value Slippage in Tests

**What goes wrong:** A test uses `7` for board size or `14` for quota, then a future game with a negotiated larger grid fails the test even though the code is correct.
**Why it happens:** Tests bypass config loading and hardcode the pilot defaults.
**How to avoid:** All tests use `params = load_game_params(POLICE_CONFIG_PATH)` or a fixture that builds `GameParams` from the actual config file. Never write `assert board_size == 7` — write `assert board_size == params.board_size`.
**Warning signs:** `QUAL-11` ruff check cannot catch this automatically in tests.

### Pitfall 5: Barrier on Cop's Own Cell Accepted

**What goes wrong:** Cop places a barrier on its own current cell, creating an impassable square under the cop's feet.
**Why it happens:** Validation only checks the thief's position and empty cells, not the cop's position.
**How to avoid:** `apply_barrier()` rejects if `barrier_at == state.cop` (rule: can only place on empty cells; cop's cell is occupied).
**Warning signs:** No test for this edge case; discovered only during integration play.

### Pitfall 6: Shared `game_params.json` File Object

**What goes wrong:** Both cop-side and thief-side code import from the same loaded config object in a test, creating the shared-state smell.
**Why it happens:** Test fixture loads config once and shares it.
**How to avoid:** Each process reads its own config dir (`config/police/` vs `config/thief/`). In tests, fixtures create a `GameParams` independently — do not share a live config object between agents. The values being identical (D-06) is verified by content comparison, not by sharing the same object.
**Warning signs:** Test `monkeypatch` changes one agent's config and unexpectedly affects the other.

### Pitfall 7: Missing `__init__.py` in Sub-packages

**What goes wrong:** `from pursuit.shared.board import GameState` fails with `ModuleNotFoundError`.
**Why it happens:** `src/pursuit/shared/` created as a directory but without `__init__.py`.
**How to avoid:** Every subdirectory under `src/pursuit/` needs an `__init__.py`. Check: `sdk/`, `services/`, `shared/`.
**Warning signs:** Import works in the IDE but fails with `uv run pytest`.

---

## Code Examples

### `game_params.json` schema (locked by D-05, D-06, BASE-08)

```json
{
  "version": "1.00",
  "board_size": 7,
  "start_cop": [0, 0],
  "start_thief": [3, 3],
  "barrier_quota": 14,
  "move_ceiling": 35,
  "survival_threshold": 35,
  "score_capture_cop": 20,
  "score_capture_thief": 5,
  "score_survival_cop": 5,
  "score_survival_thief": 10,
  "score_tie": 2
}
```

All values from PARAMETERS.md (Table 13, 15, 17). This file is identical in `config/police/` and `config/thief/`.

### `role.json` (the only legitimate difference between config dirs)

```json
{"role": "police"}
```
```json
{"role": "thief"}
```

### `constants.py` (structural values only — no game numbers)

```python
# Source: project decisions D-07; PARAMETERS Table 15 (movement rule)
from enum import Enum

class Direction(Enum):
    """Orthogonal movement directions + stay. No diagonals (rule 14, fixed)."""
    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST  = (0, 1)
    WEST  = (0, -1)
    STAY  = (0, 0)

class CellState(Enum):
    """Logical state of a grid cell (non-numeric)."""
    EMPTY   = "empty"
    BARRIER = "barrier"
    COP     = "cop"
    THIEF   = "thief"

class Outcome(Enum):
    """Game end states. All four named even though Phase 1 only produces CAPTURE/SURVIVAL."""
    CAPTURE       = "capture"
    SURVIVAL      = "survival"
    TIE           = "tie"            # produced in Phase 8 (series aggregate)
    TECHNICAL_LOSS = "technical_loss" # produced in Phase 6–7 (crypto audit)

# Config file key literals (avoid magic strings)
class ConfigKey:
    BOARD_SIZE         = "board_size"
    START_COP          = "start_cop"
    START_THIEF        = "start_thief"
    BARRIER_QUOTA      = "barrier_quota"
    MOVE_CEILING       = "move_ceiling"
    SURVIVAL_THRESHOLD = "survival_threshold"
    SCORE_CAPTURE_COP   = "score_capture_cop"
    SCORE_CAPTURE_THIEF = "score_capture_thief"
    SCORE_SURVIVAL_COP  = "score_survival_cop"
    SCORE_SURVIVAL_THIEF = "score_survival_thief"
    SCORE_TIE           = "score_tie"
    VERSION             = "version"
```

### `version.py`

```python
# Source: SEGAL_GUIDELINES.md §8, QUAL-06
VERSION = "1.00"
```

### `pyproject.toml` (D-01 verbatim)

```toml
[project]
name = "pursuit"
version = "1.00"
description = "P2P cops-and-robbers game engine"
requires-python = ">=3.10"
dependencies = []

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.coverage.run]
source = ["src"]
omit = [
    "src/main.py",
    "*/tests/*",
    "src/**/gui/*",
]

[tool.coverage.report]
fail_under = 85

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mutable board object (`board[r][c] = X`) | Immutable `GameState` dataclass + pure functions | Project design (Phase 1) | Eliminates shared-state disqualification risk; enables easy replay and testing |
| `requirements.txt` + `pip` | `pyproject.toml` + `uv` | Segal Table 5 requirement | Enforced package manager; no accidental global pip installs |
| Hardcoded constants in source | All numerics from `game_params.json` | Appendix F §2 rule 1 | Config file can be cryptographically locked (Phase 6); enables byte-for-byte verification (rule 11) |

**Deprecated/outdated in this project context:**
- `setup.py`: replaced by `pyproject.toml`; never use.
- `python -m pytest` or bare `python`: use `uv run pytest` only.
- `import constants` for game numbers: zero tolerance; config only.

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` — this section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (latest via uv) + pytest-cov |
| Config file | `pyproject.toml` `[tool.coverage.*]` sections (Wave 0 — must exist before tests) |
| Quick run command | `uv run pytest tests/unit/ -x -q` |
| Full suite command | `uv run pytest --cov=pursuit --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BASE-01 | Orthogonal move accepted; diagonal rejected | unit | `uv run pytest tests/unit/test_board.py -x` | ❌ Wave 0 |
| BASE-01 | "Stay" always legal for both agents | unit | `uv run pytest tests/unit/test_board.py::test_stay_is_legal -x` | ❌ Wave 0 |
| BASE-02 | Over-quota barrier rejected, board unchanged | unit | `uv run pytest tests/unit/test_barrier.py::test_quota_exceeded -x` | ❌ Wave 0 |
| BASE-02 | Rejected barrier does not consume quota | unit | `uv run pytest tests/unit/test_barrier.py::test_rejected_no_quota_cost -x` | ❌ Wave 0 |
| BASE-03 | Cop-on-thief → CAPTURE outcome | unit | `uv run pytest tests/unit/test_capture.py::test_cop_on_thief_capture -x` | ❌ Wave 0 |
| BASE-04 | Barrier-on-thief → CAPTURE outcome | unit | `uv run pytest tests/unit/test_capture.py::test_barrier_on_thief_capture -x` | ❌ Wave 0 |
| BASE-05 | Thief with no legal move → CAPTURE | unit | `uv run pytest tests/unit/test_capture.py::test_no_legal_move_capture -x` | ❌ Wave 0 |
| BASE-05 | Thief with 1 open neighbor not captured | unit | `uv run pytest tests/unit/test_capture.py::test_one_move_available_no_capture -x` | ❌ Wave 0 |
| BASE-06 | Turn = survival_threshold, no capture → SURVIVAL | unit | `uv run pytest tests/unit/test_capture.py::test_survival_at_threshold -x` | ❌ Wave 0 |
| BASE-06 | Turn < threshold → game continues | unit | `uv run pytest tests/unit/test_capture.py::test_game_continues_below_threshold -x` | ❌ Wave 0 |
| BASE-07 | CAPTURE outcome scores (20, 5) | unit | `uv run pytest tests/unit/test_capture.py::test_capture_score -x` | ❌ Wave 0 |
| BASE-07 | SURVIVAL outcome scores (5, 10) | unit | `uv run pytest tests/unit/test_capture.py::test_survival_score -x` | ❌ Wave 0 |
| BASE-08 | Config loaded; zero hardcoded values in source | unit | `uv run pytest tests/unit/test_config.py -x` | ❌ Wave 0 |
| BASE-08 | Missing config key raises at load, not during play | unit | `uv run pytest tests/unit/test_config.py::test_missing_key_raises -x` | ❌ Wave 0 |
| GATE-1 | Both agents move legally (full turn) | integration | `uv run pytest tests/integration/test_game_loop.py::test_legal_turn_sequence -x` | ❌ Wave 0 |
| GATE-2 | Over-quota barrier rejected mid-game | integration | `uv run pytest tests/integration/test_game_loop.py::test_barrier_quota_gate -x` | ❌ Wave 0 |
| GATE-3 | All 3 capture types fire in full game loop | integration | `uv run pytest tests/integration/test_game_loop.py::test_all_capture_types -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/ -x -q`
- **Per wave merge:** `uv run pytest --cov=pursuit --cov-report=term-missing`
- **Phase gate:** Full suite green (`pytest --cov`, `ruff check .`, `scripts/check_line_limit.sh`) before `/gsd:verify-work 1`

### Coverage Strategy

Reaching ≥85% with only stdlib engine code is achievable by ensuring:
1. Every public function in each module has at least: happy-path test + error/rejection test.
2. All three `Outcome` branches (`CAPTURE` cop-on-thief, `CAPTURE` barrier-on-thief, `CAPTURE` no-legal-move, `SURVIVAL`) are exercised.
3. `config.py` error paths tested (missing file, missing key, wrong type).
4. `constants.py` and `version.py` are imported in tests (trivial coverage pickup).
5. `sdk/engine.py` tested via `test_sdk_engine.py` which calls each façade method.

### Wave 0 Gaps (must exist before implementation begins)

- [ ] `tests/conftest.py` — shared fixtures: `default_params()` loading from `config/police/game_params.json`, `start_state()` returning the canonical initial `GameState`
- [ ] `tests/unit/test_board.py` — covers BASE-01
- [ ] `tests/unit/test_barrier.py` — covers BASE-02
- [ ] `tests/unit/test_capture.py` — covers BASE-03, BASE-04, BASE-05, BASE-06, BASE-07
- [ ] `tests/unit/test_config.py` — covers BASE-08
- [ ] `tests/unit/test_sdk_engine.py` — covers QUAL-01 SDK façade
- [ ] `tests/integration/test_game_loop.py` — covers all three §10.4 gate criteria
- [ ] Framework install: `uv add --dev pytest pytest-cov ruff` (Wave 0, before any source)

*(If no gaps: "None — existing test infrastructure covers all phase requirements" — not applicable; this is a greenfield phase.)*

---

## Project Constraints (from CLAUDE.md)

All directives below are binding in this phase. The planner must verify compliance at every task.

| Constraint | Enforcement |
|------------|-------------|
| ≤150 lines per .py file (blanks/comments excluded) | `scripts/check_line_limit.sh` pre-commit hook + CI; **never bypass** |
| `uv` only (uv add / uv sync / uv run / uv lock) | No pip, no bare python anywhere |
| `ruff check` → 0 violations | Pre-commit gate |
| `pytest --cov` → ≥85% (`fail_under=85`) | CI gate |
| Zero hardcoded numeric game values in source | Code review + QUAL-11 |
| Zero secrets in source; `os.environ.get()` only | No secrets applicable this phase; `.env-example` must be created |
| SDK layer: all logic behind `src/pursuit/sdk/`; CLI/harness is thin shell | QUAL-01 |
| No shared mutable game state between cop and thief | Rule 2; use immutable `GameState` dataclass |
| No networking, AI, crypto, GUI | Phase scope boundary; defer to phases 2–7 |
| All numeric values from `docs/PARAMETERS.md` → `game_params.json` | Appendix F §2 rule 1 |
| TDD: red → green → refactor; tests written before or alongside code | QUAL-07 |
| Versioning starts at 1.00 in `version.py` and config JSON | QUAL-06 |
| Per-phase docs triplet: `docs/phases/phase-1/{PRD,PLAN,TODO}.md` created at plan-phase | CLAUDE.md per-phase triplet rule |
| Copy skeleton from `docs/phases/_TEMPLATE/` | CLAUDE.md per-phase triplet rule |
| `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` kept current | DOC-01 |
| No graphify step this phase (Phase 1 has no substantial `src/` until after execute) | CLAUDE.md graphify rule (Phase 3+) |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | `pyproject.toml requires-python` | To be verified at execute | — | None; mandatory |
| `uv` | All install/run/test commands | To be verified at execute | — | None; mandatory |
| `git` w/ `core.hooksPath=scripts/hooks` | Pre-commit line-limit gate | Already configured (recent commit) | — | — |
| `scripts/check_line_limit.sh` | Line-limit pre-commit hook | Already exists (verified in repo) | — | — |
| No external services | Phase 1 is pure Python, no network, no DB | N/A | — | — |

**Missing dependencies with no fallback:** None identified — this phase has no external service dependencies.

**Note:** `uv` and Python 3.10+ must be confirmed available on the execution machine before the execute phase begins. The gsd:execute runner should check these as a first task.

---

## Assumptions Log

> All key claims in this research are sourced directly from repo documents read in this session. No external research was performed.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pytest`, `pytest-cov`, `ruff` are appropriate dev dependencies | Standard Stack | Negligible — these are unambiguous standard Python tools |
| A2 | Python stdlib `dataclasses` + `frozenset` sufficient for immutable state | Architecture Patterns | Low — any alternative (namedtuple, attrs) would also work |
| A3 | Zero third-party runtime dependencies needed for the game engine | Standard Stack | Low — if something is needed, `uv add` at execute time |

**All numeric values, turn rules, capture rules, scoring, and file layout are [CITED: docs/PARAMETERS.md, docs/RULES.md, .planning/phases/01-base-logic/01-CONTEXT.md] — not assumed.**

---

## Open Questions

1. **Python version on the execution machine**
   - What we know: `pyproject.toml` will target `py310` (D-01); Python 3.10+ is required
   - What's unclear: Whether Python 3.10+ is installed and `uv` is available right now
   - Recommendation: First task in Wave 0 verifies `uv --version` and `python --version` via `uv run python --version`

2. **`pyproject.toml` already exists or not?**
   - What we know: The repo has `.gitattributes`, `.github/`, `scripts/` but no `src/` yet (greenfield first code phase); `pyproject.toml` was not seen in the project root listing
   - What's unclear: Whether a minimal `pyproject.toml` from project init exists
   - Recommendation: Wave 0 task checks for it and creates/updates it per D-01

---

## Sources

### Primary (HIGH confidence — read directly in this session)
- `.planning/phases/01-base-logic/01-CONTEXT.md` — locked decisions D-01…D-16; canonical spec for this phase
- `.planning/REQUIREMENTS.md` — BASE-01…BASE-08, QUAL-01…QUAL-13
- `docs/PARAMETERS.md` — Tables 13, 15, 17 (all numeric values)
- `docs/RULES.md` — rules 13–16 (movement/barriers), 46–48 (capture/scoring)
- `docs/SEGAL_GUIDELINES.md` — §19.1 Table 5, §2.4 layout, §3 line limit, §6 TDD, §7 linting
- `CLAUDE.md` — project standing rules, binding constraints
- `.planning/ROADMAP.md` — Phase 1 plans 01-01…01-99, success criteria
- `docs/KHALED_PERSONAL_PLAN.md` — Phase 1 canonical seed (lines 217–263)
- `docs/phases/_TEMPLATE/{PRD,PLAN,TODO}.md` — per-phase triplet skeletons
- `scripts/check_line_limit.sh` — existing line-limit gate (do not recreate)
- `.planning/config.json` — `nyquist_validation: true` confirmed

### Secondary (MEDIUM confidence)
- None — all claims are directly cited from repo documents.

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib; dev tools are unambiguous
- Architecture: HIGH — directly derived from locked CONTEXT.md decisions
- Pitfalls: HIGH — derived from explicit rules (D-10, D-12, D-13, QUAL-11)
- Validation: HIGH — test map traces directly to BASE-xx requirements
- Numbers: HIGH — every value cited to PARAMETERS.md table and row

**Research date:** 2026-07-27
**Valid until:** End of Phase 1 execution (decisions are locked; no time-sensitive external dependencies)
