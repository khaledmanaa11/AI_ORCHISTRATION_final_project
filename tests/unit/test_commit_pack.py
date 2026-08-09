"""Tests for commit_pack.py (SEC-01, SEC-03, SEC-04, D-59)."""

import pytest

from pursuit.security.commit_pack import CommitKey, build_commit_payload, commit, verify_reveal
from pursuit.shared.deception_types import Intent

_STATE = {
    "game_id": "g1",
    "turn": 3,
    "role": "cop",
    "position": {"row": 1, "col": 2},
    "barriers_remaining": 2,
}
_MOVE_ONLY = {"move": {"kind": "move", "direction": "north"}, "barrier": None}
_MOVE_WITH_BARRIER = {
    "move": {"kind": "move", "direction": "stay"},
    "barrier": {"kind": "barrier", "direction": "north"},
}


def _flip_nonce(nonce: str) -> str:
    return "0" if nonce != "0" else "1"


@pytest.mark.parametrize("move", [_MOVE_ONLY, _MOVE_WITH_BARRIER])
def test_commit_reveal_audit_round_trip(move: dict) -> None:
    """D-59: commit-time and audit-time hashing always agree, and the
    function is genuinely opaque to whether the composite action carries a
    barrier (move-only vs barrier-bearing example)."""
    h_commit, nonce = commit(_STATE, move, Intent.TRUTH.value)

    assert verify_reveal(h_commit, state=_STATE, move=move, intent=Intent.TRUTH.value, nonce=nonce)

    tampered_state = {**_STATE, "turn": _STATE["turn"] + 1}
    assert not verify_reveal(
        h_commit, state=tampered_state, move=move, intent=Intent.TRUTH.value, nonce=nonce
    )

    tampered_move = {**move, "move": {"kind": "move", "direction": "south"}}
    assert not verify_reveal(
        h_commit, state=_STATE, move=tampered_move, intent=Intent.TRUTH.value, nonce=nonce
    )

    tampered_barrier = {**move, "barrier": {"kind": "barrier", "direction": "east"}}
    assert not verify_reveal(
        h_commit, state=_STATE, move=tampered_barrier, intent=Intent.TRUTH.value, nonce=nonce
    )

    assert not verify_reveal(
        h_commit, state=_STATE, move=move, intent=Intent.LIE.value, nonce=nonce
    )

    assert not verify_reveal(
        h_commit, state=_STATE, move=move, intent=Intent.TRUTH.value, nonce=_flip_nonce(nonce)
    )


def test_commit_generates_hex_nonce_via_secrets_not_random() -> None:
    """SEC-04/rule 18: nonce comes from commit() itself, 32 hex chars."""
    _, nonce = commit(_STATE, _MOVE_ONLY, Intent.LIE.value)
    assert len(nonce) == 32
    int(nonce, 16)  # raises ValueError if not valid hex


def test_build_commit_payload_returns_exactly_four_keys() -> None:
    """A stray extra key surviving into the hashed payload is impossible
    because build_commit_payload alone controls the shape."""
    payload = build_commit_payload(
        state=_STATE, move=_MOVE_WITH_BARRIER, intent=Intent.TRUTH.value, nonce="abc123"
    )
    assert set(payload) == {
        CommitKey.STATE.value,
        CommitKey.MOVE.value,
        CommitKey.INTENT.value,
        CommitKey.NONCE.value,
    }
    assert payload[CommitKey.MOVE.value] == _MOVE_WITH_BARRIER


def test_build_commit_payload_rejects_bool_intent() -> None:
    """Pitfall 3: bool is an int subtype, but here it is not even a str."""
    with pytest.raises(TypeError):
        build_commit_payload(state=_STATE, move=_MOVE_ONLY, intent=True, nonce="abc123")


def test_build_commit_payload_rejects_unknown_intent_string() -> None:
    with pytest.raises(ValueError):
        build_commit_payload(state=_STATE, move=_MOVE_ONLY, intent="maybe", nonce="abc123")


def test_build_commit_payload_rejects_non_dict_state() -> None:
    with pytest.raises(TypeError):
        build_commit_payload(state="not-a-dict", move=_MOVE_ONLY, intent=Intent.TRUTH.value, nonce="abc")


def test_build_commit_payload_rejects_non_dict_move() -> None:
    with pytest.raises(TypeError):
        build_commit_payload(state=_STATE, move="not-a-dict", intent=Intent.TRUTH.value, nonce="abc")


def test_build_commit_payload_rejects_non_str_nonce() -> None:
    with pytest.raises(TypeError):
        build_commit_payload(state=_STATE, move=_MOVE_ONLY, intent=Intent.TRUTH.value, nonce=123)


def test_build_commit_payload_rejects_empty_nonce() -> None:
    with pytest.raises(ValueError):
        build_commit_payload(state=_STATE, move=_MOVE_ONLY, intent=Intent.TRUTH.value, nonce="")


def test_commit_key_str_returns_the_bare_field_name() -> None:
    assert str(CommitKey.MOVE) == "move"
