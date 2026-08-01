"""Tests for training/plot_curves.py's PNG rendering + CLI (D-16, D-20, D-25,
rule 42). training/curve_analysis.py's E6 math is tested in
tests/unit/training/test_curves.py -- this file covers rendering only."""

from __future__ import annotations

import pathlib
import subprocess
import sys

from training import curves, plot_curves

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent


def _write_fixture_csv(path: pathlib.Path, roles: tuple[str, ...] = ("cop", "thief")) -> pathlib.Path:
    cw = curves.open_curve(path, seed=1337, config_hash="deadbeef")
    for i in range(20):
        for role in roles:
            curves.append(cw, {
                "episode": (i + 1) * 500, "epsilon": max(0.05, 1.0 - i / 20), "alpha": 0.1,
                "mean_reward": i / 20, "winrate_vs_baseline": min(0.6, i / 15),
                "fallback_rate": max(0.0, 0.5 - i / 40), "role": role,
            })
    curves.close(cw)
    return path


def test_render_all_produces_a_winrate_png_per_role_plus_one_reward_png(tmp_path: pathlib.Path) -> None:
    csv_path = _write_fixture_csv(tmp_path / "curves.csv")
    outdir = tmp_path / "out"

    paths = plot_curves.render_all(csv_path, outdir)

    names = {p.name for p in paths}
    assert names == {"winrate_cop.png", "winrate_thief.png", "mean_reward.png"}
    for path in paths:
        assert path.exists()
        assert path.stat().st_size > 0


def test_render_all_skips_a_role_with_no_rows(tmp_path: pathlib.Path) -> None:
    csv_path = _write_fixture_csv(tmp_path / "curves.csv", roles=("cop",))
    outdir = tmp_path / "out"

    paths = plot_curves.render_all(csv_path, outdir)

    names = {p.name for p in paths}
    assert names == {"winrate_cop.png", "mean_reward.png"}


def test_main_writes_pngs_and_prints_their_paths(tmp_path: pathlib.Path, capsys, monkeypatch) -> None:
    csv_path = _write_fixture_csv(tmp_path / "curves.csv")
    outdir = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["plot_curves.py", str(csv_path), str(outdir)])

    plot_curves.main()

    printed = capsys.readouterr().out
    assert "winrate_cop.png" in printed
    assert "mean_reward.png" in printed


def test_cli_runs_by_direct_path_uv_style(tmp_path: pathlib.Path) -> None:
    """Proves the plan's literal `uv run python training/plot_curves.py <csv>
    <outdir>` form actually works -- direct-path execution needs its own
    sys.path bootstrap (Rule 3 fix) since it does not get `-m`'s or pytest's
    rootdir insertion."""
    csv_path = _write_fixture_csv(tmp_path / "curves.csv")
    outdir = tmp_path / "out"

    result = subprocess.run(
        [sys.executable, "training/plot_curves.py", str(csv_path), str(outdir)],
        cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    )

    assert (outdir / "winrate_cop.png").exists()
    assert "winrate_cop.png" in result.stdout
