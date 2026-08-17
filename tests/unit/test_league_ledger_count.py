"""The rule-38 counter-control: an honest games-played claim passes against the
ledger and an inflated one fails, and NOTHING here chooses the declared value.

Split from `test_league_ledger.py` along the seam the two subjects already
have: what the ledger RECORDS and REFUSES there, what is DERIVED from it here.

Why the control pair is the test that matters. `docs/RULES.md:79` (rule 38)
makes a false games-played declaration an ABSOLUTE disqualification, and the
counter that used to answer the question is not evidence: 07-00 measured one
`pytest` run advancing `config/{police,thief}/games_played.json` by +14 for
zero games. A derivation nobody can falsify is worth no more than that
counter, so the pair below is asserted in both directions.
"""

from __future__ import annotations

import pytest

from pursuit.services.reporting.league_ledger import (
    LEAGUE_LEDGER_UNSET,
    count_reading,
    declared_count_matches,
    games_played_reading,
    read_ledger,
    record_league_game,
)
from pursuit.shared.absent import is_stated_absent

GAME = {"outcome": "cop_win", "commit_hash": "deadbeef"}


def _ledger(tmp_path, *specs):
    for index, (opponent, scored) in enumerate(specs):
        record_league_game(
            tmp_path, opponent=opponent, game_id=f"g{index}", scored=scored, **GAME
        )
    return read_ledger(tmp_path)


def test_the_honest_count_passes_and_an_inflated_one_fails(tmp_path):
    """THE control pair. Two scored games plus a warm-up."""
    ledger = _ledger(tmp_path, ("alpha", True), ("beta", True), ("alpha", False))

    assert declared_count_matches(ledger, 2, scored_only=True)
    assert declared_count_matches(ledger, 3, scored_only=False)

    for inflated in (3, 4, 10, 1922):
        assert not declared_count_matches(ledger, inflated, scored_only=True)
    for inflated in (4, 5, 1915):
        assert not declared_count_matches(ledger, inflated, scored_only=False)


def test_an_understated_count_fails_too(tmp_path):
    """Rule 38 says "falsely declare", not "overstate" -- understating one's
    own play is equally a misstatement."""
    ledger = _ledger(tmp_path, ("alpha", True), ("beta", True))
    assert not declared_count_matches(ledger, 1, scored_only=True)
    assert not declared_count_matches(ledger, 0, scored_only=True)


@pytest.mark.parametrize("claim", [None, "2", 2.0, True, False, [2]])
def test_a_malformed_claim_is_a_failed_claim_not_an_error(tmp_path, claim):
    """A verdict function returns a verdict. `True` is refused explicitly:
    `True == 1` in Python and a bool must never pass as a count."""
    assert not declared_count_matches(_ledger(tmp_path, ("alpha", True)), claim, scored_only=True)


def test_an_empty_ledger_derives_zero_and_still_declares_nothing(tmp_path):
    reading = games_played_reading(read_ledger(tmp_path))
    assert reading["scored"] == 0
    assert reading["all_recorded"] == 0
    assert is_stated_absent(reading["declared"])


def test_the_reading_never_collapses_the_two_candidate_counts(tmp_path):
    """Which reading rule 37/38 asks for is OQ8-2, a human's decision. A single
    number here would answer it by accident."""
    reading = games_played_reading(_ledger(tmp_path, ("alpha", True), ("alpha", False)))
    assert reading["scored"] == 1
    assert reading["all_recorded"] == 2
    assert reading["distinct_scored_opponents"] == 1
    assert reading["declared"] == LEAGUE_LEDGER_UNSET


def test_the_unset_marker_names_the_document_the_human_decides_from(tmp_path):
    detail = LEAGUE_LEDGER_UNSET["detail"]
    assert "GAMES-PLAYED-RECONSTRUCTION.md" in detail
    assert "ABSOLUTE disqualification" in detail


def test_scored_only_has_no_default(tmp_path):
    ledger = _ledger(tmp_path, ("alpha", True))
    with pytest.raises(TypeError, match="scored_only"):
        declared_count_matches(ledger, 1)
    with pytest.raises(TypeError, match="scored_only"):
        count_reading(ledger)


LEDGER_MODULES = ("league_ledger.py", "league_ledger_fields.py", "league_ledger_bounds.py")


def _executable_source(path) -> str:
    """`path`'s source with every DOCSTRING and comment line removed.

    By AST, not by splitting on `\"\"\"`: a first draft used
    `source.split('\"\"\"')[-1]`, which keeps only the tail after the LAST
    docstring in the file and therefore searched almost nothing. Both modules
    discuss `games_played.json` at length in prose -- that prose is the point --
    so the test is only meaningful if the prose is what gets stripped.
    """
    import ast

    source = path.read_text(encoding="utf-8")
    documented = set()
    for node in ast.walk(ast.parse(source)):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        constant = getattr(first, "value", None)
        if (
            isinstance(first, ast.Expr)
            and isinstance(constant, ast.Constant)
            and isinstance(constant.value, str)
        ):
            documented.update(range(first.lineno, first.end_lineno + 1))
    return "\n".join(
        line
        for number, line in enumerate(source.splitlines(), 1)
        if number not in documented and not line.lstrip().startswith("#")
    )


def test_the_docstring_stripper_actually_strips_docstrings():
    """The control on the control: without this, the test below passes for a
    module that reads the counter in a function whose docstring came last."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "src/pursuit/services/reporting"
    raw = (root / "league_ledger.py").read_text(encoding="utf-8")
    stripped = _executable_source(root / "league_ledger.py")
    assert "games_played.json" in raw, "the prose this test strips must exist"
    assert "games_played.json" not in stripped, "the stripper removed nothing"
    assert "ABSOLUTE disqualification" not in stripped
    assert "def record_league_game(" in stripped, "executable code must survive"


@pytest.mark.parametrize("name", LEDGER_MODULES)
def test_nothing_in_the_ledger_module_reads_the_shipped_counter(name):
    """D-80: `games_played.json` is never read back into the ledger. Seeding
    from it would import the exact defect the ledger replaces."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "src/pursuit/services/reporting"
    body = _executable_source(root / name)
    for forbidden in ("games_played.json", "read_games_played", "step0_collect", "counter_path"):
        assert forbidden not in body, f"{name} reaches for {forbidden}"
