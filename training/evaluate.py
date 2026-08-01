"""GATE-4 evaluation CLI (STRAT-01/06, PRD §10.4 criterion d, AI-SPEC Sec5 E5).

Three arms replayed over the identical, committed scenario+seed grid
(`artifacts/eval_scenarios.json`, D-23 held-out seeds): heuristic-vs-
heuristic (the per-role baseline), Q-cop vs heuristic-thief, Q-thief vs
heuristic-cop. Every game is READ-ONLY (`training.eval_arms.play_game`) --
evaluation never mutates a Q-table, on disk or in memory beyond the load.

    uv run python training/evaluate.py --smoke                  # eval_games_ci, fast
    uv run python training/evaluate.py --full --assert-gate      # the real gate

Numbers are always printed, even when a gate fails or a table is missing --
a failing gate with a real number is useful; one with no number is not.
`--assert-gate` exits nonzero unless every role's gate passes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    # `uv run python training/evaluate.py ...` (no `-m`) puts training/ itself
    # on sys.path[0], not the repo root -- see training/plot_curves.py (03-09)
    # for the same fix to the same direct-path-execution problem.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from training.eval_report import EvaluationReport, run_evaluation
from training.eval_scenarios import DEFAULT_SCENARIOS_PATH


def _print_report(report: EvaluationReport) -> None:
    total_games = report.n_scenarios * report.repeats
    print(f"Evaluated {report.n_scenarios} scenarios x {report.repeats} repeats = {total_games} games per arm.")
    for role in sorted(report.verdicts):
        v = report.verdicts[role]
        status = "PASS" if v.passed else "FAIL"
        print(
            f"[{status}] role={role} n={v.n_games} "
            f"learner_win_rate={v.learner_win_rate:.3f} baseline_win_rate={v.baseline_win_rate:.3f} "
            f"margin={v.margin:+.3f} mcnemar_p={v.mcnemar_p:.4f} z={v.z_score:.2f} "
            f"(margin_ok={v.meets_margin} floor_ok={v.meets_absolute_floor} significant={v.is_significant})"
        )
    for role in sorted(report.errors):
        baseline_rate = report.baseline_win_rates.get(role)
        print(
            f"[SKIP] role={role}: {report.errors[role]} "
            f"(measured baseline win_rate={baseline_rate:.3f} over {report.n_scenarios * report.repeats} games)"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GATE-4: QLearningBrain vs HeuristicBrain, per role")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true", help="eval_games_ci subset (default, CI-fast)")
    mode.add_argument("--full", action="store_true", help="the full eval_games statistical gate")
    parser.add_argument("--assert-gate", action="store_true", help="exit nonzero unless every role passes")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS_PATH)
    args = parser.parse_args(argv)

    report = run_evaluation(full=args.full, scenarios_path=args.scenarios)
    _print_report(report)

    if args.assert_gate and (report.errors or not all(v.passed for v in report.verdicts.values())):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
