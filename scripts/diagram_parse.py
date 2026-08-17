"""Mermaid block extraction and well-formedness, for the Sec17 diagram rows
(08-07).

WHY A SYNTAX CHECK AND NOT JUST A PRESENCE CHECK. GitHub renders a mermaid
block with a syntax error as a red error box in place of the diagram, so an
architecture document whose blocks do not parse is worse for the grader than
one with no diagrams at all. `submission_docs._diagram_row` counts blocks; it
cannot tell a diagram from a red box. This module is the half that can.

WHAT IT DOES AND DOES NOT CLAIM. It is a structural checker, not the mermaid
parser: it verifies the fence closes, the first line names a diagram kind
mermaid knows, brackets and quotes balance OUTSIDE quoted spans, and every
`src/pursuit/...` label resolves to a tracked path. It cannot prove a diagram
is semantically valid mermaid, and it is never presented as proof of that --
the rendering check is the human one in the 08-07 SUMMARY. Its counter-control
is `tests/unit/test_diagram_parse.py`, which feeds it four separately
malformed blocks and asserts each is reported.

QUOTE-AWARE ON PURPOSE. A label like `["engine (facade)"]` is legal mermaid
precisely because it is quoted, and a naive paren count would reject it. The
scanner skips quoted spans, which is both what mermaid does and what makes the
unbalanced-paren finding meaningful when it fires.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FENCE_OPEN = re.compile(r"^```mermaid\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")
#: An HTML comment naming the diagram on the line above its fence. Markdown
#: hides it, so the document reads normally while every block keeps a stable
#: identity a test can address -- the `G1-M[path]` lesson from 08-01, where
#: position-numbered rows renumbered themselves the moment one was inserted.
MARKER = re.compile(r"^<!--\s*diagram:\s*([\w-]+)\s*-->\s*$")

#: Diagram kinds this repository's documents use, spelled as mermaid spells
#: them. An unknown kind is reported rather than assumed valid: a typo in the
#: first word is the single cheapest way to produce a red error box.
KNOWN_KINDS = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram",
    "stateDiagram-v2", "erDiagram", "gantt", "pie",
)

PAIRS = (("[", "]"), ("(", ")"), ("{", "}"))

#: A repository module path used as (part of) a node label.
MODULE_LABEL = re.compile(r"src/pursuit/[\w./]*[\w]")


@dataclass(frozen=True)
class Block:
    """One fenced mermaid block, with where it came from."""

    path: str
    start_line: int
    kind: str
    body: tuple[str, ...]
    marker: str = ""

    @property
    def where(self) -> str:
        return f"{self.path}:{self.start_line}"


def strip_quoted(line: str) -> str:
    """The line with every `"..."` span removed.

    Mermaid treats a quoted label as opaque, so brackets and parentheses inside
    one are not delimiters. Counting them would make every correctly quoted
    label look unbalanced.
    """
    return re.sub(r'"[^"]*"', "", line)


def extract_blocks(path: str, text: str) -> tuple[list[Block], list[str]]:
    """Every rendered mermaid block in *text*, plus fence-level problems.

    A block counts only when its opening fence owns the whole line -- the same
    discrimination `submission_docs._FENCE` makes, and for the same reason: a
    table cell that QUOTES ```` ```mermaid ```` is not a diagram.
    """
    blocks: list[Block] = []
    problems: list[str] = []
    lines = text.splitlines()
    index = 0
    marker = ""
    while index < len(lines):
        named = MARKER.match(lines[index])
        if named:
            marker = named.group(1)
            index += 1
            continue
        if not FENCE_OPEN.match(lines[index]):
            if lines[index].strip():
                marker = ""
            index += 1
            continue
        start = index + 1
        index += 1
        body: list[str] = []
        while index < len(lines) and not FENCE_CLOSE.match(lines[index]):
            body.append(lines[index])
            index += 1
        if index >= len(lines):
            problems.append(f"{path}:{start} mermaid fence is never closed")
            break
        kind = next((line.strip().split()[0] for line in body if line.strip()), "")
        blocks.append(Block(path, start, kind, tuple(body), marker))
        marker = ""
        index += 1
    return blocks, problems


def by_marker(blocks: list[Block]) -> dict[str, Block]:
    """Marked blocks keyed by their marker. Unmarked blocks are dropped."""
    return {block.marker: block for block in blocks if block.marker}


def _delimiter_problems(block: Block) -> list[str]:
    joined = "\n".join(strip_quoted(line) for line in block.body)
    found = []
    for opener, closer in PAIRS:
        if joined.count(opener) != joined.count(closer):
            found.append(
                f"{block.where} unbalanced {opener}{closer}: "
                f"{joined.count(opener)} vs {joined.count(closer)}"
            )
    return found


def block_problems(block: Block) -> list[str]:
    """Every structural fault in one block. Empty list means well-formed."""
    if not any(line.strip() for line in block.body):
        return [f"{block.where} empty mermaid block"]
    found = []
    if block.kind not in KNOWN_KINDS:
        found.append(f"{block.where} unknown diagram kind {block.kind!r}")
    for offset, line in enumerate(block.body):
        if line.count('"') % 2:
            found.append(f"{block.where}+{offset} odd number of quotes: {line.strip()!r}")
    return found + _delimiter_problems(block)


def module_labels(block: Block) -> tuple[str, ...]:
    """Every `src/pursuit/...` path this block names, in order, de-duplicated."""
    seen: dict[str, None] = {}
    for line in block.body:
        for hit in MODULE_LABEL.findall(line):
            seen.setdefault(hit, None)
    return tuple(seen)
