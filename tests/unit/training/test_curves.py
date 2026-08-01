"""Tests for training/curves.py (header-once, append, truncate-on-resume) and
training/curve_analysis.py's E6 convergence checks (D-16, D-24, D-25, rule
42). The analysis functions live in curve_analysis.py -- a sibling module
split out of plot_curves.py at the 150-line gate (QUAL-08) -- but the plan
directs their tests here rather than into a second test file for curves.py
(they still read the exact CSV schema this file's other tests write)."""

from __future__ import annotations

import csv
import dataclasses
import pathlib
from pathlib import Path

from pursuit.shared.strategy_config import StrategyParams, load_strategy_config
from training import curve_analysis, curves

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "config"


def _row(episode: int, role: str = "cop") -> dict:
    return {
        "episode": episode,
        "epsilon": 0.5,
        "alpha": 0.1,
        "mean_reward": 0.2,
        "winrate_vs_baseline": 0.3,
        "fallback_rate": 0.4,
        "role": role,
    }


def test_open_curve_writes_header_with_seed_and_hash_only_when_new(tmp_path: Path) -> None:
    path = tmp_path / "curves.csv"
    cw = curves.open_curve(path, seed=1337, config_hash="deadbeef")
    curves.append(cw, _row(1))
    curves.close(cw)

    text = path.read_text(encoding="utf-8")
    assert text.startswith("# seed=1337 config_hash=deadbeef\n")
    assert "episode,epsilon,alpha,mean_reward,winrate_vs_baseline,fallback_rate,role" in text

    cw2 = curves.open_curve(path, seed=1337, config_hash="deadbeef")
    curves.append(cw2, _row(2))
    curves.close(cw2)
    assert path.read_text(encoding="utf-8").count("# seed=") == 1  # header written once


def test_append_rows_are_readable_by_csv_dictreader(tmp_path: Path) -> None:
    path = tmp_path / "curves.csv"
    cw = curves.open_curve(path, seed=1, config_hash="h")
    curves.append(cw, _row(1, role="cop"))
    curves.append(cw, _row(2, role="thief"))
    curves.close(cw)

    lines = path.read_text(encoding="utf-8").splitlines()
    reader = csv.DictReader(lines[1:])  # skip the "# seed=" comment line
    rows = list(reader)
    assert [r["role"] for r in rows] == ["cop", "thief"]
    assert [int(r["episode"]) for r in rows] == [1, 2]


def test_truncate_after_removes_only_rows_past_the_checkpoint_episode(tmp_path: Path) -> None:
    path = tmp_path / "curves.csv"
    cw = curves.open_curve(path, seed=1, config_hash="h")
    for episode in (1, 2, 3, 4, 5):
        curves.append(cw, _row(episode))
    curves.close(cw)

    removed = curves.truncate_after(path, episode=3)
    assert removed == 2

    lines = path.read_text(encoding="utf-8").splitlines()
    reader = csv.DictReader(lines[1:])
    remaining = [int(r["episode"]) for r in reader]
    assert remaining == [1, 2, 3]


def test_truncate_after_on_missing_file_is_a_noop(tmp_path: Path) -> None:
    assert curves.truncate_after(tmp_path / "absent.csv", episode=5) == 0


def test_truncate_after_removing_nothing_leaves_file_untouched(tmp_path: Path) -> None:
    path = tmp_path / "curves.csv"
    cw = curves.open_curve(path, seed=1, config_hash="h")
    curves.append(cw, _row(1))
    curves.close(cw)
    before = path.read_text(encoding="utf-8")

    removed = curves.truncate_after(path, episode=100)
    assert removed == 0
    assert path.read_text(encoding="utf-8") == before


def test_resume_can_append_after_truncate(tmp_path: Path) -> None:
    path = tmp_path / "curves.csv"
    cw = curves.open_curve(path, seed=9, config_hash="h")
    for episode in (1, 2, 3):
        curves.append(cw, _row(episode))
    curves.close(cw)

    curves.truncate_after(path, episode=1)
    cw2 = curves.open_curve(path, seed=9, config_hash="h")  # file exists -> no new header
    curves.append(cw2, _row(2))
    curves.close(cw2)

    lines = path.read_text(encoding="utf-8").splitlines()
    reader = csv.DictReader(lines[1:])
    assert [int(r["episode"]) for r in reader] == [1, 2]
    assert lines[0].startswith("# seed=9")


def _params(**overrides) -> StrategyParams:
    base = load_strategy_config(_CONFIG_DIR / "police" / "strategy.json")
    defaults = {"win_rate_margin": 0.10, "convergence_tolerance": 0.02, "convergence_window": 5000}
    return dataclasses.replace(base, **{**defaults, **overrides})


def _analysis_row(episode: int, winrate: float, role: str) -> dict:
    return {
        "episode": episode, "epsilon": 0.1, "alpha": 0.1, "mean_reward": 0.0,
        "winrate_vs_baseline": winrate, "fallback_rate": 0.0, "role": role,
    }


def _rising_then_flat(role: str = "cop", n: int = 100, plateau_at: int = 80, cap: float = 0.5) -> list:
    """Climbs 0 -> cap over the first `plateau_at` rows, then holds flat -- converged."""
    return [
        _analysis_row((i + 1) * 500, cap if i >= plateau_at else cap * (i / plateau_at), role)
        for i in range(n)
    ]


def _flat_noise(role: str = "cop", n: int = 100) -> list:
    """Constant-mean zigzag from episode 1 -- never actually learns."""
    return [_analysis_row((i + 1) * 500, 0.5 + (0.02 if i % 2 == 0 else -0.02), role) for i in range(n)]


def _still_climbing(role: str = "cop", n: int = 100) -> list:
    """Strictly monotonic to the very last row -- not converged at the cut."""
    return [_analysis_row((i + 1) * 500, 0.9 * i / (n - 1), role) for i in range(n)]


def test_rising_then_flat_curve_converges() -> None:
    verdict = curve_analysis.check_convergence(_rising_then_flat(), _params())["cop"]
    assert verdict.decile_gain > 0
    assert verdict.decile_pass is True
    assert verdict.slope_pass is True
    assert verdict.converged is True


def test_flat_noise_curve_fails_the_decile_gain_check() -> None:
    verdict = curve_analysis.check_convergence(_flat_noise(), _params())["cop"]
    assert verdict.decile_pass is False
    assert verdict.slope_pass is True
    assert verdict.converged is False


def test_still_climbing_curve_fails_the_slope_check() -> None:
    verdict = curve_analysis.check_convergence(_still_climbing(), _params())["cop"]
    assert verdict.decile_pass is True
    assert verdict.slope_pass is False
    assert verdict.converged is False


def test_verdicts_are_reported_separately_per_role() -> None:
    """One role converged, the other still climbing -- neither masks the other (D-25)."""
    rows = _rising_then_flat(role="cop") + _still_climbing(role="thief")
    verdicts = curve_analysis.check_convergence(rows, _params())
    assert verdicts["cop"].converged is True
    assert verdicts["thief"].converged is False


def test_read_rows_round_trips_types_from_a_written_csv(tmp_path: Path) -> None:
    path = tmp_path / "curves.csv"
    cw = curves.open_curve(path, seed=1, config_hash="h")
    curves.append(cw, _row(1, role="cop"))
    curves.close(cw)

    assert curve_analysis.read_rows(path) == [{
        "episode": 1, "epsilon": 0.5, "alpha": 0.1, "mean_reward": 0.2,
        "winrate_vs_baseline": 0.3, "fallback_rate": 0.4, "role": "cop",
    }]
