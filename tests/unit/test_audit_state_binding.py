"""05-05 Task 3 (05-UAT.md G2, D-60, SEC-05/08): the committed state record
has production readers, and no honest stranger is accused for it.

Mirrors test_audit_turn_binding.py's construction -- hand-built ledger
entries with HONEST `commit_pack` hashes, so the re-hash check passes and
the NEW state check is provably what fires.

The controls are the point of this file, not decoration. `state.role` and
`state.game_id` are the PEER's own record contents; book Sec5.3.1 shares the
canonical-JSON RECIPE, not the contents, and this repo alone carries two
role vocabularies. A control written in our own tokens and our own game-id
convention would be vacuous against the hazard these checks create, which is
a false accusation (rules 16/22).
"""

from __future__ import annotations

from pursuit.security import commit_pack
from pursuit.security.audit import all_matched, audit_peer_records

OUR_ID, PEER_ID, OTHER_GAME = "our-uid", "peer-uid", "some-other-game"
ACTION = {"move": {"kind": "move", "direction": "north"}, "barrier": None}


def _state(*, turn: int, role: str, game_id: str) -> dict:
    return {"game_id": game_id, "turn": turn, "role": role,
            "position": {"row": 2, "col": 3}, "barriers_remaining": 1}


def _entry(*, turn: int, state: dict, action: dict = ACTION) -> tuple[dict, str]:
    """One honest ledger entry: a REAL commit hash over this exact state."""
    h_commit, nonce = commit_pack.commit(state, action, "truth")
    payload = commit_pack.build_commit_payload(
        state=state, move=action, intent="truth", nonce=nonce)
    return {"turn": turn, "h_commit": h_commit, "payload": payload}, h_commit


def _audit(entry, h_commit, *, reveal=ACTION, candidates=None, forbidden=None):
    reveals = {} if reveal is None else {1: reveal}
    return audit_peer_records(
        {1: h_commit}, reveals, [entry],
        candidate_game_ids=candidates, forbidden_role=forbidden,
    )


def test_a_state_record_naming_another_turn_is_a_mismatch():
    entry, h = _entry(turn=1, state=_state(turn=99, role="thief", game_id=OUR_ID))
    records = _audit(entry, h)
    assert not all_matched(records)
    assert "names turn 99" in records[0].detail


def test_our_own_role_replayed_back_at_us_is_a_mismatch():
    """Every FINAL_REVEAL publishes our nonces, so a peer holds our complete
    past payloads and can replay OUR OWN commits at us."""
    entry, h = _entry(turn=1, state=_state(turn=1, role="police", game_id=OUR_ID))
    records = _audit(entry, h, forbidden="police")
    assert not all_matched(records)
    assert "written by 'police'" in records[0].detail


def test_a_state_record_naming_another_game_is_a_mismatch_as_police():
    entry, h = _entry(turn=1, state=_state(turn=1, role="thief", game_id=OTHER_GAME))
    records = _audit(entry, h, candidates={OUR_ID, PEER_ID})
    assert not all_matched(records)
    assert OTHER_GAME in records[0].detail and "on the table at handshake" in records[0].detail


def test_a_state_record_naming_another_game_is_a_mismatch_as_thief():
    """Asserted for BOTH roles, not just the side that adopted: on the thief
    the candidate set is `{our minted uid, the peer's id}` all the same."""
    entry, h = _entry(turn=1, state=_state(turn=1, role="police", game_id=OTHER_GAME))
    records = _audit(entry, h, candidates={PEER_ID, OUR_ID}, forbidden="thief")
    assert not all_matched(records)
    assert OTHER_GAME in records[0].detail


def test_a_trailing_commit_that_fails_a_state_check_is_still_a_mismatch():
    """PLACEMENT proof: an entry committed but never revealed in-game would
    take the trailing-commit exemption (matched=True). Placed after that
    early return, the state checks would never run on a replayed record."""
    entry, h = _entry(turn=1, state=_state(turn=1, role="police", game_id=OTHER_GAME))
    records = _audit(entry, h, reveal=None, candidates={OUR_ID, PEER_ID}, forbidden="police")
    assert not all_matched(records), "a replay must not take the trailing-commit exemption"
    assert "trailing" not in records[0].detail


def test_a_malformed_payload_is_a_named_mismatch_not_a_process_death():
    """`verify_reveal(h, **payload)` raises TypeError on any other shape, and
    `agent_entrypoint`'s guard is `except ToolError` -- so before this
    containment a peer's malformed FINAL_REVEAL killed us before we recorded
    any verdict, making US the side that published no nonces (rule 36)."""
    entry, h = _entry(turn=1, state=_state(turn=1, role="thief", game_id=OUR_ID))
    entry["payload"]["state"] = "not-a-dict"
    records = _audit(entry, h)
    assert not all_matched(records)
    assert "malformed final-reveal payload" in records[0].detail


def test_a_state_record_missing_its_d60_fields_is_a_named_mismatch():
    """The reachable malformed case: `state` IS a dict (so the re-hash runs
    and can even pass), but carries none of D-60's fields."""
    entry, h = _entry(turn=1, state={})
    records = _audit(entry, h, candidates={OUR_ID}, forbidden="police")
    assert not all_matched(records)
    assert "names turn None" in records[0].detail


# --- controls: an honest peer is never accused (rules 16/22) ---------------

def test_control_an_honest_peer_is_still_matched():
    entry, h = _entry(turn=1, state=_state(turn=1, role="thief", game_id=PEER_ID))
    records = _audit(entry, h, candidates={OUR_ID, PEER_ID}, forbidden="police")
    assert all_matched(records), [r.detail for r in records]


def test_control_a_peer_using_a_different_role_vocabulary_is_still_matched():
    """We are the THIEF and say "police"; the honest opponent's own record
    says "cop" (this repo's `engine_agent` vocabulary, and plausibly another
    team's only vocabulary). An equality check against our expected token
    would technically-lose them. The NEGATIVE check imposes nothing."""
    entry, h = _entry(turn=1, state=_state(turn=1, role="cop", game_id=PEER_ID))
    records = _audit(entry, h, candidates={OUR_ID, PEER_ID}, forbidden="thief")
    assert all_matched(records), [r.detail for r in records]


def test_control_a_peer_that_published_no_game_id_is_still_matched():
    """Limitation (a), asserted rather than assumed: candidates=None skips
    the game_id check entirely instead of accusing."""
    entry, h = _entry(turn=1, state=_state(turn=1, role="thief", game_id="whatever-they-use"))
    records = _audit(entry, h, candidates=None, forbidden="police")
    assert all_matched(records), [r.detail for r in records]
