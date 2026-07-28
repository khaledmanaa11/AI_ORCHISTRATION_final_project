---
phase: 01-base-logic
reviewed: 2026-07-28T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - src/pursuit/constants.py
  - src/pursuit/sdk/engine.py
  - src/pursuit/shared/barrier.py
  - src/pursuit/shared/board.py
  - src/pursuit/shared/capture.py
  - src/pursuit/shared/config.py
  - src/pursuit/shared/outcome.py
  - src/pursuit/shared/state.py
  - src/pursuit/shared/version.py
  - tests/conftest.py
  - tests/integration/test_game_loop.py
  - tests/unit/test_barrier.py
  - tests/unit/test_board.py
  - tests/unit/test_capture.py
  - tests/unit/test_config.py
  - tests/unit/test_sdk_engine.py
findings:
  critical: 2
  warning: 6
  info: 4
  total: 12
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-07-28T00:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Phase 1 delivers the base logic layer: immutable `GameState`, pure board/barrier/capture
functions, a fail-loud config loader, an outcome scorer, and a thin SDK facade
(`engine.py`). The module decomposition is clean, files are well under the 150-line gate
(largest is `config.py` at 84 effective lines), `ruff check` passes with zero violations,
and no secrets are present. The disqualification-level architecture rules are largely
respected: `GameState` is `frozen`, so no mutable state object is shared between cop and
thief; `engine.py` is genuinely a wiring layer that composes shared pure functions rather
than duplicating logic; and all game numbers are sourced from `game_params.json`.

However, the review surfaces two BLOCKER correctness gaps and several robustness holes:

1. **`apply_move` performs no move-legality validation.** The SDK trusts its caller
   completely and will teleport an agent to any coordinate — off-board, onto a barrier, or
   a multi-cell/diagonal jump. Nothing in this layer enforces the "single orthogonal step"
   rule (Table 15, **fixed**), so an illegal move silently produces an illegal state. This
   is the load-bearing correctness gap of the phase.
2. **The `(0, 0)` literal in `outcome.py` for `TECHNICAL_LOSS` violates the "0 hardcoded
   values" gate** while `game_params.json` already carries a `technical_loss: [0, 0]` key
   that is required, read, and then discarded. This is a self-inflicted disqualification
   risk that the config already has the data to avoid.

The config loader also validates only the top-level scalar `int` fields; the scoring arrays
and start-position tuples are indexed blindly, so a malformed-but-present config can slip
through the "fail-loud" contract that `config.py`'s own docstring promises.

## Structural Findings (fallow)

No `<structural_findings>` block was provided with this review. This section is
intentionally empty; all findings below are narrative (direct code review).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `apply_move` accepts any destination — no legality validation

**File:** `src/pursuit/shared/board.py:64-87`, reached via
`src/pursuit/sdk/engine.py:48,64`

**Issue:** `apply_move(state, agent, dest)` unconditionally writes `dest` into the new
state with `dataclasses.replace`. It never checks that `dest` is in bounds, is not a
barrier, or is one orthogonal step (or STAY) from the agent's current cell. The SDK
entry points `apply_cop_action` and `apply_thief_move` call `apply_move` directly with
the caller-supplied `move_to` and never cross-check it against `get_legal_moves`. The
codebase *has* the validator (`get_legal_moves`) but the mutation path does not use it.

Consequences, all producing a silently-illegal `GameState`:
- Off-board move: `apply_move(state, "thief", (-5, 99))` succeeds. `board_size` is never
  consulted.
- Move onto a barrier: `apply_move` ignores `state.barriers`, so an agent can occupy a
  barriered cell — directly contradicting the D-08 exclusion that `get_legal_moves`
  enforces.
- Teleport / diagonal: `apply_move(state, "cop", (6, 6))` from `(0, 0)` succeeds in one
  call, violating the **fixed** "single orthogonal step, no diagonals" rule (Table 15).

Because this is the only state-transition primitive and it sits behind the SDK facade
that "is the sole public entry point for Phase 2 and beyond" (engine.py:3), every later
phase inherits an engine that cannot reject an illegal move. A cop that jumps onto the
thief in one turn would even register a false `Outcome.CAPTURE`.

**Fix:** Validate `dest` against the legal-move set inside `apply_move` (or in the SDK
facade before calling it) and reject illegal input loudly rather than silently accepting
it:

```python
def apply_move(state: GameState, agent: str, dest: Coord, params: GameParams) -> GameState:
    if dest not in get_legal_moves(state, agent, params):
        raise ValueError(f"Illegal move for {agent}: {dest!r}")
    if agent == "cop":
        return dataclasses.replace(state, cop=dest)
    return dataclasses.replace(state, thief=dest)
```

`apply_move` currently takes no `params`; threading `params` through (the SDK already
holds it) is required for the bounds/barrier check. Add tests: illegal off-board move,
move onto a barrier, and a two-cell jump must all raise.

### CR-02: Hardcoded `(0, 0)` for TECHNICAL_LOSS violates the "0 hardcoded values" gate

**File:** `src/pursuit/shared/outcome.py:52-53` (config side:
`src/pursuit/shared/config.py:90`)

**Issue:** `score_outcome` returns a bare `(0, 0)` literal for `Outcome.TECHNICAL_LOSS`.
The project's machine-checkable code standard is **"Hardcoded values | 0 in source —
config, `constants.py`, or `Enum`"**, and rule 1 ("Never invent a numeric value. Every
number comes from PARAMETERS.md") is disqualification-level. The `0/0` technical-loss
value *is* a defined game number (PARAMETERS.md Table 17 note: "Technical loss ... =
0/0").

Critically, the value is **already present in config**: every `game_params.json` carries
`"technical_loss": [0, 0]`, and `config.py:90` explicitly *requires* that key
(`_require_key(scoring, ConfigKey.SCORE_TECHNICAL_LOSS)`) — then throws the value away
without storing it on `GameParams`. So the loader pays the cost of validating the key but
the scorer re-invents the number as a literal. The module docstring
(`outcome.py:6-10`) rationalizes this as "the only numeric literals permitted," but that
is a self-granted exception the standard does not make: the standard permits config,
`constants.py`, or `Enum` — not "literals the author deemed fixed."

This is the exact defect the review brief flagged. Severity is BLOCKER because it is a
direct violation of a disqualification-level rule, and the fix is trivial because the
data already flows in.

**Fix:** Store the technical-loss pair on `GameParams` and read it like every other
score.

```python
# config.py — add field
score_technical_loss_cop: int
score_technical_loss_thief: int

# config.py — in load_game_params
technical_loss = _require_key(scoring, ConfigKey.SCORE_TECHNICAL_LOSS)
...
score_technical_loss_cop=technical_loss[0],
score_technical_loss_thief=technical_loss[1],

# outcome.py
elif outcome is Outcome.TECHNICAL_LOSS:
    return (params.score_technical_loss_cop, params.score_technical_loss_thief)
```

Update `test_technical_loss_score` to assert against
`default_params.score_technical_loss_*` instead of literal `0`, so the test also stops
hardcoding the value.

## Warnings

### WR-01: Config loader validates only top-level ints — scoring arrays and start tuples are unchecked

**File:** `src/pursuit/shared/config.py:81-104`

**Issue:** The module docstring promises "Every required key and type is validated at load
time ... A malformed config raises immediately." In practice only the four top-level
scalars go through `_require_int`. The scoring pairs are consumed by blind indexing —
`capture[0]`, `capture[1]`, `survival[0]`, `survival[1]`, `tie[0]` — with no check that
each is a two-element list of ints. A config with `"capture": [20]` raises a raw
`IndexError` (not the promised typed `KeyError`/`TypeError`), and `"capture": "xy"` would
silently store the characters `'x'` and `'y'` as scores. Likewise `cop_start` /
`thief_start` are passed straight to `tuple(...)` with no arity or bounds check, so
`cop_start: [0, 0, 0]` or an off-board `[99, 99]` loads without complaint and later
corrupts capture/legal-move logic. This weakens the fail-loud guarantee the whole design
rests on.

**Fix:** Add a `_require_int_pair(container, key)` helper that asserts a 2-element list of
ints, and use it for `capture`, `survival`, `tie`, and `technical_loss`. Validate that
`cop_start`/`thief_start` are 2-tuples of ints within `range(board_size)`.

### WR-02: `move_ceiling` is required and loaded but never used — TIE outcome is unreachable

**File:** `src/pursuit/shared/config.py:79,97` and `src/pursuit/shared/capture.py:70-93`

**Issue:** `move_ceiling` (Table 15 #3, "max turns in the match") is validated and stored
on `GameParams`, but no code reads it. `evaluate_turn_end` decides the game solely on
`survival_threshold`. In the pilot config the two happen to be equal (35 == 35), so the
gap is invisible today — but they are independent parameters (`survival_threshold` is
"turns the thief must survive"; `move_ceiling` is "max turns in the match"), both
**minimum** and independently negotiable upward. If a future game sets
`move_ceiling > survival_threshold`, or if the intended TIE condition ("neither capture
nor survival by move_ceiling") is ever needed, this layer has no path to it. `Outcome.TIE`
exists in the enum and `score_outcome` handles it, but nothing can ever *produce* it —
dead branch reachable only from tests. This is a latent logic gap masked by equal pilot
values.

**Fix:** Either (a) document explicitly that TIE is a Phase-8 series aggregate and that
`move_ceiling` is intentionally unused in Phase 1 (and drop the eager load, or add a code
comment at the load site), or (b) if per-game move exhaustion should end a game, teach
`evaluate_turn_end` to consult `move_ceiling`. Right now the config field is loaded with
no consumer, which reads as an oversight rather than a decision.

### WR-03: `agent` parameter accepts any string; typo silently routes to the thief

**File:** `src/pursuit/shared/board.py:42,85-87` and `src/pursuit/shared/board.py:24`

**Issue:** Both `get_legal_moves` and `apply_move` branch on `agent == "cop"` with an
unconditional `else` that means "thief." Any value that is not exactly `"cop"` — `"COP"`,
`"police"`, `"Thief"`, `""`, or a typo — is silently treated as the thief. There is no
validation and no error. A caller mistake becomes a wrong-agent action with no signal.
`config/police/role.json` uses `"police"` (not `"cop"`), so a caller that forwards the
role string verbatim would move the wrong agent.

**Fix:** Validate the agent against a known set (or use an `Enum`) and raise on anything
else:

```python
if agent not in ("cop", "thief"):
    raise ValueError(f"Unknown agent: {agent!r}")
```

Consider promoting `agent` to an `Agent` enum in `constants.py` to make the typo
unrepresentable.

### WR-04: `_require_int` rejects `bool` inconsistently — `True` passes as an int

**File:** `src/pursuit/shared/config.py:43-50`

**Issue:** `isinstance(value, int)` returns `True` for `bool` in Python (`bool` subclasses
`int`). A config with `"board_size": true` would pass validation and yield
`board_size == 1`, or `"barrier_quota": false` → `0`, silently producing a degenerate
board/quota instead of the promised load-time failure. For a loader whose entire purpose
is to fail loud on malformed numeric config, admitting booleans as ints is a real
correctness hole.

**Fix:** Exclude `bool` explicitly:

```python
if isinstance(value, bool) or not isinstance(value, int):
    raise TypeError(...)
```

### WR-05: BASE-05 "no legal moves" capture branch is unreachable dead code

**File:** `src/pursuit/shared/capture.py:64-65`

**Issue:** The code and its own comment agree that the BASE-05 branch
(`if not get_legal_moves(...)`) can never fire independently: STAY (the thief's own cell)
is always legal unless that cell is a barrier, which is already caught by the BASE-04
branch immediately above (`state.thief in state.barriers`). So `get_legal_moves` for the
thief can only be empty when BASE-04 already returned `CAPTURE`. The branch is dead as
written — it is never the *first* match. `test_no_legal_move_capture` confirms this: its
docstring states a pure BASE-05 state "is geometrically impossible" and the test actually
exercises BASE-04. Dead code that a test only appears to cover is a maintenance trap: a
future change to `get_legal_moves` semantics could make this the live path with no test
that actually isolates it.

**Fix:** Either remove the branch and document that BASE-05 collapses into BASE-04 under
current move semantics, or (better) reorder so the no-legal-moves check runs *before* the
barrier-on-thief check and write a test that reaches it without also tripping BASE-04
(e.g., a hypothetical fully-walled-in non-barrier cell), so the branch is genuinely
covered.

### WR-06: `place_barrier` "added" computation is dead arithmetic that hides an invariant

**File:** `src/pursuit/shared/barrier.py:74-81`

**Issue:** By the time execution reaches line 75, the code has already returned early if
`cell in state.barriers` (line 67). Therefore `new_barriers = state.barriers | {cell}`
*always* adds exactly one element, so `added = len(new_barriers) - len(state.barriers)`
(line 76) is always `1`, and `barriers_placed + added` is always `barriers_placed + 1`.
The `len`-diff dance reads as defensive against double-counting, but the guard that makes
it safe is upstream; here it is dead arithmetic that obscures the real invariant
(one placement per accepted call). If someone later removes the line-67 guard, this code
would *silently* stop incrementing the quota on a duplicate cell — turning a quota-bypass
into invisible behavior instead of a visible bug.

**Fix:** Replace with the direct, honest increment now that duplicates are excluded above:

```python
return dataclasses.replace(
    state,
    barriers=state.barriers | frozenset({cell}),
    barriers_placed=state.barriers_placed + 1,
)
```

## Info

### IN-01: `increment_turn` uses a function-local `import dataclasses`

**File:** `src/pursuit/shared/state.py:41-45`

**Issue:** `increment_turn` imports `dataclasses` inside the function body with a
`# noqa: PLC0415 — local import avoids circular dep risk` comment. There is no circular
dependency risk: `state.py` imports nothing from the pursuit package, and `dataclasses` is
already imported at module top by every sibling (`board.py`, `barrier.py`). The local
import and its `noqa` suppress a lint rule for a risk that does not exist, and it is
inconsistent with the rest of the codebase.

**Fix:** Move `import dataclasses` to the module top alongside `from dataclasses import
dataclass` and drop the `noqa`.

### IN-02: Unused import and dead config constant in `test_board.py`

**File:** `tests/unit/test_board.py:3,9`

**Issue:** `from pathlib import Path` and the module-level `POLICE_CONFIG` are used, but
every test re-loads the config with `load_game_params(POLICE_CONFIG)` while *also*
receiving the `default_params` fixture — which is the same loaded config. The re-load is
redundant duplication (the fixture exists precisely to avoid per-test loading), and it
means these unit tests hit the filesystem on every case. `test_config.py` has the same
redundant-reload pattern. Not a correctness bug, but it duplicates the fixture's job and
couples unit tests to disk I/O.

**Fix:** Use the `default_params` (or `start_state`) fixture directly and delete the
per-test `load_game_params` calls, the `Path` import, and the `POLICE_CONFIG` constant
from the test modules.

### IN-03: `score_tie` silently drops the second tie value

**File:** `src/pursuit/shared/config.py:103` and `src/pursuit/shared/outcome.py:51`

**Issue:** Config stores only `score_tie=tie[0]` and `score_outcome` returns
`(params.score_tie, params.score_tie)` — assuming both sides of a tie score identically.
That is true for the pilot value (`[2, 2]`) and PARAMETERS Table 17 lists a single tie
score, so this is defensible. But `tie[1]` is read from config and silently discarded, and
the symmetry is an implicit assumption not asserted anywhere. If a future config ever set
`"tie": [2, 3]`, the second value would vanish with no warning.

**Fix:** Either assert `tie[0] == tie[1]` at load time (documenting the symmetry
invariant), or store both and return `(tie_cop, tie_thief)` for consistency with the other
score pairs.

### IN-04: Magic string literals `"cop"` / `"thief"` scattered across modules

**File:** `src/pursuit/shared/board.py:42,85`, `src/pursuit/shared/capture.py:64`,
`src/pursuit/sdk/engine.py:48,64`

**Issue:** The agent identity is passed as bare string literals (`"cop"`, `"thief"`) in
five call sites across three modules. `constants.py` already defines a `CellState` enum
with `COP`/`THIEF` members and a `ConfigKey` class specifically to "avoid magic strings,"
yet the agent selector remains a raw string. This is the same anti-pattern the project's
"0 hardcoded values / no magic strings" convention targets, applied to a string rather
than a number. It also enables WR-03 (typo routing).

**Fix:** Introduce an `Agent` enum (or reuse `CellState.COP`/`THIEF`) in `constants.py`
and thread it through `get_legal_moves`, `apply_move`, and the SDK facade instead of bare
strings.

---

_Reviewed: 2026-07-28T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
