"""Learning-curve CSV writer (D-16, rule 42).

Created here, in Wave 5, because the harness must append a row from
episode 1 of run 1 -- rule-42 instrumentation cannot be retrofitted onto an
overnight run already in progress (D-16).

Schema, exact column order (AI-SPEC E6)::

    episode, epsilon, alpha, mean_reward, winrate_vs_baseline, fallback_rate, role

`role` keeps the cop and thief curves separable (D-25) -- averaging them
would hide one role converging while the other stays random. Standard
library `csv` only; matplotlib (D-20) belongs to 03-09's plotting script,
never here.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import IO

FIELDNAMES = (
    "episode",
    "epsilon",
    "alpha",
    "mean_reward",
    "winrate_vs_baseline",
    "fallback_rate",
    "role",
)
_COMMENT_PREFIX = "#"


@dataclass
class CurveWriter:
    path: Path
    handle: IO[str]
    writer: csv.DictWriter


def open_curve(path: Path | str, seed: int, config_hash: str) -> CurveWriter:
    """Open path for append; writes the seed/config-hash header only if new."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    is_new = not target.exists()
    handle = target.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(handle, fieldnames=list(FIELDNAMES))
    if is_new:
        handle.write(f"{_COMMENT_PREFIX} seed={seed} config_hash={config_hash}\n")
        writer.writeheader()
        handle.flush()
    return CurveWriter(path=target, handle=handle, writer=writer)


def append(cw: CurveWriter, row: dict) -> None:
    """Write one row and flush() -- no fsync; losing one row costs one
    interval, never the whole run (RESEARCH Sec3)."""
    cw.writer.writerow(row)
    cw.handle.flush()


def close(cw: CurveWriter) -> None:
    cw.handle.close()


def truncate_after(path: Path | str, episode: int) -> int:
    """Remove rows with episode > `episode`; returns the removed count (D-24).

    Called on resume so a rewound, re-run segment never duplicates rows the
    rule-42 PNG would then plot twice.
    """
    target = Path(path)
    if not target.exists():
        return 0
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    header, data_start = _split_header(lines)
    reader = csv.DictReader(lines[data_start:], fieldnames=list(FIELDNAMES))
    kept, removed = [], 0
    for row in reader:
        if int(row["episode"]) <= episode:
            kept.append(row)
        else:
            removed += 1
    if removed:
        _rewrite(target, header, kept)
    return removed


def _rewrite(target: Path, header: list, kept: list) -> None:
    with target.open("w", newline="", encoding="utf-8") as fh:
        fh.writelines(header)
        writer = csv.DictWriter(fh, fieldnames=list(FIELDNAMES))
        writer.writerows(kept)


def _split_header(lines: list) -> tuple:
    idx = 0
    while idx < len(lines) and lines[idx].startswith(_COMMENT_PREFIX):
        idx += 1
    return lines[: idx + 1], idx + 1
