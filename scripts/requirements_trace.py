"""The traceability-table rules for `.planning/REQUIREMENTS.md` (08-02).

THIS FILE EXISTS BECAUSE THE FIRST VERSION OF THE GATE HAD A HOLE, and the probe
that was supposed to prove the gate worked is what found it.

Probe 1 flipped `SUB-05` from `[ ]` to `[x]` and expected a failure. The gate
said **OK**. The reason: an open row legitimately cites the artifact that
explains *why* it is open, and a citation supporting "this is not done" is
indistinguishable, to a path-and-quote check, from one supporting "this is
done". A one-character edit therefore produced a green ledger claiming a Git tag
existed when `git tag -l` is empty.

TWO INDEPENDENT RULES CLOSE IT, and the second is the load-bearing one.

1. `**evidence:**` now means *satisfied* and appears only on ticked rows; an open
   row carries `**status:**` instead. A bare flip loses its citation and fails.
2. EVERY TRACEABILITY ROW DECLARES ITS OWN TICK COUNT -- `**8/8 ticked**` -- and
   this module counts the family and compares. A single flipped row makes the
   declared and actual counts disagree, and no rewording of a marker can hide
   that. It also catches the reverse: quietly UN-ticking earned work.

Rule 2 is the "fix the file as a whole or leave it alone" instruction from
`05-VERIFICATION.md` turned into something a machine can hold.
"""

from __future__ import annotations

import re
from collections import Counter

#: `BASE-01 ... BASE-08` in a row's first cell -> the family prefix `BASE`.
_FAMILY = re.compile(r"\b([A-Z]+)-\d+")
#: The per-row self-declared tally, e.g. `**5/7 ticked; ... held open**`.
_DECLARED = re.compile(r"\*\*(\d+)/(\d+)\s+ticked")


def family_of(cell: str) -> str | None:
    """The requirement family a traceability row answers for."""
    match = _FAMILY.search(cell)
    return match.group(1) if match else None


def tally(ticked: list[str], open_rows: list[str]) -> tuple[Counter, Counter]:
    """(ticked-per-family, total-per-family) from the parsed checkbox rows."""
    ticked_counts = Counter(req_id.split("-")[0] for req_id in ticked)
    totals = Counter(req_id.split("-")[0] for req_id in ticked + open_rows)
    return ticked_counts, totals


def check_declared_counts(cell: str, status: str, ticked: list[str],
                          open_rows: list[str]) -> list[str]:
    """Compare a row's self-declared `N/M ticked` against the real checkboxes.

    A row that declares nothing is a violation in its own right: an undeclared
    row cannot disagree with reality, which is precisely how the previous
    version of this file stayed green for a month while six of seventy-seven
    boxes were ticked.
    """
    family = family_of(cell)
    if family is None:
        return [f"traceability row '{cell.strip()}' names no requirement family"]
    declared = _DECLARED.search(status)
    if not declared:
        return [
            f"traceability row for {family} declares no `**N/M ticked**` count -- "
            f"an undeclared row can never disagree with the checkboxes"
        ]
    ticked_counts, totals = tally(ticked, open_rows)
    want_ticked, want_total = int(declared.group(1)), int(declared.group(2))
    actual_ticked, actual_total = ticked_counts[family], totals[family]
    problems = []
    if want_ticked != actual_ticked:
        problems.append(
            f"{family}: traceability declares {want_ticked} ticked, "
            f"the checkboxes show {actual_ticked}")
    if want_total != actual_total:
        problems.append(
            f"{family}: traceability declares {want_total} requirements, "
            f"the checkboxes show {actual_total}")
    return problems
