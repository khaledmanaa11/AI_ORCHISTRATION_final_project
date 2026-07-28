# Phase 7: Reporting and Visualization Shell - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 delivers the outward face: **automatic end-of-game reporting** — both agents
email a signed JSON report to `rmisegal+uoh26finalgame@gmail.com` through the
**gatekeeper chain** (Quota Manager → Token Bucket `tokens ← min(C, tokens + r·Δt)` →
DOS Detector → Gmail API, send-only OAuth, HTTP 429 backoff, attached JSON never free
text); the **four JSON artifacts** (`declaration_` / `config_` / `log_` / `result_`);
**token accounting** per game and per series; the **live GUI** (local truth ONLY —
showing the objective board is a disqualification); and the **replay viewer** that
reconstructs a recorded game and shows `Verified OK` (REPORT-01…REPORT-09).

The gatekeeper chain, token-bucket formula, artifact names, and OAuth scope are
**spec-locked** — not design choices.

**Planning-day note:** refresh the graph (`/gsd:graphify`) before
`/gsd:plan-phase 7 --chunked` (task 07-96). The Phase-4 minimal gatekeeper (LLM calls)
is EXTENDED here for Gmail — same module, do not build a second gatekeeper.

</domain>

<decisions>
## Implementation Decisions

### Live GUI
- **Tkinter** — stdlib, zero new dependencies, runs anywhere the grader runs Python.
  Thin shell over the SDK layer: the GUI renders state, never computes it.
- **Full local dashboard**: own position + known barriers + belief heatmap over the
  opponent + sensed scent + hint log with intent flags + turn/state/timer. One GUI
  instance per agent process (two windows in a local match) — no shared state between
  them, each shows only its own agent's local truth.

### Replay viewer
- **Step-through + verdict banner**: load `log_<game_id>.json`, recompute every hash,
  display `Verified OK` / `FAILED` prominently, then step forward/back through turns
  with play/pause. The Verified-OK screenshot is a mandatory README asset (rule 42
  neighborhood) — it should look presentation-grade.

### Gmail & reporting safety
- **Personal Gmail (khaled.mnaa43@gmail.com)** with an OAuth client restricted to the
  **send-only scope** (`gmail.send`); credentials/token paths via env vars, nothing in
  git.
- **`reporting.mode = dry_run | live`** config toggle: dev/test configs default to
  `dry_run` — the report "email" is written to disk (.json/.eml) instead of sent. Only
  league configs set `live`. No accidental mail to the lecturer during development.
- Send failures queue and retry via the gatekeeper (overflow queues, never crashes);
  429 → exponential backoff per REPORT-04.

### Claude's Discretion
- Dashboard layout/colors; heatmap rendering approach in Tkinter
- Gatekeeper extension design (Quota Manager / Token Bucket / DOS Detector as composable
  stages; bucket parameters C and r from config per Table 19)
- Report signing details (reuse the Phase-6 canonical-JSON + SHA-256 helper)
- Replay file-open UX (CLI arg vs file dialog)

</decisions>

<specifics>
## Specific Ideas

- The four artifacts and the reporting address come from PARAMETERS.md; the address is
  the single mandatory destination (`rmisegal+uoh26finalgame@gmail.com`).
- `result_<game_id>.json` must include total LLM tokens consumed per game and across the
  series (REPORT-07 / rule 54) — the Phase-4 gatekeeper's token accounting feeds this.
- Live GUI displaying true opponent position = disqualification (rules 8–9). The belief
  heatmap is the legal (and more impressive) alternative.
- Per-mechanism PRD due this phase (task 07-04): `docs/PRD_gatekeeper.md`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-reporting-and-visualization-shell*
*Context gathered: 2026-07-28*
