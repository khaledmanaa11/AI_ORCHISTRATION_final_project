"""Validation for belief.json's `scent_likelihood` group (04-05, D-18).

Split out of `shared/belief_config.py` at the 150-code-line ceiling (Segal
Table 5), exactly as `shared/reliability_config.py`,
`shared/hint_likelihood_config.py` and `shared/belief_toggle_config.py` were
before it -- the file needed room for 07-11's `display` group and the
standing rule is split files, never compress code to fit.

The checks themselves are 04-05's own, moved verbatim: no threshold changed
and no message changed, so `test_belief_config.py`'s out-of-range table
still names the same fields with the same wording. Unlike its three sibling
modules this one carries no dataclass, because the group's four fields live
FLAT on `BeliefParams` (`scent_weight`/`epsilon`/`age_cap`/`freshness_decay`)
and re-nesting them would churn every reader of the belief config for no
gain.
"""

from __future__ import annotations


def validate_scent_likelihood(
    *, weight: float, epsilon: float, age_cap: int, freshness_decay: float, source: str
) -> None:
    """Raise ValueError naming the offending field.

    Raises
    ------
    ValueError
        If `weight` is not > 0, `epsilon` is outside [0, 1), `age_cap` is
        below 1, or `freshness_decay` is outside (0, 1).
    """
    if weight <= 0.0:
        raise ValueError(f"{source}: 'weight' must be > 0, got {weight}")
    if not 0.0 <= epsilon < 1.0:
        raise ValueError(f"{source}: 'epsilon' must be in [0, 1), got {epsilon}")
    if age_cap < 1:
        raise ValueError(f"{source}: 'age_cap' must be >= 1, got {age_cap}")
    if not 0.0 < freshness_decay < 1.0:
        raise ValueError(
            f"{source}: 'freshness_decay' must be in (0, 1), got {freshness_decay}"
        )
