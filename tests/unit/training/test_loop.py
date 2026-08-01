"""Tests for training/loop.py's outer, resumable run driver (Task 4, 03-08,
STRAT-06): a short seeded run, exact reproducibility, resume continuity of
the epsilon/alpha schedules, and curve truncation on resume (D-24)."""

from __future__ import annotations

import dataclasses
import pathlib
from unittest import mock

import pytest

import training.loop as loop_mod
from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.strategy_config import load_strategy_config
from training import artifacts, checkpoint, runstate
from training.loop import TrainingRunConfig, run_training
from training.loop_setup import require_shared_run_fields

_CONFIG_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "config"


def _game_params() -> GameParams:
    return load_game_params(_CONFIG_DIR / "police" / "game_params.json")


def _tiny_config(artifacts_dir: str, episodes: int) -> TrainingRunConfig:
    """A handful-of-episodes run: fast to execute, still exercises every
    cadence (checkpoint/curve/pool-snapshot all fire at least once)."""
    overrides = {
        "episodes": episodes, "checkpoint_every": 10, "curve_log_every": 5,
        "pool_snapshot_every": 10, "artifacts_dir": artifacts_dir,
        "epsilon_decay_episodes": 30, "alpha_decay_episodes": 30,
    }
    cop = dataclasses.replace(load_strategy_config(_CONFIG_DIR / "police" / "strategy.json"), **overrides)
    thief = dataclasses.replace(load_strategy_config(_CONFIG_DIR / "thief" / "strategy.json"), **overrides)
    return TrainingRunConfig(game_params=_game_params(), cop_params=cop, thief_params=thief)


def _curve_rows(path: pathlib.Path) -> list[str]:
    """Data rows only -- drops the leading `# seed=...` comment AND the
    `episode,epsilon,...` header line itself."""
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("#")]
    return lines[1:]


def test_short_seeded_run_completes_with_nonzero_visits(tmp_path: pathlib.Path) -> None:
    config = _tiny_config(str(tmp_path / "art"), episodes=30)
    result = run_training(config)

    assert result.run_state.episode == 30
    assert result.run_state.cop_episodes == 15
    assert result.run_state.thief_episodes == 15
    assert sum(result.cop_table._visits.values()) > 0
    assert sum(result.thief_table._visits.values()) > 0
    assert (tmp_path / "art" / "curves.csv").exists()


def test_same_seed_reproduces_the_same_curve_and_tables(tmp_path: pathlib.Path) -> None:
    config_a = _tiny_config(str(tmp_path / "a"), episodes=30)
    config_b = _tiny_config(str(tmp_path / "b"), episodes=30)

    result_a = run_training(config_a)
    result_b = run_training(config_b)

    rows_a = _curve_rows(tmp_path / "a" / "curves.csv")
    rows_b = _curve_rows(tmp_path / "b" / "curves.csv")
    assert rows_a == rows_b
    assert result_a.cop_table._values == result_b.cop_table._values
    assert result_a.thief_table._values == result_b.thief_table._values


def test_resume_continues_epsilon_and_alpha_across_the_checkpoint_boundary(
    tmp_path: pathlib.Path,
) -> None:
    artifacts_dir = str(tmp_path / "art")
    first = run_training(_tiny_config(artifacts_dir, episodes=20))
    assert first.run_state.cop_episodes == 10

    resumed_config = _tiny_config(artifacts_dir, episodes=40)
    expected_epsilon = runstate.epsilon_at(first.run_state.cop_episodes, resumed_config.cop_params)
    expected_alpha = runstate.alpha_at(first.run_state.cop_episodes, resumed_config.cop_params)

    # A fresh 0..40 run's cop epsilon/alpha AT role-episode 10 must equal
    # what a resumed run reads for the very next cop episode -- i.e. resume
    # does not reset the schedule back to epsilon_start/alpha.
    assert expected_epsilon < resumed_config.cop_params.epsilon_start
    assert expected_alpha < resumed_config.cop_params.alpha

    second = run_training(resumed_config)
    assert second.run_state.episode == 40
    assert second.run_state.cop_episodes == 20
    assert second.run_state.thief_episodes == 20


def test_resume_truncates_curve_rows_past_the_checkpoint_episode(tmp_path: pathlib.Path) -> None:
    artifacts_dir = str(tmp_path / "art")
    first = run_training(_tiny_config(artifacts_dir, episodes=20))
    curve_file = artifacts.curve_path(_tiny_config(artifacts_dir, episodes=20).cop_params)

    # Simulate a crash that left one extra row appended past the last
    # successful checkpoint (curve_log_every < checkpoint_every in general).
    stray_episode = first.run_state.episode + 5
    with curve_file.open("a", encoding="utf-8") as fh:
        fh.write(f"{stray_episode},0.1,0.1,0.0,0.0,0.0,cop\n")
    assert any(row.startswith(f"{stray_episode},") for row in _curve_rows(curve_file))

    run_training(_tiny_config(artifacts_dir, episodes=40))

    remaining = _curve_rows(curve_file)
    assert not any(row.startswith(f"{stray_episode},") for row in remaining)
    assert all(int(row.split(",")[0]) <= 40 for row in remaining)


def test_final_checkpoint_is_written_on_keyboard_interrupt(tmp_path: pathlib.Path) -> None:
    config = _tiny_config(str(tmp_path / "art"), episodes=100)
    real_run_episode = loop_mod.run_episode
    calls = {"n": 0}

    def _flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 23:
            raise KeyboardInterrupt("simulated ctrl-c, no SIGTERM on Windows")
        return real_run_episode(*args, **kwargs)

    with mock.patch.object(loop_mod, "run_episode", side_effect=_flaky), pytest.raises(KeyboardInterrupt):
        run_training(config)

    payload = checkpoint.load_checkpoint(artifacts.run_state_path(config.cop_params))
    assert payload is not None
    assert 0 < payload["episode"] < 100


def test_require_shared_run_fields_rejects_a_seed_mismatch() -> None:
    cop = load_strategy_config(_CONFIG_DIR / "police" / "strategy.json")
    thief = dataclasses.replace(load_strategy_config(_CONFIG_DIR / "thief" / "strategy.json"), seed=cop.seed + 1)
    with pytest.raises(ValueError, match="seed"):
        require_shared_run_fields(cop, thief)
