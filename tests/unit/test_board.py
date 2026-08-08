"""Tests for BASE-01 — board movement validation tests."""

from pathlib import Path

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams, load_game_params
from pursuit.shared.state import GameState

POLICE_CONFIG = Path(__file__).parent.parent.parent / "config" / "police" / "game_params.json"


def test_orthogonal_move_accepted(default_params: GameParams) -> None:
    """An orthogonal (N/S/E/W) step to an empty cell is accepted."""
    params = load_game_params(POLICE_CONFIG)
    state = GameState(
        cop=(1, 1),
        thief=(5, 5),
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )
    moves = get_legal_moves(state, "cop", params)
    assert (0, 1) in moves  # NORTH
    assert (2, 1) in moves  # SOUTH
    assert (1, 0) in moves  # WEST
    assert (1, 2) in moves  # EAST
    assert (1, 1) in moves  # STAY


def test_diagonal_move_rejected(default_params: GameParams) -> None:
    """A diagonal step is always rejected."""
    params = load_game_params(POLICE_CONFIG)
    state = GameState(
        cop=(1, 1),
        thief=(5, 5),
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )
    moves = get_legal_moves(state, "cop", params)
    assert (0, 0) not in moves  # NW diagonal
    assert (0, 2) not in moves  # NE diagonal
    assert (2, 0) not in moves  # SW diagonal
    assert (2, 2) not in moves  # SE diagonal


def test_stay_is_legal(default_params: GameParams) -> None:
    """Staying in place is always a legal move, even when surrounded by barriers."""
    params = load_game_params(POLICE_CONFIG)
    state = GameState(
        cop=(3, 3),
        thief=(0, 6),
        barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}),
        barriers_placed=4,
        turn=0,
    )
    moves = get_legal_moves(state, "cop", params)
    assert (3, 3) in moves  # stay must always be legal (D-13)
    assert len(moves) == 1  # only stay (all orthogonal neighbors are barriers)


def test_out_of_bounds_rejected(default_params: GameParams) -> None:
    """A move that would leave the board is rejected."""
    params = load_game_params(POLICE_CONFIG)
    state = GameState(
        cop=(0, 0),
        thief=(5, 5),
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )
    moves = get_legal_moves(state, "cop", params)
    assert (-1, 0) not in moves  # north of row 0 is OOB
    assert (0, -1) not in moves  # west of col 0 is OOB


def test_onto_barrier_rejected(default_params: GameParams) -> None:
    """A move onto a barriered cell is rejected (D-08)."""
    params = load_game_params(POLICE_CONFIG)
    state = GameState(
        cop=(2, 2),
        thief=(5, 5),
        barriers=frozenset({(1, 2)}),
        barriers_placed=1,
        turn=0,
    )
    moves = get_legal_moves(state, "cop", params)
    assert (1, 2) not in moves  # barriered cell not in legal moves
