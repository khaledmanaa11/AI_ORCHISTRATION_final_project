"""Typed container + validation for belief.json's `belief` group (Task 3):
the adapter's own on/off switch and RNG seed.

Split out of `shared/belief_config.py` at the 150-code-line ceiling, same
reasoning as `shared/reliability_config.py`/`shared/hint_likelihood_config.py`'s
own docstrings.

`enabled` is what lets 04-14 measure with and without the belief layer and
report the difference honestly (04-PLAN-OUTLINE.md Sec5), and lets a
debugging session bypass the layer without editing code. `seed` seeds the
adapter's own `random.Random` (never the module-level RNG, never `secrets`,
which is reserved for Phase 6 nonces) -- a missing (`null`) seed is NOT an
error; the caller (`strategy/registry.py`) derives one and logs it, because
rule 20's replay viewer must still be able to reproduce the game either way.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BeliefToggleParams:
    """Typed, immutable container for belief.json's `belief` group. Never
    constructed directly outside `load_belief_config()`."""

    enabled: bool
    seed: int | None


def require_bool(data: dict, key: str, *, source: str) -> bool:
    """Return data[key] as bool; raise TypeError if it is not one.

    Raises
    ------
    KeyError
        If key is not present in data.
    TypeError
        If the value is present but not a bool.
    """
    if key not in data:
        raise KeyError(f"Required key '{key}' missing from {source}")
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(f"{source} field '{key}' must be bool, got {type(value).__name__!r}")
    return value


def require_optional_int(data: dict, key: str, *, source: str) -> int | None:
    """Return data[key] as int, or None when the JSON value is null.

    Raises
    ------
    KeyError
        If key is not present in data.
    TypeError
        If the value is present but neither an int nor null.
    """
    if key not in data:
        raise KeyError(f"Required key '{key}' missing from {source}")
    value = data[key]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{source} field '{key}' must be int or null, got {type(value).__name__!r}"
        )
    return value
