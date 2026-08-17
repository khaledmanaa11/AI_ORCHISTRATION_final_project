"""Sec17 group 3 -- testing and quality (08-01).

THE COVERAGE PERCENTAGE IS NOT GUESSED FROM A CONFIG FILE. `fail_under = 85`
being present proves the FLOOR is wired, not that the suite clears it, and those
are two different claims. The floor is judged here; the measured percentage is
UNJUDGED unless `--run-suite` is passed, in which case the suite really runs and
the row is judged on its exit code. Reporting a number nobody measured is the
failure mode this whole gate exists to refuse.

"TDD -- tests written before/with the code" is a WORK PROCESS, which is what
Table 5's own `Enforced by` column says. Git history can show a `test(...)`
commit preceding a `feat(...)` commit, but it cannot show that the test was
written first, and a gate that scored the correlation as proof would be
inventing evidence. UNJUDGED, with the phases that recorded a red-then-green
sequence named in the register instead.
"""

from __future__ import annotations

from submission_common import (
    GROUP_3,
    judge,
    read_tracked,
    run,
    tracked_matching,
    unjudged,
)

PYPROJECT = "pyproject.toml"
WORKFLOW = ".github/workflows/quality-gate.yml"
#: Artifact shapes Sec17's "automated test reports" is satisfied by.
REPORT_ARTIFACTS = ("coverage.xml", "junit.xml", "test-results.xml", "htmlcov/index.html")


def _floor_row() -> object:
    text = read_tracked(PYPROJECT)
    return judge(
        "G3-01", GROUP_3, "Table 5 coverage floor wired (`fail_under` in pyproject)",
        "fail_under" in text,
        f"{PYPROJECT} declares fail_under: {'fail_under' in text}",
        PYPROJECT,
    )


def _ci_row() -> object:
    text = read_tracked(WORKFLOW)
    runs_ruff = "ruff check" in text
    runs_cov = "pytest --cov" in text or "pytest --cov" in text.replace("\n", " ")
    return judge(
        "G3-02", GROUP_3, "Sec17 the quality gate runs automatically in CI",
        bool(text) and runs_ruff and runs_cov,
        f"{WORKFLOW} tracked: {bool(text)}; runs ruff: {runs_ruff}; "
        f"runs pytest --cov: {runs_cov}",
        WORKFLOW,
    )


def _report_artifact_row() -> object:
    """Sec17 names "automated test reports" as a deliverable, not as a CI log line."""
    tracked = [name for name in REPORT_ARTIFACTS if read_tracked(name)]
    workflow = read_tracked(WORKFLOW)
    emitted = [name for name in ("--cov-report=xml", "--junitxml", "upload-artifact")
               if name in workflow]
    return judge(
        "G3-03", GROUP_3, "Sec17 automated test reports produced or stored",
        bool(tracked or emitted),
        f"tracked report artifacts: {tracked or 'none'}; CI directives that would "
        f"produce one: {emitted or 'none'}",
        WORKFLOW,
    )


def _suite_exists_row() -> object:
    """An anti-vacuity floor: a coverage claim over zero tests certifies nothing."""
    tests = tracked_matching(prefix="tests/", suffix=".py")
    return judge(
        "G3-04", GROUP_3, "Sec6 a test suite exists and is tracked",
        len(tests) > 0,
        f"tracked files under tests/: {len(tests)}",
        "tests/",
    )


def _coverage_row(run_suite: bool) -> object:
    command = "uv run pytest --cov"
    if not run_suite:
        return unjudged(
            "G3-05", GROUP_3, "Table 5 measured coverage >= 85%",
            f"not measured in this run -- pass --run-suite, or run `{command}` "
            f"yourself. The configured floor is judged separately as G3-01.",
        )
    code, output = run(["uv", "run", "pytest", "--cov"], timeout=3600)
    tail = [line for line in output.splitlines() if "TOTAL" in line or "passed" in line]
    return judge(
        "G3-05", GROUP_3, "Table 5 measured coverage >= 85% (suite run in this session)",
        code == 0,
        f"`{command}` exit {code}; {tail[-2:] if tail else '<no summary line>'}",
        PYPROJECT,
    )


def testing_items(run_suite: bool = False) -> list:
    """Group 3's rows. Two are measured only when the suite is actually run."""
    return [
        _floor_row(),
        _ci_row(),
        _report_artifact_row(),
        _suite_exists_row(),
        _coverage_row(run_suite),
        unjudged("G3-06", GROUP_3, "Sec17 TDD -- tests written before/with the code",
                 "Table 5 marks this row `Work process`. Commit order is a correlation, "
                 "not proof of authorship order; the per-plan SUMMARY files record the "
                 "red-then-green sequences instead"),
        unjudged("G3-07", GROUP_3, "Sec17 edge-case documentation and error handling",
                 "no script can tell a documented edge case from an undocumented one; "
                 "the per-mechanism PRDs carry the enumerations"),
    ]
