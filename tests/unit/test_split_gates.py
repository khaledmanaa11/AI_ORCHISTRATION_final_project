"""Reading the Table-5 gates' output inside a split repository (08-10).

A PARSER THAT MATCHES NOTHING MUST RAISE, NOT RETURN ZERO. `0 failed` and
`0.0% coverage` are both indistinguishable from "the regex missed" if the
parser is allowed to fall back to a default, and the fallback silently converts
a broken measurement into either a pass (no failures seen) or a mystery failure
nobody trusts. Both parsers here raise on unrecognised output, and both are
tested against output that does not contain their line.

THE COVERAGE ROW IS JUDGED AGAINST `fail_under`, which is read from
`pyproject.toml` rather than written here -- the floor is a project setting, and
a second copy of it in a script is the hardcoded-value defect Table 5 names.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import REPO_ROOT, load

gates_mod = load("split_gates")

PYTEST_TAIL = (
    "2455 passed, 3 warnings in 402.11s (0:06:42)\n"
    "Required test coverage of 85% reached. Total coverage: 97.44%\n"
)
FAILING_TAIL = "2 failed, 2453 passed in 400.00s\n"


def test_the_pass_count_is_read_from_the_summary_line() -> None:
    assert gates_mod.parse_pytest(PYTEST_TAIL) == (2455, 0)


def test_a_failing_run_reports_both_numbers() -> None:
    assert gates_mod.parse_pytest(FAILING_TAIL) == (2453, 2)


def test_output_with_no_summary_line_raises() -> None:
    with pytest.raises(gates_mod.GateOutputError):
        gates_mod.parse_pytest("collected 0 items\n")


def test_coverage_is_read_as_a_percentage() -> None:
    assert gates_mod.parse_coverage(PYTEST_TAIL) == pytest.approx(97.44)


def test_coverage_falls_back_to_the_total_row() -> None:
    assert gates_mod.parse_coverage("TOTAL   12000   240    98%\n") == pytest.approx(98.0)


def test_output_with_no_coverage_number_raises() -> None:
    with pytest.raises(gates_mod.GateOutputError):
        gates_mod.parse_coverage("2455 passed in 402.11s\n")


def test_the_floor_is_read_from_the_project_configuration() -> None:
    assert gates_mod.coverage_floor(REPO_ROOT) == pytest.approx(85.0)


def test_the_floor_raises_when_the_project_declares_none(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    with pytest.raises(gates_mod.GateOutputError):
        gates_mod.coverage_floor(tmp_path)


def test_the_suite_row_needs_passes_a_floor_and_zero_failures() -> None:
    row = gates_mod.suite_row(0, PYTEST_TAIL, 85.0)
    assert row.ok is True
    assert "2455 passed" in row.detail and "97.44" in row.detail


def test_the_suite_row_fails_a_run_that_collected_nothing() -> None:
    with pytest.raises(gates_mod.GateOutputError):
        gates_mod.suite_row(5, "no tests ran\n", 85.0)


def test_the_suite_row_fails_below_the_floor() -> None:
    row = gates_mod.suite_row(1, "10 passed in 1s\nTOTAL 100 50 50%\n", 85.0)
    assert row.ok is False
    assert "50.0" in row.detail


def test_a_zero_test_run_is_not_a_pass() -> None:
    row = gates_mod.suite_row(0, "0 passed in 0.10s\nTOTAL 10 0 100%\n", 85.0)
    assert row.ok is False
    assert "0 passed" in row.detail
