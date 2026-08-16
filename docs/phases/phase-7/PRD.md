# Phase 7 PRD — Reporting and Visualization Shell

**Version:** 1.00 · **Status:** ☐ draft · **Updated:** 2026-08-17

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); do not restate it — capture
> only what is specific to this phase. Numbers come from [PARAMETERS.md](../../PARAMETERS.md)
> (Table 19, §Required JSON artifacts, §Addresses) and the book (§9.3.1, §9.4.2), never invented.

## Goal
Gmail API reporting via OAuth 2.0, live GUI, replay viewer application (ROADMAP Phase 7). This is
the phase where the project stops being self-contained: a game that is won on the board but never
reported scores **zero for both teams** (rule 35), so reporting is the single most
submission-critical mechanism in the codebase.

## Requirements covered
- **REPORT-01** — at game end both agents automatically email a signed JSON report to
  `rmisegal+uoh26finalgame@gmail.com` (rules 32, 35, 51).
- **REPORT-02** — outgoing mail passes the gatekeeper chain: Quota Manager → Token Bucket →
  DOS Detector → Gmail API (rules 28-29, book §9.3.1 Figure 13).
- **REPORT-03** — the token bucket implements `tokens ← min(C, tokens + r·Δt)`, allowing a send
  iff `tokens ≥ 1` (Table 19).
- **REPORT-04** — HTTP 429 is handled with backoff; the mail interface uses a **send-only** OAuth
  scope (rules 28, 30).
- **REPORT-05** — reports are attached JSON files, never free text (rules 33-34).
- **REPORT-06** — four JSON artifacts: `declaration_`, `config_`, `log_`, `result_` (PARAMETERS).
- **REPORT-07** — the final JSON reports total tokens consumed per game **and across the series**
  (rule 54).
- **REPORT-08** — the live GUI displays only local truth, never the full objective board
  (rules 8-9).
- **REPORT-09** — a replay viewer reconstructs a recorded game log and verifies it, showing
  `Verified OK` (rule 20).

## Acceptance criteria (= §10.4 milestone gate)
1. A game summary is sent by mail — send-only OAuth, through the gatekeeper, attached JSON, never
   free text.
2. The live GUI displays state — **only local truth**, never the full objective board.
3. The replay app reconstructs a recorded round and shows `Verified OK`.

Criteria 2 and 3 are **fully machine-measurable on this one machine with no credentials**.
Criterion 1 is measured in two halves: the entire stack end to end under
`reporting.mode = dry_run` against an injected fake Google client (no OAuth, no network), plus
**one** live send that requires a human at the consent screen. Evidence:
`GATE-7-MEASUREMENT.md`, written by plan 07-09 and completed by plan 07-10.

## In scope / Out of scope (this phase)
- **In:** the `pursuit.services.reporting` package (Fig-13 chain stages, mail sinks, MIME
  assembly, the four artifact writers, the end-of-game hook); the Phase-4 gatekeeper **extended**
  — one class, two instances, never a second gatekeeper; a twelfth config block `reporting.json`
  with the `dry_run | live` toggle; the SDK-layer `LocalView` read model that makes rules 8-9
  structurally enforceable; a Tkinter live dashboard and a Tkinter replay viewer, both thin shells;
  `docs/PRD_gatekeeper.md`.
- **Out:** the repo split, the academic README, the Git tag and league play (Phase 8 — this phase
  produces the screenshots and the report Phase 8 attaches); any change to the `Envelope` shape,
  the commit-reveal payload, the **signed** Step-0 field set, or Phase-3/4 strategy and language
  behaviour; RL retraining; a second gatekeeper for any purpose.

## Dependencies
- Depends on: Phase 6 (security and cryptography) — its canonical-JSON + SHA-256 helpers, nonce
  ledger, negotiated `game_id` (D-61), Step-0 declaration artifact and mutual audit verdict are all
  direct inputs. Phase 5's shipped code is under it; Phase 4 supplies the gatekeeper and
  `TokenBudget.report()`.
- External: `google-api-python-client` / `google-auth` / `google-auth-oauthlib` (new — the first
  and only Google dependency, isolated in one module); `tkinter` (stdlib, already present,
  verified importable at Tk 8.6 on this machine); a Google account with an OAuth client restricted
  to `gmail.send`. **The OAuth consent step needs a human** — it is isolated in plan 07-10.

## Success metrics & test scenarios
- **Gatekeeper:** a mail call with zero LLM tokens never touches a `TokenBudget`; the LLM path's
  reserve/settle order is provably unchanged; the bucket admits ⌊C⌋ then blocks; quota exhaustion
  and a latched DOS lock return caller-handled refusals, never an exception into the turn loop; the
  daily quota counter survives a simulated process restart.
- **Mail:** the JSON is an **attachment** and the body carries no report content — asserted by
  parsing the MIME back, not by inspecting the builder; recipient comes from config and equals the
  single mandatory address; any scope beyond `gmail.send` fails a test; a fake client returning
  429 twice then 200 produces exactly two backoff sleeps of the configured length and then
  succeeds; a permanently-429 client exhausts retries and **queues**, never crashes.
- **Artifacts:** all four names match PARAMETERS exactly (`_g<NN>` present on `config_`/`log_`,
  absent on `declaration_`/`result_`); all four carry the same `game_uid`; `result_` carries this
  game's **and** the series' LLM token totals, plus the git commit hash the game ran on; an
  agreeing game records `agreed: true` and a disagreeing one records `agreed: false` **and still
  reports** (rule 35 requires the disagreement reported, not suppressed).
- **Rules 8-9 (highest risk in the phase):** an opponent placed at a cell distinct from every
  legitimately displayed cell appears nowhere in the serialised view; the same scan run against a
  deliberately leaky view **must fail** (counter-control against a vacuous pass); a CI script proves
  no `gui/` module imports the engine/state or reads `ctx.state`; all three fail against pre-plan
  code (revert probe).
- **Replay:** clean log → `Verified OK`; a single-bit tamper in `state`/`move`/`intent`/`nonce` →
  `FAILED` naming the turn; an **empty** log → neither verdict, an explicit "nothing to verify"
  (`all_matched([])` is `True` — the canonical vacuous pass, and this is the screen the grader
  looks at).
- **Standing gates:** ruff 0 · coverage ≥ 85% · every file ≤ 150 code lines · no secrets · no
  invented numbers · every test offline.

## Design decisions (phase ADRs)
D-68 … D-75 — recorded authoritatively in
[07-PLAN-OUTLINE.md §2](../../../.planning/phases/07-reporting-and-visualization-shell/07-PLAN-OUTLINE.md).
Headline four: **D-68** (one gatekeeper class, two instances — `GatekeeperParams` extracted, budget
injected), **D-71** (the declaration artifact **wraps** the signed Step-0 payload; extending it
would abort every game at the handshake digest check), **D-74** (the rules 8-9 firewall is a
`LocalView` read model outside `gui/`, because `ctx.state` legitimately holds both true positions
and because `*/gui/*` is coverage-omitted), **D-75** (rule 35's result agreement is derived from
the peer's existing `GAME_OVER` claim plus the Phase-6 audit verdict — no new message type).

## Open questions carried into execution
Five numbers/interpretations are **not** settled by PARAMETERS.md and are recorded rather than
invented: the Quota Manager's daily send ceiling (OQ-1), the DOS detector's trip threshold (OQ-2),
the Table-19-vs-SEGAL "stricter value" reading for backoff and concurrency (OQ-3), one `result_`
per series against one email per game (OQ-4), and — the one that needs a **human**, not Claude —
`config/police/games_played.json` currently reading `1881` while rule 38 makes a false
games-played declaration an absolute disqualification (OQ-5). Full text in
[07-PLAN-OUTLINE.md §4](../../../.planning/phases/07-reporting-and-visualization-shell/07-PLAN-OUTLINE.md).
