#!/usr/bin/env python
"""Gate for `.planning/REQUIREMENTS.md` -- a tick must cite what proves it (08-02).

    uv run python scripts/check_requirements_ledger.py
    uv run python scripts/check_requirements_ledger.py --file <path>   # probe a copy

Exit **0** when every rule holds, **1** on any violation, **2** when the ledger
judged nothing -- no checkboxes, no traceability rows, or no citation that
resolved to real text in a real file.

WHY THIS EXISTS. Before this plan the file read 6 ticks out of 77, a header
claiming 74, and ten traceability rows saying `Pending` against five phases with
`NN-VERIFICATION.md` on disk. Reconciling it once fixes today; a gate keeps it
fixed, because the next person to tick a row has to name the sentence that earns
it and this refuses a tick that does not.

THE TWO PROBES THIS GATE MUST SURVIVE, both recorded in `08-02-SUMMARY.md`:
flip one row to `[x]` without a citation and it must FAIL, and run it over an
EMPTY ledger and it must exit 2 rather than print OK.

Local reads only -- this opens files and touches no remote.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from requirements_ledger import LEDGER, emptiness, parse  # noqa: E402

OK, VIOLATIONS_FOUND, EMPTY_LEDGER = 0, 1, 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Requirements ledger gate")
    parser.add_argument("--file", type=Path, default=LEDGER,
                        help="ledger to check (default: .planning/REQUIREMENTS.md)")
    args = parser.parse_args(argv)

    if not args.file.is_file():
        print(f"EMPTY LEDGER: {args.file} does not exist")
        return EMPTY_LEDGER

    ledger = parse(args.file.read_text(encoding="utf-8", errors="replace"))
    empty = emptiness(ledger)

    print(f"Requirements ledger: {args.file}")
    print(f"  checkboxes: {ledger.total} ({len(ledger.ticked)} ticked, "
          f"{len(ledger.open_rows)} open); declared total: {ledger.declared_total}")
    print(f"  traceability rows: {ledger.trace_rows}; "
          f"citations resolved to real quotes: {ledger.citations_resolved}")

    if empty:
        for reason in empty:
            print(f"EMPTY LEDGER: {reason}")
        print(f"\nVERDICT: EMPTY_LEDGER (exit {EMPTY_LEDGER})")
        return EMPTY_LEDGER

    if ledger.violations:
        print(f"\nVIOLATIONS ({len(ledger.violations)}):")
        for violation in ledger.violations:
            print(f"  - {violation}")
        print(f"\nVERDICT: VIOLATIONS_FOUND (exit {VIOLATIONS_FOUND})")
        return VIOLATIONS_FOUND

    print(f"\nVERDICT: OK (exit {OK})")
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
