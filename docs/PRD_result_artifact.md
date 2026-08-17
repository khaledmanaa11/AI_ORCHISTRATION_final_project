# PRD — the `result_` artifact (the mandatory emailed report)

Per-mechanism PRD required by [CLAUDE.md](../CLAUDE.md) §2.3 / Segal §2.3, for the
mechanism implemented in `src/pursuit/services/reporting/artifact_result.py` and
`result_artifact_fields.py`. Written by plan 07-07.

Companion PRDs: [PRD_log_artifact.md](PRD_log_artifact.md) (the per-sub-game journal this
report points at), [PRD_gatekeeper.md](PRD_gatekeeper.md) (the chain the report leaves
through).

---

## 1. What it is

`result_<game_id>.json` — [docs/PARAMETERS.md](PARAMETERS.md):168:

> Final results summary across all sub-games. **This is the mandatory report emailed to
> the lecturer.**

It is the only one of the four required artifacts that is also a *transmission*. Rule 32
([docs/RULES.md](RULES.md):73) disqualifies the points of any game it is missing for, and
rule 35 (:76) scores **0 for both teams** when one team fails to report or the two reports
contradict each other.

## 2. OQ-4 — one file per series, emailed after every sub-game

**This is an interpretation, recorded as one.** Neither document states the shape in as
many words, and the two constraints pull in different directions:

| Source | Says |
|---|---|
| `PARAMETERS.md:168` | `result_<game_id>.json` — **no** `_g<NN>` suffix, and "across all sub-games" ⇒ ONE aggregate file per series |
| `RULES.md:73` (rule 32) | results reported automatically by mail, sanctioned **per game**: "No report → the points from that game are disqualified" |
| `PARAMETERS.md:152-153` (mandatory rule 5) | "**every game** requires an email to the lecturer carrying the **GitHub commit hash** the code ran on for that game" |

**Resolution:** one series file, durably rewritten (with `.prev` rotation) after each
sub-game, and **emailed each time**. PARAMETERS gets its single aggregate file; rule 32's
per-game sanction becomes unreachable because a mail goes out at every game end; mandatory
rule 5 is met because each sub-game entry carries its own `commit_hash` and the newest one
is also lifted to the top level.

Cross-check that the naming half is not our invention: `artifact_names.py` already fixes
`_g<NN>` as **present** on `config_`/`log_` and **absent** on `declaration_`/`result_`, and
`tests/unit/test_artifact_names.py` transcribes that table from the document.

## 3. Rule 54 — and why the series total cannot come from `budget.report()`

Rule 54 (`RULES.md`:103): *"Report in the final JSON the total tokens consumed in the game
(and across the series)."* Two numbers, and only one of them exists in this process.

Measured, not assumed:

| Fact | Where |
|---|---|
| `Gatekeeper.__init__` constructs a **fresh** `TokenBudget` per instance | `services/llm/gatekeeper.py:81` |
| the gatekeeper is constructed **once per process** | `network/language_wiring.py` (`build_language_runtime`) |
| "A fresh instance per series only — never a shared live object" | `services/llm/budget.py:44-52` |

Two games are two processes, therefore two budgets, therefore `report()` returns **this
game's** spend and nothing more. The series total is *the previous `result_` file's series
total plus this game's* — which is exactly why §2's one-durable-file-per-series shape is
load-bearing rather than cosmetic.

A per-game figure printed in the series slot is a false report under rule 54, and it is
**invisible to a single-game test**: with one game played, per-game and per-series are
equal. The test that carries this requirement therefore drives **two** sub-games and
asserts the series total is *strictly greater than either* and *equal to their sum*.

`accumulate_series` also refuses to absorb an unmeasured game: a sub-game whose
`tokens.present` is false leaves the running total and `games_measured` untouched, so the
series figure never rests on a zero nobody measured.

## 4. The honest absences

Two fields are deliberately **not** numbers, following `step0_collect._collect_gpu`'s house
rule (an honest `{"present": false, "detail": …}` rather than a fabricated reading) and
`turn_language.py`'s belief snapshot ("an honest 'not run', never fabricated"):

- **`sub_games[].tokens`** — `{"present": false, …}` when `agent_context.language` is
  `None`. A game played with the language layer off spent no tokens *that we measured*;
  reporting `0` would present an absence as a measurement.
- **`games_played_declared`** — `{"present": false, …}` always, in this plan. 07-00 fixed
  the rule-37/38 counter **mechanism** and deliberately left its **value** to a human
  decision at 07-10 (`docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md`). Rule 38 makes a
  false games-played declaration an **absolute disqualification**, so no code path here
  chooses it, defaults it, or reads around it. This game's declared figure lives in
  `declaration_<game_id>.json`, where Step-0 signed it.

## 5. The seal

`result_digest` = `artifacts.artifact_digest(sealed_body(artifact))` — SHA-256 over
`config_hash.canonical_json`, the project's ONE serializer (D-46/QUAL-02).

The sealed set is **stricter** than `log_artifact_fields.SEALED_FIELDS`: it includes the
`game_uid`/`game_id` header. This is the emailed report, and its `game_id` is what files it
against a game (rules 32/35) — a header outside the seal could be swapped to re-file a real
report against a different game without breaking the digest.

`write_result_artifact` re-reads the FILE and re-checks the seal before returning, the same
promise `write_log_artifact` makes and for the same reason: a `FAILED` verdict on a
grader's screen must never be our own write bug.

## 6. Failure posture

Reading the previous generation goes through `durable_write.load_json_with_fallback`, so a
crash in the rotate/replace window costs the series nothing. A previous file that is
present but unreadable is treated as **absent** rather than raised on — refusing to write
this game's report because the last one is corrupt would hand rule 32 the very game it
sanctions.

## 7. Known limit — `game_id` is currently minted per game, not per series (D7-15)

`agent_entrypoint.run_agent` mints `secrets.token_hex(8)` and then adopts the negotiated id
(D-61), so today's `game_id` identifies **one game**, while `PARAMETERS.md` reads
`game_id` + `<NN>` as *series* + *match within it*. The accumulator here is correct and is
proven over two sub-games sharing a `game_id`; until a series-scoped identifier exists, a
production series will contain exactly one sub-game. Filed as **D7-15** rather than solved
by inventing an id scheme.
