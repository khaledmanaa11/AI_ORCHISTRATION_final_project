"""Sec17 packaging metadata, and the licence flag that must not go quiet (08-03).

THE LICENCE HALF IS THE POINT OF THIS FILE. `LICENSE` was drafted by an agent, and
choosing a licence is a legal declaration about the repository owner's own
coursework -- so the file carries a block saying it is PREPARED AND NOT ADOPTED,
and `docs/SUBMISSION-CHECKLIST.md` registers it as awaiting the owner's explicit
confirmation before 08-12 publishes anything.

Those two statements have to move together or the flag is worthless: a LICENSE
whose caveat is deleted while the register still says "pending" understates what
happened, and a register quietly ticked while the caveat remains overstates it.
The assertion below is therefore a BICONDITIONAL over the two files, not a
presence check on either -- and both branches are named, so it cannot pass by
finding neither.

IT READS ONE ANCHORED FIELD, NOT THE PAGE. The first draft grepped the register
for each marker and failed against the register's own PROSE, which necessarily
quotes both markers while explaining them. A document that describes a state is
not in that state; only the `**LICENCE STATUS:**` line is.

THE SECTION PARSER IS DELIBERATELY HAND-ROLLED. `tomllib` is 3.11+, and
`requires-python` here is `>=3.10`, so a CI runner resolving 3.10 would turn this
test into a collection error rather than a check.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
LICENSE = REPO_ROOT / "LICENSE"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
CHECKLIST = REPO_ROOT / "docs" / "SUBMISSION-CHECKLIST.md"
#: Sec17 / Sec14 metadata a published package is expected to declare.
REQUIRED_PROJECT_KEYS = ("name", "version", "description", "license", "authors")
#: The block `LICENSE` carries until the owner confirms the choice.
NOT_ADOPTED_MARKER = "PREPARED, NOT ADOPTED"
#: The register's single status field, and its two legal values.
_STATUS_FIELD = re.compile(r"^\*\*LICENCE STATUS:\*\*\s*(\S+)\s*$", re.MULTILINE)
PENDING_STATUS = "AWAITING_OWNER_CONFIRMATION"
CONFIRMED_STATUS = "CONFIRMED_BY_THE_OWNER"
#: A licence shorter than this is a stub, not a licence.
MIN_LICENSE_LINES = 15


def project_section() -> str:
    """The `[project]` table's own lines, and nothing from any other table."""
    lines = PYPROJECT.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("[project]") + 1
    except ValueError:
        return ""
    body = []
    for line in lines[start:]:
        if line.startswith("["):
            break
        body.append(line)
    return "\n".join(body)


def declared_keys() -> set[str]:
    return {
        line.split("=")[0].strip()
        for line in project_section().splitlines()
        if "=" in line and not line.strip().startswith("#")
    }


def test_the_section_parser_stops_at_the_next_table() -> None:
    """Control: a parser that read the whole file would find `line-length` too."""
    keys = declared_keys()
    assert keys, "the [project] table parsed to nothing"
    assert "line-length" not in keys, "the parser leaked into [tool.ruff]"
    assert "select" not in keys, "the parser leaked into [tool.ruff.lint]"


def test_pyproject_declares_the_required_metadata() -> None:
    missing = [key for key in REQUIRED_PROJECT_KEYS if key not in declared_keys()]
    assert not missing, f"pyproject.toml [project] declares no {missing}"


def test_the_licence_file_is_a_licence_and_not_a_stub() -> None:
    assert LICENSE.is_file(), "LICENSE is missing"
    lines = [line for line in LICENSE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= MIN_LICENSE_LINES, f"LICENSE has {len(lines)} non-blank lines"


def test_contributing_guidelines_exist() -> None:
    assert CONTRIBUTING.is_file(), "CONTRIBUTING.md is missing"
    assert len(CONTRIBUTING.read_text(encoding="utf-8").splitlines()) >= MIN_LICENSE_LINES


def licence_status() -> str | None:
    """The register's `**LICENCE STATUS:**` value, or None when the field is gone."""
    match = _STATUS_FIELD.search(CHECKLIST.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def test_the_register_carries_a_readable_licence_status() -> None:
    """Anti-vacuity: a missing field would make the branch below unreachable."""
    status = licence_status()
    assert status in (PENDING_STATUS, CONFIRMED_STATUS), (
        f"docs/SUBMISSION-CHECKLIST.md's LICENCE STATUS field reads {status!r}; "
        f"it must be one of {(PENDING_STATUS, CONFIRMED_STATUS)}"
    )


def test_the_licence_flag_and_the_register_say_the_same_thing() -> None:
    """The biconditional. Neither file may change its story without the other."""
    drafted = NOT_ADOPTED_MARKER in LICENSE.read_text(encoding="utf-8")
    expected = PENDING_STATUS if drafted else CONFIRMED_STATUS
    assert licence_status() == expected, (
        f"LICENSE {'still carries' if drafted else 'no longer carries'} its "
        f"{NOT_ADOPTED_MARKER!r} block, so the register's LICENCE STATUS must read "
        f"{expected!r} -- it reads {licence_status()!r}. An unconfirmed licence "
        f"must never reach a public repository unflagged."
    )
