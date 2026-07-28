"""Tests for capture detection and outcome scoring (BASE-03..07)."""

from pursuit.constants import Outcome
from pursuit.shared.capture import detect_capture, evaluate_turn_end
from pursuit.shared.outcome import score_outcome
from pursuit.shared.state import GameState


def test_cop_on_thief_capture(default_params) -> None:
    """Cop on same cell as thief → CAPTURE (BASE-03: coordinate overlap)."""
    state = GameState(
        cop=(3, 3),
        thief=(3, 3),
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )
    result = detect_capture(state, default_params)
    assert result is Outcome.CAPTURE


def test_barrier_on_thief_capture(default_params, start_state) -> None:
    """Barrier placed on thief's cell → CAPTURE (BASE-04)."""
    state = GameState(
        cop=(0, 0),
        thief=start_state.thief,
        barriers=frozenset({start_state.thief}),
        barriers_placed=1,
        turn=0,
    )
    result = detect_capture(state, default_params)
    assert result is Outcome.CAPTURE


def test_no_legal_move_capture(default_params) -> None:
    """Thief's own cell in barriers (BASE-04/BASE-05) → CAPTURE.

    As per plan analysis, a pure BASE-05 state without BASE-04 is geometrically
    impossible (STAY is always legal unless thief's own cell is a barrier).
    This test uses thief-in-barrier, which triggers BASE-04 first; it also
    demonstrates the zero-legal-moves case (STAY is the thief's own cell,
    which is now a barrier).
    """
    state = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset({(3, 3)}),
        barriers_placed=1,
        turn=0,
    )
    result = detect_capture(state, default_params)
    assert result is Outcome.CAPTURE


def test_one_move_available_no_capture(default_params, start_state) -> None:
    """Thief with at least one legal move is NOT captured (BASE-05 negative)."""
    # Surround three orthogonal neighbors; (3,4) remains open plus STAY=(3,3).
    state = GameState(
        cop=(0, 0),
        thief=(3, 3),
        barriers=frozenset({(2, 3), (4, 3), (3, 2)}),
        barriers_placed=3,
        turn=0,
    )
    result = detect_capture(state, default_params)
    assert result is None


def test_survival_at_threshold(default_params) -> None:
    """turn == survival_threshold with no capture → SURVIVAL (BASE-06, D-16)."""
    state = GameState(
        cop=(0, 0),
        thief=(6, 6),
        barriers=frozenset(),
        barriers_placed=0,
        turn=default_params.survival_threshold,
    )
    result = evaluate_turn_end(state, default_params)
    assert result is Outcome.SURVIVAL


def test_game_continues_below_threshold(default_params) -> None:
    """turn < survival_threshold → None (game continues, BASE-06 negative)."""
    state = GameState(
        cop=(0, 0),
        thief=(6, 6),
        barriers=frozenset(),
        barriers_placed=0,
        turn=default_params.survival_threshold - 1,
    )
    result = evaluate_turn_end(state, default_params)
    assert result is None


def test_capture_score(default_params) -> None:
    """CAPTURE outcome scores come from params.score_capture_* (BASE-07, D-14)."""
    cop_score, thief_score = score_outcome(Outcome.CAPTURE, default_params)
    assert cop_score == default_params.score_capture_cop
    assert thief_score == default_params.score_capture_thief


def test_survival_score(default_params) -> None:
    """SURVIVAL outcome scores come from params.score_survival_* (BASE-07, D-14)."""
    cop_score, thief_score = score_outcome(Outcome.SURVIVAL, default_params)
    assert cop_score == default_params.score_survival_cop
    assert thief_score == default_params.score_survival_thief


def test_tie_score(default_params) -> None:
    """TIE outcome returns (score_tie, score_tie) from params (D-14)."""
    cop_score, thief_score = score_outcome(Outcome.TIE, default_params)
    assert cop_score == default_params.score_tie
    assert thief_score == default_params.score_tie


def test_technical_loss_score(default_params) -> None:
    """TECHNICAL_LOSS outcome returns (0, 0) — only literal zero permitted."""
    cop_score, thief_score = score_outcome(Outcome.TECHNICAL_LOSS, default_params)
    assert cop_score == 0
    assert thief_score == 0


def test_score_outcome_invalid_raises(default_params) -> None:
    """Unrecognised outcome raises ValueError (correctness guard)."""
    import pytest

    with pytest.raises(ValueError, match="Unrecognised outcome"):
        score_outcome("not_an_outcome", default_params)  # type: ignore[arg-type]
