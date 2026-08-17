"""Assembles the GATE-8 evidence JSON and computes its exit code (08-11).

INHERITED WHOLE FROM `gate7_report.py`, because 07-09 already argued it: one
place where the verdicts are computed FROM the numbers, no threshold invented
here, an empty evidence set reported separately (exit 2) from a failure (exit 1),
and -- the rule this gate needs most --

    NO CRITERION IS EVER A BLANKET PASS.

All three GATE-8 criteria are structurally human-completed. Each therefore
carries its measurable half and its human half as two NAMED fields, and the
criterion-level `verdict` is the string that joins them, so a grep for
`"verdict": "PASS"` cannot match a criterion nobody has finished. Writing GATE-8
PASS on the strength of preparation is the failure mode 07-09 refused and the
08 outline names as this plan's second trap.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import IntEnum

PASS = "PASS"
FAIL = "FAIL"
PENDING = "PENDING"
#: One rule-37/38 counter per role.
EXPECTED_COUNTER_FILES = 2
#: Both split outputs must be present for criterion 1 to have judged anything.
EXPECTED_OUTPUTS = 2


class GateExit(IntEnum):
    """Process exit codes -- structural, not game parameters."""

    OK = 0
    FAILED = 1
    EMPTY_EVIDENCE = 2


def _output_ok(output: dict) -> bool:
    tag, links = output["tag"], output["cross_link"]
    return all((
        output["exists"],
        output["tracked_file_count"] > 0,
        output["commit_count"] > 0,
        output["remote_count"] == 0,
        output.get("clean_worktree", False),
        all(count > 0 for count in output["rule50"].values()),
        links.get("banner_present", False),
        links.get("names_the_other_repository", False),
        links.get("repo_split_doc_tracked", False),
        not links.get("urls_in_banner", []),
        tag["exists"], tag["annotated"], tag["points_at_head"],
        tag["tree_file_count"] == output["tracked_file_count"],
        not tag["pushed"],
    ))


def criterion_1_built_verdict(c1: dict) -> str:
    outputs = c1["outputs"]
    if len(outputs) < EXPECTED_OUTPUTS:
        return FAIL
    return PASS if all(_output_ok(output) for output in outputs.values()) else FAIL


def criterion_2_readme_verdict(c2: dict) -> str:
    readmes = c2["published_readmes"]
    checks = [
        readme["readme_bytes"] > 0
        and not readme["missing_academic_942_headings"]
        and not readme["missing_segal_21_headings"]
        and readme["academic_sections_expected"] > 0
        for readme in readmes.values()
    ]
    return PASS if len(checks) == EXPECTED_OUTPUTS and all(checks) else FAIL


def criterion_3_machinery_verdict(c3: dict) -> str:
    wiring = c3["declaration_wiring"]
    return PASS if all((
        wiring["call_site_present"],
        len(wiring["retained_declaration_artifacts"]) > 0,
        wiring["retained_artifacts_carrying_a_commit_hash"]
        == wiring["retained_declaration_artifacts"],
        c3["bounds"]["minimum_games"] > 0,
        c3["bounds"]["max_games_per_team"] >= c3["bounds"]["minimum_games"],
        all(reading["scored_games"] <= c3["bounds"]["max_games_per_team"]
            for reading in c3["ledger"].values()),
    )) else FAIL


def build_report(c1: dict, c2: dict, c3: dict, counters: dict, verb_hits: dict) -> dict:
    built, readme, machinery = (
        criterion_1_built_verdict(c1),
        criterion_2_readme_verdict(c2),
        criterion_3_machinery_verdict(c3),
    )
    return {
        "gate": "GATE-8 (submission gate, .planning/ROADMAP.md Phase 8)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "no_remote_command_was_issued": {
            "network_verb_hits_in_this_package": verb_hits,
            "clean": not verb_hits,
        },
        "games_played_counter": counters,
        "criterion_1_two_cross_linked_repos_and_a_tag": {
            **c1,
            "built_and_tagged_verdict": built,
            "published_verdict": PENDING,
            "verdict": f"BUILT+TAGGED {built}; PUBLISHED {PENDING} (08-12)",
        },
        "criterion_2_academic_readme_and_submission_form": {
            **c2,
            "readme_sections_verdict": readme,
            "screenshots_verdict": PENDING,
            "form_and_per_member_verdict": PENDING,
            "verdict": f"README {readme}; SCREENSHOTS {PENDING} (07-10); "
                       f"FORM+SUBMISSION {PENDING} (08-14)",
        },
        "criterion_3_two_scored_league_games": {
            **c3,
            "machinery_verdict": machinery,
            "games_played_verdict": PENDING,
            "verdict": f"MACHINERY {machinery}; GAMES {PENDING} (08-13, needs 07-10)",
        },
    }


def _evidence_is_empty(report: dict) -> bool:
    """The two places a GATE-8 run can judge nothing and look tidy doing it."""
    counters = report["games_played_counter"]
    c1 = report["criterion_1_two_cross_linked_repos_and_a_tag"]
    c2 = report["criterion_2_academic_readme_and_submission_form"]
    return (
        len(counters["before"]) < EXPECTED_COUNTER_FILES
        or len(counters["after"]) < EXPECTED_COUNTER_FILES
        or not any(output["tracked_file_count"] for output in c1["outputs"].values())
        or not any(readme["readme_bytes"] for readme in c2["published_readmes"].values())
    )


def exit_code(report: dict) -> int:
    """0 only when all three MEASURABLE halves pass.

    The three human halves are PENDING by design and do not make this non-zero
    -- `gate7_report.exit_code`'s own contract. **The GATE DOCUMENT carries the
    PENDING, not this exit code**, and `GATE-8-MEASUREMENT.md` says so in as
    many words: exit 0 here means "everything that could be true before a human
    acts is true", never "GATE-8 is met".
    """
    if _evidence_is_empty(report):
        return int(GateExit.EMPTY_EVIDENCE)
    verdicts = (
        report["criterion_1_two_cross_linked_repos_and_a_tag"]["built_and_tagged_verdict"],
        report["criterion_2_academic_readme_and_submission_form"]["readme_sections_verdict"],
        report["criterion_3_two_scored_league_games"]["machinery_verdict"],
    )
    return int(GateExit.OK) if all(value == PASS for value in verdicts) else int(GateExit.FAILED)
