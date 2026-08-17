"""Stepping, and the text the window prints.

Every assertion here is about something `pyproject.toml:38` cannot measure if
it moves: the cursor arithmetic and the strings live in `services/reporting/`
precisely because `*/gui/*` is omitted from coverage, and
`test_gui_structural.py` fails the moment a `BinOp` or an f-string appears in
the Tk layer. These tests are what stands behind that split.
"""

from __future__ import annotations

from pursuit.services.reporting.log_turn_fields import LANGUAGE_INTERNAL_FIELDS
from pursuit.services.reporting.replay_session import (
    NO_TURNS_LINE,
    SECTION_TITLES,
    ReplaySession,
)
from pursuit.services.reporting.replay_verify import check_turns, verdict_from
from tests.unit import replay_fixtures as fx

SOURCE = "log_replayfixture_g01.json"
TAMPER_INDEX = 2


def _session(**kwargs) -> ReplaySession:
    artifact = fx.artifact(**kwargs)
    checks = check_turns(artifact)
    return ReplaySession(artifact, checks, verdict_from(artifact, checks), source=SOURCE)


def _tampered_session() -> ReplaySession:
    artifact = fx.reseal(fx.tamper(fx.artifact(), fx.TurnField.MOVE, index=TAMPER_INDEX))
    checks = check_turns(artifact)
    return ReplaySession(artifact, checks, verdict_from(artifact, checks), source=SOURCE)


def test_a_fresh_session_opens_on_the_first_turn():
    session = _session()
    assert session.index == 0
    assert session.turn_count == fx.COMMITTED_TURNS + 1
    assert session.playing is False


def test_step_advances_one_turn_and_stops_at_the_last():
    session = _session()
    visited = [session.index]
    for _ in range(session.turn_count + 3):
        session.step()
        visited.append(session.index)
    assert visited[: session.turn_count] == list(range(session.turn_count))
    assert session.index == session.turn_count - 1, "the cursor ran past the last turn"


def test_reaching_the_end_pauses_rather_than_redrawing_forever():
    """A timer still firing against a clamped index looks like a freeze."""
    session = _session()
    session.play()
    assert session.playing is True
    for _ in range(session.turn_count):
        session.step()
    assert session.at_end is True and session.playing is False


def test_back_stops_at_the_first_turn():
    session = _session()
    session.step()
    session.step()
    assert session.index == 2
    for _ in range(5):
        session.back()
    assert session.index == 0


def test_play_from_the_end_rewinds_so_the_button_is_never_a_no_op():
    session = _session()
    for _ in range(session.turn_count):
        session.step()
    assert session.at_end is True
    session.play()
    assert session.index == 0 and session.playing is True
    session.pause()
    assert session.playing is False


def test_an_artifact_with_no_turns_cannot_be_played():
    """Nothing to step through, so `playing` stays False and the panels say
    so -- the session's own half of the nothing-to-verify state."""
    session = _session(committed=0, trailing=False)
    assert session.turn_count == 0
    session.play()
    assert session.playing is False
    session.step()
    assert session.index == 0
    assert session.blocks() == tuple(NO_TURNS_LINE for _ in SECTION_TITLES)


def test_every_section_has_a_block_and_none_is_empty():
    session = _session()
    blocks = session.blocks()
    assert len(blocks) == len(SECTION_TITLES) == 3
    assert all(block.strip() for block in blocks)


def test_the_panel_follows_the_cursor_onto_the_turn_that_failed():
    """The positional pairing of `turns` and `checks`: stepping onto the
    tampered turn must show ITS result, not the previous turn's."""
    session = _tampered_session()
    assert session.current_check().ok is True
    for _ in range(TAMPER_INDEX):
        session.step()
    assert session.index == TAMPER_INDEX
    assert session.current_turn()[fx.TurnField.TURN] == TAMPER_INDEX
    assert session.current_check().ok is False
    assert "does not match" in session.blocks()[1]


def test_a_hint_is_labelled_as_the_senders_own_claim():
    """Rule 25 / D-47: the intent flag is what the sender declared, never a
    verified fact, and the caption says so before the text."""
    block = _session().blocks()[2]
    assert "claims:" in block
    assert "heading north" in block


def test_no_internal_state_is_invented_at_render_time():
    """D7-8: the artifact carries none of the six `LANGUAGE_INTERNAL_FIELDS`,
    and rendering must not reintroduce one. The counter-control proves the
    scan can find a name at all."""
    assert len(LANGUAGE_INTERNAL_FIELDS) == 6
    rendered = "\n".join(_session().blocks())
    assert [name for name in LANGUAGE_INTERNAL_FIELDS if name in rendered] == []
    assert "belief_argmax" in "\n".join((rendered, "belief_argmax"))
