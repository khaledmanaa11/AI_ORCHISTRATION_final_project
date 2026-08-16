"""GATE-6 core: the D-58 both-locked Commit-Ack-Reveal exchange, proven end
to end on a real two-peer game (real shipped configs, `security.json`'s
`commit_reveal=true` default, D-65). Split across three sibling modules at
the 150-code-line gate: this file (the full-game shape proof + the
toggle-off byte-equivalence proof), `test_commit_reveal_protocol_barrier.py`
(a forced cop barrier round-trip, D-66), and
`test_commit_reveal_protocol_jitter.py` (a duplicate ACK tolerated, never a
technical loss).
"""

from __future__ import annotations

import dataclasses
import json

from pursuit.constants import Outcome
from pursuit.network.agent_wiring import load_agent_config
from tests.integration.two_peer_game import play_two_peer_game

# 05-15 (G10): `game_over` is ADMITTED here, and this is a correction of the
# constant to match the test's own stated contract rather than a relaxation
# of it -- `test_toggle_off_is_byte_equivalent_to_pre_phase_6`'s docstring
# has always read "only handshake/move/hint/game_over types". The tool and
# the MessageType have existed since Phase 2; what changed in 05-15 is that
# something finally SENDS one (rule 21's Capture Claim,
# network/capture_declaration.py). The claim this test actually makes --
# that commit_reveal=False puts no D-58 traffic on the wire -- is the NEXT
# assertion, `not ({"commit", "ack", "reveal"} & types)`, and it is
# byte-unchanged. The admission is paired with a positive pin below, so the
# set is strictly stronger than before, never looser.
_ALLOWED_TYPES_OFF = {"handshake", "move", "hint", "game_over"}


def _events(log_path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _envelope_types(events: list[dict]) -> set[str]:
    return {e["envelope"]["type"] for e in events if "envelope" in e}


async def test_full_game_commits_acks_reveals_with_the_both_locked_gate(tmp_path, monkeypatch):
    """§10.4 criterion 1: the four phases run, commit then reveal with a
    valid nonce -- proven on the wire, not just unit-level (06-01 already
    proves the hash math). Zero `move`-typed envelopes; zero `"nonce"` text
    anywhere in the wire-mirroring log (rule 18); a matching nonce-bearing
    ledger record per turn each side actually committed. The both-locked
    gate (D-58's own core claim, §5.3.2): for every turn, THIS side's own
    REVEAL sent appears strictly after the OPPONENT's COMMIT received, by
    JSONL line order."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    assert cfg_a.security.commit_reveal is True and cfg_b.security.commit_reveal is True

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="commit-reveal-full", log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b

    for role, log_path, ledger_path in (
        ("police", tmp_path / "a.jsonl", tmp_path / "a.ledger.jsonl"),
        ("thief", tmp_path / "b.jsonl", tmp_path / "b.ledger.jsonl"),
    ):
        raw_text = log_path.read_text(encoding="utf-8")
        assert '"nonce"' not in raw_text, f"{role}: nonce leaked into the wire-mirroring log"
        events = [json.loads(line) for line in raw_text.splitlines()]
        types = _envelope_types(events)
        assert {"commit", "ack", "reveal"} <= types, f"{role}: missing a commit-reveal phase"
        assert "move" not in types, f"{role}: a flat MOVE envelope leaked under commit_reveal=true"

        ledger_lines = ledger_path.read_text(encoding="utf-8").splitlines()
        assert ledger_lines, f"{role}: empty ledger"
        assert all('"nonce"' in line for line in ledger_lines)

        commit_received_turn = {}
        reveal_sent_turn = {}
        for i, record in enumerate(events):
            envelope = record.get("envelope")
            if envelope is None:
                continue
            if record["event"] == "message_received" and envelope["type"] == "commit":
                commit_received_turn[envelope["turn"]] = i
            if record["event"] == "message_sent" and envelope["type"] == "reveal":
                reveal_sent_turn[envelope["turn"]] = i
        assert reveal_sent_turn, f"{role}: no REVEAL was ever sent"
        for turn, reveal_line in reveal_sent_turn.items():
            assert turn in commit_received_turn, f"{role} turn {turn}: no opponent COMMIT recorded"
            assert commit_received_turn[turn] < reveal_line, (
                f"{role} turn {turn}: REVEAL sent before the opponent's COMMIT was ever received"
            )


async def test_toggle_off_is_byte_equivalent_to_pre_phase_6(tmp_path, monkeypatch):
    """D-65/D-66: `security.commit_reveal=False` is the exact pre-Phase-6
    wire -- only handshake/move/hint/game_over types, zero barriers ever
    placed (the override seam never produces one)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    cfg_a = dataclasses.replace(cfg_a, security=dataclasses.replace(cfg_a.security, commit_reveal=False))
    cfg_b = dataclasses.replace(cfg_b, security=dataclasses.replace(cfg_b.security, commit_reveal=False))

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="commit-reveal-off", log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b

    for log_path in (tmp_path / "a.jsonl", tmp_path / "b.jsonl"):
        types = _envelope_types(_events(log_path))
        assert types <= _ALLOWED_TYPES_OFF, f"unexpected envelope type(s): {types - _ALLOWED_TYPES_OFF}"
        assert not ({"commit", "ack", "reveal"} & types)

    assert ctx_a.state.barriers_placed == 0
    assert ctx_b.state.barriers_placed == 0

    # The positive pin that pays for admitting "game_over" above (05-15).
    # Rule 21 does not depend on the commit-reveal toggle, so the Capture
    # Claim must go out on THIS path too -- from the cop only (book Sec3.5
    # p.22 Table 2), exactly once, carrying the outcome both sides resolved.
    declared = {
        role: [
            e for e in _events(path)
            if e["event"] == "message_sent" and e.get("envelope", {}).get("type") == "game_over"
        ]
        for role, path in (("police", tmp_path / "a.jsonl"), ("thief", tmp_path / "b.jsonl"))
    }
    assert declared["thief"] == [], "only the capturing side declares (rules 21/22)"
    assert len(declared["police"]) == (1 if outcome_a is Outcome.CAPTURE else 0)
    for record in declared["police"]:
        assert record["envelope"]["payload"]["outcome"] == outcome_a.value
