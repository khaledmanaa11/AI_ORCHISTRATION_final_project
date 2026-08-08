"""Integration-only shared fixtures (QUAL-02): built exactly once here, reused
by every §10.4 gate module in tests/integration/. Root tests/conftest.py
fixtures (default_params, network_params, police_network_config) are
inherited automatically and never redefined here.

Every duration, threshold and count used anywhere in this package comes from
NetworkParams -- nothing here is a numeric literal beyond list/tuple indices.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

import pytest
from fastmcp import Client

from pursuit.network.peer_runtime import PeerRuntime
from pursuit.shared.network_config import NetworkParams, load_network_config
from pursuit.shared.strategy_config import StrategyParams, load_strategy_config

_THIEF_NETWORK_CONFIG = (
    pathlib.Path(__file__).parent.parent.parent / "config" / "thief" / "network.json"
)
_CONFIG_ROOT = pathlib.Path(__file__).parent.parent.parent / "config"
_STRATEGY_CONFIG_PATHS = {
    "cop": _CONFIG_ROOT / "police" / "strategy.json",
    "thief": _CONFIG_ROOT / "thief" / "strategy.json",
}


@pytest.fixture
def police_params(network_params: NetworkParams) -> NetworkParams:
    """NetworkParams for the police side -- the root `network_params` fixture
    already loads config/police/network.json; reused here under this
    package's own name rather than rebuilt (QUAL-02)."""
    return network_params


@pytest.fixture
def thief_params() -> NetworkParams:
    """NetworkParams for the thief side, loaded the same way root conftest
    builds the police path: one pathlib constant relative to tests/."""
    return load_network_config(_THIEF_NETWORK_CONFIG)


@pytest.fixture
def peer_pair(
    police_params: NetworkParams, thief_params: NetworkParams
) -> tuple[PeerRuntime, PeerRuntime]:
    """Two independent, socket-free PeerRuntimes (NET-02, NET-03) -- one per
    side, each with the real D-05 tool surface registered via 02-06's own
    factory. Never binds a port, never calls start_server (RESEARCH
    Pattern 5: the in-memory Client(server) transport is the only path a
    test in this package ever uses)."""
    police = PeerRuntime(police_params, "pursuit-police-test")
    thief = PeerRuntime(thief_params, "pursuit-thief-test")
    return police, thief


def client_for(runtime: PeerRuntime) -> Client:
    """An in-memory fastmcp Client aimed at `runtime`'s FastMCP server
    instance (RESEARCH Pattern 5) -- never a URL, never a socket. The caller
    owns the `async with` lifetime; this helper never holds one open."""
    return Client(runtime.server)


@pytest.fixture
def agent_log_paths(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Two distinct per-agent JSONL log paths under tmp_path -- a gate test
    must never write into the repo's real log location."""
    return tmp_path / "police.jsonl", tmp_path / "thief.jsonl"


def read_events(path: pathlib.Path | str) -> list[dict]:
    """Parse a JSONL log written by 02-04's append_event, in order.

    Returns [] when the file does not exist yet -- the single JSONL reader
    every gate module in this package uses (QUAL-02)."""
    resolved = pathlib.Path(path)
    if not resolved.exists():
        return []
    text = resolved.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line]


def recording_sleep():
    """An injected async sleep double for 02-07's `call_with_retry` seam.

    Returns (sleep, durations): `sleep` is an async callable a test passes
    as `call_with_retry(..., sleep=sleep)`; `durations` accumulates every
    requested duration in call order, so a test can assert the exact backoff
    schedule without a single real second elapsing."""
    durations: list[float] = []

    async def _sleep(seconds: float) -> None:
        durations.append(seconds)

    return _sleep, durations


class _SteppingClock:
    """A hand-advanced stand-in for 02-04's `Watchdog(clock=...)` seam."""

    def __init__(self, start: float) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, offset: float) -> None:
        """Move the fake clock forward by exactly `offset` -- always a
        NetworkParams-derived value at the call site, never a new literal."""
        self._now += offset


def stepping_clock(start: float = 0.0) -> _SteppingClock:
    """An injected clock double for 02-04's `Watchdog.check_once()` seam.

    Returns a zero-arg callable (for `Watchdog(clock=...)`) that also
    exposes `.advance(offset)`, so a test can drive the watchdog threshold
    deterministically without a real second of wall-clock passing. `start`
    defaults to `0.0`, the natural monotonic-clock origin, not a game value.
    """
    return _SteppingClock(start)


def strategy_params(
    role: str,
    *,
    brain_class: str | None = None,
) -> StrategyParams:
    """Real per-role `strategy.json` (Phase-3 §10.4 gate tests, QUAL-02) --
    the one construction path `test_strategy_pluggable.py` shares instead of
    re-implementing `load_strategy_config` + `dataclasses.replace`.

    `brain_class` overrides which brain GATE-3 swaps in -- the only config
    field that test exercises; run-2 brains (docs/PRD_matrix_mover.md) need
    no Q-table repointing.
    """
    params = load_strategy_config(_STRATEGY_CONFIG_PATHS[role])
    if brain_class is None:
        return params
    return dataclasses.replace(params, brain_class=brain_class)
