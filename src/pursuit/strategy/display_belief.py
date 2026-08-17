"""THE ONE OWNER OF RULE 9 (07-11): a display-only belief that is never fed
the engine's answer, and the decision about which map a view may publish.

**Full rationale, measurements and the rejected alternative:
`docs/PRD_display_belief.md`.** Read it before changing anything here; the
short version follows.

Rule 9 (`docs/RULES.md:30`) is an absolute disqualification, and nobody owned
it: `beliefadapter.decide`'s docstring handed "local truth" to the display
layer, and `sdk/view_builder` published `ctx.brain.belief` unredacted.
Measured through the shipped path with the real `config/police/*.json`, a
cop's published `belief.argmax` WAS `ctx.state.thief` (5, 3); its support was
the legal-move plus centred on that cell, 5 of 49, which inverts back to it
uniquely; and `scent.opponent`'s peak sat on it at 0.9 -- exactly
`scent.json`'s `"source"`, the unmixed kernel centre. This module ends the
delegation: rule 9 is decided HERE, in one place.

OPTION (a) WAS CHOSEN, NOT OPTION (b). (a) publishes a display-only
`BeliefMap` never fed `ctx.state.thief`, driven by the legal-motion model and
the opponent's own broadcast hints. (b) -- publish the strategy belief only
on turns where `observe_exact` did not fire -- is for the COP a permanently
blank panel, because `turn_language.py:57` returns the true cell on every
turn but turn 0; it hides the leak by deleting the feature. See the PRD Sec2.

WHAT IS DELIBERATELY NOT FED IN: `scent_likelihood`, even though the strategy
belief takes it. This peer's `opponent` scent grid is stamped by
`emit_opponent(known_cell)` from the engine's answer, so feeding it back
re-imports the truth through the side door; feeding the display map its own
reconstructed trail instead would be circular.

THE STRATEGY BELIEF IS UNCHANGED and still sees everything: the provenance is
the opponent's own honest Reveal, and rule 9 governs the DISPLAY, not the
provenance. Play is not degraded.

COP SEAT ONLY, BY PROVENANCE RATHER THAN ROLE NAME: the substitution fires on
`contaminated`, never on a hard-coded "cop", so the thief's genuinely
multi-modal belief is published untouched (verified byte-identical) and a
future path that DID hand the thief an exact cell is covered anyway.
"""

from __future__ import annotations

from pursuit.shared.display_config import DisplayFloors
from pursuit.shared.inference import Coord
from pursuit.shared.scent_config import ScentModel
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.scentfield import ScentField


class DisplayBelief:
    """A belief map and an opponent scent grid that have never been shown
    the engine's answer, plus the rule 9 publication decision.

    Constructed once per game by `BeliefAdapter.__init__`, alongside (never
    instead of) the strategy belief, and advanced once per turn from
    `BeliefAdapter.decide`. It is built on EVERY seat, including seats that
    never contaminate their strategy map, so that a seat which starts taking
    exact observations mid-game already has a warm honest map to fall back
    to rather than a fresh uniform one.
    """

    def __init__(
        self,
        board_size: int,
        opponent_role: str,
        scent_model: ScentModel,
        floors: DisplayFloors,
    ) -> None:
        self.belief = BeliefMap(board_size, opponent_role)
        self.scent = ScentField(model=scent_model, board_size=board_size)
        self.floors = floors
        self.contaminated = False

    def advance(self, state, hint_grid, params, *, observed_exact: bool) -> None:
        """One turn of the honest pipeline: decay, legal-motion spread, hint.

        `state` is safe to pass whole even though it carries the true joint
        position: `belief_motion.spread` substitutes the HYPOTHESISED cell
        for the tracked role before reading anything, so the only fields it
        ever reads for real are the declared barriers and our own cell.
        """
        self.contaminated = self.contaminated or observed_exact
        self.scent.advance()
        self.belief.predict(state, params)
        self.belief.update(hint_grid)
        for cell, weight in positive_cells(self.belief.posterior()):
            self.scent.emit_opponent(cell, weight)

    def publishable(self) -> bool:
        """Whether the display map clears `belief.json`'s `display` floors.

        A GUARD, not the mechanism: the honest pipeline has no way to reach a
        delta (the hint likelihood mixes with uniform, so it can never zero a
        cell), so this is expected to hold on every turn of every game. It
        exists because "expected to" is what the leak this module fixes was
        also true of, and because a floor that is never checked is not a
        floor. See `shared/display_config.py` for why the two numbers are
        derived rather than picked.
        """
        support = sum(1 for row in self.belief.posterior() for value in row if value > 0.0)
        return (
            support >= self.floors.min_support_cells
            and self.belief.entropy() >= self.floors.min_entropy_bits
        )

    def published_belief(self, strategy_belief: BeliefMap) -> BeliefMap | None:
        """THE RULE 9 DECISION for the belief panel.

        Uncontaminated seat -> its own strategy posterior, untouched, byte
        for byte. Contaminated seat -> the display map, or `None` when even
        that fails the floors, which `view_builder` renders as the same
        honest "no belief this game" a disabled belief layer produces --
        never a fabricated stand-in.
        """
        if not self.contaminated:
            return strategy_belief
        return self.belief if self.publishable() else None

    def published_scent(self, actual: ScentField) -> ScentField:
        """THE RULE 9 DECISION for the scent panel, which leaks independently.

        `emit_opponent(known_cell)` stamps the kernel on the true cell at
        full source strength, and because decay is a uniform scalar two
        consecutive published snapshots subtract to recover the fresh
        deposit -- so even an animate-only GUI leaks every turn, and fixing
        only the belief would be a half fix. Our OWN trail is passed through
        exactly as it is: it is local truth by definition and rule 8 asks for
        precisely that.
        """
        if not self.contaminated:
            return actual
        return ScentField(
            model=actual.model,
            board_size=actual.board_size,
            own=dict(actual.own),
            opponent=dict(self.scent.opponent) if self.publishable() else {},
        )


def positive_cells(posterior: tuple) -> list[tuple[Coord, float]]:
    """Every (cell, weight) pair in `posterior` carrying positive mass --
    the weighted opponent-trail emission, skipping zero-mass cells (barriers,
    or a delta's zero cells) rather than emitting board_size**2 no-op calls
    every turn.

    Moved here from `beliefadapter._positive_cells` because both the strategy
    map's Regime-B emission and the display map's emission need it, and
    CLAUDE.md extracts at the second copy rather than after it.
    """
    return [
        ((row, col), value)
        for row, cells in enumerate(posterior)
        for col, value in enumerate(cells)
        if value > 0.0
    ]
