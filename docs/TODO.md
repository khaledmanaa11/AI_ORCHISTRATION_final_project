# TODO — Task List

**Version:** 1.00 · **Owner:** Khaled (solo) · **Last updated:** 2026-07-27

> Task tracker per [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md) §2.2 / §2.5 step 6 — **kept
> current as work progresses.** Split into phases (see [.planning/ROADMAP.md](../.planning/ROADMAP.md)),
> with priority, status, owner, and a definition of done per task. Requirements referenced
> by REQ-ID from [.planning/REQUIREMENTS.md](../.planning/REQUIREMENTS.md).

**Status:** ☐ not started · ◐ in progress · ☑ done
**Priority:** P0 blocking · P1 high · P2 normal

---

## Setup / Scaffolding (engineering prerequisites — not a game phase)

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| `uv init`, `pyproject.toml` (name/version 1.00/deps), `uv.lock` | P0 | ☐ | Khaled | `uv sync` works; no `requirements.txt`; `uv.lock` committed (QUAL-13) |
| Ruff + pytest + coverage config (`fail_under=85`, ruff select set) | P0 | ☐ | Khaled | `uv run ruff check` clean; `uv run pytest --cov` enforces ≥85% (QUAL-09/10) |
| `.gitignore` (`.env`, `*.key`, `*.pem`, `credentials.json`) + `.env-example` dummies | P0 | ☐ | Khaled | Secrets ignored; `.env-example` committed (QUAL-12, SUB-04) |
| `src/<pkg>/shared/version.py` = 1.00; SDK skeleton; `constants.py` | P0 | ☐ | Khaled | Version module reads 1.00; SDK is the single entry point (QUAL-01/06) |
| `config/police/` + `config/thief/` skeleton dirs | P0 | ☐ | Khaled | Two separate config dirs exist; no shared live state (NET-01/02) |
| Approve PRD/PLAN/TODO before development (§2.5 step 5) | P0 | ◐ | Khaled | Docs reviewed and approved by owner |

---

## Phase 1 — Base Logic  *(Milestone M1)*

Gate: legal movement; over-quota barrier rejected; capture on overlap.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 01-01 Board + orthogonal movement from config | P0 | ☐ | Khaled | Diagonal rejected; values from config; unit tests happy+error (BASE-01/08) |
| 01-02 Barrier placement + quota enforcement | P0 | ☐ | Khaled | Barrier beyond quota rejected; tested (BASE-02) |
| 01-03 Capture + end conditions + scoring | P0 | ☐ | Khaled | 3 capture conditions + survival + scoring table pass tests (BASE-03…07) |
| 01-04 SDK facade + integration gate + doc triplet | P0 | ☐ | Khaled | engine.py thin facade (QUAL-01); GATE-1/2/3 pass; docs/phases/phase-1/{PRD,PLAN,TODO}.md created (BASE-03/04/05, QUAL-01) |
| 01-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | This table marked ☑; DoD rolled (DOC-01) |

---

## Phase 2 — FastMCP Infrastructure  *(Milestone M2)*

Gate: geometric message A→B over localhost decoded correctly.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 02-00 Phase-2 scaffold + test stubs | P0 | ☐ | Khaled | `uv add fastmcp` (3.4.5) + `pytest-asyncio`; per-agent `network.json`; stubs collect and exit 0 (QUAL-11/12/13) |
| 02-01 Network config loader + `loader_helpers` extraction | P0 | ☐ | Khaled | Fail-loud `NetworkParams`; one validator shared by both loaders (NET-01/02, QUAL-02) |
| 02-02 Message envelope + canonical-JSON config digest | P0 | ☐ | Khaled | `{type,turn,sender,payload}` round-trips; key-order difference hashes equal (NET-08/09) |
| 02-03 Turn state machine + illegal-transition reporting | P0 | ☐ | Khaled | Enum + transitions table, no FSM library; every illegal attempt rejected **and** reported (NET-04/05) |
| 02-04 JSONL event log + watchdog | P0 | ☐ | Khaled | `flush()`+`fsync()` per write; incident record durable **before** exit fires (NET-05/07) |
| 02-05 Write `docs/PRD_mcp_transport.md` | P1 | ☐ | Khaled | Full per-mechanism PRD (§2.3) at v1.00, written before the code (DOC-02) |
| 02-06 Tool surface + peer runtime | P0 | ☐ | Khaled | Four `async def` tools; `receive_move` enqueues without blocking; shutdown releases port (NET-02/03/08) |
| 02-07 Deadline tracker + technical win | P0 | ☐ | Khaled | 30/3/5 from config; `ToolError` never becomes a technical win; truthful evidence (NET-06) |
| 02-08 Handshake + config-digest exchange | P0 | ☐ | Khaled | Mismatch aborts before move 1 with both digests logged; unreachable ≠ mismatch (NET-03/05/09) |
| 02-09 Orchestrator + thin `main.py` + dev launcher | P0 | ☐ | Khaled | Turn loop drives the machine; no shared runtime state; launcher is not a referee (NET-01/02/04/05/06/07) |
| 02-10 §10.4 gate tests + coverage audit | P0 | ☐ | Khaled | GATE-1/2/3 map to named tests; NET-01…09 audit closes; real two-process launch (NET-01…09) |
| 02-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 3 — Blind Strategy Module (RL policy)  *(Milestone M3)*

Gate: agent walks the shortest path to a known target unaided.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 03-01 `BrainBase` + registry (3 brains) | P0 | ☑ | Khaled | Pluggable via config `[strategy]`; value_search/chaser_cop/greedy_evader (STRAT-02/03) |
| 03-02 Simultaneous turn + matrix-game mover | P0 | ☑ | Khaled | `resolve_turn` joint resolver; equilibrium sampled, never an LLM (STRAT-01/04/07) |
| 03-03 Self-play harness + learning curves | P0 | ☑ | Khaled | 24,000 games; trained beats prior +14.5/+18.0 pts, significant at 95% (STRAT-06) |
| 03-04 Write `docs/PRD_matrix_mover.md` | P1 | ☑ | Khaled | Per-mechanism PRD committed; PRD_rl_strategy.md superseded (DOC-02) |
| 03-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 4 — Language and Scent  *(Milestone M4)*

Gate: hint→inference; scent decays; LLM emits a hint each turn (true or false).

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 04-01 Scent emission/decay + pre-game crypto lock | P0 | ☐ | Khaled | 0.9/0.10/5×5 exact; decay model locked (LANG-04/07) |
| 04-02 Bayesian belief map (scent + hints) | P0 | ☐ | Khaled | Belief updates via Bayes; tested (LANG-05) |
| 04-03 LLM hint decode + bluff gen with `intent` flag | P0 | ☐ | Khaled | ≤15-word hint each turn; intent committed; NL-only (LANG-01/02/03/06) |
| 04-04 Write `docs/PRD_scent_map.md`, `PRD_belief_map.md`, `PRD_deception.md` | P1 | ☐ | Khaled | Three per-mechanism PRDs committed (DOC-02) |
| 04-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 5 — Cloud Exposure and Tunneling  *(Milestone M5)*

Gate: remote agent plays a full round via tunnel.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 05-01 Tunnel integration + public URL in config | P0 | ☐ | Khaled | Peer reachable publicly via ngrok/Localtonet (CLOUD-01) |
| 05-02 Remote end-to-end round validation | P0 | ☐ | Khaled | Remote agent completes a full round (CLOUD-02) |
| 05-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 6 — Security and Cryptography  *(Milestone M6)*

Gate: move committed then revealed with valid nonce; Step-0 verified.
**Gate met — all three §10.4 criteria PASS on measured evidence
([GATE-6-MEASUREMENT.md](phases/phase-6/GATE-6-MEASUREMENT.md)); UAT 11/11 pass 2026-08-09.**

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 06-01 Crypto core — canonical-JSON hashing, nonce gen/verify, state record, durable ledger, `security.json` | P0 | ☑ | Khaled | `sort_keys`/`separators` exact; `secrets` used; round-trip + tamper proven in one test (SEC-01/03/04) |
| 06-02 Four-phase commit-reveal on the wire + barriers inside the committed action | P0 | ☑ | Khaled | Commit→Ack→Reveal, no reveal before the opponent's commit; barrier round-trips; nonce never on the wire log (SEC-01/02/04/07) |
| 06-03 Step-0 declaration + end-game mutual audit | P0 | ☑ | Khaled | Signed HW+commit-hash verified pre-game; audit catches both tamper classes → technical loss (SEC-05/06/07/08) |
| 06-04 Gate 6 measurement + `docs/PRD_commit_reveal.md` | P1 | ☑ | Khaled | One command, zero env vars, honest PASS/FAIL evidence; full per-mechanism PRD committed (DOC-02) |
| 06-96 Refresh the graphify graph (plan-phase + after execute) | P2 | ☑ | Khaled | GRAPH_REPORT.md current with `security/` and the new network modules — final refresh 6577 nodes / 11972 edges / 413 communities |
| 06-97 Create/refresh `docs/phases/phase-6/{PRD,PLAN,TODO}.md` | P1 | ☑ | Khaled | Phase triplet exists and matches the plan set (created 2026-08-09; all rows closed at verify-work) |
| 06-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 7 — Reporting and Visualization Shell  *(Milestone M7)*

Gate: summary mailed; GUI displays state (local truth); replay shows `Verified OK`.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 07-01 Gmail send-only + gatekeeper (quota/token-bucket/DOS) | P0 | ☐ | Khaled | 429 backoff; overflow queues; send-only scope (REPORT-02/03/04) |
| 07-02 Four JSON artifacts + auto end-game report + tokens | P0 | ☐ | Khaled | JSON attached, not free text; both sides report; tokens counted (REPORT-01/05/06/07) |
| 07-03 Local-truth live GUI + verifying replay viewer | P0 | ☐ | Khaled | GUI shows only local truth; replay = `Verified OK` (REPORT-08/09) |
| 07-04 Write `docs/PRD_gatekeeper.md` | P1 | ☐ | Khaled | Full per-mechanism PRD committed (DOC-02) |
| 07-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 8 — Submission and League Operations  *(Milestone M8)*

Gate: two cross-linked public repos; ≥2 scored league games played and reported.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 08-01 Split into two cross-linked public repos | P0 | ☐ | Khaled | Cop + thief repos; each has README/config/PRD/PLAN/TODO (SUB-01/02) |
| 08-02 Academic README + Git tag + 8-char team code | P0 | ☐ | Khaled | Six sections + learning curves + Verified-OK shots; tag; team code (SUB-03/05/06) |
| 08-03 Play ≥2 scored league games; auto-report + commit hash | P0 | ☐ | Khaled | Different teams; results reported; per-game commit hash emailed (SUB-07/08) |
| 08-04 Submission form (PDF, unaltered) + per-member + self-assessment | P0 | ☐ | Khaled | Form per member; code-quality self-assessment (SUB-09/10/11) |
| 08-99 Update `docs/TODO.md` — final DoD | P1 | ☐ | Khaled | All tables ☑; final checklist (§17) passed |

---

## Cross-cutting — Code-Quality Gate (every phase, continuous)

Verified on every commit; blocks merge if failing (Table 5 / QUAL-01…13).

| Check | Pri | Status | Owner | Definition of Done |
|-------|-----|--------|-------|--------------------|
| `uv run ruff check` → 0 violations | P0 | ☐ | Khaled | Clean on all committed code (QUAL-09) |
| `uv run pytest --cov` ≥ 85% | P0 | ☐ | Khaled | `fail_under=85` enforced (QUAL-10) |
| Every source/test file ≤ 150 lines | P0 | ☑ | Khaled | **Hard-enforced**: `scripts/check_line_limit.sh` via pre-commit hook (`core.hooksPath=scripts/hooks`) + CI (`.github/workflows/quality-gate.yml`); never `--no-verify` (QUAL-08) |
| Build/refresh graphify graph (Phase 3+) | P1 | ☐ | Khaled | `/gsd:graphify` at plan-phase & after execute for phases 3–8; `.planning/graphs/` current |
| 0 hardcoded values / 0 secrets | P0 | ☐ | Khaled | config/constants/Enum; `os.environ.get()` only (QUAL-11/12) |
| SDK layer + single gatekeeper + no duplication | P1 | ☐ | Khaled | Logic behind SDK; all external calls via gatekeeper (QUAL-01/02/03) |
| TDD + versioning 1.00 | P1 | ☐ | Khaled | Tests before/with code; version tracked (QUAL-06/07) |
| Prompt-engineering log maintained (§8.3) | P2 | ☐ | Khaled | Significant prompts logged with context/outputs |

---

## Per-phase documentation triplets (`docs/phases/phase-<N>/`)

Created at `plan-phase`, checked at `verify-work` — see the *Per-phase documentation triplet*
standing rule in [CLAUDE.md](../CLAUDE.md). A phase is not verified until its row is all ☑.

| Phase | PRD.md | PLAN.md | TODO.md | All TODOs ☑ |
|-------|--------|---------|---------|-------------|
| 1 Base Logic | ◐ | ◐ | ◐ | ☐ |
| 2 FastMCP Infrastructure | ☑ | ☑ | ☑ | ☐ |
| 3 Blind Strategy (RL) | ☑ | ☑ | ☑ | ☐ |
| 4 Language & Scent | ☐ | ☐ | ☐ | ☐ |
| 5 Cloud Tunneling | ☐ | ☐ | ☐ | ☐ |
| 6 Security & Crypto | ☐ | ☐ | ☐ | ☐ |
| 7 Reporting Shell | ☐ | ☐ | ☐ | ☐ |
| 8 Submission & League | ☐ | ☐ | ☐ | ☐ |

---
*Keep this file updated with progress (§2.5 step 6). Each `0N-99` task rolls its phase to ☑.*
