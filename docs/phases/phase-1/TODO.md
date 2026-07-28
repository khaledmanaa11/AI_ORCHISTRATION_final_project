# Phase 1 TODO — Base Logic

**Owner:** Khaled (solo) · **Updated:** 2026-07-28

> Phase task list. Mirrors the `.planning/` plans for Phase 1. `/gsd:verify-work 1` marks
> every row `[x]` and ticks the matching rows in the root [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 1-00 Project scaffolding + test stubs | P0 | ☑ | Khaled | uv project; pyproject.toml (D-01); src/pursuit/ layout (D-02); config dirs; game_params.json; Wave 0 test stubs — all collects 0, exits 0 (QUAL-01/06) |
| 1-01 Config loader + board model + movement | P0 | ☑ | Khaled | Diagonal rejected; values from config; load error at startup; unit tests green (BASE-01/08) |
| 1-02 Barrier placement + quota enforcement | P0 | ☑ | Khaled | Over-quota rejected; rejected placement leaves barriers_placed unchanged; unit tests green (BASE-02) |
| 1-03 Capture detection + outcome scoring | P0 | ☑ | Khaled | All three capture types + survival + scoring table pass unit tests; AST scan zero numeric literals (BASE-03..07) |
| 1-04 SDK facade + integration gate + doc triplet | P0 | ☑ | Khaled | engine.py thin facade (QUAL-01); three §10.4 gate tests green (GATE-1/2/3); per-phase docs triplet created (BASE-03/04/05, QUAL-01) |
| 1-99 Verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ☐ | Khaled | Phase gate met; all TODOs checked; root docs/TODO.md Phase 1 section all ☑ (DOC-01) |

## Phase gate (§10.4)

- [ ] `test_game_loop.py::test_legal_turn_sequence` passes (GATE-1)
- [ ] `test_game_loop.py::test_barrier_quota_gate` passes (GATE-2)
- [ ] `test_game_loop.py::test_all_capture_types` passes (GATE-3)
- [ ] `uv run pytest --cov=pursuit` ≥ 85% (QUAL-10)
- [ ] `uv run ruff check .` → 0 violations (QUAL-09)
- [ ] `bash scripts/check_line_limit.sh` passes all src/ files (QUAL-08)
- [ ] `docs/phases/phase-1/{PRD,PLAN,TODO}.md` committed and filled (CLAUDE.md)
