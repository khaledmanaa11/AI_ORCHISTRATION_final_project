"""`shared/absent.py` -- the stated-absence marker, and the proof that moving
its shape out of `result_artifact_fields.py` changed no artifact byte.

07-07 wrote `TOKENS_ABSENT` and `GAMES_PLAYED_UNSET` as inline literals. 08-04
rebuilt both from `stated_absent` when a third caller needed the shape. Those
two dicts land in `result_<game_id>.json`, which a grader reads, so the
regression that matters is not "does the helper work" but "did the values
move". The first test below is that control.
"""

from __future__ import annotations

import pytest

from pursuit.services.reporting.result_artifact_fields import (
    GAMES_PLAYED_UNSET,
    TOKENS_ABSENT,
    TokensField,
)
from pursuit.shared.absent import (
    ABSENT_DETAIL_KEY,
    ABSENT_PRESENT_KEY,
    is_stated_absent,
    stated_absent,
)

#: The two dicts EXACTLY as 07-02/07-07 committed them, transcribed from the
#: pre-08-04 source rather than recomputed from the module under test -- a
#: control that reads its subject proves nothing.
FROZEN_TOKENS_ABSENT = {
    "present": False,
    "detail": (
        "the language layer was off for this game (agent_context.language is None), "
        "so no token spend exists to report -- an honest absence, never a zero "
        "presented as a measurement"
    ),
}
FROZEN_GAMES_PLAYED_UNSET = {
    "present": False,
    "detail": (
        "deliberately unset. 07-00 fixed the rule-37/38 counter MECHANISM and left "
        "its VALUE to a human decision (docs/phases/phase-7/"
        "GAMES-PLAYED-RECONSTRUCTION.md); rule 38 makes a false games-played "
        "declaration an ABSOLUTE disqualification, so nothing here may choose it. "
        "This game's declared figure is in declaration_<game_id>.json"
    ),
}


def test_the_two_shipped_markers_are_byte_identical_to_their_pre_refactor_values():
    assert TOKENS_ABSENT == FROZEN_TOKENS_ABSENT
    assert GAMES_PLAYED_UNSET == FROZEN_GAMES_PLAYED_UNSET


def test_the_two_key_spellings_did_not_drift():
    assert (TokensField.PRESENT, TokensField.DETAIL) == (ABSENT_PRESENT_KEY, ABSENT_DETAIL_KEY)


def test_a_marker_carries_its_reason():
    marker = stated_absent("because the repository does not exist yet")
    assert marker[ABSENT_PRESENT_KEY] is False
    assert marker[ABSENT_DETAIL_KEY] == "because the repository does not exist yet"


@pytest.mark.parametrize("detail", ["", "   ", None, 7])
def test_an_absence_with_no_reason_is_refused(detail):
    """"Absent" with no reason is the hole the marker exists to close."""
    with pytest.raises(ValueError, match="non-empty reason"):
        stated_absent(detail)


def test_is_stated_absent_recognises_only_a_real_marker():
    assert is_stated_absent(stated_absent("why"))
    assert is_stated_absent(TOKENS_ABSENT)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "https://github.com/team/cop",
        {},
        {"present": True, "detail": "a presence record is not an absence"},
        {"present": False},
        {"present": False, "detail": 3},
        {"detail": "no present key"},
    ],
)
def test_is_stated_absent_refuses_everything_else(value):
    assert not is_stated_absent(value)
