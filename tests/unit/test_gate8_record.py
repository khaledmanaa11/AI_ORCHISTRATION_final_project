"""`GATE-8-MEASUREMENT.md` may not drift from what was measured (08-11).

The gate record is the document a grader reads instead of running anything, so
the two failure modes worth testing are **drift** and **overstatement**:

* **drift** -- the three criterion verdict STRINGS are read out of
  `gate8_measurement_evidence.json` and required to appear verbatim in the
  document. Re-running the measurement and hand-editing the prose to something
  friendlier fails here.
* **overstatement** -- the record must say GATE-8 is not met, must carry a
  PENDING for each human-completed half, and must name who closes each one.
  07-09 refused a gate that reported PASS on the strength of preparation; this
  test is that refusal made mechanical.
"""

from __future__ import annotations

import json
import re

from tests.unit.doc_citation_helpers import cited_paths, unresolved_citations
from tests.unit.submission_gate_helpers import load
from tests.unit.test_phase8_runbooks import LOCAL_ONLY_PATHS

common = load("submission_common")

DOC = "docs/phases/phase-8/GATE-8-MEASUREMENT.md"
EVIDENCE = "docs/phases/phase-8/gate8_measurement_evidence.json"
CRITERIA = (
    "criterion_1_two_cross_linked_repos_and_a_tag",
    "criterion_2_academic_readme_and_submission_form",
    "criterion_3_two_scored_league_games",
)
#: Every plan (or phase plan) that owns a half this gate cannot close.
PENDING_OWNERS = ("07-10", "08-12", "08-13", "08-14")
#: A status line that OPENS with a pass. Deliberately narrow: the first draft
#: matched `.{0,40}PASS` and fired on this record's own honest header --
#: "**Status: GATE-8 IS NOT MET**, and nothing reads PASS" -- which would have
#: made the assertion impossible to satisfy honestly, the mirror image of a
#: check that is impossible to fail.
_OVERALL_PASS = re.compile(r"\*\*Status:\*{0,2}\s*(?:GATE-8\s+)?(?:IS\s+)?PASS\b", re.IGNORECASE)


def _text() -> str:
    return common.read_tracked(DOC)


def _verdicts() -> dict[str, str]:
    report = json.loads(common.read_tracked(EVIDENCE))
    return {key: report[key]["verdict"] for key in CRITERIA}


def test_the_record_and_the_evidence_json_are_both_tracked() -> None:
    assert len(_text()) > 3000, DOC
    assert len(_verdicts()) == 3


def test_every_measured_verdict_string_appears_verbatim_in_the_record() -> None:
    """The anti-drift check. Hand-editing the prose fails; re-running fixes it."""
    text = _text()
    missing = {key: value for key, value in _verdicts().items() if value not in text}
    assert not missing, f"the record does not carry the measured verdict(s): {missing}"


def test_the_verdict_strings_are_two_halves_and_not_a_bare_pass() -> None:
    """A criterion whose verdict is the single word PASS would defeat the test above."""
    bare = {key: value for key, value in _verdicts().items() if value.strip() == "PASS"}
    assert not bare, f"criterion reported as a blanket PASS: {bare}"
    assert all("PENDING" in value for value in _verdicts().values())


def test_the_record_says_the_gate_is_not_met() -> None:
    assert "GATE-8 IS NOT MET" in _text()
    assert not _OVERALL_PASS.search(_text()), "the record opens with a PASS status"


def test_the_pending_detector_would_notice_a_softened_status() -> None:
    """Control for the regex above, both directions."""
    assert _OVERALL_PASS.search("**Status:** GATE-8 PASS -- everything prepared")
    assert _OVERALL_PASS.search("**Status:** PASS")
    assert not _OVERALL_PASS.search("**Status: GATE-8 IS NOT MET**, and nothing reads PASS")


def test_every_human_owner_is_named() -> None:
    text = _text()
    missing = [owner for owner in PENDING_OWNERS if owner not in text]
    assert not missing, f"PENDING halves with no owner named: {missing}"
    assert text.count("PENDING") >= 8, text.count("PENDING")


def test_every_path_the_record_cites_resolves() -> None:
    """The two gitignored counters are exempt by the same named list the runbooks use."""
    broken = [path for path in unresolved_citations(DOC) if path not in LOCAL_ONLY_PATHS]
    assert broken == [], broken
    assert len(cited_paths(DOC)) >= 10, cited_paths(DOC)
