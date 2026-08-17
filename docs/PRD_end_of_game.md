# PRD — the game-end reporting hook

Per-mechanism PRD required by [CLAUDE.md](../CLAUDE.md) §2.3 / Segal §2.3, for
`src/pursuit/services/reporting/end_of_game.py` and `end_of_game_chain.py`. Written by plan
07-07.

Companion PRDs: [PRD_result_artifact.md](PRD_result_artifact.md) (the report this hook
builds), [PRD_log_artifact.md](PRD_log_artifact.md) (the journal it points at).

---

## 1. What it does, and where it sits

At the end of every completed game, in one process, in this order:

1. `write_log_artifact` — `log_<game_id>_g<NN>.json` (07-05)
2. `build_agreement` — rule 35's record, with the `audit_verdict` lifted out of the `log_`
   artifact just written, so the two artifacts cannot disagree about the verdict
3. `record_sub_game` — read the series file, add this sub-game, rewrite it (07-07 Task 2)
4. `ReportingChain.send` — through the Figure-13 chain, `dry_run` (07-01, 07-04)

The call site is `agent_entrypoint.run_agent`, one line after `record_completed_game` and
one line before `return outcome` — **inside the `try`, never the `finally`**. It is a
separate module rather than growth in `agent_entrypoint.py`, following the
`agent_audit_wiring → agent_audit_exchange → agent_audit_verdict` precedent; that file went
from **103** to **107** of its 150 permitted code lines.

`tests/unit/test_end_of_game_wiring.py` is the gate on all of that: presence of the call,
its position between those two lines, its absence from any `finally`, and that exactly one
module in `src/` makes it. Without that gate, deleting the one production call site leaves
every other test in the plan green while no league game ever reports.

## 2. Containment — a reporting failure must not forge a technical loss

Measured: the hook runs inside the try whose `finally` runs `stop_watchdog` →
`linger_for_peer` → `stop_runtime`. An exception raised there propagates out of `_play`,
through `run_with_tunnel` and `run_agent`, to `main.py:58`'s `asyncio.run` — and since
06-05 **a non-zero exit code MEANS an audit mismatch** (`main.py:25-29`).

So `report_game_end` is contained at its own boundary, exactly as `capture_declaration`
swallows `ToolError`: it logs, returns `None`, and never touches `outcome`, `ctx.state` or
the exit code. `except Exception`, never `BaseException` — `CancelledError` must still
propagate, which is the reason `run_agent`'s own `try/finally` exists.

`tests/integration/test_end_of_game_containment.py` drives that branch with real causes
(a declaration with no commit hash; an artifact directory under `logs/`), because the
failing-**sink** case never reaches it: the chain converts a refused send into a
`SendOutcome` and returns it (rules 28-29 — queue, never crash).

## 3. The watchdog: 210 s of ladder inside a 60 s threshold

Full arithmetic and the choice of containment: `end_of_game_chain.py`'s module docstring.
Summary: the freeze watchdog is armed across this whole window
(`agent_entrypoint.py:77`→`:153`) with `os._exit(1)` as its action, and the mail ladder is
`30 × 4 + 30 × 3 = 210 s` against a `60 s` threshold. Chosen containment: **a touch per
bounded attempt** (entry and `finally`, wrapping the sink), not a total bound — a shorter
bound would be an invented number and would also make the mail path give up before rule 32
wants. Largest gap between marks: `max(response_timeout, wait_after_error) = 30 s`.

NET-07 is not traded away, and that is a test rather than a claim: a genuinely frozen
agent — nothing touching — is still killed at the same threshold.

## 4. The artifact directory is per role — a rule-35 fix found on a real game

One `scripts/dev_launch.py` run at commit `4d68886` produced, for a **single** game:

```
game_artifacts/log_1449bfdb473e0faa_g01.json    one seat
game_artifacts/log_1449bfdb473e0faa_g02.json    the OTHER seat, as if a 2nd sub-game
game_artifacts/result_1449bfdb473e0faa.json     role: police, BOTH seats' entries,
                                                games_measured: 2
```

The two agents share a repository and therefore the one configured `artifact_dir`. The
thief wrote its report; the police then read it as "the previous generation of this
series", appended its own entry, and rewrote the file with `role: police`. **The thief's
report was gone**, and `next_sub_game_index` had counted the other seat's `log_` file as a
previous sub-game.

Rule 35 (`docs/RULES.md`:76): *"each team sends its own separate report … Non-reporting …
by **one** team disqualifies the game and scores **0 for both teams**."* That is the shape
of the defect exactly.

**Fix:** this side's artifacts go to `<artifact_dir>/<role>/`, the same per-role split
`agent_lifecycle` already uses for `logs/<role>/`. `reporting.json` is **not** edited — its
`artifact_dir` is the artifact ROOT, and the role subdirectory is derived in code.
`tests/integration/test_end_of_game_two_seats.py` pins it by driving both seats into the
same root, in the order a real run produces, because a test that gave each seat its own
root would pass against the bug.

## 5. The asymmetry rule 21 creates, carried honestly

On a capture, only the **thief** receives a Capture Claim (`capture_declaration`: "The
thief stays silent; it has nothing to declare"). So on the same game the thief records
`agreed: true` and the cop records `agreed: null` **with a stated reason** — an absence,
never an inference. Both still report, which is what rule 35 asks of each team separately.

## 6. Wire truth only

Everything reported is read from this side's own JSONL, its nonce ledger and its Step-0
declaration. No belief, no scent, nothing derived from `ctx.state`: 07-11 closed a rules 8-9
disqualifying leak and a report field must not reopen it.
