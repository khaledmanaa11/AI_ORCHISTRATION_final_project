"""The six terminal predicates, in the order RULES-RESOLUTION.md Sec3 fixes.

BOOK predicates must fire under both BOOK_ONLY and PREFERRED. The two NEGOTIATED
predicates must fire under PREFERRED and must NOT fire under BOOK_ONLY -- that
asymmetry is the whole point of the separate resolution block, and a peer running
BOOK_ONLY must reach the same verdict we do on every BOOK row.
"""

from pursuit.constants import Outcome
from pursuit.sdk.actions import CopAction
from pursuit.sdk.resolve import resolve_turn
from pursuit.sdk.terminal import is_walled_in
from pursuit.shared.resolution import BOOK_ONLY, PREFERRED, ResolutionRules
from pursuit.shared.state import GameState


def _state(cop, thief, barriers=frozenset(), placed=0, turn=0):
    """Build a GameState with only the fields a test cares about."""
    return GameState(
        cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn
    )


def test_p1_barrier_on_the_thiefs_pre_move_cell_captures(default_params):
    """Rule 46 / Sec3.4: 'the cell where the thief stands at that moment'."""
    pre = _state(cop=(2, 2), thief=(2, 3))
    for rules in (BOOK_ONLY, PREFERRED):
        _, outcome = resolve_turn(
            pre, CopAction(barrier=(2, 3)), (2, 3), default_params, rules
        )
        assert outcome is Outcome.CAPTURE


def test_p2_barrier_race_captures_only_when_negotiated(default_params):
    """The thief stepped into the cell being sealed -- undefined by the book."""
    pre = _state(cop=(2, 2), thief=(2, 4))
    _, agreed = resolve_turn(
        pre, CopAction(barrier=(2, 3)), (2, 3), default_params, PREFERRED
    )
    assert agreed is Outcome.CAPTURE

    post, book = resolve_turn(
        pre, CopAction(barrier=(2, 3)), (2, 3), default_params, BOOK_ONLY
    )
    assert book is None
    assert post.thief == (2, 4), "held at its pre-turn cell, never placed on a wall"


def test_p3_same_cell_captures(default_params):
    """Sec3.5: 'the cop lands on the thief's cell' -- both landing on one cell."""
    pre = _state(cop=(1, 2), thief=(3, 2))
    for rules in (BOOK_ONLY, PREFERRED):
        _, outcome = resolve_turn(
            pre, CopAction(move=(2, 2)), (2, 2), default_params, rules
        )
        assert outcome is Outcome.CAPTURE


def test_p4_swap_captures_only_when_negotiated(default_params):
    """Without this the two agents pass through one another.

    Note we agree the swap explicitly rather than via PREFERRED: our shipped
    proposal deliberately DECLINES the swap, because making it a capture was
    measured to cost the thief seat 88 points of survival against a barrier-blind
    chaser while gaining the cop seat nothing (see resolution.py). The engine
    still has to implement it correctly in case an opponent proposes it.
    """
    swap_agreed = ResolutionRules(capture_on_barrier_race=False, capture_on_swap=True)
    pre = _state(cop=(2, 2), thief=(2, 3))
    _, agreed = resolve_turn(
        pre, CopAction(move=(2, 3)), (2, 2), default_params, swap_agreed
    )
    assert agreed is Outcome.CAPTURE

    post, book = resolve_turn(
        pre, CopAction(move=(2, 3)), (2, 2), default_params, BOOK_ONLY
    )
    assert book is None
    assert (post.cop, post.thief) == ((2, 3), (2, 2))


def test_p5_walled_in_thief_is_captured(default_params):
    """Rule 47 -- unreachable dead code in the sequential engine, live here.

    The thief sits in a corner with both open neighbours already barriered; the
    cop seals nothing new and simply stays put, so the capture comes from the
    thief's own position rather than from contact.
    """
    pre = _state(
        cop=(3, 3), thief=(0, 0), barriers=frozenset({(0, 1), (1, 0)}), placed=2
    )
    for rules in (BOOK_ONLY, PREFERRED):
        _, outcome = resolve_turn(
            pre, CopAction(move=(3, 3)), (0, 0), default_params, rules
        )
        assert outcome is Outcome.CAPTURE


def test_p5_does_not_consult_stay(default_params):
    """The book's condition is about the four adjacent cells, not about STAY.

    STAY is always a legal move, which is exactly why the old
    `if not get_legal_moves(...)` check could never fire.
    """
    assert is_walled_in((0, 0), frozenset({(0, 1), (1, 0)}), default_params.board_size)
    assert not is_walled_in((0, 0), frozenset({(0, 1)}), default_params.board_size)


def test_p6_survival_at_the_threshold(default_params):
    """Sec3.5: the thief survives the agreed number of valid steps."""
    pre = _state(cop=(0, 0), thief=(3, 3), turn=default_params.survival_threshold - 1)
    _, outcome = resolve_turn(
        pre, CopAction(move=(0, 1)), (3, 4), default_params, PREFERRED
    )
    assert outcome is Outcome.SURVIVAL


def test_capture_beats_survival_on_the_final_turn(default_params):
    """Order matters: a capture landed on the last turn is a capture."""
    pre = _state(cop=(1, 2), thief=(3, 2), turn=default_params.survival_threshold - 1)
    _, outcome = resolve_turn(
        pre, CopAction(move=(2, 2)), (2, 2), default_params, PREFERRED
    )
    assert outcome is Outcome.CAPTURE


def test_play_continues_when_no_predicate_fires(default_params):
    """The ordinary case: both agents move, nothing terminates."""
    pre = _state(cop=(0, 0), thief=(6, 6))
    _, outcome = resolve_turn(
        pre, CopAction(move=(0, 1)), (6, 5), default_params, PREFERRED
    )
    assert outcome is None
