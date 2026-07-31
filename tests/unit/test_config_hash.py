"""Tests for the NET-09 canonical-JSON config digest (D-08, D-15)."""

import hashlib
import json
from pathlib import Path

import pytest

from pursuit.network.config_hash import canonical_json, config_digest, digests_match


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_police_and_thief_configs_digest_equal():
    """THE NET-09 gate test, run against the real repo files."""
    police = Path(__file__).parents[2] / "config" / "police" / "game_params.json"
    thief = Path(__file__).parents[2] / "config" / "thief" / "game_params.json"
    assert config_digest(police) == config_digest(thief)


def test_key_order_difference_hashes_equal(tmp_path):
    """THE point of canonicalisation (RESEARCH Pitfall 5)."""
    a = _write(tmp_path, "a.json", json.dumps({"a": 1, "b": 2}, indent=2) + "\n")
    b = _write(
        tmp_path, "b.json", json.dumps({"b": 2, "a": 1}, separators=(",", ":"))
    )
    assert a.read_bytes() != b.read_bytes()
    assert config_digest(a) == config_digest(b)


def test_one_key_difference_hashes_unequal(tmp_path):
    a = _write(tmp_path, "a.json", json.dumps({"a": 1, "b": 2}))
    b = _write(tmp_path, "b.json", json.dumps({"a": 1, "b": 3}))
    c = _write(tmp_path, "c.json", json.dumps({"a": 1}))
    assert config_digest(a) != config_digest(b)
    assert config_digest(a) != config_digest(c)


def test_nested_key_order_difference_hashes_equal(tmp_path):
    # game_params.json has a nested "scoring" object; canonicalisation must
    # sort recursively. List order stays significant (scoring is [cop, thief]).
    a = _write(
        tmp_path,
        "a.json",
        json.dumps({"scoring": {"capture": [1, 2], "tie": [3, 4]}}),
    )
    b = _write(
        tmp_path,
        "b.json",
        json.dumps({"scoring": {"tie": [3, 4], "capture": [1, 2]}}),
    )
    assert config_digest(a) == config_digest(b)


def test_list_order_is_significant(tmp_path):
    # Guards against over-eager canonicalisation sorting arrays, which would
    # silently equate the cop's score with the thief's.
    a = _write(tmp_path, "a.json", json.dumps({"capture": [20, 5]}))
    b = _write(tmp_path, "b.json", json.dumps({"capture": [5, 20]}))
    assert config_digest(a) != config_digest(b)


def test_digest_is_lowercase_sha256_hex(tmp_path):
    p = _write(tmp_path, "a.json", json.dumps({"a": 1}))
    d = config_digest(p)
    assert len(d) == len(hashlib.sha256(b"").hexdigest())
    assert d == d.lower()
    assert all(c in "0123456789abcdef" for c in d)


def test_canonical_json_form():
    # Pins the SEC-03 form exactly: keys sorted, no whitespace after ',' or ':'.
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        config_digest(tmp_path / "nope.json")


def test_malformed_json_raises(tmp_path):
    p = _write(tmp_path, "bad.json", "{not json")
    with pytest.raises(ValueError):
        config_digest(p)


def test_digests_match():
    police = Path(__file__).parents[2] / "config" / "police" / "game_params.json"
    d = config_digest(police)
    assert digests_match(d, d) is True
    flipped = d[:-1] + ("0" if d[-1] != "0" else "1")
    assert digests_match(d, flipped) is False
    with pytest.raises(TypeError):
        digests_match(d, None)
