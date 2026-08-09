"""04-12 must_haves: the Figure 7 call order (book Sec6.2, p.43/PDF 59).
No test here performs network I/O -- a `FakeProvider` stands in.

The full two-peer game test (+ its `_replay_from_log` helper) lives in the
sibling `test_language_pipeline_replay.py`, split out at the 150-code-line
gate (06-02: D-58/D-66's shape-aware replay logic pushed this file over).
"""

from __future__ import annotations

import dataclasses

from pursuit.network import turn_actions, turn_language_io
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.brain_wiring import build_brain_and_scent
from pursuit.network.hint_payload import HintKey, Intent
from pursuit.network.language_wiring import build_language_runtime
from pursuit.services.llm.provider import LlmResult
from tests.unit._fakes_agent import make_ctx


class _FakeProvider:
    """Returns a schema-valid decode response or a short bluff phrase --
    never touches a network, never raises."""

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        if schema is not None:
            parsed = {"region": None, "cells": [], "direction": None, "confidence": 0.0}
            return LlmResult(text="{}", parsed=parsed, input_tokens=0, output_tokens=0)
        return LlmResult(text="Nothing to report.", parsed=None, input_tokens=0, output_tokens=0)


def _wire_language(ctx, *, default_params, belief_cfg, scent_model):
    """Real brain/scent/language runtime, provider swapped for the fake."""
    cfg = load_agent_config("config/police")
    brain, scent_field = build_brain_and_scent(
        engine_role="cop", strategy=cfg.strategy, game_params=default_params,
        belief=belief_cfg, scent=scent_model,
    )
    language = build_language_runtime(
        language=cfg.language, deception=cfg.deception, board_size=default_params.board_size,
        seed=belief_cfg.belief.seed,
    )
    fake = _FakeProvider()
    language.decode_context = dataclasses.replace(language.decode_context, provider=fake)
    language.bluff_context = dataclasses.replace(language.bluff_context, provider=fake)
    ctx.brain, ctx.scent_field, ctx.language = brain, scent_field, language
    return ctx


async def test_figure_7_order_is_decode_then_move_then_deception_then_compose(
    tmp_path, default_params, network_params, belief_cfg, scent_model,
):
    """must_haves truths #1: decode -> belief/move -> deception -> bluff,
    once per turn, asserted with a spy -- deception is planned AFTER the
    move so its claim can reference a move already committed to."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="fig7")
    _wire_language(ctx, default_params=default_params, belief_cfg=belief_cfg, scent_model=scent_model)
    ctx.incoming_hints["thief"] = {
        HintKey.TEXT.value: "heading south", HintKey.INTENT.value: Intent.TRUTH.value,
        HintKey.TURN.value: 0,
    }

    order: list[str] = []

    real_decode = turn_actions.decode_turn_hint

    async def spy_decode(*a, **kw):
        order.append("decode")
        return await real_decode(*a, **kw)

    real_choose = turn_actions.choose_destination

    def spy_choose(*a, **kw):
        order.append("choose")
        return real_choose(*a, **kw)

    real_plan = turn_language_io.build_deception_plan

    def spy_plan(*a, **kw):
        order.append("plan")
        return real_plan(*a, **kw)

    real_compose = turn_language_io.compose_outgoing

    async def spy_compose(*a, **kw):
        order.append("compose")
        return await real_compose(*a, **kw)

    turn_actions.decode_turn_hint = spy_decode
    turn_actions.choose_destination = spy_choose
    turn_language_io.build_deception_plan = spy_plan
    turn_language_io.compose_outgoing = spy_compose
    try:
        await turn_actions.take_my_turn(ctx)
    finally:
        turn_actions.decode_turn_hint = real_decode
        turn_actions.choose_destination = real_choose
        turn_language_io.build_deception_plan = real_plan
        turn_language_io.compose_outgoing = real_compose

    assert order == ["decode", "choose", "plan", "compose"]
