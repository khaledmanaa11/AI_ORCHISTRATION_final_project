# Requirements: P2P Cops-and-Robbers — Cop & Thief Agents

**Defined:** 2026-07-27
**Core Value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.

> Every numeric value is fixed in [docs/PARAMETERS.md](../docs/PARAMETERS.md). Rule numbers
> reference [docs/RULES.md](../docs/RULES.md). This is a single-milestone final project —
> all requirements are v1.

## v1 Requirements

### Base Logic (BASE)

- [ ] **BASE-01**: Agents move only orthogonally (one step or stay); diagonal moves are rejected (rules 13–14)
- [ ] **BASE-02**: The cop may place at most 14 barriers across a game; a barrier beyond quota is rejected (barrier quota, minimum)
- [ ] **BASE-03**: Capture is detected when the cop lands on the thief's cell (rule 46)
- [ ] **BASE-04**: Capture is detected when a barrier is placed on the thief's cell at the moment of contact (rule 46)
- [ ] **BASE-05**: Capture is detected when the thief is left with no legal move (rule 47)
- [ ] **BASE-06**: The thief wins by surviving the 35-turn survival threshold (minimum)
- [ ] **BASE-07**: Every end scenario scores per the scoring table — capture 20/5, survival 5/10, tie 2, technical loss 0/0 (rule 48)
- [ ] **BASE-08**: All numeric parameters load from a config file; zero hardcoded game values (Segal §19.1, PARAMETERS.md)

### P2P / FastMCP Infrastructure (NET)

- [ ] **NET-01**: Cop and thief run as two separate processes under `config/police/` vs `config/thief/` (rule 1)
- [ ] **NET-02**: No shared runtime state, memory, or variables between the two agents (rule 2)
- [ ] **NET-03**: Each agent is simultaneously a FastMCP server (exposes tools) and client (calls the opponent's tools) (§C)
- [ ] **NET-04**: The orchestrator is the single entry point, driving turn order through a proper state machine (rules 3–4)
- [ ] **NET-05**: Every attempt to transition to an illegal state is reported (rule 5)
- [ ] **NET-06**: A deadline tracker prevents freezing while waiting on the opponent (rule 6)
- [ ] **NET-07**: A watchdog monitors process crashes and rescues data (rule 7)
- [ ] **NET-08**: A geometric message sent over localhost is received and decoded correctly by the other agent (Stage 2 gate)
- [ ] **NET-09**: The configuration file is verified byte-for-byte identical on both sides (rule 11)

### Strategy Module — RL (STRAT)

- [ ] **STRAT-01**: Move selection uses a trained tabular Q-learning policy via `BrainBase._pick_move` (§B)
- [ ] **STRAT-02**: A Bayes + Manhattan heuristic fallback handles states the Q-table has never visited (§B)
- [ ] **STRAT-03**: The strategy module is pluggable — declared in config `[strategy]` as `police_class`/`thief_class`, separate from networking (§C)
- [ ] **STRAT-04**: Given a known target location, the agent computes and walks the shortest path with no manual intervention (Stage 3 gate)
- [ ] **STRAT-05**: The cop selects barrier placement via `_decide_move` (STRATEGY.md)
- [ ] **STRAT-06**: Training is offline (self-play + reference implementation); a trained Q-table ships; learning curves are instrumented from the first run (rule 42)
- [ ] **STRAT-07**: The algorithm chooses the move — the language model never does (rule 25)

### Language & Scent (LANG)

- [ ] **LANG-01**: Each turn an agent sends a free-text verbal hint of at most 15 words (hint word limit)
- [ ] **LANG-02**: Communication is natural language only — no direct numeric coordinates in the protocol (rules 26–27)
- [ ] **LANG-03**: Hints may be lies; the `intent` flag (`truth | lie`) is committed in advance (§5.3)
- [ ] **LANG-04**: Each agent emits scent — strength 0.9 at source, decaying 0.10 per turn, over a 5×5 window (all fixed)
- [ ] **LANG-05**: A belief map (probability grid over opponent position) updates via Bayes rule from scent + hints (§A)
- [ ] **LANG-06**: The LLM decodes incoming hints into an inference and generates the outgoing bluff text (§6.2)
- [ ] **LANG-07**: The scent-emission decay model is cryptographically locked before the game starts (rule 23)

### Cloud Tunneling (CLOUD)

- [ ] **CLOUD-01**: Each peer is exposed to the public internet via a tunneling tool (ngrok/Localtonet) (rule 10)
- [ ] **CLOUD-02**: A remote agent connects via tunnel and plays a full round against the local agent (Stage 5 gate)

### Security & Cryptography (SEC)

- [ ] **SEC-01**: Moves use a commit-reveal protocol based on SHA-256 (rule 17)
- [ ] **SEC-02**: Four phases — Commit (hash) → Acknowledge → Reveal (move + hint, nonce hidden) → Final Reveal / Audit (§E)
- [ ] **SEC-03**: The hash covers `{state, move, intent, nonce}` serialized as canonical JSON (`sort_keys=True, separators=(",",":")`) (§E)
- [ ] **SEC-04**: The nonce is generated with `secrets.token_hex(16)`, kept secret until game end, verified with `secrets.compare_digest` (rule 18)
- [ ] **SEC-05**: Any hash mismatch at audit is a technical loss — score 0 to the forging team (rule 19)
- [ ] **SEC-06**: A signed Step-0 hardware declaration (OS/CPU/RAM/GPU/model/commit hash) is published before the first move (rules 24, 53)
- [ ] **SEC-07**: Barrier and capture declarations are open and truthful; false barrier/capture/game-count declarations are forbidden (rules 15–16, 21–22, 38)
- [ ] **SEC-08**: A comprehensive mutual log audit runs at the end of every game (rule 36)

### Reporting & Visualization Shell (REPORT)

- [ ] **REPORT-01**: At game end both agents automatically email a signed JSON report to `rmisegal+uoh26finalgame@gmail.com` (rules 32, 35, 51)
- [ ] **REPORT-02**: Outgoing mail passes the gatekeeper chain: Quota Manager → Token Bucket → DOS Detector → Gmail API (rules 28–29)
- [ ] **REPORT-03**: The token bucket implements `tokens ← min(C, tokens + r·Δt)`, allowing a send iff `tokens ≥ 1` (Table 19)
- [ ] **REPORT-04**: HTTP 429 is handled with backoff; the mail interface uses a send-only OAuth scope (rules 28, 30)
- [ ] **REPORT-05**: Reports are attached JSON files, never free text (rules 33–34)
- [ ] **REPORT-06**: Four JSON artifacts are produced — `declaration_`, `config_`, `log_`, `result_` (PARAMETERS.md)
- [ ] **REPORT-07**: The final JSON reports total tokens consumed per game and across the series (rule 54)
- [ ] **REPORT-08**: The live GUI displays only local truth — never the full objective board (rules 8–9)
- [ ] **REPORT-09**: A replay viewer reconstructs a recorded game log and verifies it, showing `Verified OK` (rule 20)

### Submission & League (SUB)

- [ ] **SUB-01**: Two separate public GitHub repos (cop, thief), each README cross-linking the other (rule 49)
- [ ] **SUB-02**: Every repo includes README, `config/`, PRD files, a PLAN file, and TODO files (rule 50)
- [ ] **SUB-03**: Academic README with its six mandatory sections, including learning curves (RL) and `Verified OK` screenshots (rule 42)
- [ ] **SUB-04**: Secrets in `.gitignore`, never pushed; `.env-example` committed with dummy values (rules 39–40)
- [ ] **SUB-05**: The submitted version carries an appropriate Git tag (rule 41)
- [ ] **SUB-06**: A unique 8-character team identification code (no spaces) is defined (rule 45)
- [ ] **SUB-07**: At least the minimum league games (2) are played against different teams; the game count is declared accurately (rules 31, 37)
- [ ] **SUB-08**: Each game emails the lecturer the GitHub commit hash the code ran on (rule 53)

## v2 Requirements

(None — single-milestone final project; all committed scope is v1.)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Neural-network / deep RL | Tabular Q-table is tractable at 7×7 (§B); avoids unnecessary complexity |
| LLM choosing the move | Forbidden (rule 25); LLM only decodes hints and writes bluff text |
| Shared runtime state between cop and thief | Immediate disqualification (rule 2); shared *library* OK, shared *live state* not |
| True/objective board in the live GUI | Disqualification (rule 9); only local truth |
| Numeric coordinates in the protocol | Forbidden (rule 27); natural language only |
| A2A / ACP protocols | MCP via FastMCP is the requirement; others optional, not built |

## Traceability

Which phase covers each requirement. Phases are fixed by the book's 7-stage build order
(§10.3); the roadmapper confirms and locks this mapping.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BASE-01 … BASE-08 | Phase 1 — Base Logic | Pending |
| NET-01 … NET-09 | Phase 2 — FastMCP Infrastructure | Pending |
| STRAT-01 … STRAT-07 | Phase 3 — Blind Strategy (RL) | Pending |
| LANG-01 … LANG-07 | Phase 4 — Language & Scent | Pending |
| CLOUD-01 … CLOUD-02 | Phase 5 — Cloud Exposure & Tunneling | Pending |
| SEC-01 … SEC-08 | Phase 6 — Security & Cryptography | Pending |
| REPORT-01 … REPORT-09 | Phase 7 — Reporting Shell | Pending |
| SUB-01 … SUB-08 | Phase 7 — Reporting Shell / Submission | Pending |

**Coverage:**
- v1 requirements: 50 total
- Mapped to phases: 50
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-27*
*Last updated: 2026-07-27 after initial definition*
