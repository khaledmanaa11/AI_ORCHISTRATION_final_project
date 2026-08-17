"""Task 2: the artifact carries WIRE TRUTH ONLY, and it is sealed.

The leak this file guards against is not hypothetical. 07-11 reproduced a
rules 8-9 disqualification in which the cop's published belief was a delta on
`ctx.state.thief`, and D7-8 records that the true argmax is STILL written into
every `language_turn` JSONL record -- correct there (rule 38's audit log),
fatal in a file that is emailed to the lecturer.
"""

from __future__ import annotations

import json

import pytest

from pursuit.services.reporting.artifact_log import (
    SEALED_FIELDS,
    LogArtifactField,
    build_log_artifact,
    verify_log_artifact,
    verify_log_turns,
    write_log_artifact,
)
from pursuit.services.reporting.artifacts import log_filename
from pursuit.services.reporting.log_turn_fields import (
    LANGUAGE_INTERNAL_FIELDS,
    TurnField,
    WireSide,
)
from tests.unit.artifact_log_fixtures import GAME_UID, TRUE_CELL
from tests.unit.artifact_log_games import GAME_TURNS, write_game

GAME_ID = "logfixture"
SUB_GAME_INDEX = 3


def _artifact(tmp_path, **kwargs):
    log_path = write_game(tmp_path, **kwargs)
    return build_log_artifact(
        log_path, game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX
    )


@pytest.mark.parametrize("field", sorted(LANGUAGE_INTERNAL_FIELDS))
def test_no_internal_language_field_reaches_the_artifact(tmp_path, field):
    assert len(LANGUAGE_INTERNAL_FIELDS) == 6, "a thinned deny-list would pass vacuously"
    assert field not in json.dumps(_artifact(tmp_path))


def test_the_true_cell_never_reaches_the_artifact_in_any_form(tmp_path):
    """The absence scan and its COUNTER-CONTROL. 07-11's lesson: a scanner
    that has never found anything is not evidence that there is nothing."""
    serialized = json.dumps(_artifact(tmp_path))
    assert json.dumps(list(TRUE_CELL)) not in serialized
    assert "belief_argmax" not in serialized
    planted = json.dumps({"belief_argmax": list(TRUE_CELL)})
    assert json.dumps(list(TRUE_CELL)) in planted, "the scan can find something"


def test_the_hint_carries_the_intent_flag_and_nothing_else(tmp_path):
    hints = [t[TurnField.HINT][WireSide.OUTGOING] for t in _artifact(tmp_path)["turns"]]
    present = [h for h in hints if h is not None]
    assert len(present) == len(GAME_TURNS)
    assert all(sorted(h) == ["intent", "text"] for h in present)
    assert all(h["intent"] in {"truth", "lie"} for h in present)


def test_the_seal_covers_the_truncation_marker(tmp_path):
    assert LogArtifactField.TRUNCATED_TAIL in SEALED_FIELDS
    artifact = _artifact(tmp_path, log_tail='{"event": "mess')
    assert artifact[LogArtifactField.TRUNCATED_TAIL] == {"log": True, "ledger": False}


def test_a_written_artifact_re_verifies_its_own_seal(tmp_path):
    log_path = write_game(tmp_path)
    out = tmp_path / "artifacts"
    path = write_log_artifact(
        out, log_path, game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX
    )
    assert path.name == log_filename(GAME_ID, SUB_GAME_INDEX)
    assert verify_log_artifact(path)
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered[LogArtifactField.TURNS][0][TurnField.NONCE] = "0" * 32
    path.write_text(json.dumps(tampered), encoding="utf-8")
    assert not verify_log_artifact(path)


def test_a_log_for_a_different_game_is_refused(tmp_path):
    log_path = write_game(tmp_path)
    with pytest.raises(ValueError, match="carries game_uid"):
        build_log_artifact(
            log_path, game_uid="someoneelse", game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX
        )


def test_an_emptied_artifact_reports_zero_committed_turns(tmp_path):
    """The step-5 guard's target. `verify_log_turns` returns (0, 0) on an empty
    turn list, and `0 == 0` is True -- so every caller must check the count,
    and this test is what makes that requirement fail loudly if it is dropped."""
    artifact = _artifact(tmp_path)
    verified, committed = verify_log_turns(artifact)
    assert (verified, committed) == (len(GAME_TURNS), len(GAME_TURNS))
    artifact[LogArtifactField.TURNS] = []
    assert verify_log_turns(artifact) == (0, 0)


def test_a_ledger_whose_hash_disagrees_with_its_payload_is_refused_at_write(tmp_path):
    """`write_log_artifact` re-hashes what it just wrote and refuses to ship a
    file whose own turns do not verify. A `FAILED` verdict on the grader's
    screen must never be OUR transcription bug wearing the opponent's name."""
    log_path = write_game(tmp_path)
    ledger_path = log_path.parent / f"{log_path.stem}.ledger.jsonl"
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["h_commit"] = "0" * 64
    lines[0] = json.dumps(first)
    ledger_path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    with pytest.raises(ValueError, match="re-hashes"):
        write_log_artifact(
            tmp_path / "artifacts", log_path,
            game_uid=GAME_UID, game_id=GAME_ID, sub_game_index=SUB_GAME_INDEX,
        )


def test_a_tampered_turn_fails_its_re_hash(tmp_path):
    """The re-hash is real: change one nonce and the turn stops verifying."""
    artifact = _artifact(tmp_path)
    artifact[LogArtifactField.TURNS][0][TurnField.NONCE] = "f" * 32
    verified, committed = verify_log_turns(artifact)
    assert committed == len(GAME_TURNS)
    assert verified == len(GAME_TURNS) - 1
