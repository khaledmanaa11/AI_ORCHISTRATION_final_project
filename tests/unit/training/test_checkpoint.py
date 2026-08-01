"""Tests for training/checkpoint.py (durable I/O) and training/runstate.py
(the manifest shape + RNG-state round trip + ε/α schedules), 03-08 Task 1."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from pursuit.shared import durable_write
from pursuit.shared.strategy_config import load_strategy_config
from training import checkpoint, runstate

_STRATEGY_PATH = Path(__file__).parent.parent.parent.parent / "config" / "police" / "strategy.json"


def _params():
    return load_strategy_config(_STRATEGY_PATH)


def test_save_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "run_state.json"
    payload = {"episode": 5, "seed": 1337, "rng_state": {"version": 3}}
    checkpoint.save_checkpoint(path, payload)
    assert checkpoint.load_checkpoint(path) == payload


def test_load_missing_checkpoint_returns_none(tmp_path: Path) -> None:
    assert checkpoint.load_checkpoint(tmp_path / "absent.json") is None


def test_corrupt_current_falls_back_to_prev(tmp_path: Path) -> None:
    path = tmp_path / "run_state.json"
    checkpoint.save_checkpoint(path, {"episode": 1})
    checkpoint.save_checkpoint(path, {"episode": 2})  # rotates episode-1 into .prev
    path.write_text("{not valid json", encoding="utf-8")
    assert checkpoint.load_checkpoint(path) == {"episode": 1}


def test_permission_error_on_first_replace_is_retried_and_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "run_state.json"
    real_replace = durable_write.os.replace
    calls = {"count": 0}

    def _flaky_replace(src, dst):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PermissionError("simulated WinError 32")
        return real_replace(src, dst)

    monkeypatch.setattr(durable_write.os, "replace", _flaky_replace)
    checkpoint.save_checkpoint(path, {"episode": 3})
    assert calls["count"] >= 2
    monkeypatch.undo()
    assert checkpoint.load_checkpoint(path) == {"episode": 3}


def test_rng_state_round_trip_reproduces_exact_sequence() -> None:
    source = random.Random(42)
    _ = [source.random() for _ in range(5)]  # burn some draws before the snapshot
    state = runstate.capture_rng_state(source)
    expected = [source.random() for _ in range(10)]

    restored = random.Random(0)  # deliberately mismatched seed before restore
    runstate.restore_rng_state(restored, state)
    actual = [restored.random() for _ in range(10)]

    assert actual == expected


def test_runstate_payload_round_trip() -> None:
    state = runstate.RunState(
        episode=10,
        cop_episodes=5,
        thief_episodes=5,
        seed=1337,
        config_hash="abc123",
        csv_row_count=2,
        rng_state={"version": 3, "keys": [1, 2, 3], "gauss_next": None},
    )
    assert runstate.RunState.from_payload(state.to_payload()) == state


def test_config_hash_is_deterministic_and_change_sensitive() -> None:
    import dataclasses

    params = _params()
    assert runstate.config_hash(params) == runstate.config_hash(params)
    changed = dataclasses.replace(params, seed=params.seed + 1)
    assert runstate.config_hash(changed) != runstate.config_hash(params)


def test_epsilon_at_decays_linearly_to_floor() -> None:
    params = _params()
    assert runstate.epsilon_at(0, params) == params.epsilon_start
    assert runstate.epsilon_at(params.epsilon_decay_episodes, params) == pytest.approx(
        params.epsilon_floor
    )
    assert runstate.epsilon_at(params.epsilon_decay_episodes * 10, params) == pytest.approx(
        params.epsilon_floor
    )
    midpoint = runstate.epsilon_at(params.epsilon_decay_episodes // 2, params)
    assert params.epsilon_floor < midpoint < params.epsilon_start


def test_alpha_at_decays_linearly_to_floor() -> None:
    params = _params()
    assert runstate.alpha_at(0, params) == params.alpha
    assert runstate.alpha_at(params.alpha_decay_episodes, params) == pytest.approx(
        params.alpha_floor
    )
    assert runstate.alpha_at(params.alpha_decay_episodes * 10, params) == pytest.approx(
        params.alpha_floor
    )
