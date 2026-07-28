"""Tests for the shared fail-loud JSON validation helpers (QUAL-02).

These helpers were extracted from src/pursuit/shared/config.py's private
_require_key/_require_int pair when network_config.py became the second
consumer. require_str is new — it has no Phase-1 original.
"""

import pytest
from pursuit.shared.loader_helpers import require_int, require_key, require_str


def test_require_key_returns_value() -> None:
    """require_key returns the value when the key is present."""
    assert require_key({"a": 1}, "a", source="x.json") == 1


def test_require_key_missing_raises() -> None:
    """require_key raises KeyError naming the source file, not a hardcoded filename."""
    with pytest.raises(KeyError) as excinfo:
        require_key({}, "a", source="x.json")
    assert "x.json" in str(excinfo.value)


def test_require_int_returns_int() -> None:
    """require_int returns the int value (3 here is an arbitrary fixture value)."""
    value = require_int({"n": 3}, "n", source="x.json")
    assert value == 3
    assert isinstance(value, int)


def test_require_int_wrong_type_raises() -> None:
    """require_int raises TypeError naming both the source and the field."""
    with pytest.raises(TypeError) as excinfo:
        require_int({"n": "three"}, "n", source="x.json")
    assert "x.json" in str(excinfo.value)
    assert "n" in str(excinfo.value)


def test_require_int_missing_raises() -> None:
    """require_int's missing-key check runs before the type check."""
    with pytest.raises(KeyError):
        require_int({}, "n", source="x.json")


def test_require_str_returns_str() -> None:
    """require_str returns the str value."""
    assert require_str({"s": "v"}, "s", source="x.json") == "v"


def test_require_str_wrong_type_raises() -> None:
    """require_str raises TypeError when the value is not a str."""
    with pytest.raises(TypeError):
        require_str({"s": 1}, "s", source="x.json")
