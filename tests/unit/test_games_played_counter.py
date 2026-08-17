"""07-00 -- rule 37/38 (`docs/RULES.md:79`): the games-played counter must be
incremented ONCE, AT GAME END, PER COMPLETED GAME. Rule 38 makes a false
declaration of that number an ABSOLUTE DISQUALIFICATION, so WHEN the
increment happens is the entire subject of this file.

DEFECT 1 -- WRONG MOMENT -- MEASURED AT HEAD `de32c0b` BEFORE ANY FIX.
`step0_collect.record_game_played`'s own docstring reads "increment by
exactly one, durably, at game end only". Its single production caller was
the LAST LINE of `write_declaration` (`agent_step0_wiring.py:93`), which
runs inside the Step-0 DECLARATION path -- immediately after an agreed
handshake and BEFORE `run_turn_loop` is entered at all. Everything that
reached an agreed handshake was therefore counted as a game played: a run
the freeze watchdog `os._exit(1)`s at move 3, a Ctrl-C, a gate measurement
script, an integration test that exercises only the declaration.

Reproduced below with a throwaway config directory seeded at 7:
`test_write_declaration_does_not_touch_the_counter` measured **7 -> 8** at
HEAD, for a call that plays no game whatsoever.

The same three exits driven END TO END through the real `run_agent` live in
the sibling `test_games_played_at_game_end.py`, split off at the 150-line
gate; it imports `_SEED` and `_seeded` from here so the two files cannot
drift on what a seeded config directory is.

The SCOPE half of the same defect -- that a `pytest` run writes the SHIPPED
counter -- is measured in `test_shipped_counter_isolation.py`.
"""

from __future__ import annotations

import json
import shutil

import pytest

from pursuit.constants import Outcome
from pursuit.network import agent_step0_wiring
from pursuit.security import step0_collect
from tests import _shipped_config_guard as guard

_GAME_PARAMS = guard.SHIPPED_CONFIG_ROOT / "police" / "game_params.json"
"""Copied into every throwaway config dir because `run_agent` digests it at
`agent_entrypoint.py:80`. Copied, never read in place: a test that pointed
`cfg.config_dir` at the real tree is the defect this file exists to remove."""

_SEED = 7
"""An arbitrary non-zero start, so a fix that resets or zeroes the file is
as visible as one that increments it at the wrong moment."""

_ALL_OUTCOMES = tuple(Outcome)


class _Cfg:
    def __init__(self, config_dir):
        self.config_dir = config_dir


class _Ctx:
    def __init__(self, log_path):
        self.role = "police"
        self.game_uid = "0" * 16
        self.log_path = log_path


class _Result:
    peer_game_id = None
    peer_step0_declaration = None


def _seeded(tmp_path):
    """A throwaway config dir holding a counter at `_SEED`, plus a log dir."""
    config_dir, log_dir = tmp_path / "config", tmp_path / "logs"
    config_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(_GAME_PARAMS, config_dir / _GAME_PARAMS.name)
    counter = config_dir / agent_step0_wiring._COUNTER_FILENAME
    counter.write_text(json.dumps({"games_played": _SEED}), encoding="utf-8")
    return config_dir, log_dir, counter


def test_write_declaration_does_not_touch_the_counter(tmp_path):
    """DEFECT 1. Persisting the Step-0 declaration is a game START event:
    it happens before move 1 and proves nothing about a game being played.
    RED at HEAD -- measured 7 -> 8.

    The declaration-file assertion is the non-vacuity control: without it a
    `write_declaration` that did nothing at all would also pass."""
    config_dir, log_dir, counter = _seeded(tmp_path)
    ctx, cfg = _Ctx(log_dir / "game.jsonl"), _Cfg(config_dir)

    agent_step0_wiring.write_declaration(ctx, cfg, _Result(), {"declaration": {}})

    assert list(log_dir.glob("declaration_*.json")), "write_declaration did not run"
    assert step0_collect.read_games_played(counter) == _SEED


def test_the_outcome_sweep_is_not_vacuous():
    """An empty `parametrize` list makes pytest SKIP silently, so the sweep
    below would "pass" having asserted nothing. Pinned against the three
    outcomes a real game can end on."""
    assert len(_ALL_OUTCOMES) > 0
    assert {Outcome.CAPTURE, Outcome.SURVIVAL, Outcome.TECHNICAL_LOSS} <= set(_ALL_OUTCOMES)


@pytest.mark.parametrize("outcome", _ALL_OUTCOMES)
def test_a_completed_game_records_exactly_one(tmp_path, outcome):
    """Every outcome a game can END on is a game played -- including
    TECHNICAL_LOSS, which is a game this side lost, not a game it skipped."""
    config_dir, _, counter = _seeded(tmp_path)

    agent_step0_wiring.record_completed_game(_Cfg(config_dir), outcome)

    assert step0_collect.read_games_played(counter) == _SEED + 1


def test_a_game_that_never_produced_an_outcome_records_nothing(tmp_path):
    """The other direction, and the one rule 38 punishes: `run_turn_loop`
    returns None when no leg ever produced an outcome, and on that path no
    `game_over` record is written either. Nothing was played, so nothing is
    counted."""
    config_dir, _, counter = _seeded(tmp_path)

    agent_step0_wiring.record_completed_game(_Cfg(config_dir), None)

    assert step0_collect.read_games_played(counter) == _SEED
