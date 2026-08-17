"""GATE-8 criterion 1 -- the two repositories and the tag, measured (08-11).

> 1. Two cross-linked public repos (cop, thief), each carrying
>    README/config/PRD/PLAN/TODO, with a Git tag on the submitted version

THREE HALVES, NOT ONE VERDICT. `built` and `tagged` are measurable on this
machine today; **`published` is not, and is reported PENDING** -- creating a
GitHub repository and pushing to it needs an account, a consent screen and an
irreversible outward call, all of which are 08-12's human's. `remote_count` is
recorded per output precisely because `0` is the evidence that nothing has been
published from here.
"""

from __future__ import annotations

import re
from pathlib import Path

from gate8_common import ROLES, git_code, git_out, lines, split_root, tag_name

#: Rule 50's floor, counted rather than asserted present.
_RULE50 = {
    "README": lambda paths: [p for p in paths if p == "README.md"],
    "config": lambda paths: [p for p in paths if p.startswith("config/")],
    "PRD": lambda paths: [p for p in paths if p.startswith("docs/PRD") and p.endswith(".md")],
    "PLAN": lambda paths: [p for p in paths if p.endswith("PLAN.md")],
    "TODO": lambda paths: [p for p in paths if p.endswith("TODO.md")],
}
_URL = re.compile(r"https?://[^\s)|]+")
_BANNER = "<!-- split-repo-banner role={role} "


def _tracked(root: Path) -> list[str]:
    return lines(git_out(root, "ls-files"))


def _tag_facts(root: Path, name: str) -> dict:
    """Everything about the tag except whether it has been pushed -- it has not."""
    exists = name in lines(git_out(root, "tag", "-l"))
    if not exists:
        return {"name": name, "exists": False, "annotated": False, "points_at_head": False,
                "tree_file_count": 0, "message_lines": [], "pushed": False}
    kind = git_out(root, "cat-file", "-t", name).strip()
    head = git_out(root, "rev-parse", "HEAD").strip()
    target = git_out(root, "rev-list", "-n", "1", name).strip()
    message = lines(git_out(root, "tag", "-l", name, "-n20"))
    return {
        "name": name,
        "exists": True,
        "annotated": kind == "tag",
        "points_at_head": bool(head) and head == target,
        "target_commit": target,
        "tree_file_count": len(lines(git_out(root, "ls-tree", "-r", "--name-only", name))),
        "message_lines": message,
        "pushed": False,
    }


def _banner_block(text: str, role: str) -> str:
    """The marker plus the contiguous blockquote under it -- and no further.

    The first draft took a fixed 2000 characters, ran past the end of the
    blockquote into the README body, and reported `https://gofastmcp.com` as a
    rule-49 URL leak. A slice long enough to be safe is a slice long enough to
    read the wrong document.
    """
    start = text.find(_BANNER.format(role=role))
    if start < 0:
        return ""
    block: list[str] = []
    for line in text[start:].splitlines():
        if block and not line.startswith(">") and line.strip():
            break
        block.append(line)
    return "\n".join(block)


def _cross_link(root: Path, role: str) -> dict:
    """Rule 49's two links -- present as STATED-ABSENT markers until 08-12."""
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    other = "thief" if role == "police" else "police"
    banner_start = text.find(_BANNER.format(role=role))
    banner = _banner_block(text, role)
    return {
        "banner_present": banner_start >= 0,
        "banner_lines": len(banner.splitlines()),
        "names_the_other_repository": f"pursuit-{other}" in text or f"`{other}`" in banner,
        "urls_in_banner": _URL.findall(banner),
        "repo_split_doc_tracked": "docs/REPO-SPLIT.md" in _tracked(root),
    }


def measure_one(dest: Path, role: str) -> dict:
    """One built output: what it contains, what it is tagged with, what it is not."""
    root = split_root(dest, role)
    if not (root / ".git").is_dir():
        return {"role": role, "root": str(root), "exists": False, "tracked_file_count": 0,
                "remote_count": 0, "commit_count": 0, "rule50": {},
                "cross_link": {}, "tag": _tag_facts(root, tag_name())}
    paths = _tracked(root)
    return {
        "role": role,
        "root": str(root),
        "exists": True,
        "head": git_out(root, "rev-parse", "--short", "HEAD").strip(),
        "commit_count": len(lines(git_out(root, "log", "--oneline"))),
        "tracked_file_count": len(paths),
        "remote_count": len(lines(git_out(root, "remote"))),
        "clean_worktree": not lines(git_out(root, "status", "--porcelain")),
        "rule50": {key: len(select(paths)) for key, select in _RULE50.items()},
        "cross_link": _cross_link(root, role),
        "tag": _tag_facts(root, tag_name()),
    }


def measure(dest: Path) -> dict:
    """Criterion 1, both outputs, plus the half only a human can close."""
    outputs = {role: measure_one(dest, role) for role in ROLES}
    source_tags = lines(git_out(Path.cwd(), "tag", "-l"))
    return {
        "criterion": "1 -- two cross-linked public repos, each with rule-50 content and a tag",
        "tag_name": tag_name(),
        "tag_name_is_derived_from": "src/pursuit/shared/version.py VERSION",
        "outputs": outputs,
        "development_repo_tag_list": source_tags,
        "development_repo_is_deliberately_untagged": not source_tags,
        "published": {
            "verdict": "PENDING",
            "owner": "08-12 (human)",
            "why": "creating a GitHub repository and pushing to it needs an account, a "
                   "consent screen and an irreversible outward call; no agent may do it",
            "evidence_that_nothing_was_published": {
                role: outputs[role]["remote_count"] for role in ROLES
            },
        },
    }


def git_is_present(dest: Path) -> bool:
    """A cheap precondition, so a missing build reads as EMPTY rather than FAIL."""
    return all(git_code(split_root(dest, role), "rev-parse", "HEAD") == 0 for role in ROLES)

