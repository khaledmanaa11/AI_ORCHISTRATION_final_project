"""Sec17 "separate, VERSIONED configuration files" -- asserted, not assumed (08-03).

WHY PRESENCE IS NOT THE WHOLE ASSERTION. `"version": "whatever"` in every file
satisfies a presence check and tells a grader nothing. So the version each file
carries is compared against `shared/version.py` -- the single source Table 5's
T5-06 row reads -- and the ONE file allowed to differ is named here with its
reason. A second deliberate bump therefore has to be declared rather than
absorbed, and a file drifting to an unrelated value fails.

WHY THE COUNTERS ARE NAMED RATHER THAN GLOBBED AWAY. `config/*/games_played*.json`
is live rule-37/38 state written by a game, not configuration, and is gitignored
for that reason -- so it is not in the tracked set this test walks at all. It is
still named below, because the day someone tracks it the exclusion should be a
visible decision and not a silent hole.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pursuit.shared.version import VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PREFIX = "config/"
#: Live rule-37/38 counters. State, not configuration.
STATE_NOT_CONFIG = ("games_played.json", "games_played.prev.json")
#: The one deliberate divergence: the evolutionary weight set is versioned on its
#: OWN training generation, not on the package release. `config/*/weights.json`
#: reads "2.00" because run 2's fit superseded run 1's.
VERSION_EXCEPTIONS = {"config/police/weights.json": "2.00",
                      "config/thief/weights.json": "2.00"}
#: This repository ships two role directories of configuration. A walk that found
#: fewer than this has lost its subject and its all-clear means nothing.
MIN_CONFIG_FILES = 20


def tracked_config_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", f"{CONFIG_PREFIX}*.json"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return [
        line.strip() for line in out.splitlines()
        if line.strip() and not line.strip().endswith(STATE_NOT_CONFIG)
    ]


def test_the_walk_found_the_shipped_configuration() -> None:
    """Anti-vacuity floor: an empty list passes every loop below."""
    found = tracked_config_files()
    assert len(found) >= MIN_CONFIG_FILES, f"only {len(found)} tracked config files: {found}"


def test_every_tracked_config_file_declares_a_version() -> None:
    missing = [
        path for path in tracked_config_files()
        if "version" not in json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
    ]
    assert not missing, f"tracked config files with no `version` field: {missing}"


def test_every_config_version_is_the_package_version_or_a_declared_exception() -> None:
    wrong = {}
    for path in tracked_config_files():
        declared = json.loads((REPO_ROOT / path).read_text(encoding="utf-8")).get("version")
        expected = VERSION_EXCEPTIONS.get(path, VERSION)
        if declared != expected:
            wrong[path] = f"declares {declared!r}, expected {expected!r}"
    assert not wrong, f"config version drift: {wrong}"


def test_every_declared_exception_still_exists() -> None:
    """A stale exception is an exemption for a file nobody checks any more."""
    tracked = set(tracked_config_files())
    stale = [path for path in VERSION_EXCEPTIONS if path not in tracked]
    assert not stale, f"VERSION_EXCEPTIONS names files that are no longer tracked: {stale}"
