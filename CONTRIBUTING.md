# Contributing

This is a university final project for *Orchestration of AI Agents* (University of Haifa),
built solo. It is published so it can be read, run and graded — pull requests are not
expected. What follows is the working standard the code is held to, written down so a
reader can reproduce every gate rather than take a badge's word for it.

The standard is not this file's invention. It comes from the course's engineering
document, extracted to [`docs/SEGAL_GUIDELINES.md`](docs/SEGAL_GUIDELINES.md) §19.1
Table 5, and the game rules extracted to [`docs/RULES.md`](docs/RULES.md).

---

## 1. Set up

```bash
uv sync                                   # the ONLY supported install path
git config core.hooksPath scripts/hooks   # enables the pre-commit size gate
cp .env-example .env                      # then fill in your own keys
```

**`uv` is mandatory.** `pyproject.toml` + `uv.lock` are the single source of dependency
truth and there is deliberately no `requirements.txt`.

| Task | Use | Never |
|---|---|---|
| Install | `uv sync` | `pip install` |
| Add a dependency | `uv add <pkg>` | `pip install <pkg>` |
| Run anything | `uv run python …` | `python …` |
| Test | `uv run pytest tests/` | `python -m pytest` |

`.env` is gitignored and `.env-example` carries only placeholders. Never commit a real
credential — rules 39–40 make it a project failure, not a code-review note.

## 2. Run the gates before you commit

Every one of these is machine-checkable, and every one of them runs in CI
(`.github/workflows/quality-gate.yml`). Run them locally first.

```bash
uv run ruff check .                                  # must be 0 violations
sh scripts/check_line_limit.sh                       # every file <= 150 code lines
uv run pytest --cov                                  # must clear fail_under = 85
uv run python scripts/check_local_truth.py           # rules 8-9 firewall
uv run python scripts/check_no_llm_in_strategy.py    # rule 25 firewall
uv run python scripts/check_submission.py            # the §17 + Table-5 audit
```

The reports CI stores are produced by the same command it runs:

```bash
uv run pytest --cov --cov-report=term-missing --cov-report=xml --junitxml=reports/junit.xml
```

Both outputs are gitignored build artifacts.

## 3. The rules that are not negotiable

1. **Files stay at or under 150 code lines** (blanks and comments excluded). When a file
   reaches the limit, **split it** — never compress code to fit. The pre-commit hook and a
   CI job both enforce this. Do not bypass with `--no-verify`.
2. **No invented numbers.** Every numeric value comes from
   [`docs/PARAMETERS.md`](docs/PARAMETERS.md). Values marked **fixed** may not be changed at
   all. If a number you need is not there, stop and ask rather than choose one.
3. **No hardcoded values in source.** Configuration, `constants.py`, or an `Enum`.
4. **The cop and the thief share no runtime state.** They are two processes over
   `config/police/` and `config/thief/`. A shared *library* is fine; a shared live game
   state object is information leakage.
5. **The GUI never shows the true board state** — only local truth. `check_local_truth.py`
   enforces this structurally over `src/pursuit/gui/`.
6. **The language model never chooses a move.** The algorithm decides; the LLM only decodes
   incoming hints and writes outgoing bluff text. `check_no_llm_in_strategy.py` enforces it.
7. **No secrets in source, ever.**

## 4. Tests

Test-first, or test-alongside — red, green, refactor. Every module gets a test file; every
public function gets at least a happy-path test and an error-case test. **Mock every
external service**: no test may depend on a live network, an API, or an opponent. Test
files obey the 150-line limit too.

Two habits this repository has learned the hard way and expects:

- **Assert the subject exists before asserting the verdict.** A loop over an emptied table
  passes silently; a `grep` over a file that moved returns nothing and reads as "clean".
  Several tests here carry an explicit anti-vacuity floor for exactly this reason.
- **Never derive a test's expected value from the code under test.** Parse it out of the
  document that governs it. `tests/unit/test_league_bounds_against_the_book.py` reads its
  bound out of `docs/PARAMETERS.md`, because a test built from the constant it checks
  passes whatever that constant becomes.

## 5. Documentation is part of the change

`docs/PRD.md`, `docs/PLAN.md` and `docs/TODO.md` are mandatory, plus a dedicated
`docs/PRD_<mechanism>.md` for **every** algorithm or central mechanism, and a
`docs/phases/phase-<N>/{PRD,PLAN,TODO}.md` triplet per phase. Approve the documents before
writing the code they describe.

## 6. Commits

Conventional commits, scoped by the plan that produced them:

```
feat(08-03): Sec14 packaging -- __all__ on all 11 packages
fix(05-14): stamp the second mover's MOVE envelope with the played turn
test(07-03): add the failing local-truth reproduction
```

`feat` · `fix` · `test` · `refactor` · `chore` · `docs` · `plan`. One logical change per
commit, with the measurement that justifies it in the body.

## 7. Licence

See [`LICENSE`](LICENSE). **It is prepared and not yet adopted** — the file carries a block
saying so, and the repository owner must confirm the licence choice before either
submission repository is made public.
