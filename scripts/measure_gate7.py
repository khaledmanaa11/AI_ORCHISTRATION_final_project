#!/usr/bin/env python
"""GATE-7 measurement CLI (07-09): one command, zero credentials, the three
Sec10.4 milestone-7 criteria measured as far as they can honestly go.

    uv run python scripts/measure_gate7.py

CRITERION 1 IS REPORTED AS TWO FIELDS AND NEVER AS ONE. Everything up to the
send is measured here; the one live send needs a human at Google's consent
screen and is 07-10's (`docs/phases/phase-7/OAUTH-RUNBOOK.md`). A gate document
that read PASS without a delivered message is the failure mode rule 38 exists
for, and `docs/phases/phase-5/GATE-5-MEASUREMENT.md`'s retained PENDING record
is this project's own precedent for writing it honestly.

NO `gui` IMPORT AT MODULE SCOPE, ANYWHERE IN THESE SCRIPTS. `tkinter.Tk()`
raises on a machine with no display, and one criterion's environment must not
be able to fail the whole gate. Both GUI entry points are driven as
SUBPROCESSES and their exit codes recorded.

Idempotent: one fixed `game_uid` inside a throwaway temp directory (never the
real `logs/` tree), and only the one output JSON below is written, overwritten
in place. The printed summary is byte-identical across runs.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from gate7_common import counter_snapshot, play_recorded_game  # noqa: E402
from gate7_localtruth import measure_local_truth  # noqa: E402
from gate7_mail import measure_mail  # noqa: E402
from gate7_replay import measure_replay  # noqa: E402
from gate7_report import build_report, exit_code  # noqa: E402

_OUT_PATH = Path("docs/phases/phase-7/gate7_measurement_evidence.json")

_CRITERIA = (
    "criterion_1_game_summary_sent_by_mail",
    "criterion_2_live_gui_local_truth_only",
    "criterion_3_replay_shows_verified_ok",
)


async def _measure_all() -> dict:
    before = counter_snapshot()
    criterion_1 = await measure_mail()
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        game = await play_recorded_game(workdir / "logs")
        criterion_2 = measure_local_truth(game, workdir / "scan")
        criterion_3 = measure_replay(game, workdir)
    after = counter_snapshot()
    counters = {
        "before": before, "after": after, "unchanged_by_this_measurement": before == after,
    }
    return build_report(criterion_1, criterion_2, criterion_3, counters)


def _print_summary(report: dict) -> None:
    print("GATE-7 measurement -- localhost, zero credentials, zero env vars")
    for key in _CRITERIA:
        print(f"  {key}: {report[key]['verdict']}")
    counters = report["games_played_counter"]
    print(f"  games_played unchanged by this run: {counters['unchanged_by_this_measurement']}")


def main() -> int:
    report = asyncio.run(_measure_all())

    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _print_summary(report)
    print(f"Wrote {_OUT_PATH}")
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
