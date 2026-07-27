# Phase <N> PLAN — <Phase Name>

**Version:** 1.00 · **Updated:** <date>

> Phase-scoped architecture. Inherits the project [PLAN.md](../../PLAN.md); capture only the
> design specific to this phase. Link to any per-mechanism PRD written this phase.

## Components & files
| Module / file (≤150 lines each) | Responsibility |
|---|---|
| `src/<pkg>/...` | <what it does> |

## Interfaces & contracts
<New/changed SDK methods, MCP tools, class signatures, data schemas introduced this phase.>

## Phase ADRs
| # | Decision | Rationale | Alternative / trade-off |
|---|----------|-----------|-------------------------|
| P<N>-1 | <choice> | <why> | <rejected option> |

## Test plan (TDD)
- Unit: <files + happy path AND error case; external services mocked>
- Integration: <feature-level checks; the §10.4 gate demo>
- Coverage target: ≥ 85% (`fail_under=85`).

## Per-mechanism PRDs written this phase
- <docs/PRD_<mechanism>.md, if any — else "none">
