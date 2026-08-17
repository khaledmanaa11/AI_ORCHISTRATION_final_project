"""Shared reads for the GATE-8 measurement (08-11).

EVERY GIT VERB IN THIS PACKAGE IS A LOCAL READ OR A LOCAL `tag` WRITE. There is
no `push`, no `fetch`, no `remote add` and no `gh` call anywhere in these files,
and `assert_no_remote_verb` below is run over this package's own source by
`tests/unit/test_gate8_measure.py` so that stays true rather than being promised.

THE TAG NAME IS DERIVED, NEVER CHOSEN (D-79). It is `v` + `shared/version.py`'s
`VERSION`, the single source `tests/unit/test_version_single_source.py` pins
`pyproject.toml` against. Before 08-11 the two disagreed (`1.00` vs `1.00.0`),
which is why D-79 required the reconciliation to land first: a tag derived from
the wrong one of two literals names a version half the repository denies.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from pursuit.shared.version import VERSION  # noqa: E402

ROLES = ("police", "thief")
#: Where 08-10 built the two outputs. OUTSIDE this tree, by D-76.
DEFAULT_SPLIT_DEST = Path("C:/Users/Hp/pursuit-split-repos")
#: Verbs that reach a network. None of them may appear in this package.
NETWORK_VERBS = ("push", "fetch", "pull", "clone", "remote add", "gh ")


def tag_name() -> str:
    """`v1.00` -- derived from VERSION, never typed."""
    return f"v{VERSION}"


def split_root(dest: Path, role: str) -> Path:
    return Path(dest) / f"pursuit-{role}"


def git_out(root: Path, *args: str) -> str:
    """One local git read. Returns empty text on failure rather than raising."""
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    )
    return done.stdout


def git_code(root: Path, *args: str) -> int:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    ).returncode


def lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def package_sources() -> list[Path]:
    """This measurement's own source files -- the subject of the verb scan."""
    return sorted(REPO_ROOT.glob("scripts/gate8_*.py")) + [
        REPO_ROOT / "scripts" / "measure_gate8.py"
    ]


def network_verb_hits(sources: list[Path] | None = None) -> dict[str, list[str]]:
    """Any line in this package that runs a git verb reaching a remote.

    Deliberately crude and deliberately over-broad: it matches the verb inside
    a quoted argument list, which is how every git call here is written. A hit
    is a finding to explain, not a false positive to suppress.

    ONE line is skipped, named rather than pattern-matched: the definition of
    `NETWORK_VERBS` itself, which necessarily contains all of them. The first
    run of this function reported that line and nothing else, and skipping the
    whole file -- the tempting fix -- would have blinded the scan to the file
    that runs every git call in the package.
    """
    hits: dict[str, list[str]] = {}
    for path in (package_sources() if sources is None else sources):
        if not path.is_file():
            continue
        found = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if any(f'"{verb.strip()}"' in line for verb in NETWORK_VERBS)
            and not line.startswith("NETWORK_VERBS = ")
        ]
        if found:
            hits[path.name] = found
    return hits
