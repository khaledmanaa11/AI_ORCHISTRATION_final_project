"""The git-shape rows of a built split repository, and its report (08-10).

FOUR PROPERTIES THAT ARE ONLY TRUE IF SOMEONE CHECKS THEM.

* ONE commit. Two means the build ran twice into the same tree, or something
  else committed there, and the second commit's provenance is unknown.
* ZERO remotes. This plan builds locally and pushes nothing; the remote is added
  by a human at 08-12 after the public repository exists.
* A history DISJOINT from the source. A split made by cloning, or by `git init`
  inside the working tree, carries several hundred private commits and an
  inherited `origin` -- one reflex `git push` publishes all of them.
* The rule-49 cross-link block present in the README.

`overall(())` IS FALSE, DELIBERATELY. `all(())` is True in Python, so a verifier
built the obvious way reports PASS when its row list came back empty -- the
vacuous pass in its purest form, and the exact failure this phase keeps finding.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from split_docs import MARKER
from split_verify import Check, git_out


def _count(root: Path, *args: str) -> str:
    return git_out(root, *args).strip()


def single_commit_row(dest: Path) -> Check:
    """Exactly one commit -- the initial import, and nothing since."""
    count = _count(dest, "rev-list", "--count", "HEAD")
    return Check("exactly one commit", count == "1", f"rev-list --count HEAD = {count or '?'}")


def no_remote_row(dest: Path) -> Check:
    """Zero remotes. Nothing in this plan may be pushable by accident."""
    found = [name for name in git_out(dest, "remote").splitlines() if name.strip()]
    return Check("zero remotes", not found, f"{len(found)} remote(s) {found}")


def disjoint_history_row(source_root: Path, sha: str) -> Check:
    """The built commit must exist in NO history the source repository knows."""
    known = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=source_root, capture_output=True, text=True, check=False,
    ).returncode == 0
    return Check(
        "history disjoint from the source repository",
        not known,
        f"commit {sha[:7]} {'IS' if known else 'is not'} an object in the source "
        "repository; a shared commit would mean an inherited history",
    )


def cross_link_row(dest: Path, role: str) -> Check:
    """The rule-49 block, present and naming this repository's own role."""
    readme = Path(dest) / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    ok = MARKER in text and f"role={role}" in text
    return Check(
        "rule-49 cross-link block present",
        ok,
        f"README.md {'carries' if ok else 'does NOT carry'} the split banner for "
        f"role={role} ({len(text)} bytes read)",
    )


def git_rows(dest: Path, source_root: Path, role: str) -> tuple[Check, ...]:
    """Every git-shape row for one built repository."""
    sha = _count(dest, "rev-parse", "HEAD")
    return (
        single_commit_row(dest),
        no_remote_row(dest),
        disjoint_history_row(source_root, sha),
        cross_link_row(dest, role),
    )


def overall(rows) -> bool:
    """True only when there is at least one row and every row passed."""
    listed = tuple(rows)
    return bool(listed) and all(row.ok for row in listed)


def render(role: str, rows) -> str:
    """A plain-text report: one line per row, every count visible."""
    listed = tuple(rows)
    lines = [f"=== split repository: {role} ===", ""]
    lines += [f"[{'PASS' if row.ok else 'FAIL'}] {row.name}: {row.detail}" for row in listed]
    passed = sum(1 for row in listed if row.ok)
    lines += ["", f"{passed}/{len(listed)} rows passed"]
    if not overall(listed):
        lines.append("VERDICT: FAIL")
    else:
        lines.append("VERDICT: pass")
    return "\n".join(lines) + "\n"
