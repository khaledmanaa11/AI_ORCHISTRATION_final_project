"""ValueSearchBrain: solve the turn's matrix game, then sample the equilibrium.

One brain class serves both seats. The game is zero-sum, so the cop plays the row
strategy and the thief the column strategy of the SAME solved matrix, against the
SAME weight vector -- there is no second artefact and no second training run.

Why sampling rather than argmax: under simultaneous moves the equilibrium is often
mixed, and a deterministic policy is readable by any opponent that searches. The
draw comes from an injected Random the caller seeds per game and logs, so play is
reproducible in the replay viewer (rule 20) while remaining unpredictable to the
opponent, which is exactly the property we want.
"""

from __future__ import annotations

import random

from pursuit.constants import MoveSource
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import PREFERRED, ResolutionRules
from pursuit.shared.state import GameState
from pursuit.strategy.base import BrainBase, Decision, Observation
from pursuit.strategy.equilibrium import sample, solve
from pursuit.strategy.matrix import payoff_matrix
from pursuit.strategy.weights import PRIOR, load_weights

VALUE_SEARCH_BRAIN_NAME = "value_search"

#: Regret-matching iterations, used only when the turn has no pure saddle point.
#: 200 is comfortably converged for matrices this small and costs under a
#: millisecond; the pure-saddle short circuit means most turns never reach it.
DEFAULT_EQUILIBRIUM_ITERATIONS = 200

#: Deterministic default so an unseeded brain still replays identically. The live
#: agent overrides it per game with a seed derived from the logged game_uid.
DEFAULT_SEED = 20260808


class ValueSearchBrain(BrainBase):
    """Matrix-game mover over a learned 14-weight positional evaluation."""

    def __init__(
        self,
        role: str,
        params=None,
        game_params: GameParams = None,
        *,
        rules: ResolutionRules = PREFERRED,
        weights: tuple | None = None,
        iterations: int = DEFAULT_EQUILIBRIUM_ITERATIONS,
        epsilon: float = 0.0,
        rng: random.Random | None = None,
    ) -> None:
        """Build a brain for *role*.

        `params`/`game_params` keep the registry's construction signature. The
        keyword-only arguments are what training varies: `weights` for the vector
        under test, `epsilon` for off-policy exploration, `rng` for the seeded
        draw. `epsilon` must be 0.0 in a league game -- a deliberate random move
        is a training device, never a competitive one.
        """
        self.role = role
        self.game_params = game_params
        self.rules = rules
        self.iterations = iterations
        self.epsilon = epsilon
        self.rng = rng if rng is not None else random.Random(DEFAULT_SEED)
        self.weights = weights if weights is not None else _weights_from(params)
        self.last_value: float = 0.0

    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        """Return the movement half of this turn's decision.

        The cop's barrier is not a separate sub-policy here: placement is one of
        the rows of the same matrix, so both are chosen together and this method
        simply forwards. The split survives only because BrainBase declares it.
        """
        return self._decide_move(obs, state)

    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        """Solve the turn's matrix game and sample this seat's equilibrium."""
        rows, columns, matrix = payoff_matrix(state, self.weights, self.game_params, self.rules)
        row_strategy, column_strategy, self.last_value = solve(matrix, self.iterations)

        if self.role == "cop":
            index = self._choose(row_strategy)
            action = rows[index]
            return Decision(
                move=action.destination(state.cop),
                source=self._source(),
                barrier=action.barrier,
            )
        index = self._choose(column_strategy)
        return Decision(move=columns[index], source=self._source(), barrier=None)

    def _choose(self, strategy: tuple) -> int:
        """Sample the equilibrium, or explore uniformly with probability epsilon."""
        if self.epsilon and self.rng.random() < self.epsilon:
            return self.rng.randrange(len(strategy))
        return sample(strategy, self.rng.random())

    def _source(self) -> MoveSource:
        """Report provenance truthfully -- it is asserted on, never inferred."""
        return MoveSource.EXPLORATION if self.epsilon else MoveSource.EQUILIBRIUM

    def seed(self, value: int) -> None:
        """Reseed the draw for a new game, so the log can reproduce it exactly."""
        self.rng = random.Random(value)


def _weights_from(params) -> tuple:
    """Resolve the weight vector from StrategyParams, falling back to the prior.

    A configured-but-missing artefact raises inside load_weights: silently
    shipping the prior while believing the run trained is the exact failure that
    made run 1's result unexplainable.
    """
    path = getattr(params, "weights_path", None) if params is not None else None
    return load_weights(path) if path else PRIOR
