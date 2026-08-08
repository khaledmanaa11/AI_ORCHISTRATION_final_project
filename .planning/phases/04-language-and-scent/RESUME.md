# Phase 4 — resume point

**Updated:** 2026-08-08 · **Status:** waves 1–2 EXECUTED (6/14 plans). Waves 3–8 not started.

Execution was stopped deliberately after wave 2 so it can continue on a local machine. Nothing
is half-finished: every dispatched plan completed, merged, and passed the gates.

## Where things stand

All work is on branch **`claude/gsd-parallelism-config-6b4aqp`**, pushed, at commit `b334409`
(35 commits into the phase). Get it with:

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

Gates on the merged tree after wave 2 — measured, not inherited from agent self-reports:

| Check | Result |
|---|---|
| `uv run pytest --cov` | **637 passed, 93.62%** (floor 85%) |
| `uv run ruff check .` | 0 violations |
| `scripts/check_line_limit.sh` | clean repo-wide |
| `scripts/check_no_llm_in_strategy.py` | clean — `strategy/` imports no `pursuit.services` |

Remaining waves: `w3: 07 08` · `w4: 09 10` · `w5: 11` · `w6: 12` · `w7: 13` · `w8: 14`.

## The next command

On the local machine, with its own (colon-form) GSD install:

```
/gsd:execute-phase 4 --wave 3
```

`--wave 3` runs only wave 3 (04-07 hint decoding, 04-08 deception planner). Drop the flag to run
waves 3–8 straight through. Run it on a fresh context.

**`parallelization` is now `true`** in `.planning/config.json` (it was `false`, which was a
scaffold default, not a decision). Plans within a wave now execute concurrently. GSD's own
default for this key is `true`, and `execute-phase` still drops a wave back to sequential by
itself if it detects two plans in it touching the same file.

## Carry-overs from execution — read before wave 3

1. **04-02 left `local_scent_digest` defaulting to `None`.** `agent_wiring.py`/`agent_lifecycle.py`
   (plan 04-12, wave 6) call the handshake helpers without a digest, so requiring it would have
   broken out-of-scope callers. The wire requirement is still enforced once both sides opt in, but
   a caller that *forgets* to pass a digest fails open locally rather than loudly. **04-12 should
   pass a real digest and consider making it required at that point.**
2. **04-06 estimates tokens locally instead of calling `count_tokens()`.** The plan's `must_haves`
   ("the provider never calls the API directly", no carve-out) is stricter than its own task text;
   the executor obeyed the stricter one. If a later plan wants exact counts, that tension must be
   resolved in the plan first, not in the code.
3. **The knowledge graph is STALE** — built at `da345dd8`, 35+ commits behind. `graphify` is not
   installed in the cloud container, so this must be refreshed locally (CLAUDE.md requires it for
   phases ≥ 3 after code lands):
   ```
   graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/
   ```
4. **Phase-4 code currently shares a branch with a GSD toolchain change** (enabling parallelization
   and adding `scripts/ensure_gsd.sh`). If you want the phase reviewed on its own, split it before
   opening a phase PR.

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
   `belief.json` (04-05 ✅), `deception.json` (04-08, still to come). Their key enums live beside
   their loaders in `shared/`, **not** in `config_keys.py`.

## Working-environment notes

- **Do not rewrite plan files with Python's `write_text` on Windows** — it converts `\n` to
  `\r\n`, and the GSD frontmatter parser then reports every required field as missing. Use the
  editing tools, or write bytes explicitly.
- **Never `git merge` a worktree branch from inside a worktree.** It silently targets that
  worktree, reports "Already up to date", and leaves the real branch untouched. Run every
  main-branch git command from the repository root. This cost a near-miss during wave 1.
- **Do not trust a fresh worktree's base commit.** One wave-2 worktree was created off a commit
  predating wave 1; only the base assertion in the executor contract caught it and reset it.
