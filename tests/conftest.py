"""Shared pytest fixtures for all test waves."""

import pathlib

import pytest

from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.state import GameState

_POLICE_CONFIG = (
    pathlib.Path(__file__).parent.parent / "config" / "police" / "game_params.json"
)
_POLICE_NETWORK_CONFIG = (
    pathlib.Path(__file__).parent.parent / "config" / "police" / "network.json"
)


@pytest.fixture(scope="session", autouse=True)
def _shipped_config_is_off_limits():
    """07-00, rules 37/38: no test may advance the shipped games-played
    counter. STRUCTURAL and AUTOUSE -- not a request that individual tests
    be careful, which is what failed for the whole of Phase 6.

    Two independent halves, deliberately. The PATCH fails loudly at the
    instant of the attempt, naming the offending path while the failing
    test is still on the stack. The SNAPSHOT re-reads both real files at
    session end, so a write arriving through some binding the patch does
    not cover is still caught -- later and with less context, but caught
    rather than shipped. See `tests/_shipped_config_guard.py` for why the
    guard raises instead of redirecting.

    Imported inside the body, matching `network_params` below: a
    module-level import of a sibling would couple collection of the entire
    suite to it."""
    from pursuit.security import step0_collect
    from tests import _shipped_config_guard as guard

    before = guard.read_counters()
    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(
            step0_collect, "durable_write_json", guard.guarded(step0_collect.durable_write_json),
        )
        yield
    after = guard.read_counters()
    assert after == before, (
        f"the test suite advanced the shipped games-played counter: {before} -> {after}. "
        "Only a real completed game may do that (docs/RULES.md:79, rule 38)."
    )


@pytest.fixture(scope="session")
def default_params() -> GameParams:
    """Load and return the canonical game parameters from config/police/game_params.json."""
    return load_game_params(_POLICE_CONFIG)


@pytest.fixture
def start_state(default_params: GameParams) -> GameState:
    """Return the canonical initial GameState drawn from default_params.

    Values come from default_params only — no hardcoded numbers.
    """
    return GameState(
        cop=default_params.cop_start,
        thief=default_params.thief_start,
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )


@pytest.fixture
def police_network_config() -> pathlib.Path:
    """Path to config/police/network.json (Waves 1-5 read or copy it)."""
    return _POLICE_NETWORK_CONFIG


@pytest.fixture
def network_params():
    """Load config/police/network.json through the Phase-2 loader.

    The import is deliberately INSIDE the fixture body: plan 02-01 creates
    pursuit.shared.network_config, and a module-level import here would break
    collection of the entire suite until then. Only tests that actually request
    this fixture pay the import.
    """
    from pursuit.shared.network_config import load_network_config

    return load_network_config(_POLICE_NETWORK_CONFIG)
