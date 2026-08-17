# Requirements: P2P Cops-and-Robbers — Cop & Thief Agents

**Defined:** 2026-07-27 · **Reconciled:** 2026-08-17 (08-02, project-wide, one pass)
**Core Value:** The two agents play a complete, rule-compliant, cryptographically-verifiable game that both sides report correctly.

> Every numeric value is fixed in [docs/PARAMETERS.md](../docs/PARAMETERS.md). Rule numbers
> reference the 55 mandatory rules in [docs/RULES.md](../docs/RULES.md); the **Rule Coverage**
> matrix below proves each of the 55 is traceable to a requirement. Quality requirements
> (`QUAL-*`) come from [docs/SEGAL_GUIDELINES.md](../docs/SEGAL_GUIDELINES.md) §19.1 Table 5.
> Single-milestone final project — all requirements are v1.

## How to read a row — and how it is enforced

Every **`[x]`** carries `**evidence:** \`path\` "verbatim quote"` — and `**evidence:**` means *satisfied*, so an open row never carries it. Every **`[ ]`** carries
`**open:**` naming what is outstanding and where it lands. This is not a convention; it is
checked:

```bash
uv run python scripts/check_requirements_ledger.py    # 0 clean · 1 any violation · 2 judged nothing
```

The gate reads each cited artifact and looks for the quoted sentence. A row can be ticked, but
it cannot be ticked *and stay green* without pointing at text that really exists in a file that
really ships.

**Truth order, and it is not negotiable:** `NN-VERIFICATION.md` verdict → `GATE-N-MEASUREMENT.md`
measured criteria → SUMMARY counts. **A tracker's own banner is not evidence for that tracker.**
Where a verification artifact and a tracker disagreed, the disagreement is recorded rather than
resolved in the friendlier direction.

**Rule 38 cuts both ways.** Understating verified work is as wrong as overstating unverified
work. Phase 4 keeps two open rows, Phase 7 keeps all nine, and every one of the twelve `SUB-*`
rows is open — because that is what the artifacts say.

## v1 Requirements

### Base Logic (BASE) — Phase 1 · `01-VERIFICATION.md` **passed**, 3/3 must-haves

- [x] **BASE-01**: Agents move only orthogonally (one step or stay); diagonal moves are rejected (rules 13–14) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-01 | SATISFIED"
- [x] **BASE-02**: The cop may place at most the barrier quota; a barrier beyond quota is rejected (rule 15 placement; barrier quota, minimum) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-02 | SATISFIED"
- [x] **BASE-03**: Capture is detected when the cop lands on the thief's cell (rule 46) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-03 | SATISFIED"
- [x] **BASE-04**: Capture is detected when a barrier is placed on the thief's cell at the moment of contact (rule 46) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-04 | SATISFIED"
- [x] **BASE-05**: Capture is detected when the thief is left with no legal move (rule 47) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-05 | SATISFIED"
- [x] **BASE-06**: The thief wins by surviving the survival-threshold turns (minimum) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-06 | SATISFIED"
- [x] **BASE-07**: Every end scenario scores per the scoring table — capture 20/5, survival 5/10, tie 2, technical loss 0/0 (rule 48) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-07 | SATISFIED"
- [x] **BASE-08**: All numeric parameters load from config; zero hardcoded game values (PARAMETERS.md) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "BASE-08 | SATISFIED"

> **Extract defect carried, not silently corrected.** `docs/RULES.md:97` writes rule 48 as
> "capture 20/5, survival **10/5**" while `docs/PARAMETERS.md` Table 17 rows 3–4 give cop **5** /
> thief **10** — both **fixed**. Rule 48's own capture pair is cop-first, so BASE-07's `5/10`
> above is the correct ordering and the extract is the file that is wrong. Registered as row
> **G1-15** in [docs/SUBMISSION-CHECKLIST.md](../docs/SUBMISSION-CHECKLIST.md); correcting an
> extract against the book is a separate decision and **no fixed value was touched here**.

### P2P / FastMCP Infrastructure (NET) — Phase 2 · `02-VERIFICATION.md` **passed**, 3/3 must-haves + 11/11 sub-checks

- [x] **NET-01**: Cop and thief run as two separate processes under `config/police/` vs `config/thief/` (rule 1) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-01 | ✓ SATISFIED"
- [x] **NET-02**: No shared runtime state, memory, or variables between the two agents (rule 2) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-02 | ✓ SATISFIED"
- [x] **NET-03**: Each agent is simultaneously a FastMCP server (exposes tools) and client (calls the opponent's tools) (§C) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-03 | ✓ SATISFIED"
- [x] **NET-04**: The orchestrator is the single entry point, driving turn order through a proper state machine (rules 3–4) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-04 | ✓ SATISFIED"
- [x] **NET-05**: Every attempt to transition to an illegal state is reported (rule 5) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-05 | ✓ SATISFIED"
- [x] **NET-06**: A deadline tracker prevents freezing while waiting on the opponent (rule 6) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-06 | ✓ SATISFIED"
- [x] **NET-07**: A watchdog monitors process crashes and rescues data (rule 7) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-07 | ✓ SATISFIED"
- [x] **NET-08**: A geometric message sent over localhost is received and decoded correctly by the other agent (Stage 2 gate) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-08 | ✓ SATISFIED"
- [x] **NET-09**: The configuration file is verified byte-for-byte identical on both sides (rule 11) — **evidence:** `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md` "NET-09 | ✓ SATISFIED"

### Strategy Module (STRAT) — Phase 3 · `03-VERIFICATION.md` **passed**, 3/3 §10.4 criteria

> **STRAT-01, STRAT-02 and STRAT-06 are reworded here.** They described a **trained tabular
> Q-learning policy with a Bayes + Manhattan heuristic fallback**, which Phase 3 **withdrew** as
> unsound under the book's simultaneous turn order (§5.3.2 p.35). `docs/PRD_rl_strategy.md`
> carries a `⛔ SUPERSEDED — DO NOT IMPLEMENT` banner pointing at `docs/PRD_matrix_mover.md`, and
> `03-VERIFICATION.md` flagged this file's stale wording as **"OPEN, flagged not fixed"** because
> "correcting only the Phase-3 rows would misrepresent its state". This pass corrects the whole
> file, so the rows are corrected with it. The old text is preserved verbatim in the
> `03-VERIFICATION.md` quote cited by STRAT-01 below.

- [x] **STRAT-01**: Move selection comes from the algorithm — a matrix game solved per turn and sampled from its equilibrium, over a learned 15-weight evaluation (§B; **supersedes** the withdrawn tabular Q-learning wording) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "Move selection comes from the algorithm — a solved matrix game per turn, sampled from its equilibrium"
- [x] **STRAT-02**: Unvisited and uncertain states are handled inside the mover itself — the matrix game is solved fresh every turn from the current board, so there is no table to miss and no separate fallback path (**supersedes** the withdrawn Bayes + Manhattan fallback wording) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "a simultaneous-move matrix-game mover over a learned weight vector"
- [x] **STRAT-03**: The strategy module is pluggable — declared in config `[strategy]` as `police_class`/`thief_class`, separate from networking (§C) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "The strategy module is pluggable via config `[strategy]`, separate from networking"
- [x] **STRAT-04**: Given a known target location, the agent computes and walks the shortest path with no manual intervention (Stage 3 gate) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "Given a known target location, the agent computes and walks the shortest path with no manual intervention"
- [x] **STRAT-05**: The cop selects barrier placement through the same move decision, and barrier turns are counted against the shortest-path bound (STRATEGY.md) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "`move_turns + barrier_turns == the initial BFS distance`"
- [x] **STRAT-06**: Training is offline (self-play); the learned **weight vector** ships (`artifacts/run2*/weights.json`, `config/*/weights.json`), and learning curves are instrumented from the first run (rule 42; **supersedes** the withdrawn "trained Q-table ships" wording) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "no `QLearningBrain`,"
- [x] **STRAT-07**: The algorithm chooses the move — the language model never does (rule 25) — **evidence:** `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md` "The **algorithm** decides, never the LLM (rule 25 / STRAT-07)"

### Language & Scent (LANG) — Phase 4 · `04-VERIFICATION.md` **human_needed** — mechanisms verified (mocked), live-API confirmation open

- [ ] **LANG-01**: Each turn an agent sends a free-text verbal hint of at most the hint word limit (Table 14) — **open:** the mocked run measured 68/68 turns with a max of 11 words, but §10.4 criterion 3 is recorded as "✓ VERIFIED (mocked) / ? PENDING (live)" and the **responder** side has never been live-measured since 05-06 changed responder hint composition on 2026-08-14. Closes when a live GATE-4 run writes a non-PENDING `docs/phases/phase-4/gate4_measurement_live.json` for both seats — **status:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "status: human_needed"
- [x] **LANG-02**: Communication is natural language only — no direct numeric coordinates in the protocol (rules 26–27) — **evidence:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "blocks digit-pair/row-column patterns on the send path"
- [x] **LANG-03**: Hints may be lies; the `intent` flag (`truth | lie`) is committed in advance (§5.3) — **evidence:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "no call path can produce text before an intent exists"
- [x] **LANG-04**: Each agent emits scent — strength 0.9 at source, decaying 0.10 per turn, over a 5×5 window (all fixed) — **evidence:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "This criterion has no live-API dependency"
- [x] **LANG-05**: A belief map (probability grid over opponent position) updates via Bayes rule from scent + hints (§A) — **evidence:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "mean posterior L1 shift 1.171 on those turns, exact no-op on the other 114"
- [ ] **LANG-06**: The LLM decodes incoming hints into an inference and generates the outgoing bluff text (§6.2) — **open:** the decode and compose paths are structurally verified and mocked-measured, but "live decode accuracy against a real model is the pending half" and the responder side is unmeasured post-05-06. Closes with LANG-01, on the same live GATE-4 run — **status:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "Requires a real ANTHROPIC_API_KEY"
- [x] **LANG-07**: The scent-emission decay model is cryptographically locked before the game starts (rule 23) — **evidence:** `.planning/phases/04-language-and-scent/04-VERIFICATION.md` "`HandshakeKey.SCENT_DIGEST`, `HandshakeOutcome.SCENT_MISMATCH`"

### Cloud Tunneling (CLOUD) — Phase 5 · **GATE-5 MET**, both §10.4 criteria PASS · `05-VERIFICATION.md` **human_needed** 20/21, no code gap

- [x] **CLOUD-01**: Each peer is exposed to the public internet via a tunneling tool (ngrok/Localtonet) (rule 10) — **evidence:** `.planning/phases/05-cloud-exposure-and-tunneling/05-VERIFICATION.md` "CLOUD-01 — each peer reachable via tunnel | ✓ SATISFIED"
- [x] **CLOUD-02**: A remote agent connects via tunnel and plays a full round against the local agent (Stage 5 gate) — **evidence:** `.planning/phases/05-cloud-exposure-and-tunneling/05-VERIFICATION.md` "CLOUD-02 — a remote agent plays a full round | ✓ SATISFIED"

> `05-VERIFICATION.md`'s single remaining `human_verification` item **is this reconciliation**:
> *"Decide the repo-wide REQUIREMENTS.md status table (do not tick Phase 5 alone) … Fix the table
> as a whole or leave it alone."* This pass fixes it as a whole.

### Security & Cryptography (SEC) — Phase 6 · `06-VERIFICATION.md` **passed**, 11/11 must-haves

- [x] **SEC-01**: Moves use a commit-reveal protocol based on SHA-256 (rule 17) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-01 | ✓ SATISFIED"
- [x] **SEC-02**: Four phases — Commit (hash) → Acknowledge → Reveal (move + hint, nonce hidden) → Final Reveal / Audit (§E) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-02 | ✓ SATISFIED"
- [x] **SEC-03**: The hash covers `{state, move, intent, nonce}` serialized as canonical JSON (`sort_keys=True, separators=(",",":")`) (§E) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-03 | ✓ SATISFIED"
- [x] **SEC-04**: The nonce is generated with `secrets.token_hex(16)`, kept secret until game end, verified with `secrets.compare_digest` (rule 18) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-04 | ✓ SATISFIED"
- [x] **SEC-05**: Any hash mismatch at audit is a technical loss — score 0 to the forging team (rule 19) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-05 | ✓ SATISFIED"
- [x] **SEC-06**: A signed Step-0 hardware declaration (OS/CPU/RAM/GPU/model/commit hash) is published before the first move (rules 24, 53) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-06 | ✓ SATISFIED"
- [x] **SEC-07**: Barrier and capture declarations are open and truthful; false barrier/capture declarations are forbidden (rules 15–16, 21–22) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-07 | ✓ SATISFIED"
- [x] **SEC-08**: A comprehensive mutual log audit runs at the end of every game (rule 36) — **evidence:** `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md` "SEC-08 | ✓ SATISFIED"

### Reporting & Visualization Shell (REPORT) — Phase 7 · **implemented and gate-measured, NOT phase-verified — no `07-VERIFICATION.md` exists**

> **Every REPORT row stays open, and the reason is the same for all nine.** Phase 7 has never
> been through `/gsd:verify-work 7`; 11 of its 12 plans executed and `GATE-7-MEASUREMENT.md`
> reports criteria 2 and 3 **PASS** and criterion 1 as **dry-run PASS + live PENDING**. That is
> real evidence and it is recorded per row below — but a gate measurement is not a phase
> verification, and erasing the distinction is exactly what this reconciliation exists to stop.
> All nine close together when 07-10 delivers the live send and a `07-VERIFICATION.md` is written.

- [ ] **REPORT-01**: At game end both agents automatically email a signed JSON report to `rmisegal+uoh26finalgame@gmail.com` (rules 32, 35, 51) — **open:** the live send has never happened. Both shipped `config/*/reporting.json` still read `dry_run` and `measure_gate7.py` clears the Gmail credential environment variables at import, so nothing in this repo can have transmitted. Closes in **07-10** (`docs/phases/phase-7/OAUTH-RUNBOOK.md`) — **status:** `docs/phases/phase-7/GATE-7-MEASUREMENT.md` "Criterion 1 is NOT closed by this document"
- [ ] **REPORT-02**: Outgoing mail passes the gatekeeper chain: Quota Manager → Token Bucket → DOS Detector → Gmail API (rules 28–29) — **open:** gate-measured only. Closes when `07-VERIFICATION.md` is written — **status:** `docs/phases/phase-7/GATE-7-MEASUREMENT.md` "dry-run PASS, live"
- [ ] **REPORT-03**: The token bucket implements `tokens ← min(C, tokens + r·Δt)`, allowing a send iff `tokens ≥ 1` (Table 19) — **open:** gate-measured only; no phase verification exists for Phase 7 — **status:** `docs/PRD_gatekeeper.md` "Token Bucket"
- [ ] **REPORT-04**: HTTP 429 is handled with backoff; the mail interface uses a send-only OAuth scope (rules 28, 30) — **open:** the backoff ladder and the scope gate are measured in the dry run, but the scope has never been exercised against Google's consent screen. Closes in **07-10** and with `07-VERIFICATION.md` — **status:** `docs/phases/phase-7/GATE-7-MEASUREMENT.md` "backoff_ladder"
- [ ] **REPORT-05**: Reports are attached JSON files, never free text (rules 33–34) — **open:** gate-measured in the dry run (`attachment.content_type == "application/json"`, body carries no report content); no phase verification exists — **status:** `docs/phases/phase-7/GATE-7-MEASUREMENT.md` "attachment"
- [ ] **REPORT-06**: Four JSON artifacts are produced — `declaration_`, `config_`, `log_`, `result_` (PARAMETERS.md) — **open:** three of the four are written by a real game; **`declaration_` has ZERO production callers** — `build_declaration_artifact` / `write_declaration_artifact` / `DeclarationContext` are reached only by their own module, the `__init__` re-export and tests. Closes in **08-04**, which owns the first production caller — **status:** `docs/SUBMISSION-CHECKLIST.md` "zero production callers"
- [ ] **REPORT-07**: The final JSON reports total tokens consumed per game and across the series (rule 54) — **open:** `result_<game_id>.json` carries both token totals and is gate-measured; no phase verification exists — **status:** `docs/PRD_result_artifact.md` "tokens"
- [ ] **REPORT-08**: The live GUI displays only local truth — never the full objective board (rules 8–9) — **open:** §10.4 criterion 2 is measured **PASS** (7 modules scanned, 0 violations, both seats' published snapshots free of `cop`/`thief`/`barriers`, empty-scan control at exit 2), and `check_local_truth.sh` is a CI job. Only the phase verification is missing — **status:** `docs/phases/phase-7/GATE-7-MEASUREMENT.md` "Criterion 2 — the live GUI displays state, only local truth · **PASS**"
- [ ] **REPORT-09**: A replay viewer reconstructs a recorded game log and verifies it, showing `Verified OK` (rule 20) — **open:** §10.4 criterion 3 is measured **PASS** on one real game with all three verdict states shown and both sources deleted first. Only the phase verification is missing — **status:** `docs/phases/phase-7/GATE-7-MEASUREMENT.md` "Criterion 3 — the replay app shows `Verified OK` · **PASS**"

### Submission & League (SUB) — Phase 8 · **in progress**, 2 of 14 plans executed

> All twelve are open. Three of the four §10.4 submission-gate criteria are structurally
> **human-completed** — creating public repositories, pushing a tag, mailing the lecturer,
> playing league games and filling the submission form are not Claude's to do — and the
> unattended half is in progress.

- [ ] **SUB-01**: Two separate public GitHub repos (cop, thief), each README cross-linking the other (rule 49) — **open:** one repo exists and no split has been built. Built locally in **08-10**, published by a human in **08-12** — **status:** `docs/SUBMISSION-CHECKLIST.md` "only one repo, not two"
- [ ] **SUB-02**: Every repo includes README, `config/`, PRD files, a PLAN file, and TODO files (rule 50) — **open:** checked per split output in **08-10**; there is nothing to check until the split exists — **status:** `.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` "rule 50 checked per output"
- [ ] **SUB-03**: Academic README with its six mandatory sections, including learning curves (RL) and `Verified OK` screenshots (rule 42) — **open:** the root README fails all seven §2.1 items and describes a **withdrawn** mechanism (rows G1-01…G1-09). Rewritten in **08-06** — **status:** `docs/SUBMISSION-CHECKLIST.md` "The root README describes a system this repository does not ship"
- [ ] **SUB-04**: Secrets in `.gitignore`, never pushed; `.env-example` committed with dummy values (rules 39–40) — **open:** the scan is clean over 886 tracked text files and `.env` is proven ignored, but root-level `graph.json` and `graph.html` are **not** ignored (rows G4-06/G4-07) and the planted-secret control is still 08-03's — **status:** `docs/SUBMISSION-CHECKLIST.md` "are **not** ignored"
- [ ] **SUB-05**: The submitted version carries an appropriate Git tag (rule 41) — **open:** `git tag -l` is empty. The tag is cut in **08-11** and pushed by a human in **08-12**; it must land on the commit the league games actually ran on — **status:** `docs/SUBMISSION-CHECKLIST.md` "no Git tag"
- [ ] **SUB-06**: A unique 8-character team identification code (no spaces) is defined (rule 45) — **open:** `khm-mn17` already ships in `config/*/security.json`; the row closes when **08-10** proves it survives the split into both repos — **status:** `.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` "08-10 checks it survives the split"
- [ ] **SUB-07**: At least the minimum league games are played against different teams — one scoring game per opponent, no rematches for points; the game count is declared accurately and never falsely (rules 31, 37, 38, 52) — **open:** zero league games have been played. The ledger is **08-04**'s, the games are **08-13**'s (human), and the declared value is **08-14**'s. `config/police/games_played.json` reads 1922 and `config/thief/` reads 1915 — two counters for one team, disagreeing by seven, both known-wrong — **status:** `docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md` "games_played"
- [ ] **SUB-08**: Each game emails the lecturer the GitHub commit hash the code ran on (rule 53) — **open:** the declaration wrapper that would carry it has no production caller. **08-04** wires it; **08-13** runs it live — **status:** `docs/SUBMISSION-CHECKLIST.md` "has never been written by a real game"
- [ ] **SUB-09**: The submission form is downloaded, filled, and saved as PDF, unaltered/unforged (rule 43) — **open:** OQ8-3 — neither `docs/PARAMETERS.md` nor `docs/RULES.md` records where the form lives, and no location is guessed. **08-14** (human) — **status:** `.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` "No location is guessed"
- [ ] **SUB-10**: The assignment is submitted separately for each team member (rule 44) — **open:** solo team, one submission, and it is **08-14**'s (human) — **status:** `docs/RULES.md` "Submit the assignment **separately for each team member**"
- [ ] **SUB-11**: A self-assessment score is given for code quality only — not league results (rule 55) — **open:** OQ8-4 — **08-11** drafts the evidence table with the score field blank; the number is **08-14**'s (human) — **status:** `.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` "the score field **blank**"
- [ ] **SUB-12**: Parameter values respect fixed/minimum/negotiable status — minimum raised only by mutual agreement, never lowered; each game's config is attached to the repo with a per-game name (rule 12, PARAMETERS §2) — **open:** the per-game config naming has no league game to name yet; OQ8-7 leaves the agreed `token_ceiling` undecided by design. **08-04** and **08-13** — **status:** `.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` "already refuses to default it"

### Code-Quality Gate (QUAL) — cross-cutting, every phase

From [docs/SEGAL_GUIDELINES.md](../docs/SEGAL_GUIDELINES.md) §19.1 Table 5. Measured continuously
by `scripts/check_submission.py`; its Table-5 section is the live verdict.

- [x] **QUAL-01**: All business logic sits behind an SDK layer; GUI/CLI are thin shells (Table 5) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "QUAL-01 | SATISFIED"
- [ ] **QUAL-02**: OOP with no duplication — extract at 2+ copies into a shared module/base class/mixin (Table 5) — **open:** Table 5 marks this row `Code review`; the audit prints it `UNJUDGED` (row T5-02) rather than scoring a pass no script earned — **status:** `docs/SUBMISSION-CHECKLIST.md` "OOP / no duplication -- extract at 2+ copies"
- [x] **QUAL-03**: Every external API call passes through a single API gatekeeper (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "Sec17 API gatekeeper for all external calls, rate limits from config"
- [x] **QUAL-04**: Rate limits live in configuration, never in source (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "Rate limits in configuration, never in source"
- [ ] **QUAL-05**: On overflow the gatekeeper queues (FIFO), never crashes (Table 5) — **open:** Table 5 enforces this row by `Integration test`, so its verdict is the suite's; the audit prints `UNJUDGED` (row T5-05) unless run with `--run-suite` — **status:** `docs/SUBMISSION-CHECKLIST.md` "Overflow handling -- queue, never crash"
- [x] **QUAL-06**: Version tracking starts at 1.00 in `version.py` and in the config JSON files (Table 5) — **evidence:** `.planning/phases/01-base-logic/01-VERIFICATION.md` "QUAL-06 | SATISFIED"
- [ ] **QUAL-07**: TDD — red → green → refactor; tests cover happy path and error case; external services mocked (Table 5) — **open:** Table 5 marks this row `Work process`. Commit order is a correlation, not proof of authorship order; the per-plan SUMMARY files record the red-then-green sequences. `UNJUDGED` (row T5-07) — **status:** `docs/SUBMISSION-CHECKLIST.md` "TDD -- red -> green -> refactor"
- [x] **QUAL-08**: Every source and test file is ≤150 lines (excluding blanks/comments) — split, never compress (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "check_line_limit.sh exit 0; violations 0"
- [x] **QUAL-09**: `ruff check` reports zero violations (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "Sec17 / Table 5 zero Ruff violations"
- [x] **QUAL-10**: `pytest --cov` ≥ 85% with `fail_under = 85` (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "pyproject.toml declares fail_under: True"
- [ ] **QUAL-11**: Zero hardcoded values in source — config, `constants.py`, or `Enum` only (Table 5) — **open:** Table 5 marks this row `Code review`. A literal is only "hardcoded" relative to whether it ought to be configurable, which no scan can decide; `docs/PARAMETERS.md` is the authority. `UNJUDGED` (row T5-11) — **status:** `docs/SUBMISSION-CHECKLIST.md` "Hardcoded values -- 0 in source"
- [x] **QUAL-12**: Zero secrets in source; `os.environ.get()` only; `.env-example` committed (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "provider-shape hits: 0"
- [x] **QUAL-13**: `uv` is the sole package manager; `pyproject.toml` + `uv.lock`, no `requirements.txt` (Table 5) — **evidence:** `docs/phases/phase-8/submission_audit_evidence.json` "requirements.txt files: none"

### Documentation (DOC) — cross-cutting, init + per building phase

- [ ] **DOC-01**: `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md` exist as full documents; `docs/TODO.md` is kept current as work progresses (§2.2, §2.5 step 6) — **open:** all three exist and are substantial (audit rows G1-10/11/12 PASS), and `docs/TODO.md` was brought current by this plan. The "kept current" clause is a standing obligation, not a one-time achievement, so it does not tick — **status:** `docs/phases/phase-8/submission_audit_evidence.json` "Sec2.2 mandatory document `docs/TODO.md`"
- [ ] **DOC-02**: Every algorithm/central mechanism has its own `docs/PRD_<mechanism>.md`, written in the phase that builds it (§2.3) — **open:** the package walk finds 10 mechanisms; **three are uncovered** — `src/pursuit/sdk/`, `src/pursuit/gui/` and the tunnel (`network/tunnel_manager.py`, which `PRD_mcp_transport.md` puts out of scope in as many words). Closes in **08-08** — **status:** `docs/SUBMISSION-CHECKLIST.md` "Three central mechanisms have no per-mechanism PRD"

## v2 Requirements

(None — single-milestone final project; all committed scope is v1.)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Neural-network / deep RL | Superseded twice: the tabular Q-table was withdrawn in Phase 3 (§5.3.2 p.35), and what ships is a matrix-game mover over a learned 15-weight evaluation |
| LLM choosing the move | Forbidden (rule 25); LLM only decodes hints and writes bluff text. Enforced by `scripts/check_no_llm_in_strategy.py`, a CI job since 07-09 |
| Shared runtime state between cop and thief | Immediate disqualification (rule 2); shared *library* OK, shared *live state* not |
| True/objective board in the live GUI | Disqualification (rule 9); only local truth. Enforced by `scripts/check_local_truth.py`, a CI job |
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

Every verdict below is drawn from the phase's own verification artifact, never from a tracker's
banner. `Pending` survives in exactly one place, and it says why.

| Requirements | Phase | Status |
|--------------|-------|--------|
| BASE-01 … BASE-08 | Phase 1 — Base Logic | **Verified passed** 2026-07-28 — `.planning/phases/01-base-logic/01-VERIFICATION.md`, 3/3 must-haves, all 8 REQ-IDs SATISFIED. **8/8 ticked** |
| NET-01 … NET-09 | Phase 2 — FastMCP Infrastructure | **Verified passed** 2026-07-29 — `.planning/phases/02-fastmcp-infrastructure/02-VERIFICATION.md`, 3/3 must-haves (GATE-1/2/3) + 11/11 sub-checks, all 9 REQ-IDs SATISFIED. **9/9 ticked** |
| STRAT-01 … STRAT-07 | Phase 3 — Blind Strategy (matrix mover, **not** Q-learning) | **Verified passed** — `.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md`, 3/3 §10.4 criteria. STRAT-01/02/06 **reworded by this pass** to the mechanism that shipped; 12 superseded plans banner-marked. **7/7 ticked** |
| LANG-01 … LANG-07 | Phase 4 — Language & Scent | **human_needed** — `.planning/phases/04-language-and-scent/04-VERIFICATION.md`, 3/3 mechanisms verified (mocked); live-API confirmation is the sole open item and the responder side is unmeasured since 05-06. **5/7 ticked; LANG-01 and LANG-06 held open** |
| CLOUD-01 … CLOUD-02 | Phase 5 — Cloud Exposure & Tunneling | **GATE-5 MET**, both §10.4 criteria PASS — `.planning/phases/05-cloud-exposure-and-tunneling/05-VERIFICATION.md` `human_needed` 20/21, and its one open item is this reconciliation. **2/2 ticked** |
| SEC-01 … SEC-08 | Phase 6 — Security & Cryptography | **Verified passed** 2026-08-09 — `.planning/phases/06-security-and-cryptography/06-VERIFICATION.md`, 11/11 must-haves, all 8 REQ-IDs SATISFIED. **8/8 ticked** |
| REPORT-01 … REPORT-09 | Phase 7 — Reporting Shell | **Gate-measured, NOT phase-verified.** `docs/phases/phase-7/GATE-7-MEASUREMENT.md`: criterion 2 PASS, criterion 3 PASS, criterion 1 dry-run PASS + **live PENDING**. 11 of 12 plans executed; **no `07-VERIFICATION.md` exists**. **0/9 ticked** |
| SUB-01 … SUB-12 | Phase 8 — Submission & League | **In progress** — 2 of 14 plans executed (08-01, 08-02). Three of the four gate criteria are structurally human-completed. **0/12 ticked** |
| QUAL-01 … QUAL-13 | Cross-cutting (every phase) | **Continuously measured** — `docs/phases/phase-8/submission_audit_evidence.json`, Table-5 section: 7 PASS / 1 GAP / 5 UNJUDGED. **9/13 ticked**; the four open rows are the ones Table 5 itself marks `Code review`, `Work process` or `Integration test` |
| DOC-01 … DOC-02 | Init + per building phase | Pending — DOC-01's "kept current" clause is a standing obligation with no terminal state, and DOC-02 has **3 of 10 mechanisms** uncovered (08-08). This is the one row where `Pending` is what the artifacts say. **0/2 ticked** |

**Coverage:**
- v1 requirements: **77 total** (8 BASE + 9 NET + 7 STRAT + 7 LANG + 2 CLOUD + 8 SEC + 9 REPORT + 12 SUB + 13 QUAL + 2 DOC)
- Mapped to phases / cross-cutting: 77
- Unmapped: 0 ✓
- Mandatory rules (55) all traceable: ✓
- **Satisfied: 48 of 77.** Open: 29 — 2 LANG (live API), 9 REPORT (no phase verification), 12 SUB (Phase 8 in progress), 4 QUAL (unjudgeable by machine), 2 DOC.

> The previous header read **"74 total"** against a per-family breakdown that sums to **77**, and
> the "Unmapped: 0 ✓" claim was built on the wrong number. Counted mechanically this pass:
> `grep -c "^- \[[ x]\]"` returns 77.

---
*Requirements defined: 2026-07-27*
*Reconciled project-wide 2026-08-17 by plan 08-02, in one pass, from the verification artifacts*
*Enforced by `scripts/check_requirements_ledger.py` — 0 clean · 1 any violation · 2 judged nothing*
