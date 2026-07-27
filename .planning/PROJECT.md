# P2P Cops-and-Robbers — Cop & Thief Agents

## What This Is

Two autonomous AI agents — a **cop** and a **thief** — that play a distributed
cops-and-robbers match on a 7×7 grid over a peer-to-peer network with **no central server
and no referee**. Built as the final project for *Orchestration of AI Agents* (University
of Haifa). Each agent is a symmetric FastMCP peer (server + client) that decides moves with
a trained tabular **Q-learning** policy (Bayes + Manhattan fallback), communicates through
deceptive natural-language hints and a decaying scent trail, and proves honesty via
**SHA-256 commit-reveal** — then competes in a league against other teams' agents.

## Core Value

The two agents play a **complete, rule-compliant, cryptographically-verifiable game that
both sides report correctly**. A technically clean game beats a board win that gets
disqualified — a missing/contradictory report, a hash mismatch, shared state, or a true-board
GUI zeroes the game no matter how well the strategy played.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. Detailed REQ-IDs in REQUIREMENTS.md. -->

- [ ] Base game logic — 7×7 grid, orthogonal movement, barrier quota (14), capture detection
- [ ] FastMCP P2P infrastructure — two separate processes, symmetric server+client, orchestrator/state machine, watchdog, deadline tracker
- [ ] RL strategy module — tabular Q-learning with Bayes+Manhattan fallback and a belief map, playing blind
- [ ] Language & scent — natural-language hints (≤15 words), deception with `intent` flag, pheromone emit/decay
- [ ] Cloud tunneling — ngrok/Localtonet public exposure of each peer
- [ ] Security & crypto — commit-reveal SHA-256, secret nonce, Step-0 hardware declaration, end-game audit
- [ ] Reporting shell — Gmail API (send-only), gatekeeper (quota→token-bucket→DOS), JSON artifacts, replay viewer, local-truth GUI
- [ ] Submission — two cross-linked public repos, Git tag, academic README with learning curves, 8-char team code

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Neural-network / deep RL — a tabular Q-table is tractable at 7×7 (§B); avoid unnecessary complexity
- LLM choosing moves — **forbidden** (rule 25); the LLM only decodes incoming hints and writes outgoing bluff text
- Shared runtime state between cop and thief — **immediate disqualification** (rule 2); a shared *library* is fine, a shared *live state object* is not
- Displaying the true/objective board in the live GUI — **disqualification** (rule 9); only local truth
- Numeric coordinates in the protocol — **forbidden** (rule 27); free natural language only
- A2A / ACP protocols — MCP via FastMCP is the requirement; the others are optional complements, not built

## Context

- **Two binding documents**, both Hebrew, already translated and extracted:
  `police_thief_p2p.pdf` (game rules/protocol/league) → [docs/RULES.md](../docs/RULES.md),
  [docs/PARAMETERS.md](../docs/PARAMETERS.md); `software_submission_guidelines-V3.pdf`
  (engineering standard) → [docs/SEGAL_GUIDELINES.md](../docs/SEGAL_GUIDELINES.md).
- **55 mandatory rules**; **every number** comes from [docs/PARAMETERS.md](../docs/PARAMETERS.md).
  `fixed` values disqualify on any deviation; `minimum` values may move upward only.
- **Reference implementation** for self-play training baseline:
  `https://github.com/rmisegal/Game-P2P-Cop-Chase`.
- **Reporting target** (fixed recipient in both agents): `rmisegal+uoh26finalgame@gmail.com`.
- **Solo developer** — no teammates; the engineering quality gates are the review.
- Decision pipeline: `hint decode → belief update (Bayes) → Q-policy move choice → LLM bluff text → Commit pack`.

## Constraints

- **Tech stack**: Python, **`uv` only** (never pip/python directly), FastMCP, tabular Q-learning, Gmail API (send-only OAuth 2.0), ngrok/Localtonet — because the book and Segal guidelines mandate them.
- **Engineering (machine-checked gate)**: files ≤150 lines, `ruff check` 0 violations, `pytest --cov` ≥85%, 0 hardcoded values (config/constants/Enum), 0 committed secrets (`.env-example` only), TDD.
- **Architecture**: cop and thief as **separate processes and repos** under `config/police/` vs `config/thief/`, **no shared runtime state**, all business logic behind the SDK layer, thin GUI/CLI shells.
- **Protocol**: MCP via FastMCP; each peer is simultaneously server and client (symmetric); natural-language comms only; hints ≤15 words.
- **Numeric**: all values from [docs/PARAMETERS.md](../docs/PARAMETERS.md) — `fixed` non-negotiable, `minimum` upward only; never read a number from book prose.
- **Process**: 8-phase build order (§10.3 stages 1–7, each proven end-to-end before the next, + Phase 8 submission/league); never lie in a capture/barrier declaration or misreport games played.
- **Documentation**: `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` exist as full documents (Segal §2.2), plus a `docs/PRD_<mechanism>.md` per algorithm/mechanism (§2.3); the `.planning/` files do not satisfy this — the grader looks in `docs/`.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Reinforcement learning (tabular Q-learning) over pure heuristics | Game is a Dec-POMDP; a learned policy beats predictable heuristics; reward maps directly from the scoring table (§B) | — Pending |
| Keep a Bayes + Manhattan heuristic fallback | Bounds damage when the Q-table hits an unvisited state in a non-stationary (co-learning) environment | — Pending |
| FastMCP for the P2P protocol | MCP is the book's requirement; A2A/ACP are optional complements | — Pending |
| Fixed 8-phase build order (book §10.3 stages 1–7 + submission phase 8) | §10.3/§10.4 — a fault in a lower layer must not hide behind the one above it; phases are not merged/split/reordered | — Pending |
| Real `docs/PRD.md`/`PLAN.md`/`TODO.md` + per-mechanism PRDs, not `.planning/` pointers | Segal §2.2–2.3 — the grader looks in `docs/`; pointer files do not satisfy the requirement | — Pending |
| GSD config: Balanced models, Interactive mode, branching = none, docs committed | Chosen during initialization this session | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-27 after initialization*
