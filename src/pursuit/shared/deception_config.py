"""Fail-loud config loader for deception.json (D-37, D-38).

**Every number in this file is an ENGINEERING DEFAULT, not a book value.**
Nothing in `docs/PARAMETERS.md` fixes a lie rate, a danger threshold or a
truth floor -- the book leaves the deception policy to the team -- so these
are labelled as such here and are meant to be tuned in test games. D-18's
numeric-sourcing discipline cuts both ways: inventing a number and calling it
a parameter is the violation, declaring one and calling it a default is not.

`DeceptionKey` lives beside its loader rather than in `pursuit.config_keys`,
for the reason 04-PLAN-OUTLINE.md Sec4 records: `config_keys.py` is already at
90 of its 150 permitted code lines and four phase-4 key enums would breach
the hard gate. Every other phase-4 config loader follows the same pattern.

`deception.json` is a separate negotiated block, NOT fields inside
`game_params.json`: rule 11 requires `game_params.json` to be byte-identical
with a book-faithful peer, so adding fields there would abort every league
game before move 1 (RULES-RESOLUTION.md Sec5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.shared.loader_helpers import require_float, require_int, require_key

DECEPTION_CONFIG_SOURCE = "deception.json"


class DeceptionKey(str, Enum):
    """Field names for config/{police,thief}/deception.json. Structural only
    -- no numeric literal lives on this enum (D-05 discipline)."""

    VERSION = "version"
    GROUP_THIEF = "thief"
    TRUTH_FLOOR = "truth_floor"
    MIN_LIE_PROBABILITY = "min_lie_probability"
    DANGER_DISTANCE = "danger_distance"
    SAFE_DISTANCE = "safe_distance"
    LIE_CANDIDATE_POOL = "lie_candidate_pool"
    GROUP_COP = "cop"
    MIN_HERDING_GAIN = "min_herding_gain"


@dataclass(frozen=True)
class DeceptionParams:
    """Typed, immutable container for deception.json.

    Constructed only by `load_deception_config()` -- a fresh instance every
    call, never a shared live object, so the police and thief processes can
    never leak state through it (CLAUDE.md rule 2).
    """

    version: str
    truth_floor: float
    min_lie_probability: float
    danger_distance: float
    safe_distance: float
    lie_candidate_pool: int
    min_herding_gain: float

    @property
    def max_lie_probability(self) -> float:
        """The ceiling the truth floor implies.

        Derived, never configured twice: a separate `max_lie_probability` key
        could be set inconsistently with `truth_floor`, and then D-37's
        "truths are sprinkled even at maximum danger" would hold in one
        number and not the other.
        """
        return 1.0 - self.truth_floor


def load_deception_config(path: Path | str) -> DeceptionParams:
    """Load and validate config/{police,thief}/deception.json.

    Raises
    ------
    KeyError
        If any required key (top-level or in `thief`/`cop`) is absent.
    TypeError
        If any leaf value carries the wrong type.
    ValueError
        If `truth_floor` is not in (0, 1) -- a zero floor makes the agent
        always-lying at maximum danger, which collapses the opponent's
        reliability coefficient and makes our channel worthless (D-37); if
        `min_lie_probability` exceeds the ceiling `truth_floor` implies; if
        `danger_distance` is not below `safe_distance`; if
        `lie_candidate_pool` is below 1; or if `min_herding_gain` is
        negative.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)

    version = str(require_key(data, DeceptionKey.VERSION.value, source=DECEPTION_CONFIG_SOURCE))
    thief = require_key(data, DeceptionKey.GROUP_THIEF.value, source=DECEPTION_CONFIG_SOURCE)
    cop = require_key(data, DeceptionKey.GROUP_COP.value, source=DECEPTION_CONFIG_SOURCE)

    params = DeceptionParams(
        version=version,
        truth_floor=_float(thief, DeceptionKey.TRUTH_FLOOR),
        min_lie_probability=_float(thief, DeceptionKey.MIN_LIE_PROBABILITY),
        danger_distance=_float(thief, DeceptionKey.DANGER_DISTANCE),
        safe_distance=_float(thief, DeceptionKey.SAFE_DISTANCE),
        lie_candidate_pool=require_int(
            thief, DeceptionKey.LIE_CANDIDATE_POOL.value, source=DECEPTION_CONFIG_SOURCE
        ),
        min_herding_gain=_float(cop, DeceptionKey.MIN_HERDING_GAIN),
    )
    _validate(params)
    return params


def _float(group: dict, key: DeceptionKey) -> float:
    """`group[key]` as a float, naming deception.json on any failure."""
    return require_float(group, key.value, source=DECEPTION_CONFIG_SOURCE)


def _validate(params: DeceptionParams) -> None:
    """Raise ValueError naming the offending field; see load_deception_config."""
    if not 0.0 < params.truth_floor < 1.0:
        raise ValueError(
            f"{DECEPTION_CONFIG_SOURCE}: 'truth_floor' must be in (0, 1), "
            f"got {params.truth_floor}"
        )
    if not 0.0 <= params.min_lie_probability <= params.max_lie_probability:
        raise ValueError(
            f"{DECEPTION_CONFIG_SOURCE}: 'min_lie_probability' must be in "
            f"[0, {params.max_lie_probability}] (the ceiling 'truth_floor' implies), "
            f"got {params.min_lie_probability}"
        )
    if not 0.0 <= params.danger_distance < params.safe_distance:
        raise ValueError(
            f"{DECEPTION_CONFIG_SOURCE}: need 0 <= 'danger_distance' "
            f"({params.danger_distance}) < 'safe_distance' ({params.safe_distance})"
        )
    if params.lie_candidate_pool < 1:
        raise ValueError(
            f"{DECEPTION_CONFIG_SOURCE}: 'lie_candidate_pool' must be >= 1, "
            f"got {params.lie_candidate_pool}"
        )
    if params.min_herding_gain < 0.0:
        raise ValueError(
            f"{DECEPTION_CONFIG_SOURCE}: 'min_herding_gain' must be >= 0, "
            f"got {params.min_herding_gain}"
        )
