"""Tests for the network config loader (NET-01, NET-02, QUAL-02, QUAL-11)."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pursuit.constants import NetworkConfigKey
from pursuit.shared.network_config import NetworkParams, load_network_config

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICE_NETWORK = _CONFIG_DIR / "police" / "network.json"
THIEF_NETWORK = _CONFIG_DIR / "thief" / "network.json"


def _write_variant(tmp_path: Path, mutate) -> Path:
    """Write a mutated copy of the police network.json to tmp_path."""
    data = json.loads(POLICE_NETWORK.read_text(encoding="utf-8"))
    mutate(data)
    target = tmp_path / "network.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def test_loads_all_fields() -> None:
    """Every field loads from the real network.json — no literal in this test."""
    raw = json.loads(POLICE_NETWORK.read_text(encoding="utf-8"))
    params = load_network_config(POLICE_NETWORK)
    assert params.host == raw[NetworkConfigKey.HOST]
    assert params.port == raw[NetworkConfigKey.PORT]
    assert params.opponent_url == raw[NetworkConfigKey.OPPONENT_URL]
    assert params.response_timeout == raw[NetworkConfigKey.RESPONSE_TIMEOUT]
    assert params.watchdog_threshold == raw[NetworkConfigKey.WATCHDOG_THRESHOLD]
    assert params.retry_count == raw[NetworkConfigKey.RETRY_COUNT]
    assert params.backoff_seconds == raw[NetworkConfigKey.BACKOFF_SECONDS]
    assert params.watchdog_poll_seconds == raw[NetworkConfigKey.WATCHDOG_POLL_SECONDS]


def test_field_types() -> None:
    """Loaded fields carry the correct Python types."""
    params = load_network_config(POLICE_NETWORK)
    assert isinstance(params.host, str)
    assert isinstance(params.opponent_url, str)
    assert isinstance(params.port, int)
    assert isinstance(params.response_timeout, int)
    assert isinstance(params.watchdog_threshold, int)
    assert isinstance(params.retry_count, int)
    assert isinstance(params.backoff_seconds, int)
    assert isinstance(params.watchdog_poll_seconds, int)


def test_params_are_frozen() -> None:
    """NetworkParams is immutable — assignment raises FrozenInstanceError."""
    params = load_network_config(POLICE_NETWORK)
    with pytest.raises(FrozenInstanceError):
        params.port = 9999  # type: ignore[misc]


def test_agents_get_independent_objects() -> None:
    """NET-02: no shared runtime object between police and thief configs."""
    police = load_network_config(POLICE_NETWORK)
    thief = load_network_config(THIEF_NETWORK)
    assert police is not thief
    assert police.port != thief.port
    assert load_network_config(POLICE_NETWORK) is not police


def test_fixture_matches_direct_load(network_params: NetworkParams) -> None:
    """conftest's network_params fixture (02-00) matches a direct police load."""
    assert network_params.port == load_network_config(POLICE_NETWORK).port


def test_missing_key_raises(tmp_path: Path) -> None:
    """A missing required key fails loud at load time, never deferred."""
    bad = _write_variant(tmp_path, lambda d: d.pop(NetworkConfigKey.PORT))
    with pytest.raises(KeyError):
        load_network_config(bad)


def test_wrong_type_raises(tmp_path: Path) -> None:
    """A wrong-type value fails loud at load time."""
    bad = _write_variant(
        tmp_path, lambda d: d.__setitem__(NetworkConfigKey.PORT, "eight")
    )
    with pytest.raises(TypeError):
        load_network_config(bad)


def test_missing_watchdog_poll_raises(tmp_path: Path) -> None:
    """D-18: watchdog_poll_seconds is required, never silently defaulted."""
    bad = _write_variant(
        tmp_path, lambda d: d.pop(NetworkConfigKey.WATCHDOG_POLL_SECONDS)
    )
    with pytest.raises(KeyError):
        load_network_config(bad)


def test_env_overrides_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-16: PURSUIT_PORT overrides the file value."""
    base = load_network_config(POLICE_NETWORK)
    monkeypatch.setenv(NetworkConfigKey.ENV_PORT, str(base.port + 1))
    assert load_network_config(POLICE_NETWORK).port == base.port + 1


def test_env_overrides_host_and_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-16: PURSUIT_HOST and PURSUIT_OPPONENT_URL override the file values."""
    monkeypatch.setenv(NetworkConfigKey.ENV_HOST, "test.invalid")
    monkeypatch.setenv(NetworkConfigKey.ENV_OPPONENT_URL, "http://test.invalid/mcp")
    params = load_network_config(POLICE_NETWORK)
    assert params.host == "test.invalid"
    assert params.opponent_url == "http://test.invalid/mcp"


def test_bad_env_port_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-integer PURSUIT_PORT fails loud rather than silently falling back."""
    monkeypatch.setenv(NetworkConfigKey.ENV_PORT, "not-a-port")
    with pytest.raises(ValueError):
        load_network_config(POLICE_NETWORK)


def test_no_env_leaves_file_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no override env vars set, the file value passes through unchanged."""
    monkeypatch.delenv(NetworkConfigKey.ENV_PORT, raising=False)
    monkeypatch.delenv(NetworkConfigKey.ENV_HOST, raising=False)
    monkeypatch.delenv(NetworkConfigKey.ENV_OPPONENT_URL, raising=False)
    raw = json.loads(POLICE_NETWORK.read_text(encoding="utf-8"))
    assert load_network_config(POLICE_NETWORK).port == raw[NetworkConfigKey.PORT]
