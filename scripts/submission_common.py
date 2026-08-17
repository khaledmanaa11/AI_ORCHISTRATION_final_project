"""Shared vocabulary for the Sec17 + Table-5 submission audit (08-01).

THE AUDIT IS A GATE, NOT A DOCUMENT. A prose checklist cannot fail; this one
exits 0 when every judged item passes, 1 when any item is a GAP, and 2 when the
evidence set judged NOTHING. That third state is `measure_gate7.py`'s contract
(`gate7_report.GateExit`) and it exists because three separate gates in this
project have now been caught reporting OK for having looked at nothing.

THREE VERDICTS, AND `UNJUDGED` IS NOT A PASS. Sec17 names items no script can
see -- "TDD, tests written before/with the code", "OOP with no duplication".
Scoring those PASS because a file exists is the exact dishonesty the gate is
built to refuse, so they are printed as UNJUDGED, counted separately, and never
folded into the pass count.

EVERY EVIDENCE READ GOES THROUGH THE TRACKED SET. `git ls-files` is the
publishable surface; a directory walk sees `.env`, `police_thief_p2p.pdf` and
`.venv/`, none of which a grader will ever receive.

`scripts/` is scanned by NEITHER the 150-line gate (`check_line_limit.sh:18`
enumerates `src/** tests/** training/**`) NOR coverage (`pyproject.toml`
`source = ["src", "training"]`), so every file here is split by hand and checked
EXPLICITLY BY PATH, exactly as the `gate7_*.py` siblings were.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PASS = "PASS"
GAP = "GAP"
UNJUDGED = "UNJUDGED"

#: Sec17's six groups, verbatim from `docs/SEGAL_GUIDELINES.md:301-325`.
GROUP_1 = "1. Structure & documentation"
GROUP_2 = "2. Architecture & code"
GROUP_3 = "3. Testing & quality"
GROUP_4 = "4. Configuration & security"
GROUP_5 = "5. Research & visualization"
GROUP_6 = "6. Extensibility & standards"
GROUP_T5 = "T5. Table 5 (Sec19.1)"

ALL_GROUPS = (GROUP_1, GROUP_2, GROUP_3, GROUP_4, GROUP_5, GROUP_6, GROUP_T5)


class SubmissionExit(IntEnum):
    """Process exit codes -- structural, never a game parameter."""

    OK = 0
    GAPS_FOUND = 1
    EMPTY_EVIDENCE = 2


@dataclass(frozen=True)
class Item:
    """One Sec17 / Table-5 row and the measurement behind its verdict.

    `fix_path` is mandatory on a GAP and is the whole point of the register:
    a gap row that does not say WHERE the fix lands is a complaint, not a task.
    """

    item_id: str
    group: str
    requirement: str
    verdict: str
    evidence: str
    fix_path: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.item_id,
            "group": self.group,
            "requirement": self.requirement,
            "verdict": self.verdict,
            "evidence": self.evidence,
            "fix_path": self.fix_path,
        }


def judge(item_id: str, group: str, requirement: str, ok: bool, evidence: str,
          fix_path: str) -> Item:
    """PASS/GAP from one measured boolean. `fix_path` is carried on both so a
    row that later flips to GAP already knows where its repair belongs."""
    return Item(item_id, group, requirement, PASS if ok else GAP, evidence, fix_path)


def unjudged(item_id: str, group: str, requirement: str, why: str) -> Item:
    """A Sec17 item no script can see. Never PASS -- see the module docstring."""
    return Item(item_id, group, requirement, UNJUDGED, why, "")


@lru_cache(maxsize=1)
def tracked_files() -> tuple[str, ...]:
    """Every path `git ls-files` reports, POSIX-separated, sorted.

    Cached: the audit asks this question from roughly forty judges and the
    answer cannot change inside one run.
    """
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return tuple(sorted(line for line in out.stdout.splitlines() if line.strip()))


def is_tracked(relative_path: str) -> bool:
    """Tracked, not merely present. An untracked file cannot reach a grader."""
    return relative_path.replace("\\", "/") in tracked_files()


def tracked_matching(suffix: str = "", prefix: str = "") -> tuple[str, ...]:
    """Tracked paths filtered by prefix and/or suffix -- the inventory helper."""
    return tuple(
        path for path in tracked_files()
        if path.startswith(prefix) and path.endswith(suffix)
    )


def read_tracked(relative_path: str) -> str:
    """Text of a tracked file, or "" when it is absent or untracked."""
    if not is_tracked(relative_path):
        return ""
    target = REPO_ROOT / relative_path
    if not target.is_file():
        return ""
    return target.read_text(encoding="utf-8", errors="replace")


def run(command: list[str], timeout: int = 900) -> tuple[int, str]:
    """A subprocess's exit code and combined output, never raising on failure."""
    try:
        done = subprocess.run(
            command, cwd=REPO_ROOT, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - env dependent
        return 127, f"{type(exc).__name__}: {exc}"
    return done.returncode, (done.stdout or "") + (done.stderr or "")
