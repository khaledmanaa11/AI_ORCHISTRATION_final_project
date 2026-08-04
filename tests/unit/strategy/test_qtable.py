"""Tests for QTable -- values/visits API, JSON round-trip, fail-loud load
(D-02, D-08). Crash-safety/retry mechanics live in test_qtable_durability.py
(the 150-line gate forced a split, see 03-05-SUMMARY.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pursuit.strategy.qtable import SCHEMA_VERSION, QTable

_KEY_A = "2,3|5,5|9|6|1"
_KEY_B = "0,0|1,1|0|0|0"


def test_unseen_key_returns_zero_value_and_visits() -> None:
    table = QTable()
    assert table.get("nope", 0) == 0.0
    assert table.visits("nope") == 0


def test_set_get_round_trip() -> None:
    table = QTable()
    table.set(_KEY_A, 2, 0.75)
    assert table.get(_KEY_A, 2) == 0.75
    assert table.get(_KEY_A, 0) == 0.0  # untouched action still defaults


def test_copy_is_independent_of_the_original() -> None:
    """03-08's sparring pool snapshots a live table via copy() -- mutating
    either the original or the snapshot afterward must never affect the other."""
    table = QTable()
    table.set(_KEY_A, 0, 1.0)
    table.bump_visit(_KEY_A)
    clone = table.copy()

    table.set(_KEY_A, 0, 99.0)
    table.bump_visit(_KEY_A)
    clone.set(_KEY_B, 1, 5.0)

    assert clone.get(_KEY_A, 0) == 1.0
    assert clone.visits(_KEY_A) == 1
    assert table.get(_KEY_B, 1) == 0.0


def test_bump_visit_increments() -> None:
    table = QTable()
    table.bump_visit(_KEY_A)
    table.bump_visit(_KEY_A)
    assert table.visits(_KEY_A) == 2


def test_best_action_ties_break_to_smallest_index() -> None:
    table = QTable()
    table.set(_KEY_A, 3, 1.0)
    table.set(_KEY_A, 1, 1.0)
    assert table.best_action(_KEY_A) == 1


def test_best_action_on_unseen_key_defaults_to_zero() -> None:
    assert QTable().best_action("unseen") == 0


def test_save_then_load_preserves_values_and_visits(tmp_path: Path) -> None:
    table = QTable()
    table.set(_KEY_A, 0, 0.5)
    table.set(_KEY_A, 4, -0.25)
    table.bump_visit(_KEY_A)
    table.bump_visit(_KEY_A)
    table.set(_KEY_B, 2, 1.0)

    path = tmp_path / "qtable.json"
    table.save(path)
    loaded = QTable.load(path)

    assert loaded.get(_KEY_A, 0) == 0.5
    assert loaded.get(_KEY_A, 4) == -0.25
    assert loaded.visits(_KEY_A) == 2
    assert loaded.get(_KEY_B, 2) == 1.0
    assert loaded.visits(_KEY_B) == 0


def test_load_malformed_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        QTable.load(path)


def test_load_missing_version_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    path.write_text(json.dumps({"table": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="version"):
        QTable.load(path)


def test_load_unknown_action_index_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    payload = {"version": SCHEMA_VERSION, "table": {_KEY_A: {"values": {"9": 1.0}, "visits": 0}}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="action index"):
        QTable.load(path)


def test_load_unparseable_key_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    payload = {"version": SCHEMA_VERSION, "table": {"not-a-valid-key": {"values": {}, "visits": 0}}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        QTable.load(path)


def test_load_non_object_top_level_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        QTable.load(path)


def test_load_missing_table_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    path.write_text(json.dumps({"version": SCHEMA_VERSION}), encoding="utf-8")
    with pytest.raises(ValueError, match="table"):
        QTable.load(path)


def test_load_stale_schema_version_raises(tmp_path: Path) -> None:
    """A run-1-format table (SCHEMA_VERSION - 1) fails loud naming the stale
    version -- this is what makes 03-13's "no migration" safe, not lucky."""
    path = tmp_path / "qtable.json"
    stale_version = SCHEMA_VERSION - 1
    payload = {"version": stale_version, "table": {}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=str(stale_version)):
        QTable.load(path)


def test_load_entry_missing_visits_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    payload = {"version": SCHEMA_VERSION, "table": {_KEY_A: {"values": {}}}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="visits"):
        QTable.load(path)


def test_load_non_integer_action_index_raises(tmp_path: Path) -> None:
    path = tmp_path / "qtable.json"
    payload = {"version": SCHEMA_VERSION, "table": {_KEY_A: {"values": {"abc": 1.0}, "visits": 0}}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="action index"):
        QTable.load(path)
