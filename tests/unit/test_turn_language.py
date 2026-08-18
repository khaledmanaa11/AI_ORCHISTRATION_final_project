"""Tests for `network/turn_language.py` -- the Figure 7 assembly helpers,
focused on the branches the belief-enabled integration tests never exercise:
no `choose_move`/`brain` at all, and a RAW (non-`BeliefAdapter`) brain."""

from pursuit.constants import MoveSource
from pursuit.network import turn_language
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.language_wiring import build_language_runtime
from pursuit.shared.inference import NO_EVIDENCE
from pursuit.strategy.base import Decision
from pursuit.strategy.naive import ChaserCop
from pursuit.strategy.scentfield import ScentField
from tests.unit._fakes_agent import make_ctx


class _FakeBarrierBrain:
    """A raw (non-`BeliefAdapter`) brain whose `_decide_move` always
    returns a barrier `Decision` -- scripts D-66's barrier-over-the-wire
    path without a real strategy implementation."""

    def __init__(self, own_cell, barrier_cell):
        self._own_cell = own_cell
        self._barrier_cell = barrier_cell

    def _decide_move(self, obs, state):  # noqa: ARG002 -- BrainBase's own seam
        return Decision(move=self._own_cell, source=MoveSource.HEURISTIC, barrier=self._barrier_cell)


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


def test_choose_destination_stashes_a_barrier_from_a_raw_brain_and_resets_it(
    tmp_path, default_params, network_params,
):
    """D-66: choose_destination stays a bare-Coord return, but stashes the
    full Decision's barrier onto ctx.commit_state.chosen_barrier as a side
    effect -- set when the brain places one, reset to None on the very
    next call when it does not (never left stale across turns). Stashing
    requires commit_reveal ON: the pre-Phase-6 flat payload cannot carry a
    barrier, so the off path strips it (rule 15)."""
    import dataclasses

    ctx = make_ctx(tmp_path, default_params, network_params, label="barrier-choice")
    ctx.security = dataclasses.replace(ctx.security, commit_reveal=True)
    own_cell = ctx.state.cop
    barrier_cell = own_cell  # the cop's own cell is always a legal barrier target
    ctx.brain = _FakeBarrierBrain(own_cell, barrier_cell)
    known = turn_language.known_opponent_cell(ctx, "cop")

    dest = turn_language.choose_destination(ctx, "cop", NO_EVIDENCE, known)

    assert dest == own_cell
    assert ctx.commit_state.chosen_barrier == barrier_cell

    # The off path: same brain, same barrier -- stripped at the seam.
    ctx.security = dataclasses.replace(ctx.security, commit_reveal=False)
    turn_language.choose_destination(ctx, "cop", NO_EVIDENCE, known)
    assert ctx.commit_state.chosen_barrier is None
    ctx.security = dataclasses.replace(ctx.security, commit_reveal=True)

    ctx.brain = None  # a barrier-less branch on the very next call
    turn_language.choose_destination(ctx, "cop", NO_EVIDENCE, known)
    assert ctx.commit_state.chosen_barrier is None


def _load_scent(default_params):
    from pursuit.shared.scent_config import load_scent_model

    return load_scent_model("config/police/scent.json")
