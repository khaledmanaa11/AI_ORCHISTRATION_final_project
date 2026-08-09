# Phase 4 — resume point

**Updated:** 2026-08-09 · **Status:** ALL 8 WAVES EXECUTED (14/14 plans: 04-01..04-14). Phase 4
code, docs, and the GATE-4 measurement are all complete. **GATE-4 is measured and PASSING in
`--mocked` mode; the plan's own D-32 requirement (a real API game) is the single open item.**

Nothing is half-finished: every dispatched plan completed, merged, and passed the gates. The only
thing standing between this phase and `/gsd:verify-work 4` is one command a human runs with a real
key — see [The one open item](#the-one-open-item-live-gate-4-confirmation) below.

## Where things stand

All work is on branch **`claude/gsd-parallelism-config-6b4aqp`**. Get it with:

```
git fetch origin claude/gsd-parallelism-config-6b4aqp
git checkout claude/gsd-parallelism-config-6b4aqp
```

| Wave | Plan | Delivered | Summary |
|---|---|---|---|
| 1 | 04-01 | Locked scent model — Table 16 values + Figure-4 kernel, byte-identical `scent.json` both sides, digest `c0e6322…`; `ScentField` with independent own/opponent trails (D-49) | ✅ |
| 1 | 04-03 | API gatekeeper — Table 19 token bucket, D-35 budget ladder, FIFO queue that **queues on overflow rather than crashing** | ✅ |
| 1 | 04-04 | Language channel — direction-token move/barrier codec (coordinates off the wire), `MessageType.HINT`, atomic move+hint buffering | ✅ |
| 2 | 04-02 | Scent digest carried in the handshake — `SCENT_MISMATCH` distinct from `CONFIG_MISMATCH`, compared via `secrets.compare_digest` | ✅ |
| 2 | 04-05 | Belief map — legal-motion model, `BeliefMap` invariants, scent likelihood inverting the locked decay law (D-42) | ✅ |
| 2 | 04-06 | Provider layer — `Provider` protocol + registry, zero-token `TemplateProvider`, Haiku 4.5 provider routed through the gatekeeper; no key ⇒ degrades to `NO_KEY` | ✅ |
| 3 | 04-07 | Hint decoder — constrained JSON plus our own re-validation, EN **and** HE fixtures, a prompt-injection case, every failure path ⇒ `NO_EVIDENCE`, never raises | ✅ |
| 3 | 04-08 | Deception planner — a `DeceptionPlan` whose constructor refuses a lying capture/barrier claim, thief danger-adaptive lying with a measured truth floor, cop herding scored with the Phase-3 evaluation | ✅ |
| 4 | 04-09 | Belief fusion — `scent_check.contradicts()` (Sec4.4 lie detector, reproduces 0.9→0.81 exactly), `reliability.Reliability` (bounded adaptive coefficient, D-51), `belief_hint.hint_likelihood()` (D-40 mix, weighted below scent, never zeroes a cell) | ✅ |
| 4 | 04-10 | Bluff generator — `compose()`, the three-layer word limit (D-45): one call, one retry on overflow, truncate, `assert_no_coordinates`, total fallback to a seeded `HintBank` on every failure path; `bluff_prompt.py`'s style guide (D-39) never reveals `intent` to the model (D-36) | ✅ |
| 5 | 04-11 | `BeliefAdapter` — Figure-7 per-turn order (observe→predict→update(scent)→update(hint)→sample), Option A believed-state substitution (D-43 samples, never argmax), `registry.build_brain()` wired behind a `belief.enabled` config flag with a seeded RNG | ✅ |
| 6 | 04-12 | Turn-pipeline integration — Figure 7 wired live into `take_my_turn`/`await_opponent_turn`, `agent_lifecycle.default_context` now builds a REAL brain+ScentField+LanguageRuntime (first plan to wire Phase 3/4 into the live network loop), `PLACEHOLDER_HINT_TEXT` gone, four degradation games, a real two-peer concurrency bug found and fixed (late/duplicate hint no longer ends the game) | ✅ |
| 7 | 04-13 | Docs — `RULES-RESOLUTION-LANG.md` (D-48/D-49/D-51 written up for the grader, book pages verified directly against the PDF), three per-mechanism PRDs, the phase triplet, graph refresh | ✅ |
| 8 | 04-14 | GATE-4 measurement — `scripts/measure_gate4.py` (seeded, reproducible, `--mocked`/`--live`), `docs/phases/phase-4/GATE-4-MEASUREMENT.md` (all three §10.4 criteria measured mocked, all PASS; live PENDING), `tests/integration/test_gate4.py` (structural absolutes frozen as a CI test) | ✅ |

Gates on the merged tree after wave 8 (04-14) — measured, not inherited from agent self-reports:

| Check | Result |
|---|---|
| `uv run pytest --cov` | **1051 passed, 95.21%** (floor 85%) |
| `uv run ruff check .` | 0 violations |
| `scripts/check_line_limit.sh` (repo-wide + explicit scripts/test) | clean |
| `scripts/check_no_llm_in_strategy.py` | clean |
| `scripts/measure_gate4.py --mocked` reproducibility | two runs, only wall-clock timing differs; every criterion number byte-identical |
| `scripts/measure_gate4.py --live` with no key | attempts zero network calls, writes a clean `PENDING` JSON |
| GATE-4 criterion 1 (hint → inference) | 22/136 turns evidence, mean posterior L1 shift **1.171** on those turns |
| GATE-4 criterion 2 (scent decay, locked) | max deviation **1.11×10⁻¹⁶** from the closed form over 12 turns; handshake digests match (`c0e6322…`, both peers) |
| GATE-4 criterion 3 (hint every turn) | 68/68 turns, max 11 words (limit 15), both intents, **0** coordinate leaks, intent-before-text = 1.0 (structural) |
| Decode-fixture accuracy (mocked, EN/HE) | 1.0 / 1.0 (7/7, 4/4) |

No remaining waves. Phase 4's own build order is done.

## The one open item: live GATE-4 confirmation

**This is the ONLY thing left before `/gsd:verify-work 4` may run.** `ANTHROPIC_API_KEY` was not
set on any machine this phase ran on. Per rule 38 and 04-14-PLAN.md's own must_haves: a phase
whose gate criteria were only measured mocked is **not fully measured**, and the phase must not be
declared complete while that is true.

**Exact command a human runs, with a real key:**

```
ANTHROPIC_API_KEY=sk-ant-... uv run python scripts/measure_gate4.py --live
```

**What that produces** (`scripts/gate4_runner.run_live`, written and code-complete, never executed
against a real key this session): the D-33 liveness proof (`response.model` names Haiku 4.5,
non-zero provider calls, non-zero token usage — if this fails, the script marks the run `VOID` and
says so explicitly rather than reporting template numbers as live ones), real token spend in
tokens (from `response.usage`) and USD, real per-turn latency against the 60s watchdog threshold,
and real decode accuracy on the EN/HE fixtures against the actual model (ignoring the fixtures'
own canned `response` field, per that file's documented contract).

**After that run:** update `docs/phases/phase-4/GATE-4-MEASUREMENT.md`'s
[Live status](../../../docs/phases/phase-4/GATE-4-MEASUREMENT.md#live-status) section with the
real numbers (replace the PENDING block), then `/gsd:verify-work 4` may run.

## The next command

```
/gsd:verify-work 4
```

**only after the live run above lands.** Until then, nothing should tick — this phase's own gate
requires the live confirmation the plan set out to get, and mocked-PASS is not a substitute for it.

## Carry-overs from execution — read before any future work on this phase touches the language layer

**All wave 3–7 carry-overs (marked A–Y in prior revisions of this file) were fully discharged by
04-12/04-13** — see `04-12-SUMMARY.md` and `04-13-SUMMARY.md` for the complete accounting. Nothing
from those waves is open. New from wave 8 (04-14), for anyone building on the language channel
next (Phase 5 tunnelling, Phase 6 commit-reveal):

- **Z. `scripts/measure_gate4.py` and its helper modules (`scripts/gate4_*.py`) are the
  reproducible measurement path — reuse them rather than hand-rolling a third seeded-game runner.**
  `scripts/gate4_games.run_one_game(seed=, belief_enabled=, mocked=)` is the one function that
  builds a seeded two-peer game with belief toggled and either the recorded-response provider or
  the real one; `GATE4_SEEDS` is the fixed, documented seed tuple.
- **AA. The network event log has NO per-turn scent-field snapshot.** 04-12 logs
  `belief_entropy`/`belief_argmax`/`reliability` in `language_turn_record`, never the scent grids
  themselves. If a later plan wants scent values in the replay viewer (rule 20, Phase 7's GUI),
  that is a NEW field to add to `turn_events.language_turn_record` — `scripts/gate4_scent.py`
  worked around the gap by driving `ScentField`/`scent.py` directly with the locked config, which
  is sufficient for a decay-law CHECK but not for a per-turn REPLAY of what a specific game's field
  actually looked like turn-by-turn.
- **BB. `network/turn_language.py::choose_destination`'s `belief.enabled = false` fallback path
  hands the raw brain the TRUE, un-blinded current opponent cell (`ctx.state.thief`/`ctx.state.cop`
  directly), not a blind mover.** This pre-dates D-48/D-43 and was never updated when the belief
  layer's one-turn-behind `known_cell` convention landed. It makes "belief off" in this codebase
  mean "omniscient, zero-lag", not "blind, no Bayesian help" — discovered by 04-14's belief-on/off
  measurement (1.0 vs 0.0 cop win rate, the opposite direction naive intuition would predict,
  because the THIEF also becomes omniscient under the same toggle). **If a later plan wants a fair
  "belief vs blind" comparison, this fallback needs its own `known_cell`-fed raw-brain path — out
  of 04-14's own scope to add**, since this plan is measurement-only and must not touch strategy
  code to make a number come out cleaner.
- **CC. Anthropic's published Haiku 4.5 rate is a script-level constant
  (`scripts/gate4_report.HAIKU_INPUT_USD_PER_MTOK` / `HAIKU_OUTPUT_USD_PER_MTOK`, currently $1/$5
  per million tokens), cited from the public pricing page rather than `docs/PARAMETERS.md`
  (that file governs only the book's own game numerics).** Reconfirm this against Anthropic's
  current published rate before Phase 7 sends the league's actual-spend email
  (`docs/PARAMETERS.md` Table 18 row 4) — a vendor may revise a published rate at any time, and
  this script has no way to detect that on its own.

## Working-environment notes (unchanged from earlier waves, still true)

- **Do not rewrite plan files with Python's `write_text` on Windows** — it converts `\n` to
  `\r\n`, and the GSD frontmatter parser then reports every required field as missing. Use the
  editing tools, or write bytes explicitly.
- **Never `git merge` a worktree branch from inside a worktree.** Run every main-branch git
  command from the repository root.
- Direct-path script execution (`uv run python scripts/whatever.py`) puts the script's OWN
  directory on `sys.path[0]`, not the repo root — `scripts/measure_gate4.py` uses the same guarded
  `sys.path.insert(0, ...)` bootstrap `training/plot_curves.py` established in Phase 3
  (`__package__ in (None, "")`), so importing `pursuit.*`/`tests.*` from a `scripts/` entry point
  works without a `scripts/__init__.py`.
