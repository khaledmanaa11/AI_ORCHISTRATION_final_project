"""Every field name in config/{police,thief}/belief.json, in ONE place.

Split out of `shared/belief_config.py` by 07-11 at the 150-code-line ceiling
(CLAUDE.md: split files, never compress code to fit), and for a second reason
that matters more than the line count: each group's dataclass and validation
lives in its own `shared/<group>_config.py`, and every one of those modules
is imported BY `belief_config.py`. A group module that wanted the canonical
key names could not import them from there without a cycle, so before this
split the newest group would have had to spell its field names as bare
strings -- a second copy of exactly the thing 04-05's SUMMARY asked to keep
in one place ("one place a reader checks for every belief.json field name").
The enum moved down instead. `belief_config.py` re-exports both names, so
every existing `from pursuit.shared.belief_config import BeliefKey` keeps
working unchanged.

Structural only -- no numeric literal lives here. The values themselves are
engineering defaults documented by each group's own module (D-18).
"""

from __future__ import annotations

from enum import Enum

BELIEF_CONFIG_SOURCE = "belief.json"


class BeliefKey(str, Enum):
    """Field names for config/{police,thief}/belief.json, across every group.

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

    GROUP_DISPLAY = "display"
    MIN_ENTROPY_BITS = "min_entropy_bits"
    MIN_SUPPORT_CELLS = "min_support_cells"
