"""Materialising one split repository on disk (08-10, D-76).

THREE REFUSALS ARE THE POINT OF THIS FILE, and each is proven by making the bad
thing happen rather than by reading the code:

* a destination INSIDE the source repository -- `git init` inside a working tree
  is how a split gets an inherited history and, one reflex `git push` later, 486
  private commits on a public URL;
* a built repository that has ANY remote -- this plan builds locally and pushes
  nothing, so the guard is asserted against a planted remote;
* a build of zero files -- an empty repository passes every quality gate by
  looking at nothing, which is the vacuity `05-18-SUMMARY.md` recorded.

The git assertions below are counts (`rev-list --count`, `ls-files | len`), never
exit codes, for the same reason.
"""

from __future__ import annotations

import subprocess

import pytest

from tests.unit.submission_gate_helpers import REPO_ROOT, load

build_mod = load("split_build")


def _git(root, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def _tiny_source(tmp_path):
    source = tmp_path / "source"
    (source / "src").mkdir(parents=True)
    (source / "README.md").write_text("# Title\n\nbody\n", encoding="utf-8")
    (source / "src" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    return source


def test_a_destination_inside_the_source_repository_is_refused(tmp_path) -> None:
    with pytest.raises(build_mod.UnsafeDestinationError):
        build_mod.prepare_destination(REPO_ROOT / "build-here", REPO_ROOT)


def test_a_destination_that_is_the_source_repository_is_refused() -> None:
    with pytest.raises(build_mod.UnsafeDestinationError):
        build_mod.prepare_destination(REPO_ROOT, REPO_ROOT)


def test_an_outside_destination_is_created(tmp_path) -> None:
    dest = build_mod.prepare_destination(tmp_path / "pursuit-police", REPO_ROOT)
    assert dest.is_dir()
    assert not any(dest.iterdir())


def test_an_existing_destination_is_replaced_only_on_request(tmp_path) -> None:
    dest = tmp_path / "pursuit-police"
    dest.mkdir()
    (dest / "stale.txt").write_text("old", encoding="utf-8")
    with pytest.raises(build_mod.UnsafeDestinationError):
        build_mod.prepare_destination(dest, REPO_ROOT, replace=False)
    build_mod.prepare_destination(dest, REPO_ROOT, replace=True)
    assert not (dest / "stale.txt").exists()


def test_copy_files_copies_every_listed_path_and_counts_them(tmp_path) -> None:
    source = _tiny_source(tmp_path)
    dest = tmp_path / "out"
    copied = build_mod.copy_files(source, dest, ("README.md", "src/mod.py"))
    assert copied == 2
    assert (dest / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    assert (dest / "README.md").read_text(encoding="utf-8") == "# Title\n\nbody\n"


def test_copy_files_refuses_an_empty_file_list(tmp_path) -> None:
    with pytest.raises(build_mod.EmptyBuildError):
        build_mod.copy_files(_tiny_source(tmp_path), tmp_path / "out", ())


def test_copy_files_refuses_a_path_that_is_not_in_the_source(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        build_mod.copy_files(_tiny_source(tmp_path), tmp_path / "out", ("ghost.py",))


def test_the_built_repository_has_one_commit_and_no_remote(tmp_path) -> None:
    source = _tiny_source(tmp_path)
    dest = tmp_path / "out"
    build_mod.copy_files(source, dest, ("README.md", "src/mod.py"))
    sha = build_mod.init_and_commit(dest, ("README.md", "src/mod.py"), "initial", REPO_ROOT)
    assert len(sha) >= 7
    assert _git(dest, "rev-list", "--count", "HEAD") == "1"
    assert _git(dest, "remote") == ""
    assert len(_git(dest, "ls-files").splitlines()) == 2


def test_the_no_remote_guard_fires_on_a_planted_remote(tmp_path) -> None:
    source = _tiny_source(tmp_path)
    dest = tmp_path / "out"
    build_mod.copy_files(source, dest, ("README.md",))
    build_mod.init_and_commit(dest, ("README.md",), "initial", REPO_ROOT)
    subprocess.run(
        ["git", "remote", "add", "origin", "../elsewhere.git"],
        cwd=dest, check=True, capture_output=True,
    )
    assert build_mod.remotes(dest) == ("origin",)
    with pytest.raises(build_mod.RemoteFoundError):
        build_mod.assert_no_remotes(dest)


def test_the_no_remote_guard_passes_on_the_freshly_built_tree(tmp_path) -> None:
    source = _tiny_source(tmp_path)
    dest = tmp_path / "out"
    build_mod.copy_files(source, dest, ("README.md",))
    build_mod.init_and_commit(dest, ("README.md",), "initial", REPO_ROOT)
    assert build_mod.remotes(dest) == ()
    assert build_mod.assert_no_remotes(dest) == 0


def test_the_commit_identity_is_read_from_the_project_metadata() -> None:
    name, email = build_mod.commit_identity(REPO_ROOT)
    declared = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert name and email
    assert name in declared
    assert email in declared
