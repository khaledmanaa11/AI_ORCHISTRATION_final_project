"""04-12 must_haves: a full two-peer game carrying a real hint + direction-
token move every turn, replayed purely from ctx_a's own JSONL log. Split
from test_language_pipeline.py at the 150-code-line gate (06-02: D-58/
D-66's shape-aware replay logic pushed the original file over). Degrades
to the real `NO_KEY` path -- no network I/O.
"""

from __future__ import annotations

import json

from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.hint_payload import Intent
from pursuit.network.move_payload import decode as decode_move
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from tests.integration.two_peer_game import play_two_peer_game


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
        # 06-02 (D-58): under commit_reveal (default true) the action rides
        # a `reveal`-typed envelope carrying the composite {move, barrier}
        # dict, not a flat `move`-typed one -- widen the filter and check
        # the shape a coordinate could actually leak at.
        moves = [
            e for e in events
            if e["event"] == "message_sent" and e["envelope"]["type"] in ("move", "reveal")
        ]
        for record in moves:
            envelope = record["envelope"]
            payload = envelope["payload"]
            if envelope["type"] == "reveal":
                assert "x" not in payload["move"]
                assert "direction" in payload["move"]
                if payload.get("barrier") is not None:
                    assert "x" not in payload["barrier"]
                    assert "direction" in payload["barrier"]
            else:
                assert "x" not in payload
                assert "direction" in payload

    replayed_outcome, replayed_state = _replay_from_log(tmp_path / "a.jsonl", cfg_a)
    assert replayed_outcome == outcome_a
    assert replayed_state == ctx_a.state


def _json_line(line: str) -> dict:
    return json.loads(line)


def _replay_from_log(log_path, cfg_a):
    """Reconstruct the (cop_action, thief_move) sequence purely from ctx_a's
    OWN JSONL log, in file order, and replay it through engine.resolve_turn
    from a fresh make_state -- proving the log alone is enough to reproduce
    the scored game (rule 20's replay viewer needs exactly this).

    06-02 (D-58, D-66): a `reveal`-typed record's payload is the composite
    `{move, barrier}` dict, not a flat move dict -- decode `payload["move"]`
    for the move half, and when `payload.get("barrier")` is not None ALSO
    decode `payload["barrier"]` (same `pre` cell -- both sub-payloads
    encode a direction relative to the cop's own pre-turn cell), building
    `CopAction(barrier=...)` instead of `CopAction(move=...)` for that
    turn. `pending_cop.destination(cop_cell)` (not `.move`, which is None
    on a barrier turn) tracks where the cop actually ends up."""
    params = cfg_a.params
    events = [_json_line(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    cop_cell, thief_cell = params.cop_start, params.thief_start
    pending_cop, pending_thief = None, None
    sequence: list[tuple[CopAction, tuple]] = []
    for record in events:
        if record["event"] not in ("message_sent", "message_received"):
            continue
        envelope = record["envelope"]
        if envelope["type"] not in ("move", "reveal"):
            continue
        pre = cop_cell if envelope["sender"] == "police" else thief_cell
        composite = envelope["type"] == "reveal"
        barrier_payload = envelope["payload"].get("barrier") if composite else None
        if barrier_payload is not None:
            resolved = decode_move(barrier_payload, pre, params)
            assert resolved.ok, f"unreplayable barrier: {envelope}"
            pending_cop = CopAction(barrier=resolved.cell)
        else:
            move_dict = envelope["payload"]["move"] if composite else envelope["payload"]
            resolved = decode_move(move_dict, pre, params)
            assert resolved.ok, f"unreplayable move: {envelope}"
            if envelope["sender"] == "police":
                pending_cop = CopAction(move=resolved.cell)
            else:
                pending_thief = resolved.cell
        if pending_cop is not None and pending_thief is not None:
            sequence.append((pending_cop, pending_thief))
            cop_cell = pending_cop.destination(cop_cell)
            thief_cell = pending_thief
            pending_cop, pending_thief = None, None

    state = engine.make_state(params)
    outcome = None
    for cop_action, thief_move in sequence:
        state, outcome = engine.resolve_turn(state, cop_action, thief_move, params, cfg_a.rules)
        if outcome is not None:
            break
    return outcome, state
