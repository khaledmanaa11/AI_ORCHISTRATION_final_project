"""Tests for the security.json loader (SEC-01, SEC-03, SEC-04, D-65)."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.shared.security_config import (
    SecurityKey,
    SecurityParams,
    load_security_config,
)

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICE_SECURITY = _CONFIG_DIR / "police" / "security.json"
THIEF_SECURITY = _CONFIG_DIR / "thief" / "security.json"


def _write_variant(tmp_path: Path, mutate) -> Path:
    """Write a mutated copy of the police security.json to tmp_path."""
    data = json.loads(POLICE_SECURITY.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "security.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def test_loads_all_fields() -> None:
    """Every field loads from the real security.json -- no literal in this test."""
    raw = json.loads(POLICE_SECURITY.read_text(encoding="utf-8"))
    params = load_security_config(POLICE_SECURITY)
    assert params.version == raw[SecurityKey.VERSION.value]
    assert params.commit_reveal == raw[SecurityKey.COMMIT_REVEAL.value]
    assert params.team_code == raw[SecurityKey.TEAM_CODE.value]


def test_params_are_frozen() -> None:
    """SecurityParams is immutable -- assignment raises FrozenInstanceError."""
    params = load_security_config(POLICE_SECURITY)
    with pytest.raises(FrozenInstanceError):
        params.commit_reveal = False  # type: ignore[misc]


def test_fresh_object_every_call() -> None:
    """NET-02 precedent: no module-level cache/singleton, ever."""
    a = load_security_config(POLICE_SECURITY)
    b = load_security_config(POLICE_SECURITY)
    assert a is not b
    assert a == b


def test_role_files_are_byte_identical() -> None:
    """D-65: commit_reveal + team_code are shared-team, protocol-level facts."""
    assert POLICE_SECURITY.read_bytes() == THIEF_SECURITY.read_bytes()
    assert load_security_config(POLICE_SECURITY) == load_security_config(THIEF_SECURITY)


def test_team_code_is_exactly_eight_characters_no_spaces() -> None:
    """Rule 45 -- checking the shipped value, not inventing a rule."""
    params = load_security_config(POLICE_SECURITY)
    assert len(params.team_code) == 8
    assert " " not in params.team_code


def test_missing_key_raises(tmp_path: Path) -> None:
    """A missing required key fails loud at load time, naming it."""
    bad = _write_variant(tmp_path, lambda d: d.pop(SecurityKey.TEAM_CODE.value))
    with pytest.raises(KeyError, match=SecurityKey.TEAM_CODE.value):
        load_security_config(bad)


def test_commit_reveal_wrong_type_int_raises(tmp_path: Path) -> None:
    """SEC-04 pitfall: bool is an int subtype -- but so is a plain int (1)."""
    bad = _write_variant(tmp_path, lambda d: d.__setitem__(SecurityKey.COMMIT_REVEAL.value, 1))
    with pytest.raises(TypeError):
        load_security_config(bad)


def test_commit_reveal_wrong_type_string_raises(tmp_path: Path) -> None:
    bad = _write_variant(
        tmp_path, lambda d: d.__setitem__(SecurityKey.COMMIT_REVEAL.value, "true")
    )
    with pytest.raises(TypeError):
        load_security_config(bad)


def test_missing_file_raises_file_not_found() -> None:
    """Propagates unchanged, never swallowed into a default."""
    with pytest.raises(FileNotFoundError):
        load_security_config(Path("does/not/exist/security.json"))


def test_params_type_annotation_matches_dataclass() -> None:
    """Sanity: the loader's declared return type is the dataclass it constructs."""
    params = load_security_config(POLICE_SECURITY)
    assert isinstance(params, SecurityParams)


def test_security_key_str_returns_the_bare_field_name() -> None:
    """__str__ makes json.dumps({SecurityKey.TEAM_CODE: ...}) emit 'team_code'."""
    assert str(SecurityKey.TEAM_CODE) == "team_code"
