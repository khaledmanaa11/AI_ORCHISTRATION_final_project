"""Tests for training/curves.py: header-once, append, and truncate-on-resume
(D-16, D-24, rule 42)."""

from __future__ import annotations

import csv
from pathlib import Path

from training import curves


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
