# Phase 8: Submission and League Operations - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 turns the working system into a submission: **two cross-linked public GitHub
repos** (cop, thief) each carrying README / `config/` / PRD / PLAN / TODO files; the
**academic README** with its six mandatory sections (including learning curves and
`Verified OK` screenshots); a **Git tag** on the submitted version; the **team code**;
**scored league games** against different teams (one scoring game per opponent, no
rematches for points, each game emailing the commit hash it ran on); the **submission
form** saved as PDF and submitted per team member; and the **code-quality
self-assessment** (SUB-01…SUB-12).

**Planning-day note:** refresh the graph (`/gsd:graphify`) and commit
`.planning/graphs/` for the submission showcase (task 08-96) before
`/gsd:plan-phase 8 --chunked`.

</domain>

<decisions>
## Implementation Decisions

### Team identity
- **Team code: `khm-mn17`** (user's own choice — 8 characters, no spaces, per SUB-06).
  Needed before the first scored game; use it in configs, reports, and repo READMEs.

### Repo split (SUB-01, SUB-02)
- **Clean snapshot repos**: two fresh public repos; each receives the shared `pursuit`
  library (duplicated — a shared *library* is allowed; shared *state* is not, per D-04's
  neutral package naming) plus its role's config and brain. No git-surgery on the
  mono-repo near the deadline; the private dev repo remains the true history.
- Each README cross-links the other repo (rule 49).

### League operations (SUB-07, SUB-08)
- **Aim for more than the minimum games** (user's explicit choice): play as many scored
  games as time allows for league standing — but still lock the first 2 opponents NOW
  (message classmates this week), run unscored connectivity friendlies as soon as
  Phases 5–6 land, and schedule scored games for Aug 11–12 after the exam. The minimum
  2 against different teams is the floor, never at risk.
- One scoring game per opponent, no rematches for points; the game count is declared
  accurately — misreporting the count is a disqualification (rule 38).
- Every game's report emails the exact commit hash it ran on (SUB-08); per-game config
  files are attached to the repo with per-game names (SUB-12).

### Academic README (SUB-03)
- **English** — standard for code repos; the planning-day researcher double-checks
  whether §9.4.2 mandates Hebrew, and if it does, Hebrew wins.
- Six mandatory sections, learning curves from the Phase-3 CSV/plot pipeline, and
  `Verified OK` screenshots from the Phase-7 replay viewer.

### Claude's Discretion
- Public repo names and README structure details (within the six-section mandate)
- Git tag naming (e.g., `v1.00-submission`) consistent with version.py
- Self-assessment write-up drafting (code quality only, never league results — SUB-11)
- Submission-form filling flow (form itself must be unaltered — SUB-09)

</decisions>

<specifics>
## Specific Ideas

- Submission deadline: **2026-08-12**; exam **2026-08-10** — scored games realistically
  land Aug 11–12, so all technical phases must be done before the exam break.
- Secrets hygiene at split time: fresh-eyes scan of both public repos before pushing
  (`.env-example` with dummy values, nothing real — SUB-04); submitted separately per
  team member (SUB-10; solo team = one submission).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-submission-and-league-operations*
*Context gathered: 2026-07-28*
