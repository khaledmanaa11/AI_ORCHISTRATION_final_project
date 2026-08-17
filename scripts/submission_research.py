"""Sec17 groups 5 and 6 -- research/visualization and extensibility/standards
(08-01).

THE ISO/IEC 25010 ROW DERIVES ITS OWN CHECKLIST. The eight characteristic names
are parsed out of `docs/SEGAL_GUIDELINES.md` Sec13, not typed in here, and the
row passes only when some OTHER tracked document names all eight. Naming the
eight characteristics is not the requirement; MAPPING each to repo evidence is,
so the row additionally refuses a document that lists them and cites nothing.
When the parse yields anything other than eight names the row is a GAP with the
parse failure quoted -- it never falls through to a pass over an empty list.

THE SCREENSHOT ROW REFUSES TO COUNT A LEARNING CURVE. `artifacts/curves/*.png`
are required by rule 42 and satisfy Sec9.4.2 item 4; they are not screenshots of
a running system, and closing "quality graphs, screenshots" with them would
answer a question nobody asked.
"""

from __future__ import annotations

import re

from submission_common import (
    GROUP_5,
    GROUP_6,
    judge,
    read_tracked,
    run,
    tracked_files,
    tracked_matching,
    unjudged,
)

CURVE_DIR = "artifacts/curves/"
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg")
#: Documents Sec17 names by function; the paths this project has chosen for them.
SENSITIVITY = "docs/SENSITIVITY.md"
TOKEN_COST = "docs/TOKEN-COST.md"
EXTENSION_POINTS = "docs/EXTENSION-POINTS.md"
QUALITY_MODEL = "docs/QUALITY-25010.md"
DEPLOYMENT = "docs/ARCHITECTURE.md"
LICENSE = "LICENSE"
#: Conventional-commit prefixes this repo has used since phase 1.
_COMMIT = re.compile(r"^[0-9a-f]+ (feat|fix|test|refactor|chore|docs|plan|perf)[(:]")
#: How many recent commits the git-history row reads.
HISTORY_SAMPLE = 200
#: The share of the sample that must be conventional for the history to be orderly.
HISTORY_FLOOR = 0.9


def _doc_row(item_id: str, group: str, requirement: str, path: str, floor: int = 20) -> object:
    lines = [line for line in read_tracked(path).splitlines() if line.strip()]
    return judge(item_id, group, requirement, len(lines) >= floor,
                 f"{path} tracked with {len(lines)} non-blank lines (floor {floor})", path)


def _experiments_row() -> object:
    curves = tracked_matching(prefix=CURVE_DIR)
    return judge(
        "G5-01", GROUP_5, "Sec17 systematic experiments with recorded results",
        len(curves) > 1,
        f"tracked artifacts under {CURVE_DIR}: {len(curves)} {list(curves)}",
        CURVE_DIR,
    )


def _notebook_row() -> object:
    books = tracked_matching(suffix=".ipynb")
    return judge(
        "G5-03", GROUP_5, "Sec17 / Sec2.4 analysis notebook with graphs",
        bool(books),
        f"tracked *.ipynb files: {len(books)} {list(books)}",
        "notebooks/analysis.ipynb",
    )


def _screenshot_row() -> object:
    images = [path for path in tracked_files() if path.endswith(IMAGE_SUFFIXES)]
    non_curve = [path for path in images if not path.startswith(CURVE_DIR)]
    return judge(
        "G5-04", GROUP_5, "Sec17 quality graphs AND screenshots of the running system",
        bool(non_curve),
        f"tracked images: {len(images)}; of which not a training curve: "
        f"{len(non_curve)} {non_curve[:4]}",
        "docs/assets/",
    )


def _iso_characteristics() -> list[str]:
    """The eight names, parsed out of the Sec13 extract rather than typed here."""
    text = read_tracked("docs/SEGAL_GUIDELINES.md")
    match = re.search(r"eight characteristics:(.+?)\.", text, re.DOTALL)
    if not match:
        return []
    return [part.strip().lower() for part in match.group(1).split("·") if part.strip()]


def _iso_row() -> object:
    names = _iso_characteristics()
    if len(names) != 8:
        return judge("G6-05", GROUP_6, "Sec13 / Sec17 ISO/IEC 25010 compliance mapped",
                     False,
                     f"could not parse eight characteristics out of Sec13 -- got "
                     f"{len(names)}: {names}", QUALITY_MODEL)
    candidates = [
        path for path in tracked_matching(prefix="docs/", suffix=".md")
        if path != "docs/SEGAL_GUIDELINES.md"
    ]
    mapped = [
        path for path in candidates
        if all(name in (body := read_tracked(path).lower()) for name in names)
        and body.count("src/") + body.count("tests/") + body.count("config/") >= len(names)
    ]
    return judge(
        "G6-05", GROUP_6,
        "Sec13 / Sec17 ISO/IEC 25010 -- all eight characteristics mapped to repo evidence",
        bool(mapped),
        f"characteristics parsed from Sec13: {names}; tracked docs naming all eight "
        f"AND citing at least eight repo paths: {mapped or 'none'}",
        QUALITY_MODEL,
    )


def _history_row() -> object:
    code, output = run(["git", "log", f"-{HISTORY_SAMPLE}", "--oneline"])
    lines = [line for line in output.splitlines() if line.strip()]
    good = [line for line in lines if _COMMIT.match(line)]
    ratio = len(good) / len(lines) if lines else 0.0
    return judge(
        "G6-06", GROUP_6, "Sec17 orderly Git history",
        code == 0 and bool(lines) and ratio >= HISTORY_FLOOR,
        f"last {len(lines)} commits read; conventional-prefix share {ratio:.2%} "
        f"(floor {HISTORY_FLOOR:.0%})",
        "",
    )


def _tag_row() -> object:
    code, output = run(["git", "tag", "-l"])
    tags = [line for line in output.splitlines() if line.strip()]
    return judge(
        "G6-08", GROUP_6, "rule 41 / Sec17 the submitted version carries a Git tag",
        code == 0 and bool(tags),
        f"`git tag -l` exit {code}; tags: {tags or 'none'} "
        f"(cut in 08-11, PUSHED BY A HUMAN in 08-12 -- never by this gate)",
        "docs/phases/phase-8/SUBMISSION-RUNBOOK.md",
    )


def research_items() -> list:
    """Groups 5 and 6. Two rows stay UNJUDGED for the reasons written into them."""
    return [
        _experiments_row(),
        _doc_row("G5-02", GROUP_5, "Sec17 documented sensitivity analysis", SENSITIVITY),
        _notebook_row(),
        _screenshot_row(),
        _doc_row("G5-05", GROUP_5,
                 "Sec17 token-cost analysis and optimization strategy", TOKEN_COST),
        _doc_row("G6-01", GROUP_6, "Sec17 documented extension points", EXTENSION_POINTS),
        _doc_row("G6-02", GROUP_6,
                 "Sec17 deployment instructions and architecture documentation", DEPLOYMENT),
        _doc_row("G6-03", GROUP_6, "Sec17 licence file at the repo root", LICENSE, floor=1),
        _iso_row(),
        _history_row(),
        unjudged("G6-04", GROUP_6, "Sec15 parallel processing with thread safety",
                 "the code is asyncio-concurrent and `docs/PLAN.md` Sec7 records the "
                 "guidance; whether a given shared structure is safe is a review "
                 "judgement no path check can make"),
        _tag_row(),
        unjudged("G6-07", GROUP_6, "Sec17 building-block design",
                 "the 150-line gate (G2-03) enforces the mechanical half; whether the "
                 "resulting blocks are the RIGHT ones is a review judgement"),
    ]
