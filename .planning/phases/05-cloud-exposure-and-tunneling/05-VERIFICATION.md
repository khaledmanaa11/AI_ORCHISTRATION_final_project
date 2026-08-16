---
phase: 05-cloud-exposure-and-tunneling
verified: 2026-08-16T19:47:03Z
status: gaps_found
score: 16/18 truths verified; BOTH §10.4 criteria PASS with independently re-derived evidence
re_verification:
  supersedes: "05-VERIFICATION.md dated 2026-08-14T15:20:00Z (status human_needed, 18/19).
    That verdict is NOT deleted: it is preserved verbatim at
    `05-VERIFICATION-2026-08-14-superseded.md` in this directory, per the append-only
    evidence discipline this project applies to its own gate documents (rule 38). It was
    correct when written and is now stale on two counts -- §10.4 criterion 2 was still
    PENDING there and has since PASSED (attempt 4, 2026-08-16), and plans 05-12..05-16
    (gaps G6-G10 plus deferred item #10) had not been executed."
  previous_status: human_needed
  previous_score: "18/19"
  previous_truths_regression_checked: true
  gaps_closed:
    - "§10.4 criterion 2 (CLOUD-02) -- the sole human_verification item of the 2026-08-14
      report. Closed by remote-round attempt 4; re-derived independently from the raw logs
      this pass, not read off the narrative."
    - "G9 (05-12) -- a non-str peer digest is a named non-agreement at the handshake, with a
      real production caller; honest foreign digests still reach the 'differed' branch."
    - "G7 (05-12) -- peer_game_id is safety-validated before it reaches a set, a Path or the
      audit's membership key; probed on BOTH roles through the production function."
    - "G6 (05-13) -- the audit marks each bounded attempt, and BOTH legs stop accusing a peer
      that answered."
    - "G8 (05-14) -- one inbound hint is decoded at most once; `ctx.pending_hints` finally has
      a production reader."
    - "G10 (05-15) -- dead `declare_truthfully` removed; capture Claim sent on the existing
      GAME_OVER envelope driven by the resolved outcome; a PRE-EXISTING false-accusation path
      in `receive_final_reveal` closed on the way."
    - "Deferred #10 (05-16) -- the turn loop marks every bounded attempt across six ladders."
  gaps_remaining: []
  regressions:
    - "Deferred item #4 has WORSENED from a flake into a deterministic failure on this box.
      Its own 2026-08-16 note records '1 failed, 2 passed' and 'the failing run is reliably
      the FIRST run after a source file changes, and the two runs after it pass'. Measured
      this pass on a quiet box with no source change between runs: 3 consecutive runs, 3
      failures. See gap 1."
gaps:
  - truth: "The standing Table-5 quality gate is green -- `uv run pytest tests/` reports 0 failed"
    status: failed
    reason: "Measured at HEAD ff4ac93: `1 failed, 1523 passed in 163.14s`, coverage 96.62%.
      The failure is `tests/integration/test_late_peer_teardown.py::
      test_without_the_linger_the_late_peers_own_push_is_cut_off` -- deferred item #4. It is
      no longer intermittent: the file alone, on a quiet box, with NO source change between
      runs, failed 3/3 (26.04 s / 25.97 s / 24.83 s). The orchestrator's briefing figure of
      `1523 passed / 0 failed` is not reproducible here; the phase TODO's own 05-16 row is
      accurate ('The one suite failure is deferred #4's late-peer flake'), the briefing is
      not. This does NOT block either §10.4 criterion and the PRODUCT behaviour is intact --
      the positive test `test_a_late_peer_still_completes_against_a_torn_down_peer` still
      passes, so a late peer does still complete with a matched verdict. What has stopped
      holding is the NON-VACUITY CONTROL: with `linger=False` the late peer's push now lands
      anyway, so nothing currently proves 05-04's `linger_for_peer` is load-bearing. The
      test says so in its own words: 'If BOTH are ever absent, the linger has stopped being
      load-bearing and this file is testing nothing.' 05-04's linger is one of the five
      diagnosed causes of the criterion-2 failure at attempt 1, so its proof going dark is
      worth closing rather than carrying."
    artifacts:
      - path: "tests/integration/late_peer_harness.py:60"
        issue: "`_LATE_SECONDS = 0.3` sequences B's audit 0.3 s behind A's rather than
          strictly after A's `stop_runtime`, so the control condition is a race this machine
          now loses every time"
      - path: "tests/integration/test_late_peer_teardown.py:89"
        issue: "`cut_off = peer_error is not None or bool(audit_incomplete)` -- both are now
          absent, so the assertion at :90 fires"
    missing:
      - "Make the premise deterministic instead of racy, as deferred item #4 has proposed
        since 05-06: have `late_peer_round(linger=False)` await A's `stop_runtime` before
        creating B's audit task, so B is unambiguously late rather than 0.3 s late. That
        STRENGTHENS the probe (B pushes into a demonstrably closed listener)."
      - "Do NOT close this by widening a timing constant or relaxing the assertion -- deferred
        item #4 states that explicitly, and the 05-16 executor declined the quick repair for
        that reason."
      - "The `linger=True` path must keep B arriving DURING the grace window, so both paths
        need designing together, by the plan that owns `late_peer_harness.py`."
  - truth: "The phase's trackers describe what the repository actually contains (rule 38, DOC-01)"
    status: partial
    reason: "Bookkeeping, closable inside this verify-work pass; recorded rather than waved
      through because CLAUDE.md states a phase is not verified until its triplet TODOs are
      checked. Three trackers still read as if the phase were mid-flight."
    artifacts:
      - path: ".planning/REQUIREMENTS.md:59-60"
        issue: "CLOUD-01 and CLOUD-02 are still `- [ ]` unchecked, though GATE-5 now carries
          measured PASS evidence for both criteria"
      - path: ".planning/REQUIREMENTS.md:183"
        issue: "`| CLOUD-01 … CLOUD-02 | Phase 5 | Pending |`. NOTE: every phase row in that
          table reads 'Pending', including phases 1-4 -- this is repo-wide tracker rot, not a
          phase-5 defect, and should be fixed as such rather than by editing one row"
      - path: "docs/phases/phase-5/TODO.md:23-27"
        issue: "rows 05-12, 05-13, 05-14, 05-15, 05-16 are still ☐. Each says in its own cell
          'Box left ☐ deliberately: /gsd:verify-work ticks it' -- so this is the expected
          hand-off, and this pass is where they get ticked"
      - path: "docs/TODO.md:108"
        issue: "row 05-99 'Update docs/TODO.md on phase completion' still ☐"
    missing:
      - "Tick docs/phases/phase-5/TODO.md rows 05-12..05-16 and docs/TODO.md row 05-99"
      - "Check CLOUD-01 and CLOUD-02 in .planning/REQUIREMENTS.md"
      - "Fix the REQUIREMENTS.md status table repo-wide, or leave it alone -- do not tick only
        the Phase 5 row while phases 1-4 stay 'Pending', which would misdescribe the repo in
        the other direction"
open_deferred_items:
  - id: 4
    summary: "test_late_peer_teardown non-vacuity control -- ESCALATED THIS PASS from flake to
      deterministic failure (3/3 on a quiet box). Promoted to gap 1 above."
    severity: major
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 13
    summary: "With `commit_reveal=False` the second mover's MOVE envelope is stamped one turn
      ahead. VERIFIED LATENT, not active: config/police/security.json:3 and
      config/thief/security.json:3 both ship `\"commit_reveal\": true`, and on that path the
      initiator's `maybe_resolve` is genuinely a no-op. Confined to what a replay of the JSONL
      says the peer claimed; the receiver keys its own record on `ctx.state.turn`."
    severity: major-on-a-latent-path
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 14
    summary: "A stray envelope costs `receive_final_reveal` one extra bounded ladder. Each
      iteration is watchdog-marked (agent_audit_exchange.py:126 verified this pass), so it
      degrades latency, never correctness, and an honest peer sends at most one Capture Claim."
    severity: minor
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 15
    summary: "tests/unit/services/test_bluff.py at 147/150. `scripts/check_line_limit.sh` exits
      0 at HEAD; a named seam (`_bluff_fixtures.py`) is already recorded."
    severity: minor
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 2
    summary: "agent_lifecycle.py headroom; 3, 5, 6, 8, 9, 11, 12 carried forward unchanged from
      the superseded report and from deferred-items.md."
    severity: carried-forward
    blocks_phase_goal: false
    blocks_10_4_criteria: false
---

# Phase 5: Cloud Exposure and Tunneling — Verification Report (re-verification, 2026-08-16)

**Phase Goal:** Expose the local FastMCP server publicly via ngrok or Localtonet.
**Verified:** 2026-08-16T19:47:03Z at HEAD `ff4ac93`
**Status:** gaps_found
**Re-verification:** Yes — supersedes `05-VERIFICATION.md` dated 2026-08-14T15:20:00Z, which
is **preserved verbatim** at `05-VERIFICATION-2026-08-14-superseded.md` (append-only, rule 38).

## What changed since the 2026-08-14 report

| | 2026-08-14 report | Now |
|---|---|---|
| §10.4 criterion 1 | PASS | **PASS** (unchanged, re-read) |
| §10.4 criterion 2 | PENDING — needed a second machine | **PASS** — attempt 4, 2026-08-16, re-derived independently below |
| Code under verification | 05-01..05-11 | + 05-12, 05-13, 05-14, 05-15, 05-16 (G6–G10 + deferred #10) |
| Standing test gate | 1327 passed / 0 failed | **1523 passed / 1 FAILED** — see gap 1 |

**Nothing below is taken from a SUMMARY.** Every claim is either a source read with a line
reference, a probe I ran against the shipped function, a revert probe, or a re-derivation
from the retained raw evidence. Where a SUMMARY and a measurement disagree, the measurement
is recorded.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence (measured this pass) |
|---|---|---|---|
| 1 | **§10.4 criterion 1** — each peer reachable on the public internet | ✓ VERIFIED | `gate5_smoke_evidence.json`, real run 2026-08-09T09:41:20Z: `verdict: PASS`, `url_is_https_and_matches_domain: true`, `authorized_request_reached_mcp: true`, `unauthorized_request_rejected_403: true`. Corroborated by attempt 4's own console: `public_url=https://perdurable-mireille-nonzoologically.ngrok-free.dev` |
| 2 | **§10.4 criterion 2** — a remote agent plays a full round through the tunnel | ✓ VERIFIED | Re-derived by script from the raw attempt-4 logs, NOT from the narrative — table below |
| 3 | **G9** A non-str peer digest is a named non-agreement, not a `TypeError`, with a PRODUCTION caller | ✓ VERIFIED | Probe + revert probe — below |
| 4 | **G7** `peer_game_id` is safety-validated before a set, a `Path` or the audit's membership key, on BOTH roles | ✓ VERIFIED | Probe through the production function on both roles — below |
| 5 | **G6a** The audit marks each bounded attempt, so it survives its own 135 s ladder | ✓ VERIFIED | `agent_audit_exchange.py:87` (push `_call`) and `:126` (`next_protocol_message(ctx, on_attempt=ctx.watchdog.touch)`), both inside the per-attempt closure |
| 6 | **G6b** BOTH audit legs stop accusing a peer that answered | ✓ VERIFIED | `agent_audit_wiring.py` — receive-leg branch present; revert probe fails on exactly the intended case |
| 7 | **Deferred #10 / 05-16** The turn loop marks every bounded attempt | ✓ VERIFIED | Four `wait_for_*` legs + `turn_buffer.await_move` + `send_hint` + `capture_declaration`; revert probe reproduces the literal NET-07 kill |
| 8 | **G8a** One inbound hint is decoded at most once, and `ctx.pending_hints` finally has a production reader | ✓ VERIFIED | `turn_hint_buffer.py:150` `is_replay` guard; `turn_language_io.py:73` `consume_hint` — the production reader; revert probe fails 2 |
| 9 | **G8b** Both hint branches stamp the turn actually played on every supported protocol path | ✓ VERIFIED | `turn_actions.py:92` (responder, `pending.turn`) and the initiator branch's commit-reveal precondition now written out rather than assumed. Deferred #13 is the MOVE envelope on the same toggle — a different envelope, separately logged |
| 10 | **G10a** Dead `declare_truthfully` removed; the rules-15/16 reasoning recorded | ✓ VERIFIED | `grep -rn declare_truthfully src/` returns only `deception.py:22` and `:25`, both prose explaining the removal. Zero definitions, zero callers |
| 11 | **G10b** Capture Claim sent on the EXISTING `GAME_OVER` envelope, driven by the resolved outcome | ✓ VERIFIED | `orchestrator.py:154` — `await send_capture_declaration(ctx, turn=ctx.state.turn, outcome=outcome)`, sharing one `outcome` object and one `ctx.state.turn` with the `game_over_record` two statements above. No policy, no LLM (rule 22 by construction) |
| 12 | **G10c** "no unreachable BARRIER/CAPTURE branches left" | ✓ VERIFIED under the clause's own second option | 05-UAT.md's `missing` reads *"remove **(or explicitly reserve)** the dead `declare_truthfully` + unreachable BARRIER/CAPTURE templates"*. 05-15 took the reserve option and measured why — I reproduced the measurement, below |
| 13 | **Rules 16/22** No false-accusation path introduced by this phase | ✓ VERIFIED | Every hostile-input probe below ends in a named outcome or a skipped check, never an accusation; honest foreign conventions still match. 05-15 **removed** a pre-existing one (`receive_final_reveal` reading `records` off whatever arrived first) |
| 14 | **Rule 38** No fabricated numbers; the gate record is honest | ✓ VERIFIED, with one correction | GATE-5-MEASUREMENT.md's header states both criteria PASS with per-attempt sections including the two FAILED attempts, and explicitly de-claims attempt 4's second game as a deterministic re-run of the transport rather than an independent sample. `NEEDED-FROM-MACHINE-B.md` records the one missing artifact as `- [ ]`. Correction: deferred item #4's characterisation of its own failure mode is now outdated — see gap 1 |
| 15 | **Phase 6 does not regress** | ✓ VERIFIED | `uv run python scripts/measure_gate6.py` → all three criteria `PASS` |
| 16 | The knowledge graph was refreshed after this phase's code landed | ✓ VERIFIED | `.planning/graphs/GRAPH_REPORT.md` mtime 2026-08-16 22:26; contains `unusable_peer_digest()`, `usable_peer_game_id()`, `consume_hint()`, `is_replay()`, `capture_declaration` |
| 17 | **The standing Table-5 quality gate is green** | ✗ **FAILED** | `1 failed, 1523 passed` — gap 1 |
| 18 | **The phase's trackers describe what the repo contains** | ✗ **FAILED (partial)** | gap 2 |

**Score: 16/18 truths verified.** Neither failure is a §10.4 criterion, and neither touches
the phase goal — both criteria carry real, independently re-derived measured evidence.

---

### §10.4 criterion 2 — re-derived from the raw evidence, not from the narrative

I ran my own script over `docs/phases/phase-5/remote-round-2026-08-16-attempt4/` rather than
reading GATE-5-MEASUREMENT.md's conclusions.

| Side | Game | Records | `game_over` | `audit_verdict matched` | technical_win | watchdog | audit_incomplete | ledger | declaration |
|---|---|---|---|---|---|---|---|---|---|
| machineA-police | `b22361aa93ccf310` | 50 | `capture` | `True` | 0 | 0 | 0 | ✓ | ✓ |
| machineB-thief | `b22361aa93ccf310` | 49 | `capture` | `True` | 0 | 0 | 0 | ✓ | ✓ |
| machineA-police | `d265603c116a9f99` | 50 | `capture` | `True` | 0 | 0 | 0 | ✓ | ✓ |
| machineB-thief | `d265603c116a9f99` | 49 | `capture` | `True` | 0 | 0 | 0 | ✓ | ✓ |

Every log's `game_uid` set is a **singleton** equal to its own filename stem, on both sides
of both games — the artifact-join failure that sank attempt 1 does not recur.

**Cross-signed declarations, byte-compared:**

```
b22361aa93ccf310: A.own == B.peer -> True ; B.own == A.peer -> True
d265603c116a9f99: A.own == B.peer -> True ; B.own == A.peer -> True
```

**The declaration is honest and complete** — machine A, game `b22361aa93ccf310`, exactly the
ten `DeclarationField` keys, HMAC'd:

```
"llm_name": "claude-haiku-4-5",  "team_code": "khm-mn17",  "code_version": "1.00",
"games_played_so_far": 991,      "commit_hash": "0632e04e364984452ae7b5477c698f379b07e9ef"
```

`llm_name` is the live model, not `template-fallback` — so 05-07's honest-declaration gate
and criterion 2's live-LLM claim agree with the artifact.

**Two residuals in the evidence, both already recorded by the phase, neither a criterion failure:**

1. `machineB-thief/eb55daeefafb4208.jsonl` is a **1-record log containing a
   `watchdog_incident`** (`idle_seconds: 60`, `turn: 0`). This is B's pre-game session waiting
   for A before the two counted games began. It is retained deliberately and named in
   `NEEDED-FROM-MACHINE-B.md` under "Extras retained for honesty". It is not part of either
   counted game. Stated here because the orchestrator's briefing said "zero
   `watchdog_incident`" — true of the gate runs and of both counted games, not of the
   evidence directory as a whole.
2. `consoleB_attempt4.txt` was **not captured** — machine B's console was not Tee'd. Recorded
   as an open `- [ ]` in `NEEDED-FROM-MACHINE-B.md` rather than glossed. Machine A's console
   is retained and carries the public ngrok URL. Both JSONLs, both ledgers and all four
   declarations are present, which is the criterion's stated closing condition.

---

### The skeptical checks I was asked to run

#### 1. Production callers — a validator reachable only from tests proves nothing

| Symbol | Production caller | Chain to `run_agent` |
|---|---|---|
| `config_hash.unusable_peer_digest` | `config_hash.py:120`, inside `compare_named_digest` | `compare_named_digest` ← `handshake_evaluate.py:118`/`:125` (`_compare_offer`) ← `perform_handshake` ← `agent_entrypoint.py:82`. **Wired** |
| `game_identity_validate.usable_peer_game_id` | `game_identity.py:84` (`negotiated_game_id`) **and** `:170` (`adopt_negotiated_game_id`) | `adopt_negotiated_game_id` ← `agent_entrypoint.py:98`, after `result.agreed`, before `write_declaration`/`run_turn_loop`. **Wired** |
| `Watchdog.touch()` — audit path | `agent_audit_exchange.py:87` (push closure) and `:126` (`on_attempt=`) | `run_final_audit` ← `agent_entrypoint.py:110`. **Wired** |
| `Watchdog.touch()` — turn-loop path | `turn_commit_wait.py:121, :150, :170, :186` all pass `on_attempt=ctx.watchdog.touch`; `turn_buffer.py:104` and `:153`; `turn_commit_send.py:51, :132`; `capture_declaration.py:117` | all four `wait_for_*` legs are called from `turn_commit.py:79, :111, :151, :164` ← `run_turn_loop`. **Wired**. `grep -rn "watchdog\.touch" src/ --include=*.py` → **18** |
| `turn_hint_store.consume_hint` | `turn_language_io.py:73` inside `decode_turn_hint` | `decode_turn_hint` ← `turn_actions.py:107` ← `take_my_turn` ← `run_turn_loop`. **Wired** |

`ctx.pending_hints` — flagged in the 2026-08-14 report as a write-only buffer whose tests
were therefore a trap — now has a genuine production reader: `turn_hint_store.is_replay`
reads it at `turn_hint_buffer.py:150`, and `consume_hint` writes the marker at consumption.

#### 2. Do the G6–G10 fixes hold in live wiring — probed, not read

**G9, direct probe of the shipped `compare_named_digest`:**

```
remote=           7 -> (False, 'config digest present in peer payload but not a string: int')
remote=         [1] -> (False, 'config digest present in peer payload but not a string: list')
remote=    {'a': 1} -> (False, 'config digest present in peer payload but not a string: dict')
remote=        True -> (False, 'config digest present in peer payload but not a string: bool')
remote=        None -> (False, 'config digest absent from peer payload')
control wrong-but-str -> (False, 'config digest mismatch: local=abc remote=def')
control agreeing      -> (True, 'config digests agree')
strict contract kept: digests_match('abc', 7) -> TypeError: digests_match requires two str arguments
```

The safety gate contains the peer's half; `digests_match` keeps its strict D-46 contract for
internal callers. Exactly what plan 05-12 promised, verified against the function rather than
the prose.

**G7, probe through the PRODUCTION `adopt_negotiated_game_id`, both roles, 13 inputs each.**
No input raised. Selected rows:

```
police  peer_game_id='../../evil'   raised=None cand=None  log_moved=False
police  peer_game_id='{}'           raised=None cand=None  log_moved=False
police  peer_game_id=''             raised=None cand=None  log_moved=False
thief   peer_game_id='../../evil'   raised=None cand=None  log_moved=False
thief   peer_game_id='con\x00x'     raised=None cand=None  log_moved=False
thief   peer_game_id='550e8400-e29b-41d4-a716-446655440000'
        raised=None uid='550e8400-e29b-41d4-a716-446655440000'
        cand={'test-thief...','550e8400-e29b-41d4-a716-446655440000'} log_moved=True
police  peer_game_id='PEERUID99'    raised=None cand={'PEERUID99','test-police...'}
```

Both halves hold, and they are the halves that matter for rules 16/22: **hostile shapes cost
the peer nothing** — `candidate_game_ids` goes to `None`, which `audit_state` skips entirely,
so nobody is accused — while an **honest foreign convention** (a UUID, upper-case) is still
adopted and still lands in the candidate set on both roles. Validation is safety-only, never
convention-conformance, which was the trap 05-12 set out to avoid.

**Live two-peer proof, `uv run python scripts/dev_launch.py` — exit 0:**

```
police  stem=c85ef36086d92961 n=43 game_over=['capture'] matched=[True]
        technical_win=0 watchdog=0 audit_incomplete=0 ledger=True decl=True
thief   stem=c85ef36086d92961 n=42 game_over=['capture'] matched=[True]
        technical_win=0 watchdog=0 audit_incomplete=0 ledger=True decl=True
```

One shared stem across log, ledger and declaration on both sides — G2's fix still standing
after five more plans landed on top of it.

#### 3. Are the new tests non-vacuous? Four revert probes

The brief warned that three executors had caught their own tests passing against the wrong
fix. So I reverted each fix in shipped source and re-ran its guard suite. All four fixes are
genuinely load-bearing:

| Fix reverted | Suite | Result |
|---|---|---|
| `on_attempt=ctx.watchdog.touch` removed from all four `turn_commit_wait` legs + `turn_buffer._pull` | `test_turn_loop_watchdog.py` | **2 failed, 2 passed** — and the failure is the literal `ProcessKilledError: NET-07 fired: os._exit(1) would have run here`. The 2 that still pass are the counter-controls (frozen loop still killed; watchdog never disarmed), which is the correct signature |
| `turn_hint_store.is_replay` guard removed | `test_hint_replay.py` | **2 failed** — `AssertionError: the initiator decoded the same hint twice / assert 'no_evidence' == 'no_hint'` |
| G6 receive-leg non-accusation removed | `test_audit_send_failure.py` | **1 failed, 4 passed** — `test_both_of_our_own_legs_failing_after_a_board_outcome_accuses_nobody`: `the board outcome did not stand`. The 4 that pass are the fairness controls, unchanged |
| `unusable_peer_digest` gate removed **and** `usable_peer_game_id` neutered to identity | `test_config_hash_peer` + `test_handshake_peer_digest` + `test_game_identity_validate` + `test_game_identity_adopt` | **59 failed, 45 passed** |

All source files restored and confirmed byte-clean (`git status --porcelain` empty).

#### 4. The one clause knowingly not met literally

The phase TODO row for 05-15 carries *"no unreachable BARRIER/CAPTURE branches left"*. 05-15
reported honestly that it did not remove them. **The reasoning holds, and I re-measured it.**

Two things make removal wrong:

- `shared/deception_types.py:62-63` — `ALWAYS_TRUE_KINDS` maps BARRIER → *"rules 15/16"* and
  CAPTURE → *"rules 21/22"*. This dict **is** `DeceptionPlan.__post_init__`'s truthfulness
  enforcement. Deleting those rows would not remove dead code, it would make
  `DeceptionPlan(intent=LIE, kind=BARRIER)` constructible — deleting the rule-16 guard.
- `services/llm/hintbank_templates.py:130-131` — `BANK` is a **total** `(kind, intent)` map,
  indexed directly. Probe X, deleting those two rows:

```
FAILED tests/unit/services/test_bluff_property.py::test_compose_never_raises_and_always_returns_a_legal_hint
FAILED tests/unit/services/test_hintbank.py::test_select_phrases_barrier_and_capture_declarations
FAILED tests/unit/services/test_hintbank.py::test_every_legal_kind_intent_pair_selects_without_error[barrier-truth]
FAILED tests/unit/services/test_hintbank.py::test_every_legal_kind_intent_pair_selects_without_error[capture-truth]
FAILED tests/unit/services/test_hintbank_templates.py::test_bank_covers_every_legal_claim_kind_intent_pair
5 failed, 261 passed
...
E   KeyError: (<ClaimKind.CAPTURE: 'capture'>, <Intent.TRUTH: 'truth'>)
```

A `KeyError` escapes `bluff.compose()`, whose contract is having no failure mode. **These
branches are total, not dead.** And decisively: 05-UAT.md's own `missing` clause reads
*"remove **(or explicitly reserve)** the dead `declare_truthfully` + unreachable
BARRIER/CAPTURE templates and prompt branches"* — the reserve option is sanctioned by the gap
that raised it. 05-15 took it, documented it in source, and the thing the clause actually
targeted (`declare_truthfully`, the zero-caller constructor with the misleading docstring) is
**gone**: `grep -rn declare_truthfully src/` returns only two prose lines explaining its
removal. Not a gap.

#### 5. Deferred items — do any block the phase goal or the §10.4 criteria?

| Item | Blocks phase goal? | Blocks §10.4? | Finding |
|---|---|---|---|
| **#4** socket-race flake in `test_late_peer_teardown` | No | No | **But it has escalated.** Now deterministic (3/3), so the standing gate is red and 05-04's linger has no working non-vacuity proof. **Promoted to gap 1** — see below |
| **#13** toggle-off MOVE envelope stamped one turn ahead | No | No | **The orchestrator's reading is confirmed by measurement, not inherited.** `config/police/security.json:3` and `config/thief/security.json:3` both ship `"commit_reveal": true`; on that path the initiator's `maybe_resolve` is genuinely a no-op, so both sides' REVEALs carry the turn played. Latent. It also costs nothing downstream today: the receiver keys its own record on `ctx.state.turn`, and `await_move` never compares the peer's declared turn — the damage is confined to what a JSONL replay says the peer claimed (rule 20 evidence quality, not a verdict) |
| **#14** stray envelope costs one extra retry ladder | No | No | Confirmed bounded: each iteration re-enters `next_protocol_message` with `on_attempt=ctx.watchdog.touch` (`agent_audit_exchange.py:126`), so a wedged loop is still killed and a slow one still reaches a verdict. An honest peer sends at most one Capture Claim. Latency, not correctness |
| **#15** `test_bluff.py` at 147/150 | No | No | `bash scripts/check_line_limit.sh` → exit **0**. A watch item with a named seam already recorded |

So: on #13, #14 and #15 the orchestrator's reading is right and I verified it rather than
inheriting it. On **#4 the reading no longer holds** — it has stopped being a flake.

---

### Gap 1 in detail — the standing gate is red, and #4 is no longer intermittent

My own full run at HEAD `ff4ac93`:

```
FAILED tests/integration/test_late_peer_teardown.py::test_without_the_linger_the_late_peers_own_push_is_cut_off
1 failed, 1523 passed in 163.14s (0:02:43)
Required test coverage of 85.0% reached. Total coverage: 96.62%
```

Deferred item #4's own latest note (2026-08-16, written by 05-16) says the failing run is
*"reliably the FIRST run after a source file changes, and the two runs after it pass."*
Measured this pass, file alone, quiet box, **no source change between runs**:

```
--- run 1 (file alone) ---  1 failed, 1 passed in 26.04s
--- run 2 (file alone) ---  1 failed, 1 passed in 25.97s
--- run 3 (file alone) ---  1 failed, 1 passed in 24.83s
```

3/3. That is a regression in the item's character, and it matters for two reasons:

1. **The gate is red.** CLAUDE.md's Table 5 treats the suite as a pre-commit gate, and every
   SUMMARY in this phase reports "N passed / **0 failed**". The briefing figure of
   `1523 passed / 0 failed` is not reproducible here. The phase's own TODO row for 05-16 is
   accurate about this — *"The one suite failure is deferred #4's late-peer flake"* — so the
   phase documented it; the briefing rounded it away.
2. **The linger's proof has gone dark, not the linger.** The positive test
   `test_a_late_peer_still_completes_against_a_torn_down_peer` still passes, and
   `linger_for_peer` is present, literal-free and wired at `agent_entrypoint.py:144-148`
   inside a `finally` with `stop_watchdog` first. The product behaviour is intact. What fails
   is the control that proves the linger *causes* it: with `linger=False` the late peer's push
   now lands anyway. The test states the consequence in its own docstring — *"If BOTH are ever
   absent, the linger has stopped being load-bearing and this file is testing nothing."*
   `linger_for_peer` is one of the five diagnosed causes of attempt 1's criterion-2 failure,
   so losing its proof is worth a plan, not a shrug.

**Do not close this by widening `_LATE_SECONDS` or relaxing the assertion.** Deferred item #4
says so explicitly and the 05-16 executor declined the quick repair for that reason. The
recorded fix — sequence the harness so B is unambiguously late rather than 0.3 s late —
*strengthens* the probe.

### Required Artifacts (05-12..05-16, the plans not covered by the superseded report)

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pursuit/network/config_hash.py` | `unusable_peer_digest` containment | ✓ VERIFIED | Production caller at `:120`; probed; peer VALUE never interpolated into the detail, only its type name |
| `src/pursuit/network/game_identity_validate.py` | peer-id safety gate + `relocate_log` | ✓ VERIFIED | Both consumed by `game_identity.py:84` and `:170`; `relocate_log` catches `OSError` **and** `ValueError` (embedded NUL) and half-adopts nothing on failure |
| `src/pursuit/network/agent_audit_exchange.py` | per-attempt watchdog touch + FINAL_REVEAL loop | ✓ VERIFIED | `:87`, `:126`; the `while True` loop closes the pre-existing `records=[]` false-accusation path |
| `src/pursuit/network/agent_audit_wiring.py` | non-accusatory RECEIVE leg | ✓ VERIFIED | Discrimination is `send_verdict is not None` — a push that LANDED keeps rule 36's sanction intact; revert probe confirms |
| `src/pursuit/network/turn_hint_store.py` | single-decode marker | ✓ VERIFIED | `is_replay` + `consume_hint`; marker written at CONSUMPTION, and the source records that the plan's own arrival-time proposal was measured half-wrong |
| `src/pursuit/network/turn_commit_wait.py` | four legs mark each attempt | ✓ VERIFIED | `:121, :150, :170, :186`; post-ladder touch at `:100` retained |
| `src/pursuit/network/capture_declaration.py` | capture Claim on the existing envelope | ✓ VERIFIED | Cop-only, gated on the resolved `Outcome`, `ToolError` swallowed, `message_sent` written only when the push landed |
| `src/pursuit/strategy/deception.py` | no dead constructor | ✓ VERIFIED | `declare_truthfully` gone; rules 15/16/21/22 quoted in the module docstring |
| `.planning/graphs/GRAPH_REPORT.md` | refreshed after the code landed | ✓ VERIFIED | 2026-08-16 22:26, carries all five new symbols |
| `docs/phases/phase-5/GATE-5-MEASUREMENT.md` | both criteria, honest statuses | ✓ VERIFIED | Both PASS; four attempts recorded including two failures; attempt 4's second game explicitly de-claimed as a deterministic transport re-run |
| `tests/integration/test_late_peer_teardown.py` | sequenced two-peer proof | ✗ **PARTIAL** | Positive case passes; the non-vacuity control fails 3/3 — gap 1 |

### Requirements Coverage

| Requirement | Status | Blocking issue |
|---|---|---|
| CLOUD-01 (each peer reachable via tunnel) | ✓ SATISFIED | None — criterion 1 carries measured PASS evidence. Tracker checkbox still unticked (gap 2) |
| CLOUD-02 (remote agent plays a full round) | ✓ SATISFIED | None — criterion 2 closed by attempt 4 and independently re-derived above. Tracker checkbox still unticked (gap 2) |

### Standing Gates — re-run fresh this pass

| Gate | Result |
|---|---|
| `uv run ruff check .` | **All checks passed!** (0 violations) |
| `uv run pytest tests/ --cov` | **1 failed, 1523 passed**, 96.62% coverage, 163.14 s — **gap 1** |
| `bash scripts/check_line_limit.sh` | exit **0**, clean |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `uv run python scripts/measure_gate6.py` | all three criteria **PASS** |
| `uv run python scripts/dev_launch.py` | exit **0**, one shared uid `c85ef36086d92961`, both sides `matched=true`, zero technical_win / watchdog / audit_incomplete |
| Secret scan (`sk-ant-` over `src/ config/ scripts/`) | **0 hits**; `.env` untracked (`git ls-files --error-unmatch .env` → *Did you forget to 'git add'?*) |

### Anti-Patterns / Findings

| File | Severity | Finding |
|---|---|---|
| `tests/integration/late_peer_harness.py:60` | 🛑 **Blocker for the gate, not for the goal** | `_LATE_SECONDS = 0.3` makes the non-vacuity control a race this box now loses deterministically. Gap 1 |
| `.planning/phases/.../deferred-items.md` item 4 | ⚠️ Warning | Its 2026-08-16 characterisation ("first run after a source change; the two after it pass") is refuted by 3/3 consecutive failures with no source change. Needs a dated append, in the file's own correction style |
| `.planning/REQUIREMENTS.md:183` | ℹ️ Info | The whole status table reads "Pending" for every phase including 1–4. Repo-wide rot; fixing only the Phase-5 row would misdescribe the repo in the other direction |
| `docs/phases/phase-6/gate6_measurement_evidence.json` | ℹ️ Info | The **committed** evidence predates 05-15. Re-running `measure_gate6.py` this pass gave all three criteria PASS but a diff of exactly what 05-15 predicted: 3 timestamp lines plus two new `"game_over": 1` counters (under `police_sent` and `thief_received`) — the capture declaration 05-15 added. 05-15 measured this and did not refresh the committed file. Harmless (the verdict is unchanged, and the delta is explained in 05-15's own TODO row), but the file on disk no longer matches a fresh run. I reverted my regeneration to leave the tree clean; refreshing it is a one-command follow-up |
| `docs/phases/phase-5/remote-round-.../NEEDED-FROM-MACHINE-B.md` | ℹ️ Info (good practice) | Records the one missing artifact (`consoleB_attempt4.txt`) as an open `- [ ]` rather than omitting it. Noted as a model of the discipline, not as a defect |
| All Phase-5 source added by 05-12..05-16 | — | Scanned for `TODO`/`FIXME`/`XXX`/`HACK`/`PLACEHOLDER` and stub shapes: **zero matches**. No placeholder, no console-log-only implementation |

### Gaps Summary

**Both §10.4 criteria are genuinely met and their evidence survives independent
re-derivation.** Criterion 1 has a real smoke run; criterion 2 has two complete games across
two machines on two networks, with a shared uid per game across all artifact classes on both
sides, agreeing `capture` outcomes, `audit_verdict matched=true` on both machines, byte-identical
cross-signed declarations in both directions, and a live `claude-haiku-4-5` declared. I
re-derived all of that from the raw logs. Understating it would be its own misreport.

**The G6–G10 fixes are real, not merely tested.** Every validator and hook this phase added
has a production caller traceable to `run_agent`, every one of them survived a hostile-input
probe against the shipped function, and all four fixes failed their guard suites when
reverted. The one clause knowingly not met literally — "no unreachable BARRIER/CAPTURE
branches" — is met under the sanctioned alternative in the gap's own wording, and I reproduced
the `KeyError` that makes removal wrong.

**Two gaps stand:**

1. **The standing test gate is red**, and deferred item #4 is no longer a flake (3/3). The
   product is fine; the non-vacuity proof of 05-04's linger is not. Neither §10.4 criterion is
   affected, but the project's own enforced gate is, and a fix that widens a timing constant
   is explicitly ruled out by the item itself.
2. **Trackers are stale** — CLOUD-01/CLOUD-02 unchecked in REQUIREMENTS.md, five phase-TODO
   rows still ☐ (each deliberately left for this pass), and `docs/TODO.md` row 05-99 ☐. All
   closable inside this verify-work pass.

**GATE-5 is MET.** These gaps do not un-tick it.

---

*Verified: 2026-08-16T19:47:03Z at HEAD `ff4ac93`*
*Supersedes: `05-VERIFICATION-2026-08-14-superseded.md` (preserved, not deleted)*
*Verifier: Claude (gsd-verifier)*
