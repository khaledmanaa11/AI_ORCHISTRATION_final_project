"""05-12 / G7: `adopt_negotiated_game_id` against a hostile peer id, and the
honest peer it must not mistake for one.

Every hostile case here was reproduced against live source at `0437559`
before the fix, and each ended in one of three ways -- a `TypeError` out of
the set constructor, our wire log (and, via `ledger_path`'s stem derivation,
our D-64 nonce ledger) relocated outside its own directory, or a candidate
set that excluded the peer's real id and so false-accused an honest
opponent. `run_agent`'s only guard is `except ToolError`, so the first of
those killed the process AT THE HANDSHAKE: no verdict, no FINAL_REVEAL, no
nonces published -- rule 36 against US, before move 1.

So every assertion below is on a NAMED OUTCOME, never on an exception type.
`pytest.raises` appears nowhere in this file on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from pursuit.network.game_identity import GameIdentity, adopt_negotiated_game_id
from pursuit.security.audit_state import state_binding_detail
from pursuit.security.state_record import build_state_record
from tests.unit.test_game_identity_validate import HONEST_FOREIGN, UNSAFE

OWN_UID = "own1111own1111aa"


@dataclass
class FakeCtx:
    """The four `AgentContext` fields `adopt_negotiated_game_id` touches --
    a fake, so this file needs no live runtime, engine or socket."""

    role: str
    game_uid: str
    log_path: Path
    identity: GameIdentity | None = None
    negotiated_game_id: str | None = None
    candidate_game_ids: set[str] | None = None


@dataclass
class FakeResult:
    """`HandshakeResult.peer_game_id` is annotated `str | None` but is read
    verbatim off the wire, so the annotation is a hope, not a guarantee."""

    peer_game_id: object = None
    extra: dict = field(default_factory=dict)


def _ctx(tmp_path, role="thief"):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log = log_dir / f"{OWN_UID}.jsonl"
    log.write_text('{"event": "illegal_transition"}\n', encoding="utf-8")
    return FakeCtx(role=role, game_uid=OWN_UID, log_path=log,
                   identity=GameIdentity(game_uid=OWN_UID, log_path=log))


@pytest.mark.parametrize(("label", "hostile"), UNSAFE, ids=[label for label, _ in UNSAFE])
def test_a_hostile_peer_game_id_is_a_named_outcome_never_a_traceback(label, hostile, tmp_path):
    """The whole adversarial set in one place: unhashable, traversal, empty,
    over-long, non-str, NUL, reserved. Each resolves to the ONE outcome the
    module has always had for a peer that published no id."""
    ctx = _ctx(tmp_path)
    adopt_negotiated_game_id(ctx, FakeResult(hostile))

    assert ctx.game_uid == OWN_UID, label
    assert ctx.negotiated_game_id is None, label
    assert ctx.candidate_game_ids is None, label
    assert ctx.log_path == tmp_path / "logs" / f"{OWN_UID}.jsonl", label
    assert ctx.log_path.read_text(encoding="utf-8").startswith('{"event"')


def test_a_traversal_id_leaves_the_log_and_its_nonce_ledger_where_they_were(tmp_path):
    """The sharpest of the hostile cases, asserted on the FILESYSTEM rather
    than on a field. Measured before: `game_id: '../../evil'` moved
    `logs/<uid>.jsonl` two directories up as `evil.jsonl`, and because
    `turn_commit_ledger.ledger_path` derives from `log_path.stem`, every
    nonce this side later wrote followed it -- overwriting whatever stood at
    the destination, unchecked."""
    ctx = _ctx(tmp_path)
    outside = tmp_path.parent / "evil.jsonl"
    existed_before = outside.exists()

    adopt_negotiated_game_id(ctx, FakeResult("../../evil"))

    assert ctx.log_path.parent == tmp_path / "logs"
    assert (tmp_path / "logs" / f"{OWN_UID}.jsonl").exists()
    assert outside.exists() is existed_before


def test_absent_means_one_thing_on_both_lines(tmp_path):
    """THE `''` SPLIT, closed. Before: `peer_game_id or own_uid` read `''` as
    ABSENT (keep our uid) while `result.peer_game_id is not None` read it as
    PRESENT and built `{own_uid, ''}` -- a set holding neither of the peer's
    real ids, so every honest record failed membership at
    `audit_state.py:113-118` and we declared a technical loss against an
    honest opponent. The two lines now consume ONE answer, and a None
    candidate set makes the membership check skip rather than reject."""
    ctx = _ctx(tmp_path)
    adopt_negotiated_game_id(ctx, FakeResult(""))

    assert ctx.game_uid == OWN_UID
    assert ctx.candidate_game_ids is None
    entry = _peer_entry("the-peers-own-real-id")
    assert state_binding_detail(
        entry, candidate_game_ids=ctx.candidate_game_ids, forbidden_role="thief",
    ) is None


def _peer_entry(game_id: str, *, turn: int = 1, role: str = "police") -> dict:
    """One final-reveal ledger entry as the PEER would publish it."""
    state = build_state_record(
        game_id=game_id, turn=turn, role=role, position=(0, 0), barriers_remaining=1,
    )
    return {"turn": turn, "h_commit": "unused-here", "payload": {"state": state}}


@pytest.mark.parametrize("foreign", HONEST_FOREIGN)
def test_an_honest_foreign_convention_is_adopted_and_still_matches(foreign, tmp_path):
    """THE MOST IMPORTANT TEST IN THIS PLAN, asserted along the WHOLE chain
    the gate feeds: gate -> adoption -> candidate set -> the audit's
    membership check. A UUID, an upper-case id, a 64-hex id or a non-ASCII
    label is an HONEST league entrant. It must be adopted as this game's id,
    its own id must be IN the candidate set, and a record committing that id
    must audit clean -- while a THIRD game's id in the same position is still
    caught, which is what stops this from passing vacuously."""
    ctx = _ctx(tmp_path)
    adopt_negotiated_game_id(ctx, FakeResult(foreign))

    assert ctx.game_uid == foreign
    assert ctx.negotiated_game_id == foreign
    assert ctx.candidate_game_ids == {OWN_UID, foreign}
    assert ctx.log_path.name == f"{foreign}.jsonl"
    assert ctx.log_path.exists()
    assert ctx.identity.game_uid == foreign and ctx.identity.log_path == ctx.log_path

    kwargs = {"candidate_game_ids": ctx.candidate_game_ids, "forbidden_role": "thief"}
    assert state_binding_detail(_peer_entry(foreign), **kwargs) is None
    assert state_binding_detail(_peer_entry(OWN_UID), **kwargs) is None
    intruder = state_binding_detail(_peer_entry("a-third-games-id"), **kwargs)
    assert intruder is not None and "not one of the ids on the table" in intruder


def test_police_keeps_its_own_uid_and_still_records_an_honest_peer_id(tmp_path):
    """D-61 policy, unchanged: police never adopts. But it must still put the
    peer's id in the candidate set -- that is the half `audit_state.py` warns
    would silently disable the check on the role that never adopts."""
    ctx = _ctx(tmp_path, role="police")
    adopt_negotiated_game_id(ctx, FakeResult("peer-side-convention"))

    assert ctx.game_uid == OWN_UID
    assert ctx.candidate_game_ids == {OWN_UID, "peer-side-convention"}
    assert ctx.log_path.name == f"{OWN_UID}.jsonl"
