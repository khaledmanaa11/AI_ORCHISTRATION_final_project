"""Fail-loud config loader for belief.json -- the belief map's engineering
defaults across five groups, one owning plan each (04-PLAN-OUTLINE.md Sec4):
`scent_likelihood` (04-05, D-42), `reliability`/`hint_likelihood` (04-09,
D-51/D-40), `belief` (04-11, the adapter's own on/off + seed) and `display`
(07-11, the rules 8-9 publication floors). None of these numbers is a
docs/PARAMETERS.md value; all are engineering defaults this module labels as
such (D-18 discipline).

`BeliefKey` and `BELIEF_CONFIG_SOURCE` are RE-EXPORTED here from
`shared/belief_keys.py`, where 07-11 moved them so that a group module can
name its own fields canonically without importing its own importer -- see
that module's docstring. Every existing `from pursuit.shared.belief_config
import BeliefKey` is unaffected. They never lived in `pursuit.config_keys`
for the same reason ScentKey/LanguageKey do not (04-PLAN-OUTLINE.md Sec4
point 2): that file is already at its own 150-code-line ceiling.

EVERY group's own dataclass and validation now lives in its own
`shared/<group>_config.py` (`scent_likelihood_config.py`,
`reliability_config.py`, `hint_likelihood_config.py`, `belief_toggle_config.py`,
`display_config.py`) -- split out at the SAME 150-code-line ceiling this file
would otherwise breach. 07-11 moved the last one out, `scent_likelihood`'s
checks, to make room for the `display` group. This file stays the single
`load_belief_config()` entry point every other module imports, and is where
`hint_likelihood.weight` is checked against `scent_likelihood.weight`, by
name (D-40's asymmetry).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pursuit.shared.belief_keys import BELIEF_CONFIG_SOURCE, BeliefKey
from pursuit.shared.belief_toggle_config import (
    BeliefToggleParams,
    require_bool,
    require_optional_int,
)
from pursuit.shared.display_config import DisplayFloors, load_display_floors
from pursuit.shared.hint_likelihood_config import HintLikelihoodParams, validate_hint_likelihood
from pursuit.shared.loader_helpers import require_float, require_int, require_key
from pursuit.shared.reliability_config import ReliabilityParams, validate_reliability
from pursuit.shared.scent_likelihood_config import validate_scent_likelihood


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
    display: DisplayFloors


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
        `scent_likelihood_config.validate_scent_likelihood`,
        `reliability_config.validate_reliability`,
        `hint_likelihood_config.validate_hint_likelihood` and
        `display_config.validate_display_floors`.
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
    validate_scent_likelihood(
        weight=weight, epsilon=epsilon, age_cap=age_cap,
        freshness_decay=freshness_decay, source=BELIEF_CONFIG_SOURCE,
    )

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
        display=load_display_floors(data, source=BELIEF_CONFIG_SOURCE),
    )
