#!/usr/bin/env python
"""GATE-6 measurement CLI (06-04): one command, zero env vars, the full
commit-reveal lifecycle (D-58 four phases, D-67 tamper harness, D-62
Step-0 mismatch) measured end to end against the REAL shipped
config/police + config/thief -- exactly like 06-02/06-03's own
integration tests, never a synthetic override.

    uv run python scripts/measure_gate6.py

Idempotent: every game this script plays uses a fixed game_uid inside its
own throwaway temp directory (never the real logs/ tree), so a rerun
neither appends to nor duplicates a prior run's evidence -- only the one
output JSON below is written, overwritten in place.

See docs/phases/phase-6/GATE-6-MEASUREMENT.md for the write-up this
script's JSON output feeds, and the three Sec10.4 criteria quoted
verbatim from .planning/ROADMAP.md (not this script's to edit).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from gate6_clean_game import measure_clean_game  # noqa: E402
from gate6_report import build_report  # noqa: E402
from gate6_step0 import measure_step0_mismatch  # noqa: E402
from gate6_tamper import measure_tamper  # noqa: E402

_OUT_PATH = Path("docs/phases/phase-6/gate6_measurement_evidence.json")


async def _measure_all() -> dict:
    criterion_1 = await measure_clean_game()
    criterion_2 = await measure_tamper()
    criterion_3 = await measure_step0_mismatch()
    return build_report(criterion_1, criterion_2, criterion_3)


def _print_summary(report: dict) -> None:
    print("GATE-6 measurement -- localhost, zero env vars")
    for key in (
        "criterion_1_four_phases_commit_reveal",
        "criterion_2_hash_nonce_mismatch_technical_loss",
        "criterion_3_step0_verified_before_move_1",
    ):
        print(f"  {key}: {report[key]['verdict']}")


def main() -> int:
    report = asyncio.run(_measure_all())

    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _print_summary(report)
    print(f"Wrote {_OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
