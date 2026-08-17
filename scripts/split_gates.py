"""Running the Table-5 gates inside a built split repository (08-10).

THE GATES ARE RUN IN THE OUTPUT TREE, NOT REASONED ABOUT FROM THIS ONE. A split
carrying one role's configuration would fail twenty-plus integration tests that
load both seats; the only way to know a split passes Table 5 is to run Table 5
inside it, with its own `uv sync`, its own `ruff`, its own `pytest --cov`.

A PARSER THAT MATCHES NOTHING RAISES. `0 failed` and `0.0%` are exactly what a
missed regex produces, and a `0 failed` default turns a broken measurement into
a pass. `GateOutputError` is the honest answer to output nobody recognised --
the same refusal `submission_common`'s exit-2 state makes.

THE COVERAGE FLOOR IS READ FROM `pyproject.toml`. `fail_under = 85` is a project
setting; a second copy of 85 in a script is the hardcoded-value defect Table 5
names, and the two copies would eventually disagree.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from split_verify import Check

_PYTEST_PASSED = re.compile(r"(\d+) passed")
_PYTEST_FAILED = re.compile(r"(\d+) failed")
_TOTAL_COVERAGE = re.compile(r"Total coverage:\s*([\d.]+)%")
_TOTAL_ROW = re.compile(r"^TOTAL\s+.*?([\d.]+)%\s*$", re.MULTILINE)
_FAIL_UNDER = re.compile(r"fail_under\s*=\s*([\d.]+)")

#: The Table-5 commands, run inside the split tree in this order.
SYNC = ["uv", "sync"]
RUFF = ["uv", "run", "ruff", "check", "."]
SUITE = ["uv", "run", "pytest", "--cov", "--cov-report=term-missing"]


class GateOutputError(RuntimeError):
    """A gate produced output no parser recognised. Never silently a zero."""


def parse_pytest(output: str) -> tuple[int, int]:
    """`(passed, failed)` from pytest's summary line, or raise."""
    passed = _PYTEST_PASSED.search(output)
    failed = _PYTEST_FAILED.search(output)
    if not passed and not failed:
        raise GateOutputError(
            "pytest output carried neither a 'N passed' nor a 'N failed' summary. "
            "Reporting 0 failures here would turn an unread run into a pass."
        )
    return int(passed.group(1)) if passed else 0, int(failed.group(1)) if failed else 0


def parse_coverage(output: str) -> float:
    """The total coverage percentage from either shape coverage prints, or raise."""
    for pattern in (_TOTAL_COVERAGE, _TOTAL_ROW):
        found = pattern.search(output)
        if found:
            return float(found.group(1))
    raise GateOutputError(
        "no total coverage percentage in the output. A 0.0 default would read as a "
        "failure nobody trusts, and a 100.0 default would read as a pass nobody earned."
    )


def coverage_floor(root: Path) -> float:
    """`[tool.coverage.report] fail_under` from the tree's own `pyproject.toml`."""
    text = (Path(root) / "pyproject.toml").read_text(encoding="utf-8")
    found = _FAIL_UNDER.search(text)
    if not found:
        raise GateOutputError(
            f"{root}/pyproject.toml declares no `fail_under`, so this tree has no "
            "coverage floor to be judged against. Refusing to invent 85."
        )
    return float(found.group(1))


def run_gate(root: Path, command: list[str], timeout: int = 5400) -> tuple[int, str]:
    """Run one gate inside *root*, returning its exit code and combined output."""
    done = subprocess.run(
        command, cwd=root, capture_output=True, text=True, check=False, timeout=timeout,
    )
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def simple_row(name: str, code: int, output: str) -> Check:
    """A row for a gate whose only measurement is its exit code (`uv sync`, ruff)."""
    tail = [line for line in output.strip().splitlines() if line.strip()][-1:] or ["<none>"]
    return Check(name, code == 0, f"exit {code}; last line: {tail[0].strip()!r}")


def suite_row(code: int, output: str, floor: float) -> Check:
    """`pytest --cov`: zero failures, a POSITIVE pass count, and coverage >= floor."""
    passed, failed = parse_pytest(output)
    coverage = parse_coverage(output)
    return Check(
        "pytest --cov",
        code == 0 and failed == 0 and passed > 0 and coverage >= floor,
        f"exit {code}; {passed} passed, {failed} failed; coverage {coverage}% "
        f"against fail_under {floor}% (a run of 0 tests fails this row)",
    )
