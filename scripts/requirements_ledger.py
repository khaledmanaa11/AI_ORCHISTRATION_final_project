"""Parser and rules for `.planning/REQUIREMENTS.md` (08-02).

THE FILE IS A LEDGER, AND A LEDGER ENTRY WITHOUT A CITATION IS A CLAIM. Every
`[x]` must name a **tracked artifact** and a **verbatim quote** from it, and this
module reads the artifact and looks for the quote. A tick can therefore be
flipped on, but it cannot be flipped on and stay green: the row has to point at
text that really exists in a file that really ships.

WHY A QUOTE AND NOT JUST A PATH. Several verification documents -- Phase 4's in
particular -- carry no per-REQ-ID coverage table at all; their evidence lives in
book Sec10.4 criterion rows. A path-only rule would let any Phase-4 requirement
cite `04-VERIFICATION.md` and be believed, including the two that are honestly
still open. Requiring the exact sentence forces each tick to point at the
sentence that earns it.

AN EMPTY LEDGER IS NOT A CLEAN LEDGER. Zero checkboxes, zero traceability rows
or zero resolved citations exit **2**, never 0 -- `submission_report`'s contract
and `gate7_report.GateExit`'s before it.

`Pending` SURVIVES ONLY WHERE AN ARTIFACT SAYS SO. A traceability row reading
the bare word `Pending` for a phase that has an `NN-VERIFICATION.md` on disk is
the exact staleness this plan exists to remove, and it fails by name.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from requirements_rows import check_citations, check_open  # noqa: E402
from requirements_trace import check_declared_counts  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / ".planning" / "REQUIREMENTS.md"
PHASES = REPO_ROOT / ".planning" / "phases"

_ROW = re.compile(r"^- \[([ x])\] \*\*([A-Z]+-\d+)\*\*:(.*)$")
#: Tolerates markdown emphasis around the number -- `**77 total**` is the same
#: claim as `77 total`, and a gate that missed the bold one would report "no
#: total declared" for a file that declares one.
_HEADER_TOTAL = re.compile(r"v1 requirements:\s*\**\s*(\d+)\s*total")
_TRACE = re.compile(r"^\|\s*([A-Z]+-\d+[^|]*)\|([^|]*)\|(.*)\|\s*$")
_PHASE_NUM = re.compile(r"Phase\s+(\d)")
_BACKTICKED = re.compile(r"`([^`]+)`")


@dataclass
class Ledger:
    """Everything parsed out of the file, plus every rule violation found."""

    ticked: list[str] = field(default_factory=list)
    open_rows: list[str] = field(default_factory=list)
    citations_resolved: int = 0
    trace_rows: int = 0
    declared_total: int | None = None
    violations: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.ticked) + len(self.open_rows)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _verification_for(phase_number: str) -> Path | None:
    hits = sorted(PHASES.glob(f"0{phase_number}-*/0{phase_number}-VERIFICATION.md"))
    return hits[0] if hits else None


def _check_trace_row(status: str, phase_cell: str, ledger: Ledger) -> None:
    ledger.trace_rows += 1
    stripped = status.strip()
    if not stripped:
        ledger.violations.append(f"traceability row '{phase_cell.strip()}' has no status")
        return
    for cited in _BACKTICKED.findall(stripped):
        if "/" in cited and not (REPO_ROOT / cited).exists():
            ledger.violations.append(
                f"traceability row '{phase_cell.strip()}' cites a missing artifact: {cited}")
    number = _PHASE_NUM.search(phase_cell)
    if stripped == "Pending" and number and _verification_for(number.group(1)):
        ledger.violations.append(
            f"traceability row '{phase_cell.strip()}' still reads bare `Pending` while "
            f"{_verification_for(number.group(1)).name} exists on disk")


def parse(text: str) -> Ledger:
    """Parse the ledger and apply every rule to it.

    Traceability rows are collected during the pass and judged AFTER it: their
    self-declared `**N/M ticked**` counts are compared against the real
    checkboxes, which are not all known until the last line is read.
    """
    ledger = Ledger()
    trace_rows: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        row = _ROW.match(line)
        if row:
            mark, req_id, body = row.groups()
            if mark == "x":
                ledger.ticked.append(req_id)
                problems, resolved = check_citations(req_id, body)
                ledger.violations.extend(problems)
                ledger.citations_resolved += resolved
            else:
                ledger.open_rows.append(req_id)
                ledger.violations.extend(check_open(req_id, body))
            continue
        header = _HEADER_TOTAL.search(line)
        if header:
            ledger.declared_total = int(header.group(1))
            continue
        trace = _TRACE.match(line)
        if trace and "---" not in line and "Requirements" not in trace.group(1):
            trace_rows.append((trace.group(1), trace.group(2), trace.group(3)))
    for req_cell, phase_cell, status in trace_rows:
        _check_trace_row(status, phase_cell, ledger)
        ledger.violations.extend(
            check_declared_counts(req_cell, status, ledger.ticked, ledger.open_rows))
    if ledger.declared_total is None:
        ledger.violations.append("the ledger declares no `v1 requirements: N total`")
    elif ledger.declared_total != ledger.total:
        ledger.violations.append(
            f"declared total {ledger.declared_total} != {ledger.total} actual checkboxes")
    return ledger


def emptiness(ledger: Ledger) -> list[str]:
    """Every way this run judged nothing, named. Empty list means it judged."""
    reasons = []
    if not ledger.total:
        reasons.append("no requirement checkboxes were parsed at all")
    if not ledger.trace_rows:
        reasons.append("no traceability rows were parsed")
    if not ledger.citations_resolved:
        reasons.append("no citation resolved to a real quote in a real artifact")
    return reasons
