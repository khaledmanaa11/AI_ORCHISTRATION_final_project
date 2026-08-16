# Phase 7 Plan Outline — Reporting and Visualization Shell

**Phase:** `07-reporting-and-visualization-shell` · **Written:** 2026-08-17 · **Plans:** 07-01 … 07-10
**Context:** [`07-CONTEXT.md`](07-CONTEXT.md)
**Requirements:** REPORT-01 … REPORT-09
**Gate:** §10.4 milestone 7 — *(1) a game summary is sent by mail (send-only OAuth, through the
gatekeeper; attached JSON, never free text); (2) the live GUI displays state — only local truth,
never the full objective board; (3) the replay app reconstructs a recorded round and shows
`Verified OK`.*

**All plans are subject to the standing gates, not restated per plan:** `ruff check` → 0 ·
`pytest --cov` ≥ 85% · every file ≤ 150 code lines · `uv` only · zero invented numbers · zero
secrets in source · tests offline (no live Google API, no real OAuth, no opponent, no network).

This phase is **assembly plus one new external dependency**. Almost every input already exists:
the gatekeeper (Phase 4), canonical JSON + SHA-256 + the nonce ledger (Phase 6), the
wire-mirroring JSONL log (Phase 2), the negotiated `game_id` (D-61), the Step-0 declaration
artifact (Phase 6), the peer's `GAME_OVER` outcome claim on the wire (05-15), and
`TokenBudget.report()` (Phase 4). What Phase 7 adds is the **outward face** over them.

---

## 1. The structural decision — human-gated work is exactly one plan, last

`07-CONTEXT.md` locks `reporting.mode = dry_run | live`. In `dry_run` the report is written to
disk as `.json` + `.eml` instead of sent. That toggle is what makes the phase autonomous:
**the entire reporting stack — gatekeeper chain, four artifacts, token accounting, signing,
retry/429 backoff, attachment shaping — is built and measured against `dry_run` with an injected
fake Google client, with zero OAuth.**

Exactly two things genuinely need a human, and they live only in **07-10 (`autonomous: false`)**:

1. clicking through Google's OAuth consent screen and authorising the send-only client;
2. the one **live** send that proves §10.4 criterion 1 end to end.

Claude must not enter credentials and must not click consent. 07-10 is therefore a short,
scripted checkpoint with a pre-written runbook, following the GATE-4 live-run / GATE-5
remote-round precedent.

**The GUI needs judgement but not credentials.** Its acceptance splits:

| GUI acceptance | Kind | Owned by |
|---|---|---|
| Renders without exception; a scripted launch exits 0 | machine-checkable | 07-06 |
| Shows only local truth — no opponent true cell reachable by the view | machine-checkable (the D-74 firewall test) | 07-03, 07-06 |
| Replay shows `Verified OK` on a clean log and `FAILED` on a tampered one | machine-checkable | 07-08 |
| **Presentation-grade screenshot for the README** (§9.4.2 item 5, rule 42) | **human aesthetic call** | 07-10 |

Only the last row is a human judgement, and it is bundled into 07-10 so no other plan stalls on
a person.

---

## 2. Decisions — D-68 … D-75

New this phase (highest existing decision is D-67). Resolved under the autonomy directive from
the book extracts + what is already in the tree. The CONTEXT decisions (Tkinter, full local
dashboard, step-through replay + verdict banner, personal Gmail with `gmail.send`,
`reporting.mode`, queue-and-retry on failure) are locked and not re-derived.

| ID | Decision | Source |
|----|----------|--------|
| **D-68** | **One gatekeeper CLASS, two INSTANCES — extend, never duplicate.** `Gatekeeper.__init__` today demands `params: LanguageParams` and always builds a `TokenBudget`. Extract the seven Table-19 rows into a frozen `GatekeeperParams` that both `LanguageParams` and the new `ReportingParams` satisfy, and make `budget` an **injected optional** (`None` for the mail instance). `CallResult`'s own docstring already anticipates this — *"a call with no concept of tokens (Phase 7 Gmail) passes 0 for both"*. `load_language_config()`'s public return type does not change. | `gatekeeper.py:5-6,51-65`; SEGAL §4 "build **one** gatekeeper" |
| **D-69** | **The Fig-13 chain is three composable stages around the existing `submit()`**, in the book's order: `QuotaManager` (daily send ceiling, durable across process restarts) → `TokenBucket` (already shipped, `bucket.py`, unchanged) → `DosDetector` (latching lock on a runaway send loop) → Gmail API. Quota and DOS are **pre-call gates and post-call observers**; the bucket stays inside `submit()`. Rejection shapes reuse `GatekeeperOverflow`'s contract: never a crash, always a caller-handled outcome. | PROJECT_GUIDE §G / book §9.3.1 Fig 13; rules 28-29 |
| **D-70** | **The send sink is injected behind a `MailSink` protocol.** `DryRunSink` writes `.json` + `.eml` under the artifacts dir; `GmailSink` is the only module that imports `google-*`, isolated exactly as `anthropic_provider.py` isolates the LLM vendor SDK. `reporting.mode` selects the sink at wiring time; dev/test configs ship `dry_run`, league configs ship `live`. No test constructs `GmailSink` against a real credential. | 07-CONTEXT "Gmail & reporting safety"; `services/llm/anthropic_provider.py` precedent |
| **D-71** | **`declaration_<game_id>.json` is WRAPPED, not extended.** The signed Step-0 payload is frozen by D-62/D-63 and its SHA-256 digest is compared at handshake (`handshake_evaluate.py`); adding a field to it aborts every game with `STEP0_MISMATCH`. Phase 7 therefore embeds the own + peer signed payloads **verbatim** and adds PARAMETERS' remaining declaration content (repo URLs, MCP server addresses, agreed token ceiling, start/end times) **outside** the signed envelope. | PARAMETERS §"Required JSON artifacts"; `agent_step0_wiring.write_declaration` |
| **D-72** | **`<NN>` is a per-`game_id` sub-game index, `01`-based, zero-padded to two digits — and is NOT the rule-37 `games_played.json` counter.** The lifetime counter answers "how many games has this team played ever" (rule 37); `<NN>` answers "which sub-game of this series is this". Conflating them would put a five-digit number in a two-digit filename slot and would couple a filename to a disqualification-bearing declaration. Structural only, no numeric parameter. | PARAMETERS "match number `<NN>`", rule 52; `step0_collect.read_games_played` |
| **D-73** | **`log_<game_id>_g<NN>.json` is DERIVED at game end** by joining the wire-mirroring JSONL (`logs/<role>/<game_uid>.jsonl`) with the sibling nonce ledger (`<game_uid>.ledger.jsonl`). Neither source file changes: D-64's nonce separation holds *during play*, and the nonces are public *after* game end by SEC-04. The join key is **local turn truth**, never a peer-declared `envelope.turn` — that exact mistake was 06-05's blocker. | `event_log.py`, `security/ledger.py`, 06-05 gap 1 |
| **D-74** | **The rules 8-9 firewall is a `LocalView` read model in the SDK/services layer, not in `gui/`.** `ctx.state` legitimately carries the engine's true joint position on every agent process (`turn_language.py:121-122` says so in as many words), so "don't import the engine" is **not** sufficient — the leak is a *field read*, not an import. `LocalView`'s field set structurally cannot represent an opponent cell (belief grid + scent + own position + declared barriers + hint log + turn/state/timer, nothing else). It lives outside `gui/` because `pyproject.toml` omits `*/gui/*` from coverage: redaction logic inside `gui/` would be invisible to the coverage gate. | rules 8-9; `pyproject.toml [tool.coverage.run] omit`; `turn_language.py:121-122` |
| **D-75** | **Rule 35's "agree the result with the opponent" needs NO new message type.** The agreed result is derived from three things already present: this side's resolved `Outcome`, the peer's `GAME_OVER` claim (05-15 `capture_declaration`), and the Phase-6 mutual audit verdict. `result_` records `own_outcome`, `peer_outcome`, `audit_verdict` and a computed `agreed: bool`. A disagreement is **reported as a disagreement** — never smoothed, never defaulted to agreement (rules 16/22/38). | rules 35-36; `capture_declaration.py`, `agent_audit_verdict.py` |

**Not in scope:** the repo split, the academic README and league play (Phase 8 — this phase
produces the screenshots and the report that Phase 8 attaches); any change to the frozen
`Envelope` shape, to the commit-reveal payload, to the Step-0 signed field set, or to Phase-3/4
strategy and language behaviour.

---

## 3. Numbers — what is sourced, and what is genuinely missing

| Value | Number | Status | Source |
|---|---|---|---|
| Mail bucket capacity `C` / refill `r` | derived from `requests_per_minute` = 30 | **reused** | PARAMETERS Table 19 row 1 (minimum), same derivation `Gatekeeper` already documents |
| Parallel mail sends | 2 | **reused** | Table 19 row 2 (minimum) |
| Backoff before a retry (incl. HTTP 429) | 5 s | **reused** | Table 19 row 3 (minimum) |
| Retries before failure | 3 | **reused** | Table 19 row 4 (minimum) |
| Send queue depth | 100 | **reused** | Table 19 row 5 (minimum) |
| Response timeout | 30 s | **reused** | Table 19 row 6 (negotiable) |
| Reporting address | `rmisegal+uoh26finalgame@gmail.com` | **fixed** | PARAMETERS §Addresses — the single mandatory destination |
| OAuth scope | `gmail.send` | **spec-locked** | rule 30 |
| Artifact names | `declaration_` / `config_` / `log_` / `result_` | **spec-locked** | PARAMETERS §Required JSON artifacts |
| **Quota Manager daily send ceiling** | — | **MISSING** | see OQ-1 |
| **DOS detector trip threshold + lock duration** | — | **MISSING** | see OQ-2 |

`reporting.json` introduces **no book number**. It re-declares the Table-19 rows (so the mail
gatekeeper is configured, not hardcoded — SEGAL §4) and adds structural strings (`mode`,
recipient, artifact directory, credential/token **env-var names**).

---

## 4. Open questions — flagged, never invented

**OQ-1 — the Quota Manager's daily send ceiling has no value in PARAMETERS.md.**
The book (§9.3.1) defines the stage as "tracks the daily send ceiling"; Table 19 has no daily
row. `docs/SEGAL_GUIDELINES.md` §4 quotes an *hourly* figure (`requests_per_hour: 500`) for the
generic API gatekeeper, and instructs "where the two documents differ, take the stricter value".
**Proposed resolution, to confirm before 07-01 executes:** carry the ceiling as a `reporting.json`
leaf labelled an *engineering default* under the existing D-18 discipline (the precedent already
used for `watchdog_poll_seconds` and the two degrade thresholds), explicitly **not** presented as
a book value, with SEGAL's 500/hour used where it exists rather than a number being invented.
Not invented silently in any case.

**OQ-2 — the DOS detector's trip threshold and lock duration have no source at all.**
Rule 29 mandates the detector; no document gives it a number. Same proposed treatment as OQ-1
(engineering default, labelled). A cheaper alternative worth weighing at plan time: define the
trip **structurally** — the detector latches when the token bucket has been empty continuously
across `retries_before_failure` + 1 attempts, which introduces no new number at all.

**OQ-3 — `requests_per_minute` vs SEGAL's `concurrent_max: 5` / `retry_after_seconds: 30`.**
Table 19 says parallel ≥ 2 and backoff ≥ 5 s; SEGAL §4 says 5 concurrent and 30 s retry-after.
"Stricter" is unambiguous for concurrency (2 < 5, keep 2) and ambiguous for backoff (a *longer*
wait is stricter on the API, shorter is stricter on us). Needs one line of confirmation before
07-01 sets the mail instance's backoff.

**OQ-4 — one `result_` per series, but one email per game.** PARAMETERS names
`result_<game_id>.json` with **no** `_g<NN>` suffix and calls it "final results summary across
all sub-games", while rule 32 requires an automatic report at the end of **every** game and
PARAMETERS' mandatory-rule 5 requires every game's email to carry its commit hash. Reading taken
for planning: **one file per series, rewritten (durably, `.prev` rotation) after each sub-game,
emailed each time**. Flagged because it is an interpretation, not a quotation.

**OQ-5 — `config/police/games_played.json` currently reads `1881`, and it is the number the
Step-0 declaration puts on the wire and this phase puts in the emailed report.**
`agent_step0_wiring.py:93` increments it once per agent start, so ~1881 dev/test/gate runs are
counted as "games actually played". Rule 37 requires an accurate declaration and **rule 38 makes
a false games-played declaration an absolute disqualification**. This is already logged as a
Phase-6 deferred item ("the counter's correct rule-37 behaviour") but Phase 7 is where the number
leaves the machine. **This needs a human decision, not a Claude decision** — it is a
disqualification-bearing integrity claim. Carried into 07-10's checklist as a blocking item.

---

## 5. Where the code goes

```
src/pursuit/services/llm/
  gatekeeper.py            + GatekeeperParams (extracted), budget becomes injected/optional   (07-01)
src/pursuit/services/reporting/
  quota.py                 QuotaManager -- durable daily ceiling                              (07-01)
  dos.py                   DosDetector -- latching runaway-loop lock                          (07-01)
  chain.py                 the Fig-13 composition around Gatekeeper.submit                    (07-01)
  sink.py                  MailSink protocol + DryRunSink                                     (07-04)
  gmail_sink.py            the ONLY module importing google-*; send-only scope                (07-04)
  message.py               MIME assembly -- attached JSON, empty/boilerplate body (rules 33-34)(07-04)
  artifacts.py             names, <NN>, game_uid join, canonical signing                      (07-02)
  artifact_config.py       config_<game_id>_g<NN>.json writer                                 (07-02)
  artifact_declaration.py  declaration wrapper around the signed Step-0 payloads (D-71)       (07-02)
  artifact_log.py          log_<game_id>_g<NN>.json builder (JSONL x ledger join, D-73)       (07-05)
  artifact_result.py       result_<game_id>.json + per-game/per-series token totals           (07-07)
  end_of_game.py           the single game-end hook                                           (07-07)

src/pursuit/sdk/
  local_view.py            LocalView -- the rules 8-9 read model (D-74)                       (07-03)
  view_builder.py          ctx -> LocalView, the ONLY place that touches ctx.state            (07-03)

src/pursuit/gui/           (coverage-omitted -- must stay a thin shell, zero logic)
  live_app.py              Tk root, after()-driven refresh                                    (07-06)
  live_panels.py           board/heatmap/scent panels                                         (07-06)
  live_sidebar.py          hint log, intent flags, turn/state/timer                           (07-06)
  replay_app.py            file open, step/play/pause, verdict banner                         (07-08)
  replay_panels.py         per-turn rendering (reuses live_panels)                            (07-08)
  widgets.py               shared chrome (extracted at the 2nd copy -- SEGAL "no duplication") (07-06)

src/pursuit/shared/
  reporting_config.py      load_reporting_config + ReportingKey (the four-loader convention)  (07-01)
src/pursuit/services/reporting/
  replay_verify.py         recompute hashes through commit_pack -- NEVER a 2nd serializer     (07-08)

config/{police,thief}/
  reporting.json           mode, recipient, artifact dir, Table-19 rows, env-var NAMES        (07-01)

scripts/
  measure_gate7.py + gate7_*.py   the machine-measurable gate evidence                        (07-09)
  check_local_truth.py            structural import/field gate for gui/ (STRAT-07 mould)      (07-03)

docs/
  PRD_gatekeeper.md               per-mechanism PRD (ROADMAP row 07-04)                       (07-09)
docs/phases/phase-7/
  GATE-7-MEASUREMENT.md           criteria 2-3 measured; criterion 1 dry-run + live evidence  (07-09, 07-10)
  OAUTH-RUNBOOK.md                the human checkpoint, step by step                          (07-09 writes, 07-10 runs)
```

**Splits pre-authorised now, not discovered at commit time.** A Tkinter dashboard and a replay
viewer do not fit one file each: the live GUI is three files plus shared `widgets.py`, the replay
viewer is two plus `replay_verify.py`. The reporting package is nine small modules rather than
three big ones for the same reason. `gatekeeper.py` is at 89 counted lines with room for the
`GatekeeperParams` extraction; `agent_entrypoint.py` is the one existing file this phase edits
that is near the ceiling — 07-07 attaches through a **new** `end_of_game.py` rather than growing
it (the `agent_audit_wiring.py` → `agent_audit_exchange.py` → `agent_audit_verdict.py` precedent).

---

## 6. Plans and waves

```
w1:  07-01 gatekeeper chain      07-02 artifact spine       07-03 LocalView firewall
        |            \                |         \                    |
w2:  07-04 mail transport ------------+          07-05 log_ builder  07-06 live GUI
        |                                            |    \              |
w3:  07-07 end-of-game + result_ -------------------- +     07-08 replay viewer
                          \                                       /
w4:                        07-09 GATE-7 + PRD_gatekeeper + graph refresh
                                            |
w5:                        07-10  *** autonomous: false *** human checkpoint
```

| Plan | Delivers | Wave | Depends on | Auto |
|---|---|---|---|---|
| **07-01** | Gatekeeper chain: `GatekeeperParams` extraction + optional budget, `QuotaManager`, `DosDetector`, `chain.py`, `reporting.json` + loader | 1 | — | yes |
| **07-02** | Artifact spine: naming/`<NN>`/`game_uid` join + canonical signing, `config_<game_id>_g<NN>.json`, the `declaration_` wrapper (D-71) | 1 | — | yes |
| **07-03** | `LocalView` + `view_builder` + the structural local-truth gate script | 1 | — | yes |
| **07-04** | Mail transport: `MailSink`, `DryRunSink`, `GmailSink` (fake-client tested), MIME attachment shaping, 429 backoff, `.env-example` entries | 2 | 07-01, 07-02 | yes |
| **07-05** | `log_<game_id>_g<NN>.json` builder — JSONL × ledger join on local turn truth | 2 | 07-02 | yes |
| **07-06** | Live GUI: Tk shell over `LocalView`, `after()`-driven, headless launch check | 2 | 07-03 | yes |
| **07-07** | End-of-game wiring: `result_<game_id>.json` with per-game + per-series token totals, rule-35 agreement record, send through the chain in `dry_run` | 3 | 07-04, 07-05 | yes |
| **07-08** | Replay viewer: load `log_`, recompute hashes through `commit_pack`, `Verified OK` / `FAILED` banner, step/play/pause | 3 | 07-05, 07-06 | yes |
| **07-09** | GATE-7 measurement of everything machine-checkable + `docs/PRD_gatekeeper.md` + `OAUTH-RUNBOOK.md` + graph refresh (07-96) | 4 | all | yes |
| **07-10** | **Human checkpoint** — OAuth consent + send-only client authorisation, one live send to the reporting address, presentation-grade README screenshots, OQ-5 decision | 5 | 07-09 | **NO** |

07-01/07-02/07-03 are genuinely independent (rate limiting, file shapes, and the read model share
no file), so wave 1 is a real three-way fan-out — run each in its own worktree, per the
parallel-executor rule.

---

## 7. Per-plan objective, files, measurable acceptance, and the trap

Traps are drawn from what is actually in this tree, not from generic advice.

### 07-01 — Gatekeeper chain extension
**Objective:** one gatekeeper class serves both the LLM and the mail path, with the Fig-13 stages
in front of it and every limit read from `reporting.json`.
**Acceptance (measurable):** a mail call with `input_tokens=output_tokens=0` completes without
touching any `TokenBudget`; the LLM instance's degrade ladder is byte-identical to pre-phase
behaviour (existing Phase-4 tests pass unmodified); the bucket admits exactly ⌊C⌋ immediate sends
then blocks, and `time_until_available()` matches `(1-tokens)/r`; quota exhaustion and a latched
DOS lock each return a caller-handled refusal, never an exception out of the turn loop; the daily
quota counter survives a simulated process restart.
**Trap:** `submit()` calls `self.budget.reserve(...)` **unconditionally** (`gatekeeper.py:112`)
and `Gatekeeper.__init__` builds the budget from `LanguageParams`' three budget fields. Making
`budget` optional is a change to the LLM path too — if `reserve()` is skipped or reordered, D-35's
"the degrade level reflects every *queued* call immediately" silently regresses and no existing
test says so. Keep the LLM instance's call order provably identical.

### 07-02 — Artifact spine
**Objective:** the naming, joining and signing rules for all four artifacts in one place, plus the
two artifacts that need no game to produce (`config_`, the `declaration_` wrapper).
**Acceptance:** all four names match PARAMETERS exactly, including `_g<NN>` on `config_`/`log_`
and its absence on `declaration_`/`result_`; every artifact carries the same `game_uid`; the
`config_` artifact round-trips to the same SHA-256 that `config_hash.config_digest` already
computes for `game_params.json` (one serializer, not two); a two-role fixture produces
byte-identical `config_` on both sides.
**Trap:** the Step-0 declaration is **digest-compared at handshake**
(`handshake_evaluate.py:118-125`). Adding a single field to the signed payload makes every game
abort with `STEP0_MISMATCH` and every existing Phase-6 test fail for the "right" reason, which
reads like a broken test suite rather than a broken decision. Wrap, do not extend (D-71).

### 07-03 — `LocalView` firewall
**Objective:** one read model, outside `gui/`, that a view can render without any path to the
opponent's true cell.
**Acceptance — this is the phase's highest-risk item and needs three tests, not one:**
(a) a `GameState` with the opponent at a cell chosen to differ from **every** legitimately
displayed cell (own position, all declared barriers, the belief argmax) is built into a
`LocalView`, and a deep scan of the serialised view finds that cell nowhere;
(b) **counter-control** — the same scan run against a deliberately leaky view MUST fail, and the
test asserts it fails (otherwise (a) is a vacuous pass);
(c) a structural gate script proves no module under `gui/` imports `pursuit.sdk.engine` /
`pursuit.shared.state` or reads `ctx.state`, run in CI like `check_no_llm_in_strategy.sh`.
Plus a revert probe: the three tests must fail against pre-plan code.
**Trap:** every agent process legitimately holds both true positions —
`turn_language.py:121-122` states it outright, and `maybe_resolve` refreshes it each turn. So an
import-boundary check **alone** is not the firewall; a `gui/` module could import nothing
forbidden and still read `ctx.state.thief`. The field-level scan (a)+(b) is the load-bearing test.

### 07-04 — Mail transport
**Objective:** an attached-JSON report leaves through the chain, in `dry_run` to disk and in
`live` through a send-only Gmail client, with 429 handled by backoff.
**Acceptance:** the assembled message has the JSON as an **attachment** and carries no report
content in the body (rules 33-34) — asserted by parsing the MIME back, not by inspecting the
builder; recipient is exactly `rmisegal+uoh26finalgame@gmail.com` and comes from config;
requesting any scope beyond `gmail.send` fails a test; a fake client returning 429 twice then 200
produces exactly two recorded backoff sleeps of the configured length **and** succeeds; a fake
client that always 429s exhausts `retries_before_failure` and queues rather than crashes.
**Trap:** a `DryRunSink` that writes a file and returns success makes every test green whether or
not the live path works — the classic vacuous pass. The 429/backoff and scope tests must run
against the **`GmailSink` with an injected fake transport**, and must assert the injected
`sleep` was called with the configured value (the gatekeeper already injects `sleep` for exactly
this reason — `gatekeeper.py:82`). Also: no `parametrize` list may be built from a glob of
artifact files; an empty list SKIPS silently.

### 07-05 — `log_` replay artifact
**Objective:** one self-contained JSON per sub-game that a third party can verify offline.
**Acceptance:** for a recorded two-peer game, every turn in the artifact carries commitment,
revealed move, intent, hint, verdict, nonce and hash; re-hashing each turn through
`commit_pack.build_commit_payload` reproduces the recorded `h_commit` for 100% of turns; the
artifact is complete without either source file (the viewer never needs the JSONL or the ledger).
**Trap:** joining the wire log to the ledger **on the peer's declared `envelope.turn`** is exactly
the bug 06-05 closed — attacker-controlled keys emptied the audit's coverage intersection. Join on
local turn truth. Second trap: `event_log.append_event` is JSONL with an `os.fsync` per line; a
crash mid-game leaves a partial last line, and a `json.loads` over the whole file will raise —
tolerate a truncated tail explicitly rather than assuming well-formedness.

### 07-06 — Live GUI
**Objective:** a Tk dashboard, one window per agent process, rendering a `LocalView` and nothing
else.
**Acceptance:** a headless/scripted launch constructs every widget and exits 0; the app imports
nothing from `pursuit.network` beyond the `LocalView` provider; a `LocalView` with a `None` belief
map (language layer off) still renders; zero business logic in `gui/` — asserted by the same
structural script as 07-03.
**Trap 1:** `tk.mainloop()` blocks. The agent arms a freeze watchdog whose action is
`os._exit(1)` at `watchdog_threshold_seconds` = 60 (`watchdog.py:57`); blocking the event loop
kills the agent mid-game and the peer then declares us `opponent_unresponsive`. Drive Tk with
`after()` off the turn loop, or run it in a separate process — decide in the plan, not in the
executor.
**Trap 2:** `pyproject.toml` omits `*/gui/*` from coverage. Anything meaningful placed there is
untested *and* invisible to the ≥85% gate; it will look like the gate passed.

### 07-07 — End-of-game reporting and `result_`
**Objective:** at game end, both agents independently write `result_<game_id>.json` and send it.
**Acceptance:** `result_` carries total LLM tokens **for this game AND across the series**
(REPORT-07 / rule 54), fed from `ctx.language.gatekeeper.budget.report()` — with a test proving
the series total exceeds a single game's after two games; it carries `own_outcome`,
`peer_outcome`, `audit_verdict`, `agreed`, and the git commit hash the game ran on (PARAMETERS
mandatory-rule 5); **counter-control pair** — an honest agreeing game records `agreed: true`, and
a fabricated disagreement records `agreed: false` and still emits a report (rule 35 needs the
disagreement *reported*, not suppressed); a send failure leaves the game outcome and the process
exit code unchanged.
**Trap:** `run_agent`'s `finally` calls `stop_runtime(ctx)`, and 06-05 gave the **exit code
meaning** — non-zero now signals an audit mismatch (`main.py`). A reporting failure that returns
non-zero would forge a technical-loss signal. Report inside the window where
`ctx.language.gatekeeper` is still alive, bounded so the total stays under
`watchdog_threshold_seconds`, and never let it touch the outcome or the exit code.

### 07-08 — Replay viewer
**Objective:** load a `log_` artifact, verify it, and show the verdict prominently while stepping
through turns.
**Acceptance:** a clean recorded log → `Verified OK`; a single-bit tamper in any of
`state`/`move`/`intent`/`nonce` → `FAILED`, naming the turn; **an empty or zero-turn log must NOT
show `Verified OK`** — it shows an explicit "nothing to verify" state; the verdict function has at
least one production caller (grep-proven, not test-only).
**Trap:** `all_matched([])` is `True` — an empty records list is the canonical vacuous pass, and
this is the one screen a grader will look at. Second trap: recomputing the hash with a fresh
`json.dumps(sort_keys=True)` instead of going through `commit_pack`/`config_hash.canonical_json`
reintroduces the canonical-JSON drift D-59 exists to prevent, and produces **false `FAILED`
verdicts** — the worst possible failure for this screen.

### 07-09 — GATE-7 measurement + `PRD_gatekeeper.md`
**Objective:** one command, zero credentials, real evidence for everything measurable; the
per-mechanism PRD (ROADMAP row 07-04); the runbook 07-10 will follow.
**Acceptance:** `uv run python scripts/measure_gate7.py` emits a JSON evidence file with an honest
PASS/FAIL per criterion; criterion 1 is reported as **`dry_run` PASS + live PENDING**, never as a
blanket PASS; `docs/PRD_gatekeeper.md` documents the chain, every number, and its source; graph
refreshed (07-96).
**Trap:** `scripts/` is **not** scanned by `check_line_limit.sh` (its default glob is
`src/**` `tests/**` `training/**`). Logic that migrates into a gate script to dodge the 150-line
gate also escapes the coverage gate — the previous gate scripts split into `gate6_*.py` siblings
for real reasons, not to hide code. Second trap: do not let the measurement script import the
`gui/` package at module scope; a headless CI runner without a display would fail the whole gate
for an unrelated reason.

### 07-10 — Human checkpoint · **`autonomous: false`**
**Objective:** the two things Claude must not do, done once, with evidence filed.
**Checklist (human, following `OAUTH-RUNBOOK.md`):**
1. Create the OAuth client restricted to `gmail.send`; complete the consent screen; place the
   credential/token files at the env-var paths named in `reporting.json`. *(Claude must not enter
   credentials or click consent.)*
2. Flip one config to `reporting.mode = live`, run one game, confirm the mail arrives at
   `rmisegal+uoh26finalgame@gmail.com` with the JSON **attached**.
3. Capture the presentation-grade README assets: the live GUI, and the replay viewer showing
   `Verified OK` (§9.4.2 item 5, rule 42).
4. **Decide OQ-5** — what number the Step-0 declaration and the emailed report should carry for
   games played, given `games_played.json` currently reads 1881 and rule 38's sanction is absolute.
**Acceptance:** GATE-7 criterion 1 flips from PENDING to PASS in `GATE-7-MEASUREMENT.md` with the
delivered-message evidence attached; two screenshots committed; OQ-5 resolved in writing.
**Trap:** the temptation to have Claude "just test the credentials" — a single live send from an
unattended run is both a rule-31/39-40 hazard and unsolicited mail to the lecturer. `dry_run` is
the default in every config this repo ships; only 07-10 flips it, and it flips it back.

---

## 8. Decision → plan coverage

| Plan | Owns |
|---|---|
| 07-01 | D-68, D-69 |
| 07-02 | D-71, D-72 |
| 07-03 | D-74 |
| 07-04 | D-70 |
| 07-05 | D-73 |
| 07-06 | D-74 (consumer side) |
| 07-07 | D-75 |
| 07-08 | D-73 (verifier side) |
| 07-09 | — (evidence + docs) |
| 07-10 | — (human evidence) |

## 9. Requirement and §10.4 coverage

| REQ | Landed by |
|---|---|
| REPORT-01 signed JSON report auto-emailed to the fixed address | 07-02, 07-04, 07-07 (dry_run) · 07-10 (live) |
| REPORT-02 Quota Manager → Token Bucket → DOS Detector → Gmail API | 07-01, 07-04 |
| REPORT-03 `tokens ← min(C, tokens + r·Δt)`, send iff `tokens ≥ 1` | 07-01 (existing `bucket.py`, re-proved on the mail path) |
| REPORT-04 HTTP 429 backoff + send-only OAuth scope | 07-04 |
| REPORT-05 attached JSON, never free text | 07-04 |
| REPORT-06 the four artifacts | 07-02 (`declaration_`, `config_`), 07-05 (`log_`), 07-07 (`result_`) |
| REPORT-07 tokens per game and across the series | 07-07 |
| REPORT-08 GUI shows only local truth | 07-03, 07-06 |
| REPORT-09 replay viewer reconstructs and shows `Verified OK` | 07-05, 07-08 |

| §10.4 criterion | Measured by | Human-pending part |
|---|---|---|
| 1 — game summary sent by mail, through the gatekeeper, attached JSON | 07-09 (`dry_run`, end to end, fake client) | the one live send — 07-10 |
| 2 — live GUI displays state, only local truth | 07-09 (renders + firewall tests) | presentation screenshot only — 07-10 |
| 3 — replay app reconstructs a round and shows `Verified OK` | 07-09 (clean → OK, tampered → FAILED, empty → neither) | presentation screenshot only — 07-10 |

## 10. ROADMAP row → plan mapping

ROADMAP rows 07-01…07-04 are deliverable **groups**; this phase needs ten plans to keep every file
under the 150-line gate, so row IDs and plan IDs are not 1:1 here (they were in Phases 4 and 6).

| ROADMAP row | Plans |
|---|---|
| 07-01 Gmail send-only + gatekeeper | 07-01, 07-04 |
| 07-02 four artifacts + auto reporting + token accounting | 07-02, 07-05, 07-07 |
| 07-03 local-truth GUI + verifying replay viewer | 07-03, 07-06, 07-08 |
| 07-04 `docs/PRD_gatekeeper.md` | 07-09 |
| 07-96 graph refresh · 07-97 triplet · 07-99 TODO closure | 07-09 · plan-phase (done) · verify-work |

## 11. What 07-CONTEXT.md gets wrong against the current tree

Recorded so the plans start from the tree, not the draft (CONTEXT files are drafts, not specs):

1. **"the four JSON artifacts" reads as four new deliverables.** `declaration_<game_id>.json`
   already exists and is written every game by `agent_step0_wiring.write_declaration`, and the
   turn-by-turn journal already exists as `logs/<role>/<game_uid>.jsonl` + a sibling
   `.ledger.jsonl`. Only `config_` and `result_` are genuinely new; `declaration_` is *completed*
   (D-71) and `log_` is *derived* (D-73).
2. **"reuse the Phase-6 canonical-JSON + SHA-256 helper" points at the wrong package.**
   `canonical_json` / `digests_match` live in `src/pursuit/network/config_hash.py`, not in
   `pursuit.security` — `security/commit_pack.py` imports them from there as a documented
   package-boundary exception. Import from the same place; do not create a third copy.
3. **"belief heatmap … sensed scent … hint log with intent flags" assumes a hint history object
   that does not exist.** `ctx.incoming_hints` holds only the *last* hint per sender; the
   turn-by-turn history exists only in the JSONL `language_turn_record` entries. Either the view
   builder accumulates its own history, or the GUI reads it from the log — a real design choice
   07-03 must make.
4. **"one GUI instance per agent process (two windows in a local match)" is fine, but the
   watchdog makes it non-trivial**: `tk.mainloop()` in the agent process blocks the loop the
   `os._exit(1)` freeze watchdog is timing. CONTEXT does not mention this.
5. **The gatekeeper is not simply "extended for Gmail"** — its constructor is typed on
   `LanguageParams` and always builds a `TokenBudget`. The extension has a real shape (D-68) and
   touches the LLM path, so it is not a zero-risk addition.
6. **`config/police/games_played.json` = 1881** — CONTEXT says nothing about it, and this is the
   phase that mails that number to the lecturer (OQ-5, rule 38).
