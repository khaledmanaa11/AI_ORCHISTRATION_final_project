---
status: testing
phase: 02-fastmcp-infrastructure
source: [02-00-SUMMARY.md, 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md, 02-06-SUMMARY.md, 02-07-SUMMARY.md, 02-08-SUMMARY.md, 02-09-SUMMARY.md, 02-10-SUMMARY.md]
started: 2026-07-29T14:20:33Z
updated: 2026-07-29T14:20:33Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Two-Process Standalone Launch
expected: |
  Running `uv run python -m pursuit.main --config-dir config/police` and
  `uv run python -m pursuit.main --config-dir config/thief` in two separate terminals starts
  two independent agent processes. They handshake over real localhost, then play out a full
  game (alternating cop/thief moves) to a terminal outcome (capture or survival). Each process
  writes its own JSONL event log under `logs/{role}/` — two distinct PIDs, two distinct ports,
  two distinct log files, no shared state.
awaiting: user response

## Tests

### 1. Two-Process Standalone Launch
expected: |
  Running the two `python -m pursuit.main --config-dir ...` commands in separate terminals
  starts two independent processes that handshake, play a full game to a terminal outcome, and
  each write their own JSONL log. No shared PID, port, or log file.
result: [pending]

### 2. Config Mismatch Aborts Cleanly
expected: |
  If one agent's `game_params.json` differs from the other's, the handshake's config-digest
  check detects the mismatch and both sides abort to State.ERROR (recorded in the log) instead
  of hanging or crashing with an unhandled exception.
result: [pending]

### 3. Illegal Transition Reporting
expected: |
  Any illegal state-machine transition attempt is written to the JSONL event log with its
  severity — a RECOVERABLE attempt lets the game keep running, a PROTOCOL_VIOLATION attempt
  ends it — never silently ignored.
result: [pending]

### 4. Silent Opponent Produces a Technical Win
expected: |
  If an opponent stops responding, the retry/backoff ladder exhausts and the waiting agent
  declares a technical win (recorded with evidence: retries attempted, timeout used) instead of
  hanging forever.
result: [pending]

### 5. Watchdog Freeze Detection
expected: |
  If an agent's turn loop freezes past the configured watchdog threshold, a
  `watchdog_incident` record is written to the JSONL log before the process exits — the record
  is readable on disk, not lost.
result: [pending]

### 6. dev_launch.py Convenience Script
expected: |
  Running `uv run python scripts/dev_launch.py` spawns both agent processes (police + thief) as
  subprocesses and waits for them. The script itself holds no game state and imports nothing
  from `pursuit` — it cannot be mistaken for a referee.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0

## Gaps

[none yet]
