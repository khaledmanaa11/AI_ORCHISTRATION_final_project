# TODO — Task List

**Version:** 1.00 · **Owner:** Khaled (solo) · **Last updated:** 2026-08-17
**Reconciled project-wide 2026-08-17 by plan 08-02**, from the `NN-VERIFICATION.md` and
`GATE-N-MEASUREMENT.md` artifacts — never from this file's own prior claims.

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
| `uv init`, `pyproject.toml` (name/version 1.00/deps), `uv.lock` | P0 | ☑ | Khaled | `uv sync` works; no `requirements.txt`; `uv.lock` committed (QUAL-13) |
| Ruff + pytest + coverage config (`fail_under=85`, ruff select set) | P0 | ☑ | Khaled | `uv run ruff check` clean; `uv run pytest --cov` enforces ≥85% (QUAL-09/10) |
| `.gitignore` (`.env`, `*.key`, `*.pem`, `credentials.json`) + `.env-example` dummies | P0 | ☑ | Khaled | Secrets ignored; `.env-example` committed (QUAL-12, SUB-04) |
| `src/<pkg>/shared/version.py` = 1.00; SDK skeleton; `constants.py` | P0 | ☑ | Khaled | Version module reads 1.00; SDK is the single entry point (QUAL-01/06) |
| `config/police/` + `config/thief/` skeleton dirs | P0 | ☑ | Khaled | Two separate config dirs exist; no shared live state (NET-01/02) |
| Approve PRD/PLAN/TODO before development (§2.5 step 5) | P0 | ☑ | Khaled | Docs reviewed and approved by owner |

---

## Phase 1 — Base Logic  *(Milestone M1)*

Gate: legal movement; over-quota barrier rejected; capture on overlap.
**Gate met and phase VERIFIED — [01-VERIFICATION.md](../.planning/phases/01-base-logic/01-VERIFICATION.md)
`status: passed`, 3/3 must-haves, 2026-07-28.** BASE-01…BASE-08 plus QUAL-01 and QUAL-06 are each
recorded SATISFIED there. This section carried **no banner and every row ☐ for three weeks after
that verification landed** — the largest doc/reality gap in the repository, closed 2026-08-17 by
plan 08-02 together with `docs/phases/phase-1/TODO.md`.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 01-01 Board + orthogonal movement from config | P0 | ☑ | Khaled | Diagonal rejected; values from config; unit tests happy+error (BASE-01/08) |
| 01-02 Barrier placement + quota enforcement | P0 | ☑ | Khaled | Barrier beyond quota rejected; tested (BASE-02) |
| 01-03 Capture + end conditions + scoring | P0 | ☑ | Khaled | 3 capture conditions + survival + scoring table pass tests (BASE-03…07) |
| 01-04 SDK facade + integration gate + doc triplet | P0 | ☑ | Khaled | engine.py thin facade (QUAL-01); GATE-1/2/3 pass; docs/phases/phase-1/{PRD,PLAN,TODO}.md created (BASE-03/04/05, QUAL-01) |
| 01-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | This table marked ☑; DoD rolled (DOC-01) |

---

## Phase 2 — FastMCP Infrastructure  *(Milestone M2)*

Gate: geometric message A→B over localhost decoded correctly.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 02-00 Phase-2 scaffold + test stubs | P0 | ☑ | Khaled | `uv add fastmcp` (3.4.5) + `pytest-asyncio`; per-agent `network.json`; stubs collect and exit 0 (QUAL-11/12/13) |
| 02-01 Network config loader + `loader_helpers` extraction | P0 | ☑ | Khaled | Fail-loud `NetworkParams`; one validator shared by both loaders (NET-01/02, QUAL-02) |
| 02-02 Message envelope + canonical-JSON config digest | P0 | ☑ | Khaled | `{type,turn,sender,payload}` round-trips; key-order difference hashes equal (NET-08/09) |
| 02-03 Turn state machine + illegal-transition reporting | P0 | ☑ | Khaled | Enum + transitions table, no FSM library; every illegal attempt rejected **and** reported (NET-04/05) |
| 02-04 JSONL event log + watchdog | P0 | ☑ | Khaled | `flush()`+`fsync()` per write; incident record durable **before** exit fires (NET-05/07) |
| 02-05 Write `docs/PRD_mcp_transport.md` | P1 | ☑ | Khaled | Full per-mechanism PRD (§2.3) at v1.00, written before the code (DOC-02) |
| 02-06 Tool surface + peer runtime | P0 | ☑ | Khaled | Four `async def` tools; `receive_move` enqueues without blocking; shutdown releases port (NET-02/03/08) |
| 02-07 Deadline tracker + technical win | P0 | ☑ | Khaled | 30/3/5 from config; `ToolError` never becomes a technical win; truthful evidence (NET-06) |
| 02-08 Handshake + config-digest exchange | P0 | ☑ | Khaled | Mismatch aborts before move 1 with both digests logged; unreachable ≠ mismatch (NET-03/05/09) |
| 02-09 Orchestrator + thin `main.py` + dev launcher | P0 | ☑ | Khaled | Turn loop drives the machine; no shared runtime state; launcher is not a referee (NET-01/02/04/05/06/07) |
| 02-10 §10.4 gate tests + coverage audit | P0 | ☑ | Khaled | GATE-1/2/3 map to named tests; NET-01…09 audit closes; real two-process launch (NET-01…09) |
| 02-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 3 — Blind Strategy Module (RL policy)  *(Milestone M3)*

Gate: agent walks the shortest path to a known target unaided.
**Gate met — measured 2026-08-16, retroactively
([03-VERIFICATION.md](../.planning/phases/03-blind-strategy-module-rl-policy/03-VERIFICATION.md)).
All three §10.4 criteria PASS. The phase was closed on 2026-08-08 by chore commit `da345dd`
rather than by `/gsd:verify-work 3`, and that skipped pass cost one thing: criterion 1 had no
evidence at all between 2026-08-08 and 2026-08-16, because its only test was deleted with the
run-1 stack and never replaced. Restored in 03-05 below. The 12 superseded plans 03-14..03-25
are a deliberate, book-cited descope (§5.3.2 p.35), not unfinished work.**

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 03-01 `BrainBase` + registry (3 brains) | P0 | ☑ | Khaled | Pluggable via config `[strategy]`; value_search/chaser_cop/greedy_evader (STRAT-02/03) |
| 03-02 Simultaneous turn + matrix-game mover | P0 | ☑ | Khaled | `resolve_turn` joint resolver; equilibrium sampled, never an LLM (STRAT-01/04/07) |
| 03-03 Self-play harness + learning curves | P0 | ☑ | Khaled | 24,000 games; trained beats prior +14.5/+18.0 pts, significant at 95% (STRAT-06) |
| 03-04 Write `docs/PRD_matrix_mover.md` | P1 | ☑ | Khaled | Per-mechanism PRD committed; PRD_rl_strategy.md superseded (DOC-02) — banner written 2026-08-16, dated to the 2026-08-08 supersession |
| 03-05 Restore the §10.4 criterion-1 gate test | P0 | ☑ | Khaled | `tests/integration/test_shortest_path.py` — 7 starts, frozen thief, exact-1 BFS decrease per move turn, `move+barrier == initial distance`; proven able to fail (STRAT-04) |
| 03-98 Retroactive phase verification report | P1 | ☑ | Khaled | `03-VERIFICATION.md` records all three criteria, the descope, the criterion-2 reword, and its own late authorship (DOC-01) |
| 03-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 4 — Language and Scent  *(Milestone M4)*

Gate: hint→inference; scent decays; LLM emits a hint each turn (true or false).
**14/14 plans executed; phase verdict `human_needed` —
[04-VERIFICATION.md](../.planning/phases/04-language-and-scent/04-VERIFICATION.md), 3/3 book
success-criteria mechanisms verified (mocked) + 1/1 robustness item.** Criterion 2 (scent) has
**no live-API dependency** and is verified outright; criteria 1 and 3 read
`✓ VERIFIED (mocked) / ? PENDING (live)`. The task rows below are ticked because the work landed;
**the phase gate is not met** and `LANG-01` / `LANG-06` are deliberately held open in
[REQUIREMENTS.md](../.planning/REQUIREMENTS.md) — a live GATE-4 run is needed, and the responder
side has been unmeasured since 05-06 changed responder hint composition on 2026-08-14.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 04-01 Scent emission/decay + pre-game crypto lock | P0 | ☑ | Khaled | 0.9/0.10/5×5 exact; decay model locked (LANG-04/07) |
| 04-02 Bayesian belief map (scent + hints) | P0 | ☑ | Khaled | Belief updates via Bayes; tested (LANG-05) |
| 04-03 LLM hint decode + bluff gen with `intent` flag | P0 | ☑ | Khaled | ≤15-word hint each turn; intent committed; NL-only (LANG-01/02/03/06) |
| 04-04 Write `docs/PRD_scent_map.md`, `PRD_belief_map.md`, `PRD_deception.md` | P1 | ☑ | Khaled | Three per-mechanism PRDs committed (DOC-02) |
| 04-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 5 — Cloud Exposure and Tunneling  *(Milestone M5)*

Gate: remote agent plays a full round via tunnel.
**Gate met — both §10.4 criteria PASS
([GATE-5-MEASUREMENT.md](phases/phase-5/GATE-5-MEASUREMENT.md)).** Criterion 1 measured
2026-08-09 against the reserved domain; criterion 2 closed 2026-08-16 by remote-round
**attempt 4** — two machines on two networks, hotspot ↔ wired, games `b22361aa93ccf310` and
`d265603c116a9f99`, agreeing `capture` + `audit_verdict matched=true` on BOTH machines, one
shared UID each, live `claude-haiku-4-5` both sides. Attempts 1–3 are retained beside it with
their honest failure verdicts (rule 38); criterion 2 was re-derived from the raw JSONL, by
script, in three separate verification passes.

Beyond the gate, two adversarial rounds found **ten** further defects (G6–G10 plus deferred
#4, #10 and the envelope-boundary class), closed by plans 05-12…05-18. Five of those shared
one shape — an unexpected envelope type at a layer boundary dropped or misread — every one a
rules-16/22 false-declaration path reachable by an honest peer. 05-18 therefore pinned the
class with a source-enumerated guard over all 12 queue-pull sites rather than fixing the
fifth instance alone; the guard found a sixth on its first run (deferred #19, latent because
shipped config is `commit_reveal: true`). Suite 1374 → **1539 passed**, coverage 96.64%.

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 05-01 Tunnel integration + public URL in config | P0 | ☑ | Khaled | Peer reachable publicly via ngrok/Localtonet (CLOUD-01) |
| 05-02 Remote end-to-end round validation | P0 | ☑ | Khaled | Remote agent completes a full round (CLOUD-02) — closed 2026-08-16, attempt 4: two live-LLM games over the tunnel, agreeing verdicts + matched audits on both machines (phase-5 GATE-5-MEASUREMENT.md) |
| 05-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |

---

## Phase 6 — Security and Cryptography  *(Milestone M6)*

Gate: move committed then revealed with valid nonce; Step-0 verified.
**Gate met and phase closed — all three §10.4 criteria PASS on measured evidence
([GATE-6-MEASUREMENT.md](phases/phase-6/GATE-6-MEASUREMENT.md)); UAT 2026-08-09 11/11.
An adversarial audit during verify-work found 2 security gaps beyond the gate's own criteria
— the mutual audit's join key was the peer's own unvalidated `envelope.turn`, making both the
D-67 forgery check and the rule-36 coverage check bypassable by turn-skew, and a caught
mismatch never reached a durable outcome record. Both closed by plan 06-05; gate re-measured
afterwards, still PASS.**

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 06-01 Crypto core — canonical-JSON hashing, nonce gen/verify, state record, durable ledger, `security.json` | P0 | ☑ | Khaled | `sort_keys`/`separators` exact; `secrets` used; round-trip + tamper proven in one test (SEC-01/03/04) |
| 06-02 Four-phase commit-reveal on the wire + barriers inside the committed action | P0 | ☑ | Khaled | Commit→Ack→Reveal, no reveal before the opponent's commit; barrier round-trips; nonce never on the wire log (SEC-01/02/04/07) |
| 06-03 Step-0 declaration + end-game mutual audit | P0 | ☑ | Khaled | Signed HW+commit-hash verified pre-game; audit catches both tamper classes → technical loss (SEC-05/06/07/08) |
| 06-04 Gate 6 measurement + `docs/PRD_commit_reveal.md` | P1 | ☑ | Khaled | One command, zero env vars, honest PASS/FAIL evidence; full per-mechanism PRD committed (DOC-02) |
| 06-96 Refresh the graphify graph (plan-phase + after execute) | P2 | ☑ | Khaled | GRAPH_REPORT.md current with `security/` and the new network modules — final refresh 6577 nodes / 11972 edges / 413 communities |
| 06-97 Create/refresh `docs/phases/phase-6/{PRD,PLAN,TODO}.md` | P1 | ☑ | Khaled | Phase triplet exists and matches the plan set (created 2026-08-09; all rows closed at verify-work) |
| 06-99 Update `docs/TODO.md` on phase completion | P1 | ☑ | Khaled | Table marked ☑ (DOC-01) |
| 06-05 **GAP CLOSURE** — bind the mutual audit to local turn truth; make a caught mismatch durable | P0 | ☑ | Khaled | Turn-skew can no longer convert a forgery into a "trailing commit" nor empty the rule-36 coverage set; regression test with disagreeing observed dicts still mismatches; caught mismatch yields a corrected `game_over` + non-zero exit (SEC-05/08) |
| 06-06 **GAP CLOSURE** — contain a peer `ToolError`; validate the inbound `sender` | P1 | ☑ | Khaled | A peer fault ends the game on the terminal path (so the audit still publishes our nonces, rule 36) instead of killing the process; a spoofed `sender` is rejected and never enqueued, handshake exempt by design (SEC-05/08) |

---

## Phase 7 — Reporting and Visualization Shell  *(Milestone M7)*

Gate: summary mailed; GUI displays state (local truth); replay shows `Verified OK`.
**11 of 12 plans executed. Gate PARTIALLY met and the phase is NOT verified — no
`07-VERIFICATION.md` exists; `/gsd:verify-work 7` has never run.**
[GATE-7-MEASUREMENT.md](phases/phase-7/GATE-7-MEASUREMENT.md): **criterion 2 PASS**
(7 modules scanned, 0 local-truth violations, both seats' published snapshots free of
`cop`/`thief`/`barriers`), **criterion 3 PASS** (one real game, all three replay verdicts shown
with both sources deleted first), **criterion 1 dry-run PASS + live PENDING** — both shipped
`reporting.json` files still read `dry_run` and `measure_gate7.py` clears the Gmail credential
environment variables at import, so nothing here can have transmitted. The five rows below are
the ROADMAP's coarse groups, not the twelve plans; the plan-level record is
[docs/phases/phase-7/TODO.md](phases/phase-7/TODO.md).

| Task | Pri | Status | Owner | Definition of Done |
|------|-----|--------|-------|--------------------|
| 07-01 Gmail send-only + gatekeeper (quota/token-bucket/DOS) | P0 | ☑ | Khaled | Built and gate-measured in dry run: 429 backoff ladder matches config, overflow queues then drains, send-only scope enforced at 2 guard call sites (plans 07-01/07-02/07-04). **Live scope never exercised** — 07-10 (REPORT-02/03/04) |
| 07-02 Four JSON artifacts + auto end-game report + tokens | P0 | ◐ | Khaled | `config_`, `log_`, `result_` written by a real game; JSON **attached** (`application/json`), body carries no report content; both token totals present. **`declaration_` has ZERO production callers** — 08-04 wires it; the live send is 07-10 (REPORT-01/05/06/07) |
| 07-03 Local-truth live GUI + verifying replay viewer | P0 | ☑ | Khaled | Both built (plans 07-06/07-08) and both gate-measured PASS; `check_local_truth.sh` is a CI job and its empty-scan control exits 2 (REPORT-08/09) |
| 07-04 Write `docs/PRD_gatekeeper.md` | P1 | ☑ | Khaled | Committed in 07-09; every number sourced to a file and line, and the two with no book source (OQ-1, OQ-2) named rather than invented (DOC-02) |
| 07-99 Update `docs/TODO.md` on phase completion | P1 | ◐ | Khaled | This section reconciled by 08-02; **rolls to ☑ only when 07-10 lands the live send and `07-VERIFICATION.md` is written** (DOC-01) |

---

## Phase 8 — Submission and League Operations  *(Milestone M8)*

Gate: two cross-linked public repos; ≥2 scored league games played and reported.
**In progress — 2 of 14 plans executed (08-01, 08-02) as of 2026-08-17.** The four rows below
are the ROADMAP's deliverable **groups**; §17 is wider than they are, so the phase needs fourteen
plans and the row IDs are **not** 1:1 with plan IDs. The plan-level record is
[docs/phases/phase-8/TODO.md](phases/phase-8/TODO.md); the live §17 gap register is
[docs/SUBMISSION-CHECKLIST.md](SUBMISSION-CHECKLIST.md). Three of the four groups are structurally
**human-completed** — Claude does not create public repositories, push tags, mail the lecturer,
play league games or fill submission forms.

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
| `uv run ruff check` → 0 violations | P0 | ☑ | Khaled | **0 violations** at HEAD; a CI job since Phase 1 (QUAL-09) |
| `uv run pytest --cov` ≥ 85% | P0 | ☑ | Khaled | **2174 passed / 0 failed, coverage 97.37%** against a `fail_under = 85` floor; a CI job (QUAL-10) |
| Every source/test file ≤ 150 lines | P0 | ☑ | Khaled | **Hard-enforced**: `scripts/check_line_limit.sh` via pre-commit hook (`core.hooksPath=scripts/hooks`) + CI (`.github/workflows/quality-gate.yml`); never `--no-verify` (QUAL-08) |
| Build/refresh graphify graph (Phase 3+) | P1 | ◐ | Khaled | `.planning/graphs/GRAPH_REPORT.md` refreshed through 07-09 (10473 nodes / 18679 edges / 597 communities); Phase 8's refresh is task 08-96, owned by plan 08-11 |
| 0 hardcoded values / 0 secrets | P0 | ◐ | Khaled | Secrets: **886 tracked text files scanned, 0 provider-shape hits**, both scanner controls firing (audit row G4-02). Hardcoded values: Table 5 marks that row `Code review` and the audit prints it **UNJUDGED** rather than claiming a pass no script earned (QUAL-11/12) |
| SDK layer + single gatekeeper + no duplication | P1 | ◐ | Khaled | SDK layer (11 modules) and the one gatekeeper reused as two instances are both audit-PASS; "no duplication" is a Table-5 `Code review` row and stays **UNJUDGED** (QUAL-01/02/03) |
| TDD + versioning 1.00 | P1 | ◐ | Khaled | `version.py` reads `1.00`, but `pyproject.toml` reads `1.00.0` — audit row **T5-06 GAP**, and D-79 derives the tag name from the reconciled value (08-11). TDD is a Table-5 `Work process` row: **UNJUDGED** (QUAL-06/07) |
| Prompt-engineering log maintained (§8.3) | P2 | ☑ | Khaled | `docs/PROMPT_LOG.md` — **199 non-blank lines**, audit row **G1-14 PASS** (08-09). Part A covers the two prompts the agent sends, with R1 a MEASURED revision (1 third-person hint in the 10 before `50ac2fe`, 0 in the 69 after, from the tracked phase-5 wire logs); Part B covers how the codebase was prompted, including what did not work |

---

## Per-phase documentation triplets (`docs/phases/phase-<N>/`)

Created at `plan-phase`, checked at `verify-work` — see the *Per-phase documentation triplet*
standing rule in [CLAUDE.md](../CLAUDE.md). A phase is not verified until its row is all ☑.

| Phase | PRD.md | PLAN.md | TODO.md | All TODOs ☑ |
|-------|--------|---------|---------|-------------|
| 1 Base Logic | ☑ | ☑ | ☑ | ☑ — closed 2026-08-17 by 08-02 |
| 2 FastMCP Infrastructure | ☑ | ☑ | ☑ | ☑ |
| 3 Blind Strategy (matrix mover) | ☑ | ☑ | ☑ | ☑ |
| 4 Language & Scent | ☑ | ☑ | ☑ | ☐ — phase verdict `human_needed`, live GATE-4 run outstanding |
| 5 Cloud Tunneling | ☑ | ☑ | ☑ | ☑ — GATE-5 MET, both §10.4 criteria PASS |
| 6 Security & Crypto | ☑ | ☑ | ☑ | ☑ |
| 7 Reporting Shell | ☑ | ☑ | ☑ | ☐ — 11/12 plans; no `07-VERIFICATION.md` exists |
| 8 Submission & League | ☑ | ☑ | ☑ | ☐ — 2/14 plans executed |

---
*Keep this file updated with progress (§2.5 step 6). Each `0N-99` task rolls its phase to ☑.*
*Reconciled project-wide 2026-08-17 by plan 08-02 — from `NN-VERIFICATION.md` and
`GATE-N-MEASUREMENT.md`, never from a tracker's own banner. Phases 4, 7 and 8 are shown
**incomplete**, because that is what their artifacts say.*
