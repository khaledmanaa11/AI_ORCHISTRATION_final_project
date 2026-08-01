"""Reader-side E6 convergence analysis over training/curves.py's CSV (rule 42, STRAT-06).

Pure-stdlib, no matplotlib -- split out of `plot_curves.py` at the 150-line
gate (QUAL-08), the exact contingency `03-09-PLAN.md` names ("or in a small
sibling module if that file approaches 150 lines"). Kept separate from
`training/curves.py` (the writer) per QUAL-02: this module only reads the
schema that one wrote, never re-implements it.

Verdicts are computed **per role** (D-25): cop and thief are judged
independently over the CSV's `role` column so one role's failure can never
mask the other's -- a single averaged verdict could mark the phase
"converged" while one role is still random.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from pursuit.shared.strategy_config import StrategyParams
from training.curves import FIELDNAMES

ROLES = ("cop", "thief")
_INT_FIELDS = frozenset({"episode"})
_STR_FIELDS = frozenset({"role"})


def read_rows(path: Path | str) -> list[dict]:
    """Read a `curves.csv` into typed dict rows, skipping the `# seed=...` comment."""
    lines = [
        line
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if not line.startswith("#")
    ]
    return [_coerce(row) for row in csv.DictReader(lines)]


def _coerce(row: dict) -> dict:
    out = {}
    for name in FIELDNAMES:
        value = row[name]
        if name in _INT_FIELDS:
            out[name] = int(value)
        elif name in _STR_FIELDS:
            out[name] = value
        else:
            out[name] = float(value)
    return out


def rows_for_role(rows: list[dict], role: str) -> list[dict]:
    """Rows belonging to one role, sorted by episode ascending."""
    return sorted((r for r in rows if r["role"] == role), key=lambda r: r["episode"])


def decile_gain(rows: list[dict], role: str) -> float:
    """Final-decile mean win-rate minus first-decile mean win-rate (E6)."""
    role_rows = rows_for_role(rows, role)
    if len(role_rows) < 2:
        return 0.0
    size = max(1, len(role_rows) // 10)
    first_mean = _mean(role_rows[:size], "winrate_vs_baseline")
    final_mean = _mean(role_rows[-size:], "winrate_vs_baseline")
    return final_mean - first_mean


def final_slope(rows: list[dict], role: str, window: int) -> float:
    """Total projected win-rate drift over the trailing `window` episodes.

    A least-squares regression rate (win-rate change per episode) is fit
    over the rows whose episode falls within the last `window` episodes,
    then scaled back up by that window's own episode span. That keeps the
    return value a plain win-rate delta -- directly comparable to
    `convergence_tolerance`, which is itself a win-rate delta (0.02), not a
    per-episode rate (0.02 win-rate/episode would be an absurd bound to hold
    over a 20000-episode window).
    """
    role_rows = rows_for_role(rows, role)
    if len(role_rows) < 2:
        return 0.0
    last_episode = role_rows[-1]["episode"]
    windowed = [r for r in role_rows if r["episode"] >= last_episode - window]
    if len(windowed) < 2:
        return 0.0
    xs = [r["episode"] for r in windowed]
    ys = [r["winrate_vs_baseline"] for r in windowed]
    return _regression_slope(xs, ys) * (xs[-1] - xs[0])


@dataclass(frozen=True)
class Verdict:
    """One role's E6 pass/fail -- never averaged across roles (D-25)."""

    role: str
    decile_gain: float
    final_slope: float
    decile_pass: bool
    slope_pass: bool
    converged: bool


def check_convergence(rows: list[dict], params: StrategyParams) -> dict[str, Verdict]:
    """One `Verdict` per role present in `rows` (QUAL-11: thresholds from config)."""
    roles = sorted({r["role"] for r in rows}) or list(ROLES)
    verdicts = {}
    for role in roles:
        gain = decile_gain(rows, role)
        slope = final_slope(rows, role, params.convergence_window)
        decile_pass = gain >= params.win_rate_margin
        slope_pass = abs(slope) <= params.convergence_tolerance
        verdicts[role] = Verdict(
            role=role, decile_gain=gain, final_slope=slope,
            decile_pass=decile_pass, slope_pass=slope_pass,
            converged=decile_pass and slope_pass,
        )
    return verdicts


def _mean(rows: list[dict], field: str) -> float:
    return sum(r[field] for r in rows) / len(rows)


def _regression_slope(xs: list[int], ys: list[float]) -> float:
    """Ordinary least-squares slope of y over x; 0.0 for a degenerate (single-x) window."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    return numerator / denominator
