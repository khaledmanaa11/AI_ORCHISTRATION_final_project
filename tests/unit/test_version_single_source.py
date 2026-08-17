"""T5-06 -- one version, one source of truth (08-11).

`src/pursuit/shared/version.py` is THE source. Everything else in the tree that
carries a version string is checked against it here, so the two-literal defect
T5-06 registered (`version.py` `1.00` against `pyproject.toml` `1.00.0`) cannot
come back silently.

TWO THINGS THIS FILE REFUSES TO DO, both of which would make it vacuous:

1. **It does not type the Table-5 baseline.** `"1.00"` is parsed out of
   `docs/SEGAL_GUIDELINES.md` Sec19.1 Table 5, the document the rule lives in.
   A typed `BASELINE = "1.00"` here agrees with itself for ever.
2. **It compares raw strings, never parsed versions.** `"1.00"` and `"1.0"`
   are the SAME version under PEP 440 and different strings; the tag name D-79
   derives is built from the string, so string equality is the property that
   matters. A packaging-aware comparison would have called the original defect
   a non-issue by normalising `1.00.0` -> `1.0.0` and `1.00` -> `1.0`.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import tomllib

from pursuit.shared.version import VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
GUIDELINES = REPO_ROOT / "docs" / "SEGAL_GUIDELINES.md"

#: The Sec19.1 Table 5 row, matched on its requirement column rather than its value.
_TABLE5_ROW = re.compile(r"\|\s*Version control\s*\|\s*Starts at\s*(\d+\.\d[\d.]*)\s*\|")

#: Version keys that deliberately differ from VERSION, each with the reason it does.
DELIBERATE_BUMPS = {
    "config/police/weights.json": "run-2 refit of the 15-weight vector, a real content bump",
    "config/thief/weights.json": "run-2 refit of the 15-weight vector, a real content bump",
}


def _tracked_config_json() -> list[str]:
    """Every tracked `config/**.json` -- from git, never from a directory walk."""
    listed = subprocess.run(
        ["git", "ls-files", "config"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted(path for path in listed if path.endswith(".json"))


def baseline_from_the_guidelines() -> str:
    """Table 5's `Starts at 1.00`, read out of the guidelines extract."""
    found = _TABLE5_ROW.search(GUIDELINES.read_text(encoding="utf-8"))
    assert found, f"Sec19.1 Table 5's `Version control` row not found in {GUIDELINES.name}"
    return found.group(1)


def pyproject_version() -> str:
    """`[project] version`, read as the literal string TOML carries."""
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def test_the_baseline_parser_reads_a_real_value() -> None:
    """The control: a parser that returns nothing would make every test below pass."""
    baseline = baseline_from_the_guidelines()
    assert re.fullmatch(r"\d+\.\d[\d.]*", baseline), baseline
    assert not _TABLE5_ROW.search("| Version control | Starts at nothing |")


def test_the_module_carries_the_table5_baseline() -> None:
    baseline = baseline_from_the_guidelines()
    assert baseline == VERSION, (
        f"shared/version.py VERSION = {VERSION!r} but Sec19.1 Table 5 says "
        f"versioning starts at {baseline!r}"
    )


def test_pyproject_and_the_version_module_carry_the_same_string() -> None:
    """T5-06 itself. String equality -- `1.00` and `1.0` are not the same tag name."""
    declared = pyproject_version()
    assert declared == VERSION, (
        f"two version literals disagree: pyproject.toml [project] version = "
        f"{declared!r}, src/pursuit/shared/version.py VERSION = {VERSION!r}. "
        f"D-79 derives the submission tag name from VERSION, so a tag cut today "
        f"would name a version pyproject.toml does not claim."
    )


def test_every_tracked_config_json_agrees_or_is_a_named_deliberate_bump() -> None:
    """28 files today. The count is asserted so an empty scan cannot pass."""
    paths = _tracked_config_json()
    assert len(paths) >= 28, f"only {len(paths)} tracked config JSON(s) found: {paths}"
    checked, disagreeing = 0, []
    for path in paths:
        payload = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
        if "version" not in payload:
            continue
        checked += 1
        if payload["version"] != VERSION and path not in DELIBERATE_BUMPS:
            disagreeing.append((path, payload["version"]))
    assert checked >= 28, f"only {checked} of {len(paths)} config JSONs carry a version key"
    assert not disagreeing, (
        f"config version(s) disagree with shared/version.py {VERSION!r} and are not "
        f"listed as deliberate bumps: {disagreeing}"
    )


def test_the_deliberate_bump_list_names_only_files_that_are_really_bumped() -> None:
    """An exemption for a file that already agrees is a hole waiting to be used."""
    stale = [
        path for path in DELIBERATE_BUMPS
        if json.loads((REPO_ROOT / path).read_text(encoding="utf-8")).get("version") == VERSION
    ]
    assert not stale, f"these files no longer differ and must leave DELIBERATE_BUMPS: {stale}"
