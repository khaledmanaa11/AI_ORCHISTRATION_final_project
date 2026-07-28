# Phase 1 TODO — Base Logic

**Owner:** Khaled (solo) · **Updated:** 2026-07-28

> Phase task list. Mirrors the `.planning/` plans for Phase 1. `/gsd:verify-work 1` marks
> every row `[x]` and ticks the matching rows in the root [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 01-00 Project scaffold (uv + config + stubs) | P0 | ☑ done | Khaled | uv project created, game_params.json written, 7 stub test files green; commits bdb9fd7/8731a0f/4def96f |
| 01-01 Config loader + board model + movement (BASE-01, BASE-08) | P0 | ☑ done | Khaled | test_config.py + test_board.py pass (13 tests); constants.py/state.py/config.py/board.py green; ruff 0; line limit passes |
| 01-02 Barrier placement + quota enforcement (BASE-02) | P0 | ☑ done | Khaled | test_barrier.py passes (8 tests); place_barrier rejects over-quota without mutating state; rejected placement costs no quota; AST scan: zero numeric literals; commits 43e4d29/7be2a10 |
| 01-03 Capture detection + scoring (BASE-03..BASE-07) | P0 | ☐ | Khaled | test_capture.py passes all 3 capture types + survival + scoring; detect_capture + compute_score correct |
| 01-04 SDK facade + game loop integration (QUAL-01, §10.4) | P0 | ☐ | Khaled | test_sdk_engine.py + test_game_loop.py pass; SDK layer wraps engine; thin shell only |
| 01-96 Write per-mechanism PRD(s) for this phase | P1 | ☐ | Khaled | Phase 1 has no algorithm-specific PRDs (Phase 1 is pure foundational scaffolding; per-mechanism PRDs start Phase 2) |
| 01-99 On verify-work: mark all rows done + tick root docs/TODO.md | P1 | ☐ | Khaled | Phase gate met; all TODOs checked (DOC-01) |

## Phase gate (§10.4)

- [ ] `uv run pytest tests/unit/ tests/integration/ -x -q` exits 0 (full unit + integration suite green)
- [ ] `uv run pytest --cov=pursuit --cov-report=term-missing` shows >= 85% coverage for all new modules
- [ ] `uv run ruff check .` exits 0
- [ ] `bash scripts/check_line_limit.sh` passes all files
- [ ] All three capture types (cop-on-thief, barrier-on-thief, no-legal-move) demonstrated in integration test
- [ ] Scoring table (CAPTURE 20/5, SURVIVAL 5/10) verified from config, not hardcoded
