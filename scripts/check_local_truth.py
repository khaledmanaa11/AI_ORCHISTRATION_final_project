"""Structural CI gate for rules 8-9: nothing under `src/pursuit/gui/` may
reach the objective board state.

Rule 9 (`docs/RULES.md:30`) makes displaying the full objective board state
in the live interface a PROJECT DISQUALIFICATION. The read model that
prevents it is `pursuit.sdk.local_view` (D-74); this script enforces the
other half -- that no view module goes around it.

WHAT THIS GATE CANNOT DO, STATED FIRST SO NO CLEAN VERDICT IS EVER MISTAKEN
FOR COMPLIANCE (D7-9). It is an import/attribute gate: it sees a coordinate
that is NAMED, never one that is DRAWN. 07-11 measured it returning
`violations: []`, `1 module(s) scanned`, exit 0 against a synthetic panel
that markered `belief.argmax` and labelled the `scent.opponent` peak. The
recovery question -- can the true cell be INVERTED out of what a panel paints
-- is asked by `tests/unit/test_gui_recovery.py` and by
`tests/unit/test_local_truth_recovery.py`, and neither file replaces the
other.

Three checks, because each alone is porous:

1. **Imports.** A `gui/` module may not import `pursuit.sdk.engine`,
   `pursuit.shared.state` or anything under `pursuit.network`: those hand out
   a `GameState` or a live agent context. It may not bind an arbitrary
   `pursuit.services.*` name either, and the allowlist is stated in source.
2. **Attribute chains.** `<anything>.state.cop` / `.state.thief` /
   `.state.barriers`, AND the same read through a local alias
   (`s = ctx.state` then `s.thief`).
3. **Dynamic accessor keys.** `getattr(x, "thief")` and `asdict(s)["cop"]`.

Checks 2 and 3 live in the sibling `local_truth_ast.py`, split out at the
150-code-line gate when 07-06 closed D7-9. Both halves are checked
EXPLICITLY BY PATH against that gate, because `check_line_limit.sh:18`
enumerates `src/** tests/** training/**` and skips this directory.

DELIBERATELY A PLAIN `ast` WALK: it never imports `pursuit`, so it runs from
a bare checkout with nothing installed, exactly like the
`check_no_llm_in_strategy.py` mould it copies. The sibling is loaded BY FILE
PATH for the same reason -- no package, no install, no `sys.path` surgery.

IT MUST FAIL LOUDLY ON A SCAN THAT JUDGED NOTHING, in all three of its forms:
a missing root, a root with no modules, and -- closed by 07-06 after it was
measured returning `OK: 1 module(s) scanned`, exit 0 -- a root holding
nothing but bare package markers. An empty `__init__.py` is not a view layer,
and a gate that reports OK for having looked at one is worse than no gate.
`.pyw` is scanned alongside `.py` for the same reason: it is the Windows
"no console window" suffix, i.e. exactly what a GUI entry point gets renamed
to, and `rglob("*.py")` alone never saw it.

`tests/unit/test_check_local_truth.py` and `tests/unit/test_gui_structural.py`
load this module BY FILE PATH and call these functions directly, so the
pytest suite and the CI job are proven to run the SAME logic rather than two
copies of it (QUAL-02).

Usage::

    uv run python scripts/check_local_truth.py
    bash scripts/check_local_truth.sh   # the CI-facing wrapper
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from enum import IntEnum
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parent.parent / "src" / "pursuit" / "gui"

#: Module suffixes that are scanned (see the `.pyw` note above).
MODULE_GLOBS = ("*.py", "*.pyw")

#: Packages that hand out the objective board state or the live context.
FORBIDDEN_IMPORTS = ("pursuit.sdk.engine", "pursuit.shared.state", "pursuit.network")

#: The ONE service path a view may reach: the replay viewer's own hash
#: re-verification (07-08). Anything else under `pursuit.services` -- the
#: LLM gatekeeper, the Gmail sink, the artifact writers -- is reported.
#: Widening this is a deliberate act, and a test asserts it is non-empty.
ALLOWED_SERVICE_MODULES = ("pursuit.services.reporting.replay_verify",)

_SERVICES = "pursuit.services"


def _load_sibling(name: str):
    """Load a sibling script by path -- no package, no install, no
    `sys.path` surgery, so the standalone property survives the split."""
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scan = _load_sibling("local_truth_ast")

#: Re-exported so the gate's whole vocabulary is readable from one module.
TRUE_POSITION_FIELDS = scan.TRUE_POSITION_FIELDS


class ExitCode(IntEnum):
    """Process exit codes. Structural, not game parameters (the
    `watchdog.WatchdogExit` precedent for naming rather than hardcoding)."""

    OK = 0
    VIOLATIONS = 1
    EMPTY_SCAN = 2


class EmptyScanError(RuntimeError):
    """The scan judged nothing, so a clean result would mean nothing."""


def parsed_modules(root: Path = GUI_ROOT) -> list[tuple[Path, ast.Module]]:
    """Every module under `root`, parsed. Raises rather than returning `[]`."""
    if not root.is_dir():
        raise EmptyScanError(
            f"local-truth gate scanned nothing: {root} does not exist. The live view "
            "package is what this gate governs; without it nothing is vouched for."
        )
    paths = sorted({path for glob in MODULE_GLOBS for path in root.rglob(glob)})
    if not paths:
        raise EmptyScanError(f"local-truth gate scanned nothing: {root} holds no modules.")
    modules = [(path, ast.parse(path.read_text(encoding="utf-8"))) for path in paths]
    if all(scan.is_package_marker(tree) for _, tree in modules):
        raise EmptyScanError(
            f"local-truth gate scanned nothing it could judge: every module under {root} "
            "is a bare package marker. An empty __init__.py is not a view layer."
        )
    return modules


def gui_module_paths(root: Path = GUI_ROOT) -> list[Path]:
    """Every module under `root`, by path."""
    return [path for path, _ in parsed_modules(root)]


def _is_under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(f"{prefix}.")


def _service_is_allowed(name: str) -> bool:
    """True only for the allowlisted read path itself, a name inside it, or
    the package chain leading to it (`from pursuit.services.reporting import
    replay_verify` binds the parent). A bare `pursuit.services` grab is not
    allowed: it names the whole package and no specific read path."""
    return any(
        _is_under(name, allowed) or _is_under(allowed, name)
        for allowed in ALLOWED_SERVICE_MODULES
        if name != _SERVICES
    )


def _import_violations(path: Path, tree: ast.AST) -> list[str]:
    found = []
    for name in scan.bound_module_names(tree):
        if any(_is_under(name, prefix) for prefix in FORBIDDEN_IMPORTS):
            found.append(f"{path}: imports {name!r} (rules 8-9 -- reaches the true board)")
        elif _is_under(name, _SERVICES) and not _service_is_allowed(name):
            found.append(f"{path}: imports {name!r} (not the allowlisted reporting read path)")
    return found


def find_violations(root: Path = GUI_ROOT) -> list[str]:
    """One message per violation; `[]` only after a scan that judged
    something."""
    violations: list[str] = []
    for path, tree in parsed_modules(root):
        violations.extend(_import_violations(path, tree))
        violations.extend(scan.field_violations(path, tree))
    return violations


def main(root: Path = GUI_ROOT) -> int:
    try:
        scanned = len(gui_module_paths(root))
        violations = find_violations(root)
    except EmptyScanError as empty:
        print(f"ERROR: {empty}")
        return ExitCode.EMPTY_SCAN
    for violation in violations:
        print(f"VIOLATION: {violation}")
    if violations:
        print(f"\n{len(violations)} local-truth violation(s) in {scanned} module(s) under {root}.")
        return ExitCode.VIOLATIONS
    print(f"OK: {scanned} module(s) scanned under {root}; no local-truth violations.")
    return ExitCode.OK


if __name__ == "__main__":
    sys.exit(main())
