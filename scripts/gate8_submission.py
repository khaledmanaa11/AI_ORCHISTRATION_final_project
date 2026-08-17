"""GATE-8 criteria 2 and 3 -- the README/form half and the league half (08-11).

> 2. Academic README with its six mandatory sections (incl. learning curves and
>    `Verified OK` screenshots); submission form filled and saved as PDF,
>    submitted per team member
> 3. At least 2 scored league games played against different teams and reported,
>    each game emailing the commit hash it ran on

NEITHER CRITERION CAN CLOSE HERE, AND NEITHER IS WRITTEN AS THOUGH IT MIGHT.
Criterion 2's form is a PDF whose location is not recorded anywhere (OQ8-3) and
whose per-member submission is an outward act; criterion 3 needs real opponent
teams. What IS measured is everything underneath them: the six section headings
in the tree that will be published, the screenshot slots that are still empty,
the ledger's derived count against the Table-18 bounds, and the fact that the
declaration artifact -- the thing that carries the commit hash onto the wire --
now has a production caller.

THE HEADING TABLE IS IMPORTED, NEVER RETYPED. `tests/unit/readme_contract_checks`
owns Sec9.4.2's six section names; a second copy here could pass while the README
contract failed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from gate8_common import REPO_ROOT, ROLES, split_root

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pursuit.services.reporting.league_ledger import read_ledger  # noqa: E402
from pursuit.services.reporting.league_ledger_fields import (  # noqa: E402
    MAX_GAMES_PER_TEAM,
    MINIMUM_GAMES,
    count_reading,
    scored_opponents,
)
from tests.unit import readme_contract_checks as checks  # noqa: E402

DECLARATION_EVIDENCE = REPO_ROOT / "docs" / "phases" / "phase-8" / "declaration-evidence"
#: The writer whose production call sites are counted. The module that DEFINES it
#: is excluded, because a definition is not a caller -- that distinction is the
#: whole of what 08-04 found: three public names with zero production callers, so
#: rule 50's declaration artifact had never been written by a real game.
DECLARATION_WRITER = "write_declaration_artifact"
DECLARATION_WRITER_MODULE = "artifact_declaration.py"
#: Where the commit hash actually lives in the artifact -- nested, not top level.
_HASH_PATH = ("declarations", "own", "declaration", "commit_hash")
_CURVE_DIR = "artifacts/curves/"


def _readme_of(dest: Path, role: str) -> str:
    path = split_root(dest, role) / "README.md"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _screenshot_slots() -> dict:
    """Tracked images that are NOT a training curve. Zero today, and stated so.

    Asked of `git ls-files` across the whole tree, not of one directory. The
    first draft globbed `docs/assets/` only -- a directory that does not exist
    -- and reported `tracked_images: 0` while the audit gate, asking the same
    question properly, was reporting five. A count taken over the wrong set is
    not a smaller count; it is a different question.
    """
    listed = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    tracked = [path for path in listed
               if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
    return {
        "tracked_images": len(tracked),
        "non_curve_images": len([p for p in tracked if _CURVE_DIR not in p]),
        "verdict": "PENDING",
        "owner": "07-10 (human -- one live run, then two screenshots)",
        "audit_rows": ["G1-03b", "G5-04"],
        "note": "MARKED-ABSENT SLOTS. 08-06 wrote the slots and refused to fake them.",
    }


def measure_criterion_2(dest: Path) -> dict:
    """The published README's six sections, plus the three human-only halves."""
    per_role = {}
    for role in ROLES:
        text = _readme_of(dest, role)
        per_role[role] = {
            "readme_bytes": len(text),
            "missing_academic_942_headings": checks.missing_headings(
                text, checks.ACADEMIC_942_HEADINGS
            ),
            "missing_segal_21_headings": checks.missing_headings(
                text, checks.SEGAL_21_HEADINGS
            ),
            "academic_sections_expected": len(checks.ACADEMIC_942_HEADINGS),
        }
    return {
        "criterion": "2 -- academic README, screenshots, submission form PDF, per member",
        "published_readmes": per_role,
        "screenshots": _screenshot_slots(),
        "submission_form_pdf": {
            "verdict": "PENDING",
            "owner": "08-14 (human)",
            "open_question": "OQ8-3 -- neither docs/RULES.md nor docs/PARAMETERS.md records "
                             "where the form lives; no location is guessed",
            "runbook": "docs/phases/phase-8/SUBMISSION-RUNBOOK.md",
        },
        "submitted_per_member": {
            "verdict": "PENDING", "owner": "08-14 (human)",
            "team_code": "khm-mn17", "team_size": 1,
        },
        "self_assessment_score": {
            "verdict": "PENDING", "owner": "08-14 (human)",
            "open_question": "OQ8-4 -- a numeric claim about our own work (rule 55)",
            "evidence_table": "docs/SELF-ASSESSMENT.md (drafted by 08-11, score field BLANK)",
        },
    }


def _nested(payload: dict, path: tuple[str, ...]) -> object:
    for key in path:
        if not isinstance(payload, dict):
            return None
        payload = payload.get(key)
    return payload


def _call_sites() -> list[str]:
    """Every `src/` module that CALLS the declaration writer, definition excluded."""
    return sorted(
        str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        for path in (REPO_ROOT / "src").rglob("*.py")
        if path.name != DECLARATION_WRITER_MODULE
        and f"{DECLARATION_WRITER}(" in path.read_text(encoding="utf-8")
    )


def _declaration_wiring() -> dict:
    """The commit hash reaches the wire only if a production call site exists."""
    retained = sorted(
        path.name for path in DECLARATION_EVIDENCE.glob("*_declaration_*.json")
    ) if DECLARATION_EVIDENCE.is_dir() else []
    hashes = {}
    for name in retained:
        payload = json.loads((DECLARATION_EVIDENCE / name).read_text(encoding="utf-8"))
        found = _nested(payload, _HASH_PATH)
        if isinstance(found, str) and found.strip():
            hashes[name] = found
    return {
        "declaration_writer": DECLARATION_WRITER,
        "production_call_sites": _call_sites(),
        "call_site_present": bool(_call_sites()),
        "commit_hash_field": ".".join(_HASH_PATH),
        "retained_declaration_artifacts": retained,
        "retained_artifacts_carrying_a_commit_hash": sorted(hashes),
        "commit_hashes_found": sorted(set(hashes.values())),
    }


def measure_criterion_3() -> dict:
    """The ledger's derived count against Table 18's two fixed bounds."""
    ledgers = {}
    for role in ROLES:
        ledger = read_ledger(REPO_ROOT / "config" / role)
        ledgers[role] = {
            "scored_games": count_reading(ledger, scored_only=True),
            "all_games": count_reading(ledger, scored_only=False),
            "distinct_scored_opponents": list(scored_opponents(ledger)),
        }
    return {
        "criterion": "3 -- >=2 scored games vs different teams, reported with the commit hash",
        "ledger": ledgers,
        "bounds": {"minimum_games": MINIMUM_GAMES, "max_games_per_team": MAX_GAMES_PER_TEAM},
        "declaration_wiring": _declaration_wiring(),
        "scored_games_played": {
            "verdict": "PENDING",
            "owner": "08-13 (human, and blocked on 07-10)",
            "why": "real opponent teams cannot be arranged by an agent, and rule 35 zeroes "
                   "BOTH teams when either fails to report -- so no game is played to "
                   "demonstrate a delta",
            "runbook": "docs/phases/phase-8/LEAGUE-RUNBOOK.md",
        },
        "games_played_declaration": {
            "verdict": "PENDING", "owner": "08-14 (human)",
            "open_question": "OQ8-2 -- the rule-38 value is not an agent's to pick",
        },
    }
