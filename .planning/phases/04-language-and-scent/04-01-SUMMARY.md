---
phase: 04-language-and-scent
plan: "01"
subsystem: strategy
tags: [scent, pheromone, cryptographic-lock, sha256, canonical-json, config-loader, rule-25-guard, dec-pomdp]

# Dependency graph
requires:
  - phase: 03-blind-strategy-module-rl-policy
    provides: >
      loader_helpers.py fail-loud validation primitives (require_str/int/float/list/key),
      config_hash.py's canonical_json/sha256 digest pattern, ResolutionKey's precedent for
      a negotiated config block kept out of game_params.json, and
      scripts/check_no_llm_in_strategy.py's structural rule-25 import gate
provides:
  - "Locked, hashable scent model: config/{police,thief}/scent.json (byte-identical) carrying Table 16's three fixed values, the Figure-4 5x5 kernel, and the Sec4.5 worked example (0.9 -> 0.81)"
  - "shared/scent_config.py + shared/scent_kernel.py: load_scent_model()/scent_digest(), full validation (shape, range, triple symmetry, centre==source, worked-example self-consistency)"
  - "strategy/scent.py: pure emission()/decay()/expected_strength_after() implementing Sec4.3's tau(t+1)=max(0,(1-rho)*tau(t)+delta_tau) law, edge-clipped, epsilon-pruned"
  - "strategy/scentfield.py: ScentField, a mutable per-peer object holding independent own/opponent trails with no shared state (D-49, rule 2)"
  - "Hardened rule-25 CI guard: scripts/check_no_llm_in_strategy.py now rejects pursuit.services imports from strategy modules, closing the hole before services/llm/ exists"
affects: [04-02-handshake-scent-digest, 04-05-belief-map-core, 04-08-deception-policy, 04-11-belief-adapter, any later Phase-4 plan adding modules under src/pursuit/services/llm/]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "150-code-line file split mirrors strategy_config.py/strategy_schema.py: scent_config.py (JSON loading + digest) delegates kernel-shape/symmetry/worked-example validation to scent_kernel.py"
    - "Negotiated config block kept out of game_params.json, key enum living beside its own loader instead of in config_keys.py (extends the ResolutionKey precedent; config_keys.py stays untouched)"
    - "Mutable per-peer dataclass (ScentField) with field(default_factory=dict), distinct from the frozen-dataclass convention used for cross-turn GameState"
    - "scent_digest() reuses network/config_hash.py's canonical_json rather than defining a second serialiser"

key-files:
  created:
    - config/police/scent.json
    - config/thief/scent.json
    - src/pursuit/shared/scent_config.py
    - src/pursuit/shared/scent_kernel.py
    - src/pursuit/strategy/scent.py
    - src/pursuit/strategy/scentfield.py
    - tests/unit/test_scent_config.py
    - tests/unit/strategy/test_scent.py
    - tests/unit/strategy/test_scentfield.py
  modified:
    - scripts/check_no_llm_in_strategy.py
    - tests/integration/test_strategy_pluggable.py

key-decisions:
  - "scent_config.py split into scent_config.py + scent_kernel.py at the 150-code-line ceiling (not in the plan's files_modified list, but CLAUDE.md's line-limit rule takes precedence over plan instructions -- see Deviations)"
  - "emit_opponent(cell, weight=1.0) is the single primitive for both Regime A (weight=1.0, exact revealed cell) and Regime B (repeated weighted calls from a belief posterior); ScentField never decides which regime applies"
  - "ScentField.strength()/freshest() take a grid NAME ('own'/'opponent') rather than the dict itself, validated fail-loud against an explicit allow-list"

requirements-completed: [LANG-04, LANG-07]

# Metrics
duration: ~25min
completed: 2026-08-08
---

# Phase 4 Plan 01: Locked Scent Model Summary

**Cryptographically-lockable scent model (Table 16: 0.9 source / 0.10 decay / 5x5 window, Figure-4 kernel transcribed verbatim) with pure emission/decay operations and a per-peer ScentField holding independent own/opponent trails -- plus a hardened rule-25 CI guard closing the `pursuit.services` import hole before any Phase-4 strategy module exists.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-08T21:19:17Z
- **Tasks:** 4 planned tasks (5 commits: one task split into a source commit + a follow-up coverage commit, see Deviations)
- **Files modified:** 11 (9 created, 2 modified)

## Accomplishments

- Locked payload `config/{police,thief}/scent.json` is byte-identical, self-validating (kernel symmetry, centre==source, worked-example recomputed and checked against `source`/`decay`), and reduces to one stable SHA-256 digest: **`c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e`** (recorded verbatim per this plan's `<output>` spec; plan 04-02 asserts against it, and the league opponent will be asked to match it).
- `emission()`/`decay()`/`expected_strength_after()` reproduce the book to the decimal: the config's own worked example (`0.9 -> 0.81`) round-trips through `decay()` exactly, and 10/35-step repeated `decay()` matches the closed form within float tolerance.
- `ScentField` carries a peer's own trail and its local reconstruction of the opponent's on one object with zero cross-process leakage (D-49, rule 2) -- verified for 35 joint turns with no negative values and no aliasing between the live field and a `snapshot()`.
- `scripts/check_no_llm_in_strategy.py` now rejects any `pursuit.services` import (bare or dotted) from a strategy module, proven by a synthetic-tree test before `services/llm/` (the real target) exists.
- 100% line coverage on all four new modules (`scent_config.py`, `scent_kernel.py`, `scent.py`, `scentfield.py`); repo-wide suite: 416 passed, 91.27% coverage (gate: >=85%).

## Task Commits

Each task was committed atomically:

1. **Task 1: The locked payload and its loader** - `5607663` (feat) — `config/{police,thief}/scent.json`, `shared/scent_config.py`, `shared/scent_kernel.py` (split, see Deviations), `tests/unit/test_scent_config.py`
2. **Task 2: The two pure operations — emission and decay** - `3a7fc34` (feat) — `strategy/scent.py`, `tests/unit/strategy/test_scent.py`
3. **Task 3: ScentField — two grids, no shared state** - `cb145c5` (feat) — `strategy/scentfield.py`, `tests/unit/strategy/test_scentfield.py`
4. **Task 4: close the rule-25 guard's services hole** - `589772a` (fix) — `scripts/check_no_llm_in_strategy.py`, `tests/integration/test_strategy_pluggable.py`
5. **Follow-up: coverage completion for Task 1** - `509f114` (test) — two additional `tests/unit/test_scent_config.py` cases closing a discovered coverage gap (see Deviations)

_Note: no task in this plan was tagged `tdd="true"`; tests were written alongside each task's implementation and committed together, per CLAUDE.md's "tests before or alongside code."_

## Files Created/Modified

- `config/police/scent.json` / `config/thief/scent.json` — the locked payload; byte-identical (`cmp` confirms no difference)
- `src/pursuit/shared/scent_config.py` — `ScentKey` enum, frozen `ScentModel`, `load_scent_model()`, `scent_digest()`
- `src/pursuit/shared/scent_kernel.py` — kernel shape/range/symmetry validation and worked-example self-consistency check (split out of scent_config.py)
- `src/pursuit/strategy/scent.py` — `emission()`, `decay()`, `expected_strength_after()`
- `src/pursuit/strategy/scentfield.py` — `ScentField` (own/opponent grids, `emit_own`/`emit_opponent`/`advance`/`strength`/`freshest`/`snapshot`)
- `scripts/check_no_llm_in_strategy.py` — added the `pursuit.services` rejection case (STRAT-07)
- `tests/integration/test_strategy_pluggable.py` — GATE-3 extended with a parametrized services-import test and a `pursuit.shared` allow-case
- `tests/unit/test_scent_config.py`, `tests/unit/strategy/test_scent.py`, `tests/unit/strategy/test_scentfield.py` — new unit suites

## Decisions Made

- **Split `scent_config.py` at the 150-code-line ceiling** rather than compressing (CLAUDE.md: "split files, never compress code to fit"), extracting kernel/worked-example validation into `scent_kernel.py` — the same shape as this codebase's existing `strategy_config.py`/`strategy_schema.py` split.
- **`emit_opponent(cell, weight=1.0)`** is the one primitive both belief regimes (D-48) will use: Regime A calls it once at full weight for an exactly revealed cell; Regime B (plan 04-05) calls it once per `(cell, probability)` pair in its posterior. `ScentField` never decides which regime applies, keeping the belief-map plan free of a circular import — as the plan's Task 3 action explicitly required.
- **`ScentField.strength`/`freshest` take a grid name string**, validated against an explicit `('own', 'opponent')` allow-list rather than `getattr`, so an unknown grid name fails loud with a clear message instead of an obscure `AttributeError`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split `scent_config.py` into `scent_config.py` + `scent_kernel.py`**
- **Found during:** Task 1, first line-limit check after writing the loader
- **Issue:** The single-file draft (`ScentKey` + `ScentModel` + `load_scent_model` + full kernel/worked-example validation + `scent_digest`) measured 175 code lines against the 150-line hard gate (`scripts/check_line_limit.sh`, CLAUDE.md-mandated pre-commit/CI check). The plan's `files_modified` list names only `src/pursuit/shared/scent_config.py` for this concern, but CLAUDE.md states the line-limit rule "OVERRIDES any default behavior" and takes precedence over plan instructions.
- **Fix:** Extracted `validated_kernel()`, `_validated_row()`, `_check_symmetry()`, and `check_worked_example()` into a new sibling module `src/pursuit/shared/scent_kernel.py` (no `pursuit` import — plain numeric validation), following this codebase's own precedent (`strategy_config.py`/`strategy_schema.py`). `scent_config.py` now imports from it. This is a mechanical decomposition with the same public API surface, not a new architectural decision — no Rule 4 checkpoint was warranted.
- **Files modified:** `src/pursuit/shared/scent_config.py` (new), `src/pursuit/shared/scent_kernel.py` (new)
- **Verification:** Both files pass `scripts/check_line_limit.sh` (149 and ~90 code lines respectively) and `uv run ruff check`; all 20 tests in `tests/unit/test_scent_config.py` pass.
- **Committed in:** `5607663` (Task 1 commit)

**2. [Rule 3 - Blocking] Consolidated two Task-4 test functions to fit the 150-line ceiling**
- **Found during:** Task 4, line-limit check after extending `tests/integration/test_strategy_pluggable.py`
- **Issue:** Adding three new tests as separate functions took the file to 152 code lines (over the 150 limit).
- **Fix:** Merged the two `pursuit.services`-import tests (`from pursuit.services.llm.decode import decode_hint` and bare `import pursuit.services`) into a single `@pytest.mark.parametrize`-driven test, matching this file's own coverage intent with fewer lines (149 total).
- **Files modified:** `tests/integration/test_strategy_pluggable.py`
- **Verification:** `scripts/check_line_limit.sh` passes; both parametrized cases pass individually (`pytest -v` shows both `[from pursuit.services...]` and `[import pursuit.services...]` IDs).
- **Committed in:** `589772a` (Task 4 commit)

**3. [Rule 2 - Missing test coverage] Added the non-numeric/bool kernel-entry test cases**
- **Found during:** post-Task-4 verification pass (`pytest --cov` targeted at the four new modules)
- **Issue:** `scent_kernel.py`'s `_validated_row()` "must be numeric" branch (a string or `bool` kernel entry) had zero test coverage — a gap against CLAUDE.md's "every public function gets at least one test covering the happy path and the error case."
- **Fix:** Added `test_kernel_entry_non_numeric_rejected` and `test_kernel_entry_bool_rejected` to `tests/unit/test_scent_config.py`, bringing all four new modules to 100% line coverage.
- **Files modified:** `tests/unit/test_scent_config.py`
- **Verification:** `uv run pytest ... --cov=pursuit.shared.scent_config --cov=pursuit.shared.scent_kernel --cov=pursuit.strategy.scent --cov=pursuit.strategy.scentfield --cov-report=term-missing` reports 100% on all four.
- **Committed in:** `509f114` (follow-up commit; the affected test file was created in Task 1's commit, which had already been superseded by three later commits by the time the gap was found — a new small commit was made rather than rewriting history mid-branch, consistent with the destructive-git-prohibition guidance against amending non-HEAD commits in a worktree)

---

**Total deviations:** 3 auto-fixed (2 blocking/line-limit, 1 missing test coverage)
**Impact on plan:** All three are mechanical/structural, required by CLAUDE.md's hard gates rather than by any behavioral gap. No scope creep — no new files beyond the two-module split, no new behavior beyond what the plan specified.

## Issues Encountered

- **`core.hooksPath` is not configured in this worktree's git config** (`scripts/hooks/pre-commit`, which enforces the line-limit and ruff gates, exists but was not wired via `git config core.hooksPath scripts/hooks`). Rather than rely on an inactive hook, `scripts/check_line_limit.sh` and `uv run ruff check` were run manually against every touched file before each commit, and the full suite (`uv run pytest tests/ --cov`) was run before finishing. This is an environment/setup observation, not a plan deviation — no file in this plan's scope configures git hooks.

## User Setup Required

None — no external service configuration required. `ANTHROPIC_API_KEY` and other Phase-4 environment variables are not yet read by any module this plan created (D-49 explicitly keeps this plan free of network/services imports).

## Next Phase Readiness

- **Plan 04-02** (handshake carries the scent digest) can proceed immediately: `scent_digest()` is stable, deterministic, and its shipped value (`c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e`) is recorded above for the assertion this plan's `<output>` spec requires.
- **Plan 04-05** (belief map core) has `expected_strength_after()` ready for the scent-likelihood inversion (D-42) and `ScentField.snapshot()` ready to feed a belief-map read without aliasing risk.
- **Any later plan adding `src/pursuit/services/llm/`** (04-06 onward) is now covered by the hardened `pursuit.services` guard from Task 4 — CI will catch an accidental strategy-module import on day one rather than silently passing.
- No blockers identified for the next wave.

## Known Stubs

None — every function shipped in this plan is fully wired (pure computation and a fail-loud config loader); nothing renders empty/placeholder data.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-08*
