"""BrainBase seam: the only interface the rest of the system knows about (STRAT-03).

Observation and Decision are the frozen data contracts that cross the seam;
BrainBase is the abstract move/decision interface every playable brain must
implement. No policy logic lives here -- ValueSearchBrain, ChaserCop and
GreedyEvader (docs/PRD_matrix_mover.md) implement it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pursuit.constants import MoveSource
from pursuit.shared.state import GameState


@dataclass(frozen=True)
class Observation:
    """The encoded view of the board a brain's Q-key is built from.

    Deliberately carries no board -- callers needing the real board (bfs,
    fallback, the barrier sub-policy) receive the GameState explicitly
    alongside this Observation instead (D-05), so the barrier bitmap never
    bloats the encoding input.

    target_cell is a *believed* target cell (D-11): Phase 3 populated it
    with the known target (the Stage-3 gate condition). Phase 4's
    `strategy/beliefadapter.py` populates it with a cell SAMPLED from the
    belief posterior instead -- D-43 overrides this docstring's earlier
    "argmax" guess: an argmax target makes pursuit deterministic given the
    opponent's own model of our belief, and a deterministic pursuit is
    exploitable in a one-counted-game league (rule 52). The field's shape
    never changes across either source -- no brain, encoding, or trained
    Q-table needs to change when the value's origin does.
    """

    own_cell: tuple[int, int]
    target_cell: tuple[int, int]
    blocked_mask: int
    barriers_used: int
    turn_index: int


@dataclass(frozen=True)
class Decision:
    """A brain's chosen move, with provenance and an optional barrier.

    source names what produced move (equilibrium | exploration | heuristic |
    fallback) as a data field, never an inference -- 03-AI-SPEC.md Sec5
    dimensions E2 (decision provenance) and E3 (fallback trigger
    correctness) assert on decision.source directly. Every brain must set it
    truthfully; it must never default silently to a value it did not
    actually produce.

    barrier is Optional and is always None for the thief -- only the cop's
    _decide_move may set it (D-12, STRAT-05).
    """

    move: tuple[int, int]
    source: MoveSource
    barrier: tuple[int, int] | None = None


class BrainBase(ABC):
    """The one interface the rest of the system knows about (STRAT-03).

    Both abstract methods take the GameState explicitly as a second
    argument: Observation is the encoded Q-key input and deliberately
    carries no board, but bfs() (03-03), fallback.pick() (03-04), and
    choose_barrier() (03-07) all need the real board to operate. Passing
    state explicitly keeps the barrier bitmap out of the encoding input
    entirely, rather than smuggling it into Observation (D-05).
    """

    @abstractmethod
    def _pick_move(self, obs: Observation, state: GameState) -> Decision:
        """Choose a movement Decision.

        The algorithm chooses the move here -- the language model never
        does (rule 25 / STRAT-07). Returns a full Decision, not a bare
        cell, so source travels with the move.
        """
        raise NotImplementedError

    @abstractmethod
    def _decide_move(self, obs: Observation, state: GameState) -> Decision:
        """Call _pick_move, then attach the cop's barrier (thief: None)."""
        raise NotImplementedError
