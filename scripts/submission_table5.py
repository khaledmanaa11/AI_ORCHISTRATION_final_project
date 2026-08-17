"""Table 5 (Sec19.1) -- the hard summary -- reported WITHOUT re-measuring
anything (08-01).

Every Table-5 row is already answered by a Sec17 row somewhere above it, so this
section CITES those rows and takes the worst verdict among them. Measuring the
same thing twice would risk two answers to one question, and Table 5's own
`Enforced by` column is the reason the rows differ in kind: three of them say
`Code review` or `Work process`, and those stay UNJUDGED here exactly as they do
in their Sec17 rows.

A CITED ROW THAT DOES NOT EXIST IS A GAP, NOT A SHRUG. If a Sec17 id named below
is never produced -- a judge removed, a row renamed -- the aggregation would
otherwise fold an empty list into a pass. `_worst` refuses an empty backing set
by name, which is the same emptiness refusal the exit contract makes at the top
level.

ONE ROW IS MEASURED HERE AND NOWHERE ELSE: "Version control starts at 1.00".
`src/pursuit/shared/version.py` and `pyproject.toml` must agree, and today they
are written differently (`1.00` vs `1.00.0`) -- which is 08-11's problem, since
the tag name is derived from the reconciled value.
"""

from __future__ import annotations

import re

from submission_common import (
    GAP,
    GROUP_T5,
    PASS,
    UNJUDGED,
    Item,
    judge,
    read_tracked,
)

VERSION_MODULE = "src/pursuit/shared/version.py"
PYPROJECT = "pyproject.toml"
#: Table 5's baseline version string (Sec8, "Versioning starts at 1.00").
BASELINE_VERSION = "1.00"

#: (row id, Table-5 rule text, the Sec17 item ids that answer it).
ROWS = (
    ("T5-01", "SDK architecture -- all logic through the SDK layer", ("G2-01",)),
    ("T5-02", "OOP / no duplication -- extract at 2+ copies", ("G2-08",)),
    ("T5-03", "API gatekeeper -- every external call goes through it", ("G2-02",)),
    ("T5-04", "Rate limits in configuration, never in source", ("G2-02",)),
    ("T5-05", "Overflow handling -- queue, never crash", ("G3-05",)),
    ("T5-07", "TDD -- red -> green -> refactor", ("G3-06",)),
    ("T5-08", "File size <= 150 code lines", ("G2-03",)),
    ("T5-09", "Linter -- 0 Ruff violations", ("G2-04",)),
    ("T5-10", "Test coverage >= 85%", ("G3-01", "G3-05")),
    ("T5-11", "Hardcoded values -- 0 in source", ("G2-10",)),
    ("T5-12", "Secrets -- `.env-example` + 0 in source", ("G4-01", "G4-02")),
    ("T5-13", "Package manager -- everything through `uv`", ("G4-20",)),
)


def _worst(cited: tuple[str, ...], by_id: dict[str, Item]) -> tuple[str, str]:
    """The worst verdict among the cited rows, and the evidence naming them."""
    missing = [item_id for item_id in cited if item_id not in by_id]
    if missing or not cited:
        return GAP, f"cited Sec17 row(s) not produced by this run: {missing or list(cited)}"
    verdicts = {item_id: by_id[item_id].verdict for item_id in cited}
    detail = "; ".join(f"{key}={value}" for key, value in verdicts.items())
    if GAP in verdicts.values():
        return GAP, f"from {detail}"
    if UNJUDGED in verdicts.values():
        return UNJUDGED, f"from {detail}"
    return PASS, f"from {detail}"


def _version_row() -> Item:
    module = read_tracked(VERSION_MODULE)
    declared = re.search(r'VERSION\s*=\s*"([^"]+)"', module)
    project = re.search(r'^version\s*=\s*"([^"]+)"', read_tracked(PYPROJECT), re.MULTILINE)
    module_value = declared.group(1) if declared else "<absent>"
    project_value = project.group(1) if project else "<absent>"
    return judge(
        "T5-06", GROUP_T5, "Version control -- starts at 1.00 and the two sources agree",
        module_value == BASELINE_VERSION and project_value == module_value,
        f"{VERSION_MODULE} VERSION = {module_value!r}; {PYPROJECT} version = "
        f"{project_value!r}; Table 5 baseline {BASELINE_VERSION!r}",
        PYPROJECT,
    )


def _fix_path(cited: tuple[str, ...], by_id: dict[str, Item]) -> str:
    """Where the cited row says its own repair lands -- never re-invented here."""
    return next(
        (by_id[item_id].fix_path for item_id in cited
         if item_id in by_id and by_id[item_id].verdict == GAP and by_id[item_id].fix_path),
        "",
    )


def table5_items(section_items: list) -> list:
    """Table 5's thirteen rows, twelve of them cited from the Sec17 measurements."""
    by_id = {item.item_id: item for item in section_items}
    rows = [
        Item(row_id, GROUP_T5, requirement, *_worst(cited, by_id), _fix_path(cited, by_id))
        for row_id, requirement, cited in ROWS
    ]
    rows.append(_version_row())
    return sorted(rows, key=lambda item: item.item_id)
