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
#: The file name appended to a directory claim before git is asked about it.
#: Never created; `git check-ignore` answers about a path, not about a file.
DIRECTORY_PROBE = "ignore-probe-file"


def as_probe_path(claim: str) -> str:
    """The path to actually put to `git check-ignore` for one ignore claim.

    A DIRECTORY CLAIM CANNOT BE ASKED DIRECTLY, AND BOTH OBVIOUS SPELLINGS ARE
    WRONG. Measured on git 2.53.0.windows.2, in this repository:

    * `graphify-out` (no slash) -- a directory-only pattern matches only when
      the directory EXISTS on the machine running the test. Ignored here, NOT
      ignored in a freshly built split repository where it has never been
      created. That is what broke the split's suite in 08-10.
    * `graphify-out/` (with slash) -- reported ignored, matching a BLANK LINE.
      So is `README.md/`, which this repository tracks, and so is
      `definitely-not-ignored-xyz/`. Any non-existent path ending in `/` comes
      back ignored, so the question can never fail and answers nothing.

    Asking about a path INSIDE the directory has neither problem: it is matched
    by the real rule, at the real line, whether or not anything exists on disk.
    """
    return f"{claim.rstrip('/')}/{DIRECTORY_PROBE}" if claim.endswith("/") else claim


def git_available() -> bool:
    """Whether `git` is on PATH. A caller ASSERTS on this rather than skipping:
    a gate that reports OK for having looked at nothing is worse than no gate
    (the D7-6 standard)."""
    return shutil.which("git") is not None


def git_ignored(paths: list[Path | str]) -> list[str]:
    """The subset of `paths` git would refuse to track.

    NUL-separated and in BYTES both ways: `text=True` on Windows writes CRLF
    into the child's stdin, and git then sees every path with a trailing `\\r`.
    Measured -- that alone reported five false positives.

    `str` IS ACCEPTED ALONGSIDE `Path`, AND THAT MATTERS. `Path("graphify-out/")`
    quietly drops the trailing slash, and a directory-only `.gitignore` pattern
    then matches only when the directory HAPPENS TO EXIST on the machine running
    the test. Measured in 08-10: the same question answered "ignored" in the
    development tree and "not ignored" in a freshly built split repository, where
    the build artifact directory has never been created. A caller that wants the
    slash-preserving question asks it with a `str`.
    """
    result = subprocess.run(
        ["git", "check-ignore", "--stdin", "-z"],
        input=b"\0".join(str(path).encode("utf-8") for path in paths),
        capture_output=True, cwd=REPO_ROOT, check=False,
    )
    return [chunk.decode("utf-8") for chunk in result.stdout.split(b"\0") if chunk.strip()]
