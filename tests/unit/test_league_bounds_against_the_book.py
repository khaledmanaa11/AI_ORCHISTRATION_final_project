"""The ledger's two FIXED bounds, checked against `docs/PARAMETERS.md` itself.

WHY THIS FILE EXISTS, AND IT IS NOT BELT-AND-BRACES. `test_league_ledger.py`
proves the tenth game is recorded and the eleventh refused -- but it builds its
loop from `MAX_GAMES_PER_TEAM`, so it moves WITH the constant. Probe E of this
plan set the constant to 11 and the whole ledger suite stayed green: the bound
was enforced, and its VALUE was unasserted. Table 18 row 5 is status **fixed**,
and CLAUDE.md's first prohibition makes any deviation from a fixed value a
disqualification, so the value needs a control that does not move with it.

The control reads the BOOK, not a literal transcribed from it. A test asserting
`MAX_GAMES_PER_TEAM == 10` would only prove that two copies of one number
agree; this one proves the constant equals what `docs/PARAMETERS.md` says, and
fails if either side moves.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pursuit.services.reporting.league_ledger import MAX_GAMES_PER_TEAM, MINIMUM_GAMES

PARAMETERS = Path(__file__).resolve().parents[2] / "docs/PARAMETERS.md"

#: `| 5 | `[max games per team]` | Max games any one team may play | **10** | **fixed** |`
_ROW = r"\|\s*\d+\s*\|\s*`\[{name}\]`\s*\|[^|]*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*(\w+)\*\*\s*\|"


def _book_row(name: str) -> tuple[int, str]:
    match = re.search(_ROW.format(name=re.escape(name)), PARAMETERS.read_text(encoding="utf-8"))
    assert match is not None, f"docs/PARAMETERS.md has no bolded row for [{name}]"
    return int(match.group(1)), match.group(2)


@pytest.mark.parametrize(
    ("name", "constant"),
    [("max games per team", MAX_GAMES_PER_TEAM), ("minimum games", MINIMUM_GAMES)],
)
def test_the_constant_equals_the_books_value_and_the_book_calls_it_fixed(name, constant):
    value, status = _book_row(name)
    assert status == "fixed", f"[{name}] is no longer fixed in docs/PARAMETERS.md"
    assert constant == value, f"[{name}] is {value} in the book and {constant} in the code"


def test_the_row_parser_would_notice_a_changed_book_value():
    """The control on the control: a parser that matched nothing would make
    both assertions above vacuous, so prove it reads real digits."""
    assert _book_row("max games per team") == (10, "fixed")
    assert _book_row("minimum games") == (2, "fixed")
    with pytest.raises(AssertionError, match="no bolded row"):
        _book_row("a parameter the book does not have")
