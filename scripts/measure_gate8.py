#!/usr/bin/env python
"""GATE-8 measurement CLI (08-11): the submission gate, measured as far as it
can honestly go before a human acts.

    uv run python scripts/measure_gate8.py
    uv run python scripts/measure_gate8.py --dest C:/Users/Hp/pursuit-split-repos

EXIT 0 DOES NOT MEAN GATE-8 IS MET. All three Sec-submission criteria are
structurally human-completed -- publishing two repositories, filling and
submitting a form PDF, and playing scored games against real opponents. This
command measures the halves that exist on this machine and reports the other
halves as PENDING; `docs/phases/phase-8/GATE-8-MEASUREMENT.md` is the record
that carries them, and it does not read PASS.

THIS COMMAND ISSUES NO REMOTE COMMAND. Every git call it makes is a local read,
and it verifies that claim about its own source before reporting it -- see
`gate8_common.network_verb_hits`. It does not create the tag either: 08-11 cuts
that in each output by hand, and this gate only measures what is there.

Idempotent: reads only, one output JSON, overwritten in place. Two fields move
between runs and both are named -- `generated_at`, and the counter snapshot,
which is recorded before and after precisely so a run that moved a rule-38
counter cannot hide it.
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
    _scripts = str(Path(__file__).resolve().parent)
    if _scripts not in sys.path:
        sys.path.insert(0, _scripts)

from gate7_common import counter_snapshot  # noqa: E402
from gate8_common import DEFAULT_SPLIT_DEST, network_verb_hits  # noqa: E402
from gate8_report import build_report, exit_code  # noqa: E402
from gate8_repos import measure as measure_repos  # noqa: E402
from gate8_submission import measure_criterion_2, measure_criterion_3  # noqa: E402

_OUT_PATH = Path("docs/phases/phase-8/gate8_measurement_evidence.json")

_CRITERIA = (
    "criterion_1_two_cross_linked_repos_and_a_tag",
    "criterion_2_academic_readme_and_submission_form",
    "criterion_3_two_scored_league_games",
)


def _measure_all(dest: Path) -> dict:
    before = counter_snapshot()
    criterion_1 = measure_repos(dest)
    criterion_2 = measure_criterion_2(dest)
    criterion_3 = measure_criterion_3()
    after = counter_snapshot()
    counters = {
        "before": before, "after": after, "unchanged_by_this_measurement": before == after,
    }
    return build_report(criterion_1, criterion_2, criterion_3, counters, network_verb_hits())


def _print_summary(report: dict) -> None:
    print("GATE-8 measurement -- local reads only, zero remote commands")
    for key in _CRITERIA:
        print(f"  {key}:\n      {report[key]['verdict']}")
    counters = report["games_played_counter"]
    print(f"  games_played unchanged by this run: "
          f"{counters['unchanged_by_this_measurement']}")
    print(f"  network verb hits in this package: "
          f"{report['no_remote_command_was_issued']['network_verb_hits_in_this_package']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GATE-8 submission-gate measurement")
    parser.add_argument("--dest", type=Path, default=DEFAULT_SPLIT_DEST,
                        help="where the two split outputs were built (08-10)")
    parser.add_argument("--json", type=Path, default=_OUT_PATH,
                        help="where to write the evidence JSON")
    args = parser.parse_args(argv)

    report = _measure_all(args.dest)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _print_summary(report)
    print(f"Wrote {args.json}")
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
