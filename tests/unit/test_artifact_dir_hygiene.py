"""D7-19: what `game_artifacts/` publishes, and what it must never publish.

`game_artifacts/` is deliberately NOT ignored -- D7-1's resolution, because
rule 50 and Appendix F rule 4 require the four JSON artifacts to be committed.
The cost is that every `scripts/dev_launch.py` run leaves untracked files
there, and a single `git add -A` would put a throwaway local game into the
repository under filenames a grader reads as league evidence. 07-05, 07-07 and
07-08 each cleaned them up by hand and none of the three wrote down that the
next executor has to.

BOTH HALVES ARE ASSERTED HERE, and one without the other is worthless. The
first half alone ("`.eml` is ignored") would be satisfied by ignoring the whole
directory, which would undo D7-1 and silently exclude the real league evidence
07-10 has to commit. The second half alone ("`result_` is not ignored") was
already true and did nothing to stop the debris.

The FULL problem is not closed here and this file does not pretend it is: which
files under `game_artifacts/` are real league evidence and which are debris is a
judgement only the operator running the league game can make, and 07-10 owns it
(`docs/phases/phase-7/OAUTH-RUNBOOK.md` Sec6).
"""

from __future__ import annotations

from pursuit.services.reporting.artifact_names import (
    config_filename,
    declaration_filename,
    log_filename,
    result_filename,
)
from pursuit.shared.reporting_config import load_reporting_config
from tests.unit.gitignore_probe import REPO_ROOT, git_available, git_ignored

GAME_ID = "hygienecheck"
SUB_GAME_INDEX = 1
ROLE = "police"
SHIPPED_REPORTING = REPO_ROOT / "config" / "police" / "reporting.json"

#: Rendered mail and durable-write rotation generations. Neither is JSON the
#: document names, and neither is ever one of the four required artifacts.
DEBRIS_NAMES = (
    f"{result_filename(GAME_ID)[:-len('.json')]}.eml",
    f"{result_filename(GAME_ID)[:-len('.json')]}.prev.json",
)


def _artifact_root():
    """The artifact ROOT `reporting.json` sets -- read, never assumed."""
    return REPO_ROOT / load_reporting_config(SHIPPED_REPORTING).artifact_dir


def _required_names() -> tuple[str, ...]:
    """docs/PARAMETERS.md:165-168's four filenames, from the ONE namer."""
    return (
        declaration_filename(GAME_ID),
        config_filename(GAME_ID, SUB_GAME_INDEX),
        log_filename(GAME_ID, SUB_GAME_INDEX),
        result_filename(GAME_ID),
    )


def test_the_artifact_dir_is_the_one_reporting_json_names():
    """If this ever stops being `game_artifacts`, every path below is asking
    git about a directory the code does not write to."""
    assert _artifact_root() == REPO_ROOT / "game_artifacts"


def test_none_of_the_four_required_artifacts_is_ignored():
    """Rule 50 requires them committed. An ignored one cannot be."""
    assert git_available(), "git is unavailable, so this gate cannot vouch for anything"
    names = _required_names()
    assert len(names) == 4, "the four required names are the whole subject"
    paths = [_artifact_root() / ROLE / name for name in names]
    assert git_ignored(paths) == []


def test_the_directory_itself_is_not_ignored():
    """D7-1's resolution, stated as a check rather than a comment."""
    assert git_ignored([_artifact_root(), _artifact_root() / ROLE]) == []


def test_the_rendered_eml_is_ignored():
    """A dry run's rendered RFC 5322 message is not one of the four."""
    path = _artifact_root() / ROLE / DEBRIS_NAMES[0]
    assert git_ignored([path]) == [str(path)]


def test_the_durable_write_rotation_generation_is_ignored():
    """`result_<id>.prev.json` is the previous generation, not the artifact."""
    path = _artifact_root() / ROLE / DEBRIS_NAMES[1]
    assert git_ignored([path]) == [str(path)]


def test_the_two_debris_patterns_are_not_the_required_names():
    """The anti-vacuity pairing: neither ignored pattern may collide with a
    required one, or the two tests above would be contradicting each other."""
    assert set(DEBRIS_NAMES).isdisjoint(_required_names())


def test_the_readme_is_tracked_and_states_the_add_all_rule():
    """The rule has to live where someone about to sweep the tree will read
    it. A README that does not say it is a README that did not help."""
    readme = _artifact_root() / "README.md"
    assert git_ignored([readme]) == []
    text = readme.read_text(encoding="utf-8")
    assert "git add -A" in text
    assert "D7-19" in text
