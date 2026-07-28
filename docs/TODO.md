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
| 02-01 FastMCP server+client scaffold + geometric tools | P0 | ☐ | Khaled | Symmetric peer; A→B localhost message decoded (NET-03/08) |
| 02-02 Orchestrator + state machine + illegal-transition report | P0 | ☐ | Khaled | Single entry point; illegal transitions reported (NET-04/05) |
| 02-03 Watchdog + deadline tracker + byte-identical config check | P0 | ☐ | Khaled | No hang on silent opponent; config verified identical (NET-06/07/09) |
| 02-04 Write `docs/PRD_mcp_transport.md` | P1 | ☐ | Khaled | Full per-mechanism PRD (§2.3) committed (DOC-02) |
| 02-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 3 — Blind Strategy Module (RL policy)  *(Milestone M3)*

Gate: agent walks the shortest path to a known target unaided.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 03-01 `BrainBase` + Bayes+Manhattan fallback | P0 | ☐ | Khaled | Pluggable via config `[strategy]`; fallback tested (STRAT-02/03) |
| 03-02 State encoding + tabular Q-learning + ε-greedy | P0 | ☐ | Khaled | Shortest path to known target unaided; algorithm picks move (STRAT-01/04/07) |
| 03-03 Offline self-play harness + learning curves | P0 | ☐ | Khaled | Trained Q-table beats baseline; curves saved from run 1 (STRAT-06) |
| 03-04 Write `docs/PRD_rl_strategy.md` | P1 | ☐ | Khaled | Full per-mechanism PRD committed (DOC-02) |
| 03-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

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

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 06-01 Canonical-JSON hashing + nonce gen/verify | P0 | ☐ | Khaled | `sort_keys`/`separators` exact; `secrets` used (SEC-03/04) |
| 06-02 Four-phase commit-reveal in orchestrator | P0 | ☐ | Khaled | Commit→Ack→Reveal→Audit; mismatch=loss (SEC-01/02/05) |
| 06-03 Step-0 declaration + end-game mutual audit | P0 | ☐ | Khaled | Signed HW+commit-hash pre-game; audit runs (SEC-06/07/08) |
| 06-04 Write `docs/PRD_commit_reveal.md` | P1 | ☐ | Khaled | Full per-mechanism PRD committed (DOC-02) |
| 06-99 Update `docs/TODO.md` on phase completion | P1 | ☐ | Khaled | Table marked ☑ (DOC-01) |

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
| 2 FastMCP Infrastructure | ☐ | ☐ | ☐ | ☐ |
| 3 Blind Strategy (RL) | ☐ | ☐ | ☐ | ☐ |
| 4 Language & Scent | ☐ | ☐ | ☐ | ☐ |
| 5 Cloud Tunneling | ☐ | ☐ | ☐ | ☐ |
| 6 Security & Crypto | ☐ | ☐ | ☐ | ☐ |
| 7 Reporting Shell | ☐ | ☐ | ☐ | ☐ |
| 8 Submission & League | ☐ | ☐ | ☐ | ☐ |

---
*Keep this file updated with progress (§2.5 step 6). Each `0N-99` task rolls its phase to ☑.*
