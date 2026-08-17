"""The root README judged against Sec2.1's SEVEN items, one row each (08-01).

THE TRAP THIS FILE EXISTS TO DEFEAT: `[ -f README.md ] && echo PASS`. Sec17's
bar for the root README is Sec2.1's user-manual standard -- installation,
usage, examples/screenshots, configuration, contribution, licence, credits --
and the README in this tree would sail through an existence check while missing
most of them. Seven items, seven rows, seven independent failures.

AND TWO HONESTY ROWS, because rule 42 governs this file -- both derived, and
both living in `submission_readme_honesty.py` since this file crossed 150 code
lines. The seam: everything here asks whether the README is COMPLETE, everything
there asks whether it is TRUE.
"""

from __future__ import annotations

import re

from submission_common import GROUP_1, judge, read_tracked
from submission_readme_honesty import honesty_rows

README = "README.md"
#: A section carrying fewer than this many non-blank body lines is a stub.
MIN_SECTION_LINES = 3

#: Sec2.1's seven items: (id, requirement, heading terms, terms the body must carry).
SECTION_ITEMS = (
    ("G1-01", "Sec2.1 installation: prerequisites, step-by-step, env setup, troubleshooting",
     ("install", "prerequisit", "getting started", "setup"), ("prerequisit", "troubleshoot")),
    ("G1-02", "Sec2.1 usage: running in different modes, flags, CLI/GUI, typical workflow",
     ("usage", "running", "how to run", "quick start"), ("flag",)),
    ("G1-03", "Sec2.1 examples and code samples, screenshots, common use-cases",
     ("example", "screenshot", "demo", "use case"), ()),
    ("G1-04", "Sec2.1 configuration guide",
     ("configuration",), ()),
    ("G1-05", "Sec2.1 contribution guidelines",
     ("contribut",), ()),
    ("G1-06", "Sec2.1 license",
     ("license", "licence"), ()),
    ("G1-07", "Sec2.1 credits",
     ("credit", "acknowledg", "authors"), ()),
)

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_CURVE_DIR = "artifacts/curves/"


def _sections(text: str) -> dict[str, list[str]]:
    """Every heading mapped to its body lines, up to the next same-or-higher heading."""
    sections: dict[str, list[str]] = {}
    current, level = None, 0
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            new_level = len(match.group(1))
            if current is not None and new_level <= level:
                current = None
            current, level = match.group(2).strip().lower(), new_level
            sections.setdefault(current, [])
            continue
        if current is not None and line.strip():
            sections[current].append(line)
    return sections


def _find(sections: dict[str, list[str]], terms: tuple[str, ...]) -> tuple[str, list[str]]:
    for heading, body in sections.items():
        if any(term in heading for term in terms):
            return heading, body
    return "", []


def _section_row(item: tuple, sections: dict[str, list[str]]) -> object:
    item_id, requirement, heading_terms, must_contain = item
    heading, body = _find(sections, heading_terms)
    if not heading:
        return judge(item_id, GROUP_1, requirement, False,
                     f"no README heading matches any of {list(heading_terms)}", README)
    blob = "\n".join(body).lower()
    missing = [term for term in must_contain if term not in blob]
    ok = len(body) >= MIN_SECTION_LINES and not missing
    detail = f"heading '{heading}' has {len(body)} body lines"
    if missing:
        detail += f"; body never mentions {missing}"
    return judge(item_id, GROUP_1, requirement, ok, detail, README)


def _screenshot_row(text: str) -> object:
    """G1-03's second half: an image that is NOT one of the training curves.

    A learning curve is required by rule 42 and satisfies Sec9.4.2 item 4; it is
    not a screenshot, and counting it as one would close this row with evidence
    that answers a different question.
    """
    images = _IMAGE.findall(text)
    non_curve = [src for src in images if _CURVE_DIR not in src]
    has_code = "```" in text
    return judge(
        "G1-03b", GROUP_1,
        "Sec2.1 examples: at least one fenced code sample AND one non-curve screenshot",
        bool(has_code and non_curve),
        f"fenced code blocks present: {has_code}; images: {len(images)}, "
        f"of which non-curve: {len(non_curve)}",
        README,
    )


def readme_items() -> list:
    """Every README row. Non-empty by construction -- see `submission_report`."""
    text = read_tracked(README)
    if not text:
        return [judge("G1-00", GROUP_1, "Sec2.1 root README exists and is tracked",
                      False, "README.md is absent or untracked", README)]
    sections = _sections(text)
    rows = [_section_row(item, sections) for item in SECTION_ITEMS]
    rows.append(_screenshot_row(text))
    rows.extend(honesty_rows(text))
    return rows
