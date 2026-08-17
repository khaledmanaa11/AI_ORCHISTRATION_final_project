"""The `result_` artifact's defensive branches, each given a REAL cause.

Two of these cannot fire on a healthy builder, which is exactly why 07-05
found them uncovered and why they are driven here rather than left as
unexercised prose: the post-write seal check, and the accumulator's guards
against a previous generation that is on disk but not the shape we wrote.
"""

from __future__ import annotations

import json

import pytest

from pursuit.services.reporting.artifact_result import (
    ResultArtifactField,
    TokensField,
    accumulate_series,
    build_result_artifact,
    read_series,
    verify_result_artifact,
    write_result_artifact,
)
from pursuit.services.reporting.artifacts import ArtifactField, result_filename
from pursuit.services.reporting.result_artifact_fields import SEALED_FIELDS, empty_series

GAME_ID = "edgeseries"
MEASURED = {TokensField.PRESENT: True, TokensField.CALLS: 1, TokensField.INPUT_TOKENS: 5,
            TokensField.OUTPUT_TOKENS: 2, TokensField.TOTAL_TOKENS: 7}


def _artifact(**overrides) -> dict:
    base = {
        "game_uid": GAME_ID, "game_id": GAME_ID, "role": "thief", "sub_game_index": 1,
        "agreement": {"agreed": None}, "tokens": MEASURED, "commit_hash": "abc123",
        "log_artifact": None, "previous": None,
    }
    base.update(overrides)
    return build_result_artifact(**base)


def test_an_artifact_whose_body_was_changed_after_sealing_is_refused_at_write(tmp_path):
    """The post-write seal check, given a real cause: a body edited after its
    digest was computed. Shipping it would put a broken report in an inbox."""
    artifact = _artifact()
    artifact[ResultArtifactField.ROLE] = "police"

    with pytest.raises(ValueError, match="failed seal re-verification"):
        write_result_artifact(tmp_path, artifact)


def test_the_header_is_inside_the_seal_unlike_the_log_artifact(tmp_path):
    """STRICTER than `log_artifact_fields.SEALED_FIELDS` on purpose: this is the
    emailed report, and `game_id` is what files it against a game (rules 32/35).
    A header outside the seal could re-file a real report against another game.
    """
    assert {ArtifactField.GAME_UID, ArtifactField.GAME_ID} <= set(SEALED_FIELDS)
    assert len(SEALED_FIELDS) == 7, "a thinned sealed set would make the check vacuous"

    path = write_result_artifact(tmp_path, _artifact())
    assert verify_result_artifact(path), "the untouched file is the control"

    written = json.loads(path.read_text(encoding="utf-8"))
    written[ArtifactField.GAME_UID] = "someone-elses-game"
    path.write_text(json.dumps(written), encoding="utf-8")
    assert verify_result_artifact(path) is False


def test_read_series_treats_absent_corrupt_and_wrong_shaped_files_as_absent(tmp_path):
    """Three causes, three files. Refusing to report because the PREVIOUS
    report is unreadable would hand rule 32 the very game it sanctions."""
    assert read_series(tmp_path, GAME_ID) is None

    corrupt = tmp_path / result_filename("corrupt")
    corrupt.write_text("{not json", encoding="utf-8")
    assert read_series(tmp_path, "corrupt") is None

    wrong = tmp_path / result_filename("wrong")
    wrong.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert read_series(tmp_path, "wrong") is None


def test_the_accumulator_ignores_a_previous_generation_of_the_wrong_shape():
    """A `previous` that is not a dict, and one whose counts are not integers,
    both restart from zero rather than raising or silently adding a `True`."""
    assert accumulate_series(None, MEASURED)[TokensField.TOTAL_TOKENS] == 7
    assert accumulate_series("not a dict", MEASURED)[TokensField.TOTAL_TOKENS] == 7

    poisoned = {TokensField.TOTAL_TOKENS: True, TokensField.INPUT_TOKENS: "9",
                TokensField.GAMES_MEASURED: None}
    accumulated = accumulate_series(poisoned, MEASURED)
    assert accumulated[TokensField.TOTAL_TOKENS] == 7, "`True` is an int and must not add one"
    assert accumulated[TokensField.INPUT_TOKENS] == 5
    assert accumulated[TokensField.GAMES_MEASURED] == 1


def test_an_empty_series_is_all_zeros_with_nothing_measured():
    """The zeros are readable as "no game contributed", not as "no tokens"."""
    assert set(empty_series()) == {
        TokensField.CALLS, TokensField.INPUT_TOKENS, TokensField.OUTPUT_TOKENS,
        TokensField.TOTAL_TOKENS, TokensField.GAMES_MEASURED,
    }
    assert set(empty_series().values()) == {0}


def test_a_previous_sub_game_list_of_the_wrong_shape_is_not_carried_forward():
    """A corrupt list slot must not append this game onto a string."""
    artifact = _artifact(previous={ResultArtifactField.SUB_GAMES: "not a list"})
    assert len(artifact[ResultArtifactField.SUB_GAMES]) == 1
