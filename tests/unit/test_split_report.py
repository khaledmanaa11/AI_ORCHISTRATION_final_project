"""The git-shape rows and the report of one built split repository (08-10).

THE HISTORY ROWS ARE WHY THIS EXISTS. A split built by `git init`ing inside the
development tree, or by cloning it, inherits several hundred private commits and
an `origin` pointing at a repository the human may not have meant to publish.
`disjoint_history_row` asserts the built commit is in NO history the source
repository knows, and the test proves the row can fail by handing it a commit
that IS in the source.

`overall(())` IS FALSE. An empty row list is the vacuous pass in its purest
form -- nothing was checked, so nothing failed -- and `all(())` is True in
Python, which is exactly the trap.
"""

from __future__ import annotations

import subprocess

from tests.unit.submission_gate_helpers import REPO_ROOT, load

build_mod = load("split_build")
docs_mod = load("split_docs")
report_mod = load("split_report")


def _built(tmp_path, banner: bool = True):
    root = tmp_path / "out"
    root.mkdir()
    text = "# Title\n\nbody\n"
    if banner:
        text = docs_mod.inject(text, docs_mod.banner("police", "abc1234", "now"))
    (root / "README.md").write_text(text, encoding="utf-8")
    build_mod.init_and_commit(root, ("README.md",), "initial", REPO_ROOT)
    return root


def test_a_freshly_built_repository_passes_every_git_row(tmp_path) -> None:
    rows = report_mod.git_rows(_built(tmp_path), REPO_ROOT, "police")
    assert len(rows) == 4
    assert report_mod.overall(rows) is True


def test_the_single_commit_row_fails_on_a_second_commit(tmp_path) -> None:
    root = _built(tmp_path)
    (root / "extra.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "extra.md"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit",
                    "--no-verify", "-m", "second"], cwd=root, check=True, capture_output=True)
    row = next(row for row in report_mod.git_rows(root, REPO_ROOT, "police")
               if "commit" in row.name and "history" not in row.name)
    assert row.ok is False
    assert "2" in row.detail


def test_the_no_remote_row_fails_on_a_planted_remote(tmp_path) -> None:
    root = _built(tmp_path)
    subprocess.run(["git", "remote", "add", "origin", "../elsewhere.git"],
                   cwd=root, check=True, capture_output=True)
    row = next(row for row in report_mod.git_rows(root, REPO_ROOT, "police")
               if "remote" in row.name)
    assert row.ok is False
    assert "origin" in row.detail


def test_the_banner_row_fails_when_the_readme_carries_no_cross_link(tmp_path) -> None:
    root = _built(tmp_path, banner=False)
    row = next(row for row in report_mod.git_rows(root, REPO_ROOT, "police")
               if "cross-link" in row.name)
    assert row.ok is False


def test_the_history_row_fails_for_a_commit_the_source_already_knows() -> None:
    source_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                                 capture_output=True, text=True, check=True).stdout.strip()
    row = report_mod.disjoint_history_row(REPO_ROOT, source_head)
    assert row.ok is False
    assert source_head[:7] in row.detail


def test_the_history_row_passes_for_the_built_commit(tmp_path) -> None:
    root = _built(tmp_path)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True, check=True).stdout.strip()
    row = report_mod.disjoint_history_row(REPO_ROOT, sha)
    assert row.ok is True


def test_an_empty_row_list_is_not_a_pass() -> None:
    assert report_mod.overall(()) is False


def test_render_prints_every_row_and_the_verdict() -> None:
    rows = (report_mod.Check("a", True, "1 thing"), report_mod.Check("b", False, "0 things"))
    text = report_mod.render("police", rows)
    assert "a" in text and "b" in text and "1 thing" in text
    assert "FAIL" in text
    assert report_mod.render("police", (report_mod.Check("a", True, "x"),)).count("FAIL") == 0
