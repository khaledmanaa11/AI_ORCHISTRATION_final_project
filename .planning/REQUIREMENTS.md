# Requirements: P2P Cops-and-Robbers — Cop & Thief Agents

**Defined:** 2026-07-27
**Core Value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.

> Every numeric value is fixed in [docs/PARAMETERS.md](../docs/PARAMETERS.md). Rule numbers
> reference the 55 mandatory rules in [docs/RULES.md](../docs/RULES.md); the **Rule Coverage**
> matrix below proves each of the 55 is traceable to a requirement. Quality requirements
> (`QUAL-*`) come from [docs/SEGAL_GUIDELINES.md](../docs/SEGAL_GUIDELINES.md) §19.1 Table 5.
> Single-milestone final project — all requirements are v1.

## v1 Requirements

### Base Logic (BASE) — Phase 1

- [x] **BASE-01**: Agents move only orthogonally (one step or stay); diagonal moves are rejected (rules 13–14)
- [ ] **BASE-02**: The cop may place at most the barrier quota; a barrier beyond quota is rejected (rule 15 placement; barrier quota, minimum)
- [ ] **BASE-03**: Capture is detected when the cop lands on the thief's cell (rule 46)
- [ ] **BASE-04**: Capture is detected when a barrier is placed on the thief's cell at the moment of contact (rule 46)
- [ ] **BASE-05**: Capture is detected when the thief is left with no legal move (rule 47)
- [ ] **BASE-06**: The thief wins by surviving the survival-threshold turns (minimum)
- [ ] **BASE-07**: Every end scenario scores per the scoring table — capture 20/5, survival 5/10, tie 2, technical loss 0/0 (rule 48)
- [x] **BASE-08**: All numeric parameters load from config; zero hardcoded game values (PARAMETERS.md)

### P2P / FastMCP Infrastructure (NET) — Phase 2

- [ ] **NET-01**: Cop and thief run as two separate processes under `config/police/` vs `config/thief/` (rule 1)
- [ ] **NET-02**: No shared runtime state, memory, or variables between the two agents (rule 2)
- [ ] **NET-03**: Each agent is simultaneously a FastMCP server (exposes tools) and client (calls the opponent's tools) (§C)
- [ ] **NET-04**: The orchestrator is the single entry point, driving turn order through a proper state machine (rules 3–4)
- [ ] **NET-05**: Every attempt to transition to an illegal state is reported (rule 5)
- [ ] **NET-06**: A deadline tracker prevents freezing while waiting on the opponent (rule 6)
- [ ] **NET-07**: A watchdog monitors process crashes and rescues data (rule 7)
- [ ] **NET-08**: A geometric message sent over localhost is received and decoded correctly by the other agent (Stage 2 gate)
- [ ] **NET-09**: The configuration file is verified byte-for-byte identical on both sides (rule 11)

### Strategy Module — RL (STRAT) — Phase 3

- [ ] **STRAT-01**: Move selection uses a trained tabular Q-learning policy via `BrainBase._pick_move` (§B)
- [ ] **STRAT-02**: A Bayes + Manhattan heuristic fallback handles states the Q-table has never visited (§B)
- [ ] **STRAT-03**: The strategy module is pluggable — declared in config `[strategy]` as `police_class`/`thief_class`, separate from networking (§C)
- [ ] **STRAT-04**: Given a known target location, the agent computes and walks the shortest path with no manual intervention (Stage 3 gate)
- [ ] **STRAT-05**: The cop selects barrier placement via `_decide_move` (STRATEGY.md)
- [ ] **STRAT-06**: Training is offline (self-play + reference implementation); a trained Q-table ships; learning curves are instrumented from the first run (rule 42)
- [ ] **STRAT-07**: The algorithm chooses the move — the language model never does (rule 25)

### Language & Scent (LANG) — Phase 4

- [ ] **LANG-01**: Each turn an agent sends a free-text verbal hint of at most the hint word limit (Table 14)
- [ ] **LANG-02**: Communication is natural language only — no direct numeric coordinates in the protocol (rules 26–27)
- [ ] **LANG-03**: Hints may be lies; the `intent` flag (`truth | lie`) is committed in advance (§5.3)
- [ ] **LANG-04**: Each agent emits scent — strength 0.9 at source, decaying 0.10 per turn, over a 5×5 window (all fixed)
- [ ] **LANG-05**: A belief map (probability grid over opponent position) updates via Bayes rule from scent + hints (§A)
- [ ] **LANG-06**: The LLM decodes incoming hints into an inference and generates the outgoing bluff text (§6.2)
- [ ] **LANG-07**: The scent-emission decay model is cryptographically locked before the game starts (rule 23)

### Cloud Tunneling (CLOUD) — Phase 5

- [ ] **CLOUD-01**: Each peer is exposed to the public internet via a tunneling tool (ngrok/Localtonet) (rule 10)
- [ ] **CLOUD-02**: A remote agent connects via tunnel and plays a full round against the local agent (Stage 5 gate)

### Security & Cryptography (SEC) — Phase 6

- [ ] **SEC-01**: Moves use a commit-reveal protocol based on SHA-256 (rule 17)
- [ ] **SEC-02**: Four phases — Commit (hash) → Acknowledge → Reveal (move + hint, nonce hidden) → Final Reveal / Audit (§E)
- [ ] **SEC-03**: The hash covers `{state, move, intent, nonce}` serialized as canonical JSON (`sort_keys=True, separators=(",",":")`) (§E)
- [ ] **SEC-04**: The nonce is generated with `secrets.token_hex(16)`, kept secret until game end, verified with `secrets.compare_digest` (rule 18)
- [ ] **SEC-05**: Any hash mismatch at audit is a technical loss — score 0 to the forging team (rule 19)
- [ ] **SEC-06**: A signed Step-0 hardware declaration (OS/CPU/RAM/GPU/model/commit hash) is published before the first move (rules 24, 53)
- [ ] **SEC-07**: Barrier and capture declarations are open and truthful; false barrier/capture declarations are forbidden (rules 15–16, 21–22)
- [ ] **SEC-08**: A comprehensive mutual log audit runs at the end of every game (rule 36)

### Reporting & Visualization Shell (REPORT) — Phase 7

- [ ] **REPORT-01**: At game end both agents automatically email a signed JSON report to `rmisegal+uoh26finalgame@gmail.com` (rules 32, 35, 51)
- [ ] **REPORT-02**: Outgoing mail passes the gatekeeper chain: Quota Manager → Token Bucket → DOS Detector → Gmail API (rules 28–29)
- [ ] **REPORT-03**: The token bucket implements `tokens ← min(C, tokens + r·Δt)`, allowing a send iff `tokens ≥ 1` (Table 19)
- [ ] **REPORT-04**: HTTP 429 is handled with backoff; the mail interface uses a send-only OAuth scope (rules 28, 30)
- [ ] **REPORT-05**: Reports are attached JSON files, never free text (rules 33–34)
- [ ] **REPORT-06**: Four JSON artifacts are produced — `declaration_`, `config_`, `log_`, `result_` (PARAMETERS.md)
- [ ] **REPORT-07**: The final JSON reports total tokens consumed per game and across the series (rule 54)
- [ ] **REPORT-08**: The live GUI displays only local truth — never the full objective board (rules 8–9)
- [ ] **REPORT-09**: A replay viewer reconstructs a recorded game log and verifies it, showing `Verified OK` (rule 20)

### Submission & League (SUB) — Phase 8

- [ ] **SUB-01**: Two separate public GitHub repos (cop, thief), each README cross-linking the other (rule 49)
- [ ] **SUB-02**: Every repo includes README, `config/`, PRD files, a PLAN file, and TODO files (rule 50)
- [ ] **SUB-03**: Academic README with its six mandatory sections, including learning curves (RL) and `Verified OK` screenshots (rule 42)
- [ ] **SUB-04**: Secrets in `.gitignore`, never pushed; `.env-example` committed with dummy values (rules 39–40)
- [ ] **SUB-05**: The submitted version carries an appropriate Git tag (rule 41)
- [ ] **SUB-06**: A unique 8-character team identification code (no spaces) is defined (rule 45)
- [ ] **SUB-07**: At least the minimum league games are played against different teams — one scoring game per opponent, no rematches for points; the game count is declared accurately and never falsely (rules 31, 37, 38, 52)
- [ ] **SUB-08**: Each game emails the lecturer the GitHub commit hash the code ran on (rule 53)
- [ ] **SUB-09**: The submission form is downloaded, filled, and saved as PDF, unaltered/unforged (rule 43)
- [ ] **SUB-10**: The assignment is submitted separately for each team member (rule 44)
- [ ] **SUB-11**: A self-assessment score is given for code quality only — not league results (rule 55)
- [ ] **SUB-12**: Parameter values respect fixed/minimum/negotiable status — minimum raised only by mutual agreement, never lowered; each game's config is attached to the repo with a per-game name (rule 12, PARAMETERS §2)

### Code-Quality Gate (QUAL) — cross-cutting, every phase

From [docs/SEGAL_GUIDELINES.md](../docs/SEGAL_GUIDELINES.md) §19.1 Table 5.

- [x] **QUAL-01**: All business logic sits behind an SDK layer; GUI/CLI are thin shells (Table 5)
- [ ] **QUAL-02**: OOP with no duplication — extract at 2+ copies into a shared module/base class/mixin (Table 5)
- [ ] **QUAL-03**: Every external API call passes through a single API gatekeeper (Table 5)
- [ ] **QUAL-04**: Rate limits live in configuration, never in source (Table 5)
- [ ] **QUAL-05**: On overflow the gatekeeper queues (FIFO), never crashes (Table 5)
- [x] **QUAL-06**: Version tracking starts at 1.00 in `version.py` and in the config JSON files (Table 5)
- [ ] **QUAL-07**: TDD — red → green → refactor; tests cover happy path and error case; external services mocked (Table 5)
- [ ] **QUAL-08**: Every source and test file is ≤150 lines (excluding blanks/comments) — split, never compress (Table 5)
- [ ] **QUAL-09**: `ruff check` reports zero violations (Table 5)
- [ ] **QUAL-10**: `pytest --cov` ≥ 85% with `fail_under = 85` (Table 5)
- [ ] **QUAL-11**: Zero hardcoded values in source — config, `constants.py`, or `Enum` only (Table 5)
- [ ] **QUAL-12**: Zero secrets in source; `os.environ.get()` only; `.env-example` committed (Table 5)
- [ ] **QUAL-13**: `uv` is the sole package manager; `pyproject.toml` + `uv.lock`, no `requirements.txt` (Table 5)

### Documentation (DOC) — cross-cutting, init + per building phase

From [docs/SEGAL_GUIDELINES.md](../docs/SEGAL_GUIDELINES.md) §2.2–2.5.

- [ ] **DOC-01**: `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` exist as full documents; `docs/TODO.md` is kept current as work progresses (§2.2, §2.5 step 6)
- [ ] **DOC-02**: Every algorithm/central mechanism has its own `docs/PRD_<mechanism>.md`, written in the phase that builds it (§2.3)

## v2 Requirements

(None — single-milestone final project; all committed scope is v1.)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Neural-network / deep RL | Tabular Q-table is tractable at 7×7 (§B); avoids unnecessary complexity |
| LLM choosing the move | Forbidden (rule 25); LLM only decodes hints and writes bluff text |
| Shared runtime state between cop and thief | Immediate disqualification (rule 2); shared *library* OK, shared *live state* not |
| True/objective board in the live GUI | Disqualification (rule 9); only local truth |
| Numeric coordinates in the protocol | Forbidden (rule 27); natural language only |
| A2A / ACP protocols | MCP via FastMCP is the requirement; others optional, not built |

## Rule Coverage (all 55 rules → requirements)

Proves every mandatory rule in [docs/RULES.md](../docs/RULES.md) is traceable.

| Rule | Requirement(s) | Rule | Requirement(s) |
|------|----------------|------|----------------|
| 1 | NET-01 | 29 | REPORT-02 |
| 2 | NET-02 | 30 | REPORT-04 |
| 3 | NET-04 | 31 | SUB-07 |
| 4 | NET-04 | 32 | REPORT-01 |
| 5 | NET-05 | 33 | REPORT-05 |
| 6 | NET-06 | 34 | REPORT-05 |
| 7 | NET-07 | 35 | REPORT-01 |
| 8 | REPORT-08 | 36 | SEC-08 |
| 9 | REPORT-08 | 37 | SUB-07 |
| 10 | CLOUD-01 | 38 | SUB-07 |
| 11 | NET-09 | 39 | SUB-04, QUAL-12 |
| 12 | SUB-12 | 40 | SUB-04, QUAL-12 |
| 13 | BASE-01 | 41 | SUB-05 |
| 14 | BASE-01 | 42 | SUB-03, STRAT-06 |
| 15 | BASE-02, SEC-07 | 43 | SUB-09 |
| 16 | SEC-07 | 44 | SUB-10 |
| 17 | SEC-01 | 45 | SUB-06 |
| 18 | SEC-04 | 46 | BASE-03, BASE-04 |
| 19 | SEC-05 | 47 | BASE-05 |
| 20 | REPORT-09 | 48 | BASE-07 |
| 21 | SEC-07 | 49 | SUB-01 |
| 22 | SEC-07 | 50 | SUB-02 |
| 23 | LANG-07 | 51 | REPORT-01 |
| 24 | SEC-06 | 52 | SUB-07 |
| 25 | STRAT-07 | 53 | SEC-06, SUB-08 |
| 26 | LANG-02 | 54 | REPORT-07 |
| 27 | LANG-02 | 55 | SUB-11 |
| 28 | REPORT-02, REPORT-04 | | |

## Traceability (requirement → phase)

| Requirements | Phase | Status |
|--------------|-------|--------|
| BASE-01 … BASE-08 | Phase 1 — Base Logic | Pending |
| NET-01 … NET-09 | Phase 2 — FastMCP Infrastructure | Pending |
| STRAT-01 … STRAT-07 | Phase 3 — Blind Strategy (RL) | Pending |
| LANG-01 … LANG-07 | Phase 4 — Language & Scent | Pending |
| CLOUD-01 … CLOUD-02 | Phase 5 — Cloud Exposure & Tunneling | Pending |
| SEC-01 … SEC-08 | Phase 6 — Security & Cryptography | Pending |
| REPORT-01 … REPORT-09 | Phase 7 — Reporting Shell | Pending |
| SUB-01 … SUB-12 | Phase 8 — Submission & League | Pending |
| QUAL-01 … QUAL-13 | Cross-cutting (every phase) | Pending |
| DOC-01 … DOC-02 | Init + per building phase | Pending |

**Coverage:**
- v1 requirements: 74 total (8 BASE + 9 NET + 7 STRAT + 7 LANG + 2 CLOUD + 8 SEC + 9 REPORT + 12 SUB + 13 QUAL + 2 DOC)
- Mapped to phases / cross-cutting: 74
- Unmapped: 0 ✓
- Mandatory rules (55) all traceable: ✓

---
*Requirements defined: 2026-07-27*
*Last updated: 2026-07-27 after correction to 8-phase structure + full rule/quality seeding*
