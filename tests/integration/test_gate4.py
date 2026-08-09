"""GATE-4 frozen as a CI test (04-14 Task 3): the book's Sec10.4 milestone-4
STRUCTURAL absolutes, mocked, no key, no network -- so Phase 5's tunnelling
or Phase 6's commit-reveal can never silently break the language channel
without a red test, even though a game with no hints still finishes.

The MEASURED numbers (decode accuracy, wall time, token spend, the belief
on/off comparison) live in docs/phases/phase-4/GATE-4-MEASUREMENT.md and are
produced by scripts/measure_gate4.py -- a human reruns that (with a real
ANTHROPIC_API_KEY) before submission (D-32). This module only pins the
STRUCTURAL absolutes that never legitimately change: a hint every turn, zero
outgoing coordinates, intent committed before text, the scent digest
verified (matching) at handshake.
"""

from __future__ import annotations

import json

from pursuit.network import turn_language_io
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.hint_payload import Intent
from pursuit.shared.hint_guard import assert_no_coordinates
from pursuit.shared.scent_config import scent_digest
from tests.integration.two_peer_game import play_two_peer_game

_CFG_A = "config/police"
_CFG_B = "config/thief"


def _events(log_path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _language_turns(records: list[dict]) -> list[dict]:
    return [r for r in records if r["event"] == "language_turn"]


def _moves(records: list[dict]) -> list[dict]:
    return [
        r for r in records if r["event"] == "message_sent" and r["envelope"]["type"] == "move"
    ]


async def test_handshake_scent_digest_matches_before_any_move(tmp_path, monkeypatch):
    """The scent digest both peers compute and compare at handshake
    (D-46, rule 23) is identical -- the shipped scent.json is the SAME
    locked payload on both sides, verified with the real `scent_digest()`,
    then re-confirmed by actually playing a full handshake+game."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)
    assert scent_digest(cfg_a.scent) == scent_digest(cfg_b.scent)

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="gate4-handshake", log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b


async def test_a_hint_rides_every_turn_with_no_outgoing_coordinate(tmp_path, monkeypatch):
    """LANG-01/LANG-02, frozen: over a full game, both sides send exactly
    one hint per turn played, every hint is within the legal length, both
    `intent` values are representable, and no outgoing payload (hint OR
    move) ever carries a numeric coordinate (rule 27)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="gate4-hints", log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b

    limit = cfg_a.language.model["hint_word_limit"]
    for ctx, log_path in ((ctx_a, tmp_path / "a.jsonl"), (ctx_b, tmp_path / "b.jsonl")):
        records = _events(log_path)
        turns = _language_turns(records)
        assert turns, f"{ctx.role}: no language_turn records at all"
        assert len(turns) == ctx.state.turn, f"{ctx.role}: hint count does not match turns played"
        for record in turns:
            outgoing = record["outgoing_hint"]
            assert outgoing["text"], "a turn shipped with no hint text"
            assert len(outgoing["text"].split()) <= limit
            assert outgoing["intent"] in (Intent.TRUTH.value, Intent.LIE.value)
            assert_no_coordinates(outgoing["text"])  # raises ValueError on a leak
        for move in _moves(records):
            payload = move["envelope"]["payload"]
            assert "x" not in payload
            assert "y" not in payload


async def test_intent_is_always_committed_before_the_hint_text_exists(tmp_path, monkeypatch):
    """LANG-03/rule 25, frozen structurally: `send_turn_hint` calls
    `build_deception_plan()` (which fixes `plan.intent`) and only then
    calls `compose_outgoing(plan, ...)` -- `plan` is a required positional
    argument, so no call producing hint text can exist without an intent
    already decided. Verified with a live call-order spy over a full game,
    mirroring test_language_pipeline.py's own Figure-7 order test but at
    GATE-4's own full-game granularity."""
    order: list[str] = []
    real_plan = turn_language_io.build_deception_plan
    real_compose = turn_language_io.compose_outgoing

    def spy_plan(*args, **kwargs):
        order.append("plan")
        return real_plan(*args, **kwargs)

    async def spy_compose(*args, **kwargs):
        order.append("compose")
        return await real_compose(*args, **kwargs)

    turn_language_io.build_deception_plan = spy_plan
    turn_language_io.compose_outgoing = spy_compose
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    try:
        cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)
        outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
            cfg_a, cfg_b, game_uid="gate4-order", log_dir=tmp_path,
        )
    finally:
        turn_language_io.build_deception_plan = real_plan
        turn_language_io.compose_outgoing = real_compose

    assert outcome_a is not None and outcome_a == outcome_b
    assert order, "no turn ever planned/composed a hint"
    for i in range(0, len(order), 2):
        assert order[i : i + 2] == ["plan", "compose"], "intent was not committed before text"
