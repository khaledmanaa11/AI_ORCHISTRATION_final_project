---
phase: 1
slug: base-logic
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-27
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `01-RESEARCH.md` §Validation Architecture. `workflow.nyquist_validation` is `true`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (latest via uv) + pytest-cov |
| **Config file** | `pyproject.toml` `[tool.coverage.*]` (Wave 0 — must exist before tests) |
| **Quick run command** | `uv run pytest tests/unit/ -x -q` |
| **Full suite command** | `uv run pytest --cov=pursuit --cov-report=term-missing` |
| **Estimated runtime** | ~5 seconds (all-stdlib engine, no I/O beyond config read) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -x -q`
- **After every plan wave:** Run `uv run pytest --cov=pursuit --cov-report=term-missing`
- **Before `/gsd:verify-work`:** Full suite must be green **and** `ruff check .` = 0 **and** `scripts/check_line_limit.sh` passes
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-00-01 | 00 | 0 | QUAL-01/06 | — | N/A | scaffold | `uv run pytest -q` (collects 0, exits 0) | ❌ W0 | ⬜ pending |
| 1-01-01 | 01 | 1 | BASE-01 | — | Diagonal move rejected; stay legal | unit | `uv run pytest tests/unit/test_board.py -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | BASE-02 | — | Over-quota barrier rejected, board unchanged | unit | `uv run pytest tests/unit/test_barrier.py -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | BASE-03/04/05 | — | All 3 capture types → CAPTURE | unit | `uv run pytest tests/unit/test_capture.py -x` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 2 | BASE-06/07 | — | Survival at threshold; correct scores | unit | `uv run pytest tests/unit/test_capture.py -x` | ❌ W0 | ⬜ pending |
| 1-00-02 | 00 | 0 | BASE-08 | — | Config loaded; zero hardcoded numerics | unit | `uv run pytest tests/unit/test_config.py -x` | ❌ W0 | ⬜ pending |
| 1-99-01 | 99 | 3 | GATE-1/2/3 | — | All §10.4 gate criteria in a full loop | integration | `uv run pytest tests/integration/test_game_loop.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → Test detail (from RESEARCH.md)

| Req ID | Behavior | Test |
|--------|----------|------|
| BASE-01 | Orthogonal accepted / diagonal rejected; stay always legal | `test_board.py` (+ `::test_stay_is_legal`) |
| BASE-02 | Over-quota rejected, board unchanged; rejection costs no quota | `test_barrier.py::test_quota_exceeded`, `::test_rejected_no_quota_cost` |
| BASE-03 | Cop-on-thief → CAPTURE | `test_capture.py::test_cop_on_thief_capture` |
| BASE-04 | Barrier-on-thief → CAPTURE | `test_capture.py::test_barrier_on_thief_capture` |
| BASE-05 | No legal move → CAPTURE; 1 open neighbor → not captured | `test_capture.py::test_no_legal_move_capture`, `::test_one_move_available_no_capture` |
| BASE-06 | Turn = survival_threshold, no capture → SURVIVAL; below → continue | `test_capture.py::test_survival_at_threshold`, `::test_game_continues_below_threshold` |
| BASE-07 | CAPTURE scores (20,5); SURVIVAL scores (5,10) | `test_capture.py::test_capture_score`, `::test_survival_score` |
| BASE-08 | Config loaded; missing key raises at load, not during play | `test_config.py` (+ `::test_missing_key_raises`) |
| GATE-1/2/3 | Legal turn seq · quota gate mid-game · all 3 capture types | `tests/integration/test_game_loop.py` |

---

## Wave 0 Requirements

- [ ] `uv add --dev pytest pytest-cov ruff` — framework install (no `src/` exists yet; greenfield)
- [ ] `pyproject.toml` `[tool.coverage.*]` (`source = src`, `fail_under = 85`, omit main/tests/gui)
- [ ] `tests/conftest.py` — shared fixtures: `default_params()` (loads `config/police/game_params.json`), `start_state()` (canonical initial `GameState`)
- [ ] `tests/unit/test_config.py` — stubs for BASE-08 (config load + error paths)
- [ ] `tests/unit/test_board.py` — stubs for BASE-01
- [ ] `tests/unit/test_barrier.py` — stubs for BASE-02
- [ ] `tests/unit/test_capture.py` — stubs for BASE-03…BASE-07
- [ ] `tests/unit/test_sdk_engine.py` — stubs for QUAL-01 SDK façade
- [ ] `tests/integration/test_game_loop.py` — stubs for the three §10.4 gate criteria

*Greenfield phase — no existing test infrastructure; all of the above are new.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `game_params.json` byte-for-byte identical across `config/police/` + `config/thief/` | D-06 / future NET-09 | Cross-file identity, not a runtime behavior | `diff config/police/game_params.json config/thief/game_params.json` returns empty |
| No hardcoded numeric game value in any `src/` file | BASE-08 / QUAL-11 | Static audit complements the config-load test | grep `src/` for numeric literals in game logic; only `constants.py` structural values allowed |

*All game outcomes have automated verification; the two rows above are cross-file/static audits.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (all test files are Wave 0 here)
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter (set by planner once plans map every task to a verify)

**Approval:** pending
