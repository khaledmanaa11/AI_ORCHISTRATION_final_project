---
phase: 07-reporting-and-visualization-shell
plan: "03"
subsystem: sdk/local-truth-firewall
tags: [D-74, D7-6, D7-7, REPORT-08, rule-8, rule-9, rule-2, NET-02, QUAL-02, STRAT-07-mould]
one_liner: "A closed twelve-field read model outside gui/ that structurally cannot express the opponent's true cell, proven by a scan whose counter-controls are measured -- with an always-clean scanner the absence test still passes 2/2, which is exactly why (b) and (c) exist; plus a CI gate that exits 2 on an empty scan instead of printing OK for having looked at nothing."
requires:
  - "Nothing. Wave 1, depends_on: []. Reads no 07-01/07-02 code."
provides:
  - "sdk/local_view.py: LocalView + BeliefView + ScentView + HintView -- four frozen dataclasses, twelve LocalView fields, no GameState/AgentContext/dict/extras"
  - "sdk/view_builder.py: build_local_view (the ONLY reader of ctx.state outside the turn loop) + HintHistory, the caller-owned append-only accumulator"
  - "scripts/check_local_truth.py + .sh: the structural gate -- imports AND `.state.<cop|thief|barriers>` chains, EmptyScanError on a missing/empty root, module count on the OK line"
  - "shared/roles.py: engine_agent + opponent_role, moved out of network/orchestrator.py and re-exported unchanged"
  - "BeliefMap.entropy(): the Shannon formula with one owner, consumed by turn_language.belief_snapshot and by the sidebar"
affects:
  - "07-06 (live GUI) consumes LocalView/build_local_view/HintHistory and MUST turn the local-truth CI job green by creating src/pursuit/gui/"
  - "07-08 (replay viewer) is the reason pursuit.services.reporting.replay_verify is the gate's one allowlisted service path"
tech-stack:
  added: []
  patterns:
    - "A CLOSED field set as the mitigation for a data-leak rule, with the field NAMES pinned by test, rather than a filter over a rich object"
    - "Dense positional grids instead of coordinate-keyed dicts, so no coordinate is ever a VALUE in a serialised view"
    - "A CI gate that raises on an empty scan set -- the anti-vacuity inversion of the check_no_llm_in_strategy.py mould"
key-files:
  created:
    - src/pursuit/sdk/local_view.py
    - src/pursuit/sdk/view_builder.py
    - src/pursuit/shared/roles.py
    - scripts/check_local_truth.py
    - scripts/check_local_truth.sh
    - tests/unit/local_view_fixtures.py
    - tests/unit/test_local_view_firewall.py
    - tests/unit/test_view_builder.py
    - tests/unit/test_view_hint_history.py
    - tests/unit/test_check_local_truth.py
  modified:
    - src/pursuit/network/orchestrator.py
    - src/pursuit/network/turn_language.py
    - src/pursuit/strategy/belief.py
    - .github/workflows/quality-gate.yml
    - docs/phases/phase-7/TODO.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "The leak is a FIELD READ, not an import -- so the mitigation is a closed field set, and the import gate is only the second half"
  - "Belief and scent grids are DENSIFIED to positional floats; a coordinate-keyed grid would put every cell on the board into the view as a value"
  - "The CI job is RED until 07-06, deliberately: 'skip when the directory is missing' is the same vacuity moved from the script into the workflow (D7-6)"
  - "engine_agent/opponent_role moved to shared/roles.py rather than copied, because sdk/ and the 07-06 gui/ both need the vocabulary and neither may import pursuit.network"
  - "BeliefMap.entropy() extracted at its second consumer rather than the formula being retyped"
metrics:
  tasks: 3
  commits: 6
  tests_added: 32
  suite: "1794 -> 1826 passed, 0 failed"
  coverage: "96.90% -> 96.95%"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 03: The Local-Truth Firewall Summary

Rule 9 (`docs/RULES.md:30`) makes displaying the full objective board state in the live
interface a **project disqualification**, and `RULES.md:115` ranks it third among the
cheapest ways to score zero — *"the tempting debugging shortcut"*. The data that triggers
it sits on every agent process by design. This plan makes a leak structurally impossible
and, where it cannot, loud.

## The thing that had to be got right, and how it was measured

**An import boundary is not the firewall.** `GameState` (`shared/state.py:34-38`) is
exactly `{cop, thief, barriers, barriers_placed, turn}`, and `turn_language.py:57` reads
`ctx.state.thief` on every cop turn from turn 1. A `gui/` module could import nothing
forbidden and still read the opponent's true cell. So the mitigation is the **field set**,
and the load-bearing test is a value scan over the serialised view.

**A field-level absence test alone proves nothing, and that is not an opinion here — it
is measured.** With `coordinate_hits` mutated to always return clean:

```
test_opponent_true_cell_is_absent_from_the_serialised_view   2 passed   <-- STILL GREEN
test_the_same_scanner_finds_the_cells_the_view_may_carry     FAILED
test_a_leaky_view_is_reported_by_the_identical_scanner       FAILED
test_every_leak_encoding_the_scanner_claims_is_reported      FAILED
```

The absence test passes 2/2 against a scanner that cannot see anything. That is exactly
the shape that read green six times in the phase-5 audit, and the reason the other three
exist.

## The leaky-view counter-control, with its real counts

The counter-control is an honest `LocalView` with the engine's TRUE opponent cell bolted
on — `LeakyLocalView`, defined in the test tree and never importable from `pursuit`. The
identical scanner is run over it and **must report the leak**:

| Counter-control | Result |
|---|---|
| `LeakyLocalView(honest=view, true_opponent_cell=(5,3))` | **reported**, hit path names `true_opponent_cell` |
| planted `tuple_pair` `(5, 3)` | reported |
| planted `reversed_list` `[3, 5]` | reported |
| planted `row_major_index` `38` | reported |
| planted `col_major_index` `26` | reported |
| planted `text_form` `"opponent at (5, 3)"` | reported |
| the same scanner over the HONEST payload, asked for `(0,0)`, `(6,6)`, `(1,1)`, `(2,2)` | **all four found** |

And each of the scanner's own branches was deleted in turn and measured — reversed-pair
**1 failed**, flat-index **1 failed**, text-form **1 failed**, "never descend" **3
failed**, "always clean" **3 failed**. No branch is decoration.

**The coordinates are chosen, not arbitrary,** and the reason is written into the fixture
module. `OPPONENT_CELL = (5, 3)` differs from own `(0, 0)`, from both declared barriers
`(1,1)`/`(2,2)` and from the belief argmax `(6, 6)` — each of those three is a cell an
honest view is *entitled* to carry, so a coincidence there would have the scan firing on a
legitimate field and the test measuring luck. Its flat indices **38** (row-major) and
**26** (column-major) are distinct from every other integer in the view — board_size 7,
turn 4, barriers_placed 2, hint stamp 2, coordinate components {0,1,2,6} — so a flat-index
hit can only mean a real leak.

## What makes the view unable to carry it

`LocalView` is twelve fields, pinned by name so a thirteenth cannot arrive by accident:
`role`, `board_size`, `turn`, `own_cell`, `declared_barriers`, `barriers_placed`,
`belief`, `scent`, `hints`, `machine_state`, `idle_seconds`,
`watchdog_threshold_seconds`. No `GameState`, no `AgentContext`, no free-form `dict`, no
`extras`. All four dataclasses are frozen, so nothing can be attached after construction —
which is how the debugging shortcut gets in without anyone editing the file.

**The densification is the non-obvious half.** `ScentField` keys its two grids by
coordinate; handing those to a view would put *every* cell on the board into it as a
VALUE, the opponent's true cell among them. Both scent grids and the belief posterior are
therefore positional row-major floats. Reverting either densification fails the scan:
belief **7 failed**, scent **6 failed**.

`belief=None` when belief is off this game — the honest-"not run" convention
`turn_language.belief_snapshot` already uses, never a fabricated uniform grid
(**1 failed** when reverted).

## The empty-scan guard — the vacuity the plan named, and it was real

`check_no_llm_in_strategy.py:56` is `sorted(root.rglob("*.py"))`, which returns `[]` for a
missing root; `find_violations` then returns `[]` and `main()` prints OK. `src/pursuit/gui/`
does not exist until 07-06, so copying that shape verbatim would have shipped a gate that
certified a package it had never opened.

`gui_module_paths` raises `EmptyScanError` instead, `main` maps it to
`ExitCode.EMPTY_SCAN` (2), and the OK line prints the module count so a human reading CI
output can see it was not zero. Measured today, exactly as the plan asked so 07-06 knows
what it must turn green:

```
$ uv run python scripts/check_local_truth.py
ERROR: local-truth gate scanned nothing: C:\...\src\pursuit\gui does not exist.
       07-06 creates it; until then this gate cannot vouch for anything.
exit=2
```

Both halves are independently pinned: missing root **1 failed**, zero-module root **1
failed**, dropping the module count from the OK line **1 failed**.

**The CI job is therefore RED until 07-06, deliberately.** Wiring it behind "skip if the
directory is missing" is the same vacuity moved from the script into the workflow. Filed
as **D7-6** with the rejected alternatives, and 07-06 owns turning it green.

## The three pre-fix failures, verbatim

Taken before the fix, not reconstructed after it (commit `70df24a`):

```
tests/unit/test_local_view_firewall.py -- collection ERROR
  E   ModuleNotFoundError: No module named 'pursuit.sdk.local_view'

tests/unit/test_view_builder.py -- collection ERROR
  E   ModuleNotFoundError: No module named 'pursuit.sdk.view_builder'

tests/unit/test_check_local_truth.py -- 8 failed
  E   FileNotFoundError: [Errno 2] No such file or directory:
      'C:\...\final_project\scripts\check_local_truth.py'
```

## Revert probes — thirty, every count real

| # | Mutation | Result |
|---|---|---|
| 1 | view carries the opponent's cell as `own_cell` | **3 failed, 29 passed** |
| 2 | an `extras`-style field bolted onto `LocalView` | **1 failed, 31 passed** |
| 3 | belief grid keyed by coordinate, not densified | **7 failed, 25 passed** |
| 4 | scent handed over coordinate-keyed | **6 failed, 26 passed** |
| 5 | scanner always returns clean | **3 failed, 29 passed** |
| 6 | scanner loses the reversed-pair branch | **1 failed, 31 passed** |
| 7 | scanner loses the flat-index branch | **1 failed, 31 passed** |
| 8 | scanner loses the text-form branch | **1 failed, 31 passed** |
| 9 | scanner never descends past the root | **3 failed, 29 passed** |
| 10 | belief fabricated when disabled instead of `None` | **1 failed, 31 passed** |
| 11 | turn-stamp `bool` guard removed | **2 failed, 30 passed** |
| 12 | unknown intent coerced through instead of dropped | **3 failed, 29 passed** |
| 13 | non-dict peer payload not guarded | **1 failed, 31 passed** |
| 14 | hint dedupe removed | **1 failed, 31 passed** |
| 15c | history defaults to MODULE-LEVEL GLOBALS (NET-02) | **5 failed, 27 passed** *(was 0 — see below)* |
| 16 | GATE: missing root returns `[]` (the mould) | **1 failed, 31 passed** |
| 17 | GATE: zero-module root tolerated | **1 failed, 31 passed** |
| 18 | GATE: `ImportFrom` records only `node.module` | **1 failed, 31 passed** |
| 19 | GATE: `.state.<field>` chain check removed | **3 failed, 29 passed** |
| 20 | GATE: services allowlist emptied | **2 failed, 30 passed** |
| 21 | GATE: module count dropped from the OK line | **1 failed, 31 passed** |
| 22 | entropy switched from `log2` to natural log | **1 failed, 31 passed** |
| 23 | `engine_agent` maps police → thief | **3 failed, 29 passed** |
| 24b | every `ctx.state` read aliased away | **1 failed, 31 passed** *(was 0 — see below)* |
| 25 | a NEW `sdk/` module reads `ctx.state.thief` | **1 failed, 31 passed** |
| 26 | a `LocalView` field retyped to a free-form `dict` | **1 failed, 31 passed** |
| 27 | `GUI_ROOT` pointed at a stray path | **1 failed, 31 passed** |
| 28 | a view dataclass unfrozen | **1 failed, 31 passed** |
| 29 | GATE: forbidden-import check removed | **1 failed, 31 passed** |
| 30 | GATE: prefix match becomes a bare `startswith` | **3 failed, 29 passed** |
| 31 | `_FORBIDDEN_ANNOTATIONS` thinned to `()` | **1 failed, 31 passed** |
| 32 | `_TRUE_POSITION_FIELDS` thinned | **2 failed, 30 passed** |

Control restored cleanly every time (**32 passed**).

Probe **25** is the one that matters most and it is the probe run FORWARDS: a new
`src/pursuit/sdk/leaky_panel.py` containing `return ctx.state.thief` fails the "only
reader" test with `unexpected true-position readers: {'view_builder.py', 'leaky_panel.py'}`.

## Four holes the self-audit found in my own work

**1. Probe 15 first returned 0 failed, 32 passed — the probe ran the hazard NOT AT ALL.**
My first NET-02 mutation only *declared* two module-level globals; it never wired them
into the dataclass defaults, so nothing changed. (The naive form, `entries: list = []`,
cannot even be expressed — Python raises `ValueError: mutable default` at import, which is
worth knowing but is not the hazard.) Re-run with
`field(default_factory=lambda: _SHARED_ENTRIES)`, the real shape of the bug: **5 failed**.
This is the 07-02 lesson repeating, in my own hands, on the first probe I wrote for it.

**2. Probe 24 first returned 0 failed — the hazard ran halfway.** I aliased only *one*
`ctx.state` read, and `ctx.state.barriers` two lines below kept the AST chain alive, so the
scan still found the file. Re-run aliasing every read: **1 failed**.

**3. The entropy extraction had no pinned value.** `BeliefMap.entropy()` was extracted so
the Shannon formula would have one owner — but the only entropy assertions in the entire
repository were `>= 0.0` and `is not None`, both of which hold under `ln` as readily as
under `log2`. A silent base change would have shipped. Now pinned on both halves: a
uniform 7×7 prior is exactly `log2(49)` bits, and `belief_snapshot` and `build_local_view`
must report the SAME number off the same map (probe 22: **1 failed**). Confirmed on the
live path too — the real game below logged turn-0 entropy **5.6108** against
`log2(49) = 5.6147` (`ln(49) = 3.8918`).

**4. Two tests were shape-only and one loop was vacuous.**
- The densification test checked dimensions and `float` types, so an all-zero board of the
  right shape satisfied it. Values now pinned (own scent positive at the emitted cell,
  belief rows summing to 1).
- The hostile-payload test iterates `view.hints`, so a builder that dropped EVERY hint
  passed it with the loop body never running. Both outcomes are now pinned — what is
  discarded, and what survives with its untrusted fields dropped.
- An **AST scan over every `parametrize` in this plan's five test files** found exactly
  **one** site (`_SERIALISED_FORMS`), already length-guarded. But the same scan resolved
  every assert-bearing *loop* source and found two module-level literal tuples iterated
  with nothing asserting they still had rows — `_FORBIDDEN_ANNOTATIONS` and
  `_TRUE_POSITION_FIELDS`. Both now counted (probes 31-32).

One more narrowing: `BeliefView.reliability` went from `float | None` to `float`. The
`None` was unreachable — the view is built only when the brain IS a `BeliefAdapter`, which
always carries a live `Reliability`. An annotation admitting a state no code path can
produce is the same defect as a stale comment.

## Production reachability, grepped

**Every reader of the true position in `src/`, exhaustively:**

```
network/turn_actions.py:184        ctx.state.cop / ctx.state.thief    (the turn loop)
network/turn_commit_ledger.py:66   ctx.state.barriers_placed          (the turn loop)
network/turn_language.py:57,78,90,93                                  (the turn loop)
sdk/view_builder.py:95,101,102     ctx.state.cop/.thief/.barriers     <-- THE ONLY NEW ONE
```

The pre-existing four are the turn loop, which legitimately holds the joint position. A
test AST-scans `src/pursuit/sdk/` on every run and asserts the reader set is exactly
`{view_builder.py}`, with its own counter-control (a synthetic leaky module reports True, a
clean one False) and the forward probe above.

**What is production-reachable, and what honestly is not** (filed as **D7-7**, the third
occurrence of D7-3):

| Name | Production caller |
|---|---|
| `shared/roles.engine_agent` / `opponent_role` | `network/orchestrator.py` re-export → `turn_actions`, `turn_commit`, `capture_declaration`, `agent_audit_wiring`, `agent_lifecycle` |
| `BeliefMap.entropy()` | `network/turn_language.belief_snapshot` — six live invocations in the real game below |
| `sdk/local_view` | `sdk/view_builder` |
| `build_local_view` / `HintHistory` / `HintHistory.observe` | **none yet — 07-06** |
| `HintHistory.record_outgoing` | **none at all — 07-06** |

Structural, not an omission: this plan's `<non_goals>` exclude every line of Tkinter, and
07-06 declares the consumer side of D-74. Recorded rather than glossed.

## Gates

```
ruff check .                          All checks passed        (0 violations)
check_line_limit.sh                   exit 0                   (tracked)
check_line_limit.sh <12 paths>        exit 0                   (explicit -- the no-arg form
                                                                enumerates via git ls-files
                                                                and passes VACUOUSLY on an
                                                                untracked file)
check_no_llm_in_strategy.py           OK                       (unchanged)
check_local_truth.py                  exit 2, ERROR names the missing root  (D7-6)
pytest tests/ --cov                   1826 passed, 0 failed    (baseline 1794)
                                      coverage 96.95%          (baseline 96.90%)
dev_launch.py                         exit 0
                                      outcome capture, audit_verdict matched=true
                                      zero technical_*, zero STEP0_MISMATCH
                                      one illegal_transition == the pre-existing D7-5
```

New/edited module coverage: `sdk/local_view.py` **100%** · `sdk/view_builder.py` **100%** ·
`shared/roles.py` **100%** · `strategy/belief.py` **100%** · `network/turn_language.py`
**100%** · `network/orchestrator.py` 98% (unchanged).

File sizes, all ≤ 150 code lines:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `sdk/local_view.py` | 79 | | `tests/.../local_view_fixtures.py` | 138 |
| `sdk/view_builder.py` | 131 | | `tests/.../test_local_view_firewall.py` | 98 |
| `shared/roles.py` | 41 | | `tests/.../test_view_builder.py` | 118 |
| `scripts/check_local_truth.py` | 126 | | `tests/.../test_view_hint_history.py` | 106 |
| `network/orchestrator.py` | 105 (was 117) | | `tests/.../test_check_local_truth.py` | 101 |
| `strategy/belief.py` | 141 (was 130) | | `tests/` collected | **32** |

## Scope — what was NOT touched

Nine files outside `tests/`, all this plan's. `git diff` over `src/pursuit/security/`,
`agent_step0_wiring.py`, `handshake_evaluate.py`, `agent_wiring.py`, `turn_actions.py`,
`turn_commit.py` and **all of `config/`** is **EMPTY** — the Phase-6 Step-0 and
commit-reveal paths, and every configured number, are byte-unchanged.
`tests/integration/test_belief_policy.py` was not touched. No logic was placed in
`scripts/` beyond the walk itself, and none under `gui/` (which this plan does not
create): `scripts/` is scanned by neither the size gate (`check_line_limit.sh:18`) nor
coverage (`pyproject.toml:37`), and `gui/` is coverage-omitted (`pyproject.toml:38`) —
which is exactly why `LocalView` and the builder live in `sdk/`.

The workflow edit is **+18 / −0**, the only change to that file.

## Games-played counters — rule 38

Read directly (the files are gitignored):

```
FULL SUITE     before 1913 / 1906    after 1913 / 1906    DELTA 0 / 0
ONE REAL GAME  before 1913 / 1906    after 1914 / 1907    DELTA 1 / 1
```

Nothing in this plan reads, writes, defaults or reads around the counter.

## Zero numbers invented

This plan introduces **no game parameter**. Every number in it is structural and named:
`ExitCode.OK/VIOLATIONS/EMPTY_SCAN` is an `IntEnum` (the `watchdog.WatchdogExit`
precedent), `board_size` comes from `GameParams`, `watchdog_threshold_seconds` is copied
off `NetworkParams`, and `idle_seconds` is supplied by the caller rather than invented
because `Watchdog` exposes no public idle reading and this plan does not edit `network/`
to add one. The test-side coordinates are test scaffolding, chosen for the reasons written
into the fixture docstring.

## Deviations from plan

1. **[Rule 3 — blocking] `src/pursuit/shared/roles.py` created and
   `network/orchestrator.py` edited.** Not in `files_modified`. `view_builder` must know
   which `GameState` field is *our own* cell, and so will the 07-06 GUI — and neither may
   import `pursuit.network` (the gate this plan writes forbids it for `gui/` outright, and
   `sdk` → `network` inverts the direction `agent_context.py` already established). The
   only alternative was a second copy of the `"police"`/`"thief"` literals, which is
   precisely the "second, driftable copy" `opponent_role`'s own docstring warns against.
   Logic moved unchanged; the string literals became module constants per CLAUDE.md's
   hardcoded-value rule, and both names are re-exported so no call site changed. Probe 23:
   **3 failed**.
2. **[Rule 2 — missing critical functionality] `BeliefMap.entropy()` added and
   `turn_language.belief_snapshot` rewired.** The sidebar needs the same
   entropy/argmax/reliability triple, and `view_builder` cannot call `belief_snapshot`
   (it lives in `network/`). Retyping the formula would have been a second copy of a
   numeric expression — CLAUDE.md Table 5 forbids duplication at two copies. Moved to the
   object that owns the grid. Now pinned by value; see hole 3 above.
3. **[Rule 3 — blocking] test files split into four plus a fixtures module.** The plan
   named two test files. `tests/unit/local_view_fixtures.py` holds the scanner and the
   context builders (not `test_*`, so pytest collects nothing from it — the
   `artifact_config_fixtures.py` precedent), and `test_view_hint_history.py` split out of
   `test_view_builder.py` when the entropy pin took it past the gate. Split, never
   compressed.
4. **[Rule 2] The hint accumulator is total over hostile peer data.** `ctx.incoming_hints`
   is attacker-controlled (05-12's boundary rule: `tools.receive_hint` validates a payload
   as nothing more than a dict). A view that raises mid-game is worse than a blank cell, so
   a non-dict payload, a non-string text, a `bool` turn stamp and an unrecognised intent are
   each dropped rather than coerced. Probes 11-13: **2 / 3 / 1 failed**.
5. **[Rule 1 — bug in my own work] four self-audit fixes**, commits `094eb12` and
   `7c69f81`: the unpinned entropy value, the shape-only densification test, the vacuous
   hostile-payload loop, and the two unguarded literal sets.

No architectural decision was needed; no checkpoint was reached; no authentication gate
occurred.

## Issues Encountered

- **`ruff`'s isort grouping for `pursuit` oscillated** between runs (first-party vs
  third-party), producing a lint error on files it had itself just fixed. Settled by
  running `ruff check --fix .` across the whole tree rather than per-file, then
  re-verifying `ruff check .` clean.
- **The probe driver's `git checkout --` restore silently reverted two uncommitted guard
  edits** I had made between probe batches. Caught by re-reading `git diff` rather than
  trusting the edits had survived; both re-applied and re-verified before the commit.

## Open, for the plans that own it

**D7-6** — the `local-truth` CI job is red until 07-06 creates `src/pursuit/gui/`, by
construction and not by accident; the rejected alternatives are recorded. Also noted there,
**not fixed** per the scope boundary: `check_no_llm_in_strategy.sh` has been absent from
`quality-gate.yml` since 03-10 and still is — pre-existing, unrelated to this gate, and not
something to slip into a commit about a different one.
**D7-7** — the whole 07-03 surface awaits its 07-06 wiring; `record_outgoing` has no caller
at all. Everything that *could* be wired now is, and that half was grepped.

## Task Commits

1. **Task 1: RED — the three tests against pre-plan code** — `70df24a` (test)
2. **Task 2: `LocalView` + `view_builder`, outside `gui/`** — `f7d21c6` (feat)
3. **Task 3: the CI gate, wired, loud on an empty scan** — `1ccd4ea` (feat)
4. **Self-audit: the entropy pin and the 150-line split** — `094eb12` (test)
5. **Self-audit: the two literal-set guards, and an unreachable `None`** — `7c69f81` (test)

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 17 claimed paths verified present on disk with `[ -f ]` **and** tracked by git with
`git ls-files --error-unmatch` (`07-03-SUMMARY.md` itself untracked until the final
commit below); all five claimed commit hashes verified reachable in `git log --oneline
--all`; `src/pursuit/gui/` verified **absent**, which is the fact the empty-scan message
depends on. Every line count in the table above was re-measured with the gate's own awk
after the last edit, and one was wrong when first written (`local_view_fixtures.py` 137 →
**138**) and is corrected here rather than left. Every other number in this document was
read off a command's output in this session, including the four counter readings, the two
coverage figures, the thirty probe counts and the six live entropy values.

