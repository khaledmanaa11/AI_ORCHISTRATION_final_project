---
phase: 04-language-and-scent
plan: "13"
subsystem: docs
tags: [documentation, per-mechanism-prd, rules-resolution, phase-triplet, graphify, doc-01, lang-05, lang-07]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plans 04-01..04-12)
    provides: >
      every number, digest, measured curve, and shipped signature this plan transcribes --
      nothing here was re-derived; each figure traces to a specific plan SUMMARY.md
provides:
  - "docs/phases/phase-4/RULES-RESOLUTION-LANG.md: both sides of the SS5.3.2/SS6.4 contradiction
    quoted with book+PDF pages verified directly against the source PDF this session, the
    preface's academic-freedom clause, D-48's four reasons, D-49's rule-23 argument, and a
    BOOK/NEGOTIATED/DERIVED table for every Phase-4 rule call"
  - "docs/PRD_scent_map.md, docs/PRD_belief_map.md, docs/PRD_deception.md: the three
    per-mechanism PRDs Segal SS2.3 requires, each with acceptance criteria and links to the
    plans that built it"
  - "docs/phases/phase-4/{PRD,PLAN,TODO}.md: the phase triplet CLAUDE.md requires, routing a
    grader to the rules note; TODO.md states its row-ID/plan-ID namespace convention explicitly"
  - "docs/STRATEGY.md's three TBD - Phase 4 rows filled with what was built and measured"
  - ".planning/ROADMAP.md's Phase 4 plan list replaced with the real fourteen (was four
    placeholder rows), plans-complete count corrected to 13/14"
  - ".planning/graphs/GRAPH_REPORT.md refreshed for the wave-7 tree, with a programmatic
    (not eyeballed) layering check against graph.json"
affects: [04-14-gate-4-measurement, verify-work-4]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verified book quotations against the source PDF directly this session (police_thief_p2p.pdf
      pages 5, 50-53, 62-64 read via the Read tool), not re-copied from a prior extract without
      checking -- confirms 04-PLAN-OUTLINE.md SS1's quotes and page numbers, and additionally
      resolves the preface's PDF page (5, roman-numbered front matter, the +16 rule does not apply
      there) which no prior document in this repo had cited"
    - "Layering sanity check run as a script against graph.json's actual nodes/links (source_file
      substring match on both endpoints), not by reading the rendered report -- zero edges in
      either direction between services/llm and strategy, corroborating
      scripts/check_no_llm_in_strategy.py's structural guarantee independently"

key-files:
  created:
    - docs/phases/phase-4/RULES-RESOLUTION-LANG.md
    - docs/PRD_scent_map.md
    - docs/PRD_belief_map.md
    - docs/PRD_deception.md
    - docs/phases/phase-4/PRD.md
    - docs/phases/phase-4/PLAN.md
    - docs/phases/phase-4/TODO.md
  modified:
    - docs/STRATEGY.md
    - .planning/ROADMAP.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "ROADMAP.md's Phase 4 'Plans:' bullet checkboxes are left unticked for every one of the
    fourteen real plans (04-01..04-14), even though 04-01..04-13 have real SUMMARY.md files on
    disk -- read literally against this plan's own explicit environment rule ('TICK NOTHING.
    Every status stays sq or half-circle. /gsd:verify-work 4 ticks after 04-14.'), applied to
    every tick mark in every file this plan touches, not narrowly to the sq/half-circle/checkmark
    symbol system alone. The Plans-Complete NUMERIC count (13/14) was still updated, since a
    plain number is not a tick."
  - "docs/TODO.md's Phase 4 section was read and left untouched -- its four coarse rows
    (04-01..04-04 + 04-99) already describe, accurately, what the fourteen real execution plans
    built (verified by re-reading each row's Definition of Done against this session's own
    twelve summaries); editing it would have been cosmetic churn, not a correction, and it
    mirrors Phase 3's own docs/TODO.md, which never expanded to list all fifteen of its real
    03-11..03-25 execution plans either"
  - "Phase-4 TODO.md rows for the twelve already-executed plans (04-01..04-12) plus this plan
    itself (04-13) and the two roadmap tasks this plan discharges (04-96, 04-97) are marked with
    the half-circle status symbol (in progress / executed-not-verified), not the empty-box
    symbol -- distinguishing genuinely-not-started work (04-14, 04-99) from work that is real and
    committed but not yet phase-verified, while never using the checkmark symbol verify-work
    alone is entitled to write"

# Metrics
duration: ~35min
completed: 2026-08-09
---

# Phase 4 Plan 13: Documentation -- Rules Resolution, Three Mechanism PRDs, Phase Triplet Summary

**Transcribed (never re-derived) documentation covering the book's SS5.3.2/SS6.4 reveal-vs-blindness
contradiction and this project's D-48/D-49 resolution, three per-mechanism PRDs for scent/belief/
deception with every number traced to a specific plan SUMMARY, the phase-4 doc triplet, and a
programmatically-verified knowledge-graph layering check -- zero source code touched, zero boxes
ticked.**

## Performance

- **Duration:** ~35 min (estimate; exact session-start timestamp not captured, consistent with
  04-11/04-12's own summaries noting the same limitation)
- **Completed:** 2026-08-09T03:24:00Z (2026-08-09 06:24 local, +03:00)
- **Tasks:** 4/4
- **Files:** 7 created, 3 modified

## Accomplishments

- **`docs/phases/phase-4/RULES-RESOLUTION-LANG.md`** quotes both sides of the book's own
  apparent contradiction -- SS5.3.2's per-turn Reveal of the Move (book p.35/PDF 51) and Figure 6
  (book p.36/PDF 52) versus SS6.4's "neither side sees the opponent's real location" (book
  p.47/PDF 63) -- plus the preface's academic-freedom clause (book p.v, PDF 5, verified directly
  against `police_thief_p2p.pdf` this session since no prior document in this repo had cited its
  PDF page). States D-48 (per-turn Reveal kept, direction-token move, belief map is the
  one-turn-ahead predictive distribution, Regime A/B) with its four reasons, and D-49 (scent
  derived locally, never transmitted) with rule 23's own logic as the argument. A
  BOOK/NEGOTIATED/DERIVED table covers all 18 Phase-4 rule calls, matching Phase 3's
  `RULES-RESOLUTION.md` shape.
- **Three per-mechanism PRDs** (`docs/PRD_scent_map.md`, `docs/PRD_belief_map.md`,
  `docs/PRD_deception.md`), each with the shipped digest / measured curves / verbatim style guide
  the outline required, every number traced to 04-01/04-05/04-08/04-09/04-10/04-11's own
  SUMMARY.md files, and each stating its own acceptance criteria and REQ-IDs. `PRD_belief_map.md`
  states the Regime-A honesty clause in plain words and records D-51 as a **disclosed revision**
  of D-40 (not an extension) and D-43's sample-vs-argmax choice with its league-format rationale.
- **The phase triplet** (`docs/phases/phase-4/{PRD,PLAN,TODO}.md`) -- `PRD.md` states the §10.4
  gate's exact bar in advance of 04-14 measuring it (so the bar cannot be redefined after seeing
  the result); `PLAN.md` records the phase ADRs **by reference** to `04-PLAN-OUTLINE.md` §2
  rather than copying D-32…D-53 a second time; `TODO.md` states plainly, at the top, that its row
  IDs equal the `.planning/` execution-plan IDs one-to-one (unlike Phase 3's coarser TODO.md,
  which never expanded past four aggregated rows for fifteen real execution plans).
- **`docs/STRATEGY.md`'s three `TBD — Phase 4` rows** (belief map, when to lie vs. tell the
  truth, hint-vs-scent weighting) filled with what was built and measured; found by `grep -n
  'TBD'`, and the neighbouring `TBD — Phase 3` rows (state encoding, exploration, hyperparameters,
  fallback policy) confirmed untouched.
- **`.planning/ROADMAP.md`'s Phase 4 plan list** replaced: the four stale placeholder rows (which
  pre-dated the real 14-plan wave structure) are now the real `04-01`…`04-14` plus `04-96/97/99`,
  with one-line descriptions matching what was actually built. Plans-complete count corrected
  from a stale `6/14` to `13/14`.
- **The knowledge graph refreshed**: `graphify update .` → 5320 nodes / 9778 edges / 333
  communities (up from 5221/9687/336 after 04-12); only `GRAPH_REPORT.md` committed. The
  layering sanity check the plan demands was run **programmatically** against `graph.json`'s
  actual node/edge data (matching `source_file` substrings on both edge endpoints), not by
  reading the rendered report: **zero edges `services/llm → strategy` and zero edges
  `strategy → services/llm`**, in either direction — corroborating
  `scripts/check_no_llm_in_strategy.py`'s structural guarantee independently, on the real graph
  rather than by inspection.
- **Nothing ticked anywhere.** `grep -c "☑"` across every file this plan touches returns matches
  only inside legend/explanatory prose (e.g. `TODO.md`'s own "☑ done (verify-work only)" status
  key), never an actual status cell or checkbox; every `ROADMAP.md` Phase-4 plan-list checkbox
  stays `[ ]`.

## Task Commits

Each task was committed atomically:

1. **Task 1: the rules-resolution note** - `fbd43fb` (docs)
2. **Task 2: the three per-mechanism PRDs** - `6ff09d0` (docs)
3. **Task 3: the phase triplet and the trackers** - `8d5e77f` (docs)
4. **Task 4: refresh the knowledge graph** - `6d4b695` (docs)

_No TDD cycle applies -- this plan is documentation-only and touches zero source or test files,
per its own frontmatter (`files_modified` lists only `docs/` and `.planning/` paths)._

## Files Created/Modified

- `docs/phases/phase-4/RULES-RESOLUTION-LANG.md` — the reveal/belief contradiction, D-48, D-49,
  the BOOK/NEGOTIATED/DERIVED table
- `docs/PRD_scent_map.md` — locked model, kernel, decay law, digest, D-49 argument
- `docs/PRD_belief_map.md` — grid, motion/likelihoods, reliability, both regimes, honesty
  clause, D-51, D-43
- `docs/PRD_deception.md` — `DeceptionPlan`, structural rule-25 argument, both lie-rate curves,
  the D-39 style guide verbatim
- `docs/phases/phase-4/PRD.md` — what the phase delivers, the §10.4 gate as acceptance criteria
- `docs/phases/phase-4/PLAN.md` — components/files, interfaces, ADRs by reference
- `docs/phases/phase-4/TODO.md` — one row per plan, namespace note, nothing ticked
- `docs/STRATEGY.md` — three `TBD — Phase 4` rows filled
- `.planning/ROADMAP.md` — Phase 4 plan list replaced with the real fourteen; count corrected
- `.planning/graphs/GRAPH_REPORT.md` — refreshed for the wave-7 tree

## Decisions Made

See `key-decisions` in the frontmatter for the full list with rationale. In prose, the one with
the widest interpretive weight: this plan's own environment rules state, in capitals, "TICK
NOTHING. Every status stays ☐ or ◐." Read broadly (every tick mark in every file this plan
touches, not narrowly the ☐/◐/☑ status-column convention alone), this meant leaving every
`ROADMAP.md` `- [ ]`/`- [x]` GitHub-style checkbox in the Phase 4 "Plans:" list unticked as well,
even for the twelve plans (04-01…04-12) that have real, committed `SUMMARY.md` files and would,
by a narrower reading, have been accurately markable `[x]`. The plain numeric "Plans Complete"
count in the Progress table was still corrected to `13/14`, since a number is not a tick.

## Deviations from Plan

None — plan executed exactly as written. All four tasks' `<verify>` blocks pass (see
Verification below); no Rule 1–4 deviation was triggered because this plan touches no source
code, no config, and no test file — only documentation the plan itself specifies.

## Verification (the plan's own `<verification>` block, run in full)

1. **Three per-mechanism PRDs exist and every number traces to a plan summary.** Confirmed —
   `docs/PRD_{scent_map,belief_map,deception}.md` all present; every measured number
   (digest, reliability trajectory, lie-rate curves, timing figures) was copied from
   04-01/04-05/04-08/04-09/04-10/04-11-SUMMARY.md, none re-derived.
2. **`RULES-RESOLUTION-LANG.md` quotes both sides with book+PDF pages and states the choice and
   its reasons.** Confirmed — every page pair extracted from the file
   (`grep -oE "book p\.[0-9]+ \(PDF [0-9]+\)"`) differs by exactly 16: `35/51, 47/63, 27/43,
   31/47 (x2), 36/52, 30/46, 34/50`. The preface's page (book p.v / PDF 5) is cited separately,
   with an explicit note that the +16 rule does not apply to roman-numbered front matter — all
   page numbers were verified directly against `police_thief_p2p.pdf` this session (pages 5,
   50–53, 62–64 read via the Read tool), not re-copied from a prior extract unchecked.
3. **The phase triplet exists, is complete, and nothing is ticked.** Confirmed —
   `docs/phases/phase-4/{PRD,PLAN,TODO}.md` all present; `grep -n "☑" docs/phases/phase-4/*.md`
   returns only two legend-text lines inside `TODO.md`'s own status-key sentence, no actual
   ticked cell.
4. **`ROADMAP.md`'s Phase 4 plan list matches the phase directory; tasks 04-96/97/99 survive.**
   Confirmed — 17 bulleted rows under Phase 4 (`04-01`…`04-14` + `04-96/97/99`), all unticked.
5. **`docs/STRATEGY.md` has no remaining `TBD — Phase 4`.** Confirmed — `grep -c "TBD — Phase
   4"` returns `0`; the four `TBD — Phase 3` rows are untouched.
6. **`uv run ruff check .` → 0 and the test suite is unchanged.** Confirmed —
   `uv run ruff check .` → `All checks passed!`; `uv run pytest tests/ --cov` →
   **1048 passed, 95.21% coverage** (byte-identical to the pre-plan baseline recorded in
   `04-12-SUMMARY.md` and `RESUME.md`); `bash scripts/check_line_limit.sh` → clean repo-wide;
   `uv run python scripts/check_no_llm_in_strategy.py` →
   `OK: no forbidden imports under .../src/pursuit/strategy.`

## Issues Encountered

None. The one open question worth recording for a future reader: the preface's PDF page (5,
front-matter roman numerals) had never been cited anywhere in this repo before this plan — it was
resolved by reading the actual PDF directly rather than left as a citation gap, since this plan's
own environment rules required every quotation to carry a verified book+PDF page pair.

## User Setup Required

None — no external service configuration required. This plan wrote documentation only; no
`ANTHROPIC_API_KEY` or any other environment variable is read by anything this plan created.

## Next Phase Readiness

- **04-14 (GATE-4 measurement)** is unblocked: `docs/phases/phase-4/PRD.md` §2 states the exact
  bar it must measure, in advance, so the report cannot redefine it after seeing the result; the
  three per-mechanism PRDs give 04-14 a place to cite its own live-API numbers against this
  phase's mocked/template-path baselines (explicitly flagged in `PRD.md` §7.3 as superseded by
  whatever 04-14 measures live).
- **`/gsd:verify-work 4`** — ticking `docs/phases/phase-4/TODO.md`, the root `docs/TODO.md`
  Phase-4 row, and `ROADMAP.md`'s Phase-4 checkboxes is explicitly **not** this plan's job. It
  runs only after 04-14 measures GATE-4 against the live API — the phase triplet, the rules
  note, and the three PRDs are all in place and waiting for that step, not for another
  documentation plan.
- No blockers for wave 8 (04-14).

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-09*

## Self-Check: PASSED

- All 7 created files confirmed present on disk (`[ -f ]`): `RULES-RESOLUTION-LANG.md`,
  `PRD_scent_map.md`, `PRD_belief_map.md`, `PRD_deception.md`, `phase-4/PRD.md`,
  `phase-4/PLAN.md`, `phase-4/TODO.md`.
- All 3 modified files confirmed present: `docs/STRATEGY.md`, `.planning/ROADMAP.md`,
  `.planning/graphs/GRAPH_REPORT.md`.
- All 4 task commit hashes (`fbd43fb`, `6ff09d0`, `8d5e77f`, `6d4b695`) confirmed present in
  `git log --oneline --all`.
- Full repo suite re-run clean at SUMMARY time: 1048 passed, 95.21% coverage (byte-identical to
  the pre-plan baseline); `uv run ruff check .` and `bash scripts/check_line_limit.sh` both exit
  0 repo-wide; `uv run python scripts/check_no_llm_in_strategy.py` clean.
- `grep -c "☑"` across every file this plan created/modified confirms no actual status cell or
  checkbox was ticked; only legend/explanatory prose contains the character.
- Layering check (`services/llm ↔ strategy`, both directions) re-run against
  `.planning/graphs/graph.json` at self-check time: 0 violations either direction.
