"""D-67/rule 36 coverage check -- split from test_audit.py at the
150-code-line gate: a peer cannot evade the audit by simply OMITTING
turns from its own FINAL_REVEAL, up to and including sending none at all
(the cheapest possible rule-36 evasion). A genuinely turn-less game stays
vacuously matched -- there is nothing to audit."""

from __future__ import annotations

from pursuit.security import commit_pack
from pursuit.security.audit import all_matched, audit_peer_records

_STATE = {
    "game_id": "g1", "turn": 1, "role": "police",
    "position": {"row": 0, "col": 0}, "barriers_remaining": 3,
}
_MOVE = {"move": {"kind": "move", "direction": "north"}, "barrier": None}


def _genuine_records(turns: list[int]) -> tuple[dict, dict, list[dict]]:
    """Same fixture shape as test_audit.py's own (not imported, to keep
    each split file self-contained -- both build via a REAL commit_pack.commit()
    call, never a hand-rolled hash)."""
    observed_commits: dict[int, str] = {}
    observed_reveals: dict[int, dict] = {}
    peer_records: list[dict] = []
    for turn in turns:
        h_commit, nonce = commit_pack.commit(_STATE, _MOVE, "truth")
        payload = commit_pack.build_commit_payload(
            state=_STATE, move=_MOVE, intent="truth", nonce=nonce,
        )
        observed_commits[turn] = h_commit
        observed_reveals[turn] = _MOVE
        peer_records.append({"turn": turn, "h_commit": h_commit, "payload": payload})
    return observed_commits, observed_reveals, peer_records


def test_peer_omits_one_fully_exchanged_turn_that_turn_mismatches():
    observed_commits, observed_reveals, peer_records = _genuine_records([1, 2, 3])
    del peer_records[1]  # turn 2's entry never shipped

    records = audit_peer_records(observed_commits, observed_reveals, peer_records)
    by_turn = {r.turn: r for r in records}
    assert by_turn[1].matched is True and by_turn[3].matched is True
    assert by_turn[2].matched is False
    assert "absent from final reveal" in by_turn[2].detail


def test_peer_sends_empty_records_while_turns_were_observed_all_mismatch():
    """THE evasion this fix closes: an opponent publishing NO nonces at
    all (`{"records": []}`) must not pass the mutual audit vacuously."""
    observed_commits, observed_reveals, _peer_records = _genuine_records([1, 2, 3])

    records = audit_peer_records(observed_commits, observed_reveals, [])

    assert all_matched(records) is False
    assert [r.turn for r in records] == [1, 2, 3]
    assert all(r.matched is False for r in records)
    assert all("absent from final reveal" in r.detail for r in records)


def test_a_genuinely_turnless_game_is_vacuously_matched():
    """A game that died at handshake (nothing committed, nothing
    revealed, nothing claimed) has nothing to audit -- correctly."""
    records = audit_peer_records({}, {}, [])
    assert records == []
    assert all_matched(records) is True
