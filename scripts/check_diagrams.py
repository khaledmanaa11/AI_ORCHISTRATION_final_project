"""Every mermaid diagram in the tracked docs: does it parse, and does every
module it names exist? (08-07)

    uv run python scripts/check_diagrams.py            # 0 clean | 1 problems | 2 judged nothing

THE EXIT CONTRACT IS `measure_gate7.py`'s, INHERITED THROUGH D-82. Exit 2 --
never 0 -- when the run examined no diagram at all, because a checker that
reports OK for having looked at nothing is the failure three separate gates in
this repository have already been caught committing.

WHY A LABEL THAT DOES NOT RESOLVE IS THE HEADLINE FINDING. A diagram naming
`src/pursuit/strategy/qtable.py` would document a mechanism this project
WITHDREW (`docs/PRD_rl_strategy.md`'s superseded banner), and it would do it in
the file a grader opens first. Documents here have drifted from code before:
the README described a Q-learning agent that never shipped, and a documented
command deleted in `f3d9847` sat in it unrunnable. Every label is therefore
resolved against `git ls-files`, not against the filesystem -- an untracked
module cannot reach a grader either.
"""

from __future__ import annotations

import sys

from diagram_parse import block_problems, extract_blocks, module_labels
from submission_common import (
    REPO_ROOT,
    SubmissionExit,
    read_tracked,
    tracked_files,
    tracked_matching,
)

DOC_PREFIX = "docs/"


def _resolves(label: str) -> bool:
    """A label resolves when it is a tracked file or a tracked directory."""
    tracked = tracked_files()
    return label in tracked or any(path.startswith(label + "/") for path in tracked)


def collect() -> tuple[list, list[str], list[str]]:
    """(blocks, structural problems, unresolved labels) over every tracked doc."""
    blocks, problems, unresolved = [], [], []
    for path in tracked_matching(prefix=DOC_PREFIX, suffix=".md"):
        found, fence_problems = extract_blocks(path, read_tracked(path))
        problems.extend(fence_problems)
        for block in found:
            blocks.append(block)
            problems.extend(block_problems(block))
            unresolved.extend(
                f"{block.where} names {label!r}, which git ls-files does not have"
                for label in module_labels(block)
                if not _resolves(label)
            )
    return blocks, problems, unresolved


def main() -> int:
    blocks, problems, unresolved = collect()
    labels = sorted({label for block in blocks for label in module_labels(block)})
    print(f"repo: {REPO_ROOT}")
    print(f"tracked docs scanned: {len(tracked_matching(prefix=DOC_PREFIX, suffix='.md'))}")
    print(f"rendered mermaid blocks: {len(blocks)}")
    print(f"distinct src/pursuit labels: {len(labels)}")
    if not blocks:
        print("EMPTY EVIDENCE: no mermaid block was examined")
        return int(SubmissionExit.EMPTY_EVIDENCE)
    if not labels:
        print("EMPTY EVIDENCE: no diagram named a single module, so nothing was resolved")
        return int(SubmissionExit.EMPTY_EVIDENCE)
    for line in problems + unresolved:
        print(f"  PROBLEM: {line}")
    if problems or unresolved:
        print(f"VERDICT: {len(problems)} structural, {len(unresolved)} unresolved (exit 1)")
        return int(SubmissionExit.GAPS_FOUND)
    print(f"VERDICT: OK -- {len(blocks)} blocks parse, all {len(labels)} labels resolve")
    return int(SubmissionExit.OK)


if __name__ == "__main__":
    sys.exit(main())
