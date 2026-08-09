---
phase: 06-security-and-cryptography
plan: "04"
subsystem: security
tags: [gate-measurement, prd, commit-reveal, step0, audit, graphify]

# Dependency graph
requires:
  - phase: 06-security-and-cryptography plan 01
    provides: "src/pursuit/security/ (commit_pack, state_record, ledger), security_config.py"
  - phase: 06-security-and-cryptography plan 02
    provides: "the D-58 both-locked Commit-Ack-Reveal wire protocol, barrier-over-the-wire"
  - phase: 06-security-and-cryptography plan 03
    provides: "declare_step0/write_declaration/run_final_audit already wired live into agent_entrypoint.run_agent; the D-67 tamper-harness proofs; the rule-36 audit coverage check"
provides:
  - "scripts/measure_gate6.py + 6 gate6_*.py helper modules: the fully-scriptable, zero-env-var localhost GATE-6 run + tamper harness + Step-0-mismatch live measurement"
  - "docs/phases/phase-6/gate6_measurement_evidence.json: the measured evidence all three GATE-6 criteria's PASS verdicts point at"
  - "docs/phases/phase-6/GATE-6-MEASUREMENT.md: the three Sec10.4 criteria quoted verbatim, each with method/evidence/PASS verdict"
  - "docs/PRD_commit_reveal.md: the per-mechanism PRD for the whole commit-reveal protocol, SEC-01..08 traced"
  - "refreshed .planning/graphs/GRAPH_REPORT.md (06-96): 6510 nodes/11909 edges/408 communities"
affects: [phase-7-reporting-shell]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gate6_*.py helper-module split (measure_gate6.py + common/clean_game/declarations/tamper/step0/report), mirroring the gate4_*/gate5_* precedent -- scripts/ is outside the coverage gate but the 150-code-line house limit is still honored by hand"
    - "the measurement script reuses the SAME real two-peer harness 06-03's own tests already use (tests/integration/test_step0_and_audit.py's _play_to_turn_loop_end/_run_audit_and_merge, imported directly -- the ALREADY-established sibling-test-import precedent test_step0_and_audit_tamper.py itself uses) -- never a second, parallel game-runner"
    - "criterion-3's Step-0-mismatch measurement calls respond_to_handshake directly against a real default_context-built AgentContext, rather than a full two-server FastMCP round trip -- a Step-0 declaration is per-agent (D-62), so forging one side's digest is only detectable from the RECEIVING side's own evaluation, not from the forging side's own outbound perform_handshake return value"

key-files:
  created:
    - scripts/measure_gate6.py
    - scripts/gate6_common.py
    - scripts/gate6_clean_game.py
    - scripts/gate6_declarations.py
    - scripts/gate6_tamper.py
    - scripts/gate6_step0.py
    - scripts/gate6_report.py
    - docs/phases/phase-6/gate6_measurement_evidence.json
    - docs/phases/phase-6/GATE-6-MEASUREMENT.md
    - docs/PRD_commit_reveal.md
    - .planning/phases/06-security-and-cryptography/deferred-items.md
  modified:
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "Reused test_step0_and_audit.py's own _play_to_turn_loop_end/_run_audit_and_merge directly from scripts/ (rather than the plan's stale key_link naming tests/integration/two_peer_game.py's play_two_peer_game, which cannot carry the Step-0 params 06-03 added) -- 06-03-SUMMARY.md's own 'Next Phase Readiness' section explicitly named this as the intended path ('or mirror test_step0_and_audit.py's harness'), and the shipped code is the source of truth per this plan's own instructions, not the plan text's stale wording"
  - "Criterion 3 measured via a direct respond_to_handshake call against a real default_context-built AgentContext rather than a full two-server round trip -- a forged digest is asymmetric (detectable only by the receiving side's own evaluation), so a full bidirectional wire exercise would not have isolated the detection cleanly; documented in gate6_step0.py's own module docstring"
  - "Final-Reveal/Audit's occurrence for criterion 1 is measured via the audit_verdict record's presence, not an envelope-type count -- agent_audit_exchange.py's push_final_reveal/receive_final_reveal (06-03) never themselves call append_event the way COMMIT/ACK/REVEAL's send_and_log/log_received do; logged honestly in GATE-6-MEASUREMENT.md and deferred-items.md rather than silently smoothed over or misrepresented as a FAIL"

patterns-established:
  - "GATE-6 evidence -> GATE-6-MEASUREMENT.md pointer discipline: every PASS claim in the markdown names the exact evidence-JSON field it is drawn from, mirroring GATE-5-MEASUREMENT.md's own table style"

# Metrics
duration: ~90min
completed: 2026-08-09
---

# Phase 6 Plan 4: GATE-6 Measurement + docs/PRD_commit_reveal.md Summary

**scripts/measure_gate6.py proves all three book Sec10.4 milestone-6 criteria with real,
localhost-only, zero-env-var evidence against the shipped config/police + config/thief: all
three PASS, closing Phase 6.**

## Performance

- **Duration:** ~90 min
- **Tasks:** 3
- **Files created:** 11
- **Files modified:** 1 (graph refresh)

## Accomplishments

- **`scripts/measure_gate6.py` runs the whole GATE-6 lifecycle from one command, zero env vars.**
  Split into `gate6_common.py` (bootstrap + shared helpers), `gate6_clean_game.py` +
  `gate6_declarations.py` (criterion 1), `gate6_tamper.py` (criterion 2), `gate6_step0.py`
  (criterion 3), and `gate6_report.py` (verdict assembly + JSON writer) -- each file under the
  150-code-line house limit, mirroring the `gate4_*`/`gate5_*` precedent. Confirmed idempotent
  (rerun twice; the evidence JSON is overwritten in place, no duplicated log directories --
  every game plays inside its own throwaway `tempfile.TemporaryDirectory()`).
- **Criterion 1 (four phases, valid nonce) measured, not asserted.** One clean game through the
  real `config/police`/`config/thief` (reusing 06-03's own two-peer harness,
  `tests/integration/test_step0_and_audit.py`'s `_play_to_turn_loop_end`/`_run_audit_and_merge`
  -- never a second, parallel game-runner) shows commit/ack/reveal counted 5/5/5 both sides,
  zero `"nonce"` occurrences in either wire-mirroring JSONL against 5 nonce-bearing ledger
  records per side, the D-58 both-locked-gate ordering holding with zero violations, both
  declaration files present and predating first move content on both sides, and an honest
  barrier count (1 this run -- a real, non-forced placement; 0 would also have been valid).
- **Criterion 2 (canonical hash, nonce secret, mismatch = technical loss) re-run end to end
  through the script itself.** Both D-67 tamper classes 06-03 already unit/integration-tests are
  driven live here: (a) a corrupted ledger payload fails the re-hash check, `AUDIT_HASH_MISMATCH`
  / `TECHNICAL_LOSS`, caught on both the accusing AND the tampering side's own self-audit
  (symmetric honesty); (b) THE D-67 case -- hash/payload left completely untouched (independently
  re-verified via `commit_pack.verify_reveal` before any corruption), but what the peer actually
  observed played differs -- caught by check 3 alone, proving a hash-only audit would have missed
  the forgery.
- **Criterion 3 (Step-0 verified before move 1) measured live, not just unit-tested.** Two REAL
  `declare_step0`-collected declarations (genuine `git rev-parse HEAD`, `psutil` OS/CPU/RAM,
  best-effort GPU probe), one side's claimed digest forged, evaluated through the real
  `respond_to_handshake` production function against a real `default_context`-built
  `AgentContext`: `HandshakeOutcome.STEP0_MISMATCH` fires, the machine aborts to `State.ERROR`,
  and an explicit `machine.attempt(State.MY_TURN)` call made AFTER the abort confirms move 1 is
  unreachable -- `run_turn_loop` is never even called in this measurement.
- **`docs/PRD_commit_reveal.md` mirrors `docs/PRD_mcp_transport.md`'s house structure exactly**
  (mechanism/scope with the SEC-01..08 requirements table, topology/design, interfaces copied
  verbatim from the 06-01/02/03 SUMMARY files, out-of-scope future-phase extensions, parameters
  traced to `06-PLAN-OUTLINE.md` §2). Every SEC-01..08 ID appears at least once next to the
  section that satisfies it (grep-confirmed).
- **`docs/phases/phase-6/GATE-6-MEASUREMENT.md`** quotes all three §10.4 criteria verbatim in a
  blockquote, one section per criterion with method/run-command/what-a-PASS-looks-like/measured
  result, every PASS claim pointing at a named field in the evidence JSON -- mirroring
  `GATE-5-MEASUREMENT.md`'s own discipline. Two honest findings are documented rather than
  smoothed over: FINAL_REVEAL is not itself logged as a `message_sent`/`message_received`
  envelope record (only `audit_verdict` is, which is what the evidence actually cites), and
  measurement games advance the real `games_played.json` counter (the same behavior 06-03's own
  `pytest` runs already produce).
- **Knowledge graph refreshed (06-96).** `graphify update .` — 6510 nodes / 11909 edges / 408
  communities, built at commit `1de0dcf7`; `graph.html` skipped (6510 nodes exceeds the
  5000-node HTML viz limit, matching the 04-12/05-03 precedent — gitignored regardless). Only the
  committed `GRAPH_REPORT.md` moved (566 lines changed), `git diff --stat` confirms a real,
  non-trivial change.

## Task Commits

Each task was committed atomically:

1. **Task 1: measure_gate6.py — the scriptable localhost run + tamper harness** - `77eafff` (feat)
2. **Task 2: docs/PRD_commit_reveal.md** - `1de0dcf` (docs)
3. **Task 3: GATE-6-MEASUREMENT.md + graph refresh** - `216eec4` (docs)

**Plan metadata:** (this commit, appended after STATE.md update)

## Files Created/Modified

- `scripts/measure_gate6.py` - CLI entrypoint: orchestrates the three criterion measurements, writes the evidence JSON, prints a one-line PASS/FAIL summary
- `scripts/gate6_common.py` - sys.path bootstrap, `load_configs`/`events`/`ledger_path`/`wire_log_text`, clears `ANTHROPIC_API_KEY`
- `scripts/gate6_clean_game.py` - criterion-1 measurement: envelope counts, nonce checks, D-58 ordering, barrier count, Final-Reveal confirmation
- `scripts/gate6_declarations.py` - Step-0 declaration-file evidence (own/peer exist, predates first move) — split from `gate6_clean_game.py` at the 150-line gate
- `scripts/gate6_tamper.py` - criterion-2 measurement: both D-67 tamper classes re-run end to end
- `scripts/gate6_step0.py` - criterion-3 measurement: the live Step-0 digest-forgery handshake
- `scripts/gate6_report.py` - assembles the final report dict + verdicts from the three criterion pieces
- `docs/phases/phase-6/gate6_measurement_evidence.json` - the measured evidence artifact (generated, committed)
- `docs/phases/phase-6/GATE-6-MEASUREMENT.md` - the gate report
- `docs/PRD_commit_reveal.md` - the per-mechanism PRD
- `.planning/phases/06-security-and-cryptography/deferred-items.md` - two honest, out-of-scope findings, logged not fixed
- `.planning/graphs/GRAPH_REPORT.md` - refreshed (06-96)

## Exact Evidence for Phase 7 / future reference (verbatim, do not re-derive)

All three GATE-6 criteria: **PASS**. See `docs/phases/phase-6/gate6_measurement_evidence.json`
for the full field-by-field evidence and `docs/phases/phase-6/GATE-6-MEASUREMENT.md` for the
write-up. Re-run anytime with `uv run python scripts/measure_gate6.py` (idempotent, zero env
vars).

## Decisions Made

See frontmatter `key-decisions`. The most consequential: reusing `test_step0_and_audit.py`'s
own private harness functions directly from `scripts/gate6_tamper.py`/`gate6_clean_game.py`
rather than the plan's own (stale) key_link naming `two_peer_game.py`'s `play_two_peer_game`,
which structurally cannot carry the Step-0 params 06-03 added to `perform_handshake`. This
follows both the outer task's own explicit instruction ("the shipped code is the truth") and
06-03-SUMMARY.md's own forward-looking guidance for 06-04, and mirrors an ALREADY-established
project precedent (`test_step0_and_audit_tamper.py` itself imports `test_step0_and_audit.py`'s
private helpers the same way).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `gate6_clean_game.py` needed a fourth sibling module**
- **Found during:** Task 1, after the first draft of `gate6_clean_game.py` (envelope counts +
  ordering + barrier + declaration evidence, all in one file) measured 155 code lines against
  the 150-line house limit
- **Issue:** The declaration-file evidence helper (`_predates_first_move`/`_declaration_evidence`)
  pushed the file 5 lines over
- **Fix:** Split into `gate6_declarations.py` (the Step-0 declaration-file checks alone),
  mirroring the `gate4_*`/`gate5_*` multi-file precedent this plan's own hard rule pre-authorized
- **Files modified:** `scripts/gate6_declarations.py` (new), `scripts/gate6_clean_game.py`
- **Verification:** `bash scripts/check_line_limit.sh` clean on both files (clean_game=139,
  declarations=39 code lines)
- **Committed in:** `77eafff` (Task 1 commit)

**2. [Rule 1 - Bug prevention in the plan's own text, not the shipped code] Followed the
plan's key_link's INTENT, not its stale literal wording**
- **Found during:** Task 1, before writing any measurement code
- **Issue:** The plan's own `key_links` names `tests/integration/two_peer_game.py`'s
  `play_two_peer_game` as the harness to reuse. That function's own `perform_handshake` call
  (unchanged since 04-12) does not pass `local_step0_digest`/`local_game_id`/
  `local_step0_declaration` — the exact params 06-03 added — so a literal reuse would either
  silently skip Step-0 entirely or require editing `two_peer_game.py` itself (a shared module
  04-12/04-14/05-\* already depend on, out of this plan's scope to touch). 06-03's own
  `test_step0_and_audit.py` already solved this by hand-rolling the two-peer wiring with the
  Step-0 params threaded through, documented in its own module docstring.
- **Fix:** Imported `_play_to_turn_loop_end`/`_run_audit_and_merge` directly from
  `tests.integration.test_step0_and_audit` — the SAME functions 06-03's own tamper tests already
  reuse the same way, never a second, parallel game-runner, and never touching
  `two_peer_game.py`.
- **Files modified:** none beyond the new `scripts/gate6_*.py` files (no existing file edited to
  make this work)
- **Verification:** `uv run python scripts/measure_gate6.py` runs clean, all three criteria
  PASS; `two_peer_game.py` confirmed untouched (`git diff` empty)
- **Committed in:** `77eafff` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 forced file split, 1 plan-text correction favoring the
shipped code's own established precedent over stale wording)
**Impact on plan:** Both were necessary — the split for the hard 150-line gate, the harness
choice because the plan's literal key_link could not actually carry Step-0's own params. No
scope creep: no existing file outside this plan's own new files was edited.

## Issues Encountered

None beyond the deviations above. The known load-sensitive flake
(`tests/integration/test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`)
fired once during this plan's own full-suite verification runs and was re-confirmed passing in
isolation (0.22s) — unrelated to this plan, not touched, matching the baseline this plan started
from.

## User Setup Required

None. `uv run python scripts/measure_gate6.py` needs zero credentials, zero environment
variables, and no second machine — matching `06-PLAN-OUTLINE.md` §5.

## Next Phase Readiness

- **Phase 6 is closed.** All three GATE-6 (§10.4 milestone 6) criteria measured **PASS** with
  real, re-runnable, localhost-only evidence — see
  `docs/phases/phase-6/GATE-6-MEASUREMENT.md`/`gate6_measurement_evidence.json`.
- `docs/PRD_commit_reveal.md` exists, matches house structure, traces every SEC-01..08
  requirement and every number back to `06-PLAN-OUTLINE.md` §2 or a labelled structural default.
- Knowledge graph refreshed and confirmed non-trivially changed (566 lines in
  `GRAPH_REPORT.md`), reflecting `security/`, `turn_commit.py`, `agent_context.py`, and the
  extended handshake modules.
- Two minor, non-blocking, out-of-scope findings logged in
  `.planning/phases/06-security-and-cryptography/deferred-items.md` for a future plan/phase to
  pick up if wanted (FINAL_REVEAL envelope-logging symmetry; the measurement-vs-league
  `games_played.json` counter distinction) — neither affects GATE-6's own PASS verdicts.
- Full repo gates green: 1226 passed / 1 pre-existing timing flake (confirmed passing in
  isolation, unrelated to this plan) — 1227 when the flake does not fire, matching the baseline
  exactly; 96.27% coverage; `ruff check .` 0 violations; `scripts/check_line_limit.sh` clean
  (including all seven new `scripts/*.py` files, checked by hand since `scripts/` is outside the
  automated scan's own glob); `scripts/check_no_llm_in_strategy.py` OK.
- **NOTHING TICKED anywhere in this plan.** `ROADMAP.md`'s Phase 6 checkboxes, and
  `docs/phases/phase-6/TODO.md`, are `/gsd:verify-work 6`'s job, not this plan's — per the
  project's own standing convention (05-03/06-01/06-02/06-03 all left theirs unticked too).
- No blockers for `/gsd:verify-work 6`.

---
*Phase: 06-security-and-cryptography*
*Completed: 2026-08-09*

## Self-Check: PASSED

All 11 created files verified present on disk; all 3 task commits (`77eafff`, `1de0dcf`,
`216eec4`) verified present in `git log --oneline --all`. Full gate suite independently
re-confirmed: 1226 passed / 1 pre-existing timing flake (re-confirmed passing in isolation,
0.22s) — 96.27% coverage, `ruff check .` 0 violations, `scripts/check_line_limit.sh` clean,
`scripts/check_no_llm_in_strategy.py` OK. `uv run python scripts/measure_gate6.py` re-confirmed
idempotent across two consecutive runs, zero env vars set, all three criteria PASS both times.
