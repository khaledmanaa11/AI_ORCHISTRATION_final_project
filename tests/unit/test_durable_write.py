"""Tests for the crash-safe JSON write/read sequence (D-15, D-24).

durable_write.py lost its only two callers (qtable.py, checkpoint.py) when
the run-1 Q-learning architecture was retired (docs/PRD_matrix_mover.md) --
neither ever had a dedicated test of its own, the module was only exercised
indirectly. This file gives the generic crash-safety primitive its own
direct coverage, independent of whichever caller happens to use it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pursuit.shared.durable_write import durable_write_json, load_json_with_fallback

_RETRIES = 3
_BACKOFF = 0.0


def test_write_then_read_round_trips(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    durable_write_json(target, {"a": 1}, retries=_RETRIES, backoff=_BACKOFF)
    assert load_json_with_fallback(target) == {"a": 1}


def test_write_creates_parent_directories(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "dir" / "state.json"
    durable_write_json(target, {"ok": True}, retries=_RETRIES, backoff=_BACKOFF)
    assert target.exists()


def test_second_write_rotates_the_first_generation_to_prev(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    prev = tmp_path / "state.prev.json"
    durable_write_json(target, {"gen": 1}, retries=_RETRIES, backoff=_BACKOFF)
    assert not prev.exists()
    durable_write_json(target, {"gen": 2}, retries=_RETRIES, backoff=_BACKOFF)
    assert json.loads(target.read_text()) == {"gen": 2}
    assert json.loads(prev.read_text()) == {"gen": 1}


def test_load_missing_file_with_no_prev_raises_filenotfounderror(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_json_with_fallback(tmp_path / "never_written.json")


def test_load_falls_back_to_prev_when_target_is_corrupt(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    durable_write_json(target, {"gen": 1}, retries=_RETRIES, backoff=_BACKOFF)
    durable_write_json(target, {"gen": 2}, retries=_RETRIES, backoff=_BACKOFF)
    target.write_text("{not valid json", encoding="utf-8")
    assert load_json_with_fallback(target) == {"gen": 1}


def test_load_raises_the_primary_error_when_prev_is_also_bad(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    durable_write_json(target, {"gen": 1}, retries=_RETRIES, backoff=_BACKOFF)
    durable_write_json(target, {"gen": 2}, retries=_RETRIES, backoff=_BACKOFF)
    target.write_text("{not valid json", encoding="utf-8")
    (tmp_path / "state.prev.json").write_text("{also not valid", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_json_with_fallback(target)


def test_replace_retries_past_a_transient_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first os.replace() call fails once, then succeeds -- proves the
    retry loop, not just the happy path."""
    import os

    target = tmp_path / "state.json"
    real_replace = os.replace
    calls = {"count": 0}

    def _flaky_replace(src, dst):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PermissionError("simulated transient lock")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", _flaky_replace)
    durable_write_json(target, {"ok": True}, retries=_RETRIES, backoff=_BACKOFF)
    assert load_json_with_fallback(target) == {"ok": True}
    assert calls["count"] == 2


def test_replace_gives_up_after_exhausting_retries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    target = tmp_path / "state.json"

    def _always_locked(src, dst):
        raise PermissionError("simulated persistent lock")

    monkeypatch.setattr(os, "replace", _always_locked)
    with pytest.raises(PermissionError):
        durable_write_json(target, {"ok": True}, retries=1, backoff=_BACKOFF)
