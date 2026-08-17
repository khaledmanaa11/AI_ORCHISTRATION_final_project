---
phase: 08-submission-and-league-operations
plan: "04"
subsystem: services/reporting-league
tags: [D-80, D-81, D7-17, OQ8-1, OQ8-2, OQ8-6, OQ8-7, rule-38, rule-49, rule-50, rule-52, rule-53, SUB-07, SUB-08, SUB-12, REPORT-06, dead-code, league]
one_liner: "declaration_<game_id>.json stops being dead code -- a real dev_launch game writes it on both seats with rule 49's four links absent-marked and rule 38's figure explicitly unset -- plus the per-opponent league ledger with its inflated-count control, and the D7-17 question drafted for a human to send"
requires:
  - phase: 07-reporting-and-visualization-shell
    provides: "07-02's D-71 declaration wrapper (build/write_declaration_artifact, DeclarationContext), 07-07's end-of-game hook and its GAMES_PLAYED_UNSET precedent, 07-00's fixed games-played counter mechanism"
  - phase: 08-submission-and-league-operations
    provides: "08-01's docs/SUBMISSION-CHECKLIST.md gap register, which named the zero-production-callers finding and assigned it here"
provides:
  - "services/reporting/end_of_game_declaration.py -- THE first production caller for declaration_<game_id>.json; game_window (wire-log start/end times) and commit_hash_of moved here"
  - "services/reporting/league_ledger{,_fields,_bounds}.py -- the durable per-opponent audit trail, rule 52 + Table 18 row 5 refusals, and declared_count_matches (rule 38's counter-control)"
  - "shared/league_config{,_fields}.py + config/{police,thief}/league.json -- D-81: rule 49's four repo links, both MCP addresses and the token ceiling, with a live-mode refusal for absences and placeholders"
  - "shared/absent.py -- THE stated-absence marker, extracted at its third caller; 07-07's two markers rebuilt from it with byte-identical values"
  - "declaration artifact top-level field games_played_declared, unparameterised, carrying the rule-38 UNSET marker"
  - "docs/phases/phase-8/D7-17-QUESTION-FOR-THE-LECTURER.md -- drafted, UNSENT"
  - "docs/phases/phase-8/declaration-evidence/ -- the two artifacts a real game wrote, keys tabled against PARAMETERS:165"
affects:
  - "08-13 (league day) feeds the ledger and fills league.json's four URL slots; the live-mode refusal is what stops a scored game running with them absent"
  - "08-12 (human) creates the two repositories the absent markers name"
  - "08-14 (human) sets the games-played VALUE; declared_count_matches is the control it is checked against"
  - "08-11 inherits the D7-17 answer if it arrives before the runbooks are written"
tech-stack:
  added: []
  patterns:
    - "A refusal that is stricter for `live` than for `dry_run`, with the mode REQUIRED and never defaulted, so the lenient side cannot be picked silently"
    - "A stated-absence marker carrying its own reason, instead of null or a placeholder string, in any grader-facing artifact"
    - "A bound test that parses the FIXED value out of docs/PARAMETERS.md rather than from the constant it is checking"
    - "A reachability gate asserting the SHAPE of the real source, applied to a DELIVERABLE rather than to a helper"
    - "Declaration writing contained separately from the mail send, with the failure left observable on the returned report"
key-files:
  created:
    - src/pursuit/services/reporting/end_of_game_declaration.py
    - src/pursuit/services/reporting/league_ledger.py
    - src/pursuit/services/reporting/league_ledger_fields.py
    - src/pursuit/services/reporting/league_ledger_bounds.py
    - src/pursuit/shared/league_config.py
    - src/pursuit/shared/league_config_fields.py
    - src/pursuit/shared/absent.py
    - config/police/league.json
    - config/thief/league.json
    - tests/unit/test_declaration_reachability.py
    - tests/unit/test_league_ledger.py
    - tests/unit/test_league_ledger_count.py
    - tests/unit/test_league_bounds_against_the_book.py
    - tests/unit/test_league_config.py
    - tests/unit/test_league_config_shape.py
    - tests/unit/test_absent_marker.py
    - tests/unit/league_config_fixtures.py
    - tests/integration/test_end_of_game_declaration.py
    - tests/integration/test_end_of_game_declaration_containment.py
    - docs/phases/phase-8/D7-17-QUESTION-FOR-THE-LECTURER.md
    - docs/phases/phase-8/declaration-evidence/README.md
    - docs/phases/phase-8/declaration-evidence/police_declaration_397b3503b1bfa996.json
    - docs/phases/phase-8/declaration-evidence/thief_declaration_397b3503b1bfa996.json
  modified:
    - src/pursuit/services/reporting/end_of_game.py
    - src/pursuit/services/reporting/artifact_declaration.py
    - src/pursuit/services/reporting/artifact_declaration_fields.py
    - src/pursuit/services/reporting/result_artifact_fields.py
    - src/pursuit/network/agent_entrypoint.py
    - docs/PRD_end_of_game.md
    - docs/SUBMISSION-CHECKLIST.md
    - docs/phases/phase-8/TODO.md
    - tests/_shipped_config_guard.py
    - tests/unit/test_log_artifact_reachability.py
    - tests/unit/_agent_entrypoint_fixtures.py
key-decisions:
  - "D-81 implemented: rule 49's four repo links live in config/{police,thief}/league.json as JSON null, rendered into the artifact as stated-absence markers naming 08-12; the loader REFUSES an absence or a placeholder-looking URL when reporting.mode is live and permits both in dry_run"
  - "D-80 implemented: the league ledger starts empty and is never seeded from games_played.json; games_played_reading returns BOTH candidate counts plus an UNSET marker rather than one number, because which reading rule 37/38 asks for is OQ8-2 and a human's"
  - "The declaration artifact gained an unparameterised top-level games_played_declared UNSET marker -- the embedded Step-0 envelope's games_played_so_far is the raw counter (1922/1915) and nothing said so; no caller can set the field, so a number is not representable until 08-14"
  - "Start and end times are the earliest and latest timestamps in this seat's own wire log, not a clock read at report time; a log with no usable timestamp raises rather than substituting now"
  - "The declaration write is contained SEPARATELY from the mail send: rule 32/35 make an unreported game cost both teams everything, so a broken declaration returns None and logs, while EndOfGameReport.declaration_artifact keeps the failure observable"
  - "Table 18's two FIXED bounds are asserted against docs/PARAMETERS.md itself, after probe E moved MAX_GAMES_PER_TEAM to 11 and the whole ledger suite stayed green"
  - "D7-17 drafted and NOT decided: game_id is peer-negotiated (D-61), so redefining it is a protocol decision; three costed options carried over and the mail addressed for a human to send"
patterns-established:
  - "Stated absence over placeholder: shared/absent.py, used by three artifacts and one config loader"
  - "Book-reading bound tests: parse the FIXED value out of docs/PARAMETERS.md instead of transcribing it"
  - "Deliverable-level reachability gates: assert the production call site's shape, not just that some test exercises the code"
duration: 172min
completed: 2026-08-17
---

# Phase 8 Plan 04: League Machinery and the Declaration Artifact's First Production Caller

**`declaration_<game_id>.json` -- one of rule 50's four mandatory artifacts -- had never been
written by a game. Now a real `dev_launch` run writes it on both seats, carrying rule 49's four
links as honest absences and rule 38's figure as an explicit UNSET, alongside the per-opponent
league ledger with its inflated-count control and the D7-17 question drafted for a human to send.**

## Performance

- **Duration:** ~172 min
- **Tasks:** 4, each committed atomically
- **Files created:** 23 · **modified:** 11
- **Suite:** 2188 -> **2293 passed, 0 failed** · coverage **97.37% -> 97.43%**
- **Gates:** `ruff check .` 0 · line-limit 0 violations · local-truth OK (7 modules) · no-LLM OK ·
  `check_submission.py` exit 1, 41 PASS / 32 GAP / 13 UNJUDGED (unchanged, as expected)

## The defect, and the proof it is closed

08-01 re-derived at HEAD that `build_declaration_artifact`, `write_declaration_artifact` and
`DeclarationContext` had **zero production callers** -- their own module, one docstring mention at
`artifact_config.py:151`, the package re-export, and tests. Every test of them passed while
`docs/PARAMETERS.md:165`'s declaration content had never reached the wire.

**The grep, re-run at HEAD after this plan** (own module and `__init__.py` excluded):

```
src/pursuit/services/reporting/end_of_game_declaration.py:52   DeclarationContext,
src/pursuit/services/reporting/end_of_game_declaration.py:53   build_declaration_artifact,
src/pursuit/services/reporting/end_of_game_declaration.py:54   write_declaration_artifact,
src/pursuit/services/reporting/end_of_game_declaration.py:105  return build_declaration_artifact(
src/pursuit/services/reporting/end_of_game_declaration.py:110      context=DeclarationContext(
src/pursuit/services/reporting/end_of_game_declaration.py:140   return write_declaration_artifact(
```

That module is reached from `end_of_game._report`, which `agent_entrypoint.run_agent` calls one
line after `record_completed_game`.

**The real game.** `uv run python scripts/dev_launch.py`, exit 0, `game_id` `397b3503b1bfa996`.
Both seats wrote `game_artifacts/<role>/declaration_397b3503b1bfa996.json`. Read off disk:

| Key | police seat | thief seat |
|---|---|---|
| `game_uid` / `game_id` | `397b3503b1bfa996` | `397b3503b1bfa996` |
| `declarations.own` | all ten §5.5 keys, signed | all ten §5.5 keys, signed |
| `declarations.peer` | **present** | **present** |
| `peer_declaration_status` | "peer's own signed declaration embedded verbatim" | same |
| `games_played_declared` | `present: false` | `present: false` |
| `repo_urls` | 4 slots, all stated-absent | 4 slots, all stated-absent |
| `mcp_server_addresses` | `own` / `opponent`, stated-absent | same |
| `token_ceiling` | `200000` | `200000` |
| `start_time` | `2026-08-17T12:01:46.156590+00:00` | `2026-08-17T12:01:46.158186+00:00` |
| `end_time` | `2026-08-17T12:01:55.034879+00:00` | `2026-08-17T12:01:54.968262+00:00` |

Against `docs/PARAMETERS.md:165` -- *"both teams' identities, repo URLs, MCP server addresses,
hardware spec, language model, agreed token ceiling, start/end times"* -- every item is carried:
identities/hardware/language model inside the two signed envelopes (D-71 untouched), the rest at
the top level. Both files are kept at `docs/phases/phase-8/declaration-evidence/` with the mapping
tabled.

## Task Commits

1. **Task 1: league.json and its loader (D-81)** -- `4fbd4ed` (feat)
2. **Task 2: the per-opponent ledger and rule 38's counter-control (D-80)** -- `e672838` (feat)
3. **Task 3: the first production caller for the declaration artifact** -- `8c6fd1e` (feat)
4. **Task 4: the D7-17 question, and the checklist finding closed** -- `daf5654` (docs)
5. **Graph refresh** -- `b32bf9d` (chore)

## The two lines that did not move

**Rule 38 -- the games-played VALUE.** Nothing in this plan sets, defaults or infers it. The
ledger derives *two* candidate counts (`scored`, `all_recorded`) and hands back an UNSET marker
for the declared figure; the declaration artifact's `games_played_declared` is **unparameterised**
-- there is no argument for it, so no caller can choose a number. Both markers name
`docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md`. `config/*/league.json` deliberately carries
no games-played leaf at all, and a test asserts its absence.

This plan also *added* honesty that was missing: the embedded Step-0 envelope carries
`games_played_so_far` = **1922** (police) and **1915** (thief) because rule 37 puts it there, and
until now nothing in a grader-facing file said those are raw counters rather than a declaration.

**D7-17 -- no id scheme invented.** `game_id` is peer-negotiated (D-61), so redefining it is a
protocol decision. The question is drafted with both PARAMETERS citations quoted verbatim
(machine-checked against the document), the three costed options carried over from
`GATE-7-MEASUREMENT.md`, and the mail addressed to `rmisegal@gmail.com` **for a human to send**.

## Counter deltas -- all four numbers

| Reading | police | thief |
|---|---:|---:|
| Full `uv run pytest --cov` (2293 tests) | 1923 -> **1923** | 1916 -> **1916** |
| One real `dev_launch` game | 1922 -> **1923** | 1915 -> **1916** |

Suite delta **0 / 0**; one real game **+1 / +1**. 07-00's mechanism behaving exactly as specified.

## Probes -- every one asserted landed before its verdict was read

| # | Mutation | Result |
|---|---|---|
| A | `league_config_fields._validate_slot`: live-mode absence check disabled | **2 failed** (shipped file loaded in live mode) |
| B | `PLACEHOLDER_TOKENS = ()` | **3 failed** (example/TODO/`<team>` URLs accepted in live) |
| C | `from pursuit.security.step0_collect import read_games_played` planted in the ledger | **1 failed** (D-80 seeding guard) |
| D | rule 52's rematch refusal disabled | **2 failed** |
| E | `MAX_GAMES_PER_TEAM = 11` | **0 failed** -- **A HOLE, FOUND AND CLOSED** |
| E' | same mutation, after `test_league_bounds_against_the_book.py` was added | **1 failed** |
| F | the `declare_game` call site replaced with `declaration_path = None` | **7 failed** (5 integration, 2 structural) |
| G | `start_time` hardcoded to a literal timestamp | **1 failed** |
| H | declaration containment narrowed from `except Exception` to `except ValueError` | **2 failed** |

Every mutation was reverted by rewriting the file (never `git checkout --`, which restores from the
index and would have survived a staged mutation), and each revert was re-asserted and re-run green.

**Probe E is the one worth reading.** `test_the_tenth_game_is_recorded_and_the_eleventh_is_refused`
built its loop from `MAX_GAMES_PER_TEAM`, so moving the constant moved the test with it: the bound
was *enforced* and its **value was unasserted**, for a Table 18 row whose status is **fixed** and
whose deviation is a disqualification. `tests/unit/test_league_bounds_against_the_book.py` now
parses the value out of `docs/PARAMETERS.md` itself, with a control on the parser so a regex that
matched nothing could not make it vacuous.

A second vacuity was caught before it shipped: the first draft of
`test_nothing_in_the_ledger_module_reads_the_shipped_counter` stripped docstrings with
`source.split('"""')[-1]`, which keeps only the file tail and therefore searched almost nothing. It
was rewritten to strip docstrings by AST, with `test_the_docstring_stripper_actually_strips_
docstrings` as the control on the control.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] The declaration artifact presented a raw counter as a declaration**
- **Found during:** Task 3
- **Issue:** The embedded Step-0 envelope carries `games_played_so_far`, whose value is the polluted
  per-role counter, and nothing at the artifact's top level said so. A grader reads it as this
  team's declared figure -- rule 38 territory in a mandatory file.
- **Fix:** Added `DeclarationArtifactField.GAMES_PLAYED_DECLARED`, set unconditionally to a
  `stated_absent` marker that names the raw counter, the +14-for-zero-games measurement, and
  `GAMES-PLAYED-RECONSTRUCTION.md`. Deliberately **unparameterised**: no caller can set it.
- **Files:** `artifact_declaration_fields.py`, `artifact_declaration.py`
- **Verification:** `test_the_games_played_figure_is_left_unset_with_its_reason`, asserted on the
  real game's file read off disk. **Committed in:** `8c6fd1e`

**2. [Rule 3 - Blocking] `end_of_game.py` and `league_ledger.py` breached the 150-line gate**
- **Found during:** Tasks 2 and 3
- **Issue:** `league_ledger.py` measured 162 and `end_of_game.py` 151 after the wiring.
- **Fix:** Split, never compressed. `league_ledger_bounds.py` took the two book refusals (the seam
  the module docstring already named); `end_of_game_declaration.py` took the declaration path and
  `commit_hash_of`, and the module docstring's long rationale moved to `docs/PRD_end_of_game.md`
  §7 -- the relocation that file's own header already prescribes.
- **Verification:** `check_line_limit.sh` 0 violations tree-wide. **Committed in:** `e672838`, `8c6fd1e`

**3. [Rule 1 - Bug] Two structural ledgers correctly flagged the new modules and were stale**
- **Found during:** Task 3, on the first full-suite run (10 failures)
- **Issue:** `league_ledger.py` binds `durable_write_json`, which
  `test_shipped_config_guard.py`'s AST re-derivation requires in `DURABLE_WRITE_BINDERS`;
  `end_of_game_declaration.py` imports `log_read`, which
  `test_log_artifact_reachability.py`'s named reacher list must contain. The fake
  `_HandshakeResult` in `_agent_entrypoint_fixtures.py` also lacked `peer_step0_declaration`.
- **Fix:** All three updated honestly -- the binder added to the guard (so the ledger is patched
  like every other writer rather than exempted for being well-behaved today), the reacher added
  with a comment saying it is a READER, the fixture given the field with the real dataclass's
  default.
- **Verification:** `test_the_binder_list_names_every_module_that_binds_the_writer` and
  `test_the_builder_has_a_production_caller_and_it_is_the_game_end_hook` pass. **Committed in:** `8c6fd1e`

**4. [Rule 2 - Missing Critical] `shared/absent.py` extracted at the third caller**
- **Found during:** Task 1
- **Issue:** 07-07 wrote the `{"present": false, "detail": ...}` shape twice in one file and this
  plan needed it a third and fourth time. CLAUDE.md Table 5: extract at 2+ copies.
- **Fix:** New module; `TOKENS_ABSENT` and `GAMES_PLAYED_UNSET` rebuilt from it.
- **Verification:** `test_the_two_shipped_markers_are_byte_identical_to_their_pre_refactor_values`
  compares against literals transcribed from the pre-08-04 source, not recomputed from the module
  under test. **Committed in:** `4fbd4ed`

---

**Total deviations:** 4 auto-fixed (2 missing-critical, 1 blocking, 1 bug). No Rule 4 architectural
change was needed. No scope creep: every one was required to complete the planned work or to keep a
mandatory artifact honest.

## Issues Encountered

- **Probe E found a vacuous bound test in this plan's own work** -- see above. Closed, not reported.
- **A vacuous docstring-stripper** in the D-80 seeding guard, closed before commit with a control.
- The suite's first full run after Task 3 showed 10 failures; all ten were the structural ledgers
  and the entrypoint fixture doing their job, not defects in the new code.

## Explicitly NOT done

- **Nothing was pushed. No tag was created. No remote was touched.** `git tag -l` is empty and
  every commit is local. The D7-17 mail is a drafted file, unsent; no credential, no account.
- No games-played value chosen (OQ8-2, 08-14's).
- No `game_id` scheme invented (OQ8-1/D7-17, the lecturer's).
- No repo URL guessed (OQ8-6, 08-12's).
- `tests/integration/test_belief_policy.py` untouched.

## Next Plan Readiness

- **08-13** has the machinery it needs: fill `config/{police,thief}/league.json`'s six slots, flip
  `reporting.mode`, and the loader will refuse the run if any slot is still absent. Feed each
  completed game to `record_league_game`; rule 52 and Table 18 row 5 are enforced, not advisory.
- **08-14** has `declared_count_matches` as the control for whatever figure the human chooses.
- **Open, unchanged:** OQ8-1 (drafted, unsent), OQ8-2 (the value), OQ8-6 (the URLs), OQ8-7 (the
  agreed ceiling -- shipped at the book's negotiable 200,000 until a lead team says otherwise).

---
*Phase: 08-submission-and-league-operations*
*Completed: 2026-08-17*

## Self-Check: PASSED

- **23 created files:** all present on disk, sampled ones confirmed TRACKED by `git ls-files`.
- **5 commits:** `4fbd4ed`, `e672838`, `8c6fd1e`, `daf5654`, `b32bf9d` all resolve in `git log`.
- **`git tag -l`:** empty. **131 commits ahead of `origin/main`, none pushed.** No remote touched.
- **`tests/integration/test_belief_policy.py`:** last touched by `0437559` (phase 5), zero
  uncommitted changes.
- **No new `.py` is gitignored:** `git check-ignore` exits 1 for every file created by this plan.
