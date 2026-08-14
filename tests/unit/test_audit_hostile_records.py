"""05-10: every shape a PEER can put in a FINAL_REVEAL reaches a verdict.

`audit_peer_records` used to RAISE on peer-controlled input -- measured by probe
against the shipped function (05-VERIFICATION anti-patterns): a `records` that
is a string, an entry that is a string, an entry with no `turn`, and a `turn`
that is a str/None/list all escaped as TypeError/KeyError. `agent_entrypoint`
guards only `ToolError`, so each of them killed the process before any verdict
was written -- rule 36 against US, the artifact 05-04 and 05-09 exist to
prevent, arriving through the last uncontained door in the same corridor.

Every case here must LOSE (a peer whose records we cannot parse published no
usable nonces), and every case must lose by RECORDING a named mismatch. The
three controls carry the discrimination: an honest peer is untouched, an honest
peer whose `turn` arrives as the float `3.0` is STILL MATCHED (this test FAILS
against an `isinstance(turn, int)` rule -- the fairness trap the fix could
easily have introduced, rules 16/22), and `{"records": []}` still produces the
rule-36 coverage mismatches `test_audit_coverage.py` pins.
"""

from __future__ import annotations

import pytest

from pursuit.security import commit_pack
from pursuit.security.audit import all_matched, audit_peer_records
from pursuit.security.audit_shape import NO_USABLE_TURN

_STATE = {
    "game_id": "g1", "turn": 1, "role": "police",
    "position": {"row": 0, "col": 0}, "barriers_remaining": 3,
}
_MOVE = {"move": {"kind": "move", "direction": "north"}, "barrier": None}


def _genuine(turns: list[int]) -> tuple[dict, dict, list[dict]]:
    """The same fixture shape `test_audit_coverage.py` builds, via a REAL
    `commit_pack.commit()` -- never a hand-rolled hash."""
    observed_commits: dict[int, str] = {}
    observed_reveals: dict[int, dict] = {}
    records: list[dict] = []
    for turn in turns:
        state = dict(_STATE, turn=turn)
        h_commit, nonce = commit_pack.commit(state, _MOVE, "truth")
        payload = commit_pack.build_commit_payload(
            state=state, move=_MOVE, intent="truth", nonce=nonce,
        )
        observed_commits[turn] = h_commit
        observed_reveals[turn] = _MOVE
        records.append({"turn": turn, "h_commit": h_commit, "payload": payload})
    return observed_commits, observed_reveals, records


_COMMITS, _REVEALS, _RECORDS = _genuine([1])
_RECORD = _RECORDS[0]


def _repayload(**overrides: object) -> dict:
    return dict(_RECORD, payload=dict(_RECORD["payload"], **overrides))


# Shapes that cannot yield a join key at all -- rejected before the re-hash.
_UNUSABLE_SHAPES = {
    "entry is not an object": "garbage",
    "entry has no turn": {"h_commit": "x", "payload": {}},
    "turn is a str": dict(_RECORD, turn="1"),
    "turn is None": dict(_RECORD, turn=None),
    "turn is a list": dict(_RECORD, turn=[1]),
    "turn is a bool": dict(_RECORD, turn=True),
    "turn is a non-integral float": dict(_RECORD, turn=1.5),
}

# Shapes that DO join, then blow up inside `build_commit_payload`. `intent` and
# the empty `nonce` are INSTANCE 5 of audit.py's boundary rule: both raise
# ValueError, which 05-05's `(TypeError, KeyError)` containment did not catch.
_UNUSABLE_PAYLOADS = {
    "intent is maybe": _repayload(intent="maybe"),
    "intent is None": _repayload(intent=None),
    "nonce is empty": _repayload(nonce=""),
    "payload is not a mapping": dict(_RECORD, payload="garbage"),
    "payload has an extra key": _repayload(extra="surprise"),
}


@pytest.mark.parametrize("entry", _UNUSABLE_SHAPES.values(), ids=list(_UNUSABLE_SHAPES))
def test_an_unusable_join_key_is_a_named_mismatch_not_a_crash(entry):
    records = audit_peer_records(_COMMITS, _REVEALS, [entry])

    mismatch = records[0]
    assert mismatch.turn == NO_USABLE_TURN
    assert mismatch.matched is False
    assert "malformed" in mismatch.detail
    assert all_matched(records) is False, "an unparseable peer must still lose (rule 36)"


@pytest.mark.parametrize("entry", _UNUSABLE_PAYLOADS.values(), ids=list(_UNUSABLE_PAYLOADS))
def test_an_unusable_payload_is_a_named_mismatch_not_a_crash(entry):
    records = audit_peer_records(_COMMITS, _REVEALS, [entry])

    assert [(r.turn, r.matched) for r in records] == [(1, False)]
    assert "malformed final-reveal payload" in records[0].detail


def test_a_records_container_that_is_not_a_list_is_one_named_mismatch():
    """Distinguishable from `{"records": []}` on purpose: coercing an
    unreadable container to an empty list would reach the same verdict by
    accident and make the two cases indistinguishable in our own evidence."""
    records = audit_peer_records(_COMMITS, _REVEALS, "not-a-list")

    assert len(records) == 1
    assert records[0].matched is False
    assert "records is str, not a list" in records[0].detail
    assert "absent from final reveal" not in records[0].detail


def test_one_garbage_entry_does_not_disable_the_coverage_check_for_the_valid_turns():
    """THE side door: if the coverage check bailed on any malformed entry, a
    peer would append ONE garbage record and rule-36 coverage would silently
    vanish for every valid turn -- the `{"records": []}` evasion re-opened."""
    commits, reveals, records = _genuine([1, 2, 3])
    hostile = [records[0], {"payload": {}}, "garbage"]

    audited = audit_peer_records(commits, reveals, hostile)

    by_turn = {r.turn: r for r in audited}
    assert by_turn[1].matched is True, "the valid entry was collateral damage"
    for withheld in (2, 3):
        assert by_turn[withheld].matched is False
        assert "absent from final reveal" in by_turn[withheld].detail
    assert sum(1 for r in audited if r.turn == NO_USABLE_TURN) == 2


def test_control_an_honest_peer_is_entirely_unaffected():
    commits, reveals, records = _genuine([1, 2, 3])

    audited = audit_peer_records(commits, reveals, records)

    assert all_matched(audited) is True
    assert [r.turn for r in audited] == [1, 2, 3]


def test_control_an_honest_peer_whose_turn_arrives_as_a_float_is_still_matched():
    """JSON has no int/float distinction, and the shipped audit handled `3.0`
    correctly BEFORE this fix (measured: `0.0 in {0: h}` is True, `{0} - {0.0}`
    is empty, the sort is numeric). Written against an `isinstance(turn, int)`
    rule this test FAILS -- which is exactly the discrimination it owes: such a
    peer is honest and auditable, and a type check would technically-lose it
    (rules 16/22)."""
    commits, reveals, records = _genuine([3])
    floated = [dict(records[0], turn=3.0)]

    audited = audit_peer_records(commits, reveals, floated)

    assert [(r.turn, r.matched) for r in audited] == [(3, True)]
    assert "matched" in audited[0].detail


def test_control_a_peer_publishing_no_records_still_loses_under_rule_36():
    commits, reveals, _records = _genuine([1, 2, 3])

    audited = audit_peer_records(commits, reveals, [])

    assert all_matched(audited) is False
    assert [r.turn for r in audited] == [1, 2, 3]
    assert all("absent from final reveal" in r.detail for r in audited)
