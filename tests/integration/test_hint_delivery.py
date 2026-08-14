"""05-06 G4: the language channel actually DELIVERS, in both directions.

The 2026-08-13 remote round produced five `incoming_hint.outcome =
"no_hint"` in a row on machine B -- the thief decoded nothing, in every
game, loopback included -- and not one of the 1262 tests then in the suite
caught it. Two bugs made that shape:

  * the receive-side drop guard `turn < ctx.state.turn` was structurally
    unsatisfiable for a responder (a hint for turn N is pulled off the
    queue once the receiver has already resolved to N + 1);
  * the responder stamped its OWN outgoing hint with the post-resolve
    `ctx.state.turn`, one turn into the future -- which is the ONLY
    reason the police decoded anything at all.

Because of the second bug, fixing the stamp alone takes the round from
3-of-10 decodes to 0-of-10. This file therefore asserts BOTH halves at
once, and both assertions are proven non-vacuous by reverting each half
in turn (recorded in 05-06-SUMMARY.md).

Imports `_play_to_turn_loop_end` from `test_step0_and_audit.py` -- the
established sibling-import precedent that `test_step0_and_audit_tamper.py`
and the four `scripts/gate6_*.py` call sites already use. That file is
NOT modified here.
"""

from __future__ import annotations

import json

from pursuit.network.agent_wiring import load_agent_config
from tests.integration.test_step0_and_audit import _play_to_turn_loop_end

_CFG_A = "config/police"
_CFG_B = "config/thief"


def _events(log_path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _sent_turns(records: list[dict], envelope_type: str) -> list[int]:
    """The turns this side stamped on its OWN outbound envelopes of one
    type, in order. Read off the nested envelope, which is what the peer
    actually receives and buffers against."""
    return [
        r["envelope"]["turn"] for r in records
        if r["event"] == "message_sent" and r["envelope"]["type"] == envelope_type
    ]


def _incoming_outcomes(records: list[dict]) -> list[str]:
    return [r["incoming_hint"]["outcome"] for r in records if r["event"] == "language_turn"]


async def _play(tmp_path, monkeypatch, uid: str):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config(_CFG_A), load_agent_config(_CFG_B)
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_to_turn_loop_end(
        cfg_a, cfg_b, game_uid=uid, log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b
    return ctx_a, ctx_b


async def test_both_sides_stamp_the_turn_they_actually_played(tmp_path, monkeypatch):
    """Assertion 1. A side's REVEAL for turn T is by definition the turn
    it played, so the hint that rides that turn must carry the SAME
    number. The measured round had police hints 0,1,2,3,4 (correct)
    against thief hints 1,2,3,4,5 -- one turn into the future, and turn 5
    was never played by anybody.

    The per-role expectation is DERIVED, not read off a run: the
    initiator's `maybe_resolve` is a no-op on every turn including the
    last (the responder's slot is still empty when it fires), so the
    initiator composes on every turn it reveals; the responder's
    `maybe_resolve` fires on the terminal turn BEFORE its compose stage,
    and a hint for a finished game is not evidence of anything, so it
    composes on every turn but that one."""
    ctx_a, ctx_b = await _play(tmp_path, monkeypatch, "hint-delivery-stamp")

    police = _events(ctx_a.log_path)
    thief = _events(ctx_b.log_path)
    police_hints, police_reveals = _sent_turns(police, "hint"), _sent_turns(police, "reveal")
    thief_hints, thief_reveals = _sent_turns(thief, "hint"), _sent_turns(thief, "reveal")

    assert police_reveals and thief_reveals, "no turn was played at all"
    assert police_hints == police_reveals, (
        f"initiator hint turns {police_hints} must equal its reveal turns {police_reveals}"
    )
    assert thief_hints == thief_reveals[:-1], (
        f"responder hint turns {thief_hints} must equal its reveal turns "
        f"{thief_reveals} minus the resolved terminal turn"
    )
    # The specific 0..4 / 1..5 asymmetry, named directly so a future
    # regression reads as itself rather than as a list mismatch.
    assert max(thief_hints) <= max(thief_reveals), "a hint was stamped for a turn never played"
    assert police_hints[0] == thief_hints[0] == police_reveals[0]


async def test_both_sides_actually_receive_a_decodable_hint(tmp_path, monkeypatch):
    """Assertion 2, and the one that would have caught the round: the
    responder must end the game having seen at least one hint. `no_hint`
    means nothing was in `ctx.incoming_hints` when `decode_turn_hint`
    popped it -- i.e. the hint was dropped before it ever reached the
    decoder, which is precisely G4. Any other outcome (`evidence`,
    `no_evidence`, `skipped`) means the text ARRIVED; this test is about
    delivery, not about what a keyless decode concludes."""
    ctx_a, ctx_b = await _play(tmp_path, monkeypatch, "hint-delivery-decode")

    for ctx, label in ((ctx_a, "police/initiator"), (ctx_b, "thief/responder")):
        outcomes = _incoming_outcomes(_events(ctx.log_path))
        assert outcomes, f"{label}: no language_turn records at all"
        assert any(o != "no_hint" for o in outcomes), (
            f"{label}: every turn read no_hint {outcomes} -- the channel delivered nothing"
        )


def _received_hint_turns(records: list[dict]) -> list[int]:
    return [
        r["envelope"]["turn"] for r in records
        if r["event"] == "message_received" and r["envelope"]["type"] == "hint"
    ]


async def test_every_inbound_hint_is_on_the_wire_record(tmp_path, monkeypatch):
    """G3 at the integration level: both sides' logs carry
    `message_received` + `hint` records. Pre-fix this count was ZERO on
    every machine of every game -- machine A's remote-round log has 5
    `message_sent`+`hint` and 0 `message_received`+`hint`, while its own
    `language_turn` records quote the thief's hint texts verbatim.

    Asserted as a gap-free PREFIX of what the peer sent, at most one
    short, rather than as an exact count: the last hint a side pushes can
    still be in flight when the RECEIVER's own turn loop resolves and
    exits, and it is then never drained. That is the hint channel being
    best-effort by design (04-04) -- a hint must never block or extend a
    game -- not a lost record."""
    ctx_a, ctx_b = await _play(tmp_path, monkeypatch, "hint-delivery-log")

    police, thief = _events(ctx_a.log_path), _events(ctx_b.log_path)
    got_a, got_b = _received_hint_turns(police), _received_hint_turns(thief)
    sent_a, sent_b = _sent_turns(police, "hint"), _sent_turns(thief, "hint")

    assert got_a and got_b, "an inbound hint left no durable record"
    assert got_a == sent_b[:len(got_a)], f"police received {got_a}, thief sent {sent_b}"
    assert got_b == sent_a[:len(got_b)], f"thief received {got_b}, police sent {sent_a}"
    assert len(got_a) >= len(sent_b) - 1 and len(got_b) >= len(sent_a) - 1

    for record in police + thief:
        if record["event"] == "message_received" and record["envelope"]["type"] == "hint":
            assert record["envelope"]["payload"]["text"], "a hint record lost its text"
