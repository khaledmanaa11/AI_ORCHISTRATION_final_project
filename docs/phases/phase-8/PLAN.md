# Phase 8 PLAN — Submission and League Operations

**Version:** 1.00 · **Updated:** 2026-08-17

> How Phase 8 is built. The authoritative plan set lives in
> `.planning/phases/08-submission-and-league-operations/` (outline + 08-01…08-14); this file is the
> grader-facing map of it. Per-mechanism PRDs written this phase:
> [docs/PRD_sdk.md](../../PRD_sdk.md), [docs/PRD_tunnel.md](../../PRD_tunnel.md),
> [docs/PRD_gui.md](../../PRD_gui.md).

## Components

| Component | Files | Plan |
|---|---|---|
| §17 + Table-5 gate | `scripts/check_submission.py` + `submission_*.py` siblings, `docs/SUBMISSION-CHECKLIST.md` | 08-01 |
| Tracker reconciliation | `.planning/REQUIREMENTS.md`, `docs/TODO.md`, `.planning/ROADMAP.md`, `docs/phases/phase-1/TODO.md`, `scripts/check_requirements_ledger.py` | 08-02 |
| Publication hygiene | `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `pyproject.toml`, `scripts/check_publication_safety.py` | 08-03 |
| League machinery | `services/reporting/league_ledger.py`, `shared/league_config.py`, `config/{police,thief}/league.json`, `artifact_declaration.py` call site | 08-04 |
| Deferred defects | `network/turn_buffer.py` (split, not compressed), `network/turn_commit.py` | 08-05 |
| Academic README | `README.md` | 08-06 |
| Architecture docs | `docs/ARCHITECTURE.md`, `docs/QUALITY-25010.md`, `docs/EXTENSION-POINTS.md`, `docs/PLAN.md` | 08-07 |
| Missing PRDs | `docs/PRD_sdk.md`, `docs/PRD_tunnel.md`, `docs/PRD_gui.md` | 08-08 |
| Research & viz | `notebooks/analysis.ipynb`, `docs/SENSITIVITY.md`, `docs/TOKEN-COST.md`, `docs/PROMPT_LOG.md` | 08-09 |
| Repo split | `scripts/build_split_repos.py` + `split_*.py`, `docs/phases/phase-8/SPLIT-RUNBOOK.md` | 08-10 |
| Gate + runbooks | `GATE-8-MEASUREMENT.md`, `LEAGUE-RUNBOOK.md`, `SUBMISSION-RUNBOOK.md`, `docs/SELF-ASSESSMENT.md`, `.planning/graphs/` | 08-11 |
| Human checkpoints | publish · play · submit (no code) | 08-12, 08-13, 08-14 |

## Interfaces & contracts

- **`check_submission.py`** — the §17/Table-5 gate. Exit **0** all-pass, **1** any GAP, **2** on an
  evidence set that judged nothing (the `measure_gate7.py` contract). The mechanism inventory is
  derived from `src/pursuit/`'s package tree by AST/dir walk — the `local_truth_ast.py` /
  `_pull_site_discovery.py` precedent — never from a `docs/PRD_*.md` glob, which would be a
  tautology. Rows it cannot judge print `UNJUDGED`, never PASS.
- **`league.json`** (new, twelfth config block) — our two repo URLs, our MCP server addresses, the
  opponent's two URLs, and the agreed per-series token ceiling. Loader contract: **placeholders are
  permitted when `reporting.mode = dry_run` and refused when `live`.** Zero hardcoded URLs anywhere
  in `src/`.
- **`LeagueLedger`** — a durable, per-opponent record keyed on the opponent's team code. Refuses a
  second *scoring* game against an already-scored opponent (rule 52) while permitting unscored
  warm-ups; refuses beyond `max games per team` = 10 (Table 18 row 5, **fixed**). The rule-37
  games-played declaration is **derived** from it. `config/*/games_played.json` is never read back
  into the ledger.
- **`DeclarationContext`** — unchanged, and its refusal to default `token_ceiling` is load-bearing
  and must survive. This phase supplies its **first production caller**: today
  `grep -rn "write_declaration_artifact\|DeclarationContext" src/ scripts/` returns only the
  defining module and the package `__init__` re-export.
- **The split contract** — built from `git ls-files` into a destination **outside** this repository
  tree. Each output: one initial commit, **zero remotes**, no commit in common with `origin`,
  `scripts/hooks` present plus the documented `git config core.hooksPath` step, and an independent
  pass of the full Table-5 gate **run inside that tree**.

## Wave graph

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

Wave 1 is a genuine five-way fan-out and wave 2 a four-way one — run each executor in its own git
worktree, per the parallel-executor rule. **Everything through wave 4 runs unattended.** The three
things Claude must not do — publish a repository, mail the lecturer, play a real league game — are
isolated in waves 5–7, and nothing before them waits on a person.

**08-13 depends on 07-10 as well as on 08-12.** Rule 32 sanctions a missing report per game and
rule 35 zeroes **both** teams when one side fails to report, so reporting must work before a game is
reportable. Every `reporting.json` this repo ships still reads `dry_run`.

## Phase ADRs

| # | Decision | Rationale | Alternative / trade-off |
|---|---|---|---|
| D-76 | The split is built from `git ls-files`, into a destination **outside** this tree | `.env` and `police_thief_p2p.pdf` are untracked in the working tree right now; a directory walk publishes a live credential file (rules 39–40) and a copyrighted textbook | Copying the directory and deleting afterwards (rejected: the deletion is the step that gets forgotten) |
| D-77 | Each public repo ships **both** role config directories; neither ships `games_played*.json` | `tests/conftest.py`, `tests/integration/conftest.py`, `tests/_shipped_config_guard.py` and 20+ integration tests load both roles — a one-role repo cannot pass Table 5 in its own tree. The counters are live rule-37 state and disagree (1922 vs 1915) | Re-pointing the suite at fixtures (rejected: changes shipped test behaviour days before the deadline, for cosmetics) |
| D-78 | `.planning/` and `docs/phases/` ship; the exclusion list is exactly live state, secrets, build artifacts and the book PDF | §17's "orderly Git history, documented work process" and §2.5 are evidenced by nothing else in the tree; an exclude-list of four known-bad categories cannot silently drop something rule 50 requires | An allow-list of doc paths (rejected: one missed path is a rule-50 failure) |
| D-79 | The tag is cut on the split outputs, never on the mono-repo, and its name is derived from `shared/version.py` | `git tag -l` is empty and `main` is 122 commits ahead of `origin/main`; the mono-repo's remote is not the submission target. `version.py` reads `1.00` and `pyproject.toml` `1.00.0` — reconcile before deriving | Tagging the mono-repo (rejected: tags the wrong history at the wrong URL) |
| D-80 | The league ledger is the single source of the games-played declaration | Rule 38 is absolute. `agent_step0_wiring.py` records that one `pytest` run moved the two counters +14 each for zero games; 07-00 fixed the mechanism, not the value | Reading the counter files (rejected: they are polluted and they disagree) |
| D-81 | Every league-day identity value lives in `config/{police,thief}/league.json`; placeholders are refused when `mode = live` | Rule 49 wants four repo links in both teams' JSON and PARAMETERS:165 names the declaration's content; the URLs do not exist until a human creates them | Hardcoding the URLs (rejected: an invented value in the most tempting disguise) |
| D-82 | §17 is enforced as a script with the 0/1/2 exit contract, not as a prose checklist | A prose checklist cannot fail. 07-09's five mutation probes and its `EMPTY_EVIDENCE` exit 2 are the standard | A markdown checklist ticked by hand (rejected: it is exactly what `.planning/REQUIREMENTS.md` already is, and it is wrong) |

## Test plan (TDD)

- Every suite stays **offline**: no GitHub API, no live Gmail, no opponent, no network. The split is
  verified against a temporary destination directory, never against a remote.
- **Counter-controls are mandatory** wherever a check could pass vacuously: the secret scan is
  paired with a **planted dummy secret it must catch**; the §17 gate is paired with a renamed
  artifact that must flip exactly one row; the requirements ledger check is paired with a flipped
  row that must fail it; the games-played derivation is paired with an inflated count that must
  fail while the honest one passes.
- **Vacuity checks by name:** an emptied item list must exit **2**, never 0; no `parametrize` list
  may be built from a filesystem glob (an empty list SKIPS silently); `all_matched([])` is `True`;
  the line-limit gate in a fresh split tree scans **zero** files before the first commit and passes
  vacuously — assert the scanned count.
- **Revert probes** on every fix: 08-05's closures must fail against pre-plan code; 08-04's
  declaration wiring must fail without its call site.
- **Dead-code check:** `write_declaration_artifact`, the league ledger's derivation function and the
  publication scanner must each have a grep-proven **production** caller, not only test callers.
- Coverage target ≥ 85% (`fail_under = 85`), measured **inside each split output** as well as here.

## Per-mechanism PRDs written this phase
- [docs/PRD_sdk.md](../../PRD_sdk.md) — the SDK layer, §4's mandated single entry point.
- [docs/PRD_tunnel.md](../../PRD_tunnel.md) — the cloud-exposure mechanism; `PRD_mcp_transport.md`
  explicitly puts it out of scope, so it has had no root PRD.
- [docs/PRD_gui.md](../../PRD_gui.md) — the six-file `gui/` rendering and replay mechanism;
  `PRD_display_belief.md` governs what a view may *contain*, not how it renders.

## Risks

- **Publishing something that must not be public is this phase's disqualification risk.** A live
  `.env` and a copyrighted textbook sit untracked in the working tree, `game_artifacts/` is
  deliberately un-ignored, and `main` is 122 commits ahead of an existing remote. Mitigated
  structurally (built from `git ls-files`, into a destination outside the tree, with zero remotes on
  the outputs) and provably (a planted-secret control, per-path `git check-ignore` assertions, and
  the scan re-run against the split outputs and again after the push).
- **An overstated tracker is worse than an understated one.** `.planning/REQUIREMENTS.md` currently
  understates the repo (6 of 77 ticked, ten `Pending` rows). Fixing it row by row would replace that
  with an *overstatement* — and rule 38's neighbourhood punishes overstatement. It moves as one
  commit, cites its evidence, and leaves LANG/REPORT/SUB honestly open.
- **The README is factually wrong about the shipped strategy.** Its opening paragraph credits "a
  trained tabular Q-learning policy (Bayes + BFS fallback)", which Phase 3 withdrew as unsound under
  simultaneous play. Rule 42 governs this file. It is a rewrite, not a copy-edit.
- **Rule 35 zeroes both teams.** A missing or contradictory report costs an innocent opponent their
  points too. 08-13 is gated behind 07-10 for that reason, and the league runbook forbids "fixing" a
  disagreement to match the peer.
- **Line-limit pressure is anticipated.** `network/turn_buffer.py` is at 146/150 and 08-05's repair
  needs room — the answer is the split the phase-5 record already names, never a compression. And
  `scripts/` is not scanned by `check_line_limit.sh`, so every new script is split into siblings the
  way `gate7_*.py` was, not consolidated to hide code.
- **Nine open questions are recorded, not invented** (OQ8-1 … OQ8-9 in the outline). Four are
  human-only: the D7-17 protocol question, the games-played value, the self-assessment score, and
  the licence.
