"""CLAUDE.md's own gitignore claim, asked of git rather than believed (08-03).

WHY THE EXPECTED LIST IS PARSED AND NOT TYPED. `CLAUDE.md:178` states that
`graph.json`, `graph.html` and `graphify-out/` "are gitignored build artifacts".
When 08-01 audited the tree, `git check-ignore -q graph.json` exited **1**: only
the `graphify-out/` and `.planning/graphs/` copies were covered, so the standing
instruction every agent reads was false about the two ~2 MB root artifacts. A
test whose expected list were typed here would drift away from that sentence the
moment the sentence changed; this one reads the sentence, so the claim and the
check cannot disagree without a failure.

WHY THERE IS A NEGATIVE CONTROL. `git check-ignore` returning nothing is what a
broken invocation also returns -- wrong cwd, a CRLF-mangled stdin (see
`gitignore_probe.git_ignored`'s own note), a git that is not on PATH. The control
asks about paths this repository certainly DOES track; if they come back
"ignored", the helper is answering a different question and the positive result
above it means nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.unit.gitignore_probe import REPO_ROOT, git_available, git_ignored

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
#: The claim this test holds git to, quoted from CLAUDE.md rather than restated.
#: Bounded by `;` and the phrase itself and NOT by `.`, because two of the three
#: names the sentence lists contain a dot -- a `[^;.]` class silently trimmed the
#: match down to ", and " and made the first draft of this test assert nothing.
_CLAIM = re.compile(r";(.*?)are gitignored build artifacts")
_BACKTICKED = re.compile(r"`([^`]+)`")
#: The sentence names three artifacts. A parse that finds fewer has lost its
#: subject, and an assertion over a shrunken list is the vacuous pass this
#: repository has now caught three separate gates making.
EXPECTED_CLAIMED = 3
#: Files this repository certainly tracks -- the discrimination control.
DEFINITELY_TRACKED = ("README.md", "pyproject.toml", "CLAUDE.md")


def claimed_ignored_paths() -> list[str]:
    """The artifact names CLAUDE.md asserts are gitignored."""
    match = _CLAIM.search(CLAUDE_MD.read_text(encoding="utf-8"))
    if match is None:
        return []
    return _BACKTICKED.findall(match.group(1))


def test_claude_md_still_carries_the_claim_this_test_checks() -> None:
    """Anti-vacuity: the subject must exist before the verdict is read."""
    claimed = claimed_ignored_paths()
    assert len(claimed) == EXPECTED_CLAIMED, (
        f"CLAUDE.md's gitignore sentence parsed to {claimed!r}; this test is only "
        f"meaningful while it names {EXPECTED_CLAIMED} artifacts"
    )


def test_git_agrees_with_every_artifact_claude_md_calls_gitignored() -> None:
    assert git_available(), "git is not on PATH; this check cannot be run"
    claimed = claimed_ignored_paths()
    assert claimed, "parsed no artifact names out of CLAUDE.md"
    ignored = set(git_ignored([Path(name) for name in claimed]))
    missing = [name for name in claimed if name.rstrip("/") not in
               {entry.rstrip("/") for entry in ignored}]
    assert not missing, (
        f"CLAUDE.md:178 claims these are gitignored build artifacts, and git "
        f"disagrees: {missing}. Either .gitignore or the sentence is wrong."
    )


def test_the_probe_discriminates_and_does_not_call_everything_ignored() -> None:
    """The control. Without it, a broken invocation would read as an all-clear."""
    assert git_available(), "git is not on PATH; this check cannot be run"
    tracked = git_ignored([Path(name) for name in DEFINITELY_TRACKED])
    assert not tracked, (
        f"git_ignored reported tracked files as ignored: {tracked}. The helper is "
        f"answering a different question, so the positive result above is void."
    )
