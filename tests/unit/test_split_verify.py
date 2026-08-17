"""Verifying a built split repository from inside it (08-10).

THE TRAP THIS FILE IS WRITTEN AGAINST, stated once: `check_line_limit.sh`'s
no-argument form enumerates through `git ls-files`, which is EMPTY in a freshly
`git init`ed tree before the first commit. The gate then exits 0 having scanned
nothing, and a green exit code in a fresh split proves precisely nothing. The
same vacuity is on record in `05-18-SUMMARY.md`.

So `test_the_scanned_count_is_zero_before_the_first_commit` BUILDS that tree --
files on disk, git initialised, nothing committed -- and asserts both halves:
the scan set is 0, and the row that judges it is FALSE. A verifier that only
read the exit code would report that tree as clean.

Every other row here is asserted the same way: a count, and a planted defect
that must flip it.
"""

from __future__ import annotations

import shutil
import subprocess

from tests.unit.submission_gate_helpers import REPO_ROOT, load

verify_mod = load("split_verify")


def _init(root):
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)


def _tree(tmp_path, committed: bool):
    """A tree carrying the REAL gate script, so its exit code is a real one."""
    root = tmp_path / "tree"
    (root / "src" / "pursuit").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / "src" / "pursuit" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "README.md").write_text("# T\n", encoding="utf-8")
    shutil.copy2(REPO_ROOT / "scripts" / "check_line_limit.sh", root / "scripts")
    _init(root)
    if committed:
        subprocess.run(["git", "add", "-f", "src", "README.md"], cwd=root,
                       check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                        "commit", "--no-verify", "-m", "x"], cwd=root,
                       check=True, capture_output=True)
    return root


def test_line_limit_scope_counts_the_real_repository() -> None:
    scope = verify_mod.line_limit_scope(REPO_ROOT)
    assert len(scope) > 300, f"only {len(scope)} files in the line-limit scope"


def test_the_scanned_count_is_zero_before_the_first_commit(tmp_path) -> None:
    root = _tree(tmp_path, committed=False)
    assert verify_mod.line_limit_scope(root) == ()
    row = verify_mod.line_limit_row(root)
    assert row.detail.startswith("exit 0"), "the shell gate is expected to pass VACUOUSLY here"
    assert row.ok is False
    assert "scanned 0" in row.detail


def test_the_scanned_count_is_positive_after_the_first_commit(tmp_path) -> None:
    root = _tree(tmp_path, committed=True)
    assert len(verify_mod.line_limit_scope(root)) == 1
    row = verify_mod.line_limit_row(root)
    assert row.ok is True
    assert "scanned 1" in row.detail


def test_the_real_repository_passes_the_line_limit_row_with_a_real_count() -> None:
    row = verify_mod.line_limit_row(REPO_ROOT)
    assert row.ok is True
    assert "scanned 0" not in row.detail


def test_absence_row_catches_a_planted_forbidden_file(tmp_path) -> None:
    root = _tree(tmp_path, committed=True)
    (root / ".env").write_text("ANTHROPIC_API_KEY=planted\n", encoding="utf-8")
    row = verify_mod.absence_row(root)
    assert row.ok is False
    assert ".env" in row.detail


def test_absence_row_passes_on_a_tree_without_them(tmp_path) -> None:
    row = verify_mod.absence_row(_tree(tmp_path, committed=True))
    assert row.ok is True
    assert "0 present" in row.detail


def test_absence_row_also_catches_a_planted_counter(tmp_path) -> None:
    root = _tree(tmp_path, committed=True)
    (root / "config" / "police").mkdir(parents=True)
    (root / "config" / "police" / "games_played.json").write_text("{}", encoding="utf-8")
    row = verify_mod.absence_row(root)
    assert row.ok is False
    assert "games_played" in row.detail


def test_config_row_counts_both_seats_in_the_real_repository() -> None:
    row = verify_mod.config_row(REPO_ROOT)
    assert row.ok is True
    assert "police 14" in row.detail and "thief 14" in row.detail


def test_config_row_fails_when_a_seat_is_missing(tmp_path) -> None:
    row = verify_mod.config_row(_tree(tmp_path, committed=True))
    assert row.ok is False


def test_rule50_row_on_the_real_repository() -> None:
    row = verify_mod.rule50_row(REPO_ROOT)
    assert row.ok is True
    for token in ("README", "PRD", "PLAN", "TODO"):
        assert token in row.detail


def test_workflow_row_flags_a_script_the_workflow_names_but_does_not_ship(tmp_path) -> None:
    root = _tree(tmp_path, committed=True)
    flows = root / ".github" / "workflows"
    flows.mkdir(parents=True)
    (flows / "ci.yml").write_text("jobs:\n  a:\n    steps:\n"
                                  "      - run: sh scripts/ghost.sh\n", encoding="utf-8")
    row = verify_mod.workflow_row(root)
    assert row.ok is False
    assert "scripts/ghost.sh" in row.detail


def test_workflow_row_passes_on_the_real_repository() -> None:
    row = verify_mod.workflow_row(REPO_ROOT)
    assert row.ok is True
    assert "0 missing" in row.detail
    assert "referenced" in row.detail
