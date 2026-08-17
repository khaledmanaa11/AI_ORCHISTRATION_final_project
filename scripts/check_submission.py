#!/usr/bin/env python
"""The Segal Sec17 + Sec19.1 Table-5 submission audit, as a gate that can fail.

    uv run python scripts/check_submission.py              # fast: no test suite
    uv run python scripts/check_submission.py --run-suite   # also runs pytest --cov
    uv run python scripts/check_submission.py --json out.json

Exit 0 when every judged row passes, 1 when any row is a GAP, 2 when the
evidence set judged NOTHING. `docs/SUBMISSION-CHECKLIST.md` is the human-readable
register this produces the numbers for.

WHY A SCRIPT AND NOT A CHECKLIST. A prose checklist cannot fail, cannot be run
again after a fix, and cannot notice a regression. This one re-derives every row
from the tree on each run, so a gap closed in wave 2 goes green by itself and a
gap re-opened by a later edit comes back.

`--empty-probe` EXISTS TO PROVE THE EXIT-2 STATE IS REAL. It suppresses every
row and must exit 2, never 0. A gate whose empty state has never been observed
is a gate whose empty state might be a pass.

NOTHING HERE TOUCHES A REMOTE. The two git calls are `ls-files`/`log`/`tag -l`/
`check-ignore`, all local reads. This gate never pushes, never fetches, never
creates a tag -- 08-11 cuts the tag and a HUMAN pushes it in 08-12.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from submission_code import code_items  # noqa: E402
from submission_docs import doc_items  # noqa: E402
from submission_mechanisms import mechanism_items  # noqa: E402
from submission_readme import readme_items  # noqa: E402
from submission_report import build_report, exit_code, print_summary  # noqa: E402
from submission_research import research_items  # noqa: E402
from submission_security import security_items  # noqa: E402
from submission_table5 import table5_items  # noqa: E402
from submission_testing import testing_items  # noqa: E402


def collect(run_suite: bool, empty_probe: bool) -> tuple[list, int, int]:
    """Every row, plus the two counts the emptiness contract is checked against."""
    if empty_probe:
        return [], 0, 0
    readme = readme_items()
    mechanisms, mechanism_count = mechanism_items()
    sections = [
        *readme, *mechanisms, *doc_items(), *code_items(),
        *testing_items(run_suite), *security_items(), *research_items(),
    ]
    return sections + table5_items(sections), mechanism_count, len(readme)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Segal Sec17 + Table-5 submission audit")
    parser.add_argument("--run-suite", action="store_true",
                        help="also run `uv run pytest --cov` and judge T5-10 on it")
    parser.add_argument("--json", type=Path, default=None,
                        help="write the full evidence JSON to this path")
    parser.add_argument("--empty-probe", action="store_true",
                        help="suppress every row; proves the exit-2 state is reachable")
    args = parser.parse_args(argv)

    items, mechanism_count, readme_count = collect(args.run_suite, args.empty_probe)
    report = build_report(items, mechanism_count, readme_count, args.run_suite)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
        print(f"Wrote {args.json}")

    print_summary(report, items)
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
