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
    """06-02 (D-58): under commit_reveal (default true), the action rides a
    `reveal`-typed envelope carrying the composite `{move, barrier}` dict,
    not a flat `move`-typed one -- widen the type filter to both, shape-
    aware callers inspect `payload["move"]`/`payload["barrier"]`."""
    return [
        r for r in records
        if r["event"] == "message_sent" and r["envelope"]["type"] in ("move", "reveal")
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
    """LANG-01/LANG-02, frozen: over a full game, both sides send one
    hint per turn they play INTO, every hint is within the legal length,
    both `intent` values are representable, and no outgoing payload (hint
    OR move) ever carries a numeric coordinate (rule 27).

    RE-SPECIFIED 05-06, not loosened: the count is now the DERIVED
    per-role expectation, and the measurement confirms it rather than
    defining it. Asserting whatever a run happens to produce is exactly
    how the old `len(turns) == ctx.state.turn` came to certify the
    responder's mis-stamped, post-resolve hint as correct.

    The derivation. A hint rides every turn the agent plays INTO, and the
    terminal turn resolves BEFORE the responder's compose stage -- a hint
    for a finished game is evidence of nothing, and composing one costs a
    real LLM round trip after the game is already over (17.4 s of the 18 s
    inter-side divergence in the 2026-08-13 round). So:
      * INITIATOR (police, design note 7): its `maybe_resolve` is a no-op
        on every turn including the last, because the responder's action
        slot is still empty when it fires -- the initiator resolves in
        `await_opponent_turn` instead. It therefore composes on every turn
        -> `len(turns) == ctx.state.turn`.
      * RESPONDER (thief): its `maybe_resolve` completes the pair and
        fires on the terminal turn, inside `take_my_turn`, before the
        compose stage -> `len(turns) == ctx.state.turn - 1`.
    The word-limit, both-intents and zero-coordinate assertions below are
    untouched."""
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
        # Derived in the docstring above; measured here. `police` is the
        # initiator (run_turn_loop's own design-note-7 ordering).
        expected = ctx.state.turn if ctx.role == "police" else ctx.state.turn - 1
        assert len(turns) == expected, (
            f"{ctx.role}: composed {len(turns)} hints over {ctx.state.turn} turns, "
            f"derived expectation {expected}"
        )
        for record in turns:
            outgoing = record["outgoing_hint"]
            assert outgoing["text"], "a turn shipped with no hint text"
            assert len(outgoing["text"].split()) <= limit
            assert outgoing["intent"] in (Intent.TRUTH.value, Intent.LIE.value)
            assert_no_coordinates(outgoing["text"])  # raises ValueError on a leak
        for move in _moves(records):
            envelope = move["envelope"]
            payload = envelope["payload"]
            if envelope["type"] == "reveal":
                # The composite dict's TOP level never has "x"/"y" either,
                # but that would be checking the wrong nesting level (rule
                # 27's real guarantee is about the coordinate never
                # existing anywhere) -- inspect both sub-payloads.
                assert "x" not in payload["move"]
                assert "y" not in payload["move"]
                if payload.get("barrier") is not None:
                    assert "x" not in payload["barrier"]
                    assert "y" not in payload["barrier"]
            else:
                assert "x" not in payload
                assert "y" not in payload


async def test_intent_is_always_committed_before_the_hint_text_exists(tmp_path, monkeypatch):
    """LANG-03/rule 25, frozen structurally under D-58's real cross-side
    concurrency (06-02): `plan_turn_deception()` (which fixes `plan.intent`)
    always produces a plan strictly before any `compose_outgoing(plan, ...)`
    call that uses that SAME plan object -- proven identity-based (`id()`),
    not by the old per-side back-to-back atomicity assumption, which D-58
    no longer guarantees: the responder's plan and compose calls are now
    separated by a real network round trip (multiple await points), not
    two adjacent sync statements. This proves the SAME real invariant
    (intent fixed before text exists) under legitimate concurrent
    interleaving."""
    order: list[tuple[str, object]] = []
    real_plan = turn_language_io.build_deception_plan
    real_compose = turn_language_io.compose_outgoing

    def spy_plan(*args, **kwargs):
        result = real_plan(*args, **kwargs)
        order.append(("plan", result))
        return result

    async def spy_compose(*args, **kwargs):
        order.append(("compose", args[0]))
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
    seen_plan_ids: set[int] = set()
    saw_a_pair = False
    for kind, obj in order:
        if kind == "plan":
            seen_plan_ids.add(id(obj))
        else:
            assert id(obj) in seen_plan_ids, "intent was not committed before text"
            saw_a_pair = True
    assert saw_a_pair, "no turn ever planned/composed a hint"
