"""Rule 55 applied to `docs/SELF-ASSESSMENT.md` (08-11).

Rule 55 restricts the self-assessment to **code quality only** and forbids
crediting league game results. That is a property of the document's *content*,
so it is checkable, and it is checked here rather than trusted.

The second property is the one an agent could break most easily: **the score
field must stay blank.** OQ8-4 is the owner's to answer at 08-14. A test that
fails the moment a number appears is cheaper than remembering not to write one.

Every check has a control that fires it on text deserving a violation.
"""

from __future__ import annotations

import re

from tests.unit.doc_citation_helpers import cited_paths, unresolved_citations
from tests.unit.submission_gate_helpers import load

common = load("submission_common")

DOC = "docs/SELF-ASSESSMENT.md"
#: Words that would make a code-quality assessment a league-performance claim.
LEAGUE_WORDS = ("win rate", "we won", "points scored", "league table", "our placing",
                "beat the", "victories")
#: `Score: 87 / 100` in any of the shapes a filled field takes.
_FILLED_SCORE = re.compile(r"Score:\s*\**\s*\d")
_BLANK_SCORE = re.compile(r"Score:\s*_{3,}")


def _text() -> str:
    return common.read_tracked(DOC)


def test_the_document_is_tracked_and_substantial() -> None:
    assert len(_text()) > 2000, "SELF-ASSESSMENT.md is missing, untracked or a stub"


def test_the_score_field_is_blank() -> None:
    text = _text()
    assert _BLANK_SCORE.search(text), "the blank score field is gone"
    assert not _FILLED_SCORE.search(text), (
        "a score has been written into SELF-ASSESSMENT.md. OQ8-4 is the owner's "
        "at 08-14; no agent may set it."
    )


def test_the_score_detectors_actually_discriminate() -> None:
    """The control. Both patterns fired, on text that deserves each."""
    assert _FILLED_SCORE.search("### Score: 87 / 100")
    assert _FILLED_SCORE.search("Score: **92** / 100")
    assert not _FILLED_SCORE.search("### Score: ______ / 100")
    assert _BLANK_SCORE.search("### Score: ______ / 100")
    assert not _BLANK_SCORE.search("### Score: 87 / 100")


def test_it_credits_no_league_result() -> None:
    lowered = _text().lower()
    found = [word for word in LEAGUE_WORDS if word in lowered]
    assert not found, f"rule 55 violation -- league-performance language present: {found}"
    assert len(LEAGUE_WORDS) == 7


def test_it_names_the_open_question_and_the_plan_that_answers_it() -> None:
    text = _text()
    for token in ("OQ8-4", "08-14", "rule 55"):
        assert token in text or token.upper() in text.upper(), token


def test_every_path_it_cites_resolves() -> None:
    assert unresolved_citations(DOC) == []
    assert len(cited_paths(DOC)) >= 8, cited_paths(DOC)
