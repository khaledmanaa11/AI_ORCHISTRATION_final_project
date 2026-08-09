#!/usr/bin/env python
"""GATE-4 measurement CLI (04-14): one command, one JSON result, every
number the book's Sec10.4 gate (quoted verbatim in .planning/ROADMAP.md,
NOT this plan's to edit) needs, plus D-32's live-API confirmation.

    uv run python scripts/measure_gate4.py --mocked   # default; no key needed
    ANTHROPIC_API_KEY=... uv run python scripts/measure_gate4.py --live

Both runs are read-only against the shipped game: no `src/` behaviour is
special-cased for measurement (must_haves: "the measurement describes the
shipped game and not a special build"). Two runs of --mocked with the same
seeds (GATE4_SEEDS, gate4_games.py) produce identical criterion numbers --
a measurement that cannot be rerun is an anecdote.

See docs/phases/phase-4/GATE-4-MEASUREMENT.md for the write-up this
script's JSON output feeds, and the three Sec10.4 criteria quoted verbatim.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Guarded sys.path bootstrap (same idiom as training/plot_curves.py, per
# STATE.md's Phase-3 precedent): direct-path execution puts `scripts/` on
# sys.path[0], not the repo root, so `pursuit`/`tests` would not import.
if __package__ in (None, ""):
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from gate4_runner import run_live, run_mocked  # noqa: E402

_DEFAULT_OUT = {
    "mocked": Path("docs/phases/phase-4/gate4_measurement_mocked.json"),
    "live": Path("docs/phases/phase-4/gate4_measurement_live.json"),
}


def _print_summary(report: dict) -> None:
    print(f"GATE-4 measurement -- mode={report.get('mode')}")
    for key in ("criterion_1_hint_to_inference", "criterion_2_scent_decay", "criterion_3_hint_every_turn"):
        if key in report:
            verdict = report[key].get("verdict", "n/a")
            print(f"  {key}: {verdict}")
    if "live" in report:
        print(f"  live: {report['live'].get('status')}")


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    mode = "mocked"
    out: Path | None = None
    args = list(argv)
    if "--live" in args:
        mode = "live"
        args.remove("--live")
    if "--mocked" in args:
        args.remove("--mocked")
    if "--out" in args:
        idx = args.index("--out")
        out = Path(args[idx + 1])
        del args[idx : idx + 2]
    return mode, out or _DEFAULT_OUT[mode]


def main(argv: list[str] | None = None) -> int:
    mode, out_path = _parse_args(sys.argv[1:] if argv is None else argv)
    report = asyncio.run(run_live() if mode == "live" else run_mocked())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _print_summary(report)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
