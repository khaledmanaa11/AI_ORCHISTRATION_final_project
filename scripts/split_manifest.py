"""The publishable file set of one split repository, from `git ls-files` (08-10).

WHY THE TRACKED SET AND NEVER A DIRECTORY WALK (D-76). `.env` and
`police_thief_p2p.pdf` sit UNTRACKED in this working tree right now. A walk
publishes a live credential file (rules 39-40, project failure) and a
copyrighted textbook in one step; the tracked set contains neither, by
construction rather than by an exclusion someone has to remember to write.

WHAT IS SUBTRACTED (D-77). `config/*/games_played*.json` -- the rule-37 counters
this team declares to the league. They are gitignored today, so `git ls-files`
already omits them; the subtraction is written down ANYWAY, because the day a
`git add -f` puts one in the tracked set is the day the exclusion earns its
keep. `tests/unit/test_split_manifest.py` proves it on a planted input for the
same reason -- an exclusion only ever tested against a set that cannot contain
its target is an exclusion that has never run.

WHY A FORBIDDEN PATH RAISES INSTEAD OF BEING FILTERED. A tracked `.env` is not a
packaging detail to tidy up on the way out; it means the mono-repo itself has
published a credential and a silent filter would hide that. Loud is the
requirement.

BOTH ROLE CONFIG DIRECTORIES SHIP (D-77). `tests/conftest.py`,
`tests/integration/conftest.py`, `tests/_shipped_config_guard.py` and twenty-plus
integration tests load BOTH `config/police/` and `config/thief/`; a repo carrying
one role's directory cannot run its own suite, so it cannot pass Table 5 inside
its own tree. Rule 50 sets a floor (`config/` present), not a ceiling, and rule 2
forbids shared RUNTIME STATE -- which two static directories are not.
"""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: The two agent seats. Static config directories, never shared runtime state.
ROLES = ("police", "thief")

#: D-77. Live rule-37 state, excluded by name even though it is already ignored.
EXCLUDED_GLOBS = (
    "config/*/games_played.json",
    "config/*/games_played.prev.json",
)

#: Basenames that must never be tracked anywhere. Presence raises, never filters.
FORBIDDEN = (".env", "police_thief_p2p.pdf")


class ForbiddenPathError(RuntimeError):
    """A path that must never be published is tracked in the source tree."""


class EmptyManifestError(RuntimeError):
    """The manifest enumerated nothing -- the vacuous-pass shape, refused."""


@dataclass(frozen=True)
class Manifest:
    """One split repository's file list, plus what was subtracted and why."""

    included: tuple[str, ...]
    excluded: tuple[tuple[str, str], ...]

    @property
    def count(self) -> int:
        return len(self.included)

    def as_dict(self) -> dict:
        return {
            "included_count": self.count,
            "excluded": [{"path": path, "reason": reason} for path, reason in self.excluded],
            "included": list(self.included),
        }


def tracked_paths(root: Path) -> tuple[str, ...]:
    """Every path `git ls-files` reports for *root*, POSIX-separated and sorted."""
    done = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return tuple(sorted(
        entry.replace("\\", "/") for entry in done.stdout.split("\0") if entry.strip()
    ))


def exclusion_reason(path: str) -> str:
    """Why *path* is left out of a split repository, or "" when it ships."""
    for pattern in EXCLUDED_GLOBS:
        if fnmatch.fnmatch(path, pattern):
            return f"D-77: live rule-37 counter, matched {pattern}"
    return ""


def _forbidden_hits(paths: tuple[str, ...]) -> list[str]:
    return sorted(path for path in paths if path.rsplit("/", 1)[-1] in FORBIDDEN)


def build_manifest(paths) -> Manifest:
    """Split *paths* into what ships and what does not, refusing both bad ends."""
    ordered = tuple(sorted(paths))
    hits = _forbidden_hits(ordered)
    if hits:
        raise ForbiddenPathError(
            f"the source tree TRACKS {hits}, which must never reach a public repository "
            "(rules 39-40 for a credential file, copyright for the book PDF). This is a "
            "defect in the source tree, not something the split may quietly filter out."
        )
    included: list[str] = []
    excluded: list[tuple[str, str]] = []
    for path in ordered:
        reason = exclusion_reason(path)
        if reason:
            excluded.append((path, reason))
        else:
            included.append(path)
    if not included:
        raise EmptyManifestError(
            f"the manifest included 0 of {len(ordered)} paths. A repository built from an "
            "empty file list passes every gate vacuously -- see 05-18-SUMMARY.md."
        )
    return Manifest(tuple(included), tuple(excluded))


def manifest_for(root: Path) -> Manifest:
    """The manifest of the repository at *root*, straight from its tracked set."""
    return build_manifest(tracked_paths(root))


def role_config_files(manifest: Manifest) -> dict[str, tuple[str, ...]]:
    """Per-role shipped config inventory -- the D-77 assertion, as a count."""
    return {
        role: tuple(
            path for path in manifest.included if path.startswith(f"config/{role}/")
        )
        for role in ROLES
    }
