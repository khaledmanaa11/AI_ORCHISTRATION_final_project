"""Strategy package: the pluggable RL policy seam (STRAT-03).

Exports the contracts only -- BrainBase, Observation, Decision. Concrete
brains (ValueSearchBrain, ChaserCop, GreedyEvader) are registered via
pursuit.strategy.registry.build_brain, not imported here.
"""

from pursuit.strategy.base import BrainBase, Decision, Observation

__all__ = ["BrainBase", "Decision", "Observation"]
