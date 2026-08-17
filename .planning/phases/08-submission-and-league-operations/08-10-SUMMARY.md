---
phase: 08-submission-and-league-operations
plan: 10
subsystem: submission
tags: [repo-split, git-ls-files, table-5, rule-49, rule-50, publication-hygiene, vacuity, d-76, d-77, d-78]

# Dependency graph
requires:
  - phase: 08-submission-and-league-operations
    provides: "08-01's scripts/check_submission.py and submission_code.line_limit_scope -- the scanned-count refusal this plan's line-limit row copies"
  - phase: 08-submission-and-league-operations
    provides: "08-03's .gitignore rules, LICENSE and packaging metadata -- what makes the tracked set safe to copy wholesale"
  - phase: 08-submission-and-league-operations
    provides: "08-06's README -- the document the rule-49 cross-link block is injected into"
  - phase: 08-submission-and-league-operations
    provides: "08-04's config/*/league.json -- the placeholder-refusing precedent the stated-absent URLs follow"
  - phase: 07-reporting-and-visualization-shell
    provides: "07-00's tests/_shipped_config_guard.py -- the counter isolation whose read_counters contract two of the fixed tests contradicted"
provides:
  - "scripts/build_split_repos.py + split_{manifest,docs,build,verify,gates,report}.py -- one command that builds and verifies both submission repositories"
  - "C:/Users/Hp/pursuit-split-repos/pursuit-{police,thief} -- two built repositories, 12/12 rows each, zero remotes, nothing pushed"
  - "docs/phases/phase-8/SPLIT-RUNBOOK.md -- how to rebuild, and what each row counts"
  - "docs/phases/phase-8/SPLIT-VERIFICATION.md + split_build_evidence.json -- the measured result"
  - "a suite that passes on a FRESH CLONE: four tests that asserted the developer's untracked files now assert the repository"
affects: [08-11, 08-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a publishable file set derived from `git ls-files` and never a directory walk, with a planted untracked probe proving the difference"
    - "every gate row reports a COUNT beside its exit code, and a zero count fails the row"
    - "an exclusion proven on a PLANTED input, because one only ever tested against a set that cannot contain its target has never run"
    - "one BuildPlan (manifest + source commit + timestamp) shared by both outputs, so a mid-build edit cannot land in one repository and not the other"
    - "a missing link written as a stated-absent marker, never a placeholder that reads as real"
key-files:
  created:
    - scripts/build_split_repos.py
    - scripts/split_manifest.py
    - scripts/split_docs.py
    - scripts/split_build.py
    - scripts/split_verify.py
    - scripts/split_gates.py
    - scripts/split_report.py
    - tests/unit/test_split_manifest.py
    - tests/unit/test_split_docs.py
    - tests/unit/test_split_build.py
    - tests/unit/test_split_verify.py
    - tests/unit/test_split_gates.py
    - tests/unit/test_split_report.py
    - tests/unit/test_build_split_repos.py
    - docs/phases/phase-8/SPLIT-RUNBOOK.md
    - docs/phases/phase-8/SPLIT-VERIFICATION.md
    - docs/phases/phase-8/split_build_evidence.json
    - .planning/phases/08-submission-and-league-operations/deferred-items.md
  modified:
    - tests/unit/gitignore_probe.py
    - tests/unit/test_publication_ignore_rules.py
    - tests/unit/readme_contract_checks.py
    - tests/unit/test_readme_contract.py
    - tests/unit/test_shipped_counter_isolation.py
    - docs/phases/phase-8/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

decisions:
  - "D-76 held: the file list is `git ls-files` and never a directory walk, into a destination outside this tree. An untracked, non-ignored `secret.txt` was planted at the repository root and left there for the whole build; it appears in neither output, on disk or in the tracked set, and a recursive grep for its contents returns 0 files in both. `.env` and `police_thief_p2p.pdf` are absent by the same mechanism."
  - "D-77 held, and the exclusion list came out EMPTY -- which is the honest result, not a miss. The counters are gitignored, so `git ls-files` never offered them; the build subtracts them by name anyway and the test proves the subtraction on a planted input. Both outputs ship both `config/police/` and `config/thief/` (14 files each), and 2533 tests pass in each because they do."
  - "D-78 held: `.planning/` and `docs/phases/` ship. 1025 tracked files per output = the source's 1024 plus the generated `docs/REPO-SPLIT.md`."
  - "Both rule-49 URLs are written as `NOT ASSIGNED - the repository is not created or pushed yet (08-12)`, and the test asserts the banner contains no `http://`, `https://`, `github.com`, `example.com`, `<url>` or `TODO` shape at all. A placeholder reads as done to every human and every grep; a hole announces itself."
  - "The line-limit row reports its scanned count and FAILS on zero. `check_line_limit.sh`'s no-argument form enumerates through `git ls-files`, empty in a fresh `git init`ed tree: `tests/unit/test_split_verify.py` builds that tree and asserts `exit 0` AND row `False`, so the vacuity is a pinned property rather than a warning in a comment."
  - "The driver's exit contract is `check_submission.py`'s (D-82): 0 all rows pass, 1 any row fails, 2 nothing built or nothing checked. `overall(())` returns False, because `all(())` returns True."
  - "One BuildPlan feeds both outputs. Re-deriving the manifest per role read the working tree twice, minutes apart with a full `pytest --cov` between them; anything edited in the gap would have landed in the second repository only."
  - "The tag was NOT cut and nothing was pushed. No repository created, no remote added, no `gh` or network command issued; both outputs carry zero remotes, and the history-disjointness row proves neither commit is an object this repository knows."

metrics:
  duration: "~4h"
  tasks_completed: 9
  files_created: 18
  files_modified: 7
  completed: 2026-08-17
---

# Phase 8 Plan 10: The Two-Repo Split, Built and Verified Locally Summary

Two submission repositories built from `git ls-files` into `C:\Users\Hp\pursuit-split-repos\`,
each passing **12/12 rows inside its own tree** — ruff 0, `uv sync` 0, **2533 passed / 0 failed
at 97.44 % coverage**, line-limit **539 files scanned / 0 violations**, one commit, **zero
remotes** — and nothing pushed.

**No individual plan file exists for 08-10.** It was executed from
`.planning/phases/08-submission-and-league-operations/08-PLAN-OUTLINE.md` §9, the same way
08-09 was.

## What was built

| Repository | Path | Commit | Tracked | Remotes |
|---|---|---|---|---:|
| `police` | `C:\Users\Hp\pursuit-split-repos\pursuit-police` | `99d6d5f` | 1025 | 0 |
| `thief` | `C:\Users\Hp\pursuit-split-repos\pursuit-thief` | `580acae` | 1025 | 0 |

Built from source commit `8aa02ea`. The two trees differ in exactly two files — each README's
rule-49 banner and each `docs/REPO-SPLIT.md` — verified with `diff -rq`. Full measurements in
[`docs/phases/phase-8/SPLIT-VERIFICATION.md`](../../../docs/phases/phase-8/SPLIT-VERIFICATION.md);
raw rows in `split_build_evidence.json`.

## The plan's two named traps, and what actually happened

**Trap 1 — a one-role split cannot pass Table 5 in its own tree.** Resolved as D-77 said, and
*verified by running the gates rather than by reasoning*: both outputs ship both config
directories (14 tracked files each, 0 counters) and both run 2533 tests green. The counter
exclusion turned out to need no work at all — they are gitignored, so they were never in the
tracked set — and the build subtracts them by name regardless, with the test proving it on a
planted input.

**Trap 2 — `check_line_limit.sh` passes vacuously in a fresh tree.** Pinned rather than
avoided. `tests/unit/test_split_verify.py` builds a tree with files on disk, git initialised
and nothing committed, then asserts the shell gate returns **exit 0** while the row returns
**False** with `scanned 0` in its detail. Every row this plan added reports a count.

## What the split found that nothing else could

Running the suite inside a repository that is not this working tree failed **four** tests that
pass here — which means they also fail on **any fresh clone, including a grader's**. All four
are fixed, each with a mutation probe:

1. **`test_git_agrees_with_every_artifact_claude_md_calls_gitignored`** asked git about
   `Path('graphify-out/')`, which drops the trailing slash; a directory-only ignore rule then
   matches only where the directory happens to exist. **Asking with the slash would have been
   worse**: measured on git 2.53.0.windows.2, *every* non-existent path ending in `/` comes
   back ignored — `README.md/` does too — so that question can never fail. I wrote that version
   first and the mutation probe caught it. It now asks about a path inside the directory, with
   a discrimination control; removing the rule from `.gitignore` fails it.
2. **`test_the_counter_check_fires_when_a_value_is_written_in`** read
   `config/police/games_played.json` unconditionally — gitignored live state no clone has.
3. **`test_the_session_snapshot_reads_the_real_files`** required both counters to exist,
   contradicting `read_counters`' own documented contract that they may not. Replaced with a
   direct read-versus-absent discrimination test, which is strictly stronger.
4. **The rule-38 README leak detector was inert everywhere but this machine.**
   `games_played_leaks` globbed the counters, so in every clone and every CI checkout it
   searched an *empty value set* and returned `[]` unconditionally: the job guarding an
   absolute-disqualification rule was guarding nothing. Values are now injectable, the detector
   is proven with a digit-boundary case, and a second test records that an empty value set
   means "nothing compared", not "no leak found".

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 — Bug] `--replace` died half-way through deleting a built tree**
- **Found during:** the first real gated build
- **Issue:** `PermissionError: [WinError 5]` on `.git/objects/…`; git writes loose objects
  read-only and `shutil.rmtree` cannot remove them on Windows. The destination was left neither
  the old tree nor the new one.
- **Fix:** an `onerror` handler that clears the read-only bit and retries, plus a regression
  test that plants a read-only file. Probe: reverting the handler fails that test.
- **Commit:** `24261b9`

**2. [Rule 1 — Bug] the manifest was re-derived per role**
- **Found during:** self-review while the first gated build was running
- **Issue:** `build_one` called `manifest_for` and read HEAD separately for each role — two
  reads of the working tree minutes apart, with a full `pytest --cov` between them. Anything
  edited in the gap would have landed in the second repository and not the first.
- **Fix:** one `BuildPlan` (manifest + source commit + timestamp) computed once and shared;
  `--source` added so the driver is exercised end to end on a miniature repository, and the
  test asserts both outputs report the same source commit, timestamp and staged count.
- **Commit:** `24261b9`

**3. [Rule 1 — Bug] four tests asserted the developer's tree** — the four above.
- **Commits:** `363531d`, `8aa02ea`

**4. [Rule 3 — Blocking] `docs/` was not created before the provenance file was written**
- **Found during:** the driver's own end-to-end test on a miniature repository, which has no
  `docs/`. Invisible against the real repository, which does.
- **Fix:** `mkdir(parents=True)`. **Commit:** `32784c4`

### Deferred

`tests/integration/test_belief_policy.py::test_belief_enabled_completes_within_the_per_turn_time_budget`
failed once in the full mono run (one 57 ms sample against a 50 ms budget; typical samples 2–4
ms) on a machine that had just run two full split suites. It passes 3/3 twice on a quiet
machine and passed inside both split repositories. Out of scope, file explicitly out of
bounds, no config value touched. Logged in `deferred-items.md`.

## Counter delta in this repository

| | Before | After | Delta |
|---|---:|---:|---:|
| `config/police/games_played.json` | 1927 | 1927 | **0** |
| `config/thief/games_played.json` | 1920 | 1920 | **0** |

Measured across the full `uv run pytest --cov` run at `534ce7f`. The 07-00 contract is
inherited, not re-demonstrated: no game was played to manufacture a `+1/+1`, because that would
be a state change with no deliverable behind it — the refusal 08-09 already made.

## Nothing was pushed

No repository was created, no remote added, no tag cut, no `gh` command and no network git verb
issued. Both outputs carry **zero remotes**, asserted by the build before it returns a commit
hash and again by a verification row. The history-disjointness row proves neither built commit
is an object this repository knows, so neither inherited a history or an `origin`.

## What 08-11 inherits

The outputs are built from `8aa02ea`; this summary, `STATE.md` and the verification document
land after it. A rebuild is one command and is idempotent, so 08-11 rebuilds before cutting its
tag rather than tagging a tree that is one commit stale.

## Self-Check: PASSED

- **25/25 claimed files** exist and are tracked (`git ls-files --error-unmatch` on each).
- **21/21 claimed commits** resolve (`git cat-file -e <hash>^{commit}`).
- Both built repositories exist, `HEAD` matches the hash quoted here, and each reports
  **0 remotes**.
- `99d6d5f` and `580acae` resolve inside their own repositories and **do not** resolve in this
  one — the histories are disjoint, as the row claimed.
- This repository still has exactly one remote, `origin`, unchanged and untouched, and
  `git tag -l` is **empty**: no tag was cut here.
