# Split repositories — measured, 2026-08-17

**Owner:** 08-10 · **Built from:** `8aa02ea` · **Command:** the one in
[`SPLIT-RUNBOOK.md`](SPLIT-RUNBOOK.md) · **Raw evidence:**
[`split_build_evidence.json`](split_build_evidence.json)

> **Nothing was pushed.** No repository was created, no remote was added, no tag was cut and
> no `gh` or network command was issued. Both outputs carry **zero remotes**. Publishing is
> 08-12, by a human.

## Where they are

| Repository | Path | Commit | Commits | Remotes | Tracked files |
|---|---|---|---:|---:|---:|
| `police` | `C:\Users\Hp\pursuit-split-repos\pursuit-police` | `99d6d5f` | 1 | 0 | 1025 |
| `thief` | `C:\Users\Hp\pursuit-split-repos\pursuit-thief` | `580acae` | 1 | 0 | 1025 |

Outside this repository's tree (D-76), on branch `main`. 1025 = the source's 1024 tracked
files plus each output's generated `docs/REPO-SPLIT.md`. The two trees differ in exactly two
files — `README.md` (the role's rule-49 banner) and `docs/REPO-SPLIT.md` — and in nothing else,
checked with `diff -rq`.

## Table 5, run inside each output

Not reasoned about from here. Every number below was produced by the gate running in the
output tree, against that tree's own `pyproject.toml`.

| Table 5 row | `police` | `thief` |
|---|---|---|
| `uv sync` | exit 0 | exit 0 |
| `ruff check .` | exit 0, 0 violations | exit 0, 0 violations |
| `pytest --cov` | exit 0, **2533 passed, 0 failed**, coverage **97.44 %** vs `fail_under` 85 | exit 0, **2533 passed, 0 failed**, coverage **97.44 %** vs `fail_under` 85 |
| file size ≤ 150 code lines | exit 0, **539 files scanned**, 0 violations | exit 0, **539 files scanned**, 0 violations |
| secrets 0, `.env-example` present | `.env` absent on disk and untracked; `.env-example` ships | same |
| `uv` only, no `requirements.txt` | `requirements.txt` absent | same |

The mono-repo measures **97.44 %** on the same command, so the split does not measure less
than the repository it came from: `[tool.coverage.run] source = ["src", "training"]` ships
unchanged and `training/` ships with it.

**Why the scanned count is quoted and not just the exit code.** `scripts/check_line_limit.sh`'s
no-argument form enumerates through `git ls-files`, which is **empty in a freshly `git init`ed
tree before the first commit** — it then exits **0** having scanned nothing. A green exit in a
fresh split proves nothing whatsoever. `tests/unit/test_split_verify.py` builds that exact tree
and asserts both halves (`exit 0`, scan set `0`, row `False`), and the row here fails on a scan
of zero files. The same vacuity is on record in `05-18-SUMMARY.md`.

## Structural rows, per output

Both outputs: **12/12 rows PASS**, `build_split_repos.py` exit **0**.

| Row | Measured |
|---|---|
| exactly one commit | `rev-list --count HEAD` = 1 |
| zero remotes | 0 |
| history disjoint from the source | the built commit is not an object in this repository |
| rule-49 cross-link block | present, naming the output's own role |
| forbidden paths absent | 7 names checked, 0 on disk, 0 tracked |
| both seats' config (D-77) | police 14, thief 14 tracked config files; **0 counters carried** |
| rule 50 inventory | README 1 · config 28 · PRD 16 · PLAN 103 · TODO 10 |
| CI workflows | 1 workflow, 3 `scripts/` paths referenced by `run:` steps, 0 missing |

`config/{police,thief}/security.json` still carries the team code `khm-mn17` in both outputs
(SUB-06), and `scripts/hooks/pre-commit` ships with the `git config core.hooksPath
scripts/hooks` step documented in the README, in `docs/REPO-SPLIT.md` and in the runbook.

## The publication probe

A file named `secret.txt` — untracked, and **not** matched by any `.gitignore` rule, verified
with `git check-ignore` — was planted at the root of the development tree and left there for
the whole build. It appears in **neither** output: absent from disk, absent from the tracked
set, and `grep -r` for its contents returns 0 files in both. `.env` and `police_thief_p2p.pdf`,
which really are untracked in the development tree, are absent from both outputs by the same
mechanism: the file list comes from `git ls-files` and never from a directory walk.

## D-77, verified rather than assumed

Both outputs ship **both** `config/police/` and `config/thief/` (14 tracked files each) and
**neither** `games_played.json` nor `games_played.prev.json` (0 carried, absent on disk and
untracked in both). The evidence that this was necessary is the suite itself: 2533 tests pass
in a tree holding both seats, and twenty-plus of them load both.

**The exclusion list in the evidence JSON is empty, and that is the honest result.** The
counters are gitignored, so `git ls-files` never offered them and there was nothing to
subtract. The build subtracts them by name regardless — the day a `git add -f` puts one in the
tracked set is the day that line earns its keep — and `tests/unit/test_split_manifest.py`
proves the subtraction on a **planted** input, because an exclusion only ever tested against a
set that cannot contain its target has never actually run.

## What the split found that nothing else had

Running the suite inside a repository that is not this working tree was the point of the
exercise, and it failed four tests that pass here — which means **they also fail on any fresh
clone, including a grader's**:

1. **`test_git_agrees_with_every_artifact_claude_md_calls_gitignored`** asked git about
   `Path('graphify-out/')`, which drops the trailing slash; a directory-only ignore rule then
   matches only where the directory happens to exist. Asking *with* the slash would have been
   worse: on git 2.53.0.windows.2 **every** non-existent path ending in `/` comes back ignored
   — `README.md/` does too — so that question can never fail. It now asks about a path inside
   the directory, with a discrimination control, and removing the rule from `.gitignore` fails
   it.
2. **`test_the_counter_check_fires_when_a_value_is_written_in`** read
   `config/police/games_played.json` unconditionally — gitignored live state that no clone has.
3. **`test_the_session_snapshot_reads_the_real_files`** required both counters to exist,
   contradicting `read_counters`' own documented contract that they may not.
4. **The rule-38 README leak detector was inert everywhere but this machine.**
   `games_played_leaks` globbed the counters and searched an empty value set in every clone, so
   the CI job guarding an absolute-disqualification rule was guarding nothing. It now takes
   injectable values, is proven with a digit-boundary case, and a second test records that an
   empty value set means "nothing compared", not "no leak found".

## Rebuilding

One command, and it is idempotent — `--replace` wipes and rebuilds. These outputs are built
from `8aa02ea`; the 08-10 summary, `STATE.md` and this file land after it, so 08-11 rebuilds
before cutting its tag. Nothing here needs to be preserved by hand.
