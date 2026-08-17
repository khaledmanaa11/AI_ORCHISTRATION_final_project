"""Structural verification of a built split repository, run inside it (08-10).

EVERY ROW REPORTS A COUNT, AND A ZERO COUNT IS A FAILURE, NEVER A PASS. This is
not a style preference. `check_line_limit.sh`'s no-argument form enumerates
through `git ls-files`, which is EMPTY in a freshly `git init`ed tree before the
first commit; the gate then exits 0 having read nothing, and a verifier that
believed the exit code would certify an empty repository as clean. The same
vacuity is on record in `05-18-SUMMARY.md`, and `submission_code._line_limit_row`
already refuses a zero count for the same reason -- this module applies the rule
to every row it has.

THE ABSENCE ROW LOOKS ON DISK AND IN THE TRACKED SET. A file can be present and
untracked (which is how `.env` lives in the development tree) or tracked and
deleted; both are reported, because a public repository is judged on what a
`git clone` produces AND on what a directory listing shows.

NOTHING HERE MUTATES THE TREE IT IS POINTED AT, and no git call reaches a
network: `ls-files`, `rev-list`, `remote` and `rev-parse` only.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: The three globs `scripts/check_line_limit.sh:18` enumerates.
LIMIT_PREFIXES = ("src/", "tests/", "training/")
#: Nothing under any of these names may exist in a published tree.
MUST_BE_ABSENT = (
    ".env", "police_thief_p2p.pdf", "requirements.txt",
    "config/police/games_played.json", "config/police/games_played.prev.json",
    "config/thief/games_played.json", "config/thief/games_played.prev.json",
)
#: Rule 50's floor: what every submitted repository has to contain.
ROLES = ("police", "thief")
_RUN_PATH = re.compile(r"(scripts/[\w./-]+)")
_RUN_LINE = re.compile(r"^(\s*)-?\s*run:\s*(.*)$")


@dataclass(frozen=True)
class Check:
    """One verified property, its verdict, and the numbers behind it."""

    name: str
    ok: bool
    detail: str

    def as_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def git_out(root: Path, *args: str) -> str:
    """A local git read. Never a network verb."""
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    return done.stdout


def tracked(root: Path) -> tuple[str, ...]:
    """The tree's own tracked set, POSIX-separated."""
    return tuple(sorted(
        line.replace("\\", "/") for line in git_out(root, "ls-files").splitlines()
        if line.strip()
    ))


def line_limit_scope(root: Path) -> tuple[str, ...]:
    """The files `check_line_limit.sh` would scan, enumerated independently."""
    return tuple(
        path for path in tracked(root)
        if path.endswith(".py") and path.startswith(LIMIT_PREFIXES)
    )


def line_limit_row(root: Path) -> Check:
    """Exit code AND scanned count. A green exit over an empty list fails here."""
    scope = line_limit_scope(root)
    done = subprocess.run(
        ["sh", "scripts/check_line_limit.sh"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    output = (done.stdout or "") + (done.stderr or "")
    violations = [line for line in output.splitlines() if line.startswith("VIOLATION:")]
    return Check(
        "line-limit (<=150 code lines)",
        done.returncode == 0 and not violations and len(scope) > 0,
        f"exit {done.returncode}; scanned {len(scope)} tracked .py files under "
        f"{list(LIMIT_PREFIXES)}; violations {len(violations)} "
        "(a scan of 0 files is a vacuous pass and fails this row)",
    )


def absence_row(root: Path) -> Check:
    """Nothing on `MUST_BE_ABSENT` may be on disk or in the tracked set."""
    tracked_set = set(tracked(root))
    on_disk = [name for name in MUST_BE_ABSENT if (Path(root) / name).exists()]
    in_git = [name for name in MUST_BE_ABSENT if name in tracked_set]
    return Check(
        "forbidden paths absent",
        not on_disk and not in_git,
        f"{len(MUST_BE_ABSENT)} names checked; {len(on_disk)} present on disk {on_disk}; "
        f"{len(in_git)} tracked {in_git}",
    )


def config_row(root: Path) -> Check:
    """D-77: both seats' config directories ship, and neither carries a counter."""
    per_role = {
        role: [path for path in tracked(root) if path.startswith(f"config/{role}/")]
        for role in ROLES
    }
    counters = [path for files in per_role.values() for path in files if "games_played" in path]
    ok = all(len(files) >= 14 for files in per_role.values()) and not counters
    detail = "; ".join(f"{role} {len(files)}" for role, files in per_role.items())
    return Check("both seats' config shipped (D-77)", ok,
                 f"tracked config files: {detail}; counters carried: {len(counters)}")


def rule50_row(root: Path) -> Check:
    """README, config, per-mechanism PRDs, a PLAN and TODO files -- each counted."""
    paths = tracked(root)
    counts = {
        "README": len([p for p in paths if p == "README.md"]),
        "config": len([p for p in paths if p.startswith("config/")]),
        "PRD": len([p for p in paths if p.startswith("docs/PRD") and p.endswith(".md")]),
        "PLAN": len([p for p in paths if p.endswith("PLAN.md")]),
        "TODO": len([p for p in paths if p.endswith("TODO.md")]),
    }
    return Check("rule 50 inventory", all(value > 0 for value in counts.values()),
                 "; ".join(f"{key} {value}" for key, value in counts.items()))


def run_commands(text: str) -> list[str]:
    """The command text of every `run:` step, block scalars included.

    Only `run:` steps, never the whole file: `quality-gate.yml` DISCUSSES
    `scripts/submission_testing._report_artifact_row` in a comment, and a
    whole-file grep would report that prose as a missing file.
    """
    commands: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = _RUN_LINE.match(lines[index])
        index += 1
        if not match:
            continue
        indent, value = len(match.group(1)), match.group(2).strip()
        if value not in ("|", "|-", ">", ">-"):
            commands.append(value)
            continue
        while index < len(lines):
            following = lines[index]
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            commands.append(following)
            index += 1
    return commands


def workflow_row(root: Path) -> Check:
    """Every `scripts/...` path a CI workflow's `run:` step names must exist here."""
    flows = sorted((Path(root) / ".github" / "workflows").glob("*.yml"))
    referenced: set[str] = set()
    for flow in flows:
        for command in run_commands(flow.read_text(encoding="utf-8")):
            referenced.update(_RUN_PATH.findall(command))
    missing = sorted(name for name in referenced if not (Path(root) / name).is_file())
    return Check(
        "CI workflows reference only paths that ship",
        bool(flows) and bool(referenced) and not missing,
        f"{len(flows)} workflow file(s); {len(referenced)} scripts/ path(s) referenced; "
        f"{len(missing)} missing {missing}",
    )
