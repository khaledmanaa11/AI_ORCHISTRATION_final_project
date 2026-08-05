"""SDK facade for the Phase 1 pursuit game engine (QUAL-01).

This module is the sole public entry point for Phase 2 and beyond.
It wraps shared/board, shared/barrier, shared/capture, and shared/outcome.
No business logic lives here — this is wiring only.

D-12 turn order:
  1. Cop acts: apply_cop_action (move XOR barrier + capture check).
  2. Thief moves: apply_thief_move (move + turn increment + survival check).
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.shared.barrier import place_barrier
from pursuit.shared.board import apply_move, get_legal_moves
from pursuit.shared.capture import detect_capture, evaluate_turn_end
from pursuit.shared.config import GameParams
from pursuit.shared.outcome import score_outcome
from pursuit.shared.state import GameState, increment_turn


def make_state(params: GameParams) -> GameState:
    """Create canonical initial GameState from config start positions."""
    return GameState(
        cop=params.cop_start,
        thief=params.thief_start,
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )


def legal_moves(
    state: GameState, agent: str, params: GameParams
) -> list[tuple[int, int]]:
    """Return legal moves for agent. Delegates to get_legal_moves."""
    return get_legal_moves(state, agent, params)


def apply_cop_action(
    state: GameState,
    move_to: tuple[int, int] | None,
    barrier_at: tuple[int, int] | None,
    params: GameParams,
) -> tuple[GameState, Outcome | None]:
    """Apply the cop's move XOR barrier, then detect capture. D-12 steps 1-2."""
    if barrier_at is not None:
        if move_to is not None and move_to != state.cop:
            raise ValueError(
                f"cop action cannot move to {move_to} and place barrier at {barrier_at}"
            )
        after_barrier = place_barrier(state, barrier_at, params)
        outcome = detect_capture(after_barrier, params)
        return after_barrier, outcome

    after_move = apply_move(state, "cop", move_to) if move_to is not None else state
    outcome = detect_capture(after_move, params)
    return after_move, outcome


def apply_thief_move(
    state: GameState,
    move_to: tuple[int, int],
    params: GameParams,
) -> tuple[GameState, Outcome | None]:
    """Apply thief's move, increment turn, evaluate end condition. D-12 steps 3-4."""
    after_move = apply_move(state, "thief", move_to)
    after_tick = increment_turn(after_move)
    outcome = evaluate_turn_end(after_tick, params)
    return after_tick, outcome


def check_capture(state: GameState, params: GameParams) -> Outcome | None:
    """Detect any capture condition. Delegates to detect_capture."""
    return detect_capture(state, params)


def score(outcome: Outcome, params: GameParams) -> tuple[int, int]:
    """Return (cop_score, thief_score) for an outcome. Delegates to score_outcome."""
    return score_outcome(outcome, params)
