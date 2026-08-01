"""matplotlib PNG renderer for the rule-42 README learning-curve section (D-16,
D-20, D-25, STRAT-06).

This is the **only** matplotlib importer in the repo (D-20): a match never
needs a plotting dependency, only the offline training/reporting path does.
The E6 pass/fail math itself (`decile_gain`/`final_slope`/`check_convergence`)
lives in the matplotlib-free `training/curve_analysis.py` sibling and is
re-exported here so both the plan's own spec and a plain
`training.plot_curves` import keep working.

Runnable directly::

    uv run python training/plot_curves.py <csv> <outdir>

Renders, per role (never averaged, D-25): one win-rate-vs-baseline figure
with the epsilon schedule on a secondary axis, plus one shared mean-reward
figure carrying a separately labelled line per role.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    # `uv run python training/plot_curves.py ...` (no `-m`) puts training/
    # itself on sys.path[0], not the repo root, so the `training.*` absolute
    # imports below would fail to resolve. `-m training.plot_curves` and a
    # normal `import training.plot_curves` (pytest) are unaffected.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")  # headless: this runs from a training box / CI, never a GUI session
import matplotlib.pyplot as plt

from training.curve_analysis import (  # noqa: F401 -- re-exported, see module docstring
    ROLES,
    Verdict,
    check_convergence,
    decile_gain,
    final_slope,
    read_rows,
    rows_for_role,
)

WINRATE_FILENAME = "winrate_{role}.png"
MEAN_REWARD_FILENAME = "mean_reward.png"


def render_winrate_figure(rows: list[dict], role: str, outdir: Path) -> Path:
    """Win-rate vs baseline (left axis) with the epsilon schedule (right axis)."""
    role_rows = rows_for_role(rows, role)
    episodes = [r["episode"] for r in role_rows]

    fig, winrate_axis = plt.subplots()
    winrate_axis.plot(episodes, [r["winrate_vs_baseline"] for r in role_rows], color="tab:blue")
    winrate_axis.set_xlabel("episode")
    winrate_axis.set_ylabel("win rate vs baseline", color="tab:blue")
    winrate_axis.set_title(f"{role}: win rate vs baseline, with the epsilon schedule")

    epsilon_axis = winrate_axis.twinx()
    epsilon_axis.plot(episodes, [r["epsilon"] for r in role_rows], color="tab:orange", linestyle="--")
    epsilon_axis.set_ylabel("epsilon", color="tab:orange")

    fig.tight_layout()
    out_path = outdir / WINRATE_FILENAME.format(role=role)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def render_mean_reward_figure(rows: list[dict], outdir: Path) -> Path:
    """One figure, one distinctly-labelled line per role -- never averaged (D-25)."""
    fig, reward_axis = plt.subplots()
    for role in ROLES:
        role_rows = rows_for_role(rows, role)
        if not role_rows:
            continue
        reward_axis.plot(
            [r["episode"] for r in role_rows], [r["mean_reward"] for r in role_rows], label=role,
        )
    reward_axis.set_xlabel("episode")
    reward_axis.set_ylabel("mean reward")
    reward_axis.set_title("Mean reward per episode, by role")
    reward_axis.legend()

    fig.tight_layout()
    out_path = outdir / MEAN_REWARD_FILENAME
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def render_all(csv_path: Path | str, outdir: Path | str) -> list[Path]:
    """Read `csv_path` and render every README PNG into `outdir`; returns the paths written."""
    rows = read_rows(csv_path)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    paths = [
        render_winrate_figure(rows, role, out) for role in ROLES if rows_for_role(rows, role)
    ]
    paths.append(render_mean_reward_figure(rows, out))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Render rule-42 learning-curve PNGs from a curves.csv")
    parser.add_argument("csv_path", type=Path, help="path to the training/curves.py CSV")
    parser.add_argument("outdir", type=Path, help="directory the PNGs are written into")
    args = parser.parse_args()
    for path in render_all(args.csv_path, args.outdir):
        print(path)


if __name__ == "__main__":
    main()
