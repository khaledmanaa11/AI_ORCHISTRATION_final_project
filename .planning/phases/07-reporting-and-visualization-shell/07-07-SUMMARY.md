---
phase: 07-reporting-and-visualization-shell
plan: "07"
subsystem: services/reporting-end-of-game
tags: [D-75, D7-1, D7-13, D7-14, D7-17, D7-18, OQ-4, OQ-5, REPORT-01, REPORT-06, REPORT-07, rule-21, rule-32, rule-35, rule-38, rule-53, rule-54, NET-07]
one_liner: "result_<game_id>.json as ONE durable file per series whose token total is accumulated IN the file -- proven by a mutation that passes 9/9 against single-sub-game tests and fails only over two; a three-valued rule-35 agreement that records null-with-a-reason rather than inventing agreement; a game-end hook contained so no reporting failure can forge a technical loss, touching the freeze watchdog once per bounded attempt across a 210 s ladder under a 60 s threshold; and a rule-35 disqualifier found by running one real game, where both seats shared one artifact directory and the thief's report was eaten"
requires:
  - "07-01: ReportingChain / QuotaManager / DosDetector / load_reporting_config / the shipped dry_run reporting.json"
  - "07-02: artifact_header, artifact_digest, write_artifact (D7-1's logs/ refusal), result_filename, next_sub_game_index"
  - "07-04: DryRunSink, MailSink, report_filename, render_message"
  - "07-05: write_log_artifact and the LogArtifactField.AUDIT_VERDICT summary it carries"
provides:
  - "services/reporting/result_agreement.py + _fields.py: build_agreement, AgreementRecord, the five named reasons -- rule 35's three-valued record"
  - "services/reporting/artifact_result.py + result_artifact_fields.py: record_sub_game / build / verify / write, game_tokens, accumulate_series -- rule 54's two numbers"
  - "services/reporting/end_of_game.py: report_game_end -- THE game-end hook, contained"
  - "services/reporting/end_of_game_chain.py: build_reporting_chain, watchdog_touching, QUOTA_FILENAME"
  - "docs/PRD_result_artifact.md, docs/PRD_end_of_game.md: the two per-mechanism PRDs (CLAUDE.md Sec2.3)"
affects:
  - "07-08 reads result_ beside log_; its verdict screen can quote agreement.audit_verdict, which is byte-identical to the log_ artifact's"
  - "07-09 measures GATE-7 criterion 1 against the artifacts this hook writes to <artifact_dir>/<role>/"
  - "07-10 flips ONE reporting.json to live for one supervised send, and sets the games-played VALUE this artifact leaves unset"
tech-stack:
  added: []
  patterns:
    - "Accumulate a cross-process running total IN the durable artifact, never in a per-process object -- and prove it with >= 2 iterations, because one iteration cannot distinguish the two"
    - "A three-valued claim (true/false/null-with-a-reason) wherever a two-valued one would have to invent the missing half"
    - "A wiring GATE on the single production call site: presence, position between two named lines, and absence from any finally -- asserted on the AST, not on source offsets"
    - "Run the real thing once before believing the tests: dev_launch found a rule-35 disqualifier no unit test could have posed"
key-files:
  created:
    - src/pursuit/services/reporting/result_agreement.py
    - src/pursuit/services/reporting/result_agreement_fields.py
    - src/pursuit/services/reporting/artifact_result.py
    - src/pursuit/services/reporting/result_artifact_fields.py
    - src/pursuit/services/reporting/end_of_game.py
    - src/pursuit/services/reporting/end_of_game_chain.py
    - docs/PRD_result_artifact.md
    - docs/PRD_end_of_game.md
    - tests/unit/result_agreement_fixtures.py
    - tests/unit/test_result_agreement.py
    - tests/unit/test_result_agreement_edges.py
    - tests/unit/test_artifact_result.py
    - tests/unit/test_artifact_result_edges.py
    - tests/unit/test_end_of_game_chain.py
    - tests/unit/test_end_of_game_wiring.py
    - tests/integration/end_of_game_harness.py
    - tests/integration/test_end_of_game_reporting.py
    - tests/integration/test_end_of_game_message.py
    - tests/integration/test_end_of_game_watchdog.py
    - tests/integration/test_end_of_game_containment.py
    - tests/integration/test_end_of_game_two_seats.py
  modified:
    - src/pursuit/network/agent_entrypoint.py
    - src/pursuit/services/reporting/__init__.py
    - tests/unit/test_log_artifact_reachability.py
    - docs/phases/phase-7/TODO.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "OQ-4 carried verbatim: ONE result_ per SERIES, durably rewritten with .prev rotation after each sub-game and emailed each time -- recorded as an INTERPRETATION with both citations"
  - "The series token total is accumulated in the durable file, never from budget.report(): one budget is one process is one game"
  - "`agreed` is true / false / null-with-a-stated-reason, never inferred; a malformed peer claim is a NAMED non-agreement rather than an exception"
  - "The watchdog gets a touch per bounded attempt rather than a total bound, because a shorter bound would be an invented number and would give up before rule 32 wants"
  - "The artifact directory is per role -- a rule-35 fix found on a real game, not a tidiness preference; reporting.json is not edited, its value is the artifact ROOT"
  - "Games-played is emitted as an explicit absent marker carrying its own reason; 07-10 owns the value"
metrics:
  tasks: 3
  commits: 6
  tests_added: 43
  suite: "2047 -> 2090 passed, 0 failed"
  coverage: "97.19% -> 97.29%"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 07: End-of-Game Reporting and `result_` Summary

Rule 35 scores **0 for both teams** when one side fails to report, and rule 32
disqualifies the points of any game that goes unreported. This plan builds the file
that is reported and the single call site that reports it — the most
submission-critical call site in the codebase, and therefore the one most carefully
prevented from touching anything else.

---

## 1. The two facts this plan was written around, and what happened to each

**The outline said the series token total comes from `ctx.language.gatekeeper.budget.
report()`. It cannot.** `Gatekeeper.__init__:81` builds a fresh `TokenBudget` per
instance, `language_wiring.build_language_runtime` builds the gatekeeper once per
PROCESS, and `budget.py:44-52` states "A fresh instance per series only". Two games
are two processes and therefore two budgets, so `report()` only ever holds THIS
game. The series total is accumulated **in the durable `result_` file** — which is
precisely what makes OQ-4's one-file-per-series shape load-bearing rather than
cosmetic.

**OQ-4 was carried verbatim** and is recorded in `docs/PRD_result_artifact.md` §2 as
an INTERPRETATION with both citations: `PARAMETERS.md:168` names
`result_<game_id>.json` with no `_g<NN>` and calls it the summary "across all
sub-games"; rule 32 (`RULES.md:73`) sanctions per game. One series file, durably
rewritten with `.prev` rotation, emailed each time.

## 2. The measurement that makes the accumulation a proof, not a claim

Two sub-games written against the same series file:

| | input | output | **total** |
|---|---|---|---|
| sub-game 1 | 100 | 40 | **140** |
| sub-game 2 | 7 | 3 | **10** |
| **series** | **107** | **43** | **150** |

`150 > 140`, `150 > 10`, and `150 == 140 + 10`. The assertion is strict, not `>=`:
an implementation that writes `report()` into both slots passes `series >= game`
whenever the later game is the larger one.

**And here is why one game proves nothing.** The same mutation —
`accumulated = {name: _count(tokens, name) ...}`, i.e. the previous file's total
dropped — measured twice:

```
probe 2         (both test files, incl. the two-sub-game cases)   2 failed, 11 passed
probe 2-single  (THE SAME mutation, single-sub-game tests only)   0 failed,  9 passed
```

A suite that never drives a second sub-game reports a green build against a token
figure that silently under-reports the series, under rule 54.

## 3. Task 1 — the agreement record, and the asymmetry it must not smooth

`capture_declaration.declares_capture` sends `GAME_OVER` only when the outcome is a
capture **and this side is the cop** — "The thief stays silent; it has nothing to
declare". So on a survival game no peer claim exists on either side, and even on a
capture only the **thief** receives one. Measured on the real `dev_launch` game
`a5dd2a98827f4df5`:

| | own_outcome | peer_outcome | peer_claim_present | **agreed** |
|---|---|---|---|---|
| police | `capture` | `null` | `false` | **`null`** + `NO_PEER_CLAIM` |
| thief | `capture` | `capture` | `true` | **`true`** |

An implementation writing `agreed = own == peer` with `peer` defaulted to `own`
prints `agreed: true` on the police seat of every game ever played. That is a
fabricated agreement under the one rule whose sanction is zero for both teams.

The four plan cases, each a test, plus the `security/audit.py` boundary shapes:

| case | input | result |
|---|---|---|
| (a) | honest agreeing capture | `true` |
| (b) | peer claims `survival`, we resolved `capture` | `false` **and a full record still emitted** |
| (c) | no peer claim at all | `null` + a stated reason, asserted **not** `true` |
| (d) | `"we won on style"` / `42` / a non-dict payload | a NAMED non-agreement, never a `ValueError` |

**The audit verdict is passed IN**, lifted out of the `log_` artifact this hook has
just written, so the two artifacts cannot disagree about the verdict — verified on a
real game (`{"matched": true, "turn": 5}` on both seats, equal by `==`).

## 4. Task 3 — the watchdog arithmetic, and which containment was chosen

The freeze watchdog is armed from `agent_entrypoint.py:77` to `:153`, with
`os._exit(1)` as its action. The hook sits inside that window.

```
watchdog_threshold                                              60 s
response_timeout_seconds x (retries_before_failure + 1) 30x4 = 120 s
wait_after_error_seconds x retries_before_failure       30x3 =  90 s
------------------------------------------------------------------
worst-case reporting window                                    210 s   = 3.5x
```

**Chosen: a touch per bounded attempt** (entry and `finally`, wrapping the sink),
not a total bound. A bound short enough to fit under 60 s would be a **new number** —
every figure above is a Table-19 row read from `reporting.json` — and it would also
make the mail path give up before rule 32 wants. Wrapping the sink is per-attempt by
construction: `Gatekeeper._call_with_retry` invokes it exactly once per attempt and
sleeps the backoff between. Largest gap between marks:
`max(response_timeout, wait_after_error) = 30 s`.

Driven on an injected clock, **zero real sleeps**: 4 attempts ran, `armed.clock.now`
reached exactly `210.0`, `armed.checks` recorded more than one poll, `True not in
armed.checks`, `armed.fired == []`, and the report was still owed on the queue.

**NET-07 is not traded away, and that is two tests rather than a sentence.** The same
ladder with `watchdog_touching` deliberately bypassed **is** killed
(`fired[:2] == ["freeze", "exit"]`), and a genuinely frozen agent — nothing touching —
is still killed at the same threshold, while one touch inside the window still saves
it.

## 5. What a real game found that no unit test could have posed

`dev_launch.py` at commit `4d68886`, exit 0, one game:

```
game_artifacts/log_1449bfdb473e0faa_g01.json     one seat
game_artifacts/log_1449bfdb473e0faa_g02.json     the OTHER seat, as if a 2nd sub-game
game_artifacts/result_1449bfdb473e0faa.json      role: police, BOTH seats' entries,
                                                 games_measured: 2
```

The two processes share a repository and therefore the ONE configured `artifact_dir`.
The thief reported first; the police then read the thief's file as "the previous
generation of this series", appended its own entry and rewrote it with `role:
police`. **The thief's report was gone** — and `next_sub_game_index` had counted the
other seat's `log_` file as a previous sub-game.

Rule 35: *"each team sends its own separate report … Non-reporting … by **one** team
disqualifies the game and scores **0 for both teams**."* That is the defect exactly.

**Fixed** to `<artifact_dir>/<role>/`, the split `agent_lifecycle` already uses for
`logs/<role>/`. `reporting.json` is **not** edited — its value is the artifact ROOT
(`git diff` on both files is empty; both still `dry_run`). Re-run at the fix:

```
game_artifacts/police/log_a5dd2a98827f4df5_g01.json   result_a5dd2a98827f4df5.json (+ .eml)
game_artifacts/thief/ log_a5dd2a98827f4df5_g01.json   result_a5dd2a98827f4df5.json (+ .eml)
```

Two separate reports, **one sub-game each**, `games_measured: 1` each, both logs
`_g01`, each carrying its own `role`. `test_end_of_game_two_seats.py` pins it by
driving both seats into the **same** root in run order — a test that gave each seat
its own root would pass against the bug — and probe 15 (the fix reverted) fails 2.

## 6. Revert probes — eighteen numbered, twenty-two runs, every count real

Four of the eighteen carry a variant (1b/1c/1d and 2-single), so the table has 22 rows.

Anchor asserted present, mutation asserted landed, source restored and re-compared
afterwards (07-04's discipline).

| # | Mutation | Result |
|---|---|---|
| 1 | `peer_outcome` defaults to `own_outcome` (the plan's named revert) | **6 failed, 3 passed** |
| 1b | …with the `present` guard kept | **1 failed, 8 passed** |
| 1c | the malformed-claim guard removed (`Outcome()` raises through) | **2 failed, 7 passed** |
| 1d | the three-valued verdict collapsed to a two-valued equality | **5 failed, 4 passed** |
| 2 | the series accumulation removed | **2 failed, 11 passed** |
| **2-single** | **the SAME mutation, single-sub-game tests only** | **0 failed, 9 passed** |
| 3 | the absent-tokens marker replaced by zeros | **2 failed, 11 passed** |
| 4 | `games_measured` advanced for an UNMEASURED game | **2 failed, 11 passed** |
| 5 | the header dropped out of the seal | **1 failed, 12 passed** |
| 6 | the post-write seal re-check removed | **1 failed, 12 passed** |
| 7 | the durable writer swapped for a plain write (no `.prev`) | **1 failed, 12 passed** |
| 8 | the hook's containment removed | **2 failed, 11 passed** |
| 9 | the watchdog touch removed from the sink wrapper | **2 failed, 11 passed** |
| 10 | the `audit_verdict` not carried from the `log_` artifact | **1 failed, 12 passed** |
| 11 | the token budget never read | **1 failed, 12 passed** |
| 12 | the no-outcome early return removed | **1 failed, 12 passed** |
| 13 | the ONE production call site deleted | **3 failed, 11 passed** |
| 14 | the call moved into the teardown `finally` | **2 failed, 12 passed** |
| 15 | the per-role artifact directory reverted (the `4d68886` bug) | **2 failed, 6 passed** |
| 16 | D7-1's `logs/` refusal removed | **1 failed, 2 passed** |
| 17 | the quota path aimed at the shipped `config/` tree | **1 failed, 3 passed** |
| 18 | the absent-tokens marker given a zero count | **1 failed, 12 passed** |

Probe 8 answers the plan's question directly: **removing the containment fails
neither (a) nor (b) nor (c)** — it fails only the two dedicated containment cases,
because the failing-**sink** path never reaches that branch (the chain converts a
refused send into a `SendOutcome`). Without `test_end_of_game_containment.py` the
`except` clause would have been an untested branch.

Probe 9 is the paired pair the plan asked for: (c) dies while the frozen-agent
control and the bypass control both still pass.

## 7. Four holes the self-audit found in my own work

**1. Probe 14 first failed only 1, and the assertion that should have caught it was
wrong-SHAPED.** `test_the_hook_is_not_in_the_teardown_block` compared
`source.index("await report_game_end(")` against `source.index("stop_watchdog(ctx)")`
— and the mutation that moves the call to the **top of the very `finally`** it
forbids still satisfies that ordering. Rewritten on the AST (`ast.Try.body` vs
`.finalbody`); probe 14 now fails 2.

**2. `assert tokens != 0` measured nothing** — a dict never equals an int. Replaced
by "no non-`bool` integer appears in the absence marker at all". The **second** draft
(`0 not in tokens.values()`) failed too, because `present: False` **is** `0` under
`==` — this repository's own recurring `bool`-is-an-`int` trap, arriving in my test
rather than in my source. Probe 18 now fails 1.

**3. `assert not (forbidden / result_filename(...)).exists()`** in the `logs/`
refusal case checked a path that could never exist once artifacts moved to
`<root>/<role>/`. Replaced by `not forbidden.exists()` — an unrefused write would
have `mkdir(parents=True)`d its way there.

**4. The chain-construction test asserted only that `QUOTA_FILENAME` ends in
`.json`.** It now performs a send and looks for the file, so a quota path aimed at
the shipped `config/` tree fails (probe 17) instead of passing. That probe also
surfaced **D7-18**: the session guard covers `games_played.json`'s writer, not
`durable_write_json` itself, so nothing structural stops a *different* writer
reaching `config/`.

**AST scan** over all 13 new test/fixture files: **0 `parametrize` sites**, **4
assert-bearing loops**, every one floored — `shapes` by `== 2`, `seats` by
`len(seats) == 2`, `reports` by an exact `roles == ["police", "thief"]`, and
`agreements.items()` by `set(agreements) == {"police", "thief"}`.

**Production-caller grep** for all 25 new public names: every one has a reference in
`src/` outside its defining module, and `report_game_end` reaches
`network/agent_entrypoint.py`. D7-14 is closed, and
`test_log_artifact_reachability.py` now NAMES the `log_` builder's five reachers so
its empty-list assertion cannot be green because the builder is dead code.

## 8. Gates

```
uv run ruff check .                          All checks passed        (0 violations)
bash scripts/check_line_limit.sh             exit 0                   (tracked)
  + all 19 new .py files explicitly by path  exit 0
uv run python scripts/check_no_llm_in_strategy.py   OK: no forbidden imports
uv run python scripts/check_local_truth.py          OK: 5 modules scanned, no violations
uv run pytest tests/ --cov                   2090 passed, 0 failed    (baseline 2047)
                                             coverage 97.29%          (baseline 97.19%)
uv run python scripts/dev_launch.py          exit 0                   (a5dd2a98827f4df5)
  both seats                                 audit_verdict matched=true @ turn 5
  watchdog_incident 0 / technical_win 0       on BOTH seats
git diff config/{police,thief}/reporting.json   empty; both still "dry_run"
git check-ignore, every new .py + both PRDs  not ignored (D7-10's guard)
graphify update .                            10027 nodes / 17957 edges / 575 communities
  report_game_end -> end_of_game.py L89 (deg 16)
  record_sub_game -> artifact_result.py L147 (deg 9)
```

File sizes, all <= 150 code lines. **`agent_entrypoint.py`: 103 -> 107.**

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `artifact_result.py` | 145 | | `test_artifact_result.py` | 128 |
| `result_artifact_fields.py` | 143 | | `test_end_of_game_reporting.py` | 88 |
| `end_of_game.py` | 142 | | `test_end_of_game_watchdog.py` | 104 |
| `result_agreement.py` | 122 | | `test_result_agreement.py` | 87 |
| `end_of_game_chain.py` | 103 | | `test_end_of_game_two_seats.py` | 79 |
| `result_agreement_fields.py` | 75 | | `test_end_of_game_chain.py` | 84 |
| `__init__.py` | 146 | | `end_of_game_harness.py` | 54 |

All five new source modules are at **100%** coverage; so is every other module in
`services/reporting/`.

### Rule-38 counters — all four numbers, read directly (the files are gitignored)

| | police | thief |
|---|---|---|
| before full `pytest` | 1920 | 1913 |
| after full `pytest` | **1920** | **1913** |
| **suite delta** | **0** | **0** |
| before `dev_launch.py` | 1919 | 1912 |
| after `dev_launch.py` | **1920** | **1913** |
| **one-real-game delta** | **1** | **1** |

**Nothing in this plan sets, defaults or infers the games-played VALUE.** The
artifact carries `games_played_declared: {"present": false, "detail": …}` naming
`docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md` as the source and
`declaration_<game_id>.json` as where this game's declared figure actually lives.
`reporting.mode` stays `dry_run` in both shipped configs; **nothing transmitted**.

## 9. Deviations from Plan

### Auto-fixed

**1. [Rule 1 — bug] The two seats shared one artifact directory — a rule-35
disqualifier.** §5. Found by running `dev_launch.py`, not by reasoning. Commit
`5aa9ec1`.

**2. [Rule 3 — blocking] Four source files split at the 150-code-line gate, and two
PRDs written.** `result_agreement.py` measured 161 → `result_agreement_fields.py`;
`artifact_result.py` measured 168 → `result_artifact_fields.py` **and**
`docs/PRD_result_artifact.md` (the `PRD_log_artifact.md` precedent — CLAUDE.md §2.3
requires a per-mechanism PRD for a central mechanism anyway); `end_of_game.py`
measured 156 after the §5 fix → `docs/PRD_end_of_game.md`;
`end_of_game_chain.py` was split out of `end_of_game.py` from the start. **Split,
never compressed**: no function body or docstring was shortened to fit — prose moved
to the PRDs, and every public name is re-exported so callers keep one import path.

**3. [Rule 3 — blocking] Eleven test files instead of three.** The plan named
`test_result_agreement.py`, `test_artifact_result.py` and
`test_end_of_game_reporting.py`; the 150-line gate and the self-audit forced
`test_result_agreement_edges.py`, `test_artifact_result_edges.py`,
`test_end_of_game_message.py`, `test_end_of_game_watchdog.py`,
`test_end_of_game_containment.py`, `test_end_of_game_two_seats.py`,
`test_end_of_game_chain.py`, `test_end_of_game_wiring.py`, plus two fixture modules
(`result_agreement_fixtures.py`, `end_of_game_harness.py`, not `test_*` so pytest
collects nothing).

**4. [Rule 2 — missing critical] `test_end_of_game_wiring.py`.** Every other test in
this plan drives `report_game_end` directly, so deleting the one line in
`agent_entrypoint.py` that calls it would have left the whole suite green while no
league game ever reported. Probe 13 fails 3 against exactly that.

**5. [Rule 2 — missing critical] `test_end_of_game_containment.py`.** The
failing-sink case never reaches the `except` clause, so without real causes the
containment was an untested branch. Probe 8.

**6. [Rule 3] `build_reporting_chain` gained a `sleep` seam.** `Gatekeeper` already
documents that seam so "tests never wait on a real backoff"; forwarding it is what
lets the 210 s ladder run at zero wall-clock cost. One keyword, defaulting to
`asyncio.sleep`.

**7. [Rule 2 — missing critical] `live` mode with no injected transport is refused
loudly** rather than silently dry-run. 07-10 owns the one supervised live send.

**8. [Rule 3] `test_log_artifact_reachability.py` gained an assertion.** Its
"no production caller exists" docstring was about to become false. It now names the
`log_` builder's five reachers, which is what stops the neighbouring empty-list
assertion from being green for the wrong reason. Nothing was weakened.

### Out of scope, filed not fixed

- **D7-17** — `game_id` is minted per GAME while PARAMETERS reads it as the SERIES id.
  The accumulator is correct and proven; what is missing is a series-scoped
  identifier, and inventing one would be a protocol decision taken in an artifact
  writer over an id negotiated with the peer (D-61).
- **D7-18** — a `QuotaManager` path is unguarded against the shipped `config/` tree.
  Production is pinned by a test; the structural guard covers one writer.

### Known and recorded, not a defect

In `dry_run` the series file is written **twice** per game with identical bytes:
once by `write_result_artifact` (unconditional, because rule 50 needs the file on
disk in every mode) and once by `DryRunSink`, whose `report_filename` resolves to the
same path. So `.prev` holds an identical generation after one game rather than a
previous sub-game. `.prev`'s crash-safety job is unaffected — a crash in the
rotate/replace window leaves a readable copy either way — and the per-sub-game
history lives in `sub_games`. Turned into a *check* rather than left as a surprise:
`test_what_is_emailed_is_byte_for_byte_what_is_committed` re-parses the rendered
`.eml` and asserts the `application/json` attachment equals the committed artifact,
verified on both seats of the real game.

### Authentication gates

None.

## 10. Task Commits

| Hash | Message |
|---|---|
| `e61b46c` | `feat(07-07): rule 35's agreement record -- true, false, or honestly unknown` |
| `8377916` | `feat(07-07): result_<game_id>.json -- one file per series, both token totals` |
| `4d68886` | `feat(07-07): the game-end hook -- bounded, contained, and beside the counter` |
| `5aa9ec1` | `fix(07-07): per-role artifact directory -- rule 35, found on a real game` |
| `7081515` | `test(07-07): three assertions of my own that measured nothing` |
| *(this commit)* | `docs(07-07): complete the end-of-game reporting plan` — this SUMMARY, STATE.md, the ticked phase TODO row, D7-17/D7-18 and the refreshed graph |

## 11. What 07-08, 07-09 and 07-10 must know

* **The artifacts are at `<artifact_dir>/<role>/`**, not at `<artifact_dir>/`. Both
  seats' four files exist side by side under `game_artifacts/police/` and
  `game_artifacts/thief/`.
* **`agreement.audit_verdict` is byte-identical to the `log_` artifact's**, by
  construction — 07-08's verdict screen can quote either without a second extraction.
* **The cop's `agreed` is legitimately `null`** on a capture it won. That is rule 21's
  asymmetry, not a bug, and `reason` says so in the artifact. Do not render it as a
  failure.
* **`games_played_declared` is an absent MARKER, not a number.** 07-10 sets the value,
  from `GAMES-PLAYED-RECONSTRUCTION.md`, before any live send.
* **`build_reporting_chain` refuses to build a live transport.** 07-10 constructs
  `GmailSink` itself and injects it; the refusal message says so.
* **A series today contains one sub-game** (D7-17). The two-sub-game arithmetic is
  proven, but production `game_id` is per game until a series id exists.

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 26 claimed paths verified present on disk **and** verified TRACKED by git with
`git ls-files --error-unmatch` -- the check that would have caught D7-10 on its own. All five
claimed task-commit hashes verified reachable in `git log --oneline --all`. Every file-size number
in Sec8 was re-read from the awk counter after the last edit and **five of them were corrected**
rather than left as written (`test_artifact_result.py` 148->128, `test_end_of_game_reporting.py`
105->88, `test_result_agreement.py` 84->87, `test_end_of_game_chain.py` 96->84, and the explicit
line-limit claim 21->19 `.py` files). Every measurement quoted in this document came off a command
run in this session; the counter deltas were read directly out of the two gitignored files before
and after each of `pytest` and `dev_launch.py`.
