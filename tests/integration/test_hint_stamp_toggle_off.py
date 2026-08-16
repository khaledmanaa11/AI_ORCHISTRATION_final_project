"""05-14 G8: both branches stamp the turn ACTUALLY PLAYED -- on the
`commit_reveal=False` path too.

`test_hint_delivery.py` proves this for the shipped configuration
(`commit_reveal: true`) and cannot see the defect this file exists for,
because with the toggle ON the two sides take DIFFERENT branches of
`take_my_turn`: the initiator's own `maybe_resolve` is a no-op there, so
`ctx.state.turn` happened to be right.

With the toggle OFF -- a supported, documented path (`turn_commit.py:63-64`,
`:100-101`, pinned by `test_commit_reveal_protocol.py`'s byte-equivalence
case) -- `pending_action` is NEVER set, so BOTH sides come through the
INITIATOR branch. The second mover then finds the opponent's slot already
filled by its own `await_opponent_turn`, `maybe_resolve` advances
N -> N+1 before the compose stage, and the hint went out stamped one turn
in the FUTURE. That is the original G4 defect, and on this path it
corrupts wire evidence SILENTLY rather than losing it: a receiver's drop
guard never fires for a FUTURE stamp, so nothing anywhere records that the
number is wrong (rule 20). Latent, not active -- but a latent evidence
defect on a supported toggle is still a defect.

THE GROUND TRUTH IS DELIBERATELY NOT THE MOVE ENVELOPE. Measured on this
same harness, the second mover's own MOVE envelopes are stamped 1..16 for
turns 0..15 -- `send_move_only` reads `ctx.state.turn` after the very same
`maybe_resolve` (deferred item #13). Comparing hints against moves would
therefore compare two wrong numbers and pass vacuously. The turns played
are derived instead: a game starts at turn 0 and every joint turn
increments by one, so a side that composed N hints must have stamped
exactly `0..N-1`.
"""

from __future__ import annotations

import dataclasses
import json

from pursuit.network.agent_wiring import load_agent_config
from tests.integration.two_peer_game import play_two_peer_game


def _sent_hint_turns(log_path) -> list[int]:
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    return [
        r["envelope"]["turn"] for r in records
        if r["event"] == "message_sent" and r["envelope"]["type"] == "hint"
    ]


def _toggled_off(cfg):
    return dataclasses.replace(
        cfg, security=dataclasses.replace(cfg.security, commit_reveal=False)
    )


async def test_neither_side_stamps_a_hint_for_a_turn_it_has_not_played(tmp_path, monkeypatch):
    """Both sides, one assertion each, and the SECOND MOVER is the one that
    used to fail: pre-fix its hints ran 1..15 for turns 0..14, opening with
    a claim about turn 1 before turn 1 existed. The first mover is the
    paired fairness control -- it was already correct on this path, and a
    fix that "corrected" it too would be a different bug."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a = _toggled_off(load_agent_config("config/police"))
    cfg_b = _toggled_off(load_agent_config("config/thief"))

    outcome_a, outcome_b, _, _ = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="hint-stamp-off", log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b, "the game did not finish"

    first_mover = _sent_hint_turns(tmp_path / "a.jsonl")
    second_mover = _sent_hint_turns(tmp_path / "b.jsonl")

    assert first_mover and second_mover, "no hint was sent at all -- the probe is vacuous"
    assert second_mover == list(range(len(second_mover))), (
        f"second mover stamped {second_mover}, not the turns it played "
        f"(0..{len(second_mover) - 1})"
    )
    assert first_mover == list(range(len(first_mover))), (
        f"first mover stamped {first_mover} -- the control side regressed"
    )


async def test_the_peer_receives_the_corrected_numbers_on_the_wire(tmp_path, monkeypatch):
    """The stamp is only worth fixing if the number the PEER durably
    records is the corrected one. Read off each side's own inbound
    `message_received`+`hint` envelopes, which is the rule-20 replay
    evidence a grader would reconstruct the game from -- asserted as a
    gap-free PREFIX of what the other side sent, at most one short, since
    the last hint can still be in flight when the receiver's loop exits
    (the hint channel is best-effort by design, 04-04)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a = _toggled_off(load_agent_config("config/police"))
    cfg_b = _toggled_off(load_agent_config("config/thief"))

    await play_two_peer_game(cfg_a, cfg_b, game_uid="hint-stamp-off-wire", log_dir=tmp_path)

    for own, peer in ((tmp_path / "a.jsonl", tmp_path / "b.jsonl"), (tmp_path / "b.jsonl", tmp_path / "a.jsonl")):
        records = [json.loads(line) for line in own.read_text(encoding="utf-8").splitlines()]
        got = [
            r["envelope"]["turn"] for r in records
            if r["event"] == "message_received" and r["envelope"]["type"] == "hint"
        ]
        sent = _sent_hint_turns(peer)
        assert got, "an inbound hint left no durable record"
        assert got == sent[:len(got)], f"received {got}, peer sent {sent}"
        assert len(got) >= len(sent) - 1
        # Without this line the case passes against the very regression it
        # is here for: `got == sent[:len(got)]` holds just as well when
        # BOTH numbers are one turn into the future. Self-audit, 05-14 --
        # measured against revert probe P5, where it failed to fail.
        assert got == list(range(len(got))), f"the wire record carries unplayed turns: {got}"
