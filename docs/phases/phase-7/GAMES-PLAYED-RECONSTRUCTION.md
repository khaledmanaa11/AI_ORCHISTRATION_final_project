# Games-played counter — evidence and reconstruction

*Plan 07-00 · written 2026-08-17 · HEAD at time of measurement `de32c0b`*

> **THIS DOCUMENT DOES NOT SET THE COUNTER, AND NOTHING IN IT MAY BE COPIED INTO
> `config/*/games_played.json` BY AN AGENT.** It assembles the evidence and lays out the
> candidate readings with their derivations so that **a human sets the value at checkpoint
> 07-10, before any live send.** Rule 38 (`docs/RULES.md:79`) makes a false games-played
> declaration an **absolute disqualification**, and what counts as a "game played" is a
> judgement about how this team is represented to the league — being wrong in *either*
> direction is a rule-38 problem. Inventing a value would *be* the violation this work exists
> to prevent.

---

## 1. What the number is for

| Rule / parameter | Text | Consequence |
|---|---|---|
| Rule 37 (`docs/RULES.md:78`) | MUST *"declare accurately, at the start of each game, how many games have actually been played so far"* | *"Threshold condition for computing the true competition factor"* |
| Rule 38 (`docs/RULES.md:79`) | FORBIDDEN to *"falsely declare the number of games played"* | **Absolute disqualification** for an ethical and integrity breach |
| Rule 31 (`docs/RULES.md:72`) | MUST play the minimum number of games against **different** teams | Below the minimum → no passing grade |
| Table 18 row 3 (`docs/PARAMETERS.md`) | `[minimum games]` = **2** | **fixed** |
| Table 18 row 5 (`docs/PARAMETERS.md`) | `[max games per team]` = **10** | **fixed** |
| Table 18 note | *"Against each opponent there is one scoring game only — no rematches for points. Unscored warm-up games are permitted and encouraged (rule 52)."* | — |

The field is transmitted as `games_played_so_far` inside the Step-0 declaration
(`step0_collect.DeclarationField`), read from `config/<role>/games_played.json` before the
handshake and HMAC-signed, so the number a peer sees is the number on disk at launch.

## 2. Why the value on disk cannot be used

Measured directly, twice, at HEAD `de32c0b`, by reading both files immediately before and after
one full `uv run pytest tests/` (1539 passed, 96.64%):

| File | Before | After | Delta | Games actually played |
|---|---|---|---|---|
| `config/police/games_played.json` | 1895 | 1909 | **+14** | 0 |
| `config/thief/games_played.json` | 1888 | 1902 | **+14** | 0 |

Three independent facts each rule the stored value out on their own:

1. **It counts test runs.** +14 per suite run means a value near 1900 is on the order of
   130-plus suite runs of phantom games, plus dev launches and gate measurements.
2. **The two agents disagree by seven** (1909 vs 1902) although they have only ever played each
   other. Two counters of the same team cannot both be right.
3. **It is ~190x a fixed parameter.** `[max games per team]` is **10**, marked *fixed*. A
   declared 1909 contradicts, on its face, a number the same rulebook fixes.

There is no way to recover the true value from history: `config/*/games_played.json` is
gitignored (`.gitignore:80`) and so is `logs/`, so neither the counter's own past nor the local
games it counted are in the repository.

## 3. Independent proof from the retained league evidence

The defect is visible in the *committed* remote-round evidence, not only in the test suite.

`docs/phases/phase-5/remote-round-2026-08-16-attempt4/machineB-thief/eb55daeefafb4208.jsonl`
contains exactly **one** record, in full:

```json
{"event":"watchdog_incident","game_uid":"eb55daeefafb4208","idle_seconds":60,
 "sender":"thief","threshold_seconds":60,"timestamp":"2026-08-16T13:27:41.598567+00:00","turn":0}
```

The freeze watchdog fired at **turn 0**. No move was ever played. Yet
`declaration_eb55daeefafb4208.json` sits beside it — and `write_declaration` is precisely the
function that both wrote that file *and*, at the time, incremented the counter. That run
declared `games_played_so_far = 13` and left machine B's counter at 14 having played nothing.
Machine B's next two declarations read 14 and 15, which confirms the increment landed.

**A game that died before move 1 was counted as a game played, in a real two-machine round, on
disk, in committed evidence.**

## 4. Complete enumeration of games with retained evidence

Every retained remote round, from `docs/phases/phase-5/remote-round-*`. `Completed` applies
07-00's definition: the run reached a non-`None` `Outcome`, which is exactly the path that also
writes a durable `game_over` record.

| # | Date (UTC) | Round | `game_uid` | Machine A (police) | Machine B (thief) | Completed? |
|---|---|---|---|---|---|---|
| 1 | 2026-08-13 13:4x | round 1 | A `074fc2b16888899e` / B `d50ceb00be724b93` | `capture` | `capture` | **Yes**, but each side logged its *own* uid — the pre-05-05 identity defect. One game, two uids. |
| 2 | 2026-08-16 09:33 | attempt 2 | `5efbc5811fabfac4` | no `game_over`, `watchdog_incident` | `technical_loss` | **Split**: B completed (and lost), A did not |
| 3 | 2026-08-16 10:46 | attempt 3 | `9c1cf313482719d4` | `capture` | *evidence not retained* | **A yes**, B unknown |
| 4 | 2026-08-16 13:27 | attempt 4 game 1 | `b22361aa93ccf310` | `capture` | `capture` | **Yes**, both sides |
| 5 | 2026-08-16 13:29 | attempt 4 game 2 | `d265603c116a9f99` | `capture` | `capture` | **Yes**, both sides |
| — | 2026-08-16 13:27:41 | attempt 4, aborted | `eb55daeefafb4208` | — | `watchdog_incident` at turn 0, 1 record | **No** — and it still consumed counter value 13 |
| — | 2026-08-14 | attempt 1 | — | `ERR_NGROK_334`, never launched | — | **No** |

Per role, counting only completed runs with retained evidence:

* **Machine A, police: 4** (rows 1, 3, 4, 5).
* **Machine B, thief: 4** retained (rows 1, 2, 4, 5), **plus row 3** attested but unretained → **4 or 5**.

### What the declarations themselves say the counter was

Each declaration records the value read at launch, so the retained files are a partial timeline.

| Date | Round | Machine A (police) declared | Machine B (thief) declared |
|---|---|---|---|
| 2026-08-13 | round 1 | 173 | 8 |
| 2026-08-16 09:33 | attempt 2 | 875 | 9 |
| 2026-08-16 10:46 | attempt 3 | 990 | 12 |
| 2026-08-16 13:27:41 | aborted run | — | 13 |
| 2026-08-16 13:27:48 | attempt 4 game 1 | 991 | 14 |
| 2026-08-16 13:29:53 | attempt 4 game 2 | 992 | 15 |

Two things follow. **Machine A's counter is dominated by development**: 173 → 875 → 990 across
three days in which four games were played, because machine A is the repository where the suite
runs. **Machine B's counter is close to plausible**: it moved 8 → 15 across the same period, and
its gaps (9 → 12) correspond to runs whose logs were simply not collected. Neither is
independently trustworthy, but they fail in very different ways and by very different magnitudes.

## 5. A second question the value alone does not settle

**Rule 37 asks how many games *the team* has played; the implementation keeps one counter per
role directory per machine.** In attempt 4, one team — `khm-mn17` on both sides of all **19**
retained declaration files — declared **991** as police and **14** as thief *in the same game*.
At most one of those can be "how many games this team has actually played".

This is a design decision, not a value, and it is independent of §6 below. It must be settled at
07-10 as well:

* **(i) Per team** — one shared number for both agents. Matches rule 37's wording. Needs a
  single source both role directories read, which does not exist today and must not become
  shared *runtime* state between the cop and the thief (CLAUDE.md rule 2 / project rule 2 —
  a shared read-only file at rest is fine, a shared live state object is disqualification).
* **(ii) Per agent** — keep two counters and accept that they differ. Simplest, and defensible
  only if a "game played" is read as "game played *by this agent*". A peer or a grader comparing
  the two sides' declarations will see the discrepancy.

## 6. Candidate readings of "a game played", with evidence

Presented for decision. **No option is selected here.**

### Option A — scored league games against different teams

* **Reading:** rule 37 sits directly beside rule 31 ("against **different** teams") and its
  sanction line names the *competition factor*, which is computed from opponents faced.
* **Value implied by the evidence: 0.** All **19** retained declaration files on both sides carry
  `team_code = "khm-mn17"`. No game against another team has been played yet.
* **Bounded by:** Table 18 — at least 2 required for a passing grade, at most 10 permitted.
* **In favour:** it is the only reading under which the declared number can feed a competition
  factor at all, and the only one bounded by a *fixed* parameter.
* **Against:** if the lecturer means "games this software has played", 0 under-declares — and an
  under-declaration is a rule-38 breach exactly as an over-declaration is.

### Option B — every real two-machine round, warm-ups included

* **Reading:** rule 52 permits and encourages unscored warm-ups; a warm-up is still a game the
  software played end to end against a genuine remote peer.
* **Value implied by the retained evidence: 4 for police, 4–5 for thief** (§4). These are
  **lower bounds**, not counts: machine B had already declared 8 on 2026-08-13, meaning eight
  prior runs for which nothing was retained, and machine A's true remote-game history before
  2026-08-13 is likewise unrecorded.
* **In favour:** every one of those games has a log, a ledger, two declarations, and for rows 4-5
  an `audit_verdict matched=true` on both sides.
* **Against:** the two machines disagree about the same games, and the figure is a floor whose
  distance from the truth cannot be measured from committed evidence.

### Option C — every completed game, including localhost self-play

* **Reading:** the counter counts what the agent did, wherever the opponent lived.
* **Value implied by the evidence: unknowable.** `logs/` is gitignored, the counter file is
  gitignored, and the counter itself is the corrupted artifact. There is no durable lower bound.
* **Against:** self-play against one's own second process is not a game against an opponent in
  any sense rule 31 or the competition factor uses, and the resulting number would be both
  enormous and unverifiable by anyone else.

### The bound that applies whatever is chosen

Under Option A the declared value must lie in **[0, 10]** to be consistent with `[max games per
team] = 10` (*fixed*). Under B or C no such bound applies — but then the declared number has
stopped meaning what rule 37's own sanction line says it feeds, which is itself worth stating to
the lecturer rather than silently assuming.

## 7. What plan 07-00 changed, and what it deliberately did not

**Changed — the mechanism.**

* The increment moved out of `write_declaration` (game **start**) into
  `agent_step0_wiring.record_completed_game`, called from `agent_entrypoint.run_agent` after the
  turn loop **and** after the commit-reveal audit. A game is complete exactly when `run_agent`
  is about to return a non-`None` `Outcome`; the derivation is recorded in that function's
  docstring.
* The test suite can no longer reach the shipped counter: `tests/_shipped_config_guard.py`
  raises `ShippedConfigWriteError` **before any byte is written**, installed session-wide and
  autouse by `tests/conftest.py`, which additionally snapshots both real files across the
  session. It raises rather than redirecting, so the next occurrence of this defect class is
  loud instead of hidden.
* Measured after the fix: a full `uv run pytest tests/` advances both counters by **zero**
  (police 1910 → 1910, thief 1903 → 1903); `uv run python scripts/dev_launch.py` plays one real
  game and advances each by exactly **one** (1909 → 1910, 1902 → 1903).
* `docs/phases/phase-6/GATE-6-MEASUREMENT.md` no longer certifies the inflation as correct
  behaviour.

**Deliberately not changed — the value.** As this document is written the two files read
**1910** (police) and **1903** (thief) — the +1 each from the single verification game above,
on top of the 1909 / 1902 the defect had already accumulated. They are wrong, they are known to
be wrong, and 07-00 leaves them exactly as it found them.

## 8. Decision required at 07-10, before any live send

- [ ] Choose the reading of "a game played" — §6 Option A, B, or C, or a stated alternative.
- [ ] Choose per-team or per-agent counting — §5 (i) or (ii).
- [ ] Set `config/police/games_played.json` and `config/thief/games_played.json` accordingly,
      **by hand**, and record the reasoning beside the value.
- [ ] Re-run `uv run python scripts/dev_launch.py` afterwards and confirm the counters advance
      by exactly one each, so the value that ships is the value that was chosen plus real games.
- [ ] If any doubt remains about the reading, **ask the lecturer before the first league game** —
      rule 38's sanction makes a question far cheaper than a guess.

---

*Nothing downstream of this document — any writer or transmitter of
`declaration_<game_id>.json` — should ship before these boxes are ticked.*
