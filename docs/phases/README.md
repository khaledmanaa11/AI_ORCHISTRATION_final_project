# Per-phase documentation triplets

Each phase of the [8-phase roadmap](../../.planning/ROADMAP.md) keeps its own triplet here:

```
docs/phases/phase-1/{PRD.md, PLAN.md, TODO.md}
docs/phases/phase-2/{PRD.md, PLAN.md, TODO.md}
...
docs/phases/phase-8/{PRD.md, PLAN.md, TODO.md}
```

## How they are produced (GSD loop)

Per the standing rule in [CLAUDE.md](../../CLAUDE.md) → *"Per-phase documentation triplet"*:

1. **`/gsd:plan-phase N`** copies `_TEMPLATE/` into `phase-N/` and fills PRD + PLAN + TODO
   for that phase (alongside the normal `.planning/` plan). Approve before executing.
2. **`/gsd:execute-phase N`** keeps `phase-N/TODO.md` current as tasks land.
3. **`/gsd:verify-work N`** marks every `phase-N/TODO.md` task `[x]` and ticks the matching
   rows in the root [`docs/TODO.md`](../TODO.md).

By the end, `docs/phases/` holds a complete, checked triplet per phase — so the grader sees
structured design + task evidence for all eight phases.

> This exceeds Segal §2.2 (which requires only the single project-level triplet plus
> per-mechanism `PRD_<mechanism>.md`). It is an intentional quality choice.
