# Phase 4 — resume point

**Updated:** 2026-08-09 · **Status:** waves 1–3 EXECUTED, wave 4 IN PROGRESS (9/14 plans:
04-01..04-09). 04-10 (bluff generator) remains to finish wave 4. Waves 5–8 not started.

Nothing is half-finished: every dispatched plan completed, merged, and passed the gates.

## Where things stand

All work is on branch **`claude/gsd-parallelism-config-6b4aqp`**, pushed. Get it with:

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

Gates on the merged tree after wave 4's first plan (04-09) — measured, not inherited from agent
self-reports:

| Check | Result |
|---|---|
| `uv run pytest --cov` | **903 passed, 94.55%** (floor 85%) |
| `uv run ruff check .` | 0 violations |
| `scripts/check_line_limit.sh` | clean repo-wide |
| `scripts/check_no_llm_in_strategy.py` | clean — `strategy/` imports no `pursuit.services` |
| End-to-end Sec4.4 reproduction | fully-lying opponent's reliability 0.5→0.2→0.05 within 2 turns; fully-truthful holds at 0.5 for 10 turns; fused-posterior argmax follows scent in both regimes (`tests/unit/strategy/test_belief_fusion_e2e.py`) |

Remaining waves: `w4: 10` · `w5: 11` · `w6: 12` · `w7: 13` · `w8: 14`.

## The next command

```
/gsd:execute-phase 4 --wave 4
```

This resumes wave 4 at its remaining plan, 04-10 (bluff generator) — 04-09 is done. Drop the
`--wave` flag to run waves 4–8 straight through. Run it on a fresh context.

**If you are resuming in a Claude-Code-on-the-web container, the slash command will not
resolve** — the GSD plugin is not installed there (`.claude/` holds only `settings.json`, there
is no `.claude/commands/gsd/`). Wave 3 was executed by reading `04-07-PLAN.md` and
`04-08-PLAN.md` and following them task by task, running every check in each plan's
`<verification>` block and quoting the results in its SUMMARY. That works; a local run with the
real GSD install is still the intended path.

**`parallelization` is now `true`** in `.planning/config.json` (it was `false`, which was a
scaffold default, not a decision). Plans within a wave now execute concurrently. GSD's own
default for this key is `true`, and `execute-phase` still drops a wave back to sequential by
itself if it detects two plans in it touching the same file.

## Carry-overs from execution — read before continuing wave 4 (04-10) and beyond

**New in wave 4 (04-09) — 04-10/04-11/04-12 need these:**

- **F. `Reliability` is per-opponent, per-game, and is never constructed by anything in this
  plan's own scope.** `04-12` (turn-pipeline integration) is the intended owner of building one
  `Reliability(config.reliability)` per opponent at handshake time and holding it for the game's
  duration — never persisted, never shared across games (rule 52). Each incoming hint: call
  `scent_check.contradicts(inference, opponent_field, model, config)` first, then
  `reliability.observe(score)` — in that order, once per turn a hint arrives.
- **G. `hint_likelihood.weight` (D-40's fixed mixing weight `w`) and `reliability.prior` (D-51's
  adaptive coefficient's starting point) are TWO INDEPENDENT `belief.json` fields**, not the same
  number reused twice. If a later plan's prose reads as if they should be unified, that is the
  same ambiguity 04-09 resolved by keeping them separate — resolve it in the plan text first, not
  by quietly merging the config fields.
- **H. `hint_likelihood(inference, reliability, board_size, config)` takes `config: BeliefParams`
  directly** (the full loaded object, not a sub-group) — same calling convention as
  `belief_scent.scent_likelihood(..., config: BeliefParams)`. Both read their own group off the
  same `BeliefParams` instance.
- **I. A heading-only `Inference` (no region, no cells) produces NO shift in `hint_likelihood`** —
  confirmed consistent with carry-over B (confidence 0 washes it out) and, independently, with
  `hint_likelihood`'s own fallback for the case where a positive-confidence heading-only shape
  reaches it anyway (a shape the real decoder never emits, but a defensive path exists and is
  tested).

**New in wave 3 (04-07 / 04-08) — a wave-4 executor needs all five:**

- **A. `DecodeContext.word_limit` has no default and no config key yet.** 04-07 owns no config
  file, so the Table 14 row 2 word limit is passed in by the caller. **04-10 should add
  `hint_word_limit` to `language.json`'s `model` group** (it owns the emission side of the same
  negotiated number) and **04-12 must pass it into `DecodeContext`.** Nothing is broken today —
  every call site supplies it explicitly — but the number currently lives only in test code.
- **B. A heading-only hint decodes at confidence 0, so it is NOT positional evidence.**
  04-07-PLAN.md Task 1 says reject when region and cells are both absent while confidence is
  above zero; taken literally that would discard `direction` for the one case where a heading is
  all that was stated. The rule ships exactly as written, and the prompt asks for
  `confidence: 0` on such a hint, so the heading survives on the `Inference` with
  `is_evidence == False`. **If 04-09 wants a bare heading to shift mass, change the plan first,
  not the code.**
- **C. `plan_deception` needs `params`, and takes two optional keywords the plan did not name.**
  Signature is `plan_deception(role, state, params, belief, rng, config, *, scent=None,
  weights=None)`. **04-12 should pass `scent=` (it is what makes the thief's lies survive the
  §4.4 contradiction test) and `weights=` (without it a trained cop herds on `PRIOR`, not on its
  own artefact).** Both omit-safely; the loss is silent quality, not an error.
- **D. The cop's herding lever is real but shallow, and that is measured.** One-step lookahead
  cannot see a trap two steps away. 04-08's `test_the_lie_drives_the_thief_somewhere_less_connected`
  uses a board found by randomised search rather than a hand-built cul-de-sac, because the
  hand-built one did not exercise the mechanism at all. Do not read the cop's 0.644 lie rate as
  proof the claims are strategically strong — read it as proof they are non-degenerate.
- **E. Three types moved down into `shared/` so `strategy/` could reach them without importing
  `pursuit.network`** (STRAT-03): `DirectionWord`/`Origin`/`DEFAULT_ORIGIN`/`axis_signs` →
  `shared/directions.py`, and `Intent` → `shared/deception_types.py`. Both network modules
  re-export, so existing call sites are unchanged, and two tests assert the *identity* of the
  re-exports so a future re-declaration fails loudly instead of drifting.

**Still open from waves 1–2:**

1. **04-02 left `local_scent_digest` defaulting to `None`.** `agent_wiring.py`/`agent_lifecycle.py`
   (plan 04-12, wave 6) call the handshake helpers without a digest, so requiring it would have
   broken out-of-scope callers. The wire requirement is still enforced once both sides opt in, but
   a caller that *forgets* to pass a digest fails open locally rather than loudly. **04-12 should
   pass a real digest and consider making it required at that point.**
2. **04-06 estimates tokens locally instead of calling `count_tokens()`.** The plan's `must_haves`
   ("the provider never calls the API directly", no carve-out) is stricter than its own task text;
   the executor obeyed the stricter one. If a later plan wants exact counts, that tension must be
   resolved in the plan first, not in the code.
3. **The knowledge graph is STILL STALE** — built at `da345dd8`, now ~40 commits behind.
   Re-confirmed during wave 3: `which graphify` finds nothing in the cloud container, so this
   must be refreshed locally (CLAUDE.md requires it for phases ≥ 3 after code lands). Wave 3
   added 11 source modules, so the gap is now material:
   ```
   graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/
   ```
4. **Phase-4 code currently shares a branch with a GSD toolchain change** (enabling parallelization
   and adding `scripts/ensure_gsd.sh`). If you want the phase reviewed on its own, split it before
   opening a phase PR.
5. **`docs/phases/phase-4/` does not exist**, though CLAUDE.md's per-phase triplet rule says
   `/gsd:plan-phase 4` should have created `{PRD,PLAN,TODO}.md` there and approved them *before*
   execution. The plan set instead assigns the triplet to **04-13 (wave 7)**, so the two rules
   disagree about when it lands. Wave 3 did not create it: writing a phase-wide PRD/PLAN/TODO
   from inside a single wave would either duplicate 04-13's deliverable or invent content for
   waves not yet executed. **Decide before wave 7** whether to backfill the triplet now (matching
   CLAUDE.md's ordering) or let 04-13 produce it (matching the plan set). Either way the phase is
   not verified until it exists with every task checked.

## What a reader should still know (unchanged from planning)

1. **Read `04-PLAN-OUTLINE.md` §1 first.** The book contradicts itself about what a peer reveals
   each turn (§5.3.2 says the Move is revealed every turn; §6.4 says neither side ever sees the
   opponent's real location). D-48 resolves it under the preface's academic-freedom clause. Plans
   04-04, 04-05, 04-11 and 04-12 only make sense downstream of that decision.
2. **Three source-of-truth deviations are deliberate and documented**, and 04-13 must write all
   three up or the phase is not submission-ready:
   - **D-48** — the reveal contradiction and our choice.
   - **D-49** — scent is derived locally and never transmitted.
   - **D-51** — a *disclosed revision* of `04-CONTEXT.md`'s "hint trust: fixed discount weight":
     the fixed weight survives, the trust coefficient becomes adaptive per §4.4.
3. ~~Plan 04-01 Task 4 closes a live hole in the rule-25 guard.~~ **Done in wave 1** —
   `scripts/check_no_llm_in_strategy.py` now rejects `pursuit.services` imports under `strategy/`,
   and the gate is green with `services/llm/` present.
4. **Four config blocks, one owner each** — `scent.json` (04-01 ✅), `language.json` (04-03 ✅),
   `belief.json` (04-05 ✅), `deception.json` (04-08 ✅). Their key enums live beside their
   loaders in `shared/`, **not** in `config_keys.py`. All four role-file pairs are byte-identical
   and asserted so by a test.

## Working-environment notes

- **Do not rewrite plan files with Python's `write_text` on Windows** — it converts `\n` to
  `\r\n`, and the GSD frontmatter parser then reports every required field as missing. Use the
  editing tools, or write bytes explicitly.
- **Never `git merge` a worktree branch from inside a worktree.** It silently targets that
  worktree, reports "Already up to date", and leaves the real branch untouched. Run every
  main-branch git command from the repository root. This cost a near-miss during wave 1.
- **Do not trust a fresh worktree's base commit.** One wave-2 worktree was created off a commit
  predating wave 1; only the base assertion in the executor contract caught it and reset it.
