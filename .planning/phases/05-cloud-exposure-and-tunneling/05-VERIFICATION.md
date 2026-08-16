---
phase: 05-cloud-exposure-and-tunneling
verified: 2026-08-17T02:40:00Z
status: human_needed
score: 20/21 truths verified; BOTH §10.4 criteria PASS on independently re-derived evidence
re_verification:
  supersedes: "05-VERIFICATION.md dated 2026-08-16T19:47:03Z (status gaps_found, 16/18),
    preserved verbatim at `05-VERIFICATION-2026-08-16-superseded.md`. That file in turn
    supersedes `05-VERIFICATION-2026-08-14-superseded.md` (status human_needed, 18/19),
    also preserved. All three are retained, none edited: this project applies append-only
    evidence discipline to its own gate documents (rule 38)."
  previous_status: gaps_found
  previous_score: "16/18"
  previous_truths_regression_checked: true
  verified_at_head: 26204d8
  gaps_closed:
    - "GAP 1 -- the standing Table-5 test gate was red (`1 failed, 1523 passed`, deferred
      item #4's late-peer control failing 3/3). CLOSED and re-measured from scratch this
      pass: full suite `1539 passed in 185.05s`, `0 failed`, coverage `96.64%`. The control
      file alone ran 6/6 clean, every run at the ~37 s `pass` wall-clock signature the
      deferred item predicts. Fix is test-only: `git diff --name-only ff4ac93 3babfe6 |
      grep ^src/` returns 0 files."
  gaps_remaining:
    - "GAP 2 -- the trackers. UNCHANGED and deliberately held for this pass. Now
      confirmed CLOSABLE with the earned rows enumerated below; the user reserved the
      ticking, so it is filed as `human_verification` rather than as a code gap."
  regressions: []
  new_since_previous:
    - "05-16 (deferred #10) -- the turn loop marks every bounded attempt. Verified."
    - "05-17 -- an early peer FINAL_REVEAL is buffered instead of eaten, closing a
      manufactured-silence false-accusation path. Verified."
    - "05-18 -- the fifth instance closed AND the class pinned by a source-enumerated
      guard over 12 pull sites. Verified, including five vacuity probes I ran myself."
human_verification:
  - test: "Tick the earned tracker rows (bookkeeping, not a measurement)"
    expected: "docs/phases/phase-5/TODO.md rows 05-12..05-18 -> ☑;
      docs/TODO.md row 05-99 -> ☑ and a GATE-5-MET banner on its Phase-5 header;
      .planning/REQUIREMENTS.md CLOUD-01 and CLOUD-02 -> [x].
      Each row's evidence is listed in `Earned tracker rows` below."
    why_human: "The user explicitly reserved this edit ('I will tick them'). Nothing about
      it is unmeasured -- every row's evidence was verified this pass."
  - test: "Decide the repo-wide REQUIREMENTS.md status table (do not tick Phase 5 alone)"
    expected: "`.planning/REQUIREMENTS.md:179-188` reads `Pending` for ALL TEN rows,
      including Phase 3 and Phase 6 whose gates docs/TODO.md itself banners as MET. Fix the
      table as a whole or leave it alone."
    why_human: "Editing only the Phase-5 row would misdescribe the repository in the other
      direction. Scope decision, not a phase-5 defect."
open_deferred_items:
  - id: 4
    summary: "CLOSED. Re-measured this pass: control 6/6 green; mutation M1 (linger
      neutered) fails the POSITIVE test 2/2; mutation M2 (control given the linger=True
      ordering) fails the CONTROL 2/2. Both directions mutation-sensitive."
    severity: closed
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 13
    summary: "commit_reveal=False second-mover MOVE envelope stamped one turn ahead.
      LATENT, re-verified by reading the shipped files: config/police/security.json and
      config/thief/security.json both carry `\"commit_reveal\": true`."
    severity: major-on-a-latent-path
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 16
    summary: "The linger's quiet interval derivation is unsound as written (a peer schedules
      its retry one backoff from its own FAILURE, up to one response_timeout after our
      observed ARRIVAL). Prose/arithmetic defect in a module whose whole point is having no
      magic number. Attempt 4 completed both counted games with zero watchdog_incident,
      zero technical_win and zero audit_incomplete on both sides, so the window it does
      cover was sufficient over a real tunnel."
    severity: minor-to-major-arithmetic
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 17
    summary: "linger_for_peer drains a peer FINAL_REVEAL and discards it unaudited. Fires
      only AFTER run_final_audit has returned, so it cannot change our verdict or
      manufacture an accusation -- it is evidence retention (rule 20 quality), not
      correctness. Carried as the class guard's ONE named exemption; I removed the
      exemption and the breach fired, so the exempted check is live and the item is real."
    severity: major-on-a-narrow-window
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 19
    summary: "turn_buffer.await_move has no type test; 8 of 9 MessageTypes reach move
      handling on the toggle-off path. INSTANCE SIX, found by the new guard on its first
      run. LATENT on the same premise as #13, re-verified from the shipped config files."
    severity: major-on-a-non-shipped-toggle
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 20
    summary: "Three modules within two lines of the 150-line gate. `check_line_limit.sh`
      exits 0 tree-wide AND on each of the nine near-gate files named explicitly by path."
    severity: minor-structural
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 14
    summary: "A stray envelope costs receive_final_reveal one extra bounded ladder. Each
      iteration is watchdog-marked (agent_audit_exchange.py:145, re-read this pass)."
    severity: minor
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 15
    summary: "tests/unit/services/test_bluff.py at 147/150; gate exits 0. Superseded in
      substance by #20, which names three files at the same boundary."
    severity: minor
    blocks_phase_goal: false
    blocks_10_4_criteria: false
  - id: 2
    summary: "agent_lifecycle.py headroom; 3, 5, 6, 8, 9, 11, 12 carried forward unchanged."
    severity: carried-forward
    blocks_phase_goal: false
    blocks_10_4_criteria: false
findings:
  - id: F1
    severity: info
    summary: "OVER-CLAIM, documentation only. `_pull_site_discovery.py:33-34` states
      'Every one of the five historical instances sits inside the set this produces', and
      `test_envelope_boundary_invariant.py:3-5` calls 05-09, 05-10, 05-15, 05-17 and #18
      'the same defect five times over'. Measured: THREE sit inside the discovered set
      (05-15 -> receive_final_reveal, 05-17 -> next_protocol_message + the wait legs,
      #18 -> await_and_respond). 05-09's defect was an EXCEPTION taxonomy on the OUTBOUND
      ladder (`src/pursuit/network/deadline.py::call_with_retry`, per its own key-files) --
      not a queue pull, and structurally unreachable by a pull-site enumeration. 05-10
      touched `src/pursuit/security/audit.py` + `deadline.py`; its peer-data fault is
      REACHED THROUGH `receive_final_reveal` (which is in the set) but the mishandling
      function is not. The guard's load-bearing property is unaffected and was measured
      true; only the historiography in two docstrings overstates."
  - id: F2
    severity: info-good
    summary: "The enumeration's scope is COMPLETE for the class it claims, and I measured
      that rather than assuming it: `grep -rn '\\.queue\\b|get_nowait' src/ --include=*.py`
      returns ZERO hits outside `src/pursuit/network/*.py`, and that package has no
      subdirectories. The non-recursive glob therefore covers 100% of the codebase's
      queue-pull surface."
  - id: F3
    severity: info
    summary: "docs/phases/phase-6/gate6_measurement_evidence.json still predates 05-15.
      Re-running `measure_gate6.py` gives all three criteria PASS and a diff of exactly
      what 05-15 predicted: 3 timestamp lines plus `\"game_over\": 1` under `police_sent`
      and `thief_received` (the capture declaration). I reverted my regeneration to leave
      the tree clean; refreshing it is a one-command follow-up."
  - id: F4
    severity: info
    summary: "Each of the four counted attempt-4 logs carries exactly ONE
      `illegal_transition` record -- `handshake -> handshake`, `severity: recoverable`,
      turn 0. Reproduced on this box by `measure_gate6.py` and `dev_launch.py`, so it is
      the benign artifact of the two-directional handshake, not an attempt-4 anomaly.
      Recorded because I measured it and the prior reports did not name it."
  - id: F5
    severity: info
    summary: "`.planning/graphs/GRAPH_REPORT.md` does NOT contain
      `wait_for_reveal_capturing_early_ack` or `turn_commit_wait_reveal`. This is NOT
      staleness: the REPORT is a selective narrative (`turn_commit_wait`, `turn_commit_pull`,
      `agent_teardown` and `turn_buffer` are absent from it too, and all long predate this
      phase). The queryable artifact IS current -- `graph.json`, mtime 2026-08-17 01:56,
      8042 nodes, carries `turn_commit_wait_reveal`,
      `wait_for_reveal_capturing_early_ack`, `_pull_site_discovery`,
      `test_envelope_boundary_invariant` and `late_peer_gate`."
  - id: F6
    severity: info
    summary: "05-17's headline probe P2 ('widening the receive ladder to 21 attempts, 10x
      shipped, produced a BYTE-IDENTICAL accusation') was NOT re-run this pass. It is
      corroborating evidence for the routing-not-timing diagnosis, not the fix itself; the
      fix is independently proven by my probe A and by the 108-cell matrix. Named so the
      distinction between what I measured and what I read is explicit."
---

# Phase 5: Cloud Exposure and Tunneling — Verification Report (re-verification, 2026-08-17)

**Phase Goal:** Expose the local FastMCP server publicly via ngrok or Localtonet.
**Verified:** 2026-08-17 at HEAD `26204d8`, tree clean before and after every probe.
**Status:** human_needed — **20/21 truths verified; no code gap remains.**
**Re-verification:** Yes, the third. Supersedes `05-VERIFICATION-2026-08-16-superseded.md`,
which supersedes `05-VERIFICATION-2026-08-14-superseded.md`. **All three are preserved.**

## What changed since the 2026-08-16 report

| | 2026-08-16 report | Now |
|---|---|---|
| §10.4 criterion 1 | PASS | **PASS** (re-read) |
| §10.4 criterion 2 | PASS | **PASS** (re-derived again, by my own script, from the raw JSONL) |
| Code under verification | 05-01..05-16 | + **05-17**, **05-18** |
| Standing test gate | **1 FAILED** / 1523 passed | **0 failed / 1539 passed**, 96.64% |
| Gaps | 2 (gate red; trackers) | **0 code gaps**; trackers still untick, by hand-off |

**Nothing below is taken from a SUMMARY.** Every claim is a source read with a line
reference, a probe I ran against the shipped function, a mutation probe with the file
restored afterwards, or a re-derivation from retained raw evidence. Where a document and a
measurement disagree, the measurement is recorded — see finding **F1**, where they do.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence measured this pass |
|---|---|---|---|
| 1 | **§10.4 criterion 1** — each peer reachable on the public internet | ✓ VERIFIED | `gate5_smoke_evidence.json`: `verdict: PASS`, `url_is_https_and_matches_domain: true`, `authorized_request_reached_mcp: true`, `unauthorized_request_rejected_403: true`, `public_url=https://perdurable-mireille-nonzoologically.ngrok-free.dev` |
| 2 | **§10.4 criterion 2** — a remote agent plays a full round through the tunnel | ✓ VERIFIED | Re-derived by my own script from the raw attempt-4 JSONL — table below. Two games × two machines: agreeing `capture`, `matched=true`, **6-turn** peer_audit AND self_audit all matched, 6-record ledgers, byte-identical cross-signed declarations both directions, live `claude-haiku-4-5` |
| 3 | **G9** A non-str peer digest is a named non-agreement with a production caller | ✓ VERIFIED (regression) | `config_hash.py:120` inside `compare_named_digest` ← `handshake_evaluate.py` ← `perform_handshake` ← `agent_entrypoint.py:82` |
| 4 | **G7** `peer_game_id` safety-validated before a set, a `Path` or the audit key, both roles | ✓ VERIFIED (regression) | `game_identity.py:84` and `:170` ← `agent_entrypoint.py:98` |
| 5 | **G6a** The audit marks each bounded attempt | ✓ VERIFIED | `agent_audit_exchange.py:87` (push closure), `:145` (`on_attempt=ctx.watchdog.touch`) |
| 6 | **G6b** Both audit legs stop accusing a peer that answered — **and rule 36 still bites** | ✓ VERIFIED | `agent_audit_wiring.py:88-97`: the discrimination is `send_verdict is not None`. A push that LANDED keeps the sanction. My own silent-peer probe on that leg returns `opponent_unresponsive` |
| 7 | **#10 / 05-16** The turn loop marks every bounded attempt — **now with no exception** | ✓ VERIFIED, strengthened | `grep -rn "next_protocol_message(" src/` → 5 production calls, **5/5 pass `on_attempt=ctx.watchdog.touch`**. 05-18 closed the last bare one (`turn_commit.py:103`), which 05-16 had missed |
| 8 | **G8a** One inbound hint decoded at most once; `pending_hints` has a production reader | ✓ VERIFIED (regression) | `turn_hint_buffer.py:150` `is_replay`; `turn_language_io.py:73` `consume_hint` |
| 9 | **G8b** Both hint branches stamp the turn actually played | ✓ VERIFIED (regression) | `turn_actions.py:92`; deferred #13 is the MOVE envelope on the same toggle, separately logged and re-confirmed latent |
| 10 | **G10a** Dead `declare_truthfully` removed | ✓ VERIFIED (regression) | `grep -rn declare_truthfully src/` → only `deception.py:22`/`:25`, both prose |
| 11 | **G10b** Capture Claim on the EXISTING `GAME_OVER` envelope, driven by the resolved outcome | ✓ VERIFIED | `orchestrator.py:154` `await send_capture_declaration(ctx, turn=ctx.state.turn, outcome=outcome)` — no policy, no LLM (rule 22 by construction) |
| 12 | **G10c** BARRIER/CAPTURE branches **reserved**, under the gap clause's own second option | ✓ VERIFIED (regression) | 05-UAT.md's `missing` reads "remove **(or explicitly reserve)**". `ALWAYS_TRUE_KINDS` is the rule-16 guard and `BANK` is a total map; deleting them makes `DeceptionPlan(LIE, BARRIER)` constructible and puts a `KeyError` inside `bluff.compose()` |
| 13 | **Rules 16/22** — this phase introduced no false-accusation path, and **removed three** | ✓ VERIFIED | 05-15 removed one in `receive_final_reveal`; 05-17 removed the manufactured-silence one; 05-18 removed the initiator's. Held across the **108-cell** matrix: every accusation any pull site writes is a `TechnicalWinReason` member, never a decoder's string |
| 14 | **Rule 38** — no fabricated numbers; the gate record is honest | ✓ VERIFIED, with two corrections | GATE-5-MEASUREMENT.md records four attempts including the two FAILED ones and de-claims attempt 4's second game as a deterministic transport re-run; `NEEDED-FROM-MACHINE-B.md` keeps the missing `consoleB_attempt4.txt` as an open `- [ ]`. Corrections: finding **F1** (a docstring over-claim) and finding **F4** |
| 15 | **Phase 6 does not regress** | ✓ VERIFIED | `uv run python scripts/measure_gate6.py` → `criterion_1..3: PASS`, exit 0 |
| 16 | The knowledge graph was refreshed after this phase's code landed | ✓ VERIFIED | `graph.json` mtime 2026-08-17 01:56, 8042 nodes, carries `turn_commit_wait_reveal`, `wait_for_reveal_capturing_early_ack`, `_pull_site_discovery`, `test_envelope_boundary_invariant`, `late_peer_gate`. See **F5** on the REPORT vs the graph |
| 17 | **The standing Table-5 quality gate is green** | ✓ **VERIFIED — was the previous pass's gap 1** | `1539 passed in 185.05s`, **0 failed**, `Total coverage: 96.64%`; ruff `All checks passed!`; `check_line_limit.sh` exit 0; `check_no_llm_in_strategy.py` OK |
| 18 | **05-17** An early peer FINAL_REVEAL is buffered, never eaten | ✓ VERIFIED | `turn_commit_pull.py:111` `record_final_reveal` (inside the primitive all 5 legs call) → `agent_audit_exchange.py:142` `take_final_reveal`. Production-wired on both ends |
| 19 | **05-18** The initiator's own wait has the type discipline every other leg has | ✓ VERIFIED | `turn_commit.py:159` → the SHARED `wait_for_reveal_capturing_early_ack(ctx, None)`. Probe A (revert) → 4 failures including the literal `ProcessKilledError: NET-07 fired` |
| 20 | **05-18** The envelope-boundary **class** is pinned by a guard that cannot pass vacuously | ✓ VERIFIED | AST enumeration read line-by-line; 12 sites; five vacuity probes I ran myself all fire — below. Scope measured complete (**F2**). One documentation over-claim (**F1**) |
| 21 | **The phase's trackers describe what the repo contains** | ✗ **NOT YET** | Bookkeeping, unchanged by design, held for this pass. Earned rows enumerated below |

**Score: 20/21 truths verified.** The single open item is a tracker tick the user explicitly
reserved. **No code gap remains, and both §10.4 criteria carry measured evidence.**

---

## §10.4 criterion 2 — re-derived from the raw JSONL, again, by my own script

I read `docs/phases/phase-5/remote-round-2026-08-16-attempt4/` directly. My first pass keyed
on `kind` and returned all-zeros; the real key is `event`, so the corrected derivation is
below. (Recording that mis-key matters: a silent all-zero table is exactly how a vacuous
"zero technical_win" gets believed.)

```
side             stem                 n game_over matched tw wd ai ill uid singleton led decl
---------------------------------------------------------------------------------------------
machineA-police  b22361aa93ccf310    50 ['capture'] [True]  0  0  0   1 True          True True
machineA-police  d265603c116a9f99    50 ['capture'] [True]  0  0  0   1 True          True True
machineB-thief   b22361aa93ccf310    49 ['capture'] [True]  0  0  0   1 True          True True
machineB-thief   d265603c116a9f99    49 ['capture'] [True]  0  0  0   1 True          True True
machineB-thief   eb55daeefafb4208     1 []          []      0  1  0   0 True          False True
```

**The audit is non-vacuous, which is the check `all_matched([])` exists to defeat:**

```
machineA-police  b22361aa93ccf310 peer_audit turns=6 all_matched=True  self_audit turns=6 all_matched=True
machineA-police  d265603c116a9f99 peer_audit turns=6 all_matched=True  self_audit turns=6 all_matched=True
machineB-thief   b22361aa93ccf310 peer_audit turns=6 all_matched=True  self_audit turns=6 all_matched=True
machineB-thief   d265603c116a9f99 peer_audit turns=6 all_matched=True  self_audit turns=6 all_matched=True
ledgers: 6 records each, all four
```

**Cross-signed declarations, byte-compared:**

```
b22361aa93ccf310: A.own == B.peer -> True ; B.own == A.peer -> True
d265603c116a9f99: A.own == B.peer -> True ; B.own == A.peer -> True
```

**The declaration is honest and complete** — exactly the ten `DeclarationField` keys, HMAC'd,
`signed: true`:

```
llm_name: claude-haiku-4-5     team_code: khm-mn17     code_version: 1.00
games_played_so_far: 991       commit_hash: 0632e04e364984452ae7b5477c698f379b07e9ef
```

Every log's `game_uid` set is a **singleton equal to its own filename stem**, on both sides of
both games — the artifact-join failure that sank attempt 1 does not recur. Two residuals, both
already recorded by the phase and neither a criterion failure: the 1-record pre-game
`eb55daeefafb4208.jsonl` (a `watchdog_incident`, retained deliberately under "Extras retained
for honesty"), and the uncaptured `consoleB_attempt4.txt`, kept as an open `- [ ]`.

---

## The skeptical checks I was asked to run

### 1. The class guard — is it really source-enumerated, and can it fail?

**It reads the sites out of the source.** `tests/unit/_pull_site_discovery.py` is a genuine
two-stage `ast` walk over `src/pursuit/network/*.py`: SEED = a top-level function whose body
(nested closures included) touches a `.queue` attribute or calls `.get`/`.get_nowait` on a
name containing `queue`; CLOSURE = iterated to a fixpoint over callers of a set member whose
**return annotation mentions `Envelope`**. No hand-typed list anywhere in the module.

**Twelve sites, run by me:**

```
await_and_respond                     turn_commit.py
await_move                            turn_buffer.py
await_opponent_turn                   turn_actions.py
drain_trailing_hint                   turn_buffer.py
linger_for_peer                       agent_teardown.py
next_protocol_message                 turn_commit_pull.py
receive_final_reveal                  agent_audit_exchange.py
wait_for_ack_and_commit               turn_commit_wait.py
wait_for_matching_ack                 turn_commit_wait.py
wait_for_opponent                     deadline_wait.py
wait_for_opponent_commit              turn_commit_wait.py
wait_for_reveal_capturing_early_ack   turn_commit_wait_reveal.py
```

**It fails loudly on an empty enumeration — it does not skip.** There is no `parametrize`
(an empty parameter set is a silent pytest SKIP); the matrix is a plain loop, and
`pull_sites()` raises. Both ways of emptying it, run by me:

```
PROBE B  package path pointed at nothing
  -> AssertionError: ZERO pull sites discovered under does-not-exist-anywhere -- the
     enumeration is vacuous and every case built on it would pass without testing anything
PROBE B2 seed predicate neutered (simulates a rename away from `.queue`)
  -> AssertionError: ZERO pull sites discovered under ...\src\pursuit\network
```

**A new pull site is covered the day it lands** — I dropped one into the package:

```
PROBE C'  src/pursuit/network/_verifier_probe_newpull.py added (one queue.get)
  -> AssertionError: undriven sites ['brand_new_pull_by_the_verifier'], stale drivers []
```

**The exemption is live, not a blanket** — I removed deferred #17's exemption:

```
PROBE D  "linger_for_peer" removed from _LEDGER_EXEMPT
  -> AssertionError: linger_for_peer(agent_teardown.py) <- final_reveal:
     the peer's published ledger was destroyed
```

**The positive count is falsifiable** — `not breaches` alone would pass over a matrix that
never ran:

```
PROBE E  `kept` forced True at the probe
  -> AssertionError: 12 sites kept the ledger, expected 12 discovered minus 1 exempt
```

**The fix it guards is load-bearing** — I reverted 05-18 Task 2 in shipped source
(`turn_commit.py:159` back to a bare `next_protocol_message(ctx)`):

```
PROBE A  4 failed, 3 passed
  FAILED test_envelope_boundary_invariant.py::test_no_pull_site_mishandles_any_envelope_type
  FAILED test_early_final_reveal_police.py::test_an_honest_peers_ledger_is_not_read_as_an_illegal_move
  FAILED test_early_final_reveal_police.py::test_a_peer_that_publishes_and_then_stops_is_accused_of_what_it_did
  FAILED test_early_final_reveal_police.py::test_the_initiators_own_wait_marks_its_ladder_like_every_other_leg
  E  ProcessKilledError: NET-07 fired: os._exit(1) would have run here
```

The three that still pass include rule 36's counter-control — which is exactly what makes it
a control and not a consequence of the fix. **Source restored; `git status --porcelain` empty
after every probe.**

**Where the documentation over-claims (finding F1).** The module docstring says all five
historical instances sit inside the discovered set. **Three do** — 05-15
(`receive_final_reveal`), 05-17 (`next_protocol_message` and the wait legs), #18
(`await_and_respond`). **05-09 does not and cannot**: its own SUMMARY `key-files` lists
`src/pursuit/network/deadline.py`, and the defect was an exception taxonomy on the
**outbound** `call_with_retry` ladder — not a queue pull, so no pull-site enumeration can
contain it. **05-10 is partial**: it modified `src/pursuit/security/audit.py` and
`deadline.py`; its peer-data fault is *reached through* `receive_final_reveal` (in the set),
but the mishandling function is not. This changes nothing about the guard's real coverage,
which I measured and which is **complete for the class it names** (finding F2):

```
grep -rn "\.queue\b|get_nowait" src/ --include=*.py   outside src/pursuit/network/*.py -> 0 hits
find src/pursuit/network -type d                       -> no subpackages
```

### 2. Rule 36 — is a genuinely silent peer still accused?

**Yes, on every surface this round touched, on both roles.** I drove the production functions
against an empty queue myself rather than reading the guard tests:

```
[turn loop / police] queue EMPTY -> outcome=Outcome.TECHNICAL_LOSS accusations=['opponent_unresponsive']
[turn loop / thief ] queue EMPTY -> outcome=Outcome.TECHNICAL_LOSS accusations=['opponent_unresponsive']
[shared tail leg h_commit=None] verdict.reason=opponent_unresponsive attempts=2 elapsed=0.14
[shared tail leg h_commit=str ] verdict.reason=opponent_unresponsive
[audit receive leg]             verdict.reason=opponent_unresponsive
[await_and_respond police]      verdict.reason=opponent_unresponsive
```

Note `attempts=2 elapsed=0.14`: the verdict carries **measured** fields, not the
`attempts=0, elapsed=0.0` fabrication `TechnicalWin`'s own docstring forbids. The single
production constructor is `deadline.py:158-166`, reached only after the ladder is exhausted;
`agent_audit_wiring.py:88-97` still discriminates on `send_verdict is not None`, so a push
that **landed** keeps the sanction. Nothing this round softened it.

### 3. Production callers — test-only reachability proves nothing

| Symbol | Production caller | Chain |
|---|---|---|
| `record_final_reveal` (05-17) | `turn_commit_pull.py:111`, inside `next_protocol_message` | the primitive every wait leg and the audit call. **Wired** |
| `take_final_reveal` (05-17) | `agent_audit_exchange.py:142` | ← `receive_final_reveal` ← `run_final_audit` ← `agent_entrypoint.py`. **Wired** |
| `ctx.commit_state.early_final_reveal` | written `final_reveal_buffer.py:53`, read `:67` and `agent_audit_exchange.py:142` | reader and writer both production. **Wired** |
| `wait_for_reveal_capturing_early_ack` (05-18) | `turn_commit.py:159` (police, `h_commit=None`) **and** `:207` (thief) | ← `await_and_respond` ← `await_opponent_turn` ← `run_turn_loop`. **Wired, both roles** |
| the `on_attempt` hooks | `turn_commit_wait.py:94, :124, :146`; `turn_commit_wait_reveal.py:68`; `agent_audit_exchange.py:145` | **5 of 5** production calls of `next_protocol_message` pass `on_attempt=ctx.watchdog.touch`; zero bare callers remain |
| `send_capture_declaration` (05-15) | `orchestrator.py:154` | inside the resolved-outcome branch, sharing one `outcome` and one `ctx.state.turn`. **Wired** |

### 4. Deferred items — does any block the phase goal or §10.4?

**No. I verified rather than inherited this, and the orchestrator's reading is confirmed.**

| Item | Blocks goal? | Blocks §10.4? | What I measured |
|---|---|---|---|
| **#13** toggle-off MOVE turn stamp | No | No | Latent, re-verified by reading both shipped files: `config/police/security.json` and `config/thief/security.json` each carry `"commit_reveal": true`. Damage is confined to what a JSONL replay says the peer claimed; the receiver keys on `ctx.state.turn` |
| **#16** the linger's quiet-interval derivation | No | No | A real arithmetic/prose defect (retry scheduled one backoff from the peer's own FAILURE, up to one `response_timeout` after our observed ARRIVAL). But the window it *does* cover sufficed over a real tunnel: attempt 4 shows **0 watchdog_incident, 0 technical_win, 0 audit_incomplete** on both sides of both counted games. Game-end synchronisation, not a criterion |
| **#17** the linger discards a peer FINAL_REVEAL unaudited | No | No | Fires **after** `run_final_audit` has returned, so it cannot change our verdict or manufacture an accusation — evidence retention (rule 20), not correctness. Named as the guard's one exemption, and **probe D proves the exempted check is live**, so the item is real and not a laundered blind spot |
| **#19** `await_move` has no type test | No | No | Same latency premise as #13, verified from the same two shipped files. Its reachability note is honest: with the toggle off the reachable foreign types are HANDSHAKE and GAME_OVER, and `game_over` is a published tool — but the toggle ships `true`, so a league game does not run that path |
| **#20** three files at the gate | No | No | `check_line_limit.sh` exit **0** tree-wide **and** on all nine near-gate files named explicitly by path (the tree-wide form enumerates via `git ls-files`, so I checked by path too) |
| **#14 / #15 / #2 / #3 / #5 / #6 / #8 / #9 / #11 / #12** | No | No | Carried forward; `agent_audit_exchange.py:145` re-read, `check_line_limit.sh` re-run |

---

## Previous gap 1 — closed, and closed the way the item required

**The gate is green, measured from scratch:**

```
1539 passed in 185.05s (0:03:05)
Required test coverage of 85.0% reached. Total coverage: 96.64%
```

**The previously-failing control, file alone, six consecutive runs:**

```
--- late-peer run 1 --- 2 passed in 37.82s
--- late-peer run 2 --- 2 passed in 36.99s
--- late-peer run 3 --- 2 passed in 37.49s
--- late-peer run 4 --- 2 passed in 37.93s
--- late-peer run 5 --- 2 passed in 37.04s
--- late-peer run 6 --- 2 passed in 38.13s
```

Every run at ~37 s — the deferred item's own *pass* signature (a passing control makes B's
cut-off push walk the full ~12 s retry ladder; a failing one returns instantly at ~26 s). The
wall clock corroborates the outcome rather than merely accompanying it.

**And the pair is mutation-sensitive in BOTH directions — I ran both myself:**

```
M1  `return` inserted as the first statement of linger_for_peer (production)
    -> FAILED test_a_late_peer_still_completes_against_a_torn_down_peer   2/2, control still passes
M2  the linger=False branch given the linger=True ordering (harness)
    -> FAILED test_without_the_linger_the_late_peers_own_push_is_cut_off  2/2, positive still passes
```

M1 says the linger is load-bearing in the product. M2 says the control's pass comes from the
**absence of the grace window**, not from the gate's mere presence. Files restored; tree clean.

**The fix respected the item's two prohibitions.** No timing constant was widened and no
assertion relaxed: `git diff --name-only ff4ac93 3babfe6 | grep ^src/` returns **0 files** —
production untouched — and the repair is a one-shot inbound gate
(`tests/integration/late_peer_gate.py`) that monkeypatches the *instance* attribute
`ctx.runtime.queue.put`, turning "A's listener closed while B's push was in flight" into a
fact of program order. `_LATE_SECONDS`, `_RESPONSE_TIMEOUT`, `_BACKOFF_SECONDS` and every
`config/*/network.json` field are unchanged.

---

## Standing gates — all re-run fresh this pass, at HEAD `26204d8`

| Gate | Result |
|---|---|
| `uv run pytest tests/ --cov` | **1539 passed, 0 failed**, 96.64%, 185.05 s |
| `uv run ruff check .` | **All checks passed!** |
| `bash scripts/check_line_limit.sh` | exit **0** tree-wide; exit **0** again on 9 near-gate files by explicit path |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports` |
| `uv run python scripts/measure_gate6.py` | criteria 1, 2, 3 → **PASS**; exit 0 (regeneration reverted, see F3) |
| `uv run python scripts/dev_launch.py` | exit **0**; police+thief share stem `afa6aa3840d63e88`, both `game_over=capture`, both `audit_verdict matched=True`, **0** technical_win / watchdog_incident / audit_incomplete |
| Secret scan over `src/ config/ scripts/` | **0 literal secrets**; `.env` untracked (`git ls-files --error-unmatch .env` → *did not match*); `.env-example` present |
| Anti-pattern scan, all 21 files changed since `ff4ac93` | **0** TODO/FIXME/XXX/HACK/stub shapes. The only `PLACEHOLDER` hits are two prose references to the real constant `PLACEHOLDER_HINT_TEXT` in `turn_buffer.py` |
| Tree state | `git status --porcelain` **empty** at start, after each of the 8 probes, and at finish |

`dev_launch` note, measured: the thief's log carries **one** pre-adoption record (index 0,
`illegal_transition`) under its own uid before `adopt_negotiated_game_id` relocates the log;
every record from index 1 onward carries the negotiated uid, and the filename, ledger and
declaration all use it. That is 05-05's adoption working, not a stray uid inside the audited
window.

---

## Earned tracker rows — the trackers ARE now closable

The three trackers below are the last open item, and **every row is earned by measured
evidence**. I have not edited them; the user reserved the tick.

**`docs/phases/phase-5/TODO.md` — seven rows, ☐ → ☑:**

| Row | Earned by |
|---|---|
| 05-12 (G9+G7) | truths 3, 4 — both validators production-wired and probed |
| 05-13 (G6) | truths 5, 6 — per-attempt marking at `agent_audit_exchange.py:87`/`:145`; rule 36 measured intact |
| 05-14 (G8) | truths 8, 9 — `is_replay` + the `consume_hint` production reader |
| 05-15 (G10) | truths 10, 11, 12 — `declare_truthfully` gone; Capture Claim at `orchestrator.py:154`; the reserve option is the gap clause's own second option |
| 05-16 (#10) | truth 7 — and now **stronger** than when the row was written: 5/5 production callers marked, zero bare |
| 05-17 | truth 18 — buffer written at `turn_commit_pull.py:111`, read at `agent_audit_exchange.py:142` |
| 05-18 | truths 19, 20 — probe A reverts the fix and 4 tests fail; five vacuity probes on the guard all fire |

**`docs/TODO.md`:** row **05-99** ☐ → ☑, and its Phase-5 header should carry a GATE-5-MET
banner — measured: the Phase-3 and Phase-6 headers carry one, Phase 5 does not, though its
own phase TODO already says **GATE-5 MET**.

**`.planning/REQUIREMENTS.md`:** **CLOUD-01** (line 59) and **CLOUD-02** (line 60) `- [ ]` →
`- [x]`. CLOUD-01 is earned by truth 1, CLOUD-02 by truth 2.

**One caution, unchanged from the previous pass and re-measured:** the traceability table at
`.planning/REQUIREMENTS.md:179-188` reads `Pending` for **all ten** rows — including Phase 3
and Phase 6, whose gates `docs/TODO.md` itself banners as met. That is repo-wide rot. Fix the
table as a whole or leave it; ticking only the Phase-5 row would misdescribe the repository
in the other direction.

---

## Requirements Coverage

| Requirement | Status | Blocking issue |
|---|---|---|
| CLOUD-01 — each peer reachable via tunnel | ✓ SATISFIED | None. Checkbox tick pending (human item 1) |
| CLOUD-02 — a remote agent plays a full round | ✓ SATISFIED | None. Checkbox tick pending (human item 1) |
| DOC-01 — the phase triplet exists and its TODOs are checked | ◐ PENDING THE TICK | Triplet exists (`docs/phases/phase-5/{PRD,PLAN,TODO}.md`); seven rows await the tick |

## Anti-Patterns / Findings

| Where | Severity | Finding |
|---|---|---|
| `tests/unit/_pull_site_discovery.py:33-34`, `test_envelope_boundary_invariant.py:3-5` | ⚠️ Warning (documentation) | **F1** — "every one of the five historical instances sits inside the set" is true of **three**, partial for 05-10, and false for 05-09 (an outbound exception-taxonomy defect in `deadline.py`, structurally outside any pull-site enumeration). The guard's real coverage is unaffected; the class narrative overstates. Worth a dated correction in the two docstrings, in this repo's own style |
| `src/pursuit/network/` | ℹ️ Info (good) | **F2** — the non-recursive glob is nonetheless **complete**: zero queue reads exist anywhere else under `src/`, and the package has no subdirectories |
| `docs/phases/phase-6/gate6_measurement_evidence.json` | ℹ️ Info | **F3** — still predates 05-15; a fresh run gives the same three PASSes plus exactly the delta 05-15 predicted. One-command follow-up; I reverted my regeneration |
| attempt-4 logs (all four counted) | ℹ️ Info | **F4** — one `illegal_transition handshake -> handshake`, `severity: recoverable`, turn 0, per log. Reproduced locally by `measure_gate6.py` and `dev_launch.py`, so it is the benign two-directional-handshake artifact, not an attempt-4 anomaly |
| `.planning/graphs/GRAPH_REPORT.md` | ℹ️ Info | **F5** — omits the 05-18 symbols, but so does it omit `turn_commit_wait`, `turn_commit_pull`, `agent_teardown` and `turn_buffer`. The REPORT is a narrative; `graph.json` is the queryable artifact and it is current |
| 05-17's probe P2 | ℹ️ Info | **F6** — read, not re-run. Corroborating, not load-bearing; the fix is independently proven by probe A and the 108-cell matrix |
| All 21 files changed since `ff4ac93` | — | Zero TODO/FIXME/XXX/HACK/PLACEHOLDER stub markers, zero stub shapes |

## Summary

**The phase goal is achieved and both §10.4 criteria hold on evidence that survived a third
independent re-derivation.** Criterion 1 has a real smoke run against a real ngrok domain with
the 403 negative case; criterion 2 has two complete games across two machines on two networks,
each with a singleton uid spanning log, ledger and declaration on both sides, agreeing
`capture` outcomes, **six-turn** peer *and* self audits all matched (not the vacuous
`all_matched([])`), byte-identical cross-signed declarations in both directions, and a live
`claude-haiku-4-5` declared. Understating that would be its own misreport.

**The previous pass's gap 1 is genuinely closed, not papered over.** The gate is green at
1539/0 and 96.64%, the control runs 6/6 clean at the wall-clock signature that corroborates
its outcome, and it is now mutation-sensitive in **both** directions — where before it was a
coin flip that proved nothing. The repair moved no number and touched no production file, the
two things deferred item #4 forbade.

**The load-bearing new claim holds up.** The class guard enumerates from source, raises rather
than skipping on an empty set, fails on a pull function I invented and dropped into the
package, fails when its one exemption is removed, fails when its `kept` flag is forced, and
fails the fix it guards when I revert it. Its scope covers 100% of the codebase's queue
surface. Its only defect is a docstring that claims two more ancestors than it can contain.

**Rule 36 was not softened by any of this round's non-accusation work.** I measured a
genuinely silent peer earning `technical_win{opponent_unresponsive}` on six production
surfaces across both roles, with the verdict's `attempts` and `elapsed_seconds` actually
measured rather than defaulted.

**None of the five open deferred items blocks the goal or either criterion**, and I verified
that from the shipped config files and from the attempt-4 evidence rather than inheriting it.
#13 and #19 are latent on `commit_reveal=False` while both shipped `security.json` files carry
`true`; #16 and #17 are game-end synchronisation and evidence-retention questions that fire
after the verdict is already recorded; #20 is structural and the gate exits 0.

**What is left is one tick.** The trackers are stale as a matter of fact, and closable as a
matter of evidence. The seven phase-TODO rows, `docs/TODO.md` row 05-99 and its Phase-5
banner, and `REQUIREMENTS.md` CLOUD-01/CLOUD-02 are all earned. **GATE-5 is MET.**

---

*Verified: 2026-08-17 at HEAD `26204d8`*
*Supersedes: `05-VERIFICATION-2026-08-16-superseded.md` (preserved), which supersedes*
*`05-VERIFICATION-2026-08-14-superseded.md` (preserved). Append-only, rule 38.*
*Verifier: Claude (gsd-verifier)*
