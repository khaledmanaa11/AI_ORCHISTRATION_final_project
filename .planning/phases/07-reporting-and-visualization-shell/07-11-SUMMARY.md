---
phase: 07-reporting-and-visualization-shell
plan: "11"
subsystem: strategy/display-belief
tags: [D-74, D7-8, D7-9, REPORT-02, STRAT-05, QUAL-11, rule-8, rule-9, rule-22, rule-38, D-18]
one_liner: "A display-only BeliefMap that is never fed ctx.state.thief, published in place of the cop's strategy posterior -- because that posterior was a 1.0 delta ON the engine's answer, and the published support was the legal-move plus centred on the true cell, which inverts back to it uniquely even after the argmax field is deleted."
requires:
  - "07-03: sdk/local_view.py, sdk/view_builder.py and its firewall tests -- this plan repairs their fixtures and adds the question they structurally cannot ask"
  - "04-11: strategy/beliefadapter.py's Figure-7 pipeline and BeliefMap"
provides:
  - "strategy/display_belief.py: DisplayBelief -- rule 9's ONE owner, with published_belief()/published_scent()/publishable() and the shared positive_cells()"
  - "docs/PRD_display_belief.md: the per-mechanism PRD (CLAUDE.md Sec2.3) carrying the measurements, the option (a)/(b) decision and the floor derivations"
  - "shared/display_config.py: DisplayFloors + MAX_STEP_NEIGHBOURHOOD, derived from len(DIRECTION_WORDS)"
  - "shared/belief_keys.py: BeliefKey moved down so a group module can name its own fields without importing its own importer"
  - "shared/scent_likelihood_config.py: 04-05's checks, moved verbatim at the 150-line gate"
  - "tests/unit/local_view_production.py: seed_belief_as_production_does + the geometric inversion attack"
  - "tests/unit/local_view_scanner.py: 07-03's scanner, split from the fixtures it can no longer be trusted alongside"
affects:
  - "07-06 (live GUI) may now consume LocalView without shipping a disqualification; it was BLOCKED on this"
  - "07-08 (replay viewer) inherits D7-8: belief_argmax stays in the JSONL audit record and must not be rendered live"
  - "Every future reader of sdk/local_view.py -- three of its docstrings asserted the opposite of the measured behaviour"
tech-stack:
  added: []
  patterns:
    - "A second, deliberately impoverished model published in place of the accurate one, when the accurate one is accurate for a forbidden reason"
    - "Redaction keyed on PROVENANCE (a contamination flag) rather than on a role name, so a future path that contaminates a different seat is covered without an edit"
    - "A recovery test (invert what is drawn) alongside an absence test (scan for what is named) -- neither replaces the other"
    - "Config floors DERIVED from a structural constant (len(DIRECTION_WORDS)) rather than picked, and refused by the loader if they would admit the measured leak"
key-files:
  created:
    - src/pursuit/strategy/display_belief.py
    - src/pursuit/shared/display_config.py
    - src/pursuit/shared/belief_keys.py
    - src/pursuit/shared/scent_likelihood_config.py
    - docs/PRD_display_belief.md
    - tests/unit/test_local_truth_recovery.py
    - tests/unit/test_thief_belief_unpublished_change.py
    - tests/unit/local_view_production.py
    - tests/unit/local_view_scanner.py
    - tests/unit/strategy/test_display_belief.py
  modified:
    - src/pursuit/strategy/beliefadapter.py
    - src/pursuit/sdk/view_builder.py
    - src/pursuit/sdk/local_view.py
    - src/pursuit/shared/belief_config.py
    - config/police/belief.json
    - config/thief/belief.json
    - tests/unit/local_view_fixtures.py
    - tests/unit/test_local_view_firewall.py
    - tests/unit/test_view_builder.py
    - docs/phases/phase-7/TODO.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
key-decisions:
  - "OPTION (a): a display-only BeliefMap never fed ctx.state.thief, published in place of the strategy map. Option (b) -- publish only when observe_exact did not fire -- is for the COP a permanently blank panel, because turn_language.py:57 returns the true cell on every turn but turn 0; it hides the leak by deleting the feature"
  - "The strategy belief is UNCHANGED and still receives known_cell: the provenance is the opponent's own honest Reveal and rule 9 governs the DISPLAY, not the provenance. Play is not degraded"
  - "scent.opponent is redacted too -- it leaks independently at exactly scent.json's source 0.9, and uniform scalar decay lets two published snapshots subtract to recover the fresh deposit"
  - "The substitution keys on a contamination flag, never on the role name 'cop', so the thief is untouched by construction and a future contaminated seat is covered without an edit"
  - "The display map is NOT fed scent_likelihood, which the strategy map is: that grid is stamped from the engine's answer, and feeding the display map its own emission instead would be circular"
  - "The floors are DERIVED (min_support_cells 6 > the 5-cell legal-move plus; min_entropy_bits 1.0 = a fair coin) and live in belief.json, never as literals in source"
  - "BeliefKey moved to shared/belief_keys.py: every group module is imported BY belief_config.py, so the newest group could not have named its fields canonically without a cycle"
metrics:
  tasks: 3
  commits: 3
  tests_added: 20
  suite: "1826 -> 1846 passed, 0 failed"
  coverage: "96.95% -> 96.95%"
  duration: "~3h"
  completed: 2026-08-17
status: complete
---

# Phase 7 Plan 11: The Display Belief Summary

**Commits:** `4c4c03d` (RED reproduction) -> `19aa946` (the fix, option (a)) -> `df041a0` (docstrings + the thief control).

Rules 8–9 make displaying the objective board state in the live interface an **absolute
disqualification**. 07-03 built a firewall against it and the firewall was green. This plan
found that it was green because it was blind, reproduced the disqualification in the
repository's own numbers through the shipped code path, and moved the decision into one
module that owns it in writing.

---

## 1. The reproduction (Task 1) — measured, not restated

Run through the production path — a real `BeliefAdapter.decide(..., known_cell=ctx.state.thief)`
with the shipped `config/police/` files, the same call `turn_language.choose_destination` makes:

```
ctx.state.thief (engine truth): (5, 3)
known_opponent_cell returned:   (5, 3)
identical?:                     True

belief argmax:  (5, 3) == truth? True
belief entropy: 1.8799649487271113
support:        [(4, 3), (5, 2), (5, 3), (5, 4), (6, 3)]   size 5 of 49
P(true):        0.5556
geometric inversion returned: [(5, 3)] == truth? True
scent.opponent argmax: (5, 3) == truth? True   value 0.9
```

`0.9` is exactly `"source": 0.9` in `config/police/scent.json` — the **unmixed kernel centre
on the true cell**, not a decayed trace.

**The sealed-thief endgame**, thief walled at a corner behind two barriers against
`"barrier_quota": 14`:

```
barrier_quota in config: 14 -- barriers spent: 2
argmax:     (0, 0)
entropy:    -0.0
lit cells:  [(0, 0, 1.0)]
```

A one-pixel heatmap painted on the truth, in the endgame that **is** the cop's win condition.

### 1.1 It happened in a real game, not only in a fixture

The `dev_launch.py` game run for this plan's verification (`logs/police/29dec44e0ab71785.jsonl`)
records the cop's strategy-belief entropy per turn:

| Turn | Cop `belief_entropy` | Thief `belief_entropy` |
|---|---|---|
| 0 | 5.6108 (uniform, log2(49) = 5.6147) | 5.6131 |
| 1 | **1.8800** | 5.6100 |
| 2 | **1.8800** | 5.5183 |
| 3 | **1.8800** | 5.4697 |
| 4 | **1.7159** | — |

The cop's map collapses to the leaked delta on turn 1 and stays there. The thief's stays
genuinely multi-modal, which is exactly why this plan is cop-side only.

### 1.2 The firewall's own fixtures were vacuous

Two independent defects, both fixed before any assertion in this area was trusted:

* `local_view_fixtures.scent_field` **never called `emit_opponent`**, so `view.scent.opponent`
  was an ALL-ZERO grid in every one of 07-03's thirty revert probes — the one field carrying
  the true cell at 0.9 was empty in every test written to protect it.
* `honest_context` seeded belief with `observe_exact(BELIEF_ARGMAX)` on `(6, 6)`, a cell
  production never supplies.

With both corrected to run one real `decide()`, **07-03's own load-bearing absence test
failed**:

```
FAILED test_opponent_true_cell_is_absent_from_the_serialised_view[asdict]
  AssertionError: rule 9 leak in the asdict view: ['$.belief.argmax: pair [5, 3]']
FAILED test_opponent_true_cell_is_absent_from_the_serialised_view[json]
```

RED at HEAD, in full: **9 failed, 45 passed** across the five affected files — the four
recovery assertions, the sealed case, and four pre-existing tests that had been passing on
the vacuous fixtures. The two anti-vacuity controls (`the inversion attack is not a no-op`,
`the scent peak reader is not a no-op`) **passed** at HEAD, so the attack was proven to fire
before it was ever used as evidence.

---

## 2. The decision (Task 2) — option (a), and why

Recorded in `src/pursuit/strategy/display_belief.py`'s module docstring and in full in
`docs/PRD_display_belief.md` §2.

| | **Option (a) — chosen** | Option (b) — rejected |
|---|---|---|
| Mechanism | A display-only `BeliefMap`, never fed `ctx.state.thief`, published in place of the strategy map | Publish the strategy belief only on turns where `observe_exact` did not fire |
| Cop-side result | A real heatmap on every turn | **A permanently blank panel**: `turn_language.py:57` returns the true cell whenever `turn > 0`, so `observe_exact` fires on every turn but turn 0 |
| Honesty | Publishes what a peer that ignored the Reveal would believe | Hides the leak by deleting the feature |

Option (b) is not a redaction policy; it is the removal of the panel. **Nobody owned rule 9
before this plan** — `beliefadapter.py:120-123` said in its own docstring that "local truth"
was "a display-layer concern, not this one's", and the display layer published the value
unredacted. `display_belief.py` owns it now.

**What the display map is fed:** the legal-motion `predict`, the declared barriers (rule 22 —
declared on the wire, shared knowledge) and the decoded hint likelihood (the opponent's own
broadcast claim). **What it is deliberately not fed:** `scent_likelihood`, which the strategy
map does take — that grid is stamped by `emit_opponent(known_cell)` from the engine's answer,
so feeding it back would re-import the truth through the side door, and feeding the display
map its own reconstructed trail instead would be circular.

### 2.1 Measured after the fix

| | HEAD (leaked) | After |
|---|---|---|
| published `belief.argmax` | **(5, 3)** = truth | **(1, 3)** |
| published entropy | 1.8800 | **5.5469** |
| support | 5 of 49 | **47 of 49** |
| P(truth) published | 0.5556 | **0.0223** |
| geometric inversion | **[(5, 3)]** | **[]** |
| `scent.opponent` peak | **(5, 3)** at 0.9 | **(4, 4)** at 0.154 |
| sealed thief | argmax (0,0), entropy −0.0, 1 lit cell | argmax **(1, 2)**, entropy **5.5472**, support **47** |
| **strategy** belief (never published) | argmax (5,3), entropy 1.88 | **argmax (5,3), entropy 1.88 — unchanged** |
| `scent.own` peak at the cop cell | 1.8 | **1.8 — passed through untouched** |

Play is not degraded: the strategy map still receives `known_cell`. Rule 9 governs the
display, not the provenance.

### 2.2 The floors

`config/{police,thief}/belief.json` gains a `display` group. **Neither number is invented**
(CLAUDE.md rule 1; both labelled engineering defaults per D-18, as every other number in
that file already is):

| Field | Value | Derivation |
|---|---|---|
| `min_support_cells` | 6 | One cell's legal destination set is STAY plus four orthogonal moves = `len(DIRECTION_WORDS)` = 5. A support of 6+ cannot fit inside any single cell's step neighbourhood, so the inversion returns `[]` — structurally impossible, not merely unlikely. |
| `min_entropy_bits` | 1.0 | One full bit is the entropy of a fair coin between two cells. Below that the map effectively *names* a cell. |

`validate_display_floors` **refuses** a `min_support_cells` at or below `MAX_STEP_NEIGHBOURHOOD`:
a floor that admits the measured leak is not a floor. Probe 11 confirms it (22 failed, 12
errors when the shipped config is lowered to 5).

---

## 3. The trap, run as a probe and pinned as a test (Task 3)

The plan warned that deleting `BeliefView.argmax` buys a clean verdict with the leak intact.
Measured, by applying exactly that change — strategy maps published again, `argmax` field
deleted:

```
test_local_view_firewall::test_opponent_true_cell_is_absent_from_the_serialised_view[asdict] PASSED
test_local_view_firewall::test_opponent_true_cell_is_absent_from_the_serialised_view[json]   PASSED
test_local_truth_recovery::test_the_belief_support_does_not_geometrically_invert_to_the_true_cell FAILED
test_local_truth_recovery::test_the_published_opponent_scent_peak_is_not_the_true_cell            FAILED
test_local_truth_recovery::test_the_published_belief_clears_the_configured_floors                 FAILED
========================= 3 failed, 2 passed =========================
```

**07-03's scanner returns a clean verdict on a payload from which the true cell is still
recoverable twice over.** `test_the_argmax_only_fix_would_still_leak` now pins this
permanently: it asserts the clean `[]` verdict *and* that the support inverts to
`[(5, 3)]` *and* that the scent peak is the true cell.

### 3.1 The thief control — byte-identical

`tests/unit/test_thief_belief_unpublished_change.py`, plus an out-of-band serialisation of
the thief's published belief and scent before and after the fix:

```
before: bytes 2565  sha256 0b046a9430b79af3d1b7f3a58a4bf91ffdce383d739d3d5267f3e03e1ba0e3b0
after:  bytes 2565  sha256 0b046a9430b79af3d1b7f3a58a4bf91ffdce383d739d3d5267f3e03e1ba0e3b0
THIEF PUBLISHED BELIEF: BYTE-IDENTICAL
```

argmax `(4, 5)`, entropy 5.5328, support 47 of 49 — genuinely multi-modal, and the anti-vacuity
case asserts it *stays* that way (`max(support) < 0.5`), so a symmetric "fix" that degraded
the panel would fail rather than pass the byte comparison against its own degraded self.

### 3.2 Three false docstrings corrected

Each new docstring states the truth **and** what it used to claim:

| Location | Used to claim | Why it was false |
|---|---|---|
| `local_view.py` module | `LocalView` "is a CLOSED set of frozen dataclasses that cannot express an opponent's true cell" | The set is closed and frozen; a dense probability grid still expresses a cell without any coordinate in it |
| `BeliefView` | `argmax` "is routinely wrong; that is exactly why it is legal to draw" | On the cop seat `observe_exact` made it **right every turn, by construction** |
| `ScentView` | `opponent` is "our own RECONSTRUCTION … one turn behind — not a live reading of where it is now" | Every clause was wrong: the kernel was stamped on the true **current** cell at full source strength |

---

## 4. Revert probes — twelve, every count real

Each mutation applied to the shipped source, the six affected test files run, the file
restored. Baseline **51 passed, 0 failed**.

| # | Mutation | Result |
|---|---|---|
| 1 | `view_builder` publishes the strategy belief again (the original leak) | **9 failed** |
| 2 | `view_builder` publishes the raw scent field again (the half fix) | **3 failed** |
| 3 | the argmax-only "fix" (see §3) | **3 failed, 2 passed** — the scanner passes |
| 4 | `publishable()` hard-wired `True` — the floor guard never fires | **2 failed** |
| 5 | contamination never recorded — the substitution never fires | **14 failed** |
| 6 | the display map IS fed the engine's answer | **9 failed** |
| 7 | the SYMMETRIC fix — the thief redacted too | **3 failed** |
| 8 | `DisplayBelief.advance` made inert — a fabricated uniform grid | **3 failed** |
| 9 | `geometric_inversion` always returns `[]` — the attack is a no-op | **2 failed** |
| 10 | `grid_argmax` always returns `(0, 0)` — the scent reader is a no-op | **2 failed** |
| 11 | `min_support_cells` lowered to 5 — a floor that admits the leak | **22 failed, 12 errors** |
| 12 | `published_scent` leaks the raw opponent grid while redacting belief | **3 failed** |

Probe 3's first attempt reported `PROBE BROKEN: anchor not found` — the anchor carried a
trailing `\n` and the working tree is CRLF. It was **not** counted as a pass; it was rewritten
to report per-test outcomes, which is the result above. Probes 8, 9 and 10 exist because the
mechanism's own most likely failure mode is a display map that is inert or an attack that
never fires, either of which would make every assertion in this plan pass vacuously.

## 5. Self-audit

* **AST scan of all eight touched test files.** One `parametrize` site
  (`test_opponent_true_cell_is_absent_from_the_serialised_view`, already length-guarded);
  one module-level literal iterated in an assert-bearing loop (`_FORBIDDEN_ANNOTATIONS`,
  already guarded). **Zero unguarded.**
* **Production callers grepped for all 13 new names.** Ten have external production callers.
  Three (`publishable`, `contaminated`, `MAX_STEP_NEIGHBOURHOOD`) are reached only from
  within their defining module — by `published_belief`/`published_scent` and by
  `validate_display_floors` respectively, all of which are themselves on the production path
  (`view_builder` → `published_*`; `load_belief_config` → `load_display_floors`). Not dead
  code; confirmed by probes 4 and 11, which fail when either is neutered.
* **Empty-input case guarded:** `geometric_inversion([], size) == []` is asserted, so the
  attack cannot pass by returning nothing on an empty support.

---

## 6. Deviations from Plan

### Auto-fixed / adjusted

**1. [Rule 3 — blocking] The plan's file paths do not exist**
- **Found during:** Task 1
- **Issue:** the plan names `tests/unit/sdk/local_view_fixtures.py` and
  `tests/unit/sdk/test_local_truth_recovery.py`; there is no `tests/unit/sdk/` directory —
  07-03 put the fixtures at `tests/unit/local_view_fixtures.py`.
- **Fix:** used the real paths, `tests/unit/` throughout.

**2. [Rule 3 — blocking] `config/police/belief.json` landed in Task 1, not Task 2**
- **Issue:** Task 1's RED assertion is "support and entropy above a floor", and the plan
  requires that floor to be a CONFIG value. A test asserting against a group that does not
  exist raises `AttributeError` at collection — an *error*, not a measured failure.
- **Fix:** the `display` group and its loader landed with the RED tests, inert until Task 2
  wired them. The RED run then failed on `assert 5 >= 6`, an assertion, as intended.

**3. [Rule 3 — blocking] Four files split at the 150-code-line gate**
- `shared/belief_config.py` (149/150) could not absorb a fifth group → `BeliefKey` moved to
  `shared/belief_keys.py` (which also removed a real cycle: every group module is imported
  *by* `belief_config.py`, so the newest group could not have named its fields canonically);
  `scent_likelihood`'s checks moved to `shared/scent_likelihood_config.py`.
- `tests/unit/local_view_fixtures.py` hit 157 → the scanner half moved to
  `tests/unit/local_view_scanner.py`. A real seam: one builds views and imports production
  code, the other only inspects a serialised one.
- `strategy/display_belief.py` hit 151 and `strategy/beliefadapter.py` 155 → the full
  rationale moved to `docs/PRD_display_belief.md`, which CLAUDE.md §2.3 requires for a
  central mechanism anyway, and `beliefadapter.py`'s Option-A/Option-B paragraph now points
  at `docs/phases/phase-3/PRD.md` §8 where that argument already lives.
- Split, never compressed. Every new file checked **explicitly by path**.

**4. [Rule 1 — bug, in this plan's own predecessor] `BELIEF_ARGMAX` removed**
- Two 07-03 tests asserted against a fixed belief argmax seeded by a call production never
  makes. With the fixture corrected, the real argmax **was** the true cell. Both tests now
  read the *published* argmax off the view and additionally assert it is not the opponent's
  cell — a strengthening, not a weakening: an argmax equal to the true cell would now fail
  the anti-vacuity test as well as the absence test.

### Out of scope, filed not fixed

- **D7-8** — `turn_language.belief_snapshot` still writes the true argmax to the JSONL. This
  is **correct**: the log is the audit record (rule 38) and rules 8–9 govern the live
  interface. 07-08's replay viewer inherits the constraint not to render it live.
- **D7-9** — `scripts/check_local_truth.py` hardening remains 07-06's. Restated because this
  plan widened the known blind spot: it is an import/attribute gate and **cannot** see a
  coordinate that is *drawn* rather than *named*. It was **not** cited as evidence anywhere
  in this plan.

### Authentication gates

None.

---

## 7. Verification

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed** (0 violations) |
| `uv run pytest tests/ --cov` | **1846 passed, 0 failed**; coverage **96.95%** (baseline 1826 / 96.95%) |
| `bash scripts/check_line_limit.sh` | **exit 0**, plus all nine new files checked explicitly by path |
| `uv run python scripts/check_no_llm_in_strategy.py` | **OK: no forbidden imports under `src/pursuit/strategy`** |
| `uv run python scripts/dev_launch.py` | **exit 0**, both sides `"matched":true` (`29dec44e0ab71785`) |
| graphify | refreshed; `DisplayBelief` present at `display_belief.py:50`, degree 25, edges to `BeliefMap`/`ScentField`/`DisplayFloors` and from `BeliefAdapter` |

### Rule-38 counters — all four numbers

| | police | thief |
|---|---|---|
| before full `pytest` | 1914 | 1907 |
| after full `pytest` | **1914** | **1907** |
| **suite delta** | **0** | **0** |
| before `dev_launch.py` | 1914 | 1907 |
| after `dev_launch.py` | **1915** | **1908** |
| **one-real-game delta** | **1** | **1** |

---

## 8. Commits

| Hash | Message |
|---|---|
| `4c4c03d` | `test(07-11): reproduce the rules 8-9 leak on fixtures that model production` |
| `19aa946` | `fix(07-11): stop the cop publishing the thief's exact cell -- option (a)` |
| `df041a0` | `docs(07-11): correct three false docstrings, add the thief-unchanged control` |

## 9. What 07-06 and 07-08 must know

* **07-06 was blocked on this and is now unblocked.** A live GUI over `LocalView` no longer
  ships a disqualification. It still owes the `check_local_truth.py` hardening (D7-9), and
  it must render `belief=None` gracefully — that is now a *live* case (the floor guard), not
  only the belief-disabled one.
* **07-08 must not render `belief_argmax` from the log while a game is live** (D7-8). The
  only shape a live panel may consume is `sdk/local_view.py`.
* **Do not "simplify" the two-map design into one.** The strategy map must keep seeing
  `known_cell` or play is degraded; the display map must never see it or the
  disqualification returns. Probes 5 and 6 fail loudly (14 and 9) if either is collapsed.

---

## Self-Check: PASSED

All 23 files claimed above verified present on disk by path. All three commits
(`4c4c03d`, `19aa946`, `df041a0`) verified present in `git log`. Every number quoted in this
summary was produced by a run recorded in this session, not carried over from the plan.
