"""Fail-loud config loader for belief.json -- the belief map's engineering
defaults across four groups, one owning plan each (04-PLAN-OUTLINE.md Sec4):
`scent_likelihood` (04-05, D-42), `reliability`/`hint_likelihood` (04-09,
D-51/D-40) and `belief` (04-11, the adapter's own on/off + seed). None of
these numbers is a docs/PARAMETERS.md value; all are engineering defaults
this module labels as such (D-18 discipline).

BeliefKey lives HERE, not in pursuit.config_keys, for the same reason
ScentKey/LanguageKey do (04-PLAN-OUTLINE.md Sec4 point 2): config_keys.py is
already at its 150-code-line ceiling. Every group's keys are added to this
SAME enum -- 04-05's own SUMMARY anticipated exactly this extension -- so
there is one place a reader checks for every belief.json field name.

Every non-scent group's own dataclass and validation lives in its own
`shared/<group>_config.py` (`reliability_config.py`, `hint_likelihood_config.py`,
`belief_toggle_config.py`) -- split out at the SAME 150-code-line ceiling this
file would otherwise breach. This file stays the single `load_belief_config()`
entry point every other module imports, and is where `hint_likelihood.weight`
is checked against `scent_likelihood.weight`, by name (D-40's asymmetry).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pursuit.shared.belief_toggle_config import (
    BeliefToggleParams,
    require_bool,
    require_optional_int,
)
from pursuit.shared.hint_likelihood_config import HintLikelihoodParams, validate_hint_likelihood
from pursuit.shared.loader_helpers import require_float, require_int, require_key
from pursuit.shared.reliability_config import ReliabilityParams, validate_reliability

BELIEF_CONFIG_SOURCE = "belief.json"


class BeliefKey(str, Enum):
    """Field names for config/{police,thief}/belief.json, across every
    group. Structural only -- no numeric literal lives on this enum.

    Unlike ScentKey/ResolutionKey, belief.json is never canonically
    re-serialised or hashed, so there is no `__str__` override here: a plain
    `str, Enum` member already compares equal to its own value for lookup.
    """

    VERSION = "version"

    GROUP_SCENT_LIKELIHOOD = "scent_likelihood"
    WEIGHT = "weight"
    EPSILON = "epsilon"
    AGE_CAP = "age_cap"
    FRESHNESS_DECAY = "freshness_decay"

    GROUP_RELIABILITY = "reliability"
    PRIOR = "prior"
    R_MIN = "r_min"
    R_MAX = "r_max"
    CONTRADICTION_STEP = "contradiction_step"
    RECOVERY_RATE = "recovery_rate"

    GROUP_HINT_LIKELIHOOD = "hint_likelihood"

    GROUP_BELIEF = "belief"
    ENABLED = "enabled"
    SEED = "seed"


@dataclass(frozen=True)
class BeliefParams:
    """Typed, immutable container for belief.json.

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
    reliability: ReliabilityParams
    hint_likelihood: HintLikelihoodParams
    belief: BeliefToggleParams


def load_belief_config(path: Path | str) -> BeliefParams:
    """Load and validate config/{police,thief}/belief.json.

    Raises
    ------
    KeyError
        If any required key (top-level or in any group) is absent.
    TypeError
        If any leaf value carries the wrong type.
    ValueError
        If any group's fields fail its own validation -- see
        `_validate_scent_likelihood`, `reliability_config.validate_reliability`
        and `hint_likelihood_config.validate_hint_likelihood`.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)

    version = str(require_key(data, BeliefKey.VERSION.value, source=BELIEF_CONFIG_SOURCE))
    scent_group = require_key(
        data, BeliefKey.GROUP_SCENT_LIKELIHOOD.value, source=BELIEF_CONFIG_SOURCE
    )
    reliability_group = require_key(
        data, BeliefKey.GROUP_RELIABILITY.value, source=BELIEF_CONFIG_SOURCE
    )
    hint_group = require_key(
        data, BeliefKey.GROUP_HINT_LIKELIHOOD.value, source=BELIEF_CONFIG_SOURCE
    )
    belief_group = require_key(data, BeliefKey.GROUP_BELIEF.value, source=BELIEF_CONFIG_SOURCE)

    weight = require_float(scent_group, BeliefKey.WEIGHT.value, source=BELIEF_CONFIG_SOURCE)
    epsilon = require_float(scent_group, BeliefKey.EPSILON.value, source=BELIEF_CONFIG_SOURCE)
    age_cap = require_int(scent_group, BeliefKey.AGE_CAP.value, source=BELIEF_CONFIG_SOURCE)
    freshness_decay = require_float(
        scent_group, BeliefKey.FRESHNESS_DECAY.value, source=BELIEF_CONFIG_SOURCE
    )
    _validate_scent_likelihood(weight=weight, epsilon=epsilon, age_cap=age_cap, freshness_decay=freshness_decay)

    reliability = ReliabilityParams(
        prior=require_float(reliability_group, BeliefKey.PRIOR.value, source=BELIEF_CONFIG_SOURCE),
        r_min=require_float(reliability_group, BeliefKey.R_MIN.value, source=BELIEF_CONFIG_SOURCE),
        r_max=require_float(reliability_group, BeliefKey.R_MAX.value, source=BELIEF_CONFIG_SOURCE),
        contradiction_step=require_float(
            reliability_group, BeliefKey.CONTRADICTION_STEP.value, source=BELIEF_CONFIG_SOURCE
        ),
        recovery_rate=require_float(
            reliability_group, BeliefKey.RECOVERY_RATE.value, source=BELIEF_CONFIG_SOURCE
        ),
    )
    validate_reliability(reliability, source=BELIEF_CONFIG_SOURCE)

    hint_likelihood = HintLikelihoodParams(
        weight=require_float(hint_group, BeliefKey.WEIGHT.value, source=BELIEF_CONFIG_SOURCE)
    )
    validate_hint_likelihood(hint_likelihood, scent_weight=weight, source=BELIEF_CONFIG_SOURCE)

    belief_toggle = BeliefToggleParams(
        require_bool(belief_group, BeliefKey.ENABLED.value, source=BELIEF_CONFIG_SOURCE),
        require_optional_int(belief_group, BeliefKey.SEED.value, source=BELIEF_CONFIG_SOURCE),
    )

    return BeliefParams(
        version=version,
        scent_weight=weight,
        epsilon=epsilon,
        age_cap=age_cap,
        freshness_decay=freshness_decay,
        reliability=reliability,
        hint_likelihood=hint_likelihood,
        belief=belief_toggle,
    )


def _validate_scent_likelihood(
    *, weight: float, epsilon: float, age_cap: int, freshness_decay: float
) -> None:
    """Raise ValueError naming the offending field (04-05's original checks,
    unchanged by this plan)."""
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
