---
phase: 08-submission-and-league-operations
plan: 09
subsystem: research
tags: [sensitivity-analysis, token-cost, prompt-log, notebook, segal-17, segal-8.3, offline, wilson]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-01's scripts/check_submission.py -- the gate whose G1-14 / G5-02 / G5-03 / G5-05 rows this plan closes"
  - phase: 03-blind-strategy-module-rl-policy
    provides: "training/arena.run_match + training/joint_game.play_game and artifacts/run2/weights.json -- the offline harness every sweep number is measured through"
  - phase: 04-language-and-scent
    provides: "docs/phases/phase-4/gate4_measurement_{live,mocked}.json -- the ONLY recorded token spend, and the two services/llm prompts the log documents"
  - phase: 05-cloud-exposure-and-tunneling
    provides: "docs/phases/phase-5/remote-round-*/ wire logs -- the 79 real hint sentences behind the prompt-revision measurement"
  - phase: 07-reporting-and-visualization-shell
    provides: "services/llm/budget.py's TokenBudget.report() and the D-35 degrade ladder the projections are read against"
provides:
  - "docs/SENSITIVITY.md -- which parameters move outcomes, measured at n=200 with 95% Wilson intervals, plus the fixed list it did not touch"
  - "docs/TOKEN-COST.md -- the language layer's cost surface from the one recorded live game, with a ranked optimization strategy"
  - "docs/PROMPT_LOG.md -- Segal 8.3, both the agent's prompts and the codebase's"
  - "notebooks/analysis.ipynb -- the first tracked notebook, executing offline with three committed figures"
  - "scripts/sensitivity_status.py -- PARAMETERS.md's Status column as a refusal any future sweep can reuse"
  - "artifacts/sensitivity/{sweep,reconcile}.json and artifacts/token_cost/token_cost.json"
affects: [08-10, 08-11]

# Tech tracking
tech-stack:
  added: [nbconvert, ipykernel, nbformat]
  patterns:
    - "a document's every number RENDERED from a committed artifact, with a test that re-renders and compares -- hand-editing a figure fails the suite"
    - "a rule's Status PARSED out of the extract and used as a refusal, so a grid cannot grant itself permission it does not have"
    - "an offline property PARSED off the AST (import allowlist + literal_eval'd manifest) rather than grepped, because the prose contains the forbidden strings"
    - "a contradiction with an older document published, re-measured across the variables that could explain it, and left explicitly unresolved"
key-files:
  created:
    - docs/SENSITIVITY.md
    - docs/TOKEN-COST.md
    - docs/PROMPT_LOG.md
    - notebooks/analysis.ipynb
    - scripts/sensitivity_status.py
    - scripts/sensitivity_grid.py
    - scripts/sensitivity_sweep.py
    - scripts/sensitivity_report.py
    - scripts/sensitivity_reconcile.py
    - scripts/token_cost_read.py
    - scripts/token_cost_prompts.py
    - scripts/token_cost_report.py
    - scripts/prompt_log_evidence.py
    - tests/unit/test_sensitivity_grid.py
    - tests/unit/test_token_cost.py
    - tests/unit/test_notebook_offline.py
    - tests/unit/test_research_docs.py
    - artifacts/sensitivity/sweep.json
    - artifacts/sensitivity/reconcile.json
    - artifacts/token_cost/token_cost.json
  modified:
    - docs/SUBMISSION-CHECKLIST.md
    - docs/TODO.md
    - docs/phases/phase-8/TODO.md
    - docs/phases/phase-8/submission_audit_evidence.json
    - pyproject.toml

decisions:
  - "The sweep's legality is a PARSE, not a promise. sensitivity_status.py reads docs/PARAMETERS.md's Status column (32 rows, 14 fixed) and refuse_fixed() fails when a knob targets a fixed row, names a row that does not exist, or declares a status the extract contradicts; refuse_downward() fails a `minimum` swept below the shipped value. The fixed list the document prints comes from that same parse."
  - "The ENGINEERING-LOG Act 4.3 contradiction is PUBLISHED, not resolved. The sweep measures 32.0%/7.5% where the log records 89%/1%; eight arms were re-measured and none reproduces it. The direction of the shipped resolution-rules decision is confirmed and unchanged; the magnitude is not; the cause was not established and the document says so. Correcting the three documents that quote the pair is named as a follow-up 08-09 did not own."
  - "The notebook's offline property is parsed off the AST, never grepped. Its own prose and its own guard list both contain the string 'logs/', so a substring scan would have to be weakened until it caught nothing. The INPUTS manifest is ast.literal_eval'ed and each path put to `git ls-files`; the import set is held to {json, pathlib, matplotlib}."
  - "The notebook is committed WITH its executed outputs. Segal 2.4 asks for a notebook with graphs, and a grader browsing GitHub sees figures only if the outputs are stored. 309 KB, regenerable in 4.6s."
  - "The mocked GATE-4 run is compared on CALLS and on nothing else. Its own note says its per-call token counts are simulated; they are 9.83x from the live figures, so pooling them would corrupt every budget projection. compare_call_rate() is the single place the two sources meet."
  - "TOKEN-COST's S2 is recorded as BLOCKED on a named missing measurement rather than given a number. Lowering model.max_tokens is the highest-leverage change available, but the safe floor needs max(output_tokens) per call and the n=1 record stores only a total and a mean. Inventing the floor would have been inventing a numeric value."
  - "'Call the model less often' is listed as a REJECTED lever with its citation. every_n_steps would halve the call count and language_model_config.py:78-83 refuses any value above 1, because 10.4's GATE-4 criterion 3 requires a hint every turn. Listed so the next reader does not rediscover it as an idea."

metrics:
  duration: "~5h"
  tasks_completed: 7
  files_created: 20
  files_modified: 5
  completed: 2026-08-17
---

# Phase 8 Plan 09: Research and Visualization Summary

The four §17 research artifacts the repository had none of — a measured sensitivity analysis,
an offline notebook, a token-cost analysis with an optimization strategy, and the §8.3 prompt
log — each generated from a committed artifact by a committed script, with a test that
re-renders and compares so no published number can be hand-edited.

**No individual plan file exists for 08-09.** It was executed from
`.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` §9, the same way
08-07 and 08-08 were.

---

## Gate movement

`uv run python scripts/check_submission.py`, 86 rows, exit **1** both before and after:

| | PASS | GAP | UNJUDGED |
|---|---:|---:|---:|
| At `5a28a2f` (before) | 65 | 8 | 13 |
| At `aac4cf8` (after) | **69** | **4** | 13 |

| Row | Was | Now | Evidence the gate reads |
|---|---|---|---|
| **G1-14** prompt-engineering log | GAP | **PASS** | `docs/PROMPT_LOG.md` tracked, 199 non-blank lines |
| **G5-02** sensitivity analysis | GAP | **PASS** | `docs/SENSITIVITY.md` tracked, 212 non-blank lines |
| **G5-03** analysis notebook | GAP | **PASS** | tracked `*.ipynb`: 1 (was 0) |
| **G5-05** token-cost analysis | GAP | **PASS** | `docs/TOKEN-COST.md` tracked, 160 non-blank lines |

**Exactly four rows moved, and they are exactly the four this plan owns.** No other row
changed verdict in either direction. The four that remain belong elsewhere: G1-03b and G5-04
(the screenshots — 08-06 with 07-10's material), G6-08 (the tag — 08-11/08-12) and T5-06 (the
`version.py` / `pyproject.toml` reconciliation — 08-11). 08-09 added no image, so G5-04 sits
exactly where it was; a learning curve is still not a screenshot of a running system.

The gate's own anti-vacuity state was re-observed: `--empty-probe` exits **2**.

---

## What was measured

### Sensitivity — 13 configurations × 3 matchups × 200 games, 755.6s, offline

One factor at a time from the shipped configuration, through `training/arena.run_match` —
the same harness the Phase-3 curves were fitted with. No network, no API key, no counter.
Separable = non-overlapping 95% Wilson intervals, `arena.compare`'s conservative rule.

| Knob | Largest separable effect | Where |
|---|---:|---|
| `board_size` = 11 | **+35.0pp** thief survival | vs barrier-blind chaser |
| `horizon` = 70/70 | **−29.0pp** | vs sealing chaser |
| `resolution_rules` swap on | **−25.0pp** | vs barrier-blind chaser |
| `weights` = prior | **−18.0pp** | vs barrier-blind chaser |
| `equilibrium_iterations` 50 or 800 | −2.0 to −6.0, **separable nowhere** | — |
| `barrier_quota` 21 or 28 | −1.0 to −3.0, **separable nowhere** | — |

The negotiation consequences are stated where they belong: board size and horizon are both
`minimum` parameters an opponent may legitimately propose upward, and they run in opposite
directions for us. Extra barriers beyond 14 are close to free. `valuebrain.py`'s claim that
200 regret-matching iterations is "comfortably converged" now has a measurement behind it.

**The cop matchup is 200/200 at the baseline and is flagged SATURATED**, in the document, in
the notebook and in the renderer — the effect ranking refuses to rank a knob on it at all.

### Token cost — one live game, and every projection labelled as one

From `gate4_measurement_live.json` (23 calls, `claude-haiku-4-5-20251001`, 2026-08-09):

* **96.4%** of spend is input; the **system prompts are 91–96%** of each call's input
  characters and are re-sent every call, because Haiku's cacheable-prefix minimum is far
  above either prompt.
* The shipped `_estimate_tokens` **over-reserves 1.35×**, and the cause is located: the
  `max_tokens=300` ceiling is 42.5% of every reservation while real output averaged 19.1
  tokens per call. `reserve()` runs before the call and the level never regresses, so the
  degrade ladder trips about a third earlier than the real spend warrants.
* **A maximal series does not fit the budget.** 30,180 tokens per full-length game × 10 games
  (Table 18 row 5, **fixed**) = 301,800 against 200,000. The ladder absorbs it — `SHORT_PROMPT`
  at ~4.6 games, `TEMPLATE_ONLY` at ~6.0 — so the language layer goes dark for roughly the
  last four games of a maximal series. Nobody had written that down.
* The mocked run transfers on **calls** (1.643 vs 1.662, ratio 0.989) and is **9.83×** away on
  tokens. Pooling them would have corrupted every projection.

### Prompt log — one prompt revision measured end to end

`bluff_prompt.py` originally said *"phrasing a claim **for** a player"*. On 2026-08-13 it
produced *"The player is currently positioned near the eastern edge of the grid."* — asked to
write **for** someone, the model wrote **about** them. `50ac2fe` put the model in the seat.
Across the tracked wire logs: **1** third-person sentence in the 10 hints before, **0** in the
69 after. The entry states its own limit — a 10-hint before-sample, rounds not otherwise
controlled — and the third-person rule is labelled a narrow mechanical proxy where it prints.

Part B records how the codebase was prompted, with reproducible evidence for each practice
(**31 of 87** plan summaries contain *vacuous*/*vacuity*) and a section on what did **not**
work.

---

## The contradiction this plan found and did not resolve

`docs/phases/phase-3/ENGINEERING-LOG.md` Act 4.3 records thief survival against a
barrier-blind chaser as **89% → 1%** across the swap decision, and `PRD.md`, `PLAN.md` and
`shared/resolution.py`'s `PREFERRED` docstring all quote it. The sweep measures **32.0% →
7.5%**.

`scripts/sensitivity_reconcile.py` **parses both old percentages out of the log** — so the
comparison cannot drift from the document it checks — and re-measures all eight
weights × rules × opening combinations at n=200. The highest arm is 52.5%. None reproduces
89%, and none approaches 1%.

**What this licenses and what it does not.** The shipped decision is unchanged and needs no
change: declining the swap is still worth ~25pp of thief survival and the cop seat is at 100%
under all four rule combinations, so the swap still buys the cop nothing. What is *not* safe
is quoting "89% to 1%" as a current measurement. The engine moved through Phases 4–6 since
Act 4.3; this plan did **not** re-derive which change is responsible and says so rather than
guessing. Correcting the three quoting documents is recorded in
`docs/SUBMISSION-CHECKLIST.md` as a follow-up 08-09 did not own.

---

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — Blocking] `nbconvert`, `ipykernel` and `nbformat` were not in the tree**
- **Found during:** Task 4 (the notebook)
- **Issue:** the outline's acceptance is "`nbconvert --execute` exits 0"; nothing in the
  repository could execute a notebook.
- **Fix:** `uv add --dev nbconvert ipykernel nbformat`. Dev group only — the shipped agent
  imports none of them, so a league runtime is unchanged.
- **Files modified:** `pyproject.toml`, `uv.lock` · **Commit:** `32440b4`

**2. [Rule 1 — Bug] `ruff` lints notebooks; the setup cell had a Yoda condition (SIM300)**
- **Found during:** the post-commit gate run
- **Fix:** rewrote the condition and **re-executed the notebook** so its stored outputs still
  correspond to its source, rather than editing the source under stale outputs.
- **Files modified:** `notebooks/analysis.ipynb` · **Commit:** `bcce41b`

**3. [Rule 1 — Bug] a citation in this plan's own first draft did not resolve**
- **Found during:** Task 5, by the citation test written in the same task
- **Issue:** `scripts/sensitivity_status.refuse_fixed` is a function reference, not a file,
  and the check 08-07 introduced correctly rejected it. It appeared in three places
  (the document, the renderer that generates it, and the notebook).
- **Fix:** reworded to `` `scripts/sensitivity_status.py`'s `refuse_fixed` `` in all three,
  and the block re-rendered and re-spliced. · **Commit:** `32535b7`

### Scope additions

**4. `scripts/sensitivity_reconcile.py` was not in the outline.** The sweep contradicted a
shipped document; the honesty rule binding this plan says every published number must be
reproduced by a committed runnable script, so the reconciliation could not be prose.
**Commit:** `486a01a`

### Deferred

**Correcting `ENGINEERING-LOG.md`, `phase-3/PRD.md`, `phase-3/PLAN.md` and
`shared/resolution.py`'s docstring** where they quote 89%/1%. Recorded in
`docs/SUBMISSION-CHECKLIST.md`. Not done here because the *cause* is unestablished, and
replacing one unexplained number with another is not a correction.

---

## Self-audit: two vacuities found in this plan's own tests

Neither would have failed anything; both would have looked like coverage. Both fixed and
probed in `aac4cf8`.

**1. `test_every_cited_commit_hash_resolves` was parametrized over three documents and only
one cites a commit.** Two of its three parametrizations iterated an empty set and passed
having checked nothing — the regex was proven live by a third of its runs. Now gathers across
all three with a floor of 3. **Probed:** `50ac2fe` → `dead1ee` fails with *"Not a valid object
name"*.

**2. `test_no_document_claims_a_league_result` had a disjunct whose trivial branch is the one
`PROMPT_LOG.md` takes** (`"no league game" in text OR "league" not in text`). Deleting the
disclaimer from all three documents *and every mention of the league with it* would have
passed. Now asserts the non-trivial branch is exercised at least twice. **Probed:** removing
both disclaimers fails with *"mentions the league without the clause"*.

A third, caught during authoring rather than after: `test_token_cost.py`'s empty-evidence
probe originally used a fixture with **both** token totals at zero, so deleting the guard made
it fail on `ZeroDivisionError` rather than its assertion — it would have kept passing if
anyone had "fixed" the crash by guarding the division instead of the evidence. The fixture now
records a non-zero output total and the test fails with `DID NOT RAISE`. Written up in
`docs/PROMPT_LOG.md` B2.

### Assertions proven RED, then reverted

| Mutation | Landing confirmed | Result |
|---|---|---|
| `refuse_fixed`'s FIXED branch → `pass` | `"is FIXED in docs"` absent from source | 2 failed / 12 passed |
| `live_spend`'s empty-evidence guard deleted | `"no usable live spend"` absent from source | 1 failed (`DID NOT RAISE`) / 9 passed |
| notebook input repointed at `logs/sweep.json` | string present in the `.ipynb` | 2 failed / 3 passed, plus the notebook's own in-cell assertion |
| `50ac2fe` → `dead1ee` in `PROMPT_LOG.md` | `` `dead1ee` `` present | 1 failed / 12 passed |
| both league disclaimers removed | `"no league game"` absent from both | 1 failed / 12 passed |
| `96.4%` → `99.9%` inside the token-cost block | asserted `!=` original in-test | permanent test, always green-on-tamper |

Every mutation was reverted and the suite re-run green afterwards.

---

## Reproduction proof

Every published figure regenerated at HEAD and compared against what is committed:

| Block | Regenerated | Present verbatim in |
|---|---:|---|
| sensitivity sweep | 5,008 chars | `docs/SENSITIVITY.md` ✓ |
| reconciliation | 1,014 chars | `docs/SENSITIVITY.md` ✓ |
| token cost | 2,093 chars | `docs/TOKEN-COST.md` ✓ |
| prompt evidence | 930 chars | `docs/PROMPT_LOG.md` ✓ |

`artifacts/token_cost/token_cost.json` rebuilds **byte-identical**
(`sha256 693efe19…` both times). The sweep's baseline cell reproduces exactly on a fresh
200-game run: 116/200, 65/200, 200/200 — the seeded arena is deterministic.

**37 distinct cited repository paths across the three documents; 0 unresolved.** All five
published commands run.

---

## Verification

| Gate | Result |
|---|---|
| `uv run pytest` | **2455 passed / 0 failed** (was 2413; +46 new, −4 from de-parametrising two tests during the self-audit) |
| `uv run pytest --cov` | **97.44%** — unchanged from baseline, against `fail_under = 85` |
| `uv run ruff check .` | **0 violations** (ruff lints the notebook too) |
| `scripts/check_line_limit.sh` | 0 violations; the nine new `scripts/` files also checked **explicitly by path**, since that glob does not reach them |
| `scripts/check_local_truth.sh` | OK, 7 modules |
| `scripts/check_no_llm_in_strategy.sh` | OK, no forbidden imports |
| `scripts/check_submission.py` | exit **1** at 69/4/13; `--empty-probe` exit **2** |
| `jupyter nbconvert --execute` | exit **0**, 4.6s, 3 figures |

### Counter deltas — rules 37/38

| | police | thief |
|---|---:|---:|
| Before the full suite | 1927 | 1920 |
| After the full suite | **1927** | **1920** |
| **Delta** | **0** | **0** |

**No real game was played by this plan.** 08-09 delivers documents; nothing in it needs a
game, and advancing the shipped counter to demonstrate a delta would be a state change with no
deliverable behind it. The "one real game advances each counter by exactly one" contract is
inherited from Phase 7 and was **not** re-measured here — recorded as inherited rather than
claimed as measured.

`config/*/games_played.json` is untouched, and **nothing in this plan sets, infers or
publishes a games-played value** (rule 38).

### Remote

**No remote command was issued.** No `push`, no `tag`, no `fetch`, no `remote`. `git tag -l`
is still empty. `game_artifacts/police/` and `game_artifacts/thief/` remain **untracked**
(D7-19) and every commit staged explicit paths — no `git add -A` anywhere.

---

## Commits

| Hash | Message |
|---|---|
| `32440b4` | `chore(08-09)` nbconvert + ipykernel as dev deps, for the offline notebook |
| `486a01a` | `feat(08-09)` the sensitivity sweep, and the refusal that keeps it legal |
| `a8931b7` | `feat(08-09)` token-cost analysis from the recorded spend, never a fresh call |
| `bcce41b` | `feat(08-09)` the offline analysis notebook, executed and probed |
| `32535b7` | `docs(08-09)` SENSITIVITY, TOKEN-COST and PROMPT_LOG -- G5-02, G5-05, G1-14 |
| `112bd6f` | `docs(08-09)` the register, the trackers and the evidence JSON at 4 GAP |
| `aac4cf8` | `test(08-09)` close two vacuities found in this plan's own self-audit |

---

## What 08-10 and 08-11 inherit

* **`notebooks/` is a new top-level directory** and must survive the split. `analysis.ipynb`
  reads four tracked artifacts under `artifacts/`; a split that drops `artifacts/` leaves the
  notebook unable to execute, and `tests/unit/test_notebook_offline.py` will fail inside that
  tree rather than pass quietly.
* **`tests/unit/test_research_docs.py::test_every_cited_commit_hash_resolves` skips when
  `git rev-list --count HEAD` is under 50.** That is deliberate, for 08-10's single-initial-
  commit outputs, and the skip names its reason. Every other test in the file runs there.
* **Three new dev dependencies** are in `pyproject.toml`; `uv sync` inside each split output
  must still resolve them.
* **The 89%/1% correction is open** and touches `docs/phases/phase-3/{ENGINEERING-LOG,PRD,PLAN}.md`
  and `src/pursuit/shared/resolution.py`'s docstring.
* **`docs/TOKEN-COST.md` names one missing measurement** — `max(output_tokens)` per call —
  which is a one-line addition to `scripts/gate4_runner.py`'s accounting and unblocks the
  highest-leverage config change available.

---

## Self-Check: PASSED

* **25 of 25** paths named in `key-files` exist on disk.
* **7 of 7** commit hashes resolve via `git cat-file -e <hash>^{commit}`.
* **37 of 37** repository paths cited across the three new documents resolve, and
  `tests/unit/test_research_docs.py` enforces that permanently.
* All **5** commands published in the documents run to exit 0.
* All **4** generated blocks re-render and match the committed documents byte for byte.
* Counters `1927 / 1920` before and after the full suite. Nothing pushed, no tag, no remote
  command.
