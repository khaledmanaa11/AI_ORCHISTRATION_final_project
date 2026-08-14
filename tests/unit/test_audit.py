"""D-67: the Final-Reveal mutual audit -- both tamper classes proven
distinctly: (a) the payload/hash itself disagrees, (b) the hash verifies
perfectly but the revealed action differs from what was actually played
(the hash-only bypass D-67 exists to close). The rule-36 COVERAGE check
(a peer omitting turns entirely, up to and including an empty
FINAL_REVEAL) and the trailing-commit fairness fix live in the sibling
test_audit_coverage.py, split at the 150-line gate."""

from __future__ import annotations

from pursuit.security import commit_pack
from pursuit.security.audit import all_matched, audit_peer_records

_STATE = {
    "game_id": "g1", "turn": 1, "role": "police",
    "position": {"row": 0, "col": 0}, "barriers_remaining": 3,
}
_MOVE = {"move": {"kind": "move", "direction": "north"}, "barrier": None}
_OTHER_MOVE = {"move": {"kind": "move", "direction": "south"}, "barrier": None}


def _genuine_records(turns: list[int]) -> tuple[dict, dict, list[dict]]:
    """Build (observed_commits, observed_reveals, peer_records) via a REAL
    `commit_pack.commit()` call per turn -- never a hand-rolled hash.

    05-05: the state record is now built PER TURN (`dict(_STATE, turn=turn)`,
    the shape `test_audit_turn_binding._honest_turn` already used). It
    previously reused one turn-1 record for every turn, which no honest
    ledger can produce -- `turn_commit_ledger.commit_own_action` passes ONE
    `turn` to both `build_state_record` and `CommitLedger.append`. The
    fixture was made faithful to production, not the check relaxed."""
    observed_commits: dict[int, str] = {}
    observed_reveals: dict[int, dict] = {}
    peer_records: list[dict] = []
    for turn in turns:
        state = dict(_STATE, turn=turn)
        h_commit, nonce = commit_pack.commit(state, _MOVE, "truth")
        payload = commit_pack.build_commit_payload(
            state=state, move=_MOVE, intent="truth", nonce=nonce,
        )
        observed_commits[turn] = h_commit
        observed_reveals[turn] = _MOVE
        peer_records.append({"turn": turn, "h_commit": h_commit, "payload": payload})
    return observed_commits, observed_reveals, peer_records


def test_an_untampered_triple_audits_clean():
    observed_commits, observed_reveals, peer_records = _genuine_records([1, 2, 3])
    records = audit_peer_records(observed_commits, observed_reveals, peer_records)
    assert all_matched(records) is True
    assert [r.turn for r in records] == [1, 2, 3]


def test_tamper_a_a_flipped_payload_field_fails_the_hash_check():
    observed_commits, observed_reveals, peer_records = _genuine_records([1, 2, 3])
    peer_records[1]["payload"]["intent"] = "lie"  # turn 2's payload, after hashing

    records = audit_peer_records(observed_commits, observed_reveals, peer_records)
    by_turn = {r.turn: r for r in records}
    assert by_turn[1].matched is True and by_turn[3].matched is True
    assert by_turn[2].matched is False
    assert "H_commit" in by_turn[2].detail


def test_tamper_b_the_d67_case_hash_verifies_but_revealed_action_differs():
    """Payload/hash left UNTOUCHED (still verifies) -- only what we saw
    actually played in-game differs from the claimed final action."""
    observed_commits, observed_reveals, peer_records = _genuine_records([1, 2, 3])
    observed_reveals[2] = _OTHER_MOVE

    records = audit_peer_records(observed_commits, observed_reveals, peer_records)
    by_turn = {r.turn: r for r in records}
    assert by_turn[1].matched is True and by_turn[3].matched is True
    assert by_turn[2].matched is False
    assert "D-67" in by_turn[2].detail
    # The hash itself DID verify -- proving this is genuinely the bypass
    # case, not case (a) in disguise.
    assert commit_pack.verify_reveal(observed_commits[2], **peer_records[1]["payload"]) is True


def test_tamper_c_a_missing_observed_commit_is_named_not_skipped():
    observed_commits, observed_reveals, peer_records = _genuine_records([1, 2, 3])
    del observed_commits[2]
    records = audit_peer_records(observed_commits, observed_reveals, peer_records)
    by_turn = {r.turn: r for r in records}
    assert by_turn[1].matched is True and by_turn[3].matched is True
    assert by_turn[2].matched is False
    assert "no observed commit" in by_turn[2].detail


def test_a_trailing_commit_without_an_observed_reveal_is_matched_not_a_false_accusation():
    """The fairness fix: CommitLedger.append runs BEFORE the REVEAL send,
    so an abnormal ending can leave an HONEST peer with a
    committed-never-revealed entry in its own final reveal -- that must
    never be misbranded as a forgery (rules 16/22/38, the other direction)."""
    observed_commits, observed_reveals, peer_records = _genuine_records([1, 2, 3])
    del observed_reveals[3]

    records = audit_peer_records(observed_commits, observed_reveals, peer_records)
    by_turn = {r.turn: r for r in records}
    assert by_turn[1].matched is True and by_turn[2].matched is True
    assert by_turn[3].matched is True
    assert "trailing" in by_turn[3].detail and "hash verified" in by_turn[3].detail
