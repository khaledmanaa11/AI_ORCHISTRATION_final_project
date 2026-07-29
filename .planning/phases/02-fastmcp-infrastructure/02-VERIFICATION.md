---
phase: 02-fastmcp-infrastructure
verified: 2026-07-29T14:13:09Z
status: passed
score: 3/3 must-haves verified (GATE-1, GATE-2, GATE-3); 11/11 plan sub-checks verified
---

# Phase 2: FastMCP Infrastructure Verification Report

**Phase Goal:** Two separate processes exposing geometric tools over localhost, coordinates
only — the book §10.4 milestone gate (ROADMAP.md, Phase 2):

1. A geometric message sent by agent A over localhost is received and decoded correctly by
   agent B
2. Cop and thief run as two separate processes under `config/police/` and `config/thief/`
   with no shared runtime state
3. The orchestrator (single entry point) drives turn order via a state machine; illegal
   transitions are reported; watchdog + deadline tracker prevent hangs

**Verified:** 2026-07-29T14:13:09Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (§10.4 gate criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GATE-1 — geometric message round-trips A→B over localhost, decoded correctly | ✓ VERIFIED | `tests/integration/test_peer_roundtrip.py::test_coordinates_survive_round_trip` passes against the real four-tool FastMCP surface; NET-08 coverage row PASS in 02-10-SUMMARY.md; additionally proven over a **real HTTP socket** in the Task-4 two-process launch (35-turn game, matching JSONL `message_sent`/`message_received` pairs on both sides) |
| 2 | GATE-2 — cop/thief run as two separate processes under `config/police/` and `config/thief/`, no shared runtime state | ✓ VERIFIED | `tests/integration/test_turn_isolation.py::test_two_runtimes_share_no_runtime_state` (positive assertion: mutate one side's queue/machine/log, prove the other untouched) and `::test_entry_point_is_config_dir_parameterised` both pass; `config/police/network.json` and `config/thief/network.json` exist, differ only in `port`/`opponent_url` (NET-01/04 precondition intact); real launch recorded two distinct PIDs (police `14892`, thief `3656`), distinct ports (8001/8002), distinct JSONL logs, no shared log file |
| 3 | GATE-3 — orchestrator drives turn order via a state machine; illegal transitions reported; watchdog + deadline tracker prevent hangs | ✓ VERIFIED | `tests/integration/test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over` (real `run_turn_loop`, HANDSHAKE→MY_TURN→WAIT_OPPONENT→GAME_OVER, real SDK `CAPTURE`) and `::test_illegal_transition_reported_with_severity` (both `TransitionSeverity` outcomes, real wired reporter → JSONL) pass; `test_turn_resilience.py` proves silent-opponent technical win (deadline tracker) and freeze-writes-incident-before-exit (watchdog) |

**Score:** 3/3 truths verified

### Required Artifacts (aggregated across 02-00 .. 02-10 must_haves)

66 artifacts declared across the 11 plan frontmatters; all 66 exist on disk. Two initially
flagged by pattern-matching turned out to be non-issues on inspection (naming drift, not
missing functionality):

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `config/police/network.json`, `config/thief/network.json` | Per-agent endpoints, differ only in port/opponent_url | ✓ VERIFIED | Confirmed byte content: both carry identical `response_timeout`/`watchdog_threshold`/`retry_count`/`backoff_seconds`; only `port` and `opponent_url` differ |
| `src/pursuit/constants.py` (`NetworkConfigKey`) | Structural field names + env-var names, zero numbers | ✓ VERIFIED | `class NetworkConfigKey` with `ENV_HOST="PURSUIT_HOST"`, `ENV_PORT`, `ENV_OPPONENT_URL` — plan's literal string `NetworkEnvVar` was folded into the same class rather than a second one; functionally equivalent, not a stub |
| `src/pursuit/network/envelope.py`, `config_hash.py` | Envelope + canonical-JSON digest | ✓ VERIFIED | `test_envelope.py`, `test_config_hash.py` green |
| `src/pursuit/network/state_machine.py` | `State`/`ALLOWED_TRANSITIONS`/`TransitionSeverity`/`transition()` | ✓ VERIFIED | `test_state_machine.py` green; table-driven, no FSM library |
| `src/pursuit/network/event_log.py`, `watchdog.py` | JSONL sink + daemon-thread watchdog | ✓ VERIFIED | `os.fsync` call present; `daemon=True` thread present |
| `docs/PRD_mcp_transport.md` | Per-mechanism PRD, v1.00, written before code | ✓ VERIFIED | v1.00, approved, 182 lines, cites PARAMETERS.md Table 19 |
| `src/pursuit/network/tools.py`, `peer_runtime.py` | 4 async tool stubs + server/client runtime | ✓ VERIFIED | `test_tools.py`/`test_peer_runtime.py` green; in-memory `Client(server)` round-trip |
| `src/pursuit/network/deadline.py` | Deadline tracker + technical-win verdict | ✓ VERIFIED | `except ToolError: raise` placed before the retryable-transport tuple (`RETRYABLE_TRANSPORT_ERRORS = (McpError, DeadlineExpired)`) — spelling corrected from the plan's `MCPError` to the real `mcp.McpError` per RESEARCH Pitfall 4, documented in-file; not a gap |
| `src/pursuit/network/handshake.py` | Connectivity + config-digest exchange, abort before move 1 | ✓ VERIFIED | `test_handshake.py`, `test_handshake_abort.py` green; the `Client.call_tool` wire hop itself lives in `handshake_wire.py` (split at the 150-line gate, documented in handshake.py's own docstring) |
| `src/pursuit/network/orchestrator.py`, `agent_lifecycle.py`, `main.py`, `scripts/dev_launch.py` | Per-agent orchestrator, thin entry point, dev launcher (no referee) | ✓ VERIFIED | `dev_launch.py` imports nothing from `pursuit`, only spawns two `python -m pursuit.main --config-dir ...` subprocesses; `main.py` is a thin shell (parse → load config → `agent_lifecycle.run_agent`); deadline-tracker import (`from pursuit.network.deadline import`) lives in `turn_actions.py` (the documented 150-line split off `orchestrator.py`), confirmed present |
| `tests/integration/{conftest,test_peer_roundtrip,test_turn_isolation,test_turn_lifecycle,test_turn_resilience}.py` | §10.4 gate tests | ✓ VERIFIED | All 8 named gate node IDs collect and pass; `load_network_config` call for GATE-3 lives one hop away in `agent_lifecycle.load_agent_config`, confirmed present |

### Key Link Verification

66 key-links declared across the 11 plans; 62 verified directly by import/pattern match, 4
initially flagged were traced and confirmed wired one file removed (documented 150-line-limit
module splits — `handshake_wire.py`, `turn_actions.py`, `agent_lifecycle.py`) — all 66 sound.

| From | To | Via | Status |
|---|---|---|---|
| `tests/conftest.py` | `pursuit.shared.network_config` | lazy import inside `network_params` fixture | WIRED |
| `src/pursuit/shared/network_config.py` | `src/pursuit/shared/loader_helpers.py` | shared `require_*` helpers (QUAL-02) | WIRED |
| `src/pursuit/network/tools.py` | `src/pursuit/network/envelope.py` | `Envelope.from_dict` decode on every handler | WIRED |
| `src/pursuit/network/peer_runtime.py` | `fastmcp` | `from fastmcp import Client, FastMCP`, `run_async(transport=...)` | WIRED |
| `src/pursuit/network/deadline.py` | transport error handling | `except ToolError: raise` before `RETRYABLE_TRANSPORT_ERRORS` (McpError, DeadlineExpired) | WIRED (renamed from plan's literal `MCPError`) |
| `src/pursuit/network/handshake.py` | `fastmcp.Client.call_tool` | via `handshake_wire.py`'s `make_client_caller` (150-line split) | WIRED (one hop) |
| `src/pursuit/network/orchestrator.py` | `src/pursuit/network/deadline.py` | via `turn_actions.py`'s `from pursuit.network.deadline import call_with_retry, wait_for_opponent` (150-line split) | WIRED (one hop) |
| `tests/integration/test_turn_lifecycle.py` | `load_network_config` | via `agent_lifecycle.load_agent_config` | WIRED (one hop) |
| `scripts/dev_launch.py` | `src/pursuit/main.py` | subprocess spawn only, no import | WIRED |

### Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| NET-01 | ✓ SATISFIED | `test_turn_isolation.py::test_two_runtimes_share_no_runtime_state`, `::test_entry_point_is_config_dir_parameterised`; `test_network_config.py` |
| NET-02 | ✓ SATISFIED | Same GATE-2 tests; `test_peer_runtime.py`, `test_agent_lifecycle.py` |
| NET-03 | ✓ SATISFIED | `test_peer_roundtrip.py::test_move_envelope_decoded_by_peer`; `test_peer_runtime.py`, `test_tools.py` |
| NET-04 | ✓ SATISFIED | `test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over`; `test_orchestrator.py`, `test_orchestrator_loop.py` |
| NET-05 | ✓ SATISFIED | `test_turn_lifecycle.py::test_illegal_transition_reported_with_severity`; `test_state_machine.py`, `test_agent_lifecycle.py` |
| NET-06 | ✓ SATISFIED | `test_turn_resilience.py::test_silent_opponent_yields_technical_win`; `test_deadline.py`, `test_deadline_retry.py` |
| NET-07 | ✓ SATISFIED | `test_turn_resilience.py::test_freeze_writes_incident_before_exit`; `test_watchdog.py`, `test_watchdog_thread.py` |
| NET-08 | ✓ SATISFIED | `test_peer_roundtrip.py::test_coordinates_survive_round_trip`; `test_envelope.py`, `test_tools_dispatch.py` |
| NET-09 | ✓ SATISFIED | `test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over`; `test_config_hash.py`, `test_handshake_abort.py` |
| QUAL-02/11/12/13, DOC-02 | ✓ SATISFIED | `loader_helpers.py` shared by both loaders; 0 network literals under `src/` (only in `config/*/network.json`); `.env-example` placeholder-only; `uv.lock` present, no `requirements*.txt` anywhere; `docs/PRD_mcp_transport.md` v1.00 |

### Anti-Patterns Found

None blocking. Two textual matches on "placeholder"/"NOT implemented" were inspected and are
intentional, documented design seams, not stubs hiding missing behavior:

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `src/pursuit/network/orchestrator.py` | 85 | `"""Phase-2 placeholder: ..."""` on `first_legal_move` | ℹ️ Info | Explicitly documented D-01 seam for Phase 3's RL policy (`AgentContext.choose_move`); algorithmic (never LLM), functionally correct for Phase 2's blind-move scope |
| `src/pursuit/network/handshake.py` | 11 | "Step-0 is NOT implemented now" | ℹ️ Info | Correctly out of scope — Step-0/commit-reveal crypto is Phase 6 |

### Independent Checks Run

- `uv run pytest -q` → **179 passed**, 0 failed, 0 skipped
- `uv run pytest --cov=pursuit -q` → **96.87%** coverage (≥85% gate met); no module below 76%
- `uv run ruff check .` → **0 violations**
- `bash scripts/check_line_limit.sh` → passes (no output = all files within 150 lines)
- Commit hashes cited in 02-10-SUMMARY.md (`9e7e17a`, `b45e767`, `4e31d76`) and 02-08-SUMMARY.md commits (`75fadaa`, `f6f9183`) all verified present via `git cat-file -t`
- `config/police/network.json` / `config/thief/network.json` inspected directly: identical except `port` (8001/8002) and `opponent_url`
- `docs/PRD_mcp_transport.md` confirmed v1.00, approved
- No `requirements*.txt` anywhere in the repo (confirmed via file listing)

### Per-Phase Documentation Triplet (CLAUDE.md requirement)

| Document | Status |
|---|---|
| `docs/phases/phase-2/PRD.md` | ✓ Present, v1.00, approved; acceptance criteria match §10.4 gate exactly; requirements table matches REQUIREMENTS.md |
| `docs/phases/phase-2/PLAN.md` | ✓ Present, v1.00; component table matches the actually-shipped `src/pursuit/network/` module list file-for-file |
| `docs/phases/phase-2/TODO.md` | ⚠️ Content complete and accurate (rows 02-00..02-10 all show ☑, gate checklist 8/9 items checked), but row **02-99** ("mark all rows ☑ + tick root docs/TODO.md") is itself still ☐, and the phase-gate's own last line ("`docs/phases/phase-2/{PRD,PLAN,TODO}.md` committed and filled") is still unchecked pending this verification |
| Root `docs/TODO.md` Phase 2 section | ⚠️ All rows still ☐ | Task 02-99 is explicitly scoped to run "on verify-work" — i.e., as a consequence of this VERIFICATION.md landing with `status: passed`, not before it. Not a gap in the phase goal; it is bookkeeping for the orchestrator to close out now that verification has passed. |

This is not scored as a gap against the §10.4 goal (which is fully met), but is flagged so the
orchestrator finalizes task 02-99: check every row in `docs/phases/phase-2/TODO.md` (including
02-99 itself and the phase-gate's last line) and tick the matching Phase 2 rows in root
`docs/TODO.md`.

### Human Verification Required

None required beyond what was already captured empirically in 02-10-SUMMARY.md (a real,
observed two-process localhost launch with PIDs, ports, and JSONL evidence recorded). No
further manual testing is needed to confirm the §10.4 gate.

### Gaps Summary

No gaps. All three §10.4 observable truths are verified against real, passing tests plus one
genuine two-process localhost launch (not merely in-memory). All 66 declared artifacts exist;
the 4 key-links and 2 artifact patterns that did not literal-match their plan's exact wording
were traced by hand and confirmed implemented one file away, each time as a documented
consequence of the 150-line file-size gate (Segal Table 5) splitting a module — not missing
functionality. Full-repo quality gates (tests, coverage, ruff, line-limit, no
`requirements.txt`) all pass. The only open item is bookkeeping: task 02-99 (checking off
`docs/phases/phase-2/TODO.md` and root `docs/TODO.md`) is designed to run as the outcome of
this verification, not before it — the orchestrator should complete it now that `status:
passed` is recorded here.

---

*Verified: 2026-07-29T14:13:09Z*
*Verifier: Claude (gsd-verifier)*
