"""The GATE-8 measurement's own contract (08-11).

`scripts/` is outside `check_line_limit.sh`'s globs and outside the coverage
source set, so a measurement script is the easiest place in this repository for
an untested branch to live. These tests ask the three questions that matter
about a gate: does its exit code discriminate, can its evidence set be empty
without saying so, and are the two crude scans it trusts actually able to fire?

THE ONE THING THIS FILE CHECKS THAT NO OTHER TEST CAN: that the GATE-8 package
issues **no remote git command**. It is asserted over the package's real source,
and the detector is fired on a planted `push` line first -- an all-clear from a
scanner that matches nothing is not an all-clear.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import gate8_common as common  # noqa: E402
import gate8_report as report  # noqa: E402
import gate8_repos as repos  # noqa: E402
import gate8_submission as submission  # noqa: E402

from pursuit.shared.version import VERSION  # noqa: E402

_OK_OUTPUT = {
    "exists": True, "tracked_file_count": 1025, "commit_count": 1, "remote_count": 0,
    "clean_worktree": True,
    "rule50": {"README": 1, "config": 28, "PRD": 16, "PLAN": 103, "TODO": 10},
    "cross_link": {"banner_present": True, "names_the_other_repository": True,
                   "repo_split_doc_tracked": True, "urls_in_banner": []},
    "tag": {"exists": True, "annotated": True, "points_at_head": True,
            "tree_file_count": 1025, "pushed": False},
}


def _report(**overrides) -> dict:
    c1 = {"outputs": {"police": dict(_OK_OUTPUT), "thief": dict(_OK_OUTPUT)}}
    c2 = {"published_readmes": {
        role: {"readme_bytes": 42000, "missing_academic_942_headings": [],
               "missing_segal_21_headings": [], "academic_sections_expected": 6}
        for role in ("police", "thief")}}
    c3 = {
        "ledger": {role: {"scored_games": 0} for role in ("police", "thief")},
        "bounds": {"minimum_games": 2, "max_games_per_team": 10},
        "declaration_wiring": {
            "call_site_present": True,
            "retained_declaration_artifacts": ["a.json"],
            "retained_artifacts_carrying_a_commit_hash": ["a.json"],
        },
    }
    counters = {"before": {"police/x": "1", "thief/x": "1"},
                "after": {"police/x": "1", "thief/x": "1"}, "unchanged_by_this_measurement": True}
    built = report.build_report(c1, c2, c3, counters, {})
    for key, value in overrides.items():
        built[key] = value
    return built


# ---------------------------------------------------------------- exit contract

def test_a_fully_measured_run_exits_zero() -> None:
    assert report.exit_code(_report()) == report.GateExit.OK


def test_a_pushed_tag_would_fail_criterion_one() -> None:
    """The property this whole plan is organised around, asserted as a verdict."""
    built = _report()
    built["criterion_1_two_cross_linked_repos_and_a_tag"]["outputs"]["police"]["tag"][
        "pushed"] = True
    c1 = built["criterion_1_two_cross_linked_repos_and_a_tag"]
    assert report.criterion_1_built_verdict(c1) == report.FAIL


def test_a_remote_on_an_output_would_fail_criterion_one() -> None:
    built = _report()
    c1 = built["criterion_1_two_cross_linked_repos_and_a_tag"]
    c1["outputs"]["thief"]["remote_count"] = 1
    assert report.criterion_1_built_verdict(c1) == report.FAIL


def test_a_missing_tag_fails_and_exits_one() -> None:
    built = _report()
    built["criterion_1_two_cross_linked_repos_and_a_tag"]["outputs"]["thief"]["tag"][
        "exists"] = False
    c1 = built["criterion_1_two_cross_linked_repos_and_a_tag"]
    built["criterion_1_two_cross_linked_repos_and_a_tag"][
        "built_and_tagged_verdict"] = report.criterion_1_built_verdict(c1)
    assert report.exit_code(built) == report.GateExit.FAILED


def test_one_missing_readme_heading_fails_criterion_two() -> None:
    built = _report()
    c2 = built["criterion_2_academic_readme_and_submission_form"]
    c2["published_readmes"]["police"]["missing_academic_942_headings"] = ["results"]
    assert report.criterion_2_readme_verdict(c2) == report.FAIL


def test_a_declaration_writer_with_no_caller_fails_criterion_three() -> None:
    """08-04's finding, kept as a verdict: a definition is not a caller."""
    built = _report()
    c3 = built["criterion_3_two_scored_league_games"]
    c3["declaration_wiring"]["call_site_present"] = False
    assert report.criterion_3_machinery_verdict(c3) == report.FAIL


# ------------------------------------------------------------- empty evidence

def test_an_empty_counter_snapshot_exits_two_not_zero() -> None:
    built = _report()
    built["games_played_counter"]["before"] = {"police/x": "1"}
    assert report.exit_code(built) == report.GateExit.EMPTY_EVIDENCE


def test_outputs_with_no_tracked_files_exit_two_not_zero() -> None:
    """A gate run against a destination that was never built judged NOTHING."""
    built = _report()
    for output in built["criterion_1_two_cross_linked_repos_and_a_tag"]["outputs"].values():
        output["tracked_file_count"] = 0
    assert report.exit_code(built) == report.GateExit.EMPTY_EVIDENCE


def test_empty_readmes_exit_two_not_zero() -> None:
    built = _report()
    for readme in built["criterion_2_academic_readme_and_submission_form"][
            "published_readmes"].values():
        readme["readme_bytes"] = 0
    assert report.exit_code(built) == report.GateExit.EMPTY_EVIDENCE


# ------------------------------------------------------- no remote, ever

def test_the_package_issues_no_remote_git_command() -> None:
    assert common.network_verb_hits() == {}


def test_the_remote_verb_detector_fires_on_a_planted_push(tmp_path: Path) -> None:
    """The control. Without it the assertion above proves only that it read nothing."""
    planted = tmp_path / "gate8_planted.py"
    planted.write_text('def bad(root):\n    return git_out(root, "push", "origin")\n',
                       encoding="utf-8")
    hits = common.network_verb_hits([planted])
    assert list(hits) == ["gate8_planted.py"], hits
    assert len(hits["gate8_planted.py"]) == 1


def test_the_scan_reads_more_than_zero_files() -> None:
    sources = common.package_sources()
    assert len(sources) >= 5, sources
    assert all(path.is_file() for path in sources)


# ------------------------------------------------------------- derived values

def test_the_tag_name_is_derived_from_the_version_module() -> None:
    assert common.tag_name() == f"v{VERSION}"


def test_the_banner_block_stops_at_the_end_of_the_blockquote() -> None:
    """The regression: a fixed-size slice read a URL out of the README body."""
    text = (
        "# Title\n\n<!-- split-repo-banner role=police source=abc -->\n\n"
        "> | This repository | NOT ASSIGNED |\n\n"
        "Body text linking https://gofastmcp.com here.\n"
    )
    block = repos._banner_block(text, "police")
    assert "NOT ASSIGNED" in block
    assert "gofastmcp" not in block


def test_the_declaration_writer_has_a_production_call_site_that_is_not_its_own_module() -> None:
    sites = submission._call_sites()
    assert sites, "write_declaration_artifact has no production caller"
    assert all(submission.DECLARATION_WRITER_MODULE not in site for site in sites), sites
