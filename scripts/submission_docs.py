"""Sec17 group 1's remaining rows: the docs triplet, rendered diagrams, the
prompt log, and the extracts' own internal consistency (08-01).

A RENDERED DIAGRAM IS NOT A GREP HIT. `grep -rl '```mermaid' docs/` currently
matches `docs/phases/phase-8/TODO.md`, which contains that string only because a
TODO cell QUOTES the command inside a table row. A gate built on that grep would
report diagrams where there are none. A block counts here only when its opening
fence is the whole line, which is the shape GitHub actually renders.

THE EXTRACT-CONSISTENCY ROW is here because `docs/RULES.md` and
`docs/PARAMETERS.md` are both grader-facing and both derived from the same book.
Where they disagree about a FIXED value, one of them is wrong in front of the
grader. This row compares rule 48's survival pair against Table 17 rows 3-4 and
is derived from both files -- no number is written down here.
"""

from __future__ import annotations

import re

from submission_common import (
    GROUP_1,
    judge,
    read_tracked,
    tracked_matching,
)

TRIPLET = ("docs/PRD.md", "docs/PLAN.md", "docs/TODO.md")
PROMPT_LOG = "docs/PROMPT_LOG.md"
#: A mandated document shorter than this is a stub, not a document.
MIN_DOC_LINES = 20

_FENCE = re.compile(r"^\s*```mermaid\s*$")
#: Table 17 rows 3-4: `[survival score - cop]` and `[survival score - thief]`.
_PARAM_ROW = re.compile(r"\|\s*`?\[survival score\s*[-–]\s*(cop|thief)\]`?\s*\|[^|]*\|\s*\**(\d+)\**\s*\|")
_RULE_48 = re.compile(r"survival\s+(\d+)\s*/\s*(\d+)")


def _triplet_rows() -> list:
    rows = []
    for index, path in enumerate(TRIPLET, start=10):
        text = read_tracked(path)
        lines = [line for line in text.splitlines() if line.strip()]
        rows.append(judge(
            f"G1-{index}", GROUP_1, f"Sec2.2 mandatory document `{path}`",
            len(lines) >= MIN_DOC_LINES,
            f"tracked: {bool(text)}; non-blank lines: {len(lines)} "
            f"(stub floor {MIN_DOC_LINES})",
            path,
        ))
    return rows


def mermaid_blocks() -> dict[str, int]:
    """Tracked docs mapped to their count of RENDERED mermaid blocks."""
    counts: dict[str, int] = {}
    for path in tracked_matching(prefix="docs/", suffix=".md"):
        hits = sum(1 for line in read_tracked(path).splitlines() if _FENCE.match(line))
        if hits:
            counts[path] = hits
    return counts


def _diagram_row() -> object:
    blocks = mermaid_blocks()
    total = sum(blocks.values())
    return judge(
        "G1-13", GROUP_1,
        "Sec17 architecture documentation with clear (rendered) diagrams",
        total > 0,
        f"rendered mermaid blocks across tracked docs/: {total} "
        f"in {len(blocks)} file(s) {sorted(blocks)}",
        "docs/ARCHITECTURE.md",
    )


def _prompt_log_row() -> object:
    text = read_tracked(PROMPT_LOG)
    lines = [line for line in text.splitlines() if line.strip()]
    return judge(
        "G1-14", GROUP_1, "Sec8.3 / Sec17 documented prompt-engineering log",
        len(lines) >= MIN_DOC_LINES,
        f"tracked: {bool(text)}; non-blank lines: {len(lines)}",
        PROMPT_LOG,
    )


def _survival_pair() -> tuple[int, int] | None:
    """(cop, thief) survival scores, read out of PARAMETERS Table 17."""
    found = {
        role: int(value)
        for role, value in _PARAM_ROW.findall(read_tracked("docs/PARAMETERS.md"))
    }
    if {"cop", "thief"} <= set(found):
        return found["cop"], found["thief"]
    return None


def _extract_consistency_row() -> object:
    """Rule 48's survival pair in RULES.md vs Table 17's fixed values.

    Rule 48 writes its CAPTURE pair cop-first ("capture 20/5"), so its survival
    pair must be cop-first too. Both numbers come out of PARAMETERS; nothing is
    asserted here, which is why correcting the extract stays a separate decision.
    """
    table = _survival_pair()
    rules = read_tracked("docs/RULES.md")
    written = _RULE_48.search(rules)
    if table is None or written is None:
        return judge("G1-15", GROUP_1,
                     "Sec17 grader-facing extracts agree on the fixed scoring values",
                     False,
                     f"could not read the pair -- PARAMETERS Table 17: {table}; "
                     f"RULES rule 48 match: {bool(written)}",
                     "docs/RULES.md")
    stated = (int(written.group(1)), int(written.group(2)))
    return judge(
        "G1-15", GROUP_1,
        "Sec17 grader-facing extracts agree on the fixed scoring values (rule 48 vs Table 17)",
        stated == table,
        f"PARAMETERS Table 17 rows 3-4 (cop, thief) = {table}; "
        f"RULES.md rule 48 writes survival {stated[0]}/{stated[1]}",
        "docs/RULES.md",
    )


def doc_items() -> list:
    """Group 1's non-README, non-mechanism rows."""
    return [
        *_triplet_rows(),
        _diagram_row(),
        _prompt_log_row(),
        _extract_consistency_row(),
    ]
