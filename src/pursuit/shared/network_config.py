"""Fail-loud config loader for network.json (D-04, NET-01, NET-02).

load_network_config() is the single entry point for every Phase-2 endpoint and
resilience number. Every required key and type is validated at load time; host,
port and opponent_url are additionally overridable from the environment (D-16).
A fresh NetworkParams is returned on every call — never a module-level singleton
— so the police and thief processes never share a live config object (NET-02).
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from pursuit.config_keys import NetworkConfigKey
from pursuit.shared.loader_helpers import require_int, require_str

NETWORK_CONFIG_SOURCE = "network.json"


@dataclass(frozen=True)
class NetworkParams:
    """Typed, immutable container for all values read from network.json.

    Constructed only by load_network_config() — callers never build this directly.
    """

    host: str
    port: int
    opponent_url: str
    response_timeout: int
    watchdog_threshold: int
    retry_count: int
    backoff_seconds: int
    watchdog_poll_seconds: int


def _env_str(current: str, var_name: str) -> str:
    """Return the environment override for var_name, or current if unset/empty."""
    raw = os.environ.get(var_name)
    return raw if raw else current


def _env_int(current: int, var_name: str) -> int:
    """Return the environment override for var_name parsed as int, or current.

    Raises
    ------
    ValueError
        If var_name is set but does not parse as an int.
    """
    raw = os.environ.get(var_name)
    if not raw:
        return current
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {var_name} must be an integer, got {raw!r}"
        ) from exc


def load_network_config(path: "Path | str") -> NetworkParams:
    """Load and validate network parameters from a network.json file.

    Parameters
    ----------
    path:
        Filesystem path to a JSON file matching the network.json schema.

    Returns
    -------
    NetworkParams
        Fully-populated, immutable, freshly-constructed parameters object.

    Raises
    ------
    KeyError
        If any required key is absent from the file.
    TypeError
        If any field carries the wrong type in the file.
    ValueError
        If an environment override value cannot be parsed (e.g. a non-integer
        PURSUIT_PORT).
    """
    with Path(path).open() as fh:
        data = json.load(fh)

    host = require_str(data, NetworkConfigKey.HOST, source=NETWORK_CONFIG_SOURCE)
    port = require_int(data, NetworkConfigKey.PORT, source=NETWORK_CONFIG_SOURCE)
    opponent_url = require_str(
        data, NetworkConfigKey.OPPONENT_URL, source=NETWORK_CONFIG_SOURCE
    )
    response_timeout = require_int(
        data, NetworkConfigKey.RESPONSE_TIMEOUT, source=NETWORK_CONFIG_SOURCE
    )
    watchdog_threshold = require_int(
        data, NetworkConfigKey.WATCHDOG_THRESHOLD, source=NETWORK_CONFIG_SOURCE
    )
    retry_count = require_int(
        data, NetworkConfigKey.RETRY_COUNT, source=NETWORK_CONFIG_SOURCE
    )
    backoff_seconds = require_int(
        data, NetworkConfigKey.BACKOFF_SECONDS, source=NETWORK_CONFIG_SOURCE
    )
    watchdog_poll_seconds = require_int(
        data, NetworkConfigKey.WATCHDOG_POLL_SECONDS, source=NETWORK_CONFIG_SOURCE
    )

    # D-16: environment overrides applied after file validation.
    host = _env_str(host, NetworkConfigKey.ENV_HOST)
    port = _env_int(port, NetworkConfigKey.ENV_PORT)
    opponent_url = _env_str(opponent_url, NetworkConfigKey.ENV_OPPONENT_URL)

    return NetworkParams(
        host=host,
        port=port,
        opponent_url=opponent_url,
        response_timeout=response_timeout,
        watchdog_threshold=watchdog_threshold,
        retry_count=retry_count,
        backoff_seconds=backoff_seconds,
        watchdog_poll_seconds=watchdog_poll_seconds,
    )
