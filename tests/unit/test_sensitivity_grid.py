"""The sweep is not allowed to turn a knob the rules fix (08-09).

The 08 outline names this plan's trap in as many words: "varying a FIXED
parameter to produce a more interesting graph is a rule-1 / rule-12
violation dressed as research". Every test below is a way that could still
happen -- a typo'd label silently skipped, a grid that asserts its own
status, an empty parse that permits everything, a `minimum` swept downward.

`parameter_status` is `lru_cache`d, so the empty-parse probe clears it on
both sides. A probe that leaves a poisoned cache behind is a test that
breaks its neighbours.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import load

grid = load("sensitivity_grid")
status = load("sensitivity_status")


def _knob(**overrides):
    """A Knob with harmless defaults -- each test overrides only its subject."""
    fields = {
        "name": "probe", "status": status.MINIMUM, "values": (7,),
        "read": lambda setting: 7, "apply": lambda setting, value: setting,
        "labels": ("board size",), "source": "",
    }
    fields.update(overrides)
    return grid.Knob(**fields)


def test_the_extract_is_parsed_not_typed():
    parsed = status.parameter_status()
    assert len(parsed) >= 30, parsed
    assert parsed["board size"] == status.MINIMUM
    assert parsed["number of agents"] == status.FIXED
    assert parsed["hint word limit"] == status.NEGOTIABLE


def test_every_scoring_and_scent_row_is_reported_fixed():
    """Table 16 and Table 17 -- the rows the trap would most like to move."""
    fixed = status.fixed_parameters()
    for name in ("scent strength at source", "scent decay rate", "scent field size",
                 "tie score", "movement range", "number of agents"):
        assert name in fixed, f"{name} must be fixed; got {status.parameter_status().get(name)}"
    assert len(fixed) >= 12


def test_an_empty_parse_raises_rather_than_permitting_everything(tmp_path, monkeypatch):
    empty = tmp_path / "PARAMETERS.md"
    empty.write_text("no tables here\n", encoding="utf-8")
    status.parameter_status.cache_clear()
    monkeypatch.setattr(status, "PARAMETERS_DOC", empty)
    try:
        with pytest.raises(ValueError, match="parsed 0 parameter rows"):
            status.parameter_status()
    finally:
        status.parameter_status.cache_clear()


def test_a_fixed_label_is_refused():
    with pytest.raises(ValueError, match="is FIXED"):
        status.refuse_fixed([_knob(labels=("scent decay rate",))])


def test_a_knob_that_honestly_declares_itself_fixed_is_still_refused():
    """The load-bearing case, and the one the other two guards do NOT cover.

    A knob claiming `status="fixed"` on a genuinely fixed row satisfies both
    the label-exists and the status-agrees checks; only the FIXED refusal
    stops it. Deleting that refusal was probed and this is the sole test
    that goes red on its own.
    """
    with pytest.raises(ValueError, match="is FIXED"):
        status.refuse_fixed([_knob(status=status.FIXED, labels=("tie score",))])


def test_a_label_the_extract_does_not_carry_is_refused():
    with pytest.raises(KeyError, match="no row"):
        status.refuse_fixed([_knob(labels=("bord size",))])


def test_a_knob_may_not_assert_its_own_status():
    with pytest.raises(ValueError, match="grid declares"):
        status.refuse_fixed([_knob(status=status.NEGOTIABLE, labels=("board size",))])


def test_an_appendix_f_knob_must_name_a_row():
    with pytest.raises(ValueError, match="must name the row"):
        status.refuse_fixed([_knob(labels=())])


def test_an_engineering_default_must_cite_its_source():
    with pytest.raises(ValueError, match="must cite its source"):
        status.refuse_fixed([_knob(status=status.ENGINEERING, labels=(), source="")])
    status.refuse_fixed([_knob(status=status.ENGINEERING, labels=(), source="valuebrain.py:29")])


def test_a_minimum_may_not_be_swept_below_what_the_repo_ships():
    base = grid.baseline()
    assert base.params.board_size == 7
    with pytest.raises(ValueError, match="DOWNWARD"):
        status.refuse_downward([_knob(values=(5, 7, 9), read=lambda s: s.params.board_size)], base)
    status.refuse_downward([_knob(values=(7, 9), read=lambda s: s.params.board_size)], base)


def test_the_downward_check_reaches_inside_the_joint_horizon_knob():
    """`horizon` carries tuples; a scalar-only comparison would skip it."""
    base = grid.baseline()
    horizon = _knob(
        name="horizon", labels=("move ceiling", "survival threshold"),
        values=((20, 20), (35, 35)),
        read=lambda s: (s.params.move_ceiling, s.params.survival_threshold),
    )
    with pytest.raises(ValueError, match="DOWNWARD"):
        status.refuse_downward([horizon], base)


def test_the_shipped_grid_passes_both_guards():
    knobs = grid.knobs()
    assert len(knobs) == 6
    status.refuse_fixed(knobs)
    status.refuse_downward(knobs, grid.baseline())


def test_every_knob_contains_the_baseline_it_is_measured_against():
    """OFAT needs an anchor: a knob whose values exclude the shipped value
    would report deltas against a configuration nothing else shares."""
    base = grid.baseline()
    for knob in grid.knobs():
        assert knob.read(base) in knob.values, knob.name


def test_growing_the_board_recentres_the_thief_and_leaves_the_cop_in_its_corner():
    base = grid.baseline()
    board = next(knob for knob in grid.knobs() if knob.name == "board_size")
    grown = board.apply(base, 11)
    assert grown.params.board_size == 11
    assert grown.params.thief_start == (5, 5)
    assert grown.params.cop_start == base.params.cop_start
