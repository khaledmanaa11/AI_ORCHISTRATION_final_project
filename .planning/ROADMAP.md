# Roadmap: P2P Cops-and-Robbers — Cop & Thief Agents

## Overview

The journey runs from a bare 7×7 board to a league-ready, cryptographically-audited,
self-reporting pair of P2P agents, then to submission. It follows the book's **eight
construction phases** — phases 1–7 are the mandatory build stages (§10.3) whose success
criteria are the book's own milestone gates (§10.4); phase 8 is submission and league
operations. This phase breakdown is **fixed by the specification and the project rules —
it is not merged, split, reordered, renamed, or re-derived.** Each phase carries the
Segal-standard tasks: write its per-mechanism PRD(s), and update `docs/TODO.md` on
completion.

## Phases

**Phase Numbering:**

- Integer phases (1–8): mandated milestone work
- Decimal phases (2.1, 2.2): urgent insertions (marked with INSERTED)

- [x] **Phase 1: Base Logic** - Grid, movement rules, barrier quota, capture detection. No networking, no AI.
- [ ] **Phase 2: FastMCP Infrastructure** - Two separate processes exposing geometric tools over localhost, coordinates only.
- [ ] **Phase 3: Blind Strategy Module (RL policy)** - The Q-Learning decision engine, with no scent and no natural language yet.
- [ ] **Phase 4: Language and Scent** - Free-text hints, pheromone emission and decay, LLM for hint decoding and deception.
- [ ] **Phase 5: Cloud Exposure and Tunneling** - Expose the local FastMCP server publicly via ngrok or Localtonet.
- [ ] **Phase 6: Security and Cryptography** - Commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware declaration.
- [ ] **Phase 7: Reporting and Visualization Shell** - Gmail API reporting via OAuth 2.0, live GUI, replay viewer application.
- [ ] **Phase 8: Submission and League Operations** - Two public repos, academic README, Git tag, league games.

## Phase Details

### Phase 1: Base Logic

**Goal**: Grid, movement rules, barrier quota, capture detection. No networking, no AI.
**Depends on**: Nothing (first phase)
**Requirements**: BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06, BASE-07, BASE-08
**Success Criteria** (book milestone gate, §10.4):

  1. Both agents move legally on the grid (orthogonal step or stay; diagonals rejected)
  2. A barrier placed beyond the cop's quota is rejected
  3. Coordinate overlap (cop on thief) triggers capture; so do a barrier on the thief's cell and no-legal-move

**Plans**: TBD

Plans:
**Wave 1**

- [x] 01-01: Board model + orthogonal movement/validation, all values from config
- [x] 01-02: Barrier placement with quota enforcement
- [x] 01-97: Create/refresh `docs/phases/phase-1/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [x] 01-99: On verify-work, mark all Phase 1 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-03: Capture and end-condition detection + scoring table

### Phase 2: FastMCP Infrastructure

**Goal**: Two separate processes exposing geometric tools over localhost, coordinates only.
**Depends on**: Phase 1
**Requirements**: NET-01, NET-02, NET-03, NET-04, NET-05, NET-06, NET-07, NET-08, NET-09
**Success Criteria** (book milestone gate, §10.4):

  1. A geometric message sent by agent A over localhost is received and decoded correctly by agent B
  2. Cop and thief run as two separate processes under `config/police/` and `config/thief/` with no shared runtime state
  3. The orchestrator (single entry point) drives turn order via a state machine; illegal transitions are reported; watchdog + deadline tracker prevent hangs

**Plans**: TBD

Plans:

- [ ] 02-01: FastMCP server+client scaffold + geometric tool definitions (symmetric peer)
- [ ] 02-02: Orchestrator, state machine, illegal-transition reporting
- [ ] 02-03: Watchdog, deadline tracker, byte-for-byte config verification
- [ ] 02-04: Write `docs/PRD_mcp_transport.md` (the FastMCP peer layer)
- [ ] 02-97: Create/refresh `docs/phases/phase-2/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 02-99: On verify-work, mark all Phase 2 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 3: Blind Strategy Module (RL policy)

**Goal**: The Q-Learning decision engine, with no scent and no natural language yet.
**Depends on**: Phase 2
**Requirements**: STRAT-01, STRAT-02, STRAT-03, STRAT-04, STRAT-05, STRAT-06, STRAT-07
**Success Criteria** (book milestone gate, §10.4):

  1. Given a known target location, the agent computes and walks the shortest path with no manual intervention
  2. Move selection comes from a tabular Q-learning policy, with a Bayes+Manhattan fallback for unvisited states
  3. The strategy module is pluggable via config `[strategy]`, separate from networking; the algorithm — never the LLM — chooses the move

**Plans**: TBD

Plans:

- [ ] 03-01: BrainBase interface + Bayes+Manhattan fallback policy
- [ ] 03-02: State encoding + tabular Q-learning policy and ε-greedy action selection
- [ ] 03-03: Offline self-play training harness + learning-curve instrumentation
- [ ] 03-04: Write `docs/PRD_rl_strategy.md` (the Q-Learning policy)
- [ ] 03-96: Build the graphify graph — run `/gsd:graphify` at plan-phase (first build; `src/` now exists) and refresh after execute
- [ ] 03-97: Create/refresh `docs/phases/phase-3/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 03-99: On verify-work, mark all Phase 3 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 4: Language and Scent

**Goal**: Free-text hints, pheromone emission and decay, LLM for hint decoding and deception.
**Depends on**: Phase 3
**Requirements**: LANG-01, LANG-02, LANG-03, LANG-04, LANG-05, LANG-06, LANG-07
**Success Criteria** (book milestone gate, §10.4):

  1. A hint is translated into an inference (belief map updates via Bayes from scent + hints)
  2. The scent map updates (0.9 at source, 0.10 decay/turn, 5×5 window) and decays each turn; the decay model is locked pre-game
  3. The LLM emits a ≤15-word hint each turn, either true or false, with the `intent` flag committed in advance; comms stay natural-language-only

**Plans**: TBD

Plans:

- [ ] 04-01: Scent emission/decay model + cryptographic pre-game lock
- [ ] 04-02: Bayesian belief map fusing scent + hint evidence
- [ ] 04-03: LLM hint decode (inference) + LLM bluff generation with intent flag
- [ ] 04-04: Write `docs/PRD_scent_map.md`, `docs/PRD_belief_map.md`, `docs/PRD_deception.md`
- [ ] 04-96: Refresh the graphify graph (`/gsd:graphify`) at plan-phase and after execute
- [ ] 04-97: Create/refresh `docs/phases/phase-4/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 04-99: On verify-work, mark all Phase 4 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 5: Cloud Exposure and Tunneling

**Goal**: Expose the local FastMCP server publicly via ngrok or Localtonet.
**Depends on**: Phase 4
**Requirements**: CLOUD-01, CLOUD-02
**Success Criteria** (book milestone gate, §10.4):

  1. Each peer is reachable on the public internet through ngrok/Localtonet
  2. An agent on a remote machine connects through the tunnel and plays a full round against the local agent

**Plans**: TBD

Plans:

- [ ] 05-01: Tunnel integration + public URL wiring into the peer config
- [ ] 05-02: Remote end-to-end round validation
- [ ] 05-96: Refresh the graphify graph (`/gsd:graphify`) at plan-phase and after execute
- [ ] 05-97: Create/refresh `docs/phases/phase-5/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 05-99: On verify-work, mark all Phase 5 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 6: Security and Cryptography

**Goal**: Commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware declaration.
**Depends on**: Phase 5
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08
**Success Criteria** (book milestone gate, §10.4):

  1. A move is committed (SHA-256 hash) and then revealed with a valid nonce; the four phases run Commit → Acknowledge → Reveal → Final Reveal/Audit
  2. The hash covers canonical-JSON `{state, move, intent, nonce}`; the nonce (`secrets.token_hex(16)`) stays secret until game end; any mismatch is a technical loss
  3. The Step-0 hardware declaration (incl. exact commit hash) is verified before the first move

**Plans**: TBD

Plans:

- [ ] 06-01: Canonical-JSON hashing + nonce generation/verification
- [ ] 06-02: Four-phase commit-reveal protocol wired into the orchestrator
- [ ] 06-03: Step-0 hardware declaration + end-game mutual log audit
- [ ] 06-04: Write `docs/PRD_commit_reveal.md` (the cryptographic protocol)
- [ ] 06-96: Refresh the graphify graph (`/gsd:graphify`) at plan-phase and after execute
- [ ] 06-97: Create/refresh `docs/phases/phase-6/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 06-99: On verify-work, mark all Phase 6 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 7: Reporting and Visualization Shell

**Goal**: Gmail API reporting via OAuth 2.0, live GUI, replay viewer application.
**Depends on**: Phase 6
**Requirements**: REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05, REPORT-06, REPORT-07, REPORT-08, REPORT-09
**Success Criteria** (book milestone gate, §10.4):

  1. A game summary is sent by mail (send-only OAuth, through the gatekeeper; attached JSON, never free text)
  2. The live GUI displays state — only local truth, never the full objective board
  3. The replay app reconstructs a recorded round and shows `Verified OK`

**Plans**: TBD

Plans:

- [ ] 07-01: Gmail API send-only integration + gatekeeper (quota, token bucket, DOS)
- [ ] 07-02: Four JSON artifacts (`declaration_`/`config_`/`log_`/`result_`) + automatic end-of-game reporting + token accounting
- [ ] 07-03: Local-truth live GUI + verifying replay viewer
- [ ] 07-04: Write `docs/PRD_gatekeeper.md` (rate limiting and reporting)
- [ ] 07-96: Refresh the graphify graph (`/gsd:graphify`) at plan-phase and after execute
- [ ] 07-97: Create/refresh `docs/phases/phase-7/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 07-99: On verify-work, mark all Phase 7 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 8: Submission and League Operations

**Goal**: Split into two public GitHub repos, academic README, Git tag, play league games.
**Depends on**: Phase 7
**Requirements**: SUB-01, SUB-02, SUB-03, SUB-04, SUB-05, SUB-06, SUB-07, SUB-08, SUB-09, SUB-10, SUB-11, SUB-12
**Success Criteria** (submission gate):

  1. Two cross-linked public repos (cop, thief), each carrying README/config/PRD/PLAN/TODO, with a Git tag on the submitted version
  2. Academic README with its six mandatory sections (incl. learning curves and `Verified OK` screenshots); submission form filled and saved as PDF, submitted per team member
  3. At least 2 scored league games played against different teams and reported, each game emailing the commit hash it ran on

**Plans**: TBD

Plans:

- [ ] 08-01: Split into two cross-linked public repos (README/config/PRD/PLAN/TODO in each)
- [ ] 08-02: Academic README (six sections + learning curves + Verified-OK screenshots) + Git tag + 8-char team code
- [ ] 08-03: Play ≥2 scored league games vs different teams; auto-report results + per-game commit hash
- [ ] 08-04: Submission form (PDF, unaltered), per-member submission, code-quality self-assessment
- [ ] 08-96: Refresh the graphify graph (`/gsd:graphify`); commit `.planning/graphs/` for the submission showcase
- [ ] 08-97: Create/refresh `docs/phases/phase-8/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 08-99: On verify-work, mark all Phase 8 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

## Cross-cutting (every phase)

These apply to all phases and are verified continuously, not in a single phase:

- **QUAL-01…QUAL-13** — the §19.1 Table 5 code-quality gate (uv, ≤150 lines, ruff 0, coverage ≥85%, no hardcoded values, no secrets, SDK layer, gatekeeper, TDD, versioning, no duplication).
- **DOC-01/DOC-02** — `docs/PRD.md`/`PLAN.md`/`TODO.md` kept current; per-mechanism PRDs written in the phase that builds each mechanism.
- **Per-phase triplet (enforced — see CLAUDE.md)** — every phase creates `docs/phases/phase-<N>/{PRD,PLAN,TODO}.md` at `plan-phase` (from `docs/phases/_TEMPLATE/`), keeps the phase TODO current during `execute-phase`, and has **all** its TODOs marked `[x]` at `verify-work`. A phase is not verified until its triplet is complete and checked.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Base Logic | 5/5 | Complete | 2026-07-28 |
| 2. FastMCP Infrastructure | 0/5 | Not started | - |
| 3. Blind Strategy Module (RL policy) | 0/5 | Not started | - |
| 4. Language and Scent | 0/5 | Not started | - |
| 5. Cloud Exposure and Tunneling | 0/3 | Not started | - |
| 6. Security and Cryptography | 0/5 | Not started | - |
| 7. Reporting and Visualization Shell | 0/5 | Not started | - |
| 8. Submission and League Operations | 0/5 | Not started | - |
