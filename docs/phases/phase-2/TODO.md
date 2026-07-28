# Phase 2 TODO — FastMCP Infrastructure

**Owner:** Khaled (solo) · **Updated:** 2026-07-28

> Phase task list. Mirrors the `.planning/` plans for Phase 2. `/gsd:verify-work 2` marks
> every row `[x]` and ticks the matching rows in the root [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 2-00 Phase-2 scaffold + test stubs | P0 | ☑ | Khaled | `uv add fastmcp` (3.4.5) + `uv add --dev pytest-asyncio`; `asyncio_mode = "auto"`; `config/{police,thief}/network.json` (D-04/D-16/D-17/D-18); `NetworkConfigKey`; `.env-example`; 13 test stubs collect and exit 0 (QUAL-11/12/13) |
| 2-01 Network config loader + `loader_helpers` extraction | P0 | ☑ | Khaled | `NetworkParams` + fail-loud `load_network_config()`; `_require_key`/`_require_int` extracted and consumed by **both** loaders; `test_config.py` still green (NET-01/02, QUAL-02/11) |
| 2-02 Envelope + canonical-JSON config digest | P0 | ☑ | Khaled | `{type,turn,sender,payload}` round-trips losslessly; malformed rejected; key-order difference hashes **equal**, one-key difference hashes **unequal** (NET-08/09) |
| 2-03 Turn state machine + illegal-transition reporting | P0 | ☑ | Khaled | `State` enum + `ALLOWED_TRANSITIONS` table, no FSM library; every illegal attempt rejected **and** reported; recoverable keeps playing, protocol violation → `ERROR` (NET-04/05) |
| 2-04 JSONL event log + watchdog | P0 | ☑ | Khaled | One JSON object per line, `flush()` + `os.fsync()` per write; on a stale timestamp the incident record is durable **before** the injected exit fires (NET-05/07) |
| 2-05 `docs/PRD_mcp_transport.md` | P0 | ☑ | Khaled | v1.00; parameter table with a Source column; ports + poll interval labelled engineering defaults; `run_async()`-not-constructor rule pinned. Written **before** the transport code (DOC-02, SEGAL §2.5) |
| 2-06 Tool surface + peer runtime | P0 | ☐ | Khaled | Four `async def` tools registered and callable in-memory; `receive_move` enqueues and returns without blocking; server shutdown releases the port (NET-02/03/08) |
| 2-07 Deadline tracker + technical win | P0 | ☐ | Khaled | Timeout ladder uses config 30/3/5; `ToolError` never laundered into a technical win; verdict carries truthful evidence; no test sleeps on real time (NET-06) |
| 2-08 Handshake + config-digest exchange | P0 | ☐ | Khaled | Matching digests advance past `HANDSHAKE`; mismatch **aborts before move 1** with both digests recorded; unreachable peer is a distinct outcome from mismatch (NET-03/05/09) |
| 2-09 Orchestrator + thin `main.py` + dev launcher | P0 | ☐ | Khaled | Turn loop drives the state machine; no shared runtime state between agents (two named tests); launcher is not a referee; `GAME_OVER` releases the port (NET-01/02/04/05/06/07) |
| 2-10 §10.4 gate tests + coverage audit | P0 | ☐ | Khaled | GATE-1/2/3 each map to named runnable tests; NET-01…NET-09 coverage audit closes; real two-process standalone launch succeeds |
| 2-97 Phase doc triplet at plan-phase | P1 | ☑ | Khaled | `docs/phases/phase-2/{PRD,PLAN,TODO}.md` created and filled (CLAUDE.md) |
| 2-99 Verify-work: mark all rows ☑ + tick root docs/TODO.md | P1 | ☐ | Khaled | Phase gate met; all TODOs checked; root docs/TODO.md Phase 2 section all ☑ (DOC-01) |

## Phase gate (§10.4)

- [ ] `test_peer_roundtrip.py` passes — geometric message decoded correctly (GATE-1)
- [ ] `test_turn_lifecycle.py` passes — two config roots, no shared runtime state (GATE-2)
- [ ] `test_turn_lifecycle.py` + `test_turn_resilience.py` pass — state machine, illegal-transition reporting, watchdog + deadline (GATE-3)
- [ ] Real two-terminal standalone launch: both peers start, handshake, exchange a move
- [ ] `uv run pytest --cov=pursuit` ≥ 85% (QUAL-10)
- [ ] `uv run ruff check .` → 0 violations (QUAL-09)
- [ ] `bash scripts/check_line_limit.sh` passes all src/ and tests/ files (QUAL-08)
- [x] `docs/PRD_mcp_transport.md` committed at v1.00 (DOC-02)
- [ ] `docs/phases/phase-2/{PRD,PLAN,TODO}.md` committed and filled (CLAUDE.md)
