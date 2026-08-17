"""The two rule-42 honesty rows for the root README (08-01).

Split out of `submission_readme.py` when that file crossed 150 code lines --
SPLIT, never compressed (Segal Sec3). The seam is real rather than arbitrary:
everything here answers "is the README TRUE", everything left behind answers "is
the README COMPLETE", and only these two rows read evidence from outside the
README itself.

BOTH ROWS DERIVE THEIR OWN SUBJECT, and both refuse to pass over an empty
derivation.

* A mechanism whose `docs/PRD_*.md` carries a SUPERSEDED banner must not be
  advertised as what ships. The terms come out of the superseded PRD's own H1;
  if no PRD is superseded there is nothing to compare and the row is UNJUDGED,
  because deleting a banner must not be a way to turn this row green.
* A phase whose `NN-VERIFICATION.md` reads `status: passed` must not be
  described as "in progress". Same shape: no verification files, no judgement.
"""

from __future__ import annotations

import re

from submission_common import (
    GROUP_1,
    REPO_ROOT,
    judge,
    read_tracked,
    tracked_matching,
    unjudged,
)

README = "README.md"
#: Words that qualify a mention as historical rather than as a claim about today.
QUALIFIERS = ("supersede", "withdraw", "replaced")


def superseded_terms() -> dict[str, list[str]]:
    """Parenthesised, hyphenated title terms of every SUPERSEDED per-mechanism PRD.

    `# PRD - RL Strategy Module (Q-Learning Policy)` yields `Q-Learning`. The
    hyphen filter is what keeps ordinary words like "Policy" out: a bare noun
    would match half the README and the row would fire on prose.
    """
    found: dict[str, list[str]] = {}
    for path in tracked_matching(prefix="docs/PRD_", suffix=".md"):
        text = read_tracked(path)
        if "SUPERSEDED" not in text:
            continue
        head = next((line for line in text.splitlines() if line.startswith("# ")), "")
        inner = re.findall(r"\(([^)]*)\)", head)
        terms = [word for chunk in inner for word in chunk.split()
                 if "-" in word and len(word) > 3]
        if terms:
            found[path] = terms
    return found


def superseded_row(text: str) -> object:
    """G1-08 -- the README's opening claim about the shipped strategy."""
    superseded = superseded_terms()
    if not superseded:
        return unjudged(
            "G1-08", GROUP_1, "README must not advertise a superseded mechanism",
            "no tracked docs/PRD_*.md carries a SUPERSEDED banner -- nothing to compare",
        )
    offenders = [
        f"{term} ({path})"
        for path, terms in superseded.items() for term in terms
        for line in text.lower().splitlines()
        if term.lower() in line and not any(word in line for word in QUALIFIERS)
    ]
    return judge(
        "G1-08", GROUP_1, "README must not advertise a superseded mechanism (rule 42)",
        not offenders,
        f"{len(offenders)} unqualified mention(s) of a superseded mechanism: "
        f"{sorted(set(offenders))[:4]}",
        README,
    )


def _verified_phases() -> list[str]:
    numbers = []
    for path in sorted((REPO_ROOT / ".planning" / "phases").glob("*/0?-VERIFICATION.md")):
        if "status: passed" in path.read_text(encoding="utf-8", errors="replace"):
            numbers.append(path.name[:2])
    return numbers


def phase_status_row(text: str) -> object:
    """G1-09 -- the README's status table against the verification files."""
    passed = _verified_phases()
    if not passed:
        return unjudged("G1-09", GROUP_1,
                        "README phase status matches the verification files",
                        "no NN-VERIFICATION.md reads `status: passed` -- nothing to compare")
    stale = [
        number for number in passed
        for line in text.splitlines()
        if line.strip().startswith(f"| {int(number)} ") and "in progress" in line.lower()
    ]
    return judge(
        "G1-09", GROUP_1, "README phase status matches the verification files (rule 42)",
        not stale,
        f"phases verified `passed`: {passed}; still shown 'in progress' in "
        f"README: {stale}",
        README,
    )


def honesty_rows(text: str) -> list:
    """Both rule-42 rows, in id order."""
    return [superseded_row(text), phase_status_row(text)]
