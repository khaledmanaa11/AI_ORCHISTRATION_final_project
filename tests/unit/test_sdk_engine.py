"""QUAL-01 delegation tests for the SDK engine facade (plan 01-04, joint-turn
edition per plan 03-14 / RULES-RESOLUTION.md).

One test per SDK method. Each test verifies delegation behaviour only --
internal logic (movement, terminal predicates, scoring) is covered by the
respective shared/sdk module test files (test_board.py, test_resolve.py,
test_terminal.py, test_outcome.py). No numeric game-parameter values are
hardcoded here.

apply_cop_action/apply_thief_move/check_capture are gone (sdk/engine.py no
longer defines them -- resolve_turn replaces all three at once); this file
now also pins that engine.py re-exports resolve_turn/cop_actions/
thief_actions from sdk/resolve.py and sdk/actions.py, so the facade stays
the sole public entry point (QUAL-01).
"""

from pursuit.constants import Outcome
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from pursuit.shared.resolution import PREFERRED
from pursuit.shared.state import GameState


def test_make_state(default_params):
    """make_state returns a canonical GameState from config start positions."""
    state = engine.make_state(default_params)
    assert state.cop == default_params.cop_start
    assert state.thief == default_params.thief_start
    assert state.barriers == frozenset()
    assert state.barriers_placed == 0
    assert state.turn == 0


def test_legal_moves_delegates(default_params, start_state):
    """legal_moves delegates to get_legal_moves; stay is always legal."""
    moves = engine.legal_moves(start_state, "thief", default_params)
    assert isinstance(moves, list)
    assert start_state.thief in moves


def test_resolve_turn_re_exported_from_sdk_resolve(default_params, start_state):
    """engine.resolve_turn IS sdk.resolve.resolve_turn -- a re-export, not a
    reimplementation (QUAL-01): both moves apply from one pre-turn state."""
    dest = (0, 1)
    new_state, outcome = engine.resolve_turn(
        start_state, CopAction(move=dest), start_state.thief, default_params, PREFERRED
    )
    assert new_state.cop == dest
    assert new_state.thief == start_state.thief
    assert new_state.turn == start_state.turn + 1
    assert outcome is None


def test_resolve_turn_barrier_on_thief_is_capture(default_params):
    """Cop adjacent to the thief places a barrier on the thief's pre-turn
    cell -> CAPTURE (rule 46, BOOK predicate 1)."""
    state = GameState(cop=(3, 2), thief=(3, 3), barriers=frozenset(), barriers_placed=0, turn=0)
    new_state, outcome = engine.resolve_turn(
        state, CopAction(barrier=state.thief), state.thief, default_params, PREFERRED
    )
    assert state.thief in new_state.barriers
    assert outcome is Outcome.CAPTURE


def test_cop_actions_and_thief_actions_re_exported(default_params, start_state):
    """engine.cop_actions/thief_actions re-export sdk.actions' generators
    (scope item A) so a caller never has to reach past the facade."""
    assert engine.thief_actions(start_state, default_params) == engine.legal_moves(
        start_state, "thief", default_params
    )
    actions = engine.cop_actions(start_state, default_params)
    assert all(isinstance(a, CopAction) for a in actions)
    assert any(a.move is not None for a in actions)


def test_score_delegates(default_params):
    """score delegates to score_outcome; values match params.score_capture_*."""
    cop_score, thief_score = engine.score(Outcome.CAPTURE, default_params)
    assert cop_score == default_params.score_capture_cop
    assert thief_score == default_params.score_capture_thief
