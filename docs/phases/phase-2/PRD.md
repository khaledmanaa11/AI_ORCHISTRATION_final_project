# Phase 2 PRD — FastMCP Infrastructure

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-07-28

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); captures only what is
> specific to Phase 2. Numbers come from [PARAMETERS.md](../../PARAMETERS.md), except the
> two engineering defaults called out under "Numeric sourcing" below.

## Goal

Deliver the P2P plumbing: cop and thief as two separate processes, each simultaneously a
FastMCP server and client, exchanging coordinate-only messages over localhost. A per-agent
orchestrator drives turn order through a state machine; a deadline tracker and watchdog
prevent freezes; the shared game config is verified identical on both sides.

## Requirements covered

| REQ-ID | Description |
|--------|-------------|
| NET-01 | Cop and thief run as two separate processes under `config/police/` vs `config/thief/` (rule 1) |
| NET-02 | No shared runtime state, memory, or variables between the two agents (rule 2) |
| NET-03 | Each agent is simultaneously a FastMCP server (exposes tools) and client (calls the opponent's tools) (§C) |
| NET-04 | The orchestrator is the single entry point, driving turn order through a proper state machine (rules 3–4) |
| NET-05 | Every attempt to transition to an illegal state is reported (rule 5) |
| NET-06 | A deadline tracker prevents freezing while waiting on the opponent (rule 6) |
| NET-07 | A watchdog monitors process crashes and rescues data (rule 7) |
| NET-08 | A geometric message sent over localhost is received and decoded correctly by the other agent (Stage 2 gate) |
| NET-09 | The configuration file is verified byte-for-byte identical on both sides (rule 11) |
| QUAL-02 | No duplication — extracted at 2+ copies into a shared module (`loader_helpers.py`, `canonical_json`) |
| QUAL-11 | Zero hardcoded values in source — config, `constants.py`, or `Enum` only |
| QUAL-12 | Zero secrets in source; `os.environ.get()` only; `.env-example` committed |
| QUAL-13 | `uv` is the sole package manager; `pyproject.toml` + `uv.lock`, no `requirements.txt` |
| DOC-02 | `docs/PRD_mcp_transport.md` — the per-mechanism PRD for the FastMCP peer layer |

## Acceptance criteria (= §10.4 milestone gate)

1. **GATE-1 — Geometric message round-trip:** A geometric message sent by agent A over
   localhost is received and decoded correctly by agent B. An `Envelope` with `type=move`
   and payload `{x, y}` round-trips to the identical coordinates
   (`test_peer_roundtrip.py`).

2. **GATE-2 — Two processes, no shared state:** Cop and thief run as two separate
   processes under `config/police/` and `config/thief/` with no shared runtime state.
   Asserted positively: two runtimes share no queue, machine, watchdog, or log
   (`test_two_runtimes_share_no_runtime_state`); one entry point serves both config roots
   (`test_entry_point_is_config_dir_parameterised`); plus a real two-process launch in
   task 2-10.

3. **GATE-3 — State machine, reporting, and anti-hang:** The orchestrator drives turn
   order via a state machine; every illegal transition is reported; the watchdog and
   deadline tracker prevent hangs. Full `INIT → HANDSHAKE → MY_TURN ↔ WAIT_OPPONENT →
   GAME_OVER` lifecycle, an illegal transition producing a JSONL record, a silent opponent
   yielding the technical-win path, and a freeze writing its incident record
   (`test_turn_lifecycle.py`, `test_turn_resilience.py`).

## Numeric sourcing

| Value | Source | Status |
|---|---|---|
| Response timeout 30 s | PARAMETERS.md Table 19 row 6 | negotiable |
| Watchdog threshold 60 s | PARAMETERS.md Table 19 row 7 | negotiable |
| Retries 3 | PARAMETERS.md Table 19 row 4 (reused per D-17) | minimum |
| Backoff 5 s | PARAMETERS.md Table 19 row 3 (reused per D-17) | minimum |
| Ports 8001 / 8002 | **D-16 — engineering default, NOT a PARAMETERS.md value** | env-overridable |
| `watchdog_poll_seconds` 1 | **D-18 — engineering default, NOT a PARAMETERS.md value** | — |

Appendix F does not cover network ports or watchdog sampling cadence; those two rows are a
different *category* of number and are labelled as such wherever they appear.

## In scope / Out of scope (this phase)

- **In:** FastMCP streamable-HTTP peer runtime and the four-tool surface (stub bodies),
  typed message envelope, canonical-JSON config digest, turn state machine with
  severity-based illegal-transition reporting, JSONL event log, watchdog, deadline tracker
  with technical-win verdict, handshake, per-agent orchestrator, thin `main.py`, dev
  launcher, `docs/PRD_mcp_transport.md`, and the §10.4 gate tests.

- **Out:** Strategy/RL (Phase 3), hints/scent/LLM (Phase 4), cloud tunneling (Phase 5),
  commit-reveal cryptography (Phase 6), Gmail reporting/GUI (Phase 7), submission and
  league operations (Phase 8). Tool signatures for later phases are fixed now; their
  behavior is not.

## Dependencies

- Depends on: Phase 1 (`pursuit.sdk.engine` is the only route to game logic)
- External: `fastmcp` 3.4.5, `pytest-asyncio` (dev) — both added via `uv add`

## Success metrics & test scenarios

- `test_peer_roundtrip.py` passes (GATE-1)
- `test_turn_lifecycle.py` + `test_turn_resilience.py` pass (GATE-2, GATE-3)
- `uv run pytest --cov=pursuit` — suite green with ≥85% coverage
- `uv run ruff check .` — 0 violations
- `bash scripts/check_line_limit.sh` — all source and test files ≤150 lines
