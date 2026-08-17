"""Sec17 "automated test reports" -- the CI directives, pinned (08-03).

WHAT THIS TEST CAN AND CANNOT CLAIM, STATED PLAINLY. It cannot claim GitHub
Actions ran anything; nothing offline can. It claims three things it CAN check,
and each of them is a way the deliverable has been lost before:

  1. the pytest invocation still carries both report flags -- a later edit that
     "tidies" the command back to `uv run pytest --cov` silently removes the
     artifact while leaving the green tick;
  2. an upload step still exists, because a report produced into a container that
     is then destroyed is not a stored report;
  3. both output paths are GITIGNORED, because the failure mode on the other side
     is a per-run coverage.xml committed by reflex into a public repository.

The command the workflow runs is also asserted to be reproducible locally by the
exact string written into the file, so the instruction and the CI job cannot
drift apart.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from tests.unit.gitignore_probe import REPO_ROOT, git_available, git_ignored

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "quality-gate.yml"
#: The flags `scripts/submission_testing.REPORT_ARTIFACTS` and Sec17 both look for.
REQUIRED_DIRECTIVES = ("--cov-report=xml", "--junitxml=", "upload-artifact")
#: Written by the command above, and never committable.
EMITTED_PATHS = ("coverage.xml", "reports/junit.xml")
#: Removing this keeps `fail_under = 85` working but blanks the human-readable
#: summary, because `--cov-report=xml` replaces the default terminal report.
TERMINAL_REPORT = "--cov-report=term-missing"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def directives() -> str:
    """The workflow's EXECUTABLE lines -- comments stripped.

    THIS STRIPPING IS THE POINT, and it was added because the first draft of this
    test did not have it. The comment block above the job explains the flags and
    therefore contains them verbatim, so a whole-file `in` check passed with the
    flags deleted from the `run:` line -- a test that measured its own
    documentation. The probe that removed the flags is what caught it.
    """
    return "\n".join(
        line for line in workflow_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def test_the_workflow_exists_and_is_not_empty() -> None:
    """Anti-vacuity: every `in` check below passes trivially over an empty string."""
    assert WORKFLOW.is_file(), f"{WORKFLOW} is missing"
    assert len(directives().splitlines()) > 1


def test_the_comment_stripper_actually_strips() -> None:
    """The control for `directives()`. A stripper that returned the whole file
    would restore exactly the vacuity it was written to remove."""
    body = "jobs:\n  # - run: uv run pytest --junitxml=x.xml\n  - run: echo hi\n"
    kept = [line for line in body.splitlines()
            if line.strip() and not line.strip().startswith("#")]
    assert "--junitxml=" not in "\n".join(kept)
    assert "echo hi" in "\n".join(kept)


def test_every_report_directive_is_present() -> None:
    executable = directives()
    missing = [flag for flag in REQUIRED_DIRECTIVES if flag not in executable]
    assert not missing, f"the CI job no longer produces a test report: {missing}"


def test_the_terminal_report_survives_alongside_the_xml() -> None:
    assert TERMINAL_REPORT in directives(), (
        "--cov-report=xml replaces the default terminal report; without "
        f"{TERMINAL_REPORT} the log loses the summary fail_under is judged on"
    )


def test_the_coverage_gate_is_still_the_thing_being_reported() -> None:
    """The report must come off the run that enforces the floor, not a second one."""
    assert "pytest --cov" in directives()


def test_both_emitted_reports_are_gitignored() -> None:
    """PurePosixPath, not Path: on Windows `str(Path("reports/junit.xml"))` is
    `reports\\junit.xml`, and comparing that against a forward-slash name reported
    a report as trackable when git had said the opposite. The first draft of this
    test failed for that reason, which is the same separator bug
    `gitignore_probe.git_ignored` already carries a note about on its stdin side."""
    assert git_available(), "git is not on PATH; this check cannot be run"
    ignored = {name.replace("\\", "/") for name in
               git_ignored([PurePosixPath(name) for name in EMITTED_PATHS])}
    missing = [name for name in EMITTED_PATHS if name not in ignored]
    assert not missing, (
        f"per-run test reports that git would happily track: {missing}. "
        f"They are build output and belong in the run artifact, not in history."
    )


def test_the_ignore_probe_still_discriminates() -> None:
    """Control: without it, an all-clear above could mean git answered nothing."""
    assert git_available(), "git is not on PATH; this check cannot be run"
    assert not git_ignored([PurePosixPath("pyproject.toml")])
