---
phase: 07-reporting-and-visualization-shell
plan: "09"
subsystem: testing
tags: [gate-measurement, rule-38, gmail, oauth, local-truth, replay, gatekeeper, ci, graphify]

# Dependency graph
requires:
  - phase: 07-reporting-and-visualization-shell
    provides: "the mail chain (07-01/07-04), the artifact spine (07-02/07-05/07-07), the local-truth firewall (07-03/07-11), the live GUI (07-06) and the replay viewer (07-08) -- this plan measures all of them and builds none of them"
provides:
  - "scripts/measure_gate7.py + six siblings -- one command, zero credentials, an honest per-criterion verdict for book Sec10.4 milestone 7"
  - "docs/phases/phase-7/GATE-7-MEASUREMENT.md -- criteria 2 and 3 MEASURED PASS, criterion 1 dry-run PASS + live PENDING with the four items 07-10 must attach"
  - "docs/phases/phase-7/gate7_measurement_evidence.json -- every claim above as a re-openable field"
  - "docs/PRD_gatekeeper.md -- ROADMAP row 07-04: every outgoing-call limit in the project with its file-and-line source"
  - "docs/phases/phase-7/OAUTH-RUNBOOK.md -- the operator procedure 07-10 follows, human-followable start to finish"
  - "D7-18 closed: all six durable_write_json bindings guarded against the shipped config/ tree"
  - "D7-19 half-closed: game_artifacts/ debris halved by two provably-safe ignore patterns"
  - "check_no_llm_in_strategy.sh wired into quality-gate.yml (absent since 03-10)"
affects: [07-10, phase-8, submission, league-operations]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A gate criterion whose live half cannot be measured offline is reported as TWO named fields, never collapsed into one boolean"
    - "Every gate script is proven to FAIL by mutating the real subject in src/ and reverting"
    - "An empty evidence set exits 2 (EMPTY_EVIDENCE), never 0 -- 07-03's convention extended to counts, not just scans"
    - "One real game feeds two criteria, joined by game_uid in the evidence"

key-files:
  created:
    - scripts/measure_gate7.py
    - scripts/gate7_common.py
    - scripts/gate7_mail.py
    - scripts/gate7_mail_live.py
    - scripts/gate7_localtruth.py
    - scripts/gate7_replay.py
    - scripts/gate7_report.py
    - docs/PRD_gatekeeper.md
    - docs/phases/phase-7/GATE-7-MEASUREMENT.md
    - docs/phases/phase-7/OAUTH-RUNBOOK.md
    - docs/phases/phase-7/gate7_measurement_evidence.json
    - tests/unit/test_shipped_config_guard.py
    - tests/unit/test_artifact_dir_hygiene.py
    - tests/unit/gitignore_probe.py
  modified:
    - tests/_shipped_config_guard.py
    - tests/conftest.py
    - tests/unit/test_gmail_credentials.py
    - .github/workflows/quality-gate.yml
    - .gitignore
    - game_artifacts/README.md
    - .planning/graphs/GRAPH_REPORT.md
    - .planning/phases/07-reporting-and-visualization-shell/deferred-items.md
    - docs/phases/phase-7/TODO.md

key-decisions:
  - "Criterion 1 is reported as dry_run PASS + live PENDING in two named fields; the criterion-level verdict is the STRING joining them, so a grep for '\"verdict\": \"PASS\"' cannot match it"
  - "D7-17 is NOT decidable from the book and is routed to 07-10 / Phase 8 with three costed options -- PARAMETERS.md:86 (one scoring game per opponent) pulls against :72/:168 (aggregate across sub-games), and game_id is peer-negotiated (D-61), so redefining it is a protocol decision"
  - "D7-18 closed by guarding all six durable_write_json bindings, with the binder list re-derived by AST so a seventh writer fails a test"
  - "D7-19 closed only where it is provably safe: *.eml and *.prev.json under game_artifacts/ are ignored (neither is ever one of rule 50's four artifacts); the judgement half stays 07-10's"
  - "check_no_llm_in_strategy.sh wired into CI enforcing CLAUDE.md's stricter reading, with docs/RULES.md:61's 'RECOMMENDED, no mandated sanction' recorded rather than overstated"
  - "OQ-6 intervals used by the measurement are stated in scripts/ (500 ms, 400 ms) and NOT written into src/, which still has no default"

patterns-established:
  - "Mutation-probe discipline for gate scripts: break each criterion's real subject in src/, run the whole gate, record the FAIL, revert, verify git diff clean"
  - "Anti-vacuity at the report layer: every criterion's checks include a non-zero COUNT, and the exit code distinguishes FAILED (1) from EMPTY_EVIDENCE (2)"
  - "A PENDING gate row states what is proven offline, what is not, and the exact evidence that would flip it"

# Metrics
duration: 165min
completed: 2026-08-17
---

# Phase 7 Plan 09: GATE-7 measurement, the gatekeeper PRD and the OAuth runbook Summary

**Sec10.4 criteria 2 and 3 measured PASS on one real game with zero credentials, criterion 1 split honestly into a measured dry-run half and a PENDING live half, and the gate script itself proven to fail under five mutations of the things it measures — plus one defect it found in its own counter snapshot.**

## Performance

- **Duration:** ~165 min
- **Tasks:** 4 planned + 2 unplanned (a self-audit fix and the three routed findings)
- **Files created:** 14 · **Files modified:** 9

## Accomplishments

- `scripts/measure_gate7.py` + six siblings: one command, zero credentials, zero environment variables, exit 0, idempotent, writing one evidence JSON and a per-criterion summary.
- **Criterion 2 PASS** — 7 gui modules scanned / 0 violations, the gate's own empty-scan control at exit 2 in both forms, both seats' published snapshots free of `cop`/`thief`/`barriers`, both `live_app --once` launches exit 0 as subprocesses.
- **Criterion 3 PASS** — one real game (`gate7measure`, `capture` on both seats), both sources deleted before any verdict: `Verified OK` 5/5, a resealed tamper `FAILED -- turn 4: re-hash does not match h_commit` at 4/5, and a zero-turn artifact reading `Nothing to verify`.
- **Criterion 1 dry-run PASS, live PENDING** — the MIME shape re-parsed from rendered bytes, the attachment, the rule-30 scope gate at both call sites and its ordering ahead of any credential read, the 429/429/200 ladder at `[30, 30]`, and queue-and-drain. What is *not* proven — a delivered message — is stated as such with the four items 07-10 must attach.
- `docs/PRD_gatekeeper.md` — every outgoing-call limit in the project on one page, each with the file and line that states it, and the two with no book source named as such.
- `docs/phases/phase-7/OAUTH-RUNBOOK.md` — numbered, followable by someone who did not write it, stating plainly that Claude must not enter credentials and must not click consent.
- Three deferred findings resolved or routed with reasoning recorded, and a CI gate that had been missing since 03-10 wired in.

## Task Commits

1. **Task 1: measure_gate7 + siblings** — `08705d9` (test)
2. **Task 2: docs/PRD_gatekeeper.md** — `ba72c8a` (docs)
3. **Self-audit fix: the one-counter defect** — `9e044d5` (fix)
4. **Routed findings: D7-18, D7-19, CI wiring** — `96495d4` (test)
5. **Task 3: the gate record and the runbook** — `88d21fb` (docs)
6. **Task 4: refresh the knowledge graph (07-96)** — `bb8b1da` (chore)

## Verification — run in this session

| Gate | Baseline | Measured |
|---|---|---|
| `uv run ruff check .` | 0 | **0 violations** |
| `uv run pytest tests/ --cov` | 2130 passed / 0 failed, 97.37% | **2153 passed / 0 failed, 97.37%** |
| `bash scripts/check_line_limit.sh` | exit 0 | **exit 0**, plus all 10 new `.py` files checked EXPLICITLY BY PATH (`scripts/` is not enumerated by the no-arg form) |
| `check_local_truth.py` | OK, 7 modules | **`OK: 7 module(s) scanned`, exit 0** |
| `check_no_llm_in_strategy.py` | OK | **OK**, and now also a CI job |
| `scripts/dev_launch.py` | exit 0 | **exit 0**, game `6694ec24875b4208`, 11 `"matched":true` per seat, one `audit_verdict` and one `game_over` per seat, **zero** `technical_win`, **zero** `watchdog_incident` |
| `scripts/measure_gate7.py` | — | **exit 0**, run twice, summary byte-identical |

**Rule-38 counters, all four numbers.** The full suite moved police **1921 → 1921** and thief **1914 → 1914** (delta **0/0**). One real game moved police **1921 → 1922** and thief **1914 → 1915** (delta **1/1**). The gate script itself reads both counters before and after and reports `unchanged_by_this_measurement: true` — it plays a real game, so it says so with numbers rather than assuming.

**Secret scan** over every new doc, script and the evidence JSON: no `AIza`/`ya29.`/`-----BEGIN`/`client_secret`/`refresh_token` pattern. `git diff config/` empty; both `reporting.json` files still read `dry_run`. Every new `.py` confirmed NOT ignored by git (D7-10's guard).

## The five mutation probes — does this gate measure anything?

Each broke the criterion's real subject in `src/`, ran the whole gate, and was reverted; `git diff` clean after every one.

| # | Mutation | Result |
|---|---|---|
| 1a | `message.ATTACHMENT_SUBTYPE` `json` → `octet-stream` | c1 **DRY_RUN FAIL**, exit 1; evidence recorded `application/octet-stream` |
| 1b | `require_send_only_scope` weakened to *"contains gmail.send"* | c1 **DRY_RUN FAIL**, exit 1; `extra_scope_rejected: false`, `scope_checked_before_any_credential_is_read: false` |
| 2 | `from pursuit.shared.state import GameState` planted in `gui/widgets.py` | c2 **FAIL**, exit 1; `violation_count: 2` |
| 3 | the non-zero-committed guard removed from `verdict_from` | c3 **FAIL**, exit 1; **the EMPTY artifact read `Verified OK` at 0/0** |
| 4 | the per-turn re-hash removed from `check_turn` | c3 **FAIL**, exit 1; **the TAMPERED artifact read `Verified OK` at 5/5** |

Plus report-layer probes on real evidence: zeroing `modules_scanned` → exit **2** (`EMPTY_EVIDENCE`, matching 07-03's convention); zeroing `verified_ok.committed`, the attachment count, the ladder attempts or the guard call sites → **FAIL** in every case. And two more outside the gate: probe 9 (D7-18) and probe 10 (the CI gate), below.

## Decisions Made

- **Criterion 1 never reads as a blanket PASS.** Two named fields, and the criterion-level `verdict` is the string joining them, so `grep '"verdict": "PASS"'` over the evidence returns criteria 2 and 3 and cannot return criterion 1. `GATE-5-MEASUREMENT.md`'s retained PENDING record is the precedent.
- **One real game feeds criteria 2 and 3**, joined by `game_uid` in the evidence — cheaper than two games and more honest, because both criteria then answer for the same run.
- **No `gui` import at module scope anywhere in these scripts.** Both GUI entry points are driven as subprocesses with their exit codes recorded: `tkinter.Tk()` raises on a machine with no display, and one criterion's environment must not be able to fail the whole gate.
- **The OQ-6 intervals this measurement used (500 ms, 400 ms) live in `scripts/`, not `src/`.** The repository still states no UI interval; the operator does, and this script is an operator.
- **Two `PRD_gatekeeper.md` citations were wrong when first written and are corrected, not left** — `token_budget_per_series` is `PARAMETERS.md:83` (`:81` is the diversity reward), and the gatekeeper/bucket tests live under `tests/unit/services/`.

## The three routed findings

**D7-17 — ROUTED, not decided.** `game_id` is minted per GAME while `PARAMETERS.md:157-159` reads it as the SERIES id. Examined against the documents rather than shrugged at: `PARAMETERS.md:86` (rule 52, *"one scoring game only"* per opponent) means a scored series contains exactly one scoring game, which is what production produces and is **correct, understating nothing**; `:72` (Table 17 row 5's tie rule) and `:168` bind only if warm-up games are meant to share the scored game's `game_id`, and **neither document says**. `game_id` is peer-negotiated at handshake (D-61), so redefining it is a protocol decision, not an artifact-writer one — 07-07's refusal to invent an id scheme stands. Three options costed in the gate document, plus the cheapest correct move: **ask the lecturer**.

**D7-18 — CLOSED.** `install()` now wraps all six bindings of `durable_write_json` (five importers plus the defining module), per module because `from ... import` copies the function object. `tests/unit/test_shipped_config_guard.py` asserts two independent things — an AST scan that re-derives the binder list from `src/`, and a behavioural case per binding paired with a `tmp_path` control. **Probe 9** restored the pre-07-09 guard: five of six bindings did not raise, and the write physically landed — `config/police/guard_probe.json` and `guard_probe.prev.json` appeared in the SHIPPED config tree. Debris removed, probe reverted, `git status --short config/` empty.

**D7-19 — half-closed, and the half is measured.** Only patterns that can never be one of rule 50's four artifacts are ignored: `game_artifacts/**/*.eml` and `**/*.prev.json`. Measured on this session's `dev_launch`: 8 files on disk, **4 untracked** — exactly halved, and the four are the two `log_` and two `result_` artifacts a sweep *should* see. `tests/unit/test_artifact_dir_hygiene.py` asserts both halves and both were probed (remove the patterns → the ignore cases fail; ignore the directory wholesale → the not-ignored cases fail). The judgement half is written into `game_artifacts/README.md` and the runbook, and stays 07-10's.

**`check_no_llm_in_strategy.sh` — WIRED IN.** Its own job in `quality-gate.yml`, shaped like `local-truth`. The comment records that the documents disagree: `docs/RULES.md:61` marks rule 25 **RECOMMENDED** with *"No mandated sanction"*, CLAUDE.md's binding list is stricter, and the job enforces the stricter reading per `SEGAL_GUIDELINES.md:182`. An earlier draft of that comment called rule 25 a disqualification flatly and was corrected. **Probe 10:** `from pursuit.services.llm import Gatekeeper` planted in `strategy/naive.py` → exit 1 naming STRAT-07; reverted → exit 0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The gate watched ONE games-played counter while claiming both**
- **Found during:** Task 3, reading the first evidence file rather than by a test
- **Issue:** `counter_snapshot()` keyed on `path.name`, so `config/police/games_played.json` and `config/thief/games_played.json` collapsed onto the single key `games_played.json`; only the last written (thief's) survived, and the evidence reported `unchanged_by_this_measurement: true` over a dict watching half of what it named — on the one rule-38 surface in this phase
- **Fix:** keyed on `<role>/<filename>`; `gate7_report.exit_code` now returns `EMPTY_EVIDENCE` for a snapshot under two entries
- **Verification:** probe 6 — reduce the snapshot to one file, exit 2. Post-fix: police 1921/1921, thief 1914/1914, both keys present
- **Committed in:** `9e044d5`

**2. [Rule 2 - Missing Critical] The shipped-config guard covered one writer, not the rule (D7-18)**
- **Found during:** the orchestrator's routed findings
- **Issue:** the session-autouse guard patched `step0_collect.durable_write_json` alone; the rule it enforces is about the *tree*, and rule 38's sanction is absolute disqualification
- **Fix:** all six bindings guarded; the binder list re-derived by AST in a test; a behavioural case per binding
- **Verification:** probe 9 — the pre-07-09 guard lets five of six writes LAND in `config/police/`
- **Committed in:** `96495d4`

**3. [Rule 2 - Missing Critical] The rule-25 CI gate had never been wired in**
- **Found during:** the orchestrator's routed findings (recorded by 07-03, unfixed since 03-10)
- **Issue:** `check_no_llm_in_strategy.sh` existed and was run by hand in every plan's verification block, but no CI job referenced it — while Phase 7 added LLM-adjacent surface area
- **Fix:** a `no-llm-in-strategy` job in `quality-gate.yml`, with the documents' disagreement about the sanction recorded honestly
- **Verification:** probe 10 — a planted forbidden import gives exit 1; reverted, exit 0
- **Committed in:** `96495d4`

**4. [Rule 3 - Blocking] The gate's own body check compared raw CRLF against LF**
- **Found during:** Task 1's first run
- **Issue:** criterion 1 read `is_the_fixed_boilerplate: false` — `render_message` renders under `email.policy.SMTP` (CRLF) *deliberately*, so the `.eml` on disk matches the wire; the gate would have reported a FAIL for the encoding being CORRECT
- **Fix:** normalise CRLF before comparing, and record `line_ending_is_crlf` as its own measured field — the gate now measures *more*, not less. `tests/unit/test_mail_message.py:111` normalises the same way
- **Committed in:** `08705d9`

**5. [Rule 2 - Missing Critical] `_git_ignored` was about to become a second copy**
- **Found during:** the D7-19 work
- **Issue:** `test_gmail_credentials.py` owned the only `git check-ignore` helper and was at 137/150 code lines
- **Fix:** extracted to `tests/unit/gitignore_probe.py` (CLAUDE.md "extract at 2+ copies"); both callers rewired
- **Committed in:** `96495d4`

---

**Total deviations:** 5 auto-fixed (1 bug, 3 missing-critical, 1 blocking). One additional scope extension was the orchestrator's explicit instruction, not a self-granted one: resolving or routing D7-17/D7-18/D7-19 and the CI wiring, which the plan's own non-goals would otherwise have deferred.

**Impact on plan:** the plan's "measure, do not fix" rule was honoured for everything the *gate* measures — no production behaviour was edited to make a criterion pass, and the one production-adjacent correction (the CRLF comparison) was to the measurement, not to the subject. The routed findings touch test infrastructure, `.gitignore`, CI and documentation only.

## Issues Encountered

- **`git checkout --` on a probe wiped an unrelated edit in the same file.** Reverting probe 9 with `git checkout -- tests/_shipped_config_guard.py` also reverted that session's D7-18 additions, because they were uncommitted. Re-applied and re-verified; the later probes reverted by inverse edit instead. Worth knowing for the next executor: `git checkout --` reverts the FILE, not the probe.
- **A first read of probe 9 was wrong and is corrected here.** The truncated pytest tail suggested all six bindings failed to raise; the full output showed five did not raise while `step0_collect`'s raised correctly and failed only on a leftover file an earlier unguarded binding had already written. The probe was re-run cleanly to get the accurate record.
- **`GRAPH_REPORT.md` is a community digest, not a node listing.** The plan's verification asked for the phase's modules to "appear in the report"; grepping for `sdk/view_publish` etc. returns 0 because the report summarises communities. Verified by querying the graph instead (`graphify explain`), and the discrepancy recorded rather than papered over.
- **Two things are not byte-identical across gate runs**, both recorded in the gate document: `generated_at`, and the local-truth gate's own two `ERROR:` diagnostics from the empty-scan control, which echo the throwaway temp directory they scanned. The GATE-7 summary block itself is byte-identical, and the replay refusal message's temp path is redacted to `<tmp>` in a field whose name says so — which also keeps a local username out of a file bound for a public repo (rule 49).

## User Setup Required

**Criterion 1's live half needs a human.** See [`docs/phases/phase-7/OAUTH-RUNBOOK.md`](../../../docs/phases/phase-7/OAUTH-RUNBOOK.md): the OAuth client restricted to `gmail.send`, consent completed by a person, one config flipped to `live` and flipped back, one delivered message with the JSON attached, the two README screenshots, and the OQ-5 games-played decision recorded in writing **before** the send. Claude must not enter credentials and must not click consent.

## Next Phase Readiness

- **07-10 is fully specified and unblocked.** Its runbook is written, its PASS criteria are stated before the run, and the exact evidence that flips criterion 1 is enumerated.
- **Nothing in this repository transmits.** Both shipped `reporting.json` files read `dry_run`, `git diff config/` is empty, and the gate script clears both credential environment variables at import.
- **Open for 07-10 / Phase 8:** D7-17 (the series/game id question, three costed options, ask the lecturer), the remaining half of D7-19 (which `game_artifacts/` files are league evidence), and OQ-5 (the games-played value — **human only**, and the files still read 1922 / 1915, both known-wrong).

---
*Phase: 07-reporting-and-visualization-shell*
*Completed: 2026-08-17*

## Self-Check: PASSED

24 claimed paths verified present AND tracked (the SUMMARY itself untracked until the final
commit), none swallowed by `.gitignore` (D7-10's guard). All 6 task commits verified reachable
by hash. Every number in this document comes from a command run in this session. Two claims
were CORRECTED rather than left as first written: `PRD_gatekeeper.md`'s `token_budget_per_series`
citation (`:81` → `:83`) and its test-file paths, and the D7-18 binder count in
`GATE-7-MEASUREMENT.md` (five → six, five importers plus the defining module).
