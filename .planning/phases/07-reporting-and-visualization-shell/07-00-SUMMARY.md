---
phase: 07-reporting-and-visualization-shell
plan: "00"
subsystem: security/step0-declaration
tags: [rule-38, disqualification-risk, games-played, counter-integrity, test-isolation, REPORT-01, SEC-07, DOC-01]
one_liner: "The one number in this project whose sanction is absolute disqualification counted agent starts and test runs instead of games -- a full pytest run advanced it by 14 -- and Phase 7 was about to transmit it to the lecturer; the mechanism is now honest, the suite advances it by zero, a Phase-6 document that certified the bug as correct behaviour is withdrawn, and the VALUE is deliberately left unset for the human."
requires:
  - "Nothing. Wave 0 -- everything in phase 7 that writes or transmits declaration_<game_id>.json depends on THIS."
provides:
  - "agent_step0_wiring.record_completed_game(cfg, outcome): the rule-38 WRITE, separated from declare_step0's game-START READ so the two can never be confused again"
  - "tests/_shipped_config_guard.py + conftest wiring: the suite cannot reach config/{police,thief}/games_played.json, and FAILS LOUDLY if it tries"
  - "docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md: the evidence and the candidate readings, with NO option selected"
  - "docs/phases/phase-6/GATE-6-MEASUREMENT.md: the false claim withdrawn in place, the original paragraph preserved byte-for-byte beneath it"
status: complete
---

# 07-00 — the number we were about to publish was false

## Why this plan existed

Rule 38 (`docs/RULES.md:79`): *"Falsely declare the number of games played → **Absolute
disqualification** for an ethical and integrity breach."* It is the harshest sanction in the
rulebook, and Phase 7 is the phase that puts the number in front of the lecturer, inside
`declaration_<game_id>.json`.

The number was wrong.

## The two defects, measured

**Defect 1 — wrong moment, and the code said so against itself.**
`step0_collect.record_game_played`'s docstring has always read *"increment by exactly one,
durably, **at game end only**"*. It was called from `agent_step0_wiring.py:93`, inside the Step-0
**declaration** path, which runs at game START. Aborted handshakes, watchdog kills, and games that
never reached an outcome were all counted.

**Defect 2 — wrong scope.** The path derives from `cfg.config_dir`, and the test suite runs
against the real `config/police/`, so every `pytest` run mutated production state.

Measured before any change:

```
config/police/games_played.json  = 1881
config/thief/games_played.json   = 1874
one `uv run pytest tests/` run   -> 1895 / 1888      (+14 to each)
```

~1881 is therefore on the order of 134 test runs of phantom games, plus dev launches and gate
measurements. Independent proof it never counted games: two agents that only ever played *each
other* stood 7 apart.

## The fix

`record_completed_game(cfg, outcome)` is now a separate function from `declare_step0`, so rule
38's WRITE and the declaration's READ cannot be conflated again; what "completed" means is read
off the two functions that actually end a game and recorded in-source rather than assumed. The
test seam is closed **structurally** by `tests/_shipped_config_guard.py` — a test that reaches for
the shipped counter fails loudly rather than being silently redirected, because a silent redirect
would hide the next instance of exactly this bug.

## The headline measurements — verified by the orchestrator, not claimed

```
FULL SUITE     before cop=1910 thief=1903   after cop=1910 thief=1903   DELTA 0 / 0
               (1557 passed, coverage 96.65%)

ONE REAL GAME  before cop=1910 thief=1903   after cop=1911 thief=1904   DELTA 1 / 1
               (`uv run python scripts/dev_launch.py`, exit 0)
```

Was +14 per test run. Is now 0. One real game costs exactly one.

## The document that kept the bug alive

`docs/phases/phase-6/GATE-6-MEASUREMENT.md:178-184` asserted the inflation was *"the shipped,
correct behavior of the counter, not a bug this script introduces"*. That is why it survived: a
document certifying a bug as intentional turns every future reader away at the door.

Withdrawn in place with a dated correction; the original paragraph is preserved byte-for-byte
beneath it as the record of what was believed on 2026-08-09, and nothing measured elsewhere in
that document is affected. Attempts and measurements here are append-only — but a **statement of
fact that is wrong gets corrected** rather than left to mislead. Rule 38 cuts both ways.

## What this plan deliberately did NOT do

**It did not set the counter value, and that was the point.**

Whether a "game played" means league games only, any real two-machine round, or local self-play is
a judgement about how the *user* is represented to the league. Being wrong in either direction is
the same rule-38 breach, and the file is gitignored so git history cannot settle it. Inventing a
number would have *been* the violation this plan exists to prevent.

`docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md` lays out the evidence — the four retained
remote-round directories, attempt 4 holding two games — and the candidate readings with their
derivations. It states plainly: **"No option is selected here."** The value is set by the human at
checkpoint **07-10, before any live send**.

## Deviation

The executing agent was killed by a connection error (`ECONNRESET`) during its final combined gate
run, after all three task commits had landed and the tree was clean. The orchestrator re-ran both
headline measurements from scratch rather than inheriting them, confirmed the two document
corrections on disk, and wrote this SUMMARY and the STATE update — the only work the crash cost.
No task was re-executed and no commit was replayed.

## Commits

- `8e1f355` — test(07-00): pin both games-played defects, RED, with measured numbers
- `51b1f9b` — fix(07-00): count completed games only, and close the test seam structurally
- `ab50b6b` — docs(07-00): withdraw the Phase-6 claim that certified the bug, and reconstruct the evidence

## Open, and owned by the human

The counter value itself, at 07-10. Until then no declaration should be transmitted anywhere.
