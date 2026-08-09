"""Tests for the tunnel.json loader (CLOUD-01, D-54, D-55, QUAL-02, QUAL-11)."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.shared.tunnel_config import (
    TunnelKey,
    TunnelParams,
    load_tunnel_config,
    require_env,
)

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICE_TUNNEL = _CONFIG_DIR / "police" / "tunnel.json"
THIEF_TUNNEL = _CONFIG_DIR / "thief" / "tunnel.json"


def _write_variant(tmp_path: Path, mutate) -> Path:
    """Write a mutated copy of the police tunnel.json to tmp_path."""
    data = json.loads(POLICE_TUNNEL.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "tunnel.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def _walk_no_numeric(obj: object, path: str = "$") -> None:
    """D-55: recursively assert no leaf in obj is an int/float (bool included,
    since bool is a subclass of int in Python)."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            _walk_no_numeric(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            _walk_no_numeric(value, f"{path}[{index}]")
    else:
        assert not isinstance(obj, int | float), f"numeric leaf at {path}: {obj!r}"


def test_loads_all_fields() -> None:
    """Every field loads from the real tunnel.json -- no literal in this test."""
    raw = json.loads(POLICE_TUNNEL.read_text(encoding="utf-8"))
    params = load_tunnel_config(POLICE_TUNNEL)
    assert params.version == raw[TunnelKey.VERSION.value]
    assert params.provider == raw[TunnelKey.PROVIDER.value]
    assert params.secret_header == raw[TunnelKey.SECRET_HEADER.value]
    assert params.authtoken_env == raw[TunnelKey.AUTHTOKEN_ENV.value]
    assert params.domain_env == raw[TunnelKey.DOMAIN_ENV.value]
    assert params.secret_env == raw[TunnelKey.SECRET_ENV.value]


def test_params_are_frozen() -> None:
    """TunnelParams is immutable -- assignment raises FrozenInstanceError."""
    params = load_tunnel_config(POLICE_TUNNEL)
    with pytest.raises(FrozenInstanceError):
        params.provider = "localtonet"  # type: ignore[misc]


def test_fresh_object_every_call() -> None:
    """NET-02 precedent: no module-level cache/singleton, ever."""
    a = load_tunnel_config(POLICE_TUNNEL)
    b = load_tunnel_config(POLICE_TUNNEL)
    assert a is not b
    assert a == b


def test_role_files_are_byte_identical() -> None:
    """The Phase-4 config-pair convention: no per-role split for tunnel.json."""
    assert POLICE_TUNNEL.read_bytes() == THIEF_TUNNEL.read_bytes()
    assert load_tunnel_config(POLICE_TUNNEL) == load_tunnel_config(THIEF_TUNNEL)


def test_missing_key_raises(tmp_path: Path) -> None:
    """A missing required key fails loud at load time, never deferred."""
    bad = _write_variant(tmp_path, lambda d: d.pop(TunnelKey.DOMAIN_ENV.value))
    with pytest.raises(KeyError):
        load_tunnel_config(bad)


def test_wrong_type_raises(tmp_path: Path) -> None:
    """A wrong-type value fails loud at load time."""
    bad = _write_variant(tmp_path, lambda d: d.__setitem__(TunnelKey.PROVIDER.value, 7))
    with pytest.raises(TypeError):
        load_tunnel_config(bad)


def test_no_numeric_leaf_in_either_role_file() -> None:
    """D-55: tunnel.json carries only strings -- no reconnect/backoff number
    lives here; those are reused straight from NetworkParams."""
    _walk_no_numeric(json.loads(POLICE_TUNNEL.read_text(encoding="utf-8")))
    _walk_no_numeric(json.loads(THIEF_TUNNEL.read_text(encoding="utf-8")))


def test_require_env_raises_naming_the_missing_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PURSUIT_TEST_TUNNEL_VAR", raising=False)
    with pytest.raises(KeyError, match="PURSUIT_TEST_TUNNEL_VAR"):
        require_env("PURSUIT_TEST_TUNNEL_VAR")


def test_require_env_rejects_a_blank_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PURSUIT_TEST_TUNNEL_VAR", "")
    with pytest.raises(KeyError, match="PURSUIT_TEST_TUNNEL_VAR"):
        require_env("PURSUIT_TEST_TUNNEL_VAR")


def test_require_env_returns_the_set_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PURSUIT_TEST_TUNNEL_VAR", "unit-test-value")
    assert require_env("PURSUIT_TEST_TUNNEL_VAR") == "unit-test-value"


def test_params_type_annotation_matches_dataclass() -> None:
    """Sanity: the loader's declared return type is the dataclass it constructs."""
    params = load_tunnel_config(POLICE_TUNNEL)
    assert isinstance(params, TunnelParams)


def test_tunnel_key_str_returns_the_bare_field_name() -> None:
    """__str__ makes json.dumps({TunnelKey.PROVIDER: ...}) emit 'provider'."""
    assert str(TunnelKey.PROVIDER) == "provider"
