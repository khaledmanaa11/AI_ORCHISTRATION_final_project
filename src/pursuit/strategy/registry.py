"""Config-driven brain construction: the only place a BrainBase is built (STRAT-03, D-07).

Resolution goes through the explicit dict below -- never eval, exec, or an
unguarded importlib call on a config string. A config file that could name
an arbitrary importable would be an arbitrary-code-execution path, and this
project ships config alongside the agent. Concrete brains register here in
03-04 (HeuristicBrain) and 03-06 (QLearningBrain, D-07); this plan ships the
mechanism itself, with the registry still empty of real entries.
"""

from pursuit.shared.strategy_config import StrategyParams
from pursuit.strategy.base import BrainBase

# Explicit name -> class registry. Populated by 03-04 and 03-06; this plan
# proves the mechanism only (tests inject a local stub via monkeypatch).
_BRAIN_REGISTRY: dict[str, type[BrainBase]] = {}


def build_brain(role: str, params: StrategyParams) -> BrainBase:
    """Construct the BrainBase named by params.brain_class for role.

    Parameters
    ----------
    role:
        "cop" or "thief" -- passed through to the brain's constructor so a
        two-stage brain (movement then barrier) knows which role it plays.
    params:
        The per-role StrategyParams already resolved by
        load_strategy_config(); params.brain_class names the class to build.

    Raises
    ------
    ValueError
        If params.brain_class is not a registered name -- names the
        offending value and every known name. Never falls back to a
        default brain: a silent fallback means a training run or a league
        game played by the wrong policy with no signal anything is wrong.
    """
    name = params.brain_class
    if name not in _BRAIN_REGISTRY:
        known = sorted(_BRAIN_REGISTRY)
        raise ValueError(f"Unknown brain class {name!r}; known classes: {known}")
    brain_cls = _BRAIN_REGISTRY[name]
    return brain_cls(role=role, params=params)
