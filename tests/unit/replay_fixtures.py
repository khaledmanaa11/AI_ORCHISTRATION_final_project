"""A GENUINE `log_` artifact, built the way production builds one.

Not a hand-written dict of plausible-looking hex: every `h_commit` here comes
out of `commit_pack.commit()` and every `state` out of D-60's
`build_state_record`, so a test asserting `Verified OK` is asserting that real
SHA-256 work re-produced a real digest. A fixture carrying invented hashes
would fail no matter what the verifier did, and one carrying no hashes at all
would pass no matter what it did.

Not a `test_*.py` module, so pytest collects nothing from it (the
`local_view_fixtures.py` / `artifact_log_games.py` precedent).

RESEALING IS THE POINT OF `reseal`. A single-field tamper inside `turns`
breaks BOTH the turn's own hash and the artifact seal, because
`log_artifact_fields.SEALED_FIELDS` covers `turns`. A test that let both break
could not tell which check caught it. So the four field tampers reseal, and
the verdict they earn is proof that the PER-TURN re-hash fired on its own.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.security.commit_pack import commit
from pursuit.security.state_record import build_state_record
from pursuit.services.reporting.artifact_names import log_filename
from pursuit.services.reporting.artifacts import (
    artifact_digest,
    artifact_header,
    write_artifact,
)
from pursuit.services.reporting.log_artifact_fields import LogArtifactField, sealed_body
from pursuit.services.reporting.log_turn_fields import TurnField, WireSide
from pursuit.shared.deception_types import Intent

GAME_UID = "replayfixtureuid"
GAME_ID = "replayfixture"
SUB_GAME_INDEX = 1
ROLE = "police"
BARRIERS_REMAINING = 14
COMMITTED_TURNS = 4

#: The four `verify_reveal` inputs a single-bit change must be caught in. Four
#: separate tests, never one parametrized case: a verifier that re-hashes only
#: `move` passes a one-case test, and an emptied `parametrize` table SKIPS.
TAMPERABLE_FIELDS = (TurnField.STATE, TurnField.MOVE, TurnField.INTENT, TurnField.NONCE)


def _payload(turn: int) -> tuple[str, dict]:
    """One real commit: D-60's state record, D-59/D-66's composite action, and
    a genuine `secrets.token_hex(16)` nonce from `commit_pack.commit`."""
    state = build_state_record(
        game_id=GAME_ID, turn=turn, role=ROLE,
        position=(turn, 1), barriers_remaining=BARRIERS_REMAINING,
    )
    move = {"move": {"direction": "north", "kind": "move"}, "barrier": None}
    intent = Intent.TRUTH.value if turn % 2 == 0 else Intent.LIE.value
    h_commit, nonce = commit(state, move, intent)
    return h_commit, {
        TurnField.STATE: state, TurnField.MOVE: move,
        TurnField.INTENT: intent, TurnField.NONCE: nonce,
    }


def committed_turn(turn: int) -> dict:
    """A turn carrying an `h_commit`, in `log_turn_fields`' own shape."""
    h_commit, payload = _payload(turn)
    return {
        TurnField.TURN: turn,
        TurnField.HASH: h_commit,
        **payload,
        TurnField.COMMITMENT: {
            WireSide.SENT: h_commit, WireSide.RECEIVED: h_commit, WireSide.ACKED: h_commit,
        },
        TurnField.REVEALED_MOVE: {WireSide.SENT: payload[TurnField.MOVE], WireSide.RECEIVED: None},
        TurnField.HINT: {
            WireSide.OUTGOING: {"intent": payload[TurnField.INTENT], "text": "heading north"},
            WireSide.SENT: None, WireSide.RECEIVED: None,
        },
        TurnField.VERDICT: {},
        TurnField.PEER_CLAIMED_TURNS: {},
    }


def uncommitted_turn(turn: int) -> dict:
    """The trailing game-over turn: wire records, never a ledger entry. 07-05
    warns that counting it would make the ratio a lie."""
    record = committed_turn(turn)
    for name in (TurnField.HASH, *TAMPERABLE_FIELDS):
        record[name] = None
    return record


def artifact(*, committed: int = COMMITTED_TURNS, trailing: bool = True) -> dict:
    """A complete, sealed artifact. `committed=0` is the zero-turn case."""
    body = artifact_header(game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX)
    body[LogArtifactField.ROLE] = ROLE
    body[LogArtifactField.PRIOR_GAME_UIDS] = []
    turns = [committed_turn(turn) for turn in range(committed)]
    if trailing:
        turns.append(uncommitted_turn(committed))
    body[LogArtifactField.TURNS] = turns
    body[LogArtifactField.OUTCOME] = {"outcome": "capture", TurnField.TURN: committed}
    body[LogArtifactField.AUDIT_VERDICT] = {"matched": True, TurnField.TURN: committed}
    body[LogArtifactField.TRUNCATED_TAIL] = {"log": False, "ledger": False}
    return reseal(body)


def empty_artifact() -> dict:
    """No `turns` key at all -- the shape a caller can reach by handing over
    any sealed JSON object that is not a game."""
    body = artifact_header(game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX)
    body[LogArtifactField.ROLE] = ROLE
    body[LogArtifactField.PRIOR_GAME_UIDS] = []
    body[LogArtifactField.TURNS] = []
    body[LogArtifactField.OUTCOME] = None
    body[LogArtifactField.AUDIT_VERDICT] = None
    body[LogArtifactField.TRUNCATED_TAIL] = {"log": False, "ledger": False}
    return reseal(body)


def reseal(body: dict) -> dict:
    """Recompute the seal over the CURRENT body, so a per-turn tamper is
    caught by the per-turn re-hash alone and by nothing else."""
    body[LogArtifactField.LOG_DIGEST] = artifact_digest(sealed_body(body))
    return body


def _flip_state(state: dict) -> dict:
    """One field of D-60's own record moves, and the record stays LEGAL --
    so nothing but the hash can object to it."""
    return {**state, "barriers_remaining": state["barriers_remaining"] - 1}


def _flip_move(move: dict) -> dict:
    """`scripts/gate6_tamper.py:80-84`'s shape: the direction the peer
    actually played, replaced by a different legal one."""
    inner = move["move"]
    other = "south" if inner["direction"] != "south" else "north"
    return {**move, "move": {**inner, "direction": other}}


def _flip_intent(intent: str) -> str:
    """`scripts/gate6_tamper.py:43`'s shape, verbatim: truth <-> lie. Still a
    VALID intent, so this reaches the re-hash rather than the shape guard --
    which is the case that proves the hash is doing the work."""
    return Intent.LIE.value if intent == Intent.TRUTH.value else Intent.TRUTH.value


def _flip_nonce(nonce: str) -> str:
    """One hex character of the 32, and no more."""
    last = "0" if nonce[-1] != "0" else "1"
    return nonce[:-1] + last


#: One mutator per `verify_reveal` input, each producing a value that is still
#: WELL FORMED. A tamper that made the payload malformed would be caught by
#: `build_commit_payload`'s shape guard and would prove nothing about hashing.
TAMPERERS = {
    TurnField.STATE: _flip_state,
    TurnField.MOVE: _flip_move,
    TurnField.INTENT: _flip_intent,
    TurnField.NONCE: _flip_nonce,
}


def tamper(body: dict, field: str, *, index: int = 0) -> dict:
    """Flip exactly one field of exactly one committed turn, in place."""
    turn = body[LogArtifactField.TURNS][index]
    turn[field] = TAMPERERS[field](turn[field])
    return body


def write(directory: Path, body: dict) -> Path:
    """The artifact on disk, through the ONE gated write site (`write_artifact`
    and its D7-1 `logs/` refusal), under its `docs/PARAMETERS.md:167` name."""
    return write_artifact(Path(directory), log_filename(GAME_ID, SUB_GAME_INDEX), body)
