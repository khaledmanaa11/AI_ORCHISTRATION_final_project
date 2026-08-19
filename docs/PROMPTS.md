# Prompt-engineering log

One entry per prompt pattern that materially drove the work — what was asked, what came
back, what we'd do differently. Companion to `docs/devlog/`.

## Entry 001 — parallel research fan-out with evidence-gated adoption (2026-08-19)

### Context

The thief was stuck: five independent optimization runs all landed at 43–52% survival vs
the sealing chaser, and we could not tell whether that was a game-theoretic ceiling or a
representation failure. Rather than tuning harder, we ran a research workflow.

### Prompt (paraphrased)

Three parallel researchers, each with the full game spec, the measured results table, and
one angle: (1) evasion/pursuit theory on grid graphs — "is ~50% a ceiling on 7×7 with 14
walls and rule 46?"; (2) simultaneous-move adversarial search — "why did depth-2 make play
WORSE, and what are the known remedies?"; (3) noisy-fitness optimization — "why do our ES
curves drift, and what protocol fixes it at 15 dims and 13 games/sec?" Each had to return
findings with a concrete `how_to_apply` codeable against our architecture.

### Output / Decision

The theory researcher settled the ceiling question (cop number of a grid is 2 → losses are
attributable to rule 46 + walls, not fate) and produced the two ideas that defined run 3:
promote kill-range from learned feature to matrix terminal (+13 pp, shipped) and the
quota-0 endgame tablebase (later rejected — 0/1,294 losses addressable). The optimization
researcher's paired-seed/holdout protocol replaced the drifting ES and produced the v2
vector (57.4% → 70.4% sealing). Every candidate then faced a pre-registered n≥1,000 gate;
four were rejected on evidence (depth-2, noisy-ES, tablebase, KL2 trap leaf).

### Lessons Learned

- Give researchers the measured numbers and the failure question, not the codebase — the
  ceiling answer came from literature we would never have grepped for.
- A `how_to_apply` field forces implementable findings; without it research returns essays.
- Pre-register the adoption gate before running any experiment. The gate rejected four of
  six ideas — the two that shipped are trustworthy precisely because the same gate could
  have killed them.
- Structural facts beat features, features beat weights, weights beat optimizer tweaks:
  the day's biggest gain was moving one fact (rule 46 at distance 1) from a learned weight
  into the game's payoff matrix.
