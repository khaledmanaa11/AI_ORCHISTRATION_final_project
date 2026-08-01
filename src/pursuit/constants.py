"""Structural constants and enumerations for the pursuit engine.

No numeric game values live here (D-07). All game numbers are in game_params.json.
Config key string constants (ConfigKey/NetworkConfigKey/StrategyKey/TrainingKey)
live in pursuit.config_keys — split out there at the 03-07 150-code-line ceiling;
this module keeps only game-domain enums and the Action<->Direction helpers.
"""

from enum import Enum, IntEnum


class Direction(Enum):
    """Orthogonal movement directions plus stay-in-place.

    Each value is a (row_delta, col_delta) tuple.
    NORTH decrements the row (top-left origin), SOUTH increments.
    """

    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST = (0, 1)
    WEST = (0, -1)
    STAY = (0, 0)


class CellState(Enum):
    """Possible contents of a board cell."""

    EMPTY = "empty"
    BARRIER = "barrier"
    COP = "cop"
    THIEF = "thief"


class Outcome(Enum):
    """All four game outcomes (D-14).

    Phase 1 only produces CAPTURE and SURVIVAL.
    TIE is a series aggregate (Phase 8).
    TECHNICAL_LOSS is triggered by crypto audit / false declaration (Phase 6-7).
    """

    CAPTURE = "capture"
    SURVIVAL = "survival"
    TIE = "tie"
    TECHNICAL_LOSS = "technical_loss"


class MoveSource(str, Enum):
    """Decision.source provenance (AI-SPEC Sec5 E2/E3); never defaults to QTABLE."""

    QTABLE = "qtable"
    FALLBACK = "fallback"
    HEURISTIC = "heuristic"


class Action(IntEnum):
    """Canonical 5-action space (STRAT-01); order is FROZEN -- never renumber."""

    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3
    STAY = 4


def cell_for(action: Action, own_cell: tuple[int, int]) -> tuple[int, int]:
    """Return the cell reached by taking action from own_cell."""
    row_delta, col_delta = Direction[action.name].value
    return (own_cell[0] + row_delta, own_cell[1] + col_delta)


def action_for(own_cell: tuple[int, int], dest: tuple[int, int]) -> Action:
    """Return the Action from own_cell to dest; raises ValueError if not adjacent."""
    delta = (dest[0] - own_cell[0], dest[1] - own_cell[1])
    for action in Action:
        if Direction[action.name].value == delta:
            return action
    raise ValueError(f"No Action maps {own_cell} to {dest} (delta {delta})")
