"""Play one simultaneous game between two brains and record what happened.

The single game loop for the whole project: training, evaluation and the
integration tests all drive play through here, so there is exactly one place that
knows how a turn is sequenced. The old harness had that logic copied across six
cop-then-thief loops, which is how the sequential assumption survived so long.

The contract that matters: BOTH brains are asked to decide from the SAME pre-turn
state, and only then is the turn resolved. A caller that interleaves the two calls
with a resolve has reintroduced the bug this phase exists to remove.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.constants import Outcome
from pursuit.sdk.actions import CopAction
from pursuit.sdk.resolve import make_state, resolve_turn
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from pursuit.shared.state import GameState
from pursuit.strategy.base import Observation


@dataclass(frozen=True)
class GameRecord:
    """One finished game: its result and every state that was visited."""

    outcome: Outcome
    states: tuple
    turns: int

    @property
    def captured(self) -> bool:
        """True when the cop won."""
        return self.outcome is Outcome.CAPTURE

    @property
    def cop_target(self) -> float:
        """The regression target for every state in this game, cop-perspective.

        +1 for a capture, -1 for a survival. The thief's target is the negation,
        which is why one weight vector serves both seats and why a single game
        produces training signal for both.
        """
        return 1.0 if self.captured else -1.0


def observe(state: GameState, role: str) -> Observation:
    """Build the Observation a brain receives for *role* at *state*.

    target_cell carries the opponent's true cell: Phase 3 is the book's
    open-coordinate stage. Phase 4 replaces it with the belief map's argmax and
    nothing else in the pipeline changes -- the field's shape is identical.
    """
    own = state.cop if role == "cop" else state.thief
    target = state.thief if role == "cop" else state.cop
    return Observation(
        own_cell=own,
        target_cell=target,
        blocked_mask=0,
        barriers_used=state.barriers_placed,
        turn_index=state.turn,
    )


def to_cop_action(decision) -> CopAction:
    """Convert a cop Decision into the resolver's action type."""
    if decision.barrier is not None:
        return CopAction(barrier=decision.barrier)
    return CopAction(move=decision.move)


def play_game(
    cop_brain,
    thief_brain,
    params: GameParams,
    rules: ResolutionRules,
    start: GameState | None = None,
) -> GameRecord:
    """Play one game to a terminal outcome and return the record.

    A game that somehow exhausts the move ceiling without a terminal predicate
    firing is scored SURVIVAL -- the thief outlasted the clock, which is exactly
    what the survival condition means.
    """
    state = start if start is not None else make_state(params)
    visited = [state]

    for _ in range(params.move_ceiling + 1):
        cop_decision = cop_brain._decide_move(observe(state, "cop"), state)
        thief_decision = thief_brain._decide_move(observe(state, "thief"), state)
        state, outcome = resolve_turn(
            state, to_cop_action(cop_decision), thief_decision.move, params, rules
        )
        visited.append(state)
        if outcome is not None:
            return GameRecord(outcome=outcome, states=tuple(visited), turns=state.turn)

    return GameRecord(outcome=Outcome.SURVIVAL, states=tuple(visited), turns=state.turn)
