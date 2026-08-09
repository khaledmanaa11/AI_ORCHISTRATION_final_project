"""Registry wiring (Task 3, D-43), continued: seeded byte-for-byte
reproducibility and action-replay scoring.

Split out of `test_belief_policy.py` at the 150-code-line ceiling
(CLAUDE.md: split files, never compress code to fit); imports that module's
`play` (a plain function, not a fixture -- importing it does not shadow a
fixture the way importing `belief_cfg`/`scent_model` would). `belief_cfg`,
`scent_model` and `default_params` still come from conftest.py, applied
automatically -- no import needed.
"""

from __future__ import annotations

from pursuit.sdk.resolve import make_state, resolve_turn
from pursuit.shared.outcome import score_outcome
from pursuit.shared.resolution import PREFERRED
from pursuit.strategy import registry
from pursuit.strategy.scentfield import ScentField
from tests.integration.conftest import strategy_params
from tests.integration.test_belief_policy import play


def test_two_seeded_games_are_byte_identical(default_params, belief_cfg, scent_model):
    def run():
        cop = registry.build_brain(
            "cop", strategy_params("cop"), default_params,
            belief_config=belief_cfg, scent_model=scent_model,
        )
        thief = registry.build_brain(
            "thief", strategy_params("thief"), default_params,
            belief_config=belief_cfg, scent_model=scent_model,
        )
        cop_field = ScentField(model=scent_model, board_size=default_params.board_size)
        thief_field = ScentField(model=scent_model, board_size=default_params.board_size)
        return play(cop, thief, default_params, cop_field, thief_field)

    first, second = run(), run()
    assert first == second


def test_replaying_the_recorded_actions_scores_identically(default_params, belief_cfg, scent_model):
    """The belief layer decides moves, never resolves them: replaying the
    SAME recorded (cop_action, thief_move) pairs through resolve_turn alone
    reaches the same outcome, state and score."""
    cop = registry.build_brain(
        "cop", strategy_params("cop"), default_params, belief_config=belief_cfg, scent_model=scent_model
    )
    thief = registry.build_brain(
        "thief", strategy_params("thief"), default_params,
        belief_config=belief_cfg, scent_model=scent_model,
    )
    cop_field = ScentField(model=scent_model, board_size=default_params.board_size)
    thief_field = ScentField(model=scent_model, board_size=default_params.board_size)
    outcome, state, actions = play(cop, thief, default_params, cop_field, thief_field)
    assert outcome is not None

    replay_state = make_state(default_params)
    replay_outcome = None
    for cop_action, thief_move in actions:
        replay_state, replay_outcome = resolve_turn(
            replay_state, cop_action, thief_move, default_params, PREFERRED
        )
        if replay_outcome is not None:
            break

    assert replay_outcome == outcome
    assert replay_state == state
    assert score_outcome(replay_outcome, default_params) == score_outcome(outcome, default_params)
