# Phase 7 TODO — Reporting and Visualization Shell

**Owner:** Khaled (solo) · **Updated:** 2026-08-17 · **Status: ☐ planned — outline + triplet written
at plan-phase; no plan executed yet.**

> Phase task list. ROADMAP rows 07-01…07-04 are deliverable **groups**; this phase needs ten plans
> to keep every file under the 150-line gate, so row IDs and plan IDs are **not** 1:1 here (they
> were in Phases 4 and 6). The mapping is in
> [07-PLAN-OUTLINE.md §10](../../../.planning/phases/07-reporting-and-visualization-shell/07-PLAN-OUTLINE.md).
> `/gsd:verify-work 7` marks every row `☑` and ticks the matching rows in the root
> [docs/TODO.md](../../TODO.md).
> **Status:** ☐ not started · ◐ in progress · ☑ done · **Priority:** P0/P1/P2

| Task | Pri | Wave | Status | Owner | Definition of Done |
|------|-----|------|--------|-------|--------------------|
| 07-01 Gatekeeper chain — `GatekeeperParams` extraction + injected budget, `QuotaManager`, `DosDetector`, `chain.py`, `reporting.json` + loader | P0 | 1 | ☐ | Khaled | A zero-token mail call never touches a `TokenBudget`; the LLM path's reserve/settle order provably unchanged (Phase-4 tests pass unmodified); bucket admits ⌊C⌋ then blocks; quota exhaustion and a latched DOS lock return caller-handled refusals; daily counter survives a simulated restart (REPORT-02, REPORT-03) |
| 07-02 Artifact spine — names/`<NN>`/`game_uid` join + canonical signing, `config_<game_id>_g<NN>.json`, the `declaration_` wrapper | P0 | 1 | ☐ | Khaled | All four names match PARAMETERS exactly; one shared `game_uid`; `config_` round-trips to the same digest `config_hash` already computes; both roles produce byte-identical `config_`; the **signed** Step-0 payload is unchanged and the handshake still passes (REPORT-06) |
| 07-03 `LocalView` firewall — read model + view builder + CI local-truth gate | P0 | 1 | ☐ | Khaled | Opponent cell (chosen distinct from every displayed cell) appears nowhere in the serialised view; a deliberately leaky view **fails** the same scan (counter-control); no `gui/` module imports the engine/state or reads `ctx.state`; all three fail against pre-plan code (revert probe) (REPORT-08) |
| 07-04 Mail transport — `MailSink`, `DryRunSink`, `GmailSink` (fake transport), MIME attachment, 429 backoff, `.env-example` | P0 | 2 | ☐ | Khaled | JSON is an **attachment**, body carries no report content (MIME parsed back, not builder-inspected); recipient from config equals the single mandatory address; any scope beyond `gmail.send` fails a test; 429→429→200 produces exactly two configured-length backoff sleeps then succeeds; permanent 429 queues, never crashes (REPORT-04, REPORT-05) |
| 07-05 `log_<game_id>_g<NN>.json` builder — wire JSONL × nonce ledger, joined on local turn truth | P0 | 2 | ☐ | Khaled | Every turn carries commitment, revealed move, intent, hint, verdict, nonce and hash; re-hashing through `commit_pack` reproduces `h_commit` for 100% of turns; artifact is self-contained (viewer needs neither source file); a truncated JSONL tail is tolerated, not fatal (REPORT-06, REPORT-09) |
| 07-06 Live GUI — Tk shell over `LocalView`, `after()`-driven, four files | P0 | 2 | ☐ | Khaled | Scripted headless launch constructs every widget and exits 0; renders with a `None` belief map; imports nothing from `pursuit.network` beyond the view provider; zero logic in `gui/` (same CI script as 07-03); `mainloop()` provably does not block the turn loop past the watchdog threshold (REPORT-08) |
| 07-07 End-of-game reporting — `result_<game_id>.json`, token totals, rule-35 agreement, send via the chain in `dry_run` | P0 | 3 | ☐ | Khaled | `result_` carries this game's **and** the series' LLM token totals (proven: series total > one game's after two games) plus the git commit hash; honest game → `agreed: true`, fabricated disagreement → `agreed: false` **and still reported**; a send failure leaves outcome and exit code untouched (REPORT-01, REPORT-06, REPORT-07) |
| 07-08 Replay viewer — load `log_`, recompute hashes, verdict banner, step/play/pause | P0 | 3 | ☐ | Khaled | Clean log → `Verified OK`; single-bit tamper in `state`/`move`/`intent`/`nonce` → `FAILED` naming the turn; **empty log → neither verdict**, an explicit "nothing to verify"; verification goes through `commit_pack`, never a second serializer; the verdict function has a grep-proven production caller (REPORT-09) |
| 07-09 GATE-7 measurement + `docs/PRD_gatekeeper.md` + `OAUTH-RUNBOOK.md` | P1 | 4 | ☐ | Khaled | One command, zero credentials, honest PASS/FAIL per criterion; criterion 1 reported as **`dry_run` PASS + live PENDING**, never a blanket PASS; per-mechanism PRD documents the chain and the source of every number; no `gui/` import at module scope in the measurement script (DOC-02) |
| **07-10 HUMAN CHECKPOINT — `autonomous: false`** — OAuth consent + send-only client, one live send, README screenshots, OQ-5 decision | P0 | 5 | ☐ | **Khaled (human)** | Consent completed by a person (Claude must not enter credentials or click consent); one live message delivered to `rmisegal+uoh26finalgame@gmail.com` with the JSON attached; criterion 1 flips PENDING→PASS with delivered-message evidence; presentation-grade GUI + `Verified OK` screenshots committed; OQ-5 resolved in writing; `reporting.mode` returned to `dry_run` (REPORT-01) |
| 07-96 Refresh the graphify graph at plan-phase and after execute | P2 | — | ☐ | Khaled | `GRAPH_REPORT.md` current with `services/reporting/`, `sdk/local_view.py`, `gui/` |
| 07-97 Create/refresh `docs/phases/phase-7/{PRD,PLAN,TODO}.md` at plan-phase | P1 | — | ☑ | Khaled | This triplet exists and matches the plan outline (created 2026-08-17) |
| 07-99 On verify-work: mark all rows ☑ + tick root `docs/TODO.md` | P1 | — | ☐ | Khaled | Phase gate met on measured evidence; all TODOs checked (DOC-01) |

## Phase gate (§10.4)
- [ ] **1.** A game summary is sent by mail — send-only OAuth, through the gatekeeper, attached
      JSON, never free text. *(Measured in two halves: the whole stack end to end under
      `reporting.mode = dry_run` with a fake Google client — 07-09; plus one live send that needs a
      human at the consent screen — 07-10.)*
- [ ] **2.** The live GUI displays state — **only local truth**, never the full objective board.
      *(Machine-measurable: renders + the D-74 firewall tests with their counter-control. Only the
      presentation-grade README screenshot is a human aesthetic call.)*
- [ ] **3.** The replay app reconstructs a recorded round and shows `Verified OK`.
      *(Machine-measurable: clean → OK, tampered → FAILED, empty → neither.)*

## The one human-gated item
Everything through wave 4 runs unattended. **07-10 is the only `autonomous: false` plan**, and it
exists because Claude must not enter credentials or click through Google's OAuth consent screen,
and cannot judge whether a screenshot is presentation-grade. It is a short scripted checkpoint
against `OAUTH-RUNBOOK.md`, following the GATE-4 live-run and GATE-5 remote-round precedent.

## Open questions blocking parts of execution
Recorded rather than invented — full text in
[07-PLAN-OUTLINE.md §4](../../../.planning/phases/07-reporting-and-visualization-shell/07-PLAN-OUTLINE.md):

| # | Question | Blocks | Who decides |
|---|---|---|---|
| OQ-1 | The Quota Manager's **daily send ceiling** has no value in PARAMETERS.md (SEGAL §4 gives an *hourly* 500) | 07-01 | confirm, then D-18-style labelled engineering default |
| OQ-2 | The **DOS detector's** trip threshold and lock duration have no source at all | 07-01 | same — or define it structurally, with no new number |
| OQ-3 | "Take the stricter value" is ambiguous for backoff (Table 19 ≥ 5 s vs SEGAL 30 s) | 07-01 | one-line confirmation |
| OQ-4 | One `result_` per **series** vs one email per **game** (rule 32 + mandatory-rule 5) | 07-07 | interpretation, flagged not quoted |
| OQ-5 | `config/police/games_played.json` reads **1881** — incremented once per agent start — and this phase mails that number. **Rule 38: a false games-played declaration is an absolute disqualification.** | 07-10 | **human, not Claude** |
