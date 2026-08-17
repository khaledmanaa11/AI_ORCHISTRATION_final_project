"""The Sec17 audit's three-state exit contract (08-01).

THE LOAD-BEARING CASE IS EXIT 2. `docs/phases/phase-5/` and `07-09-SUMMARY.md`
both record gates in this repository that reported OK for having judged nothing,
and one of them was protecting a disqualification rule. Every one of the four
ways `submission_report.emptiness` can be satisfied is pinned here individually,
including the case that matters most: an evidence set carrying REAL GAPS whose
inventory is empty must still come out EMPTY_EVIDENCE, because a run that judged
nothing cannot know whether it has gaps. Exit 2 outranks exit 1.

The second contract pinned here is that UNJUDGED IS NOT A PASS: a report made
entirely of UNJUDGED rows has `judged == 0` and must not be exit 0.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import load

common = load("submission_common")
report = load("submission_report")

GROUP = common.GROUP_1


def _pass_row(item_id: str = "X-01"):
    return common.judge(item_id, GROUP, "probe", True, "probe", "probe.md")


def _gap_row(item_id: str = "X-02"):
    return common.judge(item_id, GROUP, "probe", False, "probe", "probe.md")


def _unjudged_row(item_id: str = "X-03"):
    return common.unjudged(item_id, GROUP, "probe", "probe")


def test_all_pass_is_exit_zero():
    built = report.build_report([_pass_row()], mechanism_count=1, readme_count=1,
                               run_suite=False)
    assert built["verdict"] == "PASS"
    assert report.exit_code(built) == int(common.SubmissionExit.OK)


def test_one_gap_is_exit_one():
    built = report.build_report([_pass_row(), _gap_row()], mechanism_count=1,
                                readme_count=1, run_suite=False)
    assert built["verdict"] == "GAPS_FOUND"
    assert report.exit_code(built) == int(common.SubmissionExit.GAPS_FOUND)


def test_no_rows_at_all_is_exit_two():
    built = report.build_report([], mechanism_count=1, readme_count=1, run_suite=False)
    assert built["verdict"] == "EMPTY_EVIDENCE"
    assert report.exit_code(built) == int(common.SubmissionExit.EMPTY_EVIDENCE)
    assert "no audit rows were produced at all" in built["empty_evidence_reasons"]


def test_only_unjudged_rows_is_exit_two():
    """UNJUDGED is not a pass, so a report made of them judged nothing."""
    built = report.build_report([_unjudged_row(f"X-{n}") for n in range(4)],
                                mechanism_count=1, readme_count=1, run_suite=False)
    assert built["counts"] == {"pass": 0, "gap": 0, "unjudged": 4, "judged": 0, "total": 4}
    assert report.exit_code(built) == int(common.SubmissionExit.EMPTY_EVIDENCE)


@pytest.mark.parametrize(
    ("mechanisms", "readmes", "expected_reason"),
    [
        (0, 1, "the package walk found no mechanisms to require a PRD of"),
        (1, 0, "no Sec2.1 README row was produced"),
    ],
)
def test_empty_inventory_outranks_gaps(mechanisms, readmes, expected_reason):
    """A run with real GAPs but an empty inventory is exit 2, never exit 1."""
    rows = [_pass_row(), _gap_row(), _gap_row("X-04")]
    built = report.build_report(rows, mechanism_count=mechanisms,
                                readme_count=readmes, run_suite=False)
    assert built["counts"]["gap"] == 2, "the probe must really carry gaps"
    assert built["verdict"] == "EMPTY_EVIDENCE"
    assert report.exit_code(built) == int(common.SubmissionExit.EMPTY_EVIDENCE)
    assert expected_reason in built["empty_evidence_reasons"]


def test_counts_are_exhaustive():
    rows = [_pass_row(), _gap_row(), _unjudged_row()]
    counts = report.counts(rows)
    assert counts["total"] == len(rows)
    assert counts["judged"] == counts["pass"] + counts["gap"]
    assert counts["judged"] + counts["unjudged"] == counts["total"]


def test_unjudged_helper_can_never_produce_a_pass():
    assert _unjudged_row().verdict == common.UNJUDGED
    assert common.UNJUDGED != common.PASS
