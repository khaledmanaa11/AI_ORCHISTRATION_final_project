"""Typed container + validation for belief.json's `hint_likelihood` group
(D-40).

Split out of `shared/belief_config.py` at the 150-code-line ceiling, same
reasoning as `shared/reliability_config.py`'s own docstring. This is D-40's
OTHER number: the fixed mixing weight `w` in `strategy/belief_hint.py`'s
`L(c) = w . [...] + (1 - w) . u(c)`, unchanged by D-51 -- only the
reliability coefficient `r` that formula also uses became adaptive, not `w`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HintLikelihoodParams:
    """Typed, immutable container for belief.json's `hint_likelihood` group
    -- `strategy/belief_hint.py`'s fixed mixing weight `w`. Never constructed
    directly outside `load_belief_config()`.
    """

    weight: float


def validate_hint_likelihood(
    params: HintLikelihoodParams, *, scent_weight: float, source: str
) -> None:
    """Raise ValueError naming the offending field.

    `weight` must be a genuine (0, 1) mixing fraction, and -- D-40's
    asymmetry, enforced structurally rather than by convention -- strictly
    below `scent_likelihood.weight`: scent cannot lie, words can, so a
    config that let a hint outweigh scent is a rule violation in spirit and
    is refused here by name.
    """
    if not 0.0 < params.weight < 1.0:
        raise ValueError(
            f"{source}: 'hint_likelihood.weight' must be in (0, 1), got {params.weight}"
        )
    if not params.weight < scent_weight:
        raise ValueError(
            f"{source}: 'hint_likelihood.weight' ({params.weight}) must be < "
            f"'scent_likelihood.weight' ({scent_weight}) -- hints may never "
            f"outweigh scent (D-40)"
        )
