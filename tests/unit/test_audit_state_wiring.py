"""05-05 Task 3, the WIRING half -- split from test_audit_state_binding.py at
the 150-code-line gate (Segal Table 5), which is also where the seam is: the
sibling asserts on the CHECK, this file asserts on the SET the production
path actually hands it.

That distinction is the whole point. A control that hand-builds its own
two-element candidate set exercises the POLICE shape only -- it passes while
the thief wiring accuses, because on the thief `adopt_negotiated_game_id`
rebinds `ctx.game_uid` to the peer's id and a set rebuilt afterwards from
`{game_uid, negotiated_game_id}` holds ONE element. So every case here drives
`adopt_negotiated_game_id` for real and reads back what it produced.

`_state`/`_entry`/`_audit` are imported from the sibling rather than copied
(the established precedent: test_step0_and_audit_tamper.py imports its
harness from test_step0_and_audit.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pursuit.network.game_identity import GameIdentity, adopt_negotiated_game_id
from pursuit.security.audit import all_matched
from tests.unit.test_audit_state_binding import OUR_ID, PEER_ID, _audit, _entry, _state


@dataclass
class _Ctx:
    """The fields `adopt_negotiated_game_id` actually touches."""

    role: str
    game_uid: str
    log_path: Path
    identity: GameIdentity | None = None
    negotiated_game_id: str | None = None
    candidate_game_ids: set[str] | None = field(default=None)


@dataclass
class _Result:
    peer_game_id: str | None


def _adopted(role: str, own: str, peer: str | None, tmp_path) -> _Ctx:
    log_path = tmp_path / f"{own}.jsonl"
    ctx = _Ctx(role=role, game_uid=own, log_path=log_path,
               identity=GameIdentity(game_uid=own, log_path=log_path))
    adopt_negotiated_game_id(ctx, _Result(peer_game_id=peer))
    return ctx


def test_the_production_path_builds_a_two_element_set_on_both_roles(tmp_path):
    """WIRING ASSERTION, not a unit case. The convention-swap control below
    is VACUOUS if it hand-builds its own two-element set: a hand-built set
    exercises the police shape only and passes while the thief wiring
    accuses. So assert on the set the PRODUCTION path actually builds.

    A version that builds it from `{ctx.game_uid, ctx.negotiated_game_id}`
    AFTER adoption yields `{PEER_ID}` on the thief -- `negotiated_game_id(
    'thief', O, P)` is `P` and `game_uid` has just become `P` -- and MUST
    fail this."""
    police = _adopted("police", OUR_ID, PEER_ID, tmp_path)
    thief = _adopted("thief", OUR_ID, PEER_ID, tmp_path)

    assert police.candidate_game_ids == {OUR_ID, PEER_ID}
    assert thief.candidate_game_ids == {OUR_ID, PEER_ID}
    assert thief.game_uid == PEER_ID, "the thief must have rebound BEFORE we read the set"
    assert _adopted("thief", OUR_ID, None, tmp_path).candidate_game_ids is None


def test_control_a_convention_swapping_peer_is_matched_through_the_real_set(tmp_path):
    """The peer ADOPTED OUR id instead of keeping its own -- two honest
    implementations that merely swapped conventions. Driven through the set
    `adopt_negotiated_game_id` really produced, on the THIEF (the role where
    a set built after the rebind degenerates). Written against either
    equality shape this FAILS, which is the discrimination a control owes."""
    thief = _adopted("thief", OUR_ID, PEER_ID, tmp_path)
    entry, h = _entry(turn=1, state=_state(turn=1, role="police", game_id=OUR_ID))

    records = _audit(entry, h, candidates=thief.candidate_game_ids, forbidden="thief")

    assert all_matched(records), [r.detail for r in records]


def test_control_a_single_element_candidate_set_is_legitimate(tmp_path):
    """Our minted id and the peer's published id happen to be EQUAL, so the
    set has one element -- correctly. Nothing may assert len == 2."""
    ctx = _adopted("police", OUR_ID, OUR_ID, tmp_path)
    assert ctx.candidate_game_ids == {OUR_ID}

    entry, h = _entry(turn=1, state=_state(turn=1, role="thief", game_id=OUR_ID))
    records = _audit(entry, h, candidates=ctx.candidate_game_ids, forbidden="police")
    assert all_matched(records), [r.detail for r in records]
