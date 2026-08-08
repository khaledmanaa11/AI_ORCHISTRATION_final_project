"""The learned artefact: one 15-float weight vector, plus its hand-set prior.

Fifteen numbers, against the 103.7 million Q-values the abandoned tabular key
induced. That ratio is the whole argument for this architecture: the search
supplies the tactics, so the learner only has to supply positional judgement, and
positional judgement over hand-designed graph features needs thousands of games
rather than hundreds of thousands of episodes.

The prior below is not a guess dressed up as a result -- it is a deliberate
starting point encoding what pursuit theory already knows, so that a run which
fails to improve on it is visibly a failure rather than a plausible-looking
number. Book Sec6.3 p.43 makes learning optional; PRIOR alone is shippable.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.strategy.features import FEATURE_COUNT, FEATURE_NAMES

WEIGHTS_VERSION = "2.00"

#: Hand-set opening weights, cop-perspective. Signs encode three facts:
#:   * closing distance matters, but is NOT the objective -- a single cop cannot
#:     corner a perfect evader on an open grid, so distance alone is a trap;
#:   * the real cop win is structural: drive the thief's region toward a forest
#:     (cycle rank 0), then it can be cornered. Hence the heaviest weights sit on
#:     cycle rank and the forest indicator, not on distance;
#:   * a thief that cannot be reached at all is a guaranteed survival, which is
#:     the worst state the cop can be in and is weighted accordingly.
PRIOR = (
    0.60,   # bias -- centres the typical position near tanh's linear region
    1.00,   # neg_distance
    2.00,   # thief_unreachable
    0.50,   # neg_thief_degree
    0.80,   # territory_diff
    0.90,   # neg_thief_region
    1.20,   # neg_cycle_rank
    1.50,   # thief_region_is_forest
    0.40,   # chokepoint_density
    0.30,   # thief_on_chokepoint
    0.25,   # barriers_remaining
    0.35,   # turns_remaining
    0.00,   # parity -- genuinely unknown sign; let training discover it
    0.20,   # cop_degree
    3.00,   # thief_in_kill_range -- large on purpose: it is a FORCED capture
            # next turn (rule 46 seals the cell the thief is leaving), so the
            # weight saturates tanh and the leaf reads as very nearly terminal.
)


def load_weights(path: Path | str | None) -> tuple:
    """Load a trained weight vector, or return PRIOR when none is configured.

    A missing file is NOT silently tolerated when a path was given: shipping a
    league game with the prior while believing it trained is the failure mode
    that produced run 1's unexplained result, so an absent configured artefact
    fails loud.

    Raises
    ------
    FileNotFoundError
        If *path* was given but does not exist.
    ValueError
        If the file holds the wrong number of weights.
    """
    if path is None:
        return PRIOR
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(
            f"configured weights {resolved} not found; remove the config key to "
            f"run on the hand-set prior deliberately rather than by accident"
        )
    with resolved.open() as handle:
        data = json.load(handle)
    weights = tuple(float(value) for value in data["weights"])
    if len(weights) != FEATURE_COUNT:
        raise ValueError(
            f"{resolved}: expected {FEATURE_COUNT} weights, found {len(weights)}. "
            f"A vector of the wrong length means the feature set changed under a "
            f"trained artefact -- retrain rather than pad."
        )
    return weights


def save_weights(path: Path | str, weights: tuple, metadata: dict | None = None) -> None:
    """Write a weight vector with its feature names, so an artefact is readable.

    Names travel with the numbers deliberately: a bare list of floats is
    unauditable, and rule 42 wants the academic report to describe the model.
    """
    if len(weights) != FEATURE_COUNT:
        raise ValueError(f"expected {FEATURE_COUNT} weights, got {len(weights)}")
    payload = {
        "version": WEIGHTS_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "weights": [float(value) for value in weights],
    }
    if metadata:
        payload["metadata"] = metadata
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def describe(weights: tuple) -> str:
    """Render weights as an aligned name/value table for the report and logs."""
    width = max(len(name) for name in FEATURE_NAMES)
    return "\n".join(
        f"{name:<{width}}  {weight:+.4f}"
        for name, weight in zip(FEATURE_NAMES, weights, strict=True)
    )
