"""Sec17 group 4 -- configuration and security (08-01).

THE SCANNER PROVES IT CAN FIRE BEFORE ITS ALL-CLEAR IS BELIEVED. `G4-02` runs
its patterns over synthetic values built at runtime, and the row is a GAP when
either control does NOT match -- because a clean result from a scanner that
matches nothing is evidence about the scanner, not about the tree. The scan
itself, its two pattern classes and its allowlist live in `submission_scan.py`;
the heavier control, a secret planted in a real file, is 08-03's.

THE IGNORE ROWS ARE ONE ASSERTION PER PATH, never one "`.gitignore` mentions
env" check. `git check-ignore` is asked about each path by name, so a rule that
stops covering one of them shows up as one failing row rather than disappearing
into a satisfied aggregate. The list carries BOTH the root-level `graph.json` /
`graph.html` names that 08-03's brief enumerates AND the `.planning/graphs/`
paths the documented `graphify` workflow actually writes -- asking only about
the second pair would leave the first pair publishable and call it covered.

NOTHING HERE READS A SECRET. `.env` is only ever asked ABOUT, never opened.
"""

from __future__ import annotations

import re

from submission_common import (
    GROUP_4,
    judge,
    read_tracked,
    run,
    tracked_files,
    tracked_matching,
)
from submission_scan import GENERIC_PATTERN, PROVIDER_PATTERNS, scan_tracked_set

ENV_EXAMPLE = ".env-example"
#: Paths that must each be individually proven ignored before anything is published.
MUST_BE_IGNORED = (
    ".env", ".venv/", "logs/", "graph.json", "graph.html",
    ".planning/graphs/graph.json", ".planning/graphs/graph.html",
    "graphify-out/", "run.log", ".coverage", "police_thief_p2p.pdf",
)
#: Live rule-37/38 counters, not configuration. They carry no `version` field
#: because they are state written by a game, and requiring one of them would be
#: asking a counter to describe itself as a config file. Named, not silently
#: skipped, so the exclusion is visible in the row's own evidence.
STATE_NOT_CONFIG = ("games_played.json", "games_played.prev.json")


def _env_example_row() -> object:
    """Every key line must be a placeholder -- checked with the real patterns."""
    text = read_tracked(ENV_EXAMPLE)
    lines = [line for line in text.splitlines() if "=" in line and not line.startswith("#")]
    real_looking = [
        line for line in lines
        if any(re.search(pattern, line) for pattern in (*PROVIDER_PATTERNS, GENERIC_PATTERN))
    ]
    return judge(
        "G4-01", GROUP_4, "Table 5 `.env-example` committed with dummy values",
        bool(lines) and not real_looking,
        f"tracked: {bool(text)}; key lines: {len(lines)}; lines matching a real "
        f"credential shape: {len(real_looking)}",
        ENV_EXAMPLE,
    )


def _secret_scan_row() -> object:
    result = scan_tracked_set()
    return judge(
        "G4-02", GROUP_4, "Table 5 zero secrets in the tracked set (scan + its own controls)",
        result.controls_fired and result.clean and result.scanned > 0,
        result.summary(),
        ".gitignore",
    )


def _ignore_rows() -> list:
    rows = []
    for index, path in enumerate(MUST_BE_IGNORED, start=3):
        code, _ = run(["git", "check-ignore", "-q", path])
        rows.append(judge(
            f"G4-{index:02d}", GROUP_4, f"rule 40 `{path}` is ignored by git",
            code == 0,
            f"`git check-ignore -q {path}` exit {code} (0 = ignored)",
            ".gitignore",
        ))
    return rows


def _uv_row() -> object:
    has_lock = bool(read_tracked("uv.lock"))
    has_project = bool(read_tracked("pyproject.toml"))
    strays = [path for path in tracked_files() if path.endswith("requirements.txt")]
    return judge(
        "G4-20", GROUP_4, "Table 5 `uv` is the sole package manager",
        has_lock and has_project and not strays,
        f"uv.lock tracked: {has_lock}; pyproject.toml tracked: {has_project}; "
        f"requirements.txt files: {strays or 'none'}",
        "pyproject.toml",
    )


def _config_version_row() -> object:
    everything = tracked_matching(prefix="config/", suffix=".json")
    configs = [
        path for path in everything
        if not path.endswith(STATE_NOT_CONFIG)
    ]
    unversioned = [path for path in configs if '"version"' not in read_tracked(path)]
    return judge(
        "G4-21", GROUP_4, "Sec17 separate, VERSIONED configuration files",
        bool(configs) and not unversioned,
        f"tracked config JSON files: {len(everything)}, of which "
        f"{len(everything) - len(configs)} are live counters excluded as state "
        f"({list(STATE_NOT_CONFIG)}); of the remaining {len(configs)}, without a "
        f"`version` field: {len(unversioned)} {unversioned}",
        "config/",
    )


def security_items() -> list:
    """Group 4's rows -- the strongest group, and the one with a live control."""
    return [
        _env_example_row(),
        _secret_scan_row(),
        *_ignore_rows(),
        _uv_row(),
        _config_version_row(),
    ]
