# 2026-08-19 — remote-round rehearsal, replay board panel, final strategy rejections

Tracker row: none open — post-verification work. Project state: [.planning/STATE.md](../../.planning/STATE.md);
strategy campaign context: [PRD_matrix_mover.md](../PRD_matrix_mover.md) run-3 section.

## What changed

- `0d180ed` feat(replay): reconstructed full-board panel in the replay viewer — new
  `services/reporting/replay_board.py` (all reconstruction + colour logic, coverage-gated),
  `gui/replay_viewer.py` (ReplayViewer split out of `replay_app.py` at the 150-line gate),
  `--game-params` flag; `test_log_artifact_reachability.py` split at the same gate
  (ledger pins → `test_ledger_reachability.py`, scanner → `reachability_helpers.py`).
- Uncommitted by design: `config/*/games_played.json` counters (rule-38 territory, human's
  value to declare), `.git/info/exclude` keeps `game_artifacts/` out of status locally.

## Command(s) run

```
uv run python -m pursuit.main --config-dir config/police   # + config/thief, per machine
uv run python -m pursuit.gui.replay_app --artifact game_artifacts/thief/log_27d792b0674c959a_g01.json --step-ms 800 --game-params config/thief/game_params.json
uv run pytest -q                                            # full gate at commit
```

## Result

**Remote rehearsal (machine A on phone hotspot, machine B on wired — the league topology):**

- `ad768afae5865bc2` 15:56 — A=police, B=thief through both tunnels. Capture turn 7,
  `audit_verdict matched=true` both sides. A ran template hints (`ANTHROPIC_API_KEY` unset —
  attempt-3's lesson repeated); B declared `claude-haiku-4-5`.
- Failed seat-swap attempt ~16:23 — `turn=0 thief illegal_transition handshake->handshake`,
  then `httpx.RemoteProtocolError` → `anyio.BrokenResourceError` crash. Root cause: B's
  standalone ngrok still forwarded 8002 while B's police bound 8001; B→A worked, A→B dead.
- `27d792b0674c959a` 16:35 — seats swapped (A=thief), after `ngrok http 8001`. Capture turn 7,
  `agreed=true`, **12 LLM calls, 6,962 in + 240 out = 7,202 tokens** (3.6% of the 200k ceiling)
  — live language layer proven in production. Both seat orientations + both tunnel
  directions now rehearsed; six-game series judged unnecessary.

**League simulation, final duo (n=500/pairing, league board):**
US **102.38** · STRONG (our cop + ES thief) 94.75 · MEDIUM 61.57 · WEAK 55.86.

**Two final strategy rejections, both by measurement:**

- Endgame tablebase: loss attribution over 2,000 games — **0 of 1,294 captures occurred at
  cop quota zero** (303 vs sealing chaser, 991 vs run-2 cop, all with quota in hand). The
  quota-0 endgame the tablebase would solve exactly never arises; competent cops keep
  barriers as standing rule-46 threats and win mid-game.
- KL2 two-step trap leaf: A/B n=1,000/cell — sealing 70.5% vs 69.7%, no-seal 85.5% vs 84.4%,
  run-2 cop 1.1% vs 1.0%; all inside the intervals. The root's one-ply matrix already prices
  two-step traps (distance-1 successors are terminal), so extra leaf foresight re-labels
  states the equilibrium already avoids.

**Gate at commit:** ruff 0 violations; line gate clean after the two splits; suite
**2,601 passed, 2 failed** — both `test_artifact_dir_hygiene`, caused by this machine's
deliberate `.git/info/exclude:22 game_artifacts/` (verified with `git check-ignore -v`);
they pass on any clean checkout.

## Decisions / fixes

- **Thief declared done evolving**, with receipts: shipped = rule-46 terminal leaf +
  evidence-gated adaptive mode + v2 seed-bank vector (70.5% sealing / 85.5% pure pursuit,
  from 30%/43% pre-run-3); rejected = depth-2 backup (46→23%), noisy-ES protocol,
  endgame tablebase (0/1,294), KL2 (null). Remaining sealing losses are simultaneous-move
  coin flips at trap boundaries — irreducible variance.
- **Cop frozen at ceiling** (100%/98.9% on all league cells) — no measurable loss mode to
  target; reopen only if a real league game shows one.
- Seat-swap operational rule for the runbook: B's standalone ngrok must be restarted per
  seat (8002 thief / 8001 police); A's pyngrok follows `--config-dir` automatically.
- `ANTHROPIC_API_KEY` loads via the `.env` one-liner in the launch window, both machines —
  no dotenv loader exists on purpose.

## Side-notes (not blockers)

- Robustness gap found by the failed swap: a broken MCP client session poisons subsequent
  sends (`BrokenResourceError` escapes the retry ladder) and crashes the agent instead of
  degrading to opponent-unresponsive handling. A flaky league opponent could trigger it.
  Candidate fix: rebuild the client session on `BrokenResourceError`, bounded by the
  existing retry budget.
- The replay viewer at 12,479 graph nodes exceeds graphify's HTML viz limit; `graph.json` +
  `GRAPH_REPORT.md` refreshed, `graph.html` intentionally absent.
- Machine B does not yet have `0d180ed` (board replays) — push/pull is the human's call.
