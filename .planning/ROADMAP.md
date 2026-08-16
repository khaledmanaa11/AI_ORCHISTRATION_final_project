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
- [x] **Phase 3: Blind Strategy Module** - The decision engine. Delivered as a matrix-game mover over a learned 15-weight evaluation, NOT Q-learning; see docs/phases/phase-3/PRD.md §2.
- [ ] **Phase 4: Language and Scent** - Free-text hints, pheromone emission and decay, LLM for hint decoding and deception.
- [ ] **Phase 5: Cloud Exposure and Tunneling** - Expose the local FastMCP server publicly via ngrok or Localtonet.
- [x] **Phase 6: Security and Cryptography** - Commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware declaration. *(All three §10.4 criteria measured PASS; the 2 security gaps verify-work found beyond the gate were closed by 06-05 and the gate re-measured.)*
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

- [ ] 02-00: Phase-2 scaffold — `uv add fastmcp` + `pytest-asyncio`, per-agent `network.json`, test stubs
- [ ] 02-01: Network config loader + `loader_helpers.py` extraction (QUAL-02)
- [ ] 02-02: Message envelope + canonical-JSON config digest
- [ ] 02-03: Turn state machine + severity-based illegal-transition reporting
- [ ] 02-04: JSONL event log + watchdog daemon thread
- [ ] 02-05: Write `docs/PRD_mcp_transport.md` (the FastMCP peer layer)
- [ ] 02-06: FastMCP tool surface (4 async stubs) + peer runtime (server+client, one loop)
- [ ] 02-07: Deadline tracker + technical-win verdict
- [ ] 02-08: Handshake — connectivity + config-digest exchange, abort before move 1
- [ ] 02-09: Per-agent orchestrator + thin `main.py` + dev launcher (no referee)
- [ ] 02-10: §10.4 gate tests (GATE-1/2/3) + NET coverage audit
- [x] 02-97: Create/refresh `docs/phases/phase-2/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [ ] 02-99: On verify-work, mark all Phase 2 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 3: Blind Strategy Module (RL policy)

**Goal**: The decision engine, with no scent and no natural language yet.
**Delivered as**: a simultaneous-move matrix-game mover over a learned 15-weight evaluation.
Tabular Q-learning was withdrawn as unsound under simultaneous play (PRD §2, ENGINEERING-LOG.md).
**Depends on**: Phase 2
**Requirements**: STRAT-01, STRAT-02, STRAT-03, STRAT-04, STRAT-05, STRAT-06, STRAT-07
**Success Criteria** (book milestone gate, §10.4):

  1. Given a known target location, the agent computes and walks the shortest path with no manual intervention
  2. Move selection comes from the algorithm — a solved matrix game per turn, sampled from its equilibrium
  3. The strategy module is pluggable via config `[strategy]`, separate from networking; the algorithm — never the LLM — chooses the move

**Plans**: TBD

Plans:

- [x] 03-01: BrainBase interface + registry (value_search / chaser_cop / greedy_evader)
- [x] 03-02: Simultaneous joint resolver + matrix-game mover (supersedes tabular Q-learning)
- [x] 03-03: Offline self-play harness + learning curves (24,000 games; artifacts/run2/curve.json)
- [x] 03-04: Write `docs/PRD_matrix_mover.md` (supersedes PRD_rl_strategy.md)
- [x] 03-96: Build the graphify graph — run `/gsd:graphify` at plan-phase (first build; `src/` now exists) and refresh after execute
- [x] 03-97: Create/refresh `docs/phases/phase-3/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [x] 03-99: On verify-work, mark all Phase 3 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 4: Language and Scent

**Goal**: Free-text hints, pheromone emission and decay, LLM for hint decoding and deception.
**Depends on**: Phase 3
**Requirements**: LANG-01, LANG-02, LANG-03, LANG-04, LANG-05, LANG-06, LANG-07
**Success Criteria** (book milestone gate, §10.4):

  1. A hint is translated into an inference (belief map updates via Bayes from scent + hints)
  2. The scent map updates (0.9 at source, 0.10 decay/turn, 5×5 window) and decays each turn; the decay model is locked pre-game
  3. The LLM emits a ≤15-word hint each turn, either true or false, with the `intent` flag committed in advance; comms stay natural-language-only

**Plans**: 14 (waves 1-8; see `.planning/phases/04-language-and-scent/04-PLAN-OUTLINE.md`)

Plans (executed 04-01..04-13; 04-14 remains — GATE-4 measurement against the live API; nothing
below is ticked until `/gsd:verify-work 4` runs, after 04-14):

- [ ] 04-01: Locked scent model — Table 16 values, Figure-4 kernel, `ScentField`, digest helper
- [ ] 04-02: Handshake carries the scent digest (rule 23, `SCENT_MISMATCH`)
- [ ] 04-03: LLM gatekeeper — Table 19 token bucket, FIFO queue, D-35 budget ladder
- [ ] 04-04: Transport — `MessageType.HINT`, direction-token move/barrier codec (D-53)
- [ ] 04-05: Belief map core — grid, motion model, scent likelihood (D-42)
- [ ] 04-06: Provider layer — registry, `template`, `claude_api` (Haiku 4.5)
- [ ] 04-07: Hint decoder — constrained JSON, EN + HE, total (never raises)
- [ ] 04-08: Deception planner — intent + claim, cop herding / thief danger-adaptive lying
- [ ] 04-09: Belief fusion — hint likelihood, adaptive reliability, Sec4.4 lie detector (D-51)
- [ ] 04-10: Bluff generator — word limit, retry, truncate, template bank
- [ ] 04-11: `BeliefAdapter` — sample from belief (D-43), believed-state substitution (Option A)
- [ ] 04-12: Turn-pipeline integration — Figure 7 wired into the live two-process turn loop
- [ ] 04-13: Three per-mechanism PRDs, `RULES-RESOLUTION-LANG.md`, phase triplet
- [ ] 04-14: GATE-4 measurement against the live API (not yet run)
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

**Plans**: 15 (05-01..05-03 built the phase; 05-04..05-07 closed the five gaps the
2026-08-13 remote round exposed — see `05-UAT.md` Round 1; 05-09..05-11 closed the
peer-data crash paths and gave `ensure_connected()` its production caller; **05-12..05-15
close G6–G10 from the post-closure audit**). **GATE-5 MET 2026-08-16** — criterion 2 closed
by remote-round attempt 4. The 05-12..05-15 set does not reopen the gate: none of G6–G10 is
a §10.4 criterion, but three are league-day blockers (a malformed peer can end our game
before move 1) and are planned, verified, and pending execution.

Plans:

- [x] 05-01: Tunnel lifecycle -- pyngrok dep, tunnel.json + loader, TunnelManager (DI'd, reconnect bounded by Table 19), lifecycle wiring, URL/secret exchange printout
- [x] 05-02: Shared-secret channel -- ASGI middleware, client transport headers, env plumbing, `.env-example`
- [x] 05-03: Gate 5 -- smoke script, in-process integration proof, `GATE-5-MEASUREMENT.md`, Localtonet runbook, graph refresh
- [x] 05-04: G1 — verdict honesty + bounded teardown grace (a failed OWN final-reveal send stops accusing the peer; corrected `game_over`; `linger_for_peer` on Table 19 values, zero new numbers) — shipped; see G6 for the reachability residual
- [x] 05-05: G2 — one negotiated game id across log/ledger/declaration/committed `state.game_id`, and an audit that validates the peer's committed role/turn (game_id when negotiated) — shipped; see G7 for the peer-input residual
- [x] 05-06: G3+G4 — inbound HINTs on the wire log; relaxed receive window AND responder `pending.turn` stamp together; no hint composed for an already-resolved turn
- [x] 05-07: G5 — keyless LLM made legible (startup WARNING, honest declared `llm_name`, first-person compose prompt); fallback behaviour unchanged
- [x] 05-08: Remote round — HUMAN-RUN on two machines/networks; **closed GATE-5 criterion 2 at attempt 4 (2026-08-16)**: agreeing verdicts + matched audits on both machines, live LLM both sides
- [x] 05-09: Transport-failure containment — `httpx.TransportError` joins the NET-06 ladder incl. the wrapped connect-path shape; LocalProtocolError/UnsupportedProtocol still raise
- [x] 05-10: Peer-data boundary — malformed FINAL_REVEAL is a named mismatch not a crash; 5xx/429 retryable while 4xx raises; `board_outcome` wiring pinned — see G9 for the seventh instance still live at the handshake
- [x] 05-11: Tunnel watch — `ensure_connected()` gets its production caller; drop repaired on the existing Table-19 bound (never exercised live — no drop occurred in attempt 4)
- [ ] 05-12: G9+G7 — a malformed peer cannot kill us at the handshake: a non-str peer digest is a named non-agreement; `peer_game_id` is safety-validated (never convention-checked) before it reaches a set, a Path, or the audit's membership key
- [ ] 05-13: G6 — the audit survives long enough to be honest: it touches the watchdog per bounded attempt, and BOTH legs stop accusing a peer that answered
- [ ] 05-14: G8 — one inbound hint is decoded at most once; both branches stamp the turn actually played, including the commit-reveal-off path
- [ ] 05-15: G10 — the declaration story settled: rules 15/16 confirmed satisfied by the committed action, dead `declare_truthfully` removed, stale PRD line corrected, capture Claim de-risked via the existing `GAME_OVER` envelope
- [x] 05-96: Refresh the graphify graph (`/gsd:graphify`) at plan-phase and after execute
- [x] 05-97: Create/refresh `docs/phases/phase-5/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [x] 05-99: On verify-work, mark all Phase 5 TODOs `[x]` in the phase triplet + root `docs/TODO.md`

### Phase 6: Security and Cryptography

**Goal**: Commit-reveal protocol over SHA-256, nonce handling, Step-0 hardware declaration.
**Depends on**: Phase 5
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08
**Success Criteria** (book milestone gate, §10.4):

  1. A move is committed (SHA-256 hash) and then revealed with a valid nonce; the four phases run Commit → Acknowledge → Reveal → Final Reveal/Audit
  2. The hash covers canonical-JSON `{state, move, intent, nonce}`; the nonce (`secrets.token_hex(16)`) stays secret until game end; any mismatch is a technical loss
  3. The Step-0 hardware declaration (incl. exact commit hash) is verified before the first move

**Plans**: 4 (waves 1-4; see `.planning/phases/06-security-and-cryptography/06-PLAN-OUTLINE.md`)

Plans (all 5 executed and verified; `/gsd:verify-work 6` run 2026-08-09 — all three §10.4
criteria measured PASS, see `docs/phases/phase-6/GATE-6-MEASUREMENT.md`. UAT 11/11.
An adversarial audit during verify-work found 2 real gaps beyond the gate's own criteria —
the mutual audit's join key was the peer's own declared `envelope.turn`, making both the
D-67 forgery check and the rule-36 coverage check bypassable by turn-skew, and a caught
mismatch never reached a durable outcome record. Both reproduced with paired controls and
closed by plan 06-05; gate re-measured afterwards, still PASS):

- [x] 06-01: Crypto core — `pursuit.security` package (canonical commit/reveal hashing, state record, durable nonce ledger), `security_config.py`, the `security.json` pair
- [x] 06-02: Four-phase wire protocol — 4 message kinds, the both-locked Commit→Ack→Reveal exchange (D-58), barrier placement inside the committed action (D-66, SEC-07), toggle-off byte-equivalence
- [x] 06-03: Step-0 hardware declaration (verified at handshake, D-62/D-63) + negotiated `game_id` (D-61) + end-game mutual log audit with the revealed-vs-played cross-check (D-67)
- [x] 06-04: GATE-6 measurement (localhost, zero env vars) + `docs/PRD_commit_reveal.md` (the cryptographic protocol)
- [x] 06-96: Refresh the graphify graph at plan-phase and after execute — final refresh 6577 nodes / 11972 edges / 413 communities
- [x] 06-97: Create/refresh `docs/phases/phase-6/{PRD,PLAN,TODO}.md` (phase triplet) at plan-phase
- [x] 06-99: On verify-work, mark all Phase 6 TODOs `[x]` in the phase triplet + root `docs/TODO.md`
- [x] 06-05 / 06-98: **GAP CLOSURE** — the mutual audit is bound to locally-authoritative turn state instead of the peer's declared `envelope.turn`, and a caught mismatch is durable (corrected `game_over` + non-zero exit). See `06-05-SUMMARY.md`; proven by `tests/unit/test_audit_turn_binding.py` + tamper (e).
- [x] 06-06: **GAP CLOSURE** — a peer `ToolError` ends the game through the technical-loss path instead of killing us after the ledger append and before FINAL_REVEAL (rule 36); every game-message handler rejects a non-opponent `sender` (handshake exempt by design). See `06-06-SUMMARY.md`.

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
| 4. Language and Scent | 13/14 | In Progress | - |
| 5. Cloud Exposure and Tunneling | 4/8 | In Progress (GATE-5 criterion 1 PASS; criterion 2 PENDING -- gap-closure plans 05-04..05-08, then the human remote round attempt 2) | - |
| 6. Security and Cryptography | 4/4 | Executed -- GATE-6 all 3 criteria PASS, 06-VERIFICATION.md passed 11/11; verify-work pending | - |
| 7. Reporting and Visualization Shell | 0/5 | Not started | - |
| 8. Submission and League Operations | 0/5 | Not started | - |
