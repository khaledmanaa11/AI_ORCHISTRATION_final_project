"""Materialising one split repository on disk, outside this tree (08-10, D-76).

NOTHING HERE TOUCHES A REMOTE. Every git call is `init`, `add`, `commit`,
`remote` (a read), `rev-parse` or `rev-list`. There is no `push`, no `remote
add`, no `fetch` and no `tag` anywhere in this module, and `assert_no_remotes`
turns that from an intention into a checked property of the built tree. Pushing
is 08-12, and it is a human's decision on a human's account.

THE DESTINATION IS CHECKED AGAINST THE SOURCE. `git init` inside the development
working tree gives the new repository the old one's history and its `origin`; a
single reflex `git push` then publishes several hundred private commits to a
public URL. `prepare_destination` refuses any destination at or under the source
root, and the refusal is proven by making it happen in
`tests/unit/test_split_build.py`.

FILES ARE STAGED BY EXPLICIT PATHSPEC, never `git add -A`. The list comes from
`split_manifest`, is written to a NUL-separated file and handed to git with
`--pathspec-from-file`, so what is committed is exactly what the manifest said
and a stray file in the destination cannot join the commit by accident.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

from split_docs import EmptyBuildError

#: `[project] authors = [{ name = "...", email = "..." }]`, for the commit identity.
_AUTHOR = re.compile(r'name\s*=\s*"([^"]+)"\s*,\s*email\s*=\s*"([^"]+)"')


class UnsafeDestinationError(RuntimeError):
    """The build destination is inside the source repository, or already in use."""


class RemoteFoundError(RuntimeError):
    """A built repository has a remote. It must have none until a human adds one."""


def _force_writable(func, path, _exc_info) -> None:
    """Retry a failed removal after clearing the read-only bit.

    MEASURED, NOT DEFENSIVE. Git writes every loose object read-only, and on
    Windows `os.unlink` then raises `PermissionError: [WinError 5]` -- the first
    real `--replace` rebuild died part-way through deleting `.git/objects/` and
    left a destination that was neither the old tree nor the new one. A
    half-deleted repository is the worst possible state for something a human is
    about to publish.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _run(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def commit_identity(source_root: Path) -> tuple[str, str]:
    """The author declared in `pyproject.toml`, never a literal in this file."""
    text = (source_root / "pyproject.toml").read_text(encoding="utf-8")
    match = _AUTHOR.search(text)
    if not match:
        raise ValueError(
            f"{source_root / 'pyproject.toml'} declares no `authors` entry, so the split "
            "commit has no author to attribute. Refusing to invent one."
        )
    return match.group(1), match.group(2)


def prepare_destination(dest: Path, source_root: Path, replace: bool = False) -> Path:
    """An empty directory OUTSIDE *source_root*, created if it does not exist."""
    dest = Path(dest).resolve()
    source_root = Path(source_root).resolve()
    if dest == source_root or source_root in dest.parents:
        raise UnsafeDestinationError(
            f"{dest} is inside the source repository {source_root}. A split built there "
            "would inherit this repository's history and its remote; one reflex push then "
            "publishes every private commit. Build outside the tree (D-76)."
        )
    if dest.exists() and any(dest.iterdir()):
        if not replace:
            raise UnsafeDestinationError(
                f"{dest} already exists and is not empty. Pass replace=True to rebuild it, "
                "so that a stale tree can never be mistaken for a fresh build."
            )
        shutil.rmtree(dest, onerror=_force_writable)
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def copy_files(source_root: Path, dest_root: Path, paths) -> int:
    """Copy every listed path, byte for byte, and return how many were copied."""
    listed = tuple(paths)
    if not listed:
        raise EmptyBuildError(
            "copy_files was given an empty file list. A repository built from nothing "
            "passes every quality gate by looking at nothing."
        )
    copied = 0
    for relative in listed:
        origin = Path(source_root) / relative
        if not origin.is_file():
            raise FileNotFoundError(
                f"{origin} is in the manifest but not in the source tree. The manifest "
                "comes from `git ls-files`, so this means the working tree is missing a "
                "tracked file -- refusing to build a repository quietly short of one."
            )
        target = Path(dest_root) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
        copied += 1
    return copied


def remotes(root: Path) -> tuple[str, ...]:
    """Every configured remote name. Expected to be empty, always, here."""
    listed = _run(root, "remote")
    return tuple(name for name in listed.splitlines() if name.strip())


def assert_no_remotes(root: Path) -> int:
    """0 remotes, or raise. Returns the count so a caller can record the number."""
    found = remotes(root)
    if found:
        raise RemoteFoundError(
            f"{root} has remotes {found}. A split repository must carry none until a "
            "human creates the public repository and adds one (08-12)."
        )
    return 0


def init_and_commit(dest_root: Path, paths, message: str, source_root: Path) -> str:
    """`git init`, stage exactly *paths* by pathspec, commit once, return the hash."""
    listed = tuple(paths)
    if not listed:
        raise EmptyBuildError("refusing to create a repository with an empty first commit.")
    name, email = commit_identity(source_root)
    _run(dest_root, "init", "-b", "main")
    spec = Path(dest_root) / ".git" / "split-pathspec"
    spec.write_bytes(b"\0".join(path.encode("utf-8") for path in listed))
    _run(dest_root, "add", "--pathspec-from-file", str(spec), "--pathspec-file-nul")
    spec.unlink()
    _run(
        dest_root, "-c", f"user.name={name}", "-c", f"user.email={email}",
        "-c", "commit.gpgsign=false", "commit", "--no-verify", "-m", message,
    )
    assert_no_remotes(dest_root)
    return _run(dest_root, "rev-parse", "HEAD")
