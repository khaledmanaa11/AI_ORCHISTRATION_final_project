"""D-67 join-key shape: whether a peer FINAL_REVEAL record can be audited at all.

Split out of `audit.py` at the 150-code-line gate (Segal Table 5) -- the same
relocate-and-import-back move `audit_state.py` already made out of the same
file, along the same seam: `audit.py` owns the AUDIT (what the peer claimed
versus what we saw), this module owns the ONE question that must be answered
before any audit can run at all, on bytes an OPPONENT wrote -- can this entry
serve as a JOIN KEY against the turns we watched on the wire?

MALFORMED MEANS UNUSABLE AS A JOIN KEY -- never "not a Python int". The
FINAL_REVEAL container shape is shared protocol (06-05 records interoperating
with another team's implementation as an acceptance criterion), so a `records`
that is not a list, an entry that is not an object, and an entry carrying no
`turn` at all are genuinely unparseable, and no honest peer produces them.

An integral FLOAT turn is a completely different case, and it is the reason this
module tests USABILITY rather than type. JSON has no int/float distinction, so a
peer serialising `turn` out of a float-typed field sends a perfectly auditable
record. Measured against the shipped audit BEFORE this module existed: a record
whose turn is `3.0` was audited correctly and came back `matched` -- `0.0 in
{0: h}` is True, `{0} - {0.0}` is empty, and the final sort is numeric. An
`isinstance(turn, int)` rule would have converted that honest peer into a
technical loss (rules 16/22): this phase's own recurring defect, arriving
through the fix instead of through the bug. An integral float therefore
NORMALISES via `int()` and proceeds, and the permissiveness opens no rule-36
hole -- the re-hash, the D-60 state binding and the D-67 move cross-check all
still fire on the normalised entry, exactly as they do on a plain int.

`bool` is REJECTED rather than normalised, agreeing with
`envelope._require_non_bool_int` and `turn_hint_store.usable_stamp`: no
serialiser emits `true` for a turn counter, and a bool silently keying a dict at
0/1 is precisely the surprise those two already refuse.
"""

from __future__ import annotations

from pursuit.security.ledger import LedgerField

NO_USABLE_TURN = -1
"""The `AuditRecord.turn` carried by an entry that has no usable turn of its own.

Turn counting starts at 0, so this can never collide with a real turn and sorts
ahead of every one of them, grouping malformed entries at the head of the
recorded verdict. Several malformed entries sharing one sentinel loses nothing:
each one's own detail names the shape that was wrong with it."""

_MALFORMED_RECORD = "malformed final-reveal record"


def container_detail(peer_records: object) -> str | None:
    """None when the FINAL_REVEAL container is a list we can iterate at all,
    else the named reason it is not.

    Deliberately NOT coerced to an empty list. That would route an unparseable
    container into `audit._missing_turns` as "published nothing" -- the same
    technical loss by accident, but it would make an unreadable peer and the
    `{"records": []}` evasion indistinguishable in our own recorded evidence.
    """
    if isinstance(peer_records, list):
        return None
    return (
        f"malformed final reveal: records is {type(peer_records).__name__}, not a list -- "
        "no nonces could be read from it (rule 36)"
    )


def join_key_turn(entry: object) -> tuple[int | None, str | None]:
    """`(turn, None)` when *entry* can be joined against our observed turns, else
    `(None, detail)` naming what is wrong with its SHAPE.

    One function, one call, two callers (`audit._audit_one` and
    `audit._missing_turns`) -- so the entries the per-entry audit rejects and the
    entries the rule-36 coverage check skips can never drift apart.
    """
    if not isinstance(entry, dict):
        return None, f"{_MALFORMED_RECORD}: expected an object, got {type(entry).__name__}"
    if LedgerField.TURN not in entry:
        return None, f"{_MALFORMED_RECORD}: no {LedgerField.TURN!r} field"
    turn = entry[LedgerField.TURN]
    usable = not isinstance(turn, bool) and (
        isinstance(turn, int) or (isinstance(turn, float) and turn.is_integer())
    )
    if not usable:
        return None, (
            f"{_MALFORMED_RECORD}: turn {turn!r} ({type(turn).__name__}) "
            "cannot serve as a join key"
        )
    return int(turn), None
