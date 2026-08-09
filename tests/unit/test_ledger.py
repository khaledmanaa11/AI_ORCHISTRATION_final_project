"""Tests for ledger.py (D-64: durable per-turn nonce ledger)."""

import json
from pathlib import Path

import pytest

from pursuit.security.ledger import CommitLedger, LedgerField


def test_append_then_read_all_reproduces_the_exact_record(tmp_path: Path) -> None:
    ledger = CommitLedger(tmp_path / "g1.ledger.jsonl")
    payload = {"state": {"turn": 1}, "move": {"move": {"kind": "move", "direction": "north"}}, "intent": "truth", "nonce": "abc123"}

    ledger.append(turn=1, h_commit="deadbeef", payload=payload)
    records = ledger.read_all()

    assert records == [
        {LedgerField.TURN: 1, LedgerField.H_COMMIT: "deadbeef", LedgerField.PAYLOAD: payload}
    ]
    assert records[0][LedgerField.PAYLOAD]["nonce"] == "abc123"


def test_multiple_turns_append_as_multiple_jsonl_lines(tmp_path: Path) -> None:
    path = tmp_path / "g1.ledger.jsonl"
    ledger = CommitLedger(path)

    for turn in range(3):
        ledger.append(turn=turn, h_commit=f"hash{turn}", payload={"nonce": f"n{turn}"})

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3

    records = ledger.read_all()
    assert [r[LedgerField.TURN] for r in records] == [0, 1, 2]
    assert [r[LedgerField.PAYLOAD]["nonce"] for r in records] == ["n0", "n1", "n2"]


def test_read_all_on_nonexistent_path_returns_empty_list(tmp_path: Path) -> None:
    ledger = CommitLedger(tmp_path / "never_written.ledger.jsonl")
    assert ledger.read_all() == []


def test_read_all_surfaces_malformed_line_as_json_decode_error(tmp_path: Path) -> None:
    path = tmp_path / "g1.ledger.jsonl"
    path.write_text("not-json-at-all\n", encoding="utf-8")
    ledger = CommitLedger(path)

    with pytest.raises(json.JSONDecodeError):
        ledger.read_all()


def test_append_accepts_str_or_path(tmp_path: Path) -> None:
    ledger = CommitLedger(str(tmp_path / "g1.ledger.jsonl"))
    ledger.append(turn=0, h_commit="h", payload={"nonce": "n"})
    assert ledger.read_all()[0][LedgerField.TURN] == 0
