#!/usr/bin/env python
"""Build the two submission repositories from this one, LOCALLY (08-10).

    uv run python scripts/build_split_repos.py --dest C:/somewhere/outside
    uv run python scripts/build_split_repos.py --dest DIR --gates --json out.json

Exit 0 when every row of every built repository passes, 1 when any row fails,
2 when nothing was built or nothing was verified -- `check_submission.py`'s
contract (D-82), because a build that produced no rows must never read as a pass.

THIS COMMAND NEVER TOUCHES A REMOTE. It runs `init`, `add`, `commit` and local
reads. There is no `push`, no `remote add`, no `fetch`, no `tag` in this file or
in any module it imports, and every built repository is asserted to have ZERO
remotes before this returns. Creating the public repositories, adding their
remotes and pushing is 08-12 -- a human, on a human's account.

WHY BOTH REPOSITORIES CARRY THE SAME FILES. The two agents are separate
PROCESSES, and rule 2 forbids sharing runtime state between them. It does not
forbid the two publishable repositories from carrying the same static library
and the same two configuration directories -- and the test suite loads BOTH
seats, so a repository holding one of them could not run its own quality gates
and therefore could not be shown to meet Table 5 inside its own tree (D-77).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from split_build import (  # noqa: E402
    UnsafeDestinationError,
    copy_files,
    init_and_commit,
    prepare_destination,
)
from split_docs import banner, inject, provenance  # noqa: E402
from split_gates import (  # noqa: E402
    RUFF,
    SUITE,
    SYNC,
    coverage_floor,
    run_gate,
    simple_row,
    suite_row,
)
from split_manifest import ROLES, manifest_for  # noqa: E402
from split_report import git_rows, overall, render  # noqa: E402
from split_verify import (  # noqa: E402
    absence_row,
    config_row,
    git_out,
    line_limit_row,
    rule50_row,
    workflow_row,
)

PROVENANCE = "docs/REPO-SPLIT.md"
NAME_TEMPLATE = "pursuit-{role}"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_one(source_root: Path, dest_root: Path, role: str, replace: bool) -> dict:
    """Materialise one role's repository and return what was built, in numbers."""
    manifest = manifest_for(source_root)
    stamp = _stamp()
    source_commit = git_out(source_root, "rev-parse", "--short", "HEAD").strip()
    dest = prepare_destination(dest_root, source_root, replace=replace)
    copied = copy_files(source_root, dest, manifest.included)

    readme = dest / "README.md"
    readme.write_text(
        inject(readme.read_text(encoding="utf-8"), banner(role, source_commit, stamp)),
        encoding="utf-8", newline="\n",
    )
    (dest / PROVENANCE).parent.mkdir(parents=True, exist_ok=True)
    (dest / PROVENANCE).write_text(
        provenance(role, source_commit, stamp, manifest.count, manifest.excluded),
        encoding="utf-8", newline="\n",
    )
    staged = (*manifest.included, PROVENANCE)
    sha = init_and_commit(
        dest, staged,
        f"chore: initial import of the {role} submission repository "
        f"(split from {source_commit}, {manifest.count} tracked files)",
        source_root,
    )
    return {
        "role": role, "path": str(dest), "commit": sha, "source_commit": source_commit,
        "generated": stamp, "copied": copied, "staged": len(staged),
        "excluded": [{"path": path, "reason": reason} for path, reason in manifest.excluded],
    }


def verify_one(dest: Path, source_root: Path, role: str, with_gates: bool) -> list:
    """Every row for one built repository, structural first, gates last."""
    rows = [
        *git_rows(dest, source_root, role),
        line_limit_row(dest), absence_row(dest), config_row(dest),
        rule50_row(dest), workflow_row(dest),
    ]
    if with_gates:
        rows.append(simple_row("uv sync", *run_gate(dest, SYNC)))
        rows.append(simple_row("ruff check .", *run_gate(dest, RUFF)))
        code, output = run_gate(dest, SUITE)
        rows.append(suite_row(code, output, coverage_floor(dest)))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the two submission repositories")
    parser.add_argument("--dest", type=Path, required=True,
                        help="a directory OUTSIDE this repository to build into")
    parser.add_argument("--roles", nargs="+", default=list(ROLES), choices=list(ROLES))
    parser.add_argument("--replace", action="store_true", help="rebuild over an existing tree")
    parser.add_argument("--gates", action="store_true",
                        help="also run uv sync, ruff and pytest --cov inside each output")
    parser.add_argument("--json", type=Path, default=None, help="write the evidence here")
    args = parser.parse_args(argv)

    source_root = Path(__file__).resolve().parent.parent
    evidence, failures, checked = [], 0, 0
    for role in args.roles:
        try:
            built = build_one(source_root, args.dest / NAME_TEMPLATE.format(role=role),
                              role, args.replace)
        except UnsafeDestinationError as exc:
            print(f"REFUSED: {exc}")
            return 2
        rows = verify_one(Path(built["path"]), source_root, role, args.gates)
        checked += len(rows)
        failures += sum(1 for row in rows if not row.ok)
        print(render(role, rows))
        built["rows"] = [row.as_dict() for row in rows]
        built["verdict"] = "pass" if overall(rows) else "FAIL"
        evidence.append(built)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8", newline="\n")
        print(f"Wrote {args.json}")
    if not evidence or not checked:
        print("NOTHING WAS BUILT OR NOTHING WAS CHECKED -- this is not a pass.")
        return 2
    print(f"{len(evidence)} repository/repositories, {checked} rows, {failures} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
