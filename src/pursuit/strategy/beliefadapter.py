"""BeliefAdapter: connects the belief map to the mover (D-43, D-48, Task 1+2).

Owns one opponent's belief lifecycle for one game -- a fresh `BeliefMap` and
a fresh `Reliability`, both constructed HERE, never persisted or shared
across games (rule 52) or processes (rule 2). `decide()` runs Figure 7's
per-turn order (book Sec6.2, p.43 / PDF 59) and nothing else:

    observe -> predict -> update(scent) -> update(hint) -> sample -> decide

D-43 overrides `Observation.target_cell`'s Phase-3 docstring guess: the
mover receives a cell SAMPLED from the posterior, not its argmax -- an
argmax target makes pursuit deterministic given the opponent's own model of
our belief, and a deterministic pursuit is exploitable in a
one-counted-game league (rule 52).

This is Option A (docs/phases/phase-3/PRD.md Sec8, where the rejected Option
B and its cost argument are written out): the sampled cell substitutes the
opponent's coordinate in a believed GameState, so the UNCHANGED matrix mover
(valuebrain.py/matrix.py -- neither touched by this module) reasons over it
exactly as it always has.

Honesty clause (04-PLAN-OUTLINE.md Sec1): in Regime A (this turn's Reveal
was integrable) the substitution is the identity for a cornered opponent
(see the tests) -- the belief map contributes nothing to move SCORING
there. Its value in Regime A is LANG-05 compliance, the opponent-action
prior, the deception channel that shapes the OPPONENT's belief (via the fed
`opponent_field`), and survival once a game degrades into Regime B
(`known_cell=None` every turn).

RULE 9 IS NOT THIS MODULE'S ANY MORE, AND THAT IS THE POINT (07-11). This
docstring used to hand "local truth" to the display layer while
`sdk/view_builder` published what `observe_exact` had just collapsed onto the
engine's answer -- both delegated, neither owned. `self.display`
(`strategy/display_belief.py`, `docs/PRD_display_belief.md`) owns it now.
`self.belief` is UNCHANGED and still sees `known_cell`.

Strategy-layer only (STRAT-07): imports nothing from `pursuit.services` or
`pursuit.network`. Receives an already-decoded `Inference`; never calls a
language model.
"""

from __future__ import annotations

import random
from dataclasses import replace

from pursuit.shared.belief_config import BeliefParams
from pursuit.shared.config import GameParams
from pursuit.shared.inference import Coord, Inference
from pursuit.shared.resolution import ResolutionRules
from pursuit.shared.scent_config import ScentModel
from pursuit.shared.state import GameState
from pursuit.strategy.base import BrainBase, Decision, Observation
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.belief_hint import hint_likelihood
from pursuit.strategy.belief_scent import scent_likelihood
from pursuit.strategy.display_belief import DisplayBelief, positive_cells
from pursuit.strategy.reliability import Reliability
from pursuit.strategy.scentfield import ScentField

#: Which role BeliefAdapter tracks for each seat it plays -- matches
#: belief_motion.ROLES and GameState's own field names exactly.
_OPPONENT_OF = {"cop": "thief", "thief": "cop"}


class BeliefAdapter:
    """Wraps a `BrainBase` and owns its belief lifecycle for one game.

    Composition, not inheritance: `decide()`'s inputs (an `Inference`, a
    `ScentField`, an explicit Regime-A/B signal) are more than
    `BrainBase._decide_move(obs, state)` accepts, so this is a distinct
    public entry point rather than an ABC override.
    """

    def __init__(
        self,
        brain: BrainBase,
        role: str,
        game_params: GameParams,
        belief_config: BeliefParams,
        scent_model: ScentModel,
        rng: random.Random,
    ) -> None:
        """Build the adapter for `role` ("cop" or "thief" -- OUR OWN seat).

        `self.belief`/`self.reliability` are constructed fresh HERE, once
        per game, and exposed as public attributes so a turn-pipeline
        caller can drive `self.reliability.observe(score)` from
        `scent_check.contradicts()` between `decide()` calls
        (04-09-SUMMARY.md carry-over F): this module owns CONSTRUCTING the
        one instance per game; the caller owns feeding it evidence.
        """
        if role not in _OPPONENT_OF:
            raise ValueError(f"BeliefAdapter: role must be 'cop' or 'thief', got {role!r}")
        self.brain = brain
        self.role = role
        self.opponent_role = _OPPONENT_OF[role]
        self.game_params = game_params
        self.belief_config = belief_config
        self.scent_model = scent_model
        self.rng = rng
        self.belief = BeliefMap(game_params.board_size, self.opponent_role)
        self.reliability = Reliability(belief_config.reliability)
        self.display = DisplayBelief(
            game_params.board_size, self.opponent_role, scent_model, belief_config.display
        )

    def decide(
        self,
        state: GameState,
        inference: Inference,
        opponent_field: ScentField,
        rules: ResolutionRules,
        *,
        known_cell: Coord | None = None,
    ) -> Decision:
        """Run Figure 7's order once and return the wrapped brain's Decision.

        `rules` is accepted, not read, inside this method: the wrapped
        brain already carries its own negotiated `ResolutionRules` from
        construction (`ValueSearchBrain`'s own `rules` keyword), and this
        module may not touch `valuebrain.py` to thread a second copy
        through it. Kept in the signature so a caller is never left
        guessing which rules governed the turn a Decision came from.

        `known_cell` is the opponent's pre-turn cell when this turn's
        Reveal was integrable (Regime A) -- caller-supplied rather than
        read off `state` directly, because `state` keeps carrying the
        engine's true joint position regardless of regime. It is used here
        WITHOUT reservation: rule 9 governs what is DISPLAYED, not what is
        known. `self.display` is advanced alongside from the hint and motion
        models only, and is what a view publishes once this map has been
        collapsed onto an exact cell (07-11). `None` means Regime B, and
        `observe_exact` is skipped entirely.
        """
        our_cell = state.cop if self.role == "cop" else state.thief
        if known_cell is not None:
            self.belief.observe_exact(known_cell)
            opponent_field.emit_opponent(known_cell)
        else:
            for cell, weight in positive_cells(self.belief.posterior()):
                opponent_field.emit_opponent(cell, weight)
        opponent_field.emit_own(our_cell)

        self.belief.predict(state, self.game_params)

        scent_grid = scent_likelihood(
            opponent_field,
            self.opponent_role,
            state,
            self.game_params,
            self.scent_model,
            self.belief_config,
        )
        self.belief.update(scent_grid)

        hint_grid = hint_likelihood(
            inference, self.reliability, self.game_params.board_size, self.belief_config
        )
        self.belief.update(hint_grid)

        self.display.advance(
            state, hint_grid, self.game_params, observed_exact=known_cell is not None
        )

        sampled_cell = self.belief.sample(self.rng)

        obs = Observation(
            own_cell=our_cell,
            target_cell=sampled_cell,
            blocked_mask=0,
            barriers_used=state.barriers_placed,
            turn_index=state.turn,
        )
        believed_state = replace(state, **{self.opponent_role: sampled_cell})
        return self.brain._decide_move(obs, believed_state)
