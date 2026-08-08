# Phase 4 — resume point

**Written:** 2026-08-08 · **Status:** planning COMPLETE, execution NOT started.

## Where things stand

`/gsd:plan-phase 4` finished. The phase directory holds `04-PLAN-OUTLINE.md` and fourteen
`04-NN-PLAN.md` files. Nothing under `src/` has been touched by Phase 4 yet — the repo is still
exactly as Phase 3 left it.

Verified before commit, all mechanically rather than by eye:

| Check | Result |
|---|---|
| `gsd-tools frontmatter validate --schema plan` (×14) | 14/14 valid, 0 errors, 0 warnings |
| `gsd-tools verify plan-structure` (×14) | 14/14 valid, 0 errors, 0 warnings |
| Decisions D-32 … D-53 present in some plan's `must_haves` | 22/22 covered |
| No plan shares a wave with a plan it depends on | clean |
| No two plans in one wave modify the same file | clean |

Waves: `w1: 01 03 04` · `w2: 02 05 06` · `w3: 07 08` · `w4: 09 10` · `w5: 11` · `w6: 12` ·
`w7: 13` · `w8: 14`.

## The next command

```
/gsd:execute-phase 4
```

Run it on a fresh context. Everything an executor needs is in the plan files; nothing
important lives only in the planning conversation.

## What a reader should know before executing

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
3. **Plan 04-01 Task 4 closes a live hole in the rule-25 guard.** `scripts/check_no_llm_in_strategy.py`
   forbids `strategy/` from importing `anthropic`/`pursuit.network` but **not** `pursuit.services`,
   which this phase creates. Do that task early — several later plans cite the guard as their
   structural proof of rule 25.
4. **Four config blocks, one owner each** — `scent.json` (04-01), `language.json` (04-03),
   `belief.json` (04-05), `deception.json` (04-08). Their key enums live beside their loaders in
   `shared/`, **not** in `config_keys.py`, which is at 90 of its 150 permitted lines.

## Working-environment notes

- **Do not rewrite plan files with Python's `write_text` on Windows** — it converts `\n` to
  `\r\n`, and the GSD frontmatter parser then reports every required field as missing. Use the
  editing tools, or write bytes explicitly. This bit once and cost a re-validation pass.
- The knowledge graph was refreshed at the start of planning (3265 nodes / 5027 edges). Task
  04-96 refreshes it again after code lands.
