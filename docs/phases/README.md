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

## Beyond the triplet: how a phase actually went

Some phases carry a fourth document — an engineering log recording the failures,
measurements, reversals and rejected alternatives that the PRD/PLAN/TODO deliberately do
not. A PRD states what the module does; it is a poor place to record that we picked a rule
from a plausible argument and had to reverse it after measuring.

| Phase | Log |
|---|---|
| 3 | [ENGINEERING-LOG.md](phase-3/ENGINEERING-LOG.md) — why run 1 failed for a reason its own post-mortem missed, the three live engine bugs found by *running* the engine, and the two optimisers of which one shipped |
| 3 | [RUN-1-POSTMORTEM.md](phase-3/RUN-1-POSTMORTEM.md) — forensic analysis of the abandoned 300,000-episode run |
| 3 | [RULES-RESOLUTION.md](phase-3/RULES-RESOLUTION.md) — every turn-resolution predicate pinned to a book quote or marked as a negotiated extension |
