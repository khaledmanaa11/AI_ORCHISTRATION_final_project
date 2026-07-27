# PRD — P2P Cops-and-Robbers (Cop & Thief Agents)

**Version:** 1.00 · **Status:** Approved for build · **Last updated:** 2026-07-27

> Product Requirements Document per [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §2.2. The
> binding specification lives in [RULES.md](RULES.md) (55 rules) and [PARAMETERS.md](PARAMETERS.md)
> (every number). This PRD organizes *what* we deliver; it never overrides those documents.
> Companion planning docs: [PLAN.md](PLAN.md) (architecture), [TODO.md](TODO.md) (tasks).

## 1. Context & Problem

Final project for *Orchestration of AI Agents* (University of Haifa). We build **two
autonomous agents — a cop and a thief** — that play a distributed cops-and-robbers match on
a **7×7** grid over a peer-to-peer network using **MCP (Model Context Protocol)** via the
**FastMCP** Python library. There is **no central server and no referee**. Each agent is
simultaneously an MCP server and an MCP client. Neither agent can see the true board; each
builds a **belief map** from a decaying **scent trail** and from the opponent's **free-text
hints**, which are allowed to be lies. **Move decisions come from a reinforcement-learning
Q-policy**; the language model is used **only** to decode incoming hints and write outgoing
bluff text — it never chooses a move (rule 25).

The problem the architecture solves: in a refereeless P2P game, nothing structurally
prevents a player from editing a move after seeing the opponent's, showing itself the true
board, or falsely reporting results. The design answers each with **Zero-Trust**
mechanisms — separate processes, commit-reveal cryptography, local-truth-only display, and
mutual signed reporting.

## 2. Target Audience & "Market"

- **Primary evaluator:** the course lecturer/grader (Dr. Segal), who runs the submitted
  code, inspects `docs/`, verifies the replay shows `Verified OK`, and reads the automated
  game reports mailed to `rmisegal+uoh26finalgame@gmail.com`.
- **Opponents:** other teams' agents in the league. Our cop plays their thief; our thief
  plays their cop.
- **"Market" landscape (§6.3.1):** three equal-citizen strategy tracks — pure heuristics
  (Bayes + Manhattan, the reference default), a bespoke heuristic, or **RL**. The reference
  implementation (`https://github.com/rmisegal/Game-P2P-Cop-Chase`) is the baseline to beat.
  We deliberately choose RL to field a *thinking* opponent that a fixed heuristic cannot
  match (rationale: [PROJECT_GUIDE.md §B](PROJECT_GUIDE.md)).

## 3. Goals, KPIs & Acceptance Criteria

**Goals**
1. Field a legal, self-reporting, cryptographically-verifiable cop and thief.
2. Win league games with a trained RL policy that beats the Bayes + Manhattan baseline.
3. Meet the Segal engineering standard as a graded quality rubric.

**KPIs**
- RL policy win-rate vs. Bayes + Manhattan baseline in offline self-play: **> 50%**.
- Games completed without any disqualification trigger: **100%**.
- Both-side game reports delivered: **100%** (a single miss zeroes both teams — rule 35).
- Code-quality gate (Table 5): all machine-checkable rows pass.

**Acceptance criteria**
- **Quality gate** (machine-checkable): `ruff check` → 0; `pytest --cov` ≥ 85% (`fail_under=85`);
  every source/test file ≤ 150 lines; `uv`-only; 0 secrets in source; 0 hardcoded values.
- **Game correctness:** all eight phase milestone gates (§10.4) pass end-to-end.
- **Integrity:** replay viewer reconstructs a recorded round and shows `Verified OK`; any
  hash mismatch is treated as a technical loss (rule 19).
- **Submission:** two cross-linked public repos, academic README with learning curves,
  Git tag, ≥ 2 scored league games reported.

## 4. Functional Requirements

Full, traceable list with REQ-IDs and rule mappings: [.planning/REQUIREMENTS.md](../.planning/REQUIREMENTS.md).
Summary by capability area:

- **Base logic (BASE):** 7×7 grid, orthogonal movement, barrier quota, three capture
  conditions, survival win, scoring table — all values from config.
- **P2P/FastMCP (NET):** two separate processes, symmetric server+client, orchestrator +
  state machine, watchdog, deadline tracker, byte-identical config.
- **Strategy (STRAT):** tabular Q-learning policy + Bayes+Manhattan fallback, pluggable
  `BrainBase`, offline self-play training, learning curves; algorithm (not LLM) picks moves.
- **Language & scent (LANG):** ≤15-word natural-language hints (lies allowed, `intent`
  flag), pheromone emit/decay (0.9 / 0.10 / 5×5), Bayesian belief map, LLM decode + bluff.
- **Cloud (CLOUD):** public exposure via ngrok/Localtonet; remote round.
- **Security (SEC):** SHA-256 commit-reveal (4 phases), secret nonce, Step-0 declaration,
  end-game mutual audit.
- **Reporting (REPORT):** Gmail send-only + gatekeeper, four JSON artifacts, token
  accounting, local-truth GUI, verifying replay viewer.
- **Submission (SUB):** two repos, README/config/PRD/PLAN/TODO, Git tag, team code, league
  games, per-game commit-hash email, submission form.

## 5. Non-Functional Requirements

- **Reliability:** watchdog + deadline tracker guarantee no hang when the opponent never
  replies; gatekeeper overflow queues, never crashes.
- **Security:** Zero-Trust — no shared runtime state between cop and thief; secrets only via
  `os.environ.get()`; send-only mail scope; nonce via `secrets` module.
- **Maintainability:** SDK-layer architecture, files ≤150 lines, OOP/no-duplication, docstrings.
- **Performance efficiency:** tabular Q-table (not a neural net) keeps inference light;
  token budget ~200,000 per series (Table 18) tracked and reported.
- **Portability/compatibility:** `uv`-managed Python; localhost in dev, tunneled in league.
- **Quality model:** ISO/IEC 25010 (§13) as the umbrella rubric.

## 6. User Stories & Use-Cases

- *As the cop*, I move toward my belief-peak, place barriers to shrink the thief's space,
  and declare a capture truthfully the instant it happens.
- *As the thief*, I evade toward low-belief cells, exploit my own scent to mislead, and
  survive to the move ceiling.
- *As either agent*, each turn I: decode the incoming hint → update belief (Bayes) →
  choose a move (Q-policy) → write a bluff hint (LLM) → commit (hash) → reveal.
- *As the grader*, I clone both repos, run `uv sync`, launch a game, watch the local-truth
  GUI, receive the mailed JSON report, and replay the log to `Verified OK`.

## 7. Assumptions, Dependencies, Out-of-Scope

**Assumptions**
- The state space (7×7, two positions, barrier layout) stays small enough for a tabular
  Q-table; if not, barriers are abstracted into features (open question, Phase 3).
- Opponents honor the agreed, byte-identical config and the commit-reveal protocol.

**Dependencies**
- Python 3.10+, **`uv`**, **FastMCP**, an LLM (model id from config; default to the latest
  Claude model, accessed only through the gatekeeper), **ngrok/Localtonet**, **Gmail API**
  (OAuth 2.0, send-only), the reference implementation (self-play baseline), opponent teams.

**Out-of-scope** (see [.planning/REQUIREMENTS.md](../.planning/REQUIREMENTS.md))
- Deep/neural RL; LLM move selection; shared runtime state; true-board GUI; numeric
  coordinates in the protocol; A2A/ACP protocols.

## 8. Timeline & Milestones

Solo project — ordered milestones, not calendar dates. Each phase's deliverable is its
book milestone gate (§10.4); details in [.planning/ROADMAP.md](../.planning/ROADMAP.md) and
[TODO.md](TODO.md).

| Milestone | Phase | Deliverable (gate) |
|-----------|-------|--------------------|
| M1 | 1 Base Logic | Legal movement; over-quota barrier rejected; capture on overlap |
| M2 | 2 FastMCP | Geometric message A→B over localhost decoded correctly |
| M3 | 3 RL Strategy | Agent walks shortest path to a known target unaided |
| M4 | 4 Language & Scent | Hint→inference; scent decays; LLM emits a hint each turn |
| M5 | 5 Tunneling | Remote agent plays a full round via tunnel |
| M6 | 6 Security | Move committed then revealed with valid nonce; Step-0 verified |
| M7 | 7 Reporting | Mailed summary; local-truth GUI; replay shows `Verified OK` |
| M8 | 8 Submission | Two cross-linked repos; ≥2 scored league games reported |

---
*Approve this PRD before building the code it describes (§2.5 step 5).*
