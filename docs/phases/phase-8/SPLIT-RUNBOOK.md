# Split runbook — building the two submission repositories

**Owner:** 08-10 · **Run by:** anyone, at any time · **Pushed by:** a human, at 08-12

Rule 49 asks for two cross-linked public repositories. This runbook builds them **locally**,
from this repository's tracked set, into a directory **outside** this tree. It creates nothing
on GitHub, adds no remote, cuts no tag and pushes nothing — every one of those is a human
action with a human's account behind it, and they belong to 08-12.

## One command

```bash
uv run python scripts/build_split_repos.py --dest C:/Users/Hp/pursuit-split-repos --replace --gates \
    --json docs/phases/phase-8/split_build_evidence.json
```

| Flag | Effect |
|---|---|
| `--dest DIR` | required; refused if it is at or under this repository's root |
| `--roles police thief` | which repositories to build (default: both) |
| `--replace` | rebuild over an existing output tree; without it, a non-empty destination is refused |
| `--gates` | also run `uv sync`, `ruff check .` and `pytest --cov` **inside each output** |
| `--json PATH` | write the full evidence, row by row |
| `--source DIR` | the repository to split (default: the one the script lives in) |

Both outputs are built from **one** manifest, **one** source commit and **one** timestamp,
derived before the first repository is created. Re-deriving per role would read the working
tree twice — minutes apart, with a full `pytest --cov` in between — and anything that changed
in the gap would land in the second repository and not the first.

**Exit contract** (`check_submission.py`'s, D-82): `0` every row of every output passed · `1`
any row failed · `2` nothing was built or nothing was checked. Two is not a pass; a build that
produced no rows is the vacuity this phase keeps finding, not a clean bill of health.

## What is built, and from what

The file list is `git ls-files` and nothing else (D-76). **Never a directory walk**: `.env`
and the course book PDF sit untracked in this working tree right now, and a walk would publish
a live credential and a copyrighted text in one step. A planted, untracked, non-ignored
`secret.txt` is the standing probe for this — it must appear in neither output.

Subtracted by name (D-77): `config/*/games_played*.json`. They are gitignored, so they were
never in the tracked set; the exclusion is written down anyway, so a future `git add -f`
cannot carry the league's declared games-played count into a public repository.

**Both** `config/police/` and `config/thief/` ship in **both** repositories. `tests/conftest.py`,
`tests/integration/conftest.py`, `tests/_shipped_config_guard.py` and twenty-plus integration
tests load both seats; a repository carrying one of them could not run its own suite and so
could not be shown to meet Table 5 inside its own tree. Rule 50 sets a floor, not a ceiling,
and rule 2 forbids shared *runtime state* — these are two static directories of JSON.

Each output additionally gets two generated files:

- the rule-49 cross-link block, injected into `README.md` after its `# ` heading, with **both**
  repository URLs written as a stated-absent marker;
- `docs/REPO-SPLIT.md` — what shipped, what was subtracted and why, and the first-commit setup.

## What is verified, inside each output

Nine structural rows plus three gate rows. Every row carries a **count**, never only an exit
code:

| Row | The number it reports |
|---|---|
| exactly one commit | `rev-list --count HEAD` |
| zero remotes | how many are configured |
| history disjoint from the source | whether the built commit is an object this repository knows |
| rule-49 cross-link present | README bytes read, and the role the banner names |
| line-limit | exit code **and** the number of tracked `.py` files under `src/ tests/ training/` |
| forbidden paths absent | how many of seven names are on disk, and how many are tracked |
| both seats' config (D-77) | tracked config files per role, and counters carried |
| rule 50 inventory | README / config / PRD / PLAN / TODO counts |
| CI workflows | `scripts/` paths referenced by a `run:` step, and how many are missing |
| `uv sync` · `ruff check .` | exit code and last line |
| `pytest --cov` | passed, failed, coverage % against the tree's own `fail_under` |

**The line-limit row is the one to read carefully.** `scripts/check_line_limit.sh`'s
no-argument form enumerates through `git ls-files`, which is **empty in a freshly `git init`ed
tree before the first commit** — it then exits 0 having scanned nothing. A green exit in a
fresh split proves nothing at all, which is why the row fails on a scan of zero files.
`tests/unit/test_split_verify.py` builds that exact tree and asserts both halves: `exit 0`,
and the row `False`.

## Working in an output repository

```bash
cd <dest>/pursuit-police
git config core.hooksPath scripts/hooks   # the 150-line + ruff pre-commit gate
uv sync                                   # uv only; there is no requirements.txt
uv run pytest --cov                       # the same suite, inside the split
```

## What a human does next (08-12 — not this runbook)

1. Decide whether this repository's `origin` is public or private (OQ8-9) **before** anything else.
2. Create the two public repositories.
3. `git remote add` in each output, then `git push`.
4. Push the tag 08-11 cut in each output.
5. Fill the two real URLs into `config/{police,thief}/league.json` and into each README's
   cross-link block, replacing the stated-absent markers.
6. Re-run `scripts/check_submission.py` and this build's verification against the pushed trees.

Until step 3, every output repository has **zero remotes** and there is nothing to push by
accident. That is the point of building outside this tree.
