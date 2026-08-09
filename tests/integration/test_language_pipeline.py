"""04-12 must_haves: the Figure 7 call order (book Sec6.2, p.43/PDF 59) and
a full two-peer game carrying a real hint + direction-token move every
turn. No test here performs network I/O: the order test uses a
`FakeProvider`, the full-game test degrades to the real `NO_KEY` path.
"""

from __future__ import annotations

import dataclasses
import json

from pursuit.network import turn_actions, turn_language_io
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.brain_wiring import build_brain_and_scent
from pursuit.network.hint_payload import HintKey, Intent
from pursuit.network.language_wiring import build_language_runtime
from pursuit.network.move_payload import decode as decode_move
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from pursuit.services.llm.provider import LlmResult
from tests.integration.two_peer_game import play_two_peer_game
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


async def test_two_peer_game_carries_a_direction_move_and_a_hint_every_turn(
    tmp_path, monkeypatch,
):
    """A complete two-peer game (04-12's own harness, RESEARCH Pattern 5):
    every turn logs a direction-token move and a legal hint with an
    `intent` flag on BOTH sides, and the final score matches a direct
    engine simulation of the same recorded action sequence."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a = load_agent_config("config/police")
    cfg_b = load_agent_config("config/thief")

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="lang-pipeline", log_dir=tmp_path,
    )

    assert outcome_a is not None and outcome_a == outcome_b

    for ctx, log_path in ((ctx_a, tmp_path / "a.jsonl"), (ctx_b, tmp_path / "b.jsonl")):
        events = [_json_line(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        language_turns = [e for e in events if e["event"] == "language_turn"]
        assert language_turns, f"{ctx.role}: no language_turn records at all"
        for record in language_turns:
            outgoing = record["outgoing_hint"]
            assert outgoing["text"]
            assert len(outgoing["text"].split()) <= cfg_a.language.model["hint_word_limit"]
            assert outgoing["intent"] in (Intent.TRUTH.value, Intent.LIE.value)
        moves = [e for e in events if e["event"] == "message_sent" and e["envelope"]["type"] == "move"]
        for record in moves:
            assert "x" not in record["envelope"]["payload"]
            assert "direction" in record["envelope"]["payload"]

    replayed_outcome, replayed_state = _replay_from_log(tmp_path / "a.jsonl", cfg_a)
    assert replayed_outcome == outcome_a
    assert replayed_state == ctx_a.state


def _json_line(line: str) -> dict:
    return json.loads(line)


def _replay_from_log(log_path, cfg_a):
    """Reconstruct the (cop_action, thief_move) sequence purely from ctx_a's
    OWN JSONL log, in file order, and replay it through engine.resolve_turn
    from a fresh make_state -- proving the log alone is enough to reproduce
    the scored game (rule 20's replay viewer needs exactly this)."""
    params = cfg_a.params
    events = [_json_line(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    cop_cell, thief_cell = params.cop_start, params.thief_start
    pending_cop, pending_thief = None, None
    sequence: list[tuple[CopAction, tuple]] = []
    for record in events:
        if record["event"] not in ("message_sent", "message_received"):
            continue
        envelope = record["envelope"]
        if envelope["type"] != "move":
            continue
        pre = cop_cell if envelope["sender"] == "police" else thief_cell
        resolved = decode_move(envelope["payload"], pre, params)
        assert resolved.ok, f"unreplayable move: {envelope}"
        if envelope["sender"] == "police":
            pending_cop = CopAction(move=resolved.cell)
        else:
            pending_thief = resolved.cell
        if pending_cop is not None and pending_thief is not None:
            sequence.append((pending_cop, pending_thief))
            cop_cell, thief_cell = pending_cop.move, pending_thief
            pending_cop, pending_thief = None, None

    state = engine.make_state(params)
    outcome = None
    for cop_action, thief_move in sequence:
        state, outcome = engine.resolve_turn(state, cop_action, thief_move, params, cfg_a.rules)
        if outcome is not None:
            break
    return outcome, state
