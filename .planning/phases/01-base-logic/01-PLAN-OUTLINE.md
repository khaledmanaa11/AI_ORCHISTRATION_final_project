# Phase 1 — Base Logic: Plan Manifest

**Source artifacts:** `01-CONTEXT.md` (D-01…D-16), `ROADMAP.md` §Phase 1,
`01-VALIDATION.md` (per-req test map).

**All requirement IDs that must be covered:** BASE-01, BASE-02, BASE-03, BASE-04,
BASE-05, BASE-06, BASE-07, BASE-08, QUAL-01, QUAL-06.

---

## Plan Manifest

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|------------|--------------|
| 01-00 | Project scaffolding + test-stub infrastructure: uv project, `pyproject.toml` (ruff select/ignore per D-01, coverage `fail_under=85`, `source=src`), `src/pursuit/{sdk,services,shared,constants.py}` layout (D-02/D-04), `config/police/game_params.json` + `config/thief/game_params.json` byte-for-byte identical (D-06) with all numeric game parameters from PARAMETERS.md (D-05/D-07), `config/{police,thief}/role.json` (D-06), `.env-example` dummy values, `src/pursuit/shared/version.py=1.00` (D-02), `tests/conftest.py` + all unit/integration stub files (see VALIDATION.md Wave 0 list), `uv.lock` generated | 0 | — | QUAL-01, QUAL-06 |
| 01-01 | Config loader + board model + orthogonal movement: `ConfigLoader` (fail-loud on missing/malformed key — BASE-08), `GameState` dataclass (D-12), `constants.py` (4 orthogonal directions + stay, `CellState` enum, config key constants — D-07), `get_legal_moves()` (orthogonal + stay accepted; diagonals/OOB/onto-barrier rejected — BASE-01), `apply_move()` | 1 | 01-00 | BASE-01, BASE-08 |
| 01-02 | Barrier placement + quota enforcement: `place_barrier()` (impassable cell — D-08), cop moves AND places same turn (D-09), placement on any empty in-bounds cell (D-10), over-quota/on-own/on-already-barriered/on-occupied rejected with no quota cost (D-10/D-11), quota=14 from config (D-11) | 1 | 01-00 | BASE-02 |
| 01-03 | Capture detection + turn sequencing: `detect_capture(state)` implementing D-12 turn order (cop acts → cop-on-thief check → barrier-on-thief check → no-legal-move check at thief turn start → thief moves) covering all three capture types (BASE-03: coordinate overlap, BASE-04: barrier-on-thief D-10, BASE-05: no legal move D-13); `Outcome` enum with all four values + scoring table from config (D-14, PARAMETERS Table 17); engine produces only `CAPTURE` or `SURVIVAL` this phase (D-15); survival at `move_ceiling`/`survival_threshold`=35 from config (D-16) | 2 | 01-01, 01-02 | BASE-03, BASE-04, BASE-05, BASE-06, BASE-07 |
| 01-04 | SDK façade + per-phase doc triplet + integration gate: `src/pursuit/sdk/engine.py` (thin public API wrapping board/barrier/capture modules — QUAL-01), integration test `tests/integration/test_game_loop.py` validating all three §10.4 gate criteria (legal turn sequence, quota gate mid-game, all three capture types in one loop), create `docs/phases/phase-1/{PRD,PLAN,TODO}.md` from `docs/phases/_TEMPLATE/` skeletons, update root `docs/TODO.md` | 3 | 01-03 | QUAL-01, BASE-03, BASE-04, BASE-05 |

---

## Decisions Coverage Trace

| Decision | Covered By |
|----------|------------|
| D-01 pyproject.toml ruff+coverage config | 01-00 |
| D-02 src/pursuit layout, tests/, config/, .env-example, version.py=1.00 | 01-00 |
| D-03 reuse existing check_line_limit.sh (no re-create) | 01-00 (conformance note in action) |
| D-04 package name `pursuit` | 01-00 |
| D-05 all numeric params in game_params.json | 01-00 (file creation) + 01-01 (loader) |
| D-06 byte-for-byte game_params.json in both config dirs; role.json only diff | 01-00 |
| D-07 constants.py holds non-numeric structural values only | 01-01 |
| D-08 barrier = impassable cell | 01-02 |
| D-09 cop moves AND places same turn | 01-02 |
| D-10 placement on any empty in-bounds cell; barrier-on-thief = capture | 01-02 (placement), 01-03 (capture) |
| D-11 quota=14, over-quota rejected with no quota cost | 01-02 |
| D-12 turn order: cop acts → cap check → thief's turn | 01-03 |
| D-13 no-legal-move evaluated at start of thief's turn | 01-03 |
| D-14 Outcome enum defines all four outcomes + scoring table in config | 01-03 |
| D-15 Phase 1 engine produces only CAPTURE or SURVIVAL | 01-03 |
| D-16 move_ceiling and survival_threshold both 35 from config | 01-03 |

---

## Wave Structure

```
Wave 0: 01-00  (greenfield scaffold + test stubs)
Wave 1: 01-01, 01-02  (board+movement / barrier — independent, no file overlap)
Wave 2: 01-03  (capture — needs both board and barrier)
Wave 3: 01-04  (SDK façade + phase doc triplet + integration gate)
```

Waves 1 plans are parallel: `01-01` touches board/movement files;
`01-02` touches barrier files — zero `files_modified` overlap.

---

## Requirement Coverage Audit

| Requirement | Plan(s) |
|-------------|---------|
| BASE-01 | 01-01 |
| BASE-02 | 01-02 |
| BASE-03 | 01-03, 01-04 |
| BASE-04 | 01-03, 01-04 |
| BASE-05 | 01-03, 01-04 |
| BASE-06 | 01-03 |
| BASE-07 | 01-03 |
| BASE-08 | 01-01 |
| QUAL-01 | 01-00, 01-04 |
| QUAL-06 | 01-00 |

All BASE-01…BASE-08 appear in at least one plan. Coverage complete.

---

## OUTLINE COMPLETE
