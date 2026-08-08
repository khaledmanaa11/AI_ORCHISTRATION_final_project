"""Fail-loud config loader for belief.json -- the belief map's scent-
likelihood engineering defaults (D-42, Task 3): the fusion weight, the
epsilon floor, the age cap, and the freshness-decay mapping. None of these
four numbers is a docs/PARAMETERS.md value; all four are engineering
defaults this module labels as such and validates, never presenting them as
fixed (D-18 discipline, this plan's must_haves truths).

BeliefKey lives HERE, not in pursuit.config_keys, for the same reason
ScentKey/LanguageKey do (04-PLAN-OUTLINE.md Sec4 point 2): config_keys.py is
already at its 150-code-line ceiling. This loader owns only the
`scent_likelihood` group Task 3 introduces; plans 04-09 and 04-11 add their
own groups and BeliefKey entries to the same belief.json without touching
this file's existing keys (04-PLAN-OUTLINE.md Sec4's "one owner per file").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.shared.loader_helpers import require_float, require_int, require_key

BELIEF_CONFIG_SOURCE = "belief.json"


class BeliefKey(str, Enum):
    """Field names for config/{police,thief}/belief.json's `scent_likelihood`
    group. Structural only -- no numeric literal lives on this enum.

    Unlike ScentKey/ResolutionKey, belief.json is never canonically
    re-serialised or hashed (it holds local engineering defaults, not a
    cryptographically-locked cross-peer agreement -- D-46 is scent.json's
    concern, not this file's), so there is no `__str__` override here: a
    plain `str, Enum` member already compares equal to its own value for
    every dict-key lookup this loader performs.
    """

    VERSION = "version"
    GROUP_SCENT_LIKELIHOOD = "scent_likelihood"
    WEIGHT = "weight"
    EPSILON = "epsilon"
    AGE_CAP = "age_cap"
    FRESHNESS_DECAY = "freshness_decay"


@dataclass(frozen=True)
class BeliefParams:
    """Typed, immutable container for belief.json's `scent_likelihood` group.

    Constructed only by load_belief_config() -- callers never build this
    directly (NET-02 precedent: a fresh instance every call, never a shared
    live object, so police and thief processes can never leak state through
    it -- CLAUDE.md rule 2).
    """

    version: str
    scent_weight: float
    epsilon: float
    age_cap: int
    freshness_decay: float


def load_belief_config(path: Path | str) -> BeliefParams:
    """Load and validate config/{police,thief}/belief.json.

    Raises
    ------
    KeyError
        If any required key (top-level or in `scent_likelihood`) is absent.
    TypeError
        If any leaf value carries the wrong type.
    ValueError
        If `weight` is not positive, `epsilon` is not in [0, 1), `age_cap`
        is not >= 1 (an uncapped-at-zero age would never project the
        likelihood forward, which is exactly the "chase the strongest
        cell" failure D-42 exists to prevent), or `freshness_decay` is not
        in (0, 1).
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)

    version = str(require_key(data, BeliefKey.VERSION.value, source=BELIEF_CONFIG_SOURCE))
    group = require_key(data, BeliefKey.GROUP_SCENT_LIKELIHOOD.value, source=BELIEF_CONFIG_SOURCE)

    weight = require_float(group, BeliefKey.WEIGHT.value, source=BELIEF_CONFIG_SOURCE)
    epsilon = require_float(group, BeliefKey.EPSILON.value, source=BELIEF_CONFIG_SOURCE)
    age_cap = require_int(group, BeliefKey.AGE_CAP.value, source=BELIEF_CONFIG_SOURCE)
    freshness_decay = require_float(
        group, BeliefKey.FRESHNESS_DECAY.value, source=BELIEF_CONFIG_SOURCE
    )
    _validate(weight=weight, epsilon=epsilon, age_cap=age_cap, freshness_decay=freshness_decay)

    return BeliefParams(
        version=version,
        scent_weight=weight,
        epsilon=epsilon,
        age_cap=age_cap,
        freshness_decay=freshness_decay,
    )


def _validate(*, weight: float, epsilon: float, age_cap: int, freshness_decay: float) -> None:
    """Raise ValueError naming the offending field; see load_belief_config."""
    if weight <= 0.0:
        raise ValueError(f"{BELIEF_CONFIG_SOURCE}: 'weight' must be > 0, got {weight}")
    if not 0.0 <= epsilon < 1.0:
        raise ValueError(f"{BELIEF_CONFIG_SOURCE}: 'epsilon' must be in [0, 1), got {epsilon}")
    if age_cap < 1:
        raise ValueError(f"{BELIEF_CONFIG_SOURCE}: 'age_cap' must be >= 1, got {age_cap}")
    if not 0.0 < freshness_decay < 1.0:
        raise ValueError(
            f"{BELIEF_CONFIG_SOURCE}: 'freshness_decay' must be in (0, 1), got {freshness_decay}"
        )
