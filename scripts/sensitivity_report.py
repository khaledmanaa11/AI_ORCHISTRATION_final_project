"""Renders `docs/SENSITIVITY.md`'s tables from `artifacts/sensitivity/sweep.json`
(08-09).

    uv run python scripts/sensitivity_report.py            # print the block

SEPARABILITY IS THE CONSERVATIVE TEST `training/arena.compare` ALREADY USES:
two rates are called separable only when their 95% Wilson intervals do not
OVERLAP, which is stricter than a two-proportion z-test. At the sample sizes
here that means most knobs will read "not separable", and reporting that
honestly is the point -- Phase 3's post-mortem exists because run 1 quoted
5/20 and 16/20 as bare fractions and could not tell a broken policy from a
working one.

A knob whose baseline is already at 100% is flagged SATURATED. It cannot
show an upward effect, so no conclusion about that knob may be drawn from
that matchup, and the summary refuses to rank it on one.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SWEEP_PATH = REPO_ROOT / "artifacts" / "sensitivity" / "sweep.json"
BEGIN = "<!-- BEGIN GENERATED: sensitivity -->"
END = "<!-- END GENERATED: sensitivity -->"
SATURATED = 1.0


def load(path=SWEEP_PATH) -> dict:
    """The sweep artifact, or a loud failure -- never an empty report."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"{target} is missing -- run scripts/sensitivity_sweep.py")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not data.get("cells"):
        raise ValueError(f"{target} has no cells -- refusing to render an empty sweep")
    return data


def _baseline_cell(data: dict) -> dict:
    for cell in data["cells"]:
        if cell.get("is_baseline"):
            return cell
    raise ValueError("the sweep has no baseline cell to measure deltas against")


def _separable(one: dict, other: dict) -> bool:
    """Non-overlapping 95% Wilson intervals -- `arena.compare`'s rule."""
    return one["ci_low"] > other["ci_high"] or one["ci_high"] < other["ci_low"]


def _rows(data: dict, label: str) -> list:
    """One matchup's table: every configuration against the baseline."""
    base = _baseline_cell(data)["matchups"][label]
    saturated = base["rate"] >= SATURATED
    head = [
        f"**{label}** -- baseline {base['wins']}/{base['games']} = {base['rate']:.1%} "
        f"[{base['ci_low']:.1%}, {base['ci_high']:.1%}]"
        + ("  **SATURATED: no upward effect is observable here**" if saturated else ""),
        "",
        "| Knob | Value | Wins | Rate | 95% Wilson | delta | 95% separable |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for cell in data["cells"]:
        if cell.get("is_baseline"):
            continue
        entry = cell["matchups"][label]
        delta = entry["rate"] - base["rate"]
        verdict = "**yes**" if _separable(entry, base) else "no"
        head.append(
            f"| `{cell['knob']}` | {cell['value']} | {entry['wins']}/{entry['games']} "
            f"| {entry['rate']:.1%} | [{entry['ci_low']:.1%}, {entry['ci_high']:.1%}] "
            f"| {delta:+.1%} | {verdict} |"
        )
    head.append("")
    return head


def summary(data: dict) -> list:
    """Knobs ranked by the largest separable effect they produced anywhere."""
    base = _baseline_cell(data)["matchups"]
    labels = list(base)
    scored = {}
    for cell in data["cells"]:
        if cell.get("is_baseline"):
            continue
        for label in labels:
            if base[label]["rate"] >= SATURATED:
                continue
            entry = cell["matchups"][label]
            delta = entry["rate"] - base[label]["rate"]
            best = scored.get(cell["knob"])
            if best is None or abs(delta) > abs(best[0]):
                scored[cell["knob"]] = (delta, cell["value"], label,
                                        _separable(entry, base[label]))
    lines = [
        "| Knob | Largest effect | At | On matchup | 95% separable |",
        "|---|---:|---|---|---|",
    ]
    for knob, (delta, value, label, sep) in sorted(
            scored.items(), key=lambda item: -abs(item[1][0])):
        lines.append(f"| `{knob}` | {delta:+.1%} | {value} | {label} "
                     f"| {'**yes**' if sep else 'no'} |")
    return [*lines, ""]


def render(data: dict) -> str:
    """The generated block, between its two markers."""
    base = data["baseline"]
    lines = [
        BEGIN, "",
        f"Sweep: **{len(data['cells'])} configurations**, "
        f"**{data['games_per_matchup']} games per matchup**, eval seed "
        f"`{data['eval_seed']}`, wall time {data['wall_time_seconds']}s.",
        "",
        "Baseline (the shipped configuration): "
        + ", ".join(f"`{key}`={value}" for key, value in sorted(base.items())) + ".",
        "",
        "### Effect ranking", "",
        *summary(data),
        "### Per-matchup detail", "",
    ]
    for label in _baseline_cell(data)["matchups"]:
        lines.extend(_rows(data, label))
    lines.extend([
        "### Fixed parameters the sweep did NOT vary", "",
        "Derived from `docs/PARAMETERS.md`'s Status column, not typed here; "
        "`scripts/sensitivity_status.py`'s `refuse_fixed` fails the sweep if "
        "any of them reaches the grid.", "",
        *(f"- `[{name}]`" for name in data["fixed_parameters_not_varied"]),
        "", END,
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    """Print the block `docs/SENSITIVITY.md` embeds."""
    parser = argparse.ArgumentParser(description="Render the sensitivity tables")
    parser.add_argument("--sweep", default=str(SWEEP_PATH))
    print(render(load(parser.parse_args(argv).sweep)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
