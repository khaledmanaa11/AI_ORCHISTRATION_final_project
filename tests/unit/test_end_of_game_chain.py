"""The game-end chain's construction rules: no live transport builds itself,
and the watchdog is marked per bounded attempt.

The `live` refusal cannot fire from any config this repository ships -- every
`reporting.json` is `dry_run` -- so it is driven here with a `ReportingParams`
whose mode has been flipped in memory. Without that, the branch is a promise
nothing checks, and 07-10 is the step it exists to protect.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from pursuit.services.reporting.end_of_game_chain import (
    LIVE_MODE_UNWIRED,
    QUOTA_FILENAME,
    build_reporting_chain,
    watchdog_touching,
)
from pursuit.shared.reporting_config import (
    REPORTING_CONFIG_SOURCE,
    ReportingMode,
    load_reporting_config,
)

POLICE_CONFIG = Path("config/police")


class CountingWatchdog:
    def __init__(self) -> None:
        self.touches = 0

    def touch(self) -> None:
        self.touches += 1


class OneShotSink:
    def __init__(self, *, fail: bool) -> None:
        self._fail = fail

    async def send(self, report: dict) -> str:
        if self._fail:
            raise RuntimeError("simulated transport failure")
        return "delivered"


@pytest.fixture
def params():
    return load_reporting_config(POLICE_CONFIG / REPORTING_CONFIG_SOURCE)


def test_a_live_config_with_no_injected_transport_is_refused(params, tmp_path):
    """07-10 owns the one supervised live send. Nothing on the game-end path
    may construct a live transport on its own (rules 31, 39-40)."""
    live = dataclasses.replace(params, mode=ReportingMode.LIVE)
    assert live.mode is not ReportingMode.DRY_RUN, "the fixture really is live"

    with pytest.raises(ValueError, match="07-10"):
        build_reporting_chain(
            live, watchdog=CountingWatchdog(), artifact_dir=tmp_path, quota_dir=tmp_path,
        )
    assert "GmailSink" in LIVE_MODE_UNWIRED


def test_a_live_config_with_an_injected_transport_is_allowed(params, tmp_path):
    """The paired control: the refusal is about building one, not about mode."""
    live = dataclasses.replace(params, mode=ReportingMode.LIVE)
    chain = build_reporting_chain(
        live, watchdog=CountingWatchdog(), artifact_dir=tmp_path, quota_dir=tmp_path,
        sink=OneShotSink(fail=False),
    )
    assert chain.pending == 0


def test_the_shipped_config_builds_a_chain_and_names_the_quota_file(params, tmp_path):
    """The quota counter lands beside the run output, NOT in the shipped
    `config/` tree -- `tests/_shipped_config_guard.py` makes that structural."""
    assert params.mode is ReportingMode.DRY_RUN, "every shipped config is dry_run"
    build_reporting_chain(
        params, watchdog=CountingWatchdog(), artifact_dir=tmp_path / "art",
        quota_dir=tmp_path / "run",
    )
    assert QUOTA_FILENAME.endswith(".json")
    assert "config" not in QUOTA_FILENAME


async def test_the_wrapper_touches_on_entry_and_on_the_way_out():
    """Two touches per attempt, success AND failure, which is what bounds the
    gap between marks to one timeout or one backoff rather than their sum."""
    watchdog = CountingWatchdog()
    assert await watchdog_touching(watchdog, OneShotSink(fail=False))({}) == "delivered"
    assert watchdog.touches == 2

    with pytest.raises(RuntimeError):
        await watchdog_touching(watchdog, OneShotSink(fail=True))({})
    assert watchdog.touches == 4, "a FAILED attempt marks activity on its way out too"
