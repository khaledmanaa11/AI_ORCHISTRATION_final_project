"""`sdk/view_text.py` -- every string the live sidebar prints.

The load-bearing cases are the ABSENT ones: a fabricated `0.0` idle reading
would claim the agent had just been touched, and a fabricated belief caption
would claim a posterior that was deliberately not published.
"""

from __future__ import annotations

import dataclasses

import pytest

from pursuit.sdk.local_view import HintView
from pursuit.sdk.view_text import (
    ABSENT,
    NO_BELIEF_LINE,
    NO_HINTS_LINE,
    SIDEBAR_TITLES,
    UNDECLARED_INTENT,
    as_block,
    belief_lines,
    hint_lines,
    sidebar_blocks,
    status_lines,
    timer_line,
)
from tests.unit import local_view_fixtures as fx

_IDLE = 12.5
_THRESHOLD = 60.0


@pytest.fixture
def view(tmp_path, default_params, network_params):
    return fx.honest_view(tmp_path, default_params, network_params)


def test_the_status_block_names_the_seat_and_its_own_position(view):
    lines = status_lines(view)
    assert f"role: {view.role}" in lines
    assert f"turn: {view.turn}" in lines
    assert f"state: {view.machine_state}" in lines
    assert "own cell: (0, 0)" in lines
    assert f"barriers placed: {fx.BARRIERS_PLACED}" in lines


def test_the_belief_caption_reports_the_published_map(view):
    lines = belief_lines(view)
    assert any(line.startswith("entropy:") for line in lines)
    assert any(line.startswith("reliability:") for line in lines)
    assert any(line.startswith("lit cells:") for line in lines)
    assert NO_BELIEF_LINE not in lines


def test_an_absent_belief_says_so_rather_than_inventing_one(view):
    assert belief_lines(dataclasses.replace(view, belief=None)) == (NO_BELIEF_LINE,)


def test_the_lit_cell_count_matches_the_published_support(view):
    positive = sum(1 for row in view.belief.rows for value in row if value > 0.0)
    assert f"lit cells: {positive}" in belief_lines(view)


def test_an_absent_idle_reading_prints_as_absent_not_as_zero(view):
    without = dataclasses.replace(
        view, idle_seconds=None, watchdog_threshold_seconds=_THRESHOLD
    )
    line = timer_line(without)
    assert ABSENT in line and "0.00 /" not in line
    assert "60.00" in line


def test_a_live_idle_reading_is_printed_against_the_threshold(view):
    line = timer_line(
        dataclasses.replace(view, idle_seconds=_IDLE, watchdog_threshold_seconds=_THRESHOLD)
    )
    assert line == "idle: 12.50 / 60.00 s"


def test_each_hint_is_labelled_as_the_senders_own_claim(view):
    line = hint_lines(view)[0]
    assert "thief" in line and "claims: lie" in line
    assert fx.INCOMING_HINT["text"] in line


def test_an_undeclared_or_unstamped_hint_says_so(view):
    bare = dataclasses.replace(
        view, hints=(HintView(sender="thief", turn=None, text="nothing", claimed_intent=None),)
    )
    line = hint_lines(bare)[0]
    assert UNDECLARED_INTENT in line and f"t{ABSENT}" in line


def test_an_empty_hint_log_says_so(view):
    assert hint_lines(dataclasses.replace(view, hints=())) == (NO_HINTS_LINE,)


def test_every_sidebar_title_gets_exactly_one_block(view):
    blocks = sidebar_blocks(view)
    assert len(blocks) == len(SIDEBAR_TITLES)
    assert all(isinstance(block, str) and block for block in blocks)


def test_the_timer_rides_in_the_status_block(view):
    assert timer_line(view) in sidebar_blocks(view)[0]


def test_a_block_is_one_line_per_entry():
    assert as_block(("a", "b", "c")) == "a\nb\nc"
    assert as_block(()) == ""
