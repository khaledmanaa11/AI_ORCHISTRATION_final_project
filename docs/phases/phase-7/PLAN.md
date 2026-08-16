# Phase 7 PLAN — Reporting and Visualization Shell

**Version:** 1.00 · **Updated:** 2026-08-17

> How Phase 7 is built. The authoritative plan set lives in
> `.planning/phases/07-reporting-and-visualization-shell/` (outline + 07-01…07-10); this file is
> the grader-facing map of it. Per-mechanism PRD written this phase:
> [docs/PRD_gatekeeper.md](../../PRD_gatekeeper.md).

## Components

| Component | Files (≤150 code lines each) | Plan |
|---|---|---|
| Gatekeeper chain | `services/llm/gatekeeper.py` (extended), `services/reporting/{quota,dos,chain}.py`, `shared/reporting_config.py`, `config/{police,thief}/reporting.json` | 07-01 |
| Artifact spine | `services/reporting/{artifacts,artifact_config,artifact_declaration}.py` | 07-02 |
| Local-truth read model | `sdk/{local_view,view_builder}.py`, `scripts/check_local_truth.py` | 07-03 |
| Mail transport | `services/reporting/{sink,gmail_sink,message}.py`, `.env-example` | 07-04 |
| Replay artifact | `services/reporting/artifact_log.py` | 07-05 |
| Live GUI | `gui/{live_app,live_panels,live_sidebar,widgets}.py` | 07-06 |
| End-of-game reporting | `services/reporting/{artifact_result,end_of_game}.py`, `network/agent_entrypoint.py` (call site only) | 07-07 |
| Replay viewer | `gui/{replay_app,replay_panels}.py`, `services/reporting/replay_verify.py` | 07-08 |
| Gate evidence + PRD | `scripts/measure_gate7.py` + `gate7_*.py`, `GATE-7-MEASUREMENT.md`, `OAUTH-RUNBOOK.md`, `docs/PRD_gatekeeper.md` | 07-09 |
| Human checkpoint | consent + one live send + README screenshots (no code) | 07-10 |

## Interfaces & contracts

- **`GatekeeperParams`** — the seven Table-19 rows extracted from `LanguageParams` so both it and
  `ReportingParams` satisfy one type. `Gatekeeper(params=..., budget=None, clock=..., sleep=...)`:
  `budget` becomes an **injected optional**; the mail instance passes `None` and its `CallResult`
  carries `input_tokens=output_tokens=0`, which `gatekeeper.py`'s own docstring already anticipates.
  One class, two instances — never a second gatekeeper (SEGAL §4, 07-CONTEXT).
- **The Fig-13 chain** — `QuotaManager.allow() → Gatekeeper.submit() [TokenBucket inside] →
  DosDetector.observe()/locked` → `MailSink`. Quota and DOS are pre-call gates and post-call
  observers; the bucket is untouched (`bucket.py` already implements `tokens ← min(C, tokens+r·Δt)`
  verbatim). Every refusal is a caller-handled outcome in the `GatekeeperOverflow` mould, never a
  crash and never a rejection-without-queue.
- **`MailSink`** protocol with two implementations: `DryRunSink` (writes `.json` + `.eml` to the
  artifacts dir) and `GmailSink` (the only module importing `google-*`, scope `gmail.send` only,
  credential/token **paths** from env vars named in `reporting.json`). Selected by
  `reporting.mode = dry_run | live`.
- **The four artifacts** — `declaration_<game_id>.json` (a wrapper embedding own + peer **signed**
  Step-0 payloads verbatim, plus repo URLs, MCP addresses, agreed token ceiling and start/end times
  *outside* the signed envelope), `config_<game_id>_g<NN>.json`, `log_<game_id>_g<NN>.json`,
  `result_<game_id>.json`. All four share one `game_uid`; `<NN>` is a per-`game_id` sub-game index,
  `01`-based, **distinct from** the rule-37 lifetime `games_played` counter.
- **`LocalView`** — the rules 8-9 read model: own position, declared barriers, belief grid over the
  opponent, sensed scent, hint log with intent flags, turn/state/timer. Its field set structurally
  cannot represent an opponent's true cell. Built by `view_builder`, the **one** module allowed to
  read `ctx.state`; every GUI module consumes `LocalView` and nothing else.
- **Verification** — `replay_verify` recomputes each turn's hash through
  `security/commit_pack.build_commit_payload` and `network/config_hash.canonical_json`. **One
  serializer, never a second** (D-59): a fresh `json.dumps(sort_keys=True)` would drift and produce
  false `FAILED` verdicts on the exact screen the grader inspects.
- **Result agreement (rule 35)** — no new `MessageType`. `result_` records `own_outcome` (this
  side's resolved `Outcome`), `peer_outcome` (the peer's existing `GAME_OVER` claim, 05-15),
  `audit_verdict` (Phase-6 mutual audit) and a computed `agreed: bool`. A disagreement is reported
  as a disagreement.

## Wave graph

```
w1:  07-01 gatekeeper chain     07-02 artifact spine      07-03 LocalView firewall
        |          \                 |        \                   |
w2:  07-04 mail transport ------- ---+         07-05 log_ builder  07-06 live GUI
        |                                          |    \              |
w3:  07-07 end-of-game + result_ ------------------ +     07-08 replay viewer
                        \                                     /
w4:                      07-09 GATE-7 + PRD_gatekeeper + graph refresh
                                          |
w5:                      07-10  *** autonomous: false *** human checkpoint
```

Wave 1 is a real three-way fan-out (rate limiting, file shapes and the read model share no file) —
run each executor in its own git worktree. **Everything through wave 4 runs unattended**; the two
things Claude must not do (click OAuth consent, judge a presentation screenshot) are isolated in
07-10 and nothing else waits on a person.

## Phase ADRs

| # | Decision | Rationale | Alternative / trade-off |
|---|---|---|---|
| D-68 | One gatekeeper class, two instances; `GatekeeperParams` extracted, budget injected | 07-CONTEXT and SEGAL §4 both forbid a second gatekeeper; `CallResult` was already designed for a zero-token Gmail call | A second mail-only gatekeeper (rejected: duplicated retry/queue logic, explicitly forbidden) |
| D-69 | Quota and DOS are stages *around* `submit()`; the bucket stays inside it | Preserves the book's Figure-13 order without rewriting shipped, tested code | Rebuilding the chain as one new pipeline (rejected: throws away `bucket.py`'s verbatim Table-19 law) |
| D-70 | The send sink is injected behind a `MailSink` protocol; `google-*` imported in one module | Mirrors `anthropic_provider.py`'s vendor isolation; lets the whole stack be tested with no OAuth | Calling the Google client inline (rejected: untestable, and couples every test to a credential) |
| D-71 | `declaration_` **wraps** the signed Step-0 payload; extra PARAMETERS fields sit outside it | The payload's SHA-256 is digest-compared at handshake — one added field aborts every game with `STEP0_MISMATCH` | Extending the signed field set (rejected: breaks Phase 6 on both sides simultaneously) |
| D-72 | `<NN>` is a per-`game_id` sub-game index, not the lifetime games-played counter | Rule 37's counter is a disqualification-bearing declaration; a filename must not be coupled to it | Reusing `games_played` (rejected: five digits in a two-digit slot, and OQ-5) |
| D-73 | `log_` is derived at game end by joining the wire JSONL with the nonce ledger, on **local** turn truth | Keeps D-64's during-play nonce separation; nonces are public after game end (SEC-04) | Joining on the peer's declared `envelope.turn` (rejected: that is precisely 06-05's blocker) |
| D-74 | The rules 8-9 firewall is a `LocalView` in the SDK layer, outside `gui/` | `ctx.state` legitimately holds both true positions, so an import boundary is not enough; `*/gui/*` is coverage-omitted, so redaction logic there is invisible to the gate | Redacting inside the GUI (rejected: untested by construction) |
| D-75 | Result agreement derived from the existing `GAME_OVER` claim + audit verdict | Rule 35 is satisfiable with data already on the wire; re-opening the protocol in Phase 7 risks Phase 6 | A new `RESULT_AGREE` message (rejected: new protocol surface for no new information) |

## Test plan (TDD)

- Every suite stays **offline**: no live Google API, no OAuth, no real network, no opponent. The
  two-peer proofs reuse `tests/integration/two_peer_game.py`; the Gmail path is proven against an
  injected fake transport, never a real client.
- **Counter-controls are mandatory** where a test could pass vacuously — the phase-5 lesson, built
  in from the start rather than discovered by audit: the local-truth scan is paired with a
  deliberately leaky view that **must** fail it; `Verified OK` is paired with a tampered log
  (`FAILED`) and an empty log (neither); `agreed: true` on an honest game is paired with
  `agreed: false` on a fabricated disagreement that still reports.
- **Revert probes**: each of the three rules 8-9 tests, and the replay verdict tests, must fail
  against pre-plan code. No `parametrize` list may be built from a filesystem glob — an empty list
  skips silently.
- **Dead-code check**: `replay_verify`'s verdict function and the local-truth scan must each have a
  grep-proven **production** caller, not only test callers.
- Coverage target ≥ 85% (`fail_under=85`), with `*/gui/*` omitted — which is exactly why no logic
  may live there.

## Per-mechanism PRDs written this phase
- [docs/PRD_gatekeeper.md](../../PRD_gatekeeper.md) — rate limiting and reporting (ROADMAP row
  07-04, SEGAL §2.3 / DOC-02). Documents the Figure-13 chain, every number, and the source of every
  number.

## Risks

- **Rules 8-9 are the phase's disqualification risk and the reason 07-03 exists as its own plan.**
  Showing the opponent's real position is a project disqualification, and the data to do it is
  sitting in `ctx.state` on every agent process by design. Mitigated structurally (a read model
  that cannot express it) and provably (a field-level scan with a counter-control, plus a CI import
  gate in the `check_no_llm_in_strategy.sh` mould).
- **`tk.mainloop()` versus the freeze watchdog.** The agent arms a watchdog whose action is
  `os._exit(1)` at 60 s; blocking the event loop with Tk kills the agent mid-game and hands the
  peer an `opponent_unresponsive` declaration. Resolved in the plan (`after()`-driven or a separate
  process), not left to the executor.
- **A reporting failure must not forge a verdict.** Since 06-05, a non-zero exit code *means* an
  audit mismatch. The end-of-game hook is bounded, runs while the gatekeeper is still alive, and
  never touches the outcome or the exit code.
- **Line-limit pressure is anticipated, not discovered.** A Tkinter dashboard and a replay viewer
  do not fit one file each; the splits are written into the outline up front (`gui/` is 6 files,
  `services/reporting/` is 9). Note that `scripts/` is *not* scanned by `check_line_limit.sh` —
  migrating logic there to dodge the gate would also dodge coverage, and is forbidden.
- **Five open questions are recorded, not invented** (OQ-1…OQ-5 in the outline). OQ-5 —
  `games_played.json` reading `1881` while rule 38's sanction is absolute — is a human decision and
  is a blocking row in 07-10.
