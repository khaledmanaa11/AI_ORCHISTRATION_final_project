---
phase: 07-reporting-and-visualization-shell
plan: "08"
subsystem: services/reporting-replay-verifier
tags: [D-59, D-64, D-76, D7-3, D7-8, D7-14, OQ-6, REPORT-09, SEC-04, rule-18, rule-20, rule-25, rules-8-9, canonical-json, tkinter]
one_liner: "A replay viewer whose Verified OK is earned turn by turn from the artifact alone -- proven on a real game with both sources moved off disk, 5/5 on both seats -- with FAILED and a distinct nothing-to-verify both reachable and tested, and with the second-serializer alternative measured accusing 10 of 10 honest turns"
requires:
  - "07-05: the log_ artifact, verify_log_turns, and the proof that it is self-contained"
  - "07-06: gui/widgets.TextPanel, the coverage-omitted-directory discipline, and the ALLOWED_SERVICE_MODULES pre-authorisation in check_local_truth.py"
  - "07-11: the rules 8-9 fix -- nothing here reads live state, belief or scent"
  - "06-01/06-02: commit_pack.verify_reveal, the one payload builder (D-59)"
provides:
  - "services/reporting/replay_verdict.py: VERIFIED_OK / NOTHING_TO_VERIFY / FAILED, VerdictState, TurnCheck, ReplayVerdict, banner_colour"
  - "services/reporting/replay_verify.py: check_turn / check_turns / seal_matches / verdict_from / open_replay -- the ONE import path a gui/ module may take"
  - "services/reporting/replay_source.py: load_artifact and the in-progress-game refusal (rule 18)"
  - "services/reporting/replay_session.py: ReplaySession -- the cursor, the auto-pause, and every string the window prints"
  - "gui/replay_app.py + gui/replay_panels.py: the Tk shell, 181 code lines of widget construction"
  - "tests/unit/local_truth_helpers.py: the gate loader, extracted at the third copy"
affects:
  - "07-09 takes criterion-3 evidence through open_replay(path).verdict -- the EXACT value the banner renders; there is deliberately no one-call verdict_for wrapper"
  - "07-10 screenshots the banner; the three states and their colours are pinned by test"
  - "Any plan adding a gui/ module inherits the widened-by-reading import allowlist in test_gui_structural.py"
tech-stack:
  added: []
  patterns:
    - "A THIRD verdict state for 'nothing to verify', so a vacuous pass cannot be spelled as a success on screen"
    - "A refusal by FILENAME at the one read site, turning a policy question (may this be opened on a live game?) into something that cannot happen"
    - "Resealing a tampered fixture, so a per-field verdict is provably earned by the per-turn check and not by the whole-file seal"
    - "A test reading a sibling gate's allowlist instead of keeping a second copy of it"
    - "Reading the banner back off the RENDERED widget, not off the model that fed it"
key-files:
  created:
    - src/pursuit/services/reporting/replay_verdict.py
    - src/pursuit/services/reporting/replay_source.py
    - src/pursuit/services/reporting/replay_session.py
    - src/pursuit/services/reporting/replay_verify.py
    - src/pursuit/gui/replay_app.py
    - src/pursuit/gui/replay_panels.py
    - tests/unit/replay_fixtures.py
    - tests/unit/local_truth_helpers.py
    - tests/unit/test_replay_verify.py
    - tests/unit/test_replay_verify_boundary.py
    - tests/unit/test_replay_session.py
    - tests/integration/test_replay_roundtrip.py
  modified:
    - tests/unit/test_gui_structural.py
    - tests/unit/test_check_local_truth.py
    - tests/unit/test_log_artifact_reachability.py
    - docs/phases/phase-7/TODO.md
key-decisions:
  - "THREE verdict states, not two. The non-zero-committed-turn guard runs BEFORE any aggregate; dropping it makes an empty artifact read `Verified OK` (measured)"
  - "`Verified OK` is the banner EXACTLY -- counts live on a separate detail line, so tests assert equality rather than a substring"
  - "The per-turn check runs FIRST and names the failing turn; the artifact seal is checked only when every turn passed, so all four field tampers name a turn rather than the seal"
  - "The in-progress-game question is decided by REFUSAL: `load_artifact` rejects any path not named `log_`, so `<uid>.jsonl` and `<uid>.ledger.jsonl` cannot be opened at all (rule 18)"
  - "`main()` verifies BEFORE it builds a Tk root -- a refused file can never produce a window whose empty banner a screenshot might flatter"
  - "`--step-ms` is required with no default anywhere in `src/` (OQ-6, 07-06's precedent applied to a second UI number)"
  - "The one-call `verdict_for(artifact)` wrapper was REMOVED after the production-caller grep found it test-only; callers take `open_replay(path).verdict`, which is the value on screen"
  - "`test_gui_structural.py` READS `check_local_truth.ALLOWED_SERVICE_MODULES` rather than keeping a second hardcoded allowlist"
metrics:
  tasks: 3
  commits: 5
  tests_added: 40
  suite: "2090 -> 2130 passed, 0 failed"
  coverage: "97.29% -> 97.37%"
  probes: 7
  duration: 41min
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 08: The Replay Viewer Summary

**Sec10.4 criterion 3 is the words on this screen, and rule 20 makes a *verifying*
replay viewer a threshold condition for approving the project.** So the whole plan is
about one thing: making `Verified OK` a claim that has to be earned every time, and
making the other two answers reachable enough to prove it.

---

## 1. The headline measurement, on a real game with the sources gone

`uv run python scripts/dev_launch.py` → exit 0, game `55fa28cbef618a19`, both seats
`"matched":true`, outcome `capture`, **zero `technical_win`, zero `watchdog_incident`**.

Then `<uid>.jsonl` and `<uid>.ledger.jsonl` were **moved off disk on both seats** (`ls
logs/<role>/ | grep <uid>` returned only the `.view.json` snapshots and the
declarations), and only then was the viewer run:

| | police | thief |
|---|---|---|
| banner | **`Verified OK`** | **`Verified OK`** |
| detail | `5/5 committed turns re-hash` | `5/5 committed turns re-hash` |
| turn entries in the file | 6 | 6 |
| state | `ok` | `ok` |

Read back off the **rendered Tk widget**, not off the model that fed it:

```
REAL GAME, BANNER ON THE WIDGET = 'Verified OK' | '5/5 committed turns re-hash'
panel section 2, turn 0:  re-hash: re-hashed against h_commit
```

`uv run python -m pursuit.gui.replay_app --artifact game_artifacts/police/log_55fa28cbef618a19_g01.json --step-ms 600 --once` → **exit 0**.

07-05 proved the artifact *could* be verified with both sources deleted. This plan is
the thing that does it, and it did it on a game played today.

## 2. The three states, and why the third one is the plan

`security/audit_record.py:34-36` says its verdict is "vacuously True for an empty
list". For the AUDIT that is right — a peer with no records has published nothing to
disagree with, and rule 36 sanctions that separately. **On a screen it is a lie.**

So `verdict_from` counts committed turns and returns `NOTHING_TO_VERIFY` **before it
evaluates any aggregate**. All three states are reachable, all three are tested, and
all three were read off the widget:

| Artifact | banner on the widget | colour | detail |
|---|---|---|---|
| clean fixture (4 committed + 1 game-over) | `Verified OK` | `#1b7f3b` | `4/4 committed turns re-hash` |
| one field of turn 2 flipped, **resealed** | `FAILED -- turn 2: re-hash does not match h_commit` | `#b00020` | `3/4 committed turns re-hash` |
| zero committed turns | `Nothing to verify` | `#4a4a4a` | `0/0 committed turns re-hash` |

`Verified OK` is asserted by **equality**, never by substring: the counts live on a
separate detail line precisely so a banner that merely *contained* the phrase would
fail the test.

## 3. Tamper detection, field by field, and why each one reseals

Four separate tests, **not one `parametrize` case** — an emptied table skips silently
(this phase has found that twice), and a verifier that re-hashed only `move` would pass
a one-case test. The table is still floored: `len(TAMPERABLE_FIELDS) == 4` and
`set(TAMPERERS) == set(TAMPERABLE_FIELDS)`, so a fifth `verify_reveal` input added
upstream fails here rather than going unchecked.

**Every field tamper reseals the artifact first.** `log_artifact_fields.SEALED_FIELDS`
covers `turns`, so a one-field change breaks the seal *and* the turn hash; a test that
let both break could not say which check caught it. Resealing makes the verdict proof
that the **per-turn re-hash** fired on its own.

The mutation shapes are `scripts/gate6_tamper.py`'s, reused rather than reinvented:
`intent` flips truth↔lie (`:43`), `move` swaps one legal direction for another
(`:80-84`), `state` moves one field of D-60's record, `nonce` flips one hex character of
the 32. Each asserts the banner names the tampered turn **and explicitly does not name
turn 0** — a verifier that always reported the first turn would pass a tamper aimed at
the first turn and tell a grader nothing.

**On the real game**, the last committed turn (a barrier-placing turn, so `move` reads
`"stay"`) was flipped to `"south"` and resealed:

```
tampered turn 4 : {"barrier":{"direction":"east",...},"move":{"direction":"stay",...}}
               -> {"barrier":{"direction":"east",...},"move":{"direction":"south",...}}
TAMPERED banner = 'FAILED -- turn 4: re-hash does not match h_commit' | 4/5
```

**A fifth tamper is genuinely additive.** `outcome` sits inside the seal and inside no
commit hash at all: every turn still re-hashes 4/4, and the artifact is still `FAILED`,
naming the seal. That is why the seal check is not redundant with the per-turn ones.

## 4. The measurement that matters most: a second serializer, on real data

The worst failure of this screen is not a missed forgery — it is a **false `FAILED`**,
which accuses an honest opponent of our own formatting. `commit_pack.py:10-18` forbids a
second `json.dumps(sort_keys=True, ...)` in this repository in as many words, and probe
1 measures the cost of ignoring it, on the artifacts of the real game:

```
police  banner='FAILED -- turn 0: ...'  FALSE FAILED turns=[0,1,2,3,4]  (5 of 5)
thief   banner='FAILED -- turn 0: ...'  FALSE FAILED turns=[0,1,2,3,4]  (5 of 5)
```

**10 of 10 committed turns across both seats**, wrong. On the fixture the same mutation
gives 4 of 4. `grep -rn "json.dumps" src/pursuit/services/reporting/` returns five hits
and **every one is inside a docstring forbidding it**; the only serialiser reached is
`config_hash.canonical_json`, including the one used to render a move into a caption.

## 5. Rules 8-9 and rule 18 — decided, not assumed

The plan asked for the in-progress-game question to be *decided explicitly*. It is, in
`replay_source.py`'s docstring, and it holds for two independent reasons:

1. **The artifact does not exist during play.** D-64 keeps the ledger off the wire path,
   rule 18 keeps every nonce secret while the game is live, and only SEC-04's end-of-game
   publication makes it readable. `test_log_artifact_reachability.py` fails on every
   suite run if anything under `network/turn_*` or the orchestrator reaches the builder.
2. **The two live files are refused BY NAME.** `load_artifact` checks the
   `docs/PARAMETERS.md:167` prefix. `<uid>.jsonl`, `<uid>.ledger.jsonl`, `result_*.json`
   and `declaration_*.json` are all refused with a message naming rule 18, and the
   counter-control in the same test opens the artifact this viewer exists for.

`main()` runs that refusal **before** `tk.Tk()`, so the shipped entry point is tested
with no display at all, and a refused file can never produce a window whose empty banner
a screenshot might flatter.

Nothing here reads `ctx.state`, the strategy belief, the scent, or the live `logs/`
tree. D7-8's constraint is satisfied by absence: the artifact carries none of the six
`LANGUAGE_INTERNAL_FIELDS`, and a render-time scan asserts the viewer does not
reintroduce one (with a control proving the scan can find a name).

## 6. `gui/` is still logic-free, and the gate needed no widening

`check_local_truth.py` → **`OK: 7 module(s) scanned`, exit 0** — grown by exactly two
from 07-06's five. **The gate was not widened**: 07-06 had already written
`ALLOWED_SERVICE_MODULES = ("pursuit.services.reporting.replay_verify",)` for this plan,
so `replay_verify.py` re-exports everything the window needs and the app names that one
module rather than the package.

`test_gui_structural.py`'s import check was the one that had a second, narrower copy of
the same decision (`_ALLOWED_PACKAGES`). It now **reads the gate's own allowlist**, pins
it to that one module, and carries a new counter-control proving `gmail_sink` and a bare
`import pursuit.services` are still reported.

| `gui/` (omitted) | lines | | `services/reporting/` (covered) | lines | coverage |
|---|---|---|---|---|---|
| `replay_app.py` | 132 | | `replay_verify.py` | 142 | **100%** |
| `replay_panels.py` | 49 | | `replay_session.py` | 139 | **100%** |
| | | | `replay_verdict.py` | 98 | **100%** |
| | | | `replay_source.py` | 60 | **100%** |
| **total** | **181** | | **total** | **439** | |

Zero arithmetic `BinOp`s, zero f-strings, zero `.join`/`.format` under `gui/` — the
existing structural scans, unchanged, still pass. Nothing was parked in `scripts/`.

## 7. Revert probes — seven, every count real

Anchor asserted present, mutation asserted landed, source restored and re-compared.

| # | Mutation | Result |
|---|---|---|
| 1 | a second `json.dumps(sort_keys=True)` re-hash (D-59 drift) | **15 failed, 18 passed** — and **4/4 fixture turns, 10/10 real turns**, falsely FAILED |
| 2 | the non-zero-turn guard dropped | **4 failed, 29 passed** — the empty artifact banner reads `Verified OK` |
| 3 | a replay module binding `write_log_artifact` | **1 failed, 19 passed** |
| 4 | the per-turn re-hash always succeeds | **1 failed, 3 passed** |
| 5 | the production-caller scan made blind | **1 failed, 3 passed** |
| 6 | `main()` swallows the refusal and reports OK | **1 failed, 3 passed** |
| 7 | the trailing game-over turn counted as committed | **10 failed, 5 passed** |

Probes 1 and 2 are the plan's two named reverts. Probes 3–6 exist because this
mechanism's most likely silent failure is a check that never fires.

## 8. Two holes the self-audit found in my own work

**1. `banner_colour` had TEST-ONLY absence of coverage** — `replay_verdict.py` measured
98%, and the one missing line was `banner_colour`'s only statement, because its only
caller lives in the coverage-omitted `gui/`. This is 07-06's `lit_cells` finding in a new
place, and it was tested rather than excused: a `FAILED` banner painted the OK green
would be a lie on the one screen a grader screenshots, and a state with no entry raises
`KeyError` at render time rather than at import. All four modules are now at **100%**.

**2. `verdict_for` was reachable from tests only** — D7-3's finding, in this plan's own
work, found by grepping production callers for every new public name. Rather than ship a
second entry point nothing on the screen's path uses, it was **removed**, its absence
recorded in source with the reason, and callers take `open_replay(path).verdict` — the
exact value the banner renders. A measurement taken through a parallel helper would be
evidence about the helper.

**AST scan** over all seven of this plan's test/fixture files: **0 `parametrize` sites**
(the four tampers are four tests, deliberately) and **3 assert-bearing loops**. Two
carried inline literal tables and are now named and floored (`BAD_DIGESTS == 3`,
`REFUSED_NAMES == 4`); the third pair is 07-06's and is already guarded.

## 9. Gates

```
uv run ruff check .                       All checks passed          (0 violations)
uv run pytest tests/ --cov                2130 passed, 0 failed      (baseline 2090)
                                          coverage 97.37%            (baseline 97.29%)
bash scripts/check_line_limit.sh          exit 0                     (no-arg, tracked)
  + all 15 new/touched files by path      exit 0
uv run python scripts/check_local_truth.py  OK: 7 module(s) scanned, exit 0  (was 5)
uv run python scripts/check_no_llm_in_strategy.py  OK
uv run python -m pursuit.gui.replay_app --help     exit 0
  ... --artifact <real log_> --step-ms 600 --once  exit 0
  ... --artifact logs/police/<uid>.jsonl           exit 2, message names rule 18
uv run python scripts/dev_launch.py       exit 0, game 55fa28cbef618a19
                                          both seats matched=true, capture,
                                          0 technical_win, 0 watchdog_incident
grep json.dumps services/reporting/       5 hits, all inside docstrings forbidding it
git diff config/                          EMPTY
git check-ignore, every new .py           none ignored (D7-10's guard)
graphify update .                         10266 nodes / 18371 edges / 588 communities
                                          open_replay -> replay_verify.py:163, degree 11,
                                          with `<-- main() [calls]` found independently
```

File sizes, all ≤ 150 code lines:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| `replay_verify.py` | 142 | | `test_replay_verify_boundary.py` | 134 |
| `replay_session.py` | 139 | | `test_replay_roundtrip.py` | 139 |
| `replay_verdict.py` | 98 | | `test_replay_verify.py` | 111 |
| `replay_source.py` | 60 | | `test_replay_session.py` | 104 |
| `replay_app.py` | 132 | | `replay_fixtures.py` | 144 |
| `replay_panels.py` | 49 | | `local_truth_helpers.py` | 41 |
| `test_gui_structural.py` | 147 | | `test_log_artifact_reachability.py` | 149 |

### Rule-38 counters — all four numbers, read directly (the files are gitignored)

| | police | thief |
|---|---|---|
| before full `pytest` | 1921 | 1914 |
| after full `pytest` | **1921** | **1914** |
| **suite delta** | **0** | **0** |
| before `dev_launch.py` | 1920 | 1913 |
| after `dev_launch.py` | **1921** | **1914** |
| **one-real-game delta** | **1** | **1** |

Nothing in this plan reads, writes, defaults or reads around the counter. Its **value**
stays the human's at 07-10 (OQ-5). **Nothing transmits:** the viewer opens one local
file and draws it.

## 10. Deviations from Plan

### Auto-fixed

**1. [Rule 3 — blocking] Four `services/` modules instead of the plan's one.**
`replay_verify.py` measured **183** combined against the 150-code-line gate. Split along
seams the file already had, and **split, never compressed** — not one line of any
docstring or body was shortened. `replay_verdict.py` is the dependency-free leaf holding
the words and shapes (the `log_artifact_fields.py` precedent); `replay_source.py` owns
*which file may be read* and the in-progress-game decision; `replay_session.py` owns the
cursor and the strings, which had to live outside `gui/` anyway. `replay_verify.py`
re-exports every public name, so the Tk layer keeps the one import path
`check_local_truth.py:80` allows.

**2. [Rule 3 — blocking] Four test files plus two non-test modules.** The plan named two
test files; the 150-line gate and the self-audit forced
`test_replay_verify_boundary.py`, `test_replay_session.py`, and the fixture module
`replay_fixtures.py` (not `test_*`, so pytest collects nothing from it — the
`artifact_log_games.py` precedent).

**3. [Rule 3 — blocking] `tests/unit/local_truth_helpers.py` extracted.**
`test_check_local_truth.py` and `test_gui_structural.py` each carried their own
`_check`/`_tree`; this plan's import-allowlist tests would have made a third copy, which
CLAUDE.md Table 5 forbids. Both prior copies now fold onto it. That also kept
`test_gui_structural.py` at 147/150 without compressing anything.

**4. [Rule 2 — missing critical] The artifact seal is checked as well as the turns.**
Not in the plan, which named only the per-turn re-hash. `outcome`, `audit_verdict`,
`prior_game_uids`, `truncated_tail` and every hint text sit inside `SEALED_FIELDS` and
inside no commit hash, so a viewer checking only turn hashes would show `Verified OK`
over a rewritten outcome. Ordered **after** the per-turn checks so the four field
tampers still name a turn.

**5. [Rule 2 — missing critical] The public surface shrank by one.** `verdict_for` had
no production caller and was removed (§8).

**6. [Rule 1 — bug in this plan's own test] `test_log_artifact_reachability.py`'s exact
reacher list needed two new entries.** The two replay modules take `LogArtifactField` and
`TurnField` and are therefore reachers. The list stays **exact** (never widened to a
`>=`), and the reader/writer distinction it used to imply is now pinned separately by an
AST binding scan in `test_replay_verify_boundary.py`, with its own control.

### Out of scope, filed not fixed

- **D7-5** — the recoverable `handshake -> handshake` transition still fires once per
  run. Pre-existing, unclaimed, untouched.
- `check_no_llm_in_strategy.sh` is still absent from `quality-gate.yml`. Pre-existing
  since 03-10; not something to slip into a commit about a different subject.
- **D7-19 filed** — the dev-run `game_artifacts/{police,thief}/` output was **removed
  rather than committed**, matching 07-05 and 07-07, but none of the three had written
  down that the next executor has to. `game_artifacts/` is deliberately not ignored
  (that is D7-1's resolution), so every `dev_launch` leaves 8 untracked files that one
  `git add -A` would publish as league evidence. Owner is 07-10, which knows which files
  are real evidence and which are debris.

### Authentication gates

None.

## 11. Task Commits

| Hash | Message |
|---|---|
| `bd1ce8d` | `feat(07-08): the verifier -- three verdicts, and the empty one is not OK` |
| `cce667a` | `feat(07-08): the replay window -- two thin files that render and decide nothing` |
| `f67e6b1` | `test(07-08): the round trip -- a real game, both sources deleted, and the caller` |
| `cbc6e97` | `test(07-08): two findings in my own work -- an untested colour, two unfloored tables` |
| *(this commit)* | `docs(07-08): complete the replay viewer plan` — this SUMMARY, STATE.md, the ticked phase TODO row and the refreshed graph |

## 12. What 07-09 and 07-10 must know

* **07-09 takes criterion-3 evidence through `open_replay(path).verdict`.** There is
  deliberately no one-call `verdict_for(artifact)`; that value IS the banner, and a
  measurement through a parallel helper would be evidence about the helper.
* **All three states must appear in the GATE-7 report,** not just the OK one. A run that
  only ever shows `Verified OK` proves nothing — feed it the tamper and the zero-turn
  case too, as `test_replay_roundtrip.py` does.
* **07-10 screenshots the banner.** It needs `--step-ms` stated at launch (OQ-6: the
  repository holds no UI interval), and the artifact path must be a real
  `log_<game_id>_g<NN>.json` — the app refuses anything else, including the `.jsonl`.
  The three colours are pinned by test, so a screenshot showing green is showing OK.
* **The viewer cannot be pointed at a live game.** Decided, refused by name, tested.

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 17 claimed paths verified present on disk with `[ -f ]` **and** verified TRACKED by
git with `git ls-files --error-unmatch`, plus `git check-ignore` clean on every one
(D7-10's guard). All four claimed commit hashes verified reachable in
`git log --oneline --all`.

Every number in this document came off a command run in this session: the two
suite/coverage figures, the four counter readings, the seven probe counts, the 5/5 and
10/10 real-game measurements, the three banner strings read back off the rendered
widget, the graph's node and edge counts, and all 15 line counts — **re-measured with
the gate's own `awk` after the last edit**, which corrected `test_replay_verify.py` from
121 to 111 and `test_replay_verify_boundary.py` from 130 to 134.

The suite arithmetic was reconciled rather than assumed: 2130 − 2090 = 40, which is
exactly the 39 tests collected in this plan's four new test files plus the one added to
`test_gui_structural.py`. Production callers were grepped for every new public name; the
one with test-only reachability (`verdict_for`) was removed rather than excused.
