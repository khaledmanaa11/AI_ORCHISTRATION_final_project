"""Per-row rules for `.planning/REQUIREMENTS.md` (08-02).

Split out of `requirements_ledger.py` when that file reached 149 of its 150
permitted code lines -- SPLIT, never compressed (Segal Sec3), and done at 149
rather than at 151 because a file sitting one line from the gate is a trap for
whoever edits it next. The phase-5 record already carries one of those
(`turn_buffer.py` at 146/150).

The seam is honest: everything here judges ONE ROW in isolation, everything left
behind parses the DOCUMENT and needs the whole checkbox set to do its job.

TWO RULES, AND THE SECOND IS THE ONE A PROBE EARNED.

* A ticked row cites `path` "verbatim quote", and the quote is looked for in the
  file. A tick can be flipped on; it cannot be flipped on and point at text that
  does not exist.
* An open row carries `**open:**` and must NOT carry `**evidence:**`. That
  marker means *satisfied*. Before this rule existed, an open row citing the
  artifact that explained why it was open stayed green when one character
  flipped it to ticked -- probe 1 of this plan found exactly that.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
#: Shortest string that can count as a stated reason for an open row.
MIN_OPEN_REASON = 10

CITATION = re.compile(r"`([^`]+\.(?:md|json))`\s+\"([^\"]+)\"")
OPEN = re.compile(r"\*\*open:\*\*\s*(.+?)(?:\s+--\s+\*\*evidence|$)")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def check_citations(req_id: str, body: str) -> tuple[list[str], int]:
    """(violations, citations that resolved) for one ticked row."""
    pairs = CITATION.findall(body)
    if not pairs:
        return [f"{req_id} is ticked with no `path` \"quote\" citation"], 0
    violations, resolved = [], 0
    for raw_path, quote in pairs:
        target = REPO_ROOT / raw_path
        if not target.is_file():
            violations.append(f"{req_id} cites a missing artifact: {raw_path}")
            continue
        if quote not in _read(target):
            violations.append(
                f"{req_id} quotes {raw_path} with text that is not in it: {quote!r}")
            continue
        resolved += 1
    return violations, resolved


def check_open(req_id: str, body: str) -> list[str]:
    """Violations for one unticked row."""
    violations = []
    match = OPEN.search(body)
    if not match or len(match.group(1).strip()) < MIN_OPEN_REASON:
        violations.append(
            f"{req_id} is unticked and names nothing outstanding "
            f"(needs `**open:** <what and where>`)")
    if "**evidence:**" in body:
        violations.append(
            f"{req_id} is unticked but carries `**evidence:**`, which means satisfied "
            f"-- an open row cites its artifact with `**status:**`")
    return violations
