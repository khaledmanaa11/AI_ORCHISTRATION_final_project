"""Ask git, once, whether it would refuse to track a path.

Extracted at the second copy (CLAUDE.md Table 5, "extract at 2+ copies"):
`test_gmail_credentials.py` (D7-10) and `test_artifact_dir_hygiene.py` (D7-19)
both need it, and two spellings of "ask git" is how one of them ends up asking
a subtly different question.

Not a `test_*.py` module, so pytest collects nothing from it -- the
`local_truth_helpers.py` precedent.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def git_available() -> bool:
    """Whether `git` is on PATH. A caller ASSERTS on this rather than skipping:
    a gate that reports OK for having looked at nothing is worse than no gate
    (the D7-6 standard)."""
    return shutil.which("git") is not None


def git_ignored(paths: list[Path]) -> list[str]:
    """The subset of `paths` git would refuse to track.

    NUL-separated and in BYTES both ways: `text=True` on Windows writes CRLF
    into the child's stdin, and git then sees every path with a trailing `\\r`.
    Measured -- that alone reported five false positives.
    """
    result = subprocess.run(
        ["git", "check-ignore", "--stdin", "-z"],
        input=b"\0".join(str(path).encode("utf-8") for path in paths),
        capture_output=True, cwd=REPO_ROOT, check=False,
    )
    return [chunk.decode("utf-8") for chunk in result.stdout.split(b"\0") if chunk.strip()]
