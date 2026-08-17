"""Resolve the repository paths a document cites (08-07).

Three documents now assert things about the code by citing it -- `ARCHITECTURE.md`,
`QUALITY-25010.md`, `EXTENSION-POINTS.md` -- so the "does this path still
exist" question is asked from three test modules. CLAUDE.md's no-duplication
rule puts it here at the second copy rather than the third.

RESOLVED AGAINST `git ls-files`, NOT THE FILESYSTEM. An untracked file cannot
reach a grader, so a document citing one is citing something the reader will
not receive. This is the check that would have caught the README's
`training/plot_curves.py`, deleted in `f3d9847` and left documented behind it.
"""

from __future__ import annotations

import re

from tests.unit.submission_gate_helpers import load

common = load("submission_common")

#: A backticked repository path. Globs and `::name` suffixes are excluded on
#: purpose -- the claim being checked is that the FILE exists.
CITED = re.compile(r"`((?:src|tests|scripts|config|training|docs)/[\w./-]+)`")


def cited_paths(doc: str) -> list[str]:
    """Every distinct repository path *doc* cites in backticks, sorted.

    A trailing slash is normalised away: `src/pursuit/strategy/` is a
    legitimate way to cite a directory, and the question being asked is
    whether the directory exists.
    """
    return sorted({hit.rstrip("/") for hit in CITED.findall(common.read_tracked(doc))})


def unresolved_citations(doc: str) -> list[str]:
    """The cited paths `git ls-files` has neither as a file nor as a directory."""
    tracked = common.tracked_files()
    return [
        path for path in cited_paths(doc)
        if path not in tracked and not any(entry.startswith(path + "/") for entry in tracked)
    ]
