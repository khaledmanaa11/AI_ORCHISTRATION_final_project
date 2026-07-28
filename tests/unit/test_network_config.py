"""Stub tests for plan 02-01 (network config loader). NET-01, NET-02, QUAL-02."""

import pytest


def test_loads_host_port_opponent_url():
    """Loader returns host/port/opponent_url from network.json."""
    pytest.skip("stub — implemented in plan 02-01")


def test_loads_timeout_threshold_retry_backoff():
    """Loader returns response_timeout/watchdog_threshold/retry_count/backoff_seconds."""
    pytest.skip("stub — implemented in plan 02-01")


def test_loads_watchdog_poll_seconds():
    """Loader returns watchdog_poll_seconds (D-18)."""
    pytest.skip("stub — implemented in plan 02-01")


def test_missing_key_raises():
    """A network.json missing a required key fails loud, not silently."""
    pytest.skip("stub — implemented in plan 02-01")


def test_non_int_port_raises():
    """A non-integer port value fails loud at load time."""
    pytest.skip("stub — implemented in plan 02-01")


def test_env_var_overrides_port():
    """PURSUIT_PORT env var overrides the config file value (D-16)."""
    pytest.skip("stub — implemented in plan 02-01")


def test_police_and_thief_configs_differ_only_in_endpoint():
    """Loaded police and thief configs differ only in port and opponent_url."""
    pytest.skip("stub — implemented in plan 02-01")
