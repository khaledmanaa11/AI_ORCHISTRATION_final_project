# Phase 8 PRD — Submission and League Operations

**Version:** 1.00 · **Status:** ☐ draft · **Updated:** 2026-08-17

> Phase-scoped PRD. Inherits the project [PRD.md](../../PRD.md); do not restate it — capture only
> what is specific to this phase. Numbers come from [PARAMETERS.md](../../PARAMETERS.md)
> (Table 18, §Addresses) and from [SEGAL_GUIDELINES.md](../../SEGAL_GUIDELINES.md) §17 / §19.1
> Table 5, never invented.

## Goal
Split into two public GitHub repos, write the academic README, tag the submitted version, and play
the league games (ROADMAP Phase 8). This is the phase where the project stops being a codebase and
becomes a **submission**: the engineering standard is graded here, not the game.

## Requirements covered
- **SUB-01** — two separate public GitHub repos (cop, thief), each README cross-linking the other
  (rule 49).
- **SUB-02** — every repo includes README, `config/`, PRD files, a PLAN file, TODO files (rule 50).
- **SUB-03** — academic README with its six §9.4.2 sections, including learning curves and
  `Verified OK` screenshots (rule 42).
- **SUB-04** — secrets in `.gitignore`, never pushed; `.env-example` with dummy values
  (rules 39–40).
- **SUB-05** — the submitted version carries an appropriate Git tag (rule 41).
- **SUB-06** — a unique 8-character team code, no spaces (rule 45) — already shipped as
  `khm-mn17` in `config/*/security.json`; this phase proves it survives the split.
- **SUB-07** — at least the minimum league games against different teams, one scoring game per
  opponent, the count declared accurately (rules 31, 37, 38, 52).
- **SUB-08** — each game emails the lecturer the commit hash the code ran on (rule 53).
- **SUB-09** — the submission form downloaded, filled, saved as PDF, unaltered (rule 43).
- **SUB-10** — submitted separately per team member (rule 44).
- **SUB-11** — a self-assessment score for **code quality only**, never league results (rule 55).
- **SUB-12** — fixed/minimum/negotiable statuses respected; each game's config attached to the repo
  under a per-game name (rule 12, PARAMETERS §2).
- **Cross-cutting:** QUAL-01 … QUAL-13 and DOC-01 … DOC-02 are audited, recorded and closed here —
  §17 is the phase's spine, and it is wider than the four ROADMAP rows.

## Acceptance criteria (= the submission gate)
1. **Two cross-linked public repos** (cop, thief), each carrying README / `config/` / PRD / PLAN /
   TODO, with a Git tag on the submitted version.
2. **Academic README** with its six mandatory §9.4.2 sections (the chosen Dec-POMDP model ·
   orchestration dilemmas · the chosen strategy · learning curves · screenshots of the live GUI and
   of the replay viewer showing `Verified OK` · the link to the companion repo), and the submission
   form filled, saved as PDF, submitted per team member.
3. **At least 2 scored league games against different teams**, reported, each game emailing the
   commit hash it ran on.

Criteria 1 and 2 are **prepared and measured** unattended and **completed** by a human (creating a
public repo, pushing a tag, and submitting a form are outward-facing and irreversible). Criterion 3
is entirely human — it needs real opponent teams — and additionally **depends on 07-10** closing,
because reporting must work before a game is reportable (rules 32, 35). Evidence:
`GATE-8-MEASUREMENT.md`, written by plan 08-11 and completed by 08-12 … 08-14.

## In scope / Out of scope (this phase)
- **In:** the §17 checklist audited end to end as a runnable gate; `.planning/REQUIREMENTS.md` and
  every other tracker reconciled project-wide in one pass; the documentation §17 names and this
  repo lacks (root README rewritten to §2.1 **and** §9.4.2, `LICENSE`, `CONTRIBUTING.md`,
  `PROMPT_LOG.md`, rendered C4/deployment/sequence diagrams, an ISO/IEC 25010 mapping, documented
  extension points, three missing per-mechanism PRDs, an offline analysis notebook, a sensitivity
  analysis, a token-cost analysis); the league ledger and the first production caller for the
  `declaration_` artifact; the two-repo split built and verified locally; the tag prepared and
  verified; the two deferred `commit_reveal=False` evidence defects closed or formally accepted.
- **Out:** any change to the `Envelope` shape, the commit-reveal payload, the signed Step-0 field
  set, the scent or belief models, or Phase-3/4 strategy behaviour. No retraining. No new protocol
  message type. No reopening of a closed §10.4 gate. **Nothing in this phase invents a numeric
  value, a repo URL, a games-played figure or a self-assessment score.**

## Dependencies
- Depends on: Phase 7 (reporting and visualization shell). Specifically **plan 07-10** — the live
  send, the OAuth-authorised send-only client and the two presentation screenshots — which gates
  criterion 3 and supplies criterion 2's images.
- Phase 4 is `human_needed`: the live GATE-4 run completed 2026-08-09, but no verification pass was
  written to flip the status, and the **responder side was never live-measured** after 05-06
  changed responder hint composition. This phase records that honestly; it does not close it.
- No `07-VERIFICATION.md` exists — Phase 7 has never been through `/gsd:verify-work 7`, so
  REPORT-02 … REPORT-07 are implemented and gate-measured but not phase-verified.
- External: two public GitHub repositories (created by a human), real opponent teams, the
  submission form (its location is not recorded in any project document — see the open questions).

## Success metrics & test scenarios
- **The §17 gate can fail.** `scripts/check_submission.py` exits 0 all-pass, 1 on any GAP, and
  **2 on an evidence set that judged nothing**; the mechanism inventory is derived from the package
  tree, not from a `docs/PRD_*.md` glob (proven by planting an empty package); renaming one
  satisfied artifact flips exactly one row; rows the tool cannot judge print `UNJUDGED`, never PASS.
- **Reconciliation is honest in both directions.** Every `[x]` cites the verification artifact that
  proves it; every `[ ]` names what is outstanding; `Pending` survives only where an artifact says
  so; a check fails when a row claims Done while its cited artifact disagrees.
- **Nothing unpublishable can reach a public tree.** The secret scan runs over the tracked set and
  is paired with a **planted dummy secret it must catch**; each sensitive path is proven ignored by
  its own `git check-ignore` assertion; the split is built from `git ls-files` and a planted
  untracked file appears in neither output.
- **Each split repo passes Table 5 inside its own tree** — ruff 0, `uv sync` resolves,
  `pytest --cov` ≥ 85% compared against the mono-repo's 97.37%, and the line-limit gate reporting a
  **scanned-file count > 0** (its no-argument form enumerates via `git ls-files`, which is empty in
  a fresh tree before the first commit and passes vacuously).
- **The declaration artifact stops being dead code.** `write_declaration_artifact` gains a
  grep-proven production caller, and a real `dev_launch.py` game leaves a `declaration_` file
  carrying repo URLs, MCP addresses, the agreed token ceiling and start/end times.
- **The games-played declaration is derivable and falsifiable.** The count comes from the league
  ledger, never from `games_played.json`; an honest count passes the check and an inflated one
  fails.
- **Standing gates:** ruff 0 · coverage ≥ 85% · every file ≤ 150 code lines · `uv` only · no
  secrets · no invented numbers · every test offline.

## Design decisions (phase ADRs)
D-76 … D-82 — recorded authoritatively in
[08-PLAN-OUTLINE.md §3](../../../.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md).
Headline four: **D-76** (the split is built from `git ls-files` into a destination outside this
tree — a directory walk would publish the untracked `.env` and the copyrighted book PDF sitting in
the working tree today), **D-77** (each repo ships **both** role config directories, because
twenty-plus tests load both and a one-role repo cannot pass Table 5 inside its own tree; the two
live counter files ship in neither), **D-80** (the games-played declaration is derived from a league
ledger and never read back from `games_played.json`, which reads 1922 and 1915 for one team),
**D-82** (§17 is enforced as a script with the `measure_gate7.py` exit contract, because a prose
checklist cannot fail).

## Open questions carried into execution
Nine are recorded rather than invented; the full text is in
[08-PLAN-OUTLINE.md §4](../../../.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md).
The four that need a **human, not Claude**: the D7-17 `game_id`-per-game-vs-per-series protocol
question (OQ8-1 — routed with three costed options and "ask the lecturer"); the games-played
**value** (OQ8-2, rule 38, absolute); the self-assessment **score** (OQ8-4, rule 55); and the
licence (OQ8-5). Three are unknowable until a human acts: the submission form's location (OQ8-3 —
recorded in no project document), the two repo URLs (OQ8-6), and whether the existing `origin` is
already public (OQ8-9). Two are open readings: the agreed per-series token ceiling (OQ8-7, Table 18
row 4 is an *example*, status negotiable) and whether §9.4.2 mandates a Hebrew README (OQ8-8).
