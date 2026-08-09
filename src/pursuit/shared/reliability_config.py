"""Typed container + validation for belief.json's `reliability` group (D-51).

Split out of `shared/belief_config.py` at the 150-code-line ceiling (CLAUDE.md:
split files, never compress code to fit) -- `belief_config.py`'s `BeliefKey`
still names every field across every group (04-05's own SUMMARY anticipated
this exact extension: "one place a reader checks for every belief.json field
name"); this module only carries the group's own dataclass and its
validation, called from `belief_config.load_belief_config()`.

`prior` is D-40's original single "trust hints below scent" number, now the
STARTING point of an adaptive coefficient (D-51) -- a field distinct from
`hint_likelihood.weight` (shared/hint_likelihood_config.py), which stays
fixed forever in the same Bayes mix. See `strategy/reliability.py`'s
docstring for why the two are not the same JSON field wearing two names.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReliabilityParams:
    """Typed, immutable container for belief.json's `reliability` group --
    `strategy/reliability.py`'s `Reliability` starting point and bounds.
    Never constructed directly outside `load_belief_config()`.
    """

    prior: float
    r_min: float
    r_max: float
    contradiction_step: float
    recovery_rate: float


def validate_reliability(params: ReliabilityParams, *, source: str) -> None:
    """Raise ValueError naming the offending field.

    `r_min`/`r_max` must both sit strictly inside (0, 1) with `r_min <
    r_max` -- the clamp is a design requirement (see `strategy/reliability.py`):
    at 0 an honest opponent's information is wasted, at 1 a fluent liar is
    trusted completely, and both must stay reachable-but-not-exceedable.
    `prior` must lie within `[r_min, r_max]` so a fresh instance never starts
    outside its own bounds. `contradiction_step`/`recovery_rate` are step
    sizes on the same [0, 1]-valued coefficient, so both must be positive and
    at most 1.
    """
    if not 0.0 < params.r_min < params.r_max < 1.0:
        raise ValueError(
            f"{source}: need 0 < 'r_min' ({params.r_min}) < 'r_max' "
            f"({params.r_max}) < 1"
        )
    if not params.r_min <= params.prior <= params.r_max:
        raise ValueError(
            f"{source}: 'prior' ({params.prior}) must be in "
            f"['r_min' {params.r_min}, 'r_max' {params.r_max}]"
        )
    if not 0.0 < params.contradiction_step <= 1.0:
        raise ValueError(
            f"{source}: 'contradiction_step' must be in (0, 1], "
            f"got {params.contradiction_step}"
        )
    if not 0.0 < params.recovery_rate <= 1.0:
        raise ValueError(
            f"{source}: 'recovery_rate' must be in (0, 1], got {params.recovery_rate}"
        )
