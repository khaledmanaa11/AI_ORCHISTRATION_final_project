"""Derived checks over the root README's TEXT (08-06).

Every function takes the README text and RETURNS the violations it found, so
the same check can be run against `git show HEAD:README.md` to prove it goes
red on the pre-rewrite file. A checker that cannot fail is not evidence.

Each check derives its own subject from the repository -- the shipped mail
mode, the shipped brain, the verification files that do or do not exist -- so
it cannot be satisfied by editing a keyword into the wrong part of the README,
and it tracks the tree instead of freezing today's prose.
"""

from __future__ import annotations

import json
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Sec2.1's seven user-manual items -> a heading substring each.
SEGAL_21_HEADINGS = (
    ("installation", "install"),
    ("usage", "usage"),
    ("examples/screenshots", "example"),
    ("configuration guide", "configuration"),
    ("contribution guidelines", "contribut"),
    ("licence", "licen"),
    ("credits", "credit"),
)

#: Sec9.4.2's six academic-report sections -> a heading substring each.
ACADEMIC_942_HEADINGS = (
    ("1 Dec-POMDP model", "dec-pomdp"),
    ("2 orchestration dilemmas", "orchestration dilemma"),
    ("3 the chosen strategy", "strategy"),
    ("4 learning curves", "learning curve"),
    ("5 screenshots", "screenshot"),
    ("6 companion repo link", "companion repo"),
)

_HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
_FENCE = re.compile(r"```.*?```", re.DOTALL)
_REPO_PATH = re.compile(r"(?:scripts|training|src|tests|config)/[\w./-]+\.(?:py|sh|json)")


def headings(text: str) -> list[str]:
    return [match.strip().lower() for match in _HEADING.findall(text)]


def missing_headings(text: str, table: tuple) -> list[str]:
    """Items from `table` with no heading carrying their substring."""
    found = headings(text)
    return [label for label, term in table
            if not any(term in heading for heading in found)]


def broken_relative_links(text: str) -> list[str]:
    """Every non-external link and image target that resolves to nothing.

    This is what keeps an absent screenshot an absent SLOT: the moment someone
    writes `![...](docs/assets/x.png)` before the file exists, this fires.
    """
    broken = []
    for target in _LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#", "<")):
            continue
        path = target.split("#", 1)[0]
        if path and not (REPO_ROOT / path).exists():
            broken.append(target)
    return broken


def commands_naming_absent_paths(text: str) -> list[str]:
    """Repo paths quoted inside fenced command blocks that do not exist.

    The pre-rewrite README documented `training/plot_curves.py`, deleted with
    the rest of the run-1 stack -- a documented command a reader cannot run.
    """
    absent = []
    for block in _FENCE.findall(text):
        for token in _REPO_PATH.findall(block):
            if "<" in token or (REPO_ROOT / token).exists():
                continue
            absent.append(token)
    return sorted(set(absent))


def shipped_mail_modes() -> set[str]:
    """`reporting.mode` from every shipped per-role config."""
    return {
        json.loads(path.read_text(encoding="utf-8"))["reporting"]["mode"]
        for path in sorted(REPO_ROOT.glob("config/*/reporting.json"))
    }


def mail_honesty_violations(text: str) -> list[str]:
    """While every shipped config is `dry_run`, the README must say so.

    Silence here is the overstatement: a reader who is told the mail path
    exists and not told nothing has ever been delivered has been misled.
    """
    if shipped_mail_modes() != {"dry_run"}:
        return []
    lowered = text.lower()
    return [term for term in ("dry_run", "pending") if term not in lowered]


def unverified_phases() -> list[int]:
    """Phases with NO `NN-VERIFICATION.md` anywhere under `.planning/phases/`."""
    present = {
        int(path.name[:2])
        for path in (REPO_ROOT / ".planning" / "phases").glob("*/0?-VERIFICATION.md")
    }
    return [number for number in range(1, 9) if number not in present]


def phase_status_violations(text: str) -> list[str]:
    """A phase with no verification document must not read as verified."""
    violations = []
    for number in unverified_phases():
        rows = [line.strip() for line in text.splitlines()
                if line.strip().startswith(f"| {number} ")]
        if not rows:
            violations.append(f"phase {number}: no status row in the README")
        elif not any("not verified" in row.lower() for row in rows):
            violations.append(f"phase {number}: row does not say it is not verified")
    return violations


def shipped_brain_modules() -> list[str]:
    """The module that defines each brain name the shipped configs select."""
    names = set()
    for path in sorted(REPO_ROOT.glob("config/*/strategy.json")):
        block = json.loads(path.read_text(encoding="utf-8"))
        block = block.get("strategy", block)
        names.update(str(value) for key, value in block.items() if key.endswith("_class"))
    modules = set()
    for source in sorted((REPO_ROOT / "src" / "pursuit" / "strategy").glob("*.py")):
        body = source.read_text(encoding="utf-8")
        if any(f'"{name}"' in body or f"'{name}'" in body for name in names):
            modules.add(f"strategy/{source.name}")
    return sorted(modules)


def unnamed_shipped_brain(text: str) -> list[str]:
    """The README must name the module the shipped configuration actually uses."""
    return [module for module in shipped_brain_modules() if module not in text]


def counter_values() -> list[tuple[str, str]]:
    """`(role, value)` for every shipped counter that EXISTS in this tree.

    EMPTY IN EVERY PUBLISHED COPY, AND THAT HAS TO BE SAID OUT LOUD.
    `config/*/games_played.json` is gitignored live state (D-77): a fresh clone,
    a CI checkout and both split repositories have none. `games_played_leaks`
    then has nothing to search for and returns `[]` -- which means "nothing to
    compare", NOT "no leak found". Until 08-10 that distinction was invisible,
    so the CI job standing guard over an absolute-disqualification rule was
    standing guard over an empty list.
    """
    return [
        (path.parent.name,
         str(json.loads(path.read_text(encoding="utf-8"))["games_played"]))
        for path in sorted(REPO_ROOT.glob("config/*/games_played.json"))
    ]


def games_played_leaks(text: str, values=None) -> list[str]:
    """Rule 38: no counter value may be restated in this file as a claim.

    `values` is injectable so the DETECTOR can be proven on a machine that has
    no counters -- which is every machine except a developer's.
    """
    pairs = counter_values() if values is None else list(values)
    return [
        f"{role}: {value}" for role, value in pairs
        if re.search(rf"(?<!\d){re.escape(value)}(?!\d)", text)
    ]
