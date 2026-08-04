"""Crash-safety/retry tests for QTable.save()/load() over durable_write.py
(D-15, D-24). Split out of test_qtable.py by the 150-line gate."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from pursuit.shared import durable_write
from pursuit.strategy.qtable import SCHEMA_VERSION, QTable

_KEY_A = "2,3|5,5|9|6|1"
_KEY_B = "0,0|1,1|0|0|0"


def test_durable_write_raises_after_retries_exhausted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "qtable.json"

    def _always_denied(*_args, **_kwargs):
        raise PermissionError("simulated persistent WinError 32")

    monkeypatch.setattr(durable_write.os, "replace", _always_denied)
    with pytest.raises(PermissionError):
        durable_write.durable_write_json(
            path, {"version": SCHEMA_VERSION, "table": {}}, retries=1, backoff=0.01
        )


def test_interrupted_write_before_rotate_leaves_target_loadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulated crash between step 1 (write temp) and step 2 (rotate) --
    os.replace never completes, so target is untouched and still loads."""
    path = tmp_path / "qtable.json"
    good = QTable()
    good.set(_KEY_A, 0, 0.5)
    good.save(path)

    def _boom(*_args, **_kwargs):
        raise RuntimeError("simulated crash before rotate")

    monkeypatch.setattr(durable_write.os, "replace", _boom)
    another = QTable()
    another.set(_KEY_B, 1, 9.9)
    with pytest.raises(RuntimeError):
        another.save(path)

    monkeypatch.undo()
    reloaded = QTable.load(path)
    assert reloaded.get(_KEY_A, 0) == 0.5


def test_corrupted_current_file_falls_back_to_prev_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "qtable.json"
    first = QTable()
    first.set(_KEY_A, 0, 0.5)
    first.save(path)  # first save: no .prev yet

    second = QTable()
    second.set(_KEY_B, 1, 9.9)
    second.save(path)  # rotates first save's data into .prev

    path.write_text("{not valid json", encoding="utf-8")  # corrupt the current target

    with caplog.at_level(logging.WARNING):
        loaded = QTable.load(path)

    assert loaded.get(_KEY_A, 0) == 0.5  # recovered from .prev, not the corrupt target
    assert any("fall" in record.message.lower() for record in caplog.records)


def test_permission_error_on_first_replace_is_retried_and_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "qtable.json"
    real_replace = durable_write.os.replace
    calls = {"count": 0}

    def _flaky_replace(src, dst):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PermissionError("simulated WinError 32")
        return real_replace(src, dst)

    monkeypatch.setattr(durable_write.os, "replace", _flaky_replace)

    table = QTable()
    table.set(_KEY_A, 0, 0.5)
    table.save(path)  # must succeed despite the first PermissionError

    assert calls["count"] >= 2
    monkeypatch.undo()
    loaded = QTable.load(path)
    assert loaded.get(_KEY_A, 0) == 0.5
