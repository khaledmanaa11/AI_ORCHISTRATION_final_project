"""The two grader-facing extracts must agree on the fixed scoring values (08-03).

NEITHER NUMBER IS WRITTEN IN THIS FILE. Both pairs are parsed out of the two
documents and compared to each other, which is the only shape that can survive a
value changing: a test carrying `(5, 10)` of its own would pass while both
documents drifted together, and would have to be edited by the same hand that
broke them.

WHAT WENT WRONG, so the record does not rot. `docs/RULES.md` rule 48 read
"survival 10/5" while `docs/PARAMETERS.md` Table 17 gives cop 5 / thief 10, both
**fixed**. Rule 48's own CAPTURE pair is cop-first (20/5 against Table 17's cop 20
/ thief 5), so its survival pair had the two roles the wrong way round -- awarding
the cop more for failing to capture than the thief for surviving. 08-03 corrected
the extract, changed no fixed value, and recorded the correction with both
citations in RULES.md's "Corrections to this extract" section.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES = REPO_ROOT / "docs" / "RULES.md"
PARAMETERS = REPO_ROOT / "docs" / "PARAMETERS.md"
#: Table 17 rows 1-4, read by role label so ordering cannot be assumed.
_PARAM_ROW = re.compile(
    r"\|\s*`?\[(capture|survival) score\s*[-–]\s*(cop|thief)\]`?\s*\|[^|]*\|\s*\**(\d+)\**\s*\|"
)
#: Rule 48's two compressed pairs, in the order the rule writes them.
_RULE_48 = re.compile(r"capture\s+(\d+)\s*/\s*(\d+),\s*survival\s+(\d+)\s*/\s*(\d+)")
#: The correction record, so deleting it fails rather than going quiet.
CORRECTION_HEADING = "## Corrections to this extract"
CORRECTION_ROW = "G1-15"


def table_17() -> dict[tuple[str, str], int]:
    return {
        (scenario, role): int(value)
        for scenario, role, value in _PARAM_ROW.findall(
            PARAMETERS.read_text(encoding="utf-8")
        )
    }


def rule_48() -> tuple[int, int, int, int]:
    match = _RULE_48.search(RULES.read_text(encoding="utf-8"))
    assert match is not None, "rule 48's scoring pairs could not be parsed out of RULES.md"
    return tuple(int(group) for group in match.groups())


def test_both_documents_still_state_the_values_this_test_compares() -> None:
    """Anti-vacuity: an empty parse on either side would agree with anything."""
    table = table_17()
    for key in (("capture", "cop"), ("capture", "thief"),
                ("survival", "cop"), ("survival", "thief")):
        assert key in table, f"PARAMETERS Table 17 no longer states {key}"
    assert len(rule_48()) == len(table)


def test_rule_48_and_table_17_agree_on_the_capture_pair() -> None:
    capture_cop, capture_thief, _, _ = rule_48()
    table = table_17()
    assert (capture_cop, capture_thief) == (table["capture", "cop"], table["capture", "thief"])


def test_rule_48_and_table_17_agree_on_the_survival_pair() -> None:
    """The pair 08-03 corrected. Cop-first, exactly as the capture pair is."""
    _, _, survival_cop, survival_thief = rule_48()
    table = table_17()
    assert (survival_cop, survival_thief) == (
        table["survival", "cop"], table["survival", "thief"]
    ), "rule 48's survival pair is not cop-first, or disagrees with the fixed Table 17 values"


def test_the_correction_is_recorded_with_its_provenance() -> None:
    text = RULES.read_text(encoding="utf-8")
    assert CORRECTION_HEADING in text, "the correction record was removed from RULES.md"
    assert CORRECTION_ROW in text, "the correction no longer cites the row that found it"
    assert "PARAMETERS.md" in text and "Table 17" in text
