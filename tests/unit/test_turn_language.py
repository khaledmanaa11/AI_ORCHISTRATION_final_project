"""Tests for `network/turn_language.py` -- the Figure 7 assembly helpers,
focused on the branches the belief-enabled integration tests never exercise:
no `choose_move`/`brain` at all, and a RAW (non-`BeliefAdapter`) brain."""

from pursuit.network import turn_language
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.language_wiring import build_language_runtime
from pursuit.shared.inference import NO_EVIDENCE
from pursuit.strategy.naive import ChaserCop
from pursuit.strategy.scentfield import ScentField
from tests.unit._fakes_agent import make_ctx


def _language(default_params, seed=1):
    cfg = load_agent_config("config/police")
    return build_language_runtime(
        language=cfg.language, deception=cfg.deception, board_size=default_params.board_size,
        seed=seed,
    )


def test_choose_destination_falls_back_to_first_legal_move_with_no_brain(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="no-brain")
    known = turn_language.known_opponent_cell(ctx, "cop")
    dest = turn_language.choose_destination(ctx, "cop", NO_EVIDENCE, known)
    from pursuit.sdk import engine

    assert dest in engine.legal_moves(ctx.state, "cop", default_params)


def test_choose_destination_uses_a_raw_non_adapter_brain(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="raw-brain")
    ctx.brain = ChaserCop(role="cop", game_params=default_params)
    known = turn_language.known_opponent_cell(ctx, "cop")
    dest = turn_language.choose_destination(ctx, "cop", NO_EVIDENCE, known)
    from pursuit.sdk import engine

    assert dest in engine.legal_moves(ctx.state, "cop", default_params)


def test_build_deception_plan_uses_a_fresh_belief_map_without_an_adapter(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="raw-deception")
    ctx.brain = ChaserCop(role="cop", game_params=default_params)
    ctx.scent_field = ScentField(model=_load_scent(default_params), board_size=default_params.board_size)
    ctx.language = _language(default_params)
    plan = turn_language.build_deception_plan(ctx, "cop", ctx.state, ctx.state.cop)
    assert plan.intent is not None


def test_observe_reliability_is_a_noop_without_a_belief_adapter(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="raw-reliability")
    ctx.brain = None
    turn_language.observe_reliability(ctx, NO_EVIDENCE)  # must not raise


def test_belief_snapshot_returns_all_none_without_a_belief_adapter(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="raw-snapshot")
    ctx.brain = ChaserCop(role="cop", game_params=default_params)
    assert turn_language.belief_snapshot(ctx) == (None, None, None)


def _load_scent(default_params):
    from pursuit.shared.scent_config import load_scent_model

    return load_scent_model("config/police/scent.json")
