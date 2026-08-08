"""The six terminal predicates of a joint turn, in evaluation order.

Every predicate is a function of the PRE-turn and POST-turn positions together --
never of one snapshot. That is the structural reason the sequential engine could
not be repaired by reordering calls: it destroyed the pre-turn positions before
either agent had finished acting, and a swap is invisible without both.

Order matters. Capture is tested before survival, so a capture landed on the final
turn is a capture and not a survival. Full sourcing per predicate is in
docs/phases/phase-3/RULES-RESOLUTION.md Sec3; BOOK rows are unconditional, the two
NEGOTIATED rows are gated on ResolutionRules.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from pursuit.shared.state import GameState

Coord = tuple[int, int]


def is_walled_in(cell: Coord, barriers: frozenset, board_size: int) -> bool:
    """True when all four orthogonal neighbours of *cell* are blocked or off-board.

    Rule 47 / book Sec3.4 p.21: "a thief imprisoned without any legal move (all
    adjacent cells blocked and/or at the board edges) is likewise considered
    captured." The book's condition is about the four ADJACENT cells and says
    nothing about staying put, so this deliberately does not consult STAY --
    which is what made the old `if not get_legal_moves(...)` check unreachable.
    """
    row, col = cell
    for neighbour in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
        in_bounds = 0 <= neighbour[0] < board_size and 0 <= neighbour[1] < board_size
        if in_bounds and neighbour not in barriers:
            return False
    return True


def terminal_outcome(
    pre: GameState,
    post: GameState,
    barrier: Coord | None,
    raced: bool,
    params: GameParams,
    rules: ResolutionRules,
) -> Outcome | None:
    """Return the outcome of a resolved joint turn, or None if play continues.

    Parameters
    ----------
    pre:
        The shared pre-turn snapshot both agents chose their actions from.
    post:
        The resolved snapshot, with both moves applied, any barrier added, and
        the turn counter already advanced by exactly one.
    barrier:
        The cell the cop sealed this turn, or None if the cop moved instead.
    raced:
        True when the thief's chosen destination was the cell the cop sealed this
        same turn. Resolved in resolve_turn (the thief is held at its pre-turn
        cell either way); this flag only decides whether that is a capture.
    params:
        Game parameters; supplies board_size and survival_threshold.
    rules:
        The negotiated predicates. BOOK_ONLY disables both optional rows.
    """
    # 1. BOOK, rule 46 -- the cop sealed the cell the thief was standing on.
    if barrier is not None and barrier == pre.thief:
        return Outcome.CAPTURE

    # 2. NEGOTIATED -- the thief stepped into the cell being sealed.
    if raced and rules.capture_on_barrier_race:
        return Outcome.CAPTURE

    # 3. BOOK, Sec3.5 -- both agents landed on the same cell.
    if post.cop == post.thief:
        return Outcome.CAPTURE

    # 4. NEGOTIATED -- the agents traded cells; without this they pass through
    #    one another, which no reading of Sec3.4 supports.
    if rules.capture_on_swap and post.cop == pre.thief and post.thief == pre.cop:
        return Outcome.CAPTURE

    # 5. BOOK, rule 47 -- the thief is walled in.
    if is_walled_in(post.thief, post.barriers, params.board_size):
        return Outcome.CAPTURE

    # 6. BOOK, Sec3.5 -- the thief survived the agreed number of joint turns.
    if post.turn >= params.survival_threshold:
        return Outcome.SURVIVAL

    return None
