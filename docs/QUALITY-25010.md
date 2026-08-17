# ISO/IEC 25010 — the eight characteristics, mapped to evidence in this repository

**Version:** 1.00 · **Status:** approved · **Updated:** 2026-08-17 · **Plan:** 08-07
**Covers:** §17 group 6 "ISO/IEC 25010 compliance" and §13 · **Related:**
[ARCHITECTURE.md](ARCHITECTURE.md), [SEGAL_GUIDELINES.md](SEGAL_GUIDELINES.md),
[SUBMISSION-CHECKLIST.md](SUBMISSION-CHECKLIST.md)

> **Naming the eight characteristics is not the requirement; mapping each one is.**
> Before 08-07 the entire repository contained **one line** on ISO/IEC 25010,
> `docs/PRD.md:94`, against an explicitly named §17 item.
>
> Each section below points at a **file, a test or a config key** — never at an adjective.
> `tests/unit/test_quality_docs_contract.py` parses the eight names out of
> `docs/SEGAL_GUIDELINES.md` §13 (they are not typed into the test), requires a section
> headed by each, requires that section to cite at least one repository path, and fails
> when any path this document names is not in `git ls-files`. That last rule is why a
> backticked path here is a claim about the tree as it stands **now**.

**Honest scope.** This is a self-assessment of engineering evidence, and it deliberately
carries no score. Where a characteristic is only partly evidenced, the gap is written into
its own section rather than smoothed over — mail has **never** been delivered, phase 4 is
`human_needed`, phases 7 and 8 have no verification pass, and **no league game has been
played**.

---

## Functional suitability — does it do what the book says, and is that measured?

| Sub-characteristic | Evidence |
|---|---|
| Functional completeness | requirement ledger `.planning/REQUIREMENTS.md`, reconciled in one pass by 08-02 and re-checked by `scripts/check_requirements_ledger.py` |
| Functional correctness | the six terminal predicates live in one module, `src/pursuit/sdk/terminal.py`, evaluated in the order `docs/phases/phase-3/RULES-RESOLUTION.md` §3 fixes; the joint turn is applied in exactly one place, `src/pursuit/sdk/resolve.py` |
| Functional appropriateness | movement is the book's orthogonal set only — `src/pursuit/sdk/actions.py` can never emit a diagonal, because a diagonal is a technical loss under rules 13/14 |

Measured, not asserted: `tests/integration/test_game_loop.py` and
`tests/integration/test_turn_lifecycle.py` drive whole games, and every phase carries a
`GATE-N-MEASUREMENT.md` under `docs/phases`. The numbers themselves are never invented —
each config value cites its source, e.g. the `_sources` block in
`config/police/reporting.json` names a `docs/PARAMETERS.md` row for every numeric leaf.

**Known limit:** `docs/phases/phase-4/GATE-4-MEASUREMENT.md` records that the *responder*
side was never live-measured after 05-06 changed responder hint composition, so LANG-01 and
LANG-06 stay unticked.

## Performance efficiency — time, resources, and a hard ceiling on external calls

| Sub-characteristic | Evidence |
|---|---|
| Time behaviour | one response deadline and one retry ladder, `src/pursuit/network/deadline.py`, with `response_timeout` / `retry_count` / `backoff_seconds` read from `config/police/network.json` — never a literal |
| Resource utilisation | the token budget, `src/pursuit/services/llm/budget.py`, and the token bucket, `src/pursuit/services/llm/bucket.py` |
| Capacity | the single API gatekeeper, `src/pursuit/services/llm/gatekeeper.py`, is the one door every external call passes; on overflow it **queues and refuses, never crashes** |

The mail path runs a **second instance of the same gatekeeper class**, configured from
`config/police/reporting.json`, rather than a second implementation — which is why
`tests/unit/test_gatekeeper_llm_unchanged.py` exists: it pins that adding the mail instance
changed nothing about the LLM one. Ordering is pinned separately by
`tests/unit/test_gatekeeper_order.py`.

**Known limit:** no latency budget is defined for a league turn; §10.4 sets none, so none
is invented here.

## Compatibility — two independently written agents must interoperate

| Sub-characteristic | Evidence |
|---|---|
| Co-existence | each peer is one process with its own port and its own config directory; `src/pursuit/network/peer_runtime.py` holds zero module-level state, so two agents can share a machine |
| Interoperability | the MCP tool surface, `src/pursuit/network/tools.py`, and the handshake, `src/pursuit/network/handshake.py`; config identity is compared as a digest by `src/pursuit/network/config_hash.py` |

The hard interoperability case is an opponent we do not control. `src/pursuit/security/step0_sign.py`
accepts a **digest-only** peer — a team whose implementation publishes no declaration
content still agrees, logged as digest-only — while a declaration mutated after its digest
was computed aborts before move 1. `tests/integration/test_step0_and_audit_tamper.py` holds
both halves.

Proven against a genuinely foreign machine: `docs/phases/phase-5/GATE-5-MEASUREMENT.md`
attempt 4, two complete games across two networks with agreeing verdicts on both sides.
**That was our own second machine, not another team's agent** — the cross-team case is
08-13's, and it has not happened.

## Usability — an operator who is not the author must be able to run it

| Sub-characteristic | Evidence |
|---|---|
| Learnability | `docs/ARCHITECTURE.md` §5.1 deployment instructions, and the operator runbook `docs/phases/phase-5/REMOTE-ROUND-RUNBOOK.md` |
| Operability | `src/pursuit/main.py` accepts `--check-config`, a preflight that loads every config file and reports before a game starts |
| User error protection | `src/pursuit/shared/tunnel_config.py::require_env` refuses a missing environment variable **by name, at startup**, instead of failing cryptically mid-connect |
| User interface aesthetics | two Tk applications, `src/pursuit/gui/live_app.py` and `src/pursuit/gui/replay_app.py` |
| Accessibility | not assessed — no accessibility requirement exists in either binding document, and inventing one here would be a claim without a source |

`--refresh-ms` and `--step-ms` are **required with no default** on purpose: no document in
this project states a UI refresh interval, so the operator states it and the repository
states none.

**Known limit:** `docs/SUBMISSION-CHECKLIST.md` row G5-04 — there are still **no
screenshots** of the running system. They come from 07-10, which has not run.

## Reliability — a peer, a tunnel or a provider can fail without taking the game with it

| Sub-characteristic | Evidence |
|---|---|
| Maturity | 2 366 tests at 97.44 % coverage against a `fail_under = 85` gate |
| Availability | the freeze watchdog, `src/pursuit/network/watchdog.py`, 60 s from `config/police/network.json`, tested by `tests/unit/test_watchdog.py` and `tests/unit/test_turn_loop_watchdog.py` |
| Fault tolerance | the bounded tunnel repair, `src/pursuit/network/tunnel_manager.py::ensure_connected`, driven by the watch task in `src/pursuit/network/tunnel_wiring.py`; a raising probe is contained as one spent attempt, never a crash |
| Recoverability | durable writes with temp-file rotation, `src/pursuit/shared/durable_write.py`, so a reader that arrives mid-write gets the previous frame instead of a crash |

Degradation is designed rather than hoped for: a provider failure returns an `LlmFailure`
value, never raises past `src/pursuit/services/llm/provider.py`'s contract, and
`tests/integration/test_llm_degradation.py` drives the whole pipeline through it.

**Known limit, measured and written down:** the tunnel repair path **has never fired in a
live game**. `docs/phases/phase-5/GATE-5-MEASUREMENT.md` says so in its own words —
attempt 4 is evidence that a *healthy* tunnel completes a round, not that a dropped one is
repaired.

## Security — the rules that carry an absolute sanction

| Sub-characteristic | Evidence |
|---|---|
| Confidentiality | the shared-secret ASGI middleware, `src/pursuit/network/secret_guard.py`, rejects with 403 **before** any MCP session or tool body runs; the nonce stays local until game end, `src/pursuit/security/ledger.py` |
| Integrity | SHA-256 over canonical JSON, `src/pursuit/security/commit_pack.py`, and the mutual final audit, `src/pursuit/security/audit.py` |
| Non-repudiation | the durable per-turn nonce ledger plus the signed Step-0 declaration, `src/pursuit/security/step0_collect.py`, carrying the exact commit hash the game ran on (rule 53) |
| Accountability | the append-only event log, `src/pursuit/services/reporting/artifact_log.py`, replayable and re-verifiable from the artifact alone by `src/pursuit/services/reporting/replay_verify.py` |
| Authenticity | HMAC-SHA256 over the declaration when a shared secret exists, `src/pursuit/security/step0_sign.py`; an absent secret produces an explicit `signed: false`, never a silent pass |

No credential is in the tree. `scripts/submission_scan.py` scans the **tracked** set — 886
text files, 0 provider-shape hits — and carries a positive control for each of its two
pattern classes, assembled at runtime so the scanner itself holds no credential shape. The
exemptions it honours are listed with a reason each in `docs/credential-scan-allowlist.json`,
and an entry whose file no longer matches is **stale and fails the row**. The ignore rules
are held to CLAUDE.md's own wording by `tests/unit/test_publication_ignore_rules.py`.
Every secret is an environment-variable **name** in config — see `config/police/tunnel.json`,
which carries a provider, a header name and three variable names, and not one value.

The audit joins the peer's claims to **this side's own** turn numbers, never the peer's —
one relabelled integer used to disable two defences at once. The attack and the fix are
written out in `docs/PRD_commit_reveal.md` §2.6.1.

## Maintainability — the properties that are enforced rather than encouraged

| Sub-characteristic | Evidence |
|---|---|
| Modularity | 195 modules under `src/pursuit`, every one ≤ 150 code lines |
| Reusability | one canonicalisation and one digest comparison for the whole project, `src/pursuit/network/config_hash.py`, reused by the Phase-4 scent digest and the Phase-6 commit hash |
| Analysability | a module docstring on all 195 `src/pursuit` modules, and a per-mechanism PRD for every package — the register is `docs/mechanism-prd-map.json`, walked from `git ls-files` so a new package becomes a gap by itself |
| Modifiability | the extension seams are documented and tested — `docs/EXTENSION-POINTS.md` |
| Testability | the whole suite is offline; every external service is injected, e.g. every pyngrok call in `src/pursuit/network/tunnel_manager.py` is a constructor default a test replaces |

Enforced twice, not encouraged once: `scripts/check_line_limit.sh` runs as a pre-commit
hook **and** as a CI job, `ruff check` reports 0, and `scripts/check_submission.py`
re-derives all 86 §17 / Table-5 rows on every run with exit 2 reserved for an evidence set
that judged nothing. Package exports are derived from the tree by
`tests/unit/test_package_exports.py`, so `__all__` cannot decay into decoration.

## Portability — one command, two operating systems, no machine-specific value

| Sub-characteristic | Evidence |
|---|---|
| Adaptability | every endpoint is config or environment, `src/pursuit/shared/network_config.py`; no host, port or URL is a literal in source |
| Installability | `uv sync` against a committed lockfile; `uv` is the only package manager, and there is no `requirements.txt` |
| Replaceability | the tunnel provider is named in `config/police/tunnel.json`, and the ngrok-unavailable fallback is written out end to end in `docs/phases/phase-5/LOCALTONET-FALLBACK.md` |

The remote round ran between two different Windows machines on two different networks with
no code change on either side — only environment variables differed.

**Known limit:** the suite has only ever been run on Windows and on the CI runner
configured in `.github/workflows/quality-gate.yml`. macOS is untested, and no claim is made
about it. `docs/phases/phase-5/LOCALTONET-FALLBACK.md` is **documentation only** — no
Localtonet code path exists anywhere, which that file states in its own first paragraph.

---

## What this mapping is not

- It is **not a score.** The self-assessment number is SUB-11's, restricted by rule 55 to
  code quality, drafted with the field blank in 08-11 and written by a human in 08-14.
- It is **not a certification.** Every row above points at something a reader can run or
  open; nothing above was measured by this document.
- It does not cover league results, which rule 55 excludes from self-assessment and which
  do not exist yet in any case.
