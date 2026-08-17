"""The defensive branches of the `log_` join, each with a real input.

Split from `test_artifact_log.py` at the 150-code-line gate. Every branch here
was found by a coverage run, not guessed: an untested defensive branch is a
branch nobody has ever proved does the right thing.
"""

from __future__ import annotations

import json

import pytest

from pursuit.services.reporting import artifact_log
from pursuit.services.reporting.artifact_log import write_log_artifact
from pursuit.services.reporting.log_join import join_game
from pursuit.services.reporting.log_turn_fields import TurnField, WireSide, outgoing_hint
from tests.unit.artifact_log_fixtures import GAME_UID, write_jsonl
from tests.unit.artifact_log_games import GAME_TURNS, write_game

GAME_ID = "edgecases"
SUB_GAME_INDEX = 2


def _append(log_path, record):
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def test_a_wire_record_with_no_envelope_is_skipped_not_crashed(tmp_path):
    """`turn_events.illegal_transition_record` and the terminal `audit_verdict`
    both carry no envelope, and a truncated or hostile peer record may carry a
    non-dict one. Neither may take the builder down."""
    log_path = write_game(tmp_path)
    before = len(join_game(log_path).turns)
    _append(log_path, {"event": "message_received", "game_uid": GAME_UID, "turn": 1,
                       "sender": "police", "timestamp": "t"})
    _append(log_path, {"event": "message_received", "game_uid": GAME_UID, "turn": 1,
                       "sender": "police", "timestamp": "t", "envelope": "not-a-dict"})
    joined = join_game(log_path)
    assert len(joined.turns) == before
    turn_one = next(t for t in joined.turns if t[TurnField.TURN] == 1)
    assert turn_one[TurnField.COMMITMENT][WireSide.RECEIVED] is not None


def test_a_record_with_an_unusable_turn_is_skipped(tmp_path):
    """A non-int turn cannot be a key and must not become one."""
    log_path = write_game(tmp_path)
    before = [t[TurnField.TURN] for t in join_game(log_path).turns]
    for bad in (None, "3", 2.5, True):
        _append(log_path, {"event": "message_sent", "game_uid": GAME_UID, "turn": bad,
                           "sender": "police", "timestamp": "t",
                           "envelope": {"type": "commit", "turn": bad, "sender": "thief",
                                        "payload": {"h_commit": "x"}}})
    assert [t[TurnField.TURN] for t in join_game(log_path).turns] == before


@pytest.mark.parametrize(
    "language", [None, {}, {"outgoing_hint": None}, {"outgoing_hint": "text"}, "not-a-dict"]
)
def test_a_language_record_without_a_usable_outgoing_hint_yields_none(language):
    assert outgoing_hint(language) is None


def test_the_outgoing_hint_is_read_when_it_is_there():
    """The control for the parametrized absence cases above."""
    assert outgoing_hint({"outgoing_hint": {"intent": "lie", "text": "x", "extra": 1}}) == {
        "intent": "lie", "text": "x"
    }


def test_a_game_with_no_ledger_at_all_still_produces_an_artifact(tmp_path):
    """A crash before the first commit. The artifact is honest and EMPTY of
    committed turns rather than absent -- and `verify_log_turns` says so."""
    log_path = write_game(tmp_path)
    (log_path.parent / f"{log_path.stem}.ledger.jsonl").unlink()
    joined = join_game(log_path)
    assert len(joined.turns) == len(GAME_TURNS) + 1
    assert all(t[TurnField.HASH] is None for t in joined.turns)
    artifact = artifact_log.build_log_artifact(
        log_path, game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX
    )
    assert artifact_log.verify_log_turns(artifact) == (0, 0)


def test_an_artifact_whose_seal_does_not_survive_the_write_is_refused(tmp_path, monkeypatch):
    """The seal half of the post-write promise, injected: a rotation that
    landed the wrong generation looks exactly like this."""
    log_path = write_game(tmp_path)
    monkeypatch.setattr(artifact_log, "verify_log_artifact", lambda path: False)
    with pytest.raises(ValueError, match="seal re-verification"):
        write_log_artifact(
            tmp_path / "artifacts", log_path,
            game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX,
        )


def test_an_empty_log_and_ledger_join_to_an_empty_game(tmp_path):
    """Nothing on disk yet is a legitimate pre-game state, not an error."""
    log_path = write_jsonl(tmp_path / "empty.jsonl", [])
    joined = join_game(log_path)
    assert joined.turns == []
    assert joined.game_uids == () and joined.role is None
    assert joined.outcome is None and joined.audit_verdict is None
    assert joined.truncated_tail == {"log": False, "ledger": False}


def test_a_pre_negotiation_game_uid_is_carried_not_refused(tmp_path):
    """D-61, measured on a real thief-side log: `adopt_negotiated_game_id`
    renames the log mid-stream, so the one record written before the handshake
    keeps its process-local id. A builder that took the FIRST record's uid as
    "the log's uid" would have refused the thief an artifact in every game."""
    log_path = write_game(tmp_path)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    stale = json.loads(lines[0])
    stale["game_uid"] = "prenegotiation01"
    log_path.write_text(
        "".join(f"{line}\n" for line in [json.dumps(stale), *lines]), encoding="utf-8"
    )
    assert join_game(log_path).game_uids == ("prenegotiation01", GAME_UID)

    artifact = artifact_log.build_log_artifact(
        log_path, game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX
    )
    assert artifact[artifact_log.LogArtifactField.PRIOR_GAME_UIDS] == ["prenegotiation01"]
    assert artifact_log.verify_log_turns(artifact) == (len(GAME_TURNS), len(GAME_TURNS))


def test_a_log_holding_none_of_the_requested_uid_is_still_refused(tmp_path):
    """The check the D-61 tolerance must not have softened away."""
    log_path = write_game(tmp_path)
    with pytest.raises(ValueError, match="not the requested"):
        artifact_log.build_log_artifact(
            log_path, game_uid="anothergame00000", game_id=GAME_ID,
            sub_game_index=SUB_GAME_INDEX,
        )
