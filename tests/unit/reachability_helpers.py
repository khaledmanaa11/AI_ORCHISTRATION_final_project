"""The AST import scanner shared by the reachability pin suites.

Extracted at the second copy (Segal Sec3, CLAUDE.md Table 5) when the
150-code-line gate split `test_log_artifact_reachability.py` into the
log-builder pins and the ledger pins -- both suites scan `src/` the same way,
and two drifting copies of the scanner would let one suite go blind while the
other still passed its control.

A `from X import Y` contributes BOTH `X` and `X.Y`: the second form is what
makes `from pursuit.services.reporting import artifact_log` visible. Package
re-exports contribute the bare NAME too -- probe 16 measured a turn-loop
module importing `artifact_log` from the package passing 6/6 under a
module-path-only scan, which is the hole this closes.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
PACKAGE = "pursuit.services.reporting"

#: Floor on the scan size, so no suite can pass by having looked at nothing
#: (D7-6's standard). Shared here so both suites keep the same floor.
MIN_SCANNED = 100


def imported_modules(path: Path) -> set[str]:
    """Every module this file imports, by AST -- not by substring, which a
    docstring mention would trip."""
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules.add(node.module)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
            if node.module.startswith(PACKAGE):
                modules.update(alias.name for alias in node.names)
    return modules


def scan_src() -> tuple[dict[str, set[str]], list[Path]]:
    """`{module path -> imported modules}` for every `.py` under `src/`."""
    files = sorted(SRC.rglob("*.py"))
    return {p.relative_to(SRC).as_posix(): imported_modules(p) for p in files}, files
