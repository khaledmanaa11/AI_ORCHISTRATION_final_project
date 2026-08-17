"""What `docs/PARAMETERS.md` says a parameter's status is, and the two
refusals that keep the sweep legal (08-09).

THE GRID IS NOT ALLOWED TO DECIDE WHAT IT MAY VARY. CLAUDE.md's first
disqualification is inventing a numeric value, and the 08 outline names the
matching research failure by name: "varying a FIXED parameter to produce a
more interesting graph is a rule-1 / rule-12 violation dressed as research".
So the status of every knob is PARSED OUT OF THE EXTRACT here and the grid
declares what it believes -- `refuse_fixed` fails when the two disagree,
which means a knob cannot silently acquire permission it does not have.

`refuse_downward` is the second half and it is not decoration. A `minimum`
parameter "may be negotiated upward, never downward"; a sweep that put
`board_size = 5` beside 7 and 9 would produce a perfectly readable curve out
of a value the rules forbid. The baseline is read from the shipped config,
so the refusal is measured against what this repository actually plays.

Nothing here reads the book. The extract is the binding document per
CLAUDE.md, and if it is ever found to disagree with Appendix F the fix lands
in `docs/PARAMETERS.md` and this module follows for free.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PARAMETERS_DOC = REPO_ROOT / "docs" / "PARAMETERS.md"

FIXED = "fixed"
MINIMUM = "minimum"
NEGOTIABLE = "negotiable"
#: Not an Appendix F row at all -- a value this project chose and labelled.
#: `refuse_fixed` skips the extract lookup for these and demands a citation
#: instead (`Knob.source`), because a made-up status is the same defect as a
#: made-up number.
ENGINEERING = "engineering default"

#: One Appendix F table row: `| 1 | `[board size]` | ... | **7x7** | minimum |`.
#: The status cell is the last one and may or may not be bolded.
_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*`\[([^\]]+)\]`\s*\|.*\|\s*"
    r"\*{0,2}(fixed|minimum|negotiable)\*{0,2}\s*\|\s*$",
    re.MULTILINE,
)


@lru_cache(maxsize=1)
def parameter_status() -> dict:
    """Every `[bracketed]` Appendix F parameter mapped to its status.

    Raises when the parse finds nothing: an empty mapping would make
    `refuse_fixed` vacuously permissive, which is the failure mode this
    repository has now caught in three separate gates.
    """
    text = PARAMETERS_DOC.read_text(encoding="utf-8")
    rows = dict(_ROW.findall(text))
    if not rows:
        raise ValueError(
            f"parsed 0 parameter rows out of {PARAMETERS_DOC} -- refusing to "
            "report every knob as permitted over an empty extract"
        )
    return rows


def fixed_parameters() -> tuple:
    """The labels no sweep may vary, in document order."""
    return tuple(label for label, status in parameter_status().items() if status == FIXED)


def refuse_fixed(knobs) -> None:
    """Fail unless every knob's declared status matches the extract.

    Three distinct refusals, because they are three distinct mistakes: a
    label the extract does not carry (typo, or a parameter that does not
    exist), a label the extract marks `fixed`, and a label whose real status
    differs from the one the grid claims.
    """
    statuses = parameter_status()
    for knob in knobs:
        if knob.status == ENGINEERING:
            if not knob.source:
                raise ValueError(f"{knob.name}: an engineering default must cite its source")
            continue
        if not knob.labels:
            raise ValueError(f"{knob.name}: an Appendix F knob must name the row it varies")
        for label in knob.labels:
            _check_label(knob, label, statuses)


def _check_label(knob, label: str, statuses: dict) -> None:
    """One knob, one Appendix F row: exists, is not fixed, and agrees."""
    actual = statuses.get(label)
    if actual is None:
        raise KeyError(f"{knob.name}: docs/PARAMETERS.md has no row `[{label}]`")
    if actual == FIXED:
        raise ValueError(
            f"{knob.name}: `[{label}]` is FIXED in docs/PARAMETERS.md. "
            "Varying it is a rule-1 deviation, not an experiment."
        )
    if actual != knob.status:
        raise ValueError(
            f"{knob.name}: grid declares `{knob.status}`, "
            f"docs/PARAMETERS.md says `{actual}` for `[{label}]`"
        )


def refuse_downward(knobs, baseline) -> None:
    """Fail when a `minimum` knob is swept below the value the repo ships.

    Only `minimum` rows are checked: `negotiable` rows may take any agreed
    value, and an engineering default is ours to move in either direction.
    """
    for knob in knobs:
        if knob.status != MINIMUM:
            continue
        floor = knob.read(baseline)
        below = [value for value in knob.values if _scalar(value) < _scalar(floor)]
        if below:
            raise ValueError(
                f"{knob.name}: {list(knob.labels)} is a MINIMUM at {floor}; "
                f"{below} would negotiate it DOWNWARD, which the rules forbid"
            )


def _scalar(value) -> float:
    """Compare tuples by their first element -- the joint horizon knob."""
    return float(value[0]) if isinstance(value, tuple) else float(value)
