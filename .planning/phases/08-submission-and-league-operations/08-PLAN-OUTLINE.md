# Phase 8 Plan Outline — Submission and League Operations

**Phase:** `08-submission-and-league-operations` · **Written:** 2026-08-17 · **Plans:** 08-01 … 08-14
**Context:** [`08-CONTEXT.md`](08-CONTEXT.md)
**Requirements:** SUB-01 … SUB-12, plus the project-wide QUAL/DOC reconciliation
**Gate:** the submission gate — *(1) two cross-linked public repos (cop, thief), each carrying
README/config/PRD/PLAN/TODO, with a Git tag on the submitted version; (2) academic README with its
six §9.4.2 sections, submission form filled and saved as PDF, submitted per team member; (3) at
least 2 scored league games against different teams and reported, each game emailing the commit
hash it ran on.*

**Standing gates apply to every plan and are not restated per plan:** `ruff check` → 0 ·
`pytest --cov` ≥ 85% · every file ≤ 150 code lines · `uv` only · zero invented numbers · zero
secrets in source · tests offline.

This phase builds almost no new game behaviour. It is **audit, reconciliation, documentation and
packaging** — and then three short human sessions that publish, play and submit. The spine is
`docs/SEGAL_GUIDELINES.md` §17 (the six-group final checklist) and §19.1 Table 5; the
Phase-8 ROADMAP rows 08-01 … 08-04 are a subset of it.

---

## 1. The structural decision — the human appears three times, at the very end

Everything that is **outward-facing or irreversible** is isolated into three `autonomous: false`
plans in waves 5–7. Claude must not, and will not: create or push to a public repository, push a
git tag, mail the lecturer, play a league game against a real team, or enter a credential or click
a consent screen.

Everything else — and it is the large majority of the phase — runs with **no human present**:

| Unattended (08-01 … 08-11) | Human-gated (08-12, 08-13, 08-14) |
|---|---|
| the §17 checklist audited end to end, gaps listed with exact paths | creating the two public repos, pushing them |
| `.planning/REQUIREMENTS.md` + every other tracker reconciled project-wide, **one pass** | pushing the tag |
| the academic README **drafted in full** | reviewing and approving the README |
| the two-repo split built LOCALLY and verified, **nothing pushed** | mailing the lecturer (incl. the D7-17 question) |
| the tag prepared, its content verified, **not pushed** | playing the ≥2 scored league games |
| `LICENSE`, `CONTRIBUTING`, ISO 25010 map, extension points, prompt log, notebook, token-cost analysis | the self-assessment **score**, the games-played **value**, the form PDF |
| the league ledger, the declaration wiring, the per-game config naming | filling the real repo URLs into `league.json` |

The three human sessions are short and scripted, following the GATE-4 live-run / GATE-5
remote-round / 07-10 OAuth precedent: a runbook is written by an unattended plan and the human
executes it.

**One item has lead time and must not wait for wave 5.** The D7-17 question to the lecturer
(§4, OQ8-1) is *drafted* by 08-04 in wave 1 and can be sent by the human on any day from then on.
The outline places the send in 08-12 for bookkeeping; in practice it should leave the building the
day Phase 8 starts, because the answer gates nothing Claude can do but may gate the league games.

---

## 2. Dependencies outside this phase — stated, not assumed

- **08-13 (league games) depends on 07-10 closing first.** Rule 32 sanctions a *missing report*
  per game and rule 35 zeroes **both** teams when one side fails to report. 07-10 is the plan that
  authorises the send-only OAuth client and proves one live send end to end; until it closes,
  `GATE-7-MEASUREMENT.md` records criterion 1 as `dry_run` PASS + **live PENDING**, and every
  `reporting.json` this repo ships still reads `dry_run`. **Reporting must work before games are
  reportable** — playing a scored game before 07-10 risks a 0/0 for us *and* for an innocent
  opponent.
- **08-13 also depends on 08-12**, because rule 53 requires the Step-0 declaration to carry the
  commit hash the game ran on and rule 49 requires four repo links in the JSON. A commit hash that
  resolves nowhere public is not evidence.
- **Phase 4 is `human_needed`.** `04-VERIFICATION.md` records `human_needed`; the live GATE-4 run
  did complete (2026-08-09, `gate4_measurement_live.json`, real `claude-haiku-4-5-20251001`), but
  no verification pass was ever written to flip the status, and `GATE-4-MEASUREMENT.md` states in
  its own words that **the responder side was never live-measured** after 05-06 changed responder
  hint composition on 2026-08-14. 08-02 must record LANG-01/LANG-06 accordingly and must not tick
  them.
- **No `07-VERIFICATION.md` exists** — Phase 7 has never been through `/gsd:verify-work 7`. So
  REPORT-02 … REPORT-07 are implemented and gate-measured but *not phase-verified*. 08-02 records
  that distinction rather than erasing it.

```
07-10 (human: OAuth + one live send)
   |
   +-----------------------------> 08-13 (human: league games)
                                      ^
08-12 (human: publish repos + tag) ----+
```

---

## 3. Decisions — D-76 … D-82

Highest existing decision is D-75 (Phase 7). Resolved under the autonomy directive from the book
extracts and from what is measurably in the tree. `08-CONTEXT.md`'s locked choices — clean
snapshot repos, team code `khm-mn17`, more than the minimum games, English README pending a
§9.4.2 check — are inherited, not re-derived.

| ID | Decision | Source / evidence |
|----|----------|-------------------|
| **D-76** | **The split is built from `git ls-files`, into a destination OUTSIDE this repository tree.** Never a directory walk, never git surgery on the mono-repo. | `.env` and `police_thief_p2p.pdf` sit **untracked in the working tree right now**; a directory walk publishes a live credential file (rules 39–40, project failure) and a copyrighted textbook in one step. `git ls-files` returns 895 paths and neither of those. |
| **D-77** | **Each public repo ships BOTH `config/police/` and `config/thief/`, and ships neither `games_played.json` nor `games_played.prev.json`.** | Twenty-plus integration tests plus `tests/conftest.py`, `tests/integration/conftest.py` and `tests/_shipped_config_guard.py` load **both** role directories. A repo carrying one role's config cannot run its own suite, so it cannot pass Table 5 inside its own tree — and re-pointing the suite at fixtures days before the deadline changes shipped test behaviour for cosmetic reasons. Rule 50 sets a floor (`config/` present), not a ceiling; rule 2 forbids shared *runtime state*, which two static directories are not. The counters are excluded because they are live rule-37 state and because the two files **disagree** (police `1922`, thief `1915`). |
| **D-78** | **`.planning/` and `docs/phases/` ship.** The exclusion list is exactly: live state, secrets, build artifacts, and the book PDF. | §17's "orderly Git history, documented work process" and §2.5's mandatory process are evidenced by nothing else in the tree. An allow-list of docs risks dropping something rule 50 requires; an exclude-list of four known-bad categories does not. Reversible at 08-12 if the human disagrees. |
| **D-79** | **The tag is cut on the split outputs, never on the mono-repo, and its name is derived from `src/pursuit/shared/version.py`.** | `VERSION = "1.00"`; `pyproject.toml` reads `version = "1.00.0"`. The two must be reconciled before a tag name is derived from either. `git tag -l` is empty today and `main` is **122 commits ahead of `origin/main`** — the mono-repo's remote is not the submission target. |
| **D-80** | **The league ledger is the single source of the games-played declaration.** The declared count is *derived* from a durable per-opponent ledger; `games_played.json` is never read back into it. | Rule 38 is absolute. `agent_step0_wiring.py`'s own docstring records the measurement: one `uv run pytest tests/` advanced the two counters by +14 each for zero games, and they disagreed by seven for two agents that have only ever played each other. 07-00 fixed the *mechanism*; the *value* is 08-14's. |
| **D-81** | **Every league-day identity value lives in a new `config/{police,thief}/league.json`** — the two repo URLs, the MCP server addresses, the opponent's two URLs, the agreed token ceiling. Zero hardcoded URLs; the loader **refuses a placeholder when `reporting.mode = live`** and permits it in `dry_run`. | Rule 49 wants two links in the form and **four** links in both teams' JSON; PARAMETERS:165 names repo URLs, MCP addresses, agreed token ceiling and start/end times as declaration content. `DeclarationContext.__post_init__` already refuses to default `token_ceiling` — that refusal is load-bearing and must survive. |
| **D-82** | **§17 is enforced as a script with the `measure_gate7.py` exit contract — 0 all-pass, 1 any GAP, 2 on an evidence set that judged nothing** — not as a prose checklist. | A prose checklist cannot fail. The 07-09 precedent (five mutation probes broke the real subject and the gate went FAIL each time; an emptied evidence set exits 2, never 0) is the standard this phase inherits. |

**Not in scope:** any change to the `Envelope` shape, the commit-reveal payload, the signed Step-0
field set, the scent or belief models, or Phase-3/4 strategy behaviour. No retraining. No new
protocol message type. Phase 8 does not reopen a closed gate.

---

## 4. Open questions — flagged, never invented

**OQ8-1 — D7-17: `game_id` is minted per GAME, PARAMETERS reads it as the SERIES id.**
`PARAMETERS.md:157-159` and `:168` describe `result_<game_id>.json` as the summary "across all
sub-games"; `:72` settles ties on that aggregate; `:86` (rule 52) says there is **one scoring game
only** per opponent, which is what production produces today. `game_id` is **peer-negotiated**
(D-61), so redefining it is a protocol decision over a value we do not solely control. Three costed
options plus "ask the lecturer" are written out in
[`GATE-7-MEASUREMENT.md`](../../../docs/phases/phase-7/GATE-7-MEASUREMENT.md) §"D7-17 in full".
**Claude drafts the question in 08-04; a human sends it.** No scheme is invented here.

**OQ8-2 — the games-played VALUE (rule 38, absolute disqualification).**
`config/police/games_played.json` reads **1922** and `config/thief/` reads **1915** today — one
team, two counters, disagreeing by seven. The reading of "a game played" (Option A/B/C) and the
resulting number are decided by the human from
[`GAMES-PLAYED-RECONSTRUCTION.md`](../../../docs/phases/phase-7/GAMES-PLAYED-RECONSTRUCTION.md) §6,
whose §8 is a five-box checklist. Under Option A the value must lie in `[0, 10]` to be consistent
with Table 18 row 5 (`max games per team` = 10, **fixed**). Not Claude's to pick.

**OQ8-3 — where the submission form lives.** Rule 43 says "download the submission form"; neither
`docs/PARAMETERS.md` §Addresses (which names only `rmisegal@gmail.com` and
`rmisegal+uoh26finalgame@gmail.com`) nor `docs/RULES.md` gives a URL, a Moodle location, or a file
name. **No location is guessed.** 08-11 writes the fill-in notes; 08-14's human supplies the form.

**OQ8-4 — the self-assessment SCORE (SUB-11, rule 55).** A numeric claim about our own work,
restricted to code quality and explicitly **not** league results. 08-11 drafts the *evidence table*
with the score field blank; 08-14's human writes the number.

**OQ8-5 — which licence.** §17 requires a licence and none exists. Publishing one is a legal
declaration about someone else's coursework repository. 08-03 creates the file only once the human
names the licence; until then the plan carries a `LICENSE` placeholder that 08-01's checker reports
as a GAP so it cannot ship unnoticed.

**OQ8-6 — the two public repo names/URLs.** They do not exist until 08-12. Hardcoding a guessed
`github.com/...` string is the invented-value failure in its most tempting form; D-81 puts them in
config with a live-mode refusal.

**OQ8-7 — the agreed `token_ceiling` per series.** Table 18 row 4 gives ~200,000, status
**negotiable** — an example, not a value. The real figure is agreed with the lead team per
opponent at league time. `DeclarationContext` already refuses to default it; keep that refusal.

**OQ8-8 — README language.** `08-CONTEXT.md` says English and instructs the planning-day
researcher to check whether §9.4.2 mandates Hebrew, "and if it does, Hebrew wins". The extracts in
`docs/` do not settle it. 08-06 must confirm against the book before writing, not assume.

**OQ8-9 — is `origin` public or private?** `main` is 122 commits ahead of
`https://github.com/khaledmanaa11/AI_ORCHISTRATION_final_project.git`. If that repo is already
public, some of what D-78 ships is already published and the secrets scan in 08-03 becomes urgent
rather than preventive. Cannot be determined offline; first item of 08-12.

---

## 5. The §17 audit — gaps already found, with paths

Measured against the current tree, not predicted. These are 08-01's expected findings; 08-01 still
re-derives them mechanically so the list cannot rot.

### Group 1 — Structure & documentation

| Gap | Where it must land |
|---|---|
| **The root README describes a system this repo does not ship.** Line 7 says moves are decided "with a trained tabular **Q-learning** policy (Bayes + BFS fallback)", which Phase 3 withdrew as unsound under simultaneous play; the shipped mover is a matrix-game solver over a learned 15-weight evaluation (`docs/phases/phase-3/PRD.md` §2). Its status table also still calls Phase 3 "in progress". **This is a false description of the system in the single most grader-facing file** (rule 42). | `README.md` |
| Root README fails §2.1's user-manual bar on six of seven items: no prerequisites/step-by-step install/troubleshooting, **no usage instructions at all** (no cop/thief launch, no CLI flags, no GUI launch despite `gui/live_app.py` and `gui/replay_app.py` shipping), no screenshots, no configuration guide, no contribution guidelines, no licence/credits. ~90% of the file is the Phase-3 curves report. | `README.md`, `CONTRIBUTING.md` |
| No `LICENSE` file anywhere; `pyproject.toml` has no `license` and no `authors`. | `LICENSE`, `pyproject.toml` |
| No prompt-engineering log (§8.3, named in §17). | `docs/PROMPT_LOG.md` |
| Every diagram in `docs/PLAN.md` is ASCII art in a code fence — `grep -rl '```mermaid' docs/` returns nothing. §17 wants "clear diagrams". | `docs/PLAN.md` / `docs/ARCHITECTURE.md` |
| Three central mechanisms have no root per-mechanism PRD (§2.3, "critical requirement"): the **SDK layer** (`src/pursuit/sdk/`, the mandated single entry point), the **tunnel** (`network/tunnel_manager.py` — `PRD_mcp_transport.md` explicitly puts it out of scope), and the **`gui/` rendering/replay mechanism** (`PRD_display_belief.md` covers only what a view may *contain*). Thirteen PRDs exist; these three are absent. | `docs/PRD_sdk.md`, `docs/PRD_tunnel.md`, `docs/PRD_gui.md` |

### Group 2 — Architecture & code
PASS: SDK layer, one gatekeeper reused as two instances, rate limits in config, `ruff check` 0,
the ≤150 gate enforced twice (pre-commit hook **and** the `line-limit` CI job).
**GAP:** most sub-package `__init__.py` files export nothing — only `strategy/__init__.py` defines
`__all__`, and `__version__` exists nowhere outside `shared/version.py` (§14, "professional Python
packaging"). Minor: no single `config/rate_limits.json` as §2.4's recommended layout names it;
the values are config-driven but scattered per mechanism.

### Group 3 — Testing & quality
PASS: coverage 97% against a `fail_under = 85` gate, ruff 0, CI runs `ruff` + `pytest --cov`,
20+ per-phase gate-measurement scripts.
**GAP:** no automated test-report artifact is produced or stored — no `coverage.xml`, no JUnit XML,
no HTML report. §17 names "automated test reports" explicitly.

### Group 4 — Configuration & security
**The strongest group: no gaps found.** `.env-example` is 43 lines of placeholders; `.env` is
untracked and matched by `.gitignore:11`; the credential patterns §7.4 lists are all covered;
`uv.lock` + `pyproject.toml` present with no stray `requirements.txt`; `version.py` reads `1.00`
and every config file carries a matching `"version": "1.00"` except `weights.json` at `"2.00"`
(a deliberate bump); a scan of the tracked set for `sk-ant-` / `AIza` / `ghp_` / literal
`api_key = "..."` found **zero** hits.

### Group 5 — Research & visualization
PASS: `artifacts/curves/{winrate_cop,winrate_thief,mean_reward}.png` + `curves.csv`, discussed in
the README with a McNemar correction — real statistical work, instrumented from episode 1.
**GAP:** no analysis notebook anywhere (`*.ipynb` → zero, and no `notebooks/` despite §2.4);
**no token-cost analysis document** and no optimization strategy, though §17 names both and
`TokenBudget.report()` already produces the data; no sensitivity analysis outside the Phase-3
curves — nothing for gatekeeper limits, belief parameters or scent decay; no screenshots.

### Group 6 — Extensibility & standards
PASS: 486 commits in a consistent conventional-commit style, tagged by phase; concurrency guidance
in `docs/PLAN.md` §7; genuine building-block decomposition (`network/` alone is 46 single-purpose
files).
**GAP:** no git tag (expected, rule 41 — this phase); only one repo, not two (rule 49); no
`LICENSE`; **no deployment instructions** beyond one ASCII topology diagram; **ISO/IEC 25010 has
exactly one line of content in the whole repo** (`docs/PRD.md:94`) against an explicit §17 item —
no characteristic-by-characteristic mapping; **no documented extension points**, though `BrainBase`
in `strategy/__init__.py` is a real extension seam.

### A documentation defect found while reading, worth one line in 08-02
`docs/RULES.md:83` (rule 48) writes the scoring table as "capture 20/5, survival **10/5**" while
`docs/PARAMETERS.md` Table 17 rows 3–4 give cop **5** / thief **10**, and rule 48's own capture
figure uses cop-first ordering. `.planning/REQUIREMENTS.md` BASE-07 writes "survival 5/10". Same
numbers, contradictory ordering, in two grader-facing extracts. Fix the extract; **do not touch a
fixed value.**

---

## 6. Requirements reconciliation — one pass over every tracker, never one row

`.planning/REQUIREMENTS.md` holds **77** requirement checkboxes of which **6** are ticked
(`BASE-01`, `BASE-08`, `CLOUD-01`, `CLOUD-02`, `QUAL-01`, `QUAL-06`); its own header at line 191
claims "74 total" while its per-family breakdown sums to 77, so the header is **wrong by 3** and
the "Unmapped: 0 ✓" claim built on it is unsupported. Its traceability table at **lines 179-188**
reads `Pending` for all ten rows — including Phase 3, Phase 5 and Phase 6, whose own
`NN-VERIFICATION.md` files read `passed` and whose `GATE-N-MEASUREMENT.md` files read PASS on every
§10.4 criterion.

**It is fixed as a whole or not at all.** Ticking the phases that are done, without simultaneously
recording the ones that are *not*, replaces "understates the repo" with "overstates the repo" —
and the second error is the one rule 38's neighbourhood punishes. Four other files carry the same
staleness and must move in the same commit:

| File | What is stale |
|---|---|
| `.planning/REQUIREMENTS.md` | 77-vs-74 header; six ticks against ~50 satisfied; all ten traceability rows `Pending`; STRAT-01/02 still describe the **withdrawn** tabular Q-learning mechanism |
| `docs/TODO.md` | Phase 1 has **no** gate banner and every row `☐`, against `01-VERIFICATION.md` `passed` (2026-07-28) — the largest single doc/reality gap; Phase 7's section lists 5 coarse rows and does not reflect 11 of 12 plans executed; the triplet table at 198-213 shows Phase 1 `◐/◐/◐` and "All TODOs ☐" for Phases 2–3 |
| `.planning/ROADMAP.md` | the Progress table says Phase 7 is *"Not started — not yet planned"* |
| `docs/phases/phase-1/TODO.md` | row `1-99` and the phase-gate checklist unticked despite verified evidence |
| `docs/phases/phase-6/gate6_measurement_evidence.json` | predates 05-15; a one-command refresh |

**Truth order:** `NN-VERIFICATION.md` verdict → `GATE-N-MEASUREMENT.md` measured criteria →
SUMMARY counts. A tracker's own banner is **not** evidence for that tracker. Where a verification
artifact and a tracker disagree, record the disagreement; do not pick the friendlier one.

**What must stay unticked, with the reason written in:** LANG-01 and LANG-06 (responder side never
live-measured after 05-06); REPORT-01 (live send PENDING, 07-10 not run); REPORT-02 … REPORT-07
(implemented and gate-measured, but **no `07-VERIFICATION.md` exists**, so no phase-verified
record); all twelve SUB-*; DOC-01's "kept current" clause, which is the very thing under audit.

---

## 7. Where the work goes

```
scripts/
  check_submission.py + submission_*.py   the §17 + Table-5 gate, exit 0/1/2            (08-01)
  check_publication_safety.py             tracked-set secret + ignore-rule scan          (08-03)
  build_split_repos.py + split_*.py       git-ls-files -> two repos outside the tree     (08-10)
  check_requirements_ledger.py            a claim without a cited artifact fails         (08-02)

src/pursuit/services/reporting/
  league_ledger.py                        per-opponent scoring ledger, derived count     (08-04)
  artifact_declaration.py                 (call site only) its first production caller   (08-04)
src/pursuit/shared/
  league_config.py                        loader; refuses placeholders when mode=live    (08-04)
config/{police,thief}/
  league.json                             repo URLs, MCP addresses, token ceiling        (08-04)

README.md                                 §2.1 manual + §9.4.2 academic report           (08-06)
CONTRIBUTING.md · LICENSE                                                                (08-03/08-06)
docs/
  ARCHITECTURE.md                         C4 x4 + deployment + commit-reveal sequence    (08-07)
  QUALITY-25010.md                        eight characteristics -> repo evidence         (08-07)
  EXTENSION-POINTS.md                     BrainBase, MailSink, provider registry          (08-07)
  PRD_sdk.md · PRD_tunnel.md · PRD_gui.md the three missing per-mechanism PRDs           (08-08)
  PROMPT_LOG.md                           §8.3                                           (08-09)
  SENSITIVITY.md · TOKEN-COST.md                                                          (08-09)
  SUBMISSION-CHECKLIST.md                 the living gap register                        (08-01)
  SELF-ASSESSMENT.md                      evidence table, score field BLANK              (08-11)
notebooks/analysis.ipynb                  executes offline from tracked artifacts        (08-09)

docs/phases/phase-8/
  GATE-8-MEASUREMENT.md                   the submission gate, measured                  (08-11)
  SPLIT-RUNBOOK.md   LEAGUE-RUNBOOK.md    written by 08-10/08-11, run by 08-12/08-13
  SUBMISSION-RUNBOOK.md                                                                  (08-11 writes, 08-14 runs)
```

`scripts/` is **not** scanned by `check_line_limit.sh` (its glob is `src/** tests/** training/**`),
so logic that migrates there dodges both the 150-line gate and coverage. Every new script is split
into siblings the way `gate7_*.py` was — for the same reason, not to hide code.

---

## 8. Plans and waves

```
w1:  08-01 §17 audit    08-02 tracker reconciliation    08-03 publication hygiene
     08-04 league machinery + declaration wiring        08-05 deferred #13/#19
             \                |                /                    |
w2:  08-06 README   08-07 architecture docs   08-08 missing PRDs   08-09 research & viz
                          \        |        /
w3:                        08-10 two-repo split, built LOCALLY, nothing pushed
                                    |
w4:                        08-11 tag prepared + graph refresh + GATE-8 + runbooks
                                    |
w5:                        08-12  *** autonomous: false ***  publish repos + tag
                                    |
w6:                        08-13  *** autonomous: false ***  league games   (also needs 07-10)
                                    |
w7:                        08-14  *** autonomous: false ***  submit
```

| Plan | Delivers | Wave | Depends on | Auto |
|---|---|---|---|---|
| **08-01** | The §17 + Table-5 audit as a runnable gate, and `docs/SUBMISSION-CHECKLIST.md` as its gap register | 1 | — | yes |
| **08-02** | `.planning/REQUIREMENTS.md` + `docs/TODO.md` + `ROADMAP.md` Progress + the phase-1 triplet reconciled **in one pass** | 1 | — | yes |
| **08-03** | Publication hygiene made machine-checkable; `LICENSE`, `CONTRIBUTING.md`, packaging metadata | 1 | — | yes |
| **08-04** | League machinery: the opponent ledger, `league.json`, and the **first production caller** for the declaration artifact; the D7-17 question drafted | 1 | — | yes |
| **08-05** | Deferred #13 and #19 closed, or formally accepted with re-measured evidence | 1 | — | yes |
| **08-06** | The root README rebuilt to §2.1 **and** §9.4.2 — the phase's largest single document | 2 | 08-01 | yes |
| **08-07** | Architecture docs: C4 ×4, deployment, commit-reveal sequence, ISO 25010 map, extension points | 2 | 08-01 | yes |
| **08-08** | The three missing per-mechanism PRDs, derived from the package tree | 2 | 08-01 | yes |
| **08-09** | Sensitivity analysis, offline analysis notebook, token-cost analysis, prompt log | 2 | 08-01 | yes |
| **08-10** | Two split repos built LOCALLY from `git ls-files`, each independently passing Table 5 inside its own tree | 3 | 08-02 … 08-09 | yes |
| **08-11** | Tag prepared and verified (**not pushed**), graph refreshed (08-96), `GATE-8-MEASUREMENT.md`, three runbooks, self-assessment evidence | 4 | 08-10 | yes |
| **08-12** | **Human:** create + push the two public repos, push the tag, fill real URLs, send the lecturer question | 5 | 08-11 | **NO** |
| **08-13** | **Human:** ≥2 scored league games vs different teams, live-reported | 6 | 08-12, **07-10** | **NO** |
| **08-14** | **Human:** submission form PDF, self-assessment score, games-played sign-off, per-member submission | 7 | 08-13 | **NO** |

Wave 1 is a genuine five-way fan-out — the audit script, the trackers, `.gitignore`/licence, the
`services/reporting` + `config/` code, and `network/turn_buffer.py` share no file. Run each in its
own git worktree, per the parallel-executor rule. Wave 2 is a four-way fan-out over four disjoint
document sets.

---

## 9. Per-plan objective, files, measurable acceptance, and the trap

Traps are drawn from what is actually in this tree.

### 08-01 — The §17 audit, as a gate that can fail
**Objective:** one command produces an honest PASS/GAP row for every §17 item and every Table-5
row, and the gap register becomes the input to waves 2–3.
**Acceptance:** exit **0** all-pass, **1** any GAP, **2** on an evidence set that judged nothing —
proven by a probe that empties the item list and must exit 2, never 0; the mechanism inventory is
derived from `src/pursuit/`'s package tree by AST/dir walk (the `local_truth_ast.py` /
`_pull_site_discovery.py` precedent) and **not** from a `docs/PRD_*.md` glob, proven by planting an
empty package and watching a new GAP row appear; a counter-control per group — renaming one
satisfied artifact (e.g. `.env-example`) flips exactly that row to GAP and no other; every GAP row
names the exact path where the fix must land; rows the tool **cannot** judge (e.g. "TDD, tests
written before/with the code") are printed as `UNJUDGED`, never scored PASS.
**Trap:** the tempting implementation greps for a filename and calls the group PASS. §17's bar for
the root README is §2.1's **seven** items individually — and the current README would pass a
"README.md exists" check while failing six of the seven. Second trap: `scripts/` escapes both the
150-line gate and coverage, so a 400-line audit script looks clean and is untested.

### 08-02 — Project-wide tracker reconciliation, one commit
**Objective:** every checkbox, every traceability row and every tracker banner rewritten from the
verification artifacts, in a single pass.
**Acceptance:** the header total equals the actual checkbox count (77, not 74); every `[x]` cites
the artifact that proves it and every `[ ]` names what is outstanding and where; all ten
traceability rows carry a verdict drawn from `NN-VERIFICATION.md` / `GATE-N-MEASUREMENT.md`, with
`Pending` surviving **only** where an artifact says so; STRAT-01/02 reworded to the mechanism that
actually shipped; `scripts/check_requirements_ledger.py` fails when a row claims Done while its
cited artifact says otherwise — **proven by flipping one row and watching it fail**, and by an
empty-ledger probe that must not print OK; `docs/TODO.md`, `ROADMAP.md`'s Progress table and
`docs/phases/phase-1/TODO.md` move in the same commit.
**Trap:** fixing one row. With BASE/NET/STRAT/SEC/CLOUD closed and LANG/REPORT/SUB genuinely open,
a partial pass leaves the file wrong in the *other* direction — and an overstated tracker is the
more dangerous error. Second trap: `docs/TODO.md` banners Phases 3, 5 and 6 as gate-MET; those are
the trackers' own claims about themselves. Cite the verification artifact, not the banner.

### 08-03 — Publication hygiene, made machine-checkable
**Objective:** nothing that must not be public can reach a public tree, and the packaging metadata
§17 demands exists.
**Acceptance:** the secret scan runs over the **tracked** set and is paired with a **planted dummy
secret that it must catch** — an all-clear from a scan that examined nothing certifies nothing;
`.env`, `.venv/`, `logs/`, `graphify-out/`, `graph.json`, `graph.html`, `run.log`, `.coverage`,
`scratchpad/` and `police_thief_p2p.pdf` are each proven ignored by an individual `git check-ignore`
assertion, not by one "`.gitignore` mentions env" check; D7-19's remaining half becomes a rule —
the four rule-50 artifact names stay un-ignored under `game_artifacts/` while every other shape
there is ignored, and the publication script **refuses** when `game_artifacts/` holds a JSON whose
`game_id` is not on the league ledger; `LICENSE` + `pyproject.toml` `license`/`authors` present
(gated on OQ8-5); `uv sync` still resolves after the metadata edit.
**Trap:** "no secrets" proven by grepping for `sk-ant`. The current tree passes that grep and still
has a live `.env` one careless `git add -f` from publication. The control is the planted secret,
and the scope is the tracked set — the scan that matters is the one run against the **split
outputs** in 08-10, not against this repo.

### 08-04 — League machinery, and the declaration artifact's first production caller
**Objective:** the `declaration_` wrapper, the per-opponent scoring ledger and the per-game commit
hash stop being untested intentions.
**Acceptance:** `write_declaration_artifact` has a **grep-proven production caller** — today
`grep -rn "write_declaration_artifact\|DeclarationContext" src/ scripts/` returns only its own
module and the `__init__.py` re-export, so REPORT-06's declaration wrapper is **dead code**; a real
`dev_launch.py` game must leave a `declaration_<game_id>.json` carrying `repo_urls`,
`mcp_server_addresses`, `token_ceiling`, `start_time`, `end_time`; rule 49's **four** links are
carried when the peer supplies theirs and their **absence is recorded honestly**, never defaulted;
the ledger refuses a second *scoring* game against an already-scored opponent (rule 52) while
permitting unscored warm-ups, and refuses beyond `max games per team` = **10** (Table 18 row 5,
fixed); the declared games-played count is **derived from the ledger**, with a counter-control pair
— the honest count passes and an inflated one fails (rule 38); the D7-17 question is drafted as a
committed file with both PARAMETERS citations quoted.
**Trap:** the URLs do not exist yet. A guessed `github.com/...` literal is the invented-value
failure wearing its most reasonable disguise; D-81 puts them in config with a live-mode refusal.
Second trap: seeding the ledger from `games_played.json`. Those two files read 1922 and 1915 and
07-00's own docstring records why — one `pytest` run moved them +14 each for zero games. The ledger
starts empty and is fed only by completed league games.

### 08-05 — Deferred #13 and #19: closed, or accepted with evidence
**Objective:** two latent `commit_reveal=False` evidence defects stop being open text in a phase-5
file no grader will open.
**Acceptance:** either (a) both closed, each with a revert probe that fails against pre-plan code;
or (b) both formally accepted in `docs/SUBMISSION-CHECKLIST.md` with the shipped-config evidence
**re-measured at HEAD** (`config/{police,thief}/security.json` both `"commit_reveal": true`), and
the existing scope-asserting test — the one that **fails deliberately when the defect is closed**
— left in place so the record cannot rot.
**Trap:** `src/pursuit/network/turn_buffer.py` sits at **146 of 150** code lines. #19's repair needs
room, and the answer is the split the phase-5 record already names (`await_move` /
`drain_trailing_hint` away from `reject_peer_payload` / `log_illegal` / `send_hint`) — a split,
never a compression. Second trap: "latent" is a claim about the shipped config, and it expires the
moment someone flips the toggle; if (b) is chosen, the acceptance must be tied to a test that reads
the shipped files, not to a sentence.

### 08-06 — The root README: user manual and academic report in one file
**Objective:** one README that satisfies §2.1's seven items and §9.4.2's six sections, drafted
completely so a human only reviews it.
**Acceptance:** all seven §2.1 items present and non-empty (install/prereqs/troubleshooting ·
usage modes and flags · examples and screenshots · configuration guide · contribution guidelines ·
licence · credits) — checked individually by 08-01's gate; all six §9.4.2 sections present (the
chosen Dec-POMDP model · orchestration dilemmas · the chosen strategy · learning curves ·
screenshots of the live GUI and of the replay viewer showing `Verified OK` · the link to the
companion repo); the curves are the existing `artifacts/curves/*.png` with the generating command
recorded; the cross-link is a **config-sourced placeholder** that 08-01 reports as a GAP until
08-12 fills it, so it cannot ship empty; the GUI/replay screenshots come from 07-10.
**Trap:** the README currently states the agent decides moves "with a trained tabular Q-learning
policy (Bayes + BFS fallback)". Phase 3 withdrew that as unsound under simultaneous play and
shipped a matrix-game mover over a learned 15-weight evaluation. Copy-editing around the claim, or
keeping it because §9.4.2 item 4 asks for learning curves "since we use RL", makes a false academic
claim in the file rule 42 governs. Describe what was built, and show the curves the evolutionary
fit actually produced. Second trap: OQ8-8 — do not assume English.

### 08-07 — Architecture documentation with diagrams that resolve
**Objective:** the diagrams, quality model and extension points §17 names, in a form that renders.
**Acceptance:** all four C4 levels present as **rendered** diagrams (mermaid, which GitHub renders —
`grep -rl '```mermaid' docs/` returns nothing today); a deployment diagram covering two processes,
two tunnels and the Gmail path; a sequence diagram for Commit → Acknowledge → Reveal → Final
Reveal/Audit; **every component label in every diagram resolves to a real module path**, checked by
a script that parses the labels against `src/pursuit/` — a diagram naming a module that does not
exist is worse than no diagram; the eight ISO/IEC 25010 characteristics each mapped to concrete
repo evidence (a test, a script, a config file), never to prose; extension points documented
against the real seams (`BrainBase`, `MailSink`, the provider registry, the `[strategy]` config
block).
**Trap:** a mermaid block with a syntax error renders as a red error box on GitHub — the grader's
first impression becomes a broken page. Validate every block renders before committing. Second
trap: an ISO 25010 section that restates the eight characteristic *names* satisfies nothing; the
whole content of that item is the mapping.

### 08-08 — The three missing per-mechanism PRDs
**Objective:** close §2.3's "critical requirement" for the SDK layer, the tunnel, and the `gui/`
rendering/replay mechanism.
**Acceptance:** the mechanism inventory comes from the package tree (08-01's walk), and each entry
either has a `docs/PRD_<mechanism>.md` or a recorded reason it needs none; a probe adding an empty
package makes the check fail; each new PRD documents every number it uses **and the source of
each**; `docs/PRD_rl_strategy.md`'s superseded banner is verified still intact and pointing at
`PRD_matrix_mover.md`.
**Trap:** writing a PRD per *file* inflates the count and satisfies nothing — §2.3 is per
mechanism. Second trap: `PRD_display_belief.md` looks like GUI coverage and is not; it governs what
a view may *contain* (rules 8–9), not how the six `gui/` files render. Reading it as coverage
leaves the actual gap open under a green check.

### 08-09 — Research and visualization
**Objective:** the systematic experiments, notebook, sensitivity analysis and token-cost work §17
names, none of which exist outside the Phase-3 curves.
**Acceptance:** the sweep varies only parameters whose PARAMETERS status is `negotiable` or a
labelled engineering default, and the document **lists the fixed ones it did not touch**; the
notebook executes end to end offline from **tracked** inputs (`nbconvert --execute` exits 0), with
a probe proving it does not read `logs/`; the token-cost analysis is fed by real
`TokenBudget.report()` output from a recorded run, not an estimate, and states an optimization
strategy; `docs/PROMPT_LOG.md` records the actual prompts in `services/llm/` with their revisions.
**Trap:** varying a **fixed** parameter to produce a more interesting graph is a rule-1 / rule-12
violation dressed as research — Table 16, Table 17 and the 5×5 scent window are fixed. Second trap:
a notebook that reads `logs/` is empty on a clean checkout because `logs/` is gitignored; feed it
from `artifacts/` and `docs/phases/phase-5/remote-round-*/`, which are tracked.

### 08-10 — The two-repo split, built and verified LOCALLY
**Objective:** two publishable repos exist on disk, each provably safe and provably complete, with
nothing pushed.
**Acceptance:** built from `git ls-files` into a destination **outside** this repository tree, with
a probe planting an untracked `secret.txt` in the working tree proving it appears in neither
output; each output is a real git repo with exactly one initial commit, **zero remotes**, and no
commit in common with `origin`; each output independently passes the full Table-5 gate **run inside
that tree** — `ruff check` 0, `uv sync` resolves, `uv run pytest --cov` ≥ 85% with the percentage
**compared against the mono-repo's 97.37%**, and `check_line_limit.sh` reporting a scanned-file
count **> 0**; rule 50 checked per output (README, `config/`, PRD files, a PLAN file, TODO files);
each README cross-links the other (rule 49); each output carries `scripts/hooks` **and** the
documented `git config core.hooksPath scripts/hooks` step; `.github/workflows/` present with every
job referencing only paths that exist there; 08-03's publication scan re-run against both outputs.
**Trap:** `check_line_limit.sh`'s no-argument form enumerates via `git ls-files`, which in a freshly
`git init`ed tree **before the first commit is empty** — the gate passes vacuously. This exact
vacuity is already on record in `05-18-SUMMARY.md`; assert the scanned count. Second trap:
`[tool.coverage.run] source = ["src", "training"]`. A split that drops `training/` while leaving
`pyproject.toml` alone changes what coverage measures and can still exit 0 while measuring less
than it claims. Third trap: `git init` inside the mono-repo, or an inherited `origin` — one reflex
`git push` publishes 486 private commits to a public URL.

### 08-11 — Tag prepared, graph refreshed, GATE-8 measured, runbooks written
**Objective:** everything that can be true before a human acts, is true and measured.
**Acceptance:** `src/pursuit/shared/version.py` (`1.00`) and `pyproject.toml` (`1.00.0`) are
reconciled and the tag name is **derived** from the reconciled value, not chosen; the tag is created
in each split output and its content verified (`git show <tag>` lists the expected tree), and the
plan states in as many words that it is **not pushed**; `.planning/graphs/` refreshed and
`GRAPH_REPORT.md` committed (ROADMAP 08-96); 08-01's gate re-run at HEAD with every GAP either
closed or carrying a dated recorded reason; `GATE-8-MEASUREMENT.md` reports the three submission
criteria with the human-dependent halves as **PENDING**, never as a blanket PASS — the
`GATE-7-MEASUREMENT.md` criterion-1 precedent; `SELF-ASSESSMENT.md` drafted with the score field
**blank**; three runbooks written.
**Trap:** `git push --tags` by reflex. It is irreversible on a public repo, and the tag must land on
the commit the league games actually ran on — which is not known until 08-13. Second trap: writing
GATE-8 as PASS because everything Claude could do is done. Two of three criteria are structurally
human-completed; a gate that reports PASS on the strength of preparation is the failure mode 07-09
refused.

### 08-12 — **Human · publish** · `autonomous: false`
**What only the human can do:**
1. Determine whether `origin` is public or private (OQ8-9) before anything else.
2. Create the two public GitHub repos — account/consent screens; Claude must not.
3. Add a remote to each prepared output and `git push` — outward-facing and irreversible.
4. `git push` the tag on each.
5. Fill the two real URLs into `config/{police,thief}/league.json` and re-run 08-04's URL check so
   the declaration artifact stops carrying placeholders.
6. Send the D7-17 question (drafted in 08-04) to `rmisegal@gmail.com` — mailing the lecturer is
   human-only.
7. Re-run 08-03's publication scan against the **pushed** trees.
**Acceptance:** both repos reachable and cross-linking each other; the tag visible on both;
`league.json` holds real URLs and 08-01's placeholder GAP is closed; the question is sent and dated.
**Trap:** pushing from the mono-repo working directory. The split outputs live outside this tree
precisely so that a `git push` typed in the wrong window cannot reach a public URL.

### 08-13 — **Human · league games** · `autonomous: false` · also needs **07-10**
**What only the human can do:**
1. Arrange real opponent teams — Claude cannot.
2. One unscored connectivity warm-up per opponent, then the **one** scoring game (rule 52).
3. `reporting.mode = live` for the scored games only, using 07-10's authorised credential, and
   flipped back afterwards.
4. Confirm each report arrived at `rmisegal+uoh26finalgame@gmail.com` with the JSON **attached**
   and the commit hash inside it.
5. Record each game in the ledger; commit that game's four artifacts under their per-game names
   (SUB-12).
**Acceptance:** ≥ 2 scored games against **different** teams (Table 18 row 3, fixed minimum),
≤ 10 total (row 5, fixed); the ledger's derived games-played equals what went on the wire; verdicts
agree, or the disagreement is **reported as a disagreement**.
**Trap:** rule 35 zeroes **both** teams when either fails to report or the reports contradict. The
league-day temptation is to edit our report to match theirs and keep the points. That is rules
16/22/38 territory and it costs more than the game. Second trap: playing before 07-10 closes —
an unreportable win is a 0/0 for an innocent opponent as well as for us.

### 08-14 — **Human · submit** · `autonomous: false`
**What only the human can do:**
1. Obtain the submission form (OQ8-3 — its location is not recorded anywhere), fill it, save as
   PDF, alter nothing (rule 43).
2. Enter the two repo links (rule 49) and the team code `khm-mn17` (rule 45).
3. Set the self-assessment **score** — code quality only, never league results (rule 55).
4. Sign off the declared games-played value (OQ8-2, rule 38).
5. Submit per team member (rule 44; solo team = one submission).
6. If code changed after 08-12, re-push and move the tag to the final commit.
**Acceptance:** the PDF is saved unaltered; the submission is confirmed; the games-played figure in
the form equals the ledger's derived value and the value declared on the wire.
**Trap:** a self-assessment that quietly credits league performance. Rule 55 restricts it to code
quality, and the evidence table 08-11 drafts is deliberately all Table-5 and §17 rows.

---

## 10. Decision → plan coverage

| Plan | Owns |
|---|---|
| 08-01 | D-82 |
| 08-02 | — (reconciliation) |
| 08-03 | D-76 (the scan half) |
| 08-04 | D-80, D-81 |
| 08-05 | — (deferred-item closure) |
| 08-06 … 08-09 | — (documentation) |
| 08-10 | D-76, D-77, D-78 |
| 08-11 | D-79 |
| 08-12 … 08-14 | — (human evidence) |

## 11. Requirement and gate coverage

| REQ | Landed by |
|---|---|
| SUB-01 two cross-linked public repos | 08-10 (built + cross-links) · 08-12 (published) |
| SUB-02 README/`config/`/PRD/PLAN/TODO in every repo | 08-10 (checked per output) |
| SUB-03 academic README, six sections | 08-06 · screenshots from 07-10 |
| SUB-04 secrets ignored, `.env-example` with dummies | 08-03 · re-scanned in 08-10, 08-12 |
| SUB-05 Git tag on the submitted version | 08-11 (prepared) · 08-12 / 08-14 (pushed) |
| SUB-06 8-character team code | already shipped — `config/*/security.json` = `khm-mn17`; 08-10 checks it survives the split |
| SUB-07 ≥ min games vs different teams, count declared accurately | 08-04 (ledger) · 08-13 (played) · 08-14 (declared) |
| SUB-08 each game emails the commit hash | 08-04 (declaration wiring) · 08-13 (live) |
| SUB-09 submission form as PDF, unaltered | 08-11 (notes) · 08-14 (filled) |
| SUB-10 submitted per team member | 08-14 |
| SUB-11 self-assessment, code quality only | 08-11 (evidence) · 08-14 (score) |
| SUB-12 fixed/minimum/negotiable respected; per-game config attached | 08-04 · 08-13 |
| QUAL-01 … QUAL-13, DOC-01 … DOC-02 | 08-01 (audited) · 08-02 (recorded) · 08-03, 08-06 … 08-09 (gaps closed) |

| Submission-gate criterion | Prepared by | Human-completed by |
|---|---|---|
| 1 — two cross-linked public repos + tag | 08-10, 08-11 | 08-12 |
| 2 — academic README + form PDF, per member | 08-06, 08-11 | 08-14 |
| 3 — ≥ 2 scored games vs different teams, reported with commit hash | 08-04 | 08-13 (needs **07-10**) |

## 12. ROADMAP row → plan mapping

| ROADMAP row | Plans |
|---|---|
| 08-01 two cross-linked public repos | 08-10, 08-12 |
| 08-02 academic README + tag + team code | 08-06, 08-11, 08-12 |
| 08-03 ≥2 scored league games, auto-reported with commit hash | 08-04, 08-13 |
| 08-04 submission form, per-member submission, self-assessment | 08-11, 08-14 |
| 08-96 graph refresh · 08-97 triplet · 08-99 TODO closure | 08-11 · plan-phase (done) · verify-work |

Rows 08-01 … 08-04 are deliverable **groups**, not plans; §17 is wider than the four rows, which is
why the phase needs fourteen plans and why ten of them are unattended.

## 13. What `08-CONTEXT.md` gets wrong against the current tree

CONTEXT files are drafts, not specs. Recorded so the plans start from the tree.

1. **"each receives the shared `pursuit` library plus its role's config and brain"** — a repo with
   one role's config **cannot run its own test suite**. `tests/conftest.py`,
   `tests/integration/conftest.py`, `tests/_shipped_config_guard.py` and twenty-plus integration
   tests load both `config/police/` and `config/thief/`. D-77 ships both directories and excludes
   the two live counter files instead.
2. **"the academic README"** reads as a new document. It is a **rewrite of an existing file whose
   opening paragraph is factually wrong about the shipped strategy** — the harder job, and a rule-42
   honesty problem rather than a formatting one.
3. **"scored games land Aug 11–12"** — the dates in CONTEXT have passed. The schedule is stale;
   the ordering constraint (07-10 → 08-12 → 08-13) is what survives.
4. **CONTEXT says nothing about `.planning/REQUIREMENTS.md`**, which is the single most misleading
   file a grader could open: 6 of 77 ticked and ten `Pending` traceability rows for a project with
   five phases verified `passed`.
5. **CONTEXT treats the repo split as the phase's centre of gravity.** Measured against §17, the
   split is one plan; the documentation gaps (README, licence, prompt log, notebook, ISO 25010,
   extension points, three PRDs, token-cost analysis) are four.
6. **CONTEXT does not mention that `declaration_<game_id>.json`'s Phase-7 wrapper has no production
   caller**, so rule 49's four links and PARAMETERS:165's declaration content have never been
   written by a real game.
7. **"the planning-day researcher double-checks whether §9.4.2 mandates Hebrew"** — still
   unchecked. OQ8-8.

---

*Phase: 08-submission-and-league-operations*
*Written 2026-08-17 · plans 08-01 … 08-14 · human-gated: 08-12, 08-13, 08-14*
