"""Structural CI gate for rules 8-9: nothing under `src/pursuit/gui/` may
reach the objective board state.

Rule 9 (`docs/RULES.md:30`) makes displaying the full objective board state
in the live interface a PROJECT DISQUALIFICATION. The read model that
prevents it is `pursuit.sdk.local_view` (D-74); this script enforces the
other half -- that no view module goes around it.

Two independent checks, because either alone is porous:

1. **Imports.** A `gui/` module may not import `pursuit.sdk.engine`,
   `pursuit.shared.state` or anything under `pursuit.network`: those are
   the packages that hand out a `GameState` or an `AgentContext`. It may
   not bind an arbitrary `pursuit.services.*` name either -- the LLM
   gatekeeper and the mail sinks have no business inside a view -- and the
   allowlist below is stated in source, not implied.
2. **Attribute chains.** `<anything>.state.cop` / `.state.thief` /
   `.state.barriers`. This is the check that matters: `ctx.state` is on
   every agent process by design, so a module could import nothing
   forbidden and still read the opponent's true cell off it.

DELIBERATELY A PLAIN `ast` WALK: it never imports `pursuit`, so it runs
from a bare checkout with nothing installed, exactly like the
`check_no_llm_in_strategy.py` mould it copies. `find_violations(root=...)`
is overridable so a test can point it at a synthetic tree.

IT MUST FAIL LOUDLY ON AN EMPTY SCAN. `src/pursuit/gui/` does not exist
until 07-06, and `Path.rglob` over a missing directory returns nothing at
all -- so the mould's own shape would find zero violations and print OK,
reporting success for having looked at nothing. `EmptyScanError` and the
module count on the OK line exist so that can never happen quietly.

`tests/unit/test_check_local_truth.py` loads this module BY FILE PATH and
calls these functions directly, so the pytest suite and the CI job are
proven to run the SAME logic rather than two copies of it (QUAL-02).

Usage::

    uv run python scripts/check_local_truth.py
    bash scripts/check_local_truth.sh   # the CI-facing wrapper
"""

from __future__ import annotations

import ast
import sys
from enum import IntEnum
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parent.parent / "src" / "pursuit" / "gui"

#: Packages that hand out the objective board state or the live context.
FORBIDDEN_IMPORTS = ("pursuit.sdk.engine", "pursuit.shared.state", "pursuit.network")

#: `GameState`'s own field names (`shared/state.py`). `barriers_placed` and
#: `turn` are omitted on purpose: both are legitimately displayable, and a
#: rule that flagged them would be routed around rather than obeyed.
TRUE_POSITION_FIELDS = ("cop", "thief", "barriers")

#: The ONE service path a view may reach: the replay viewer's own hash
#: re-verification (07-08). Anything else under `pursuit.services` -- the
#: LLM gatekeeper, the Gmail sink, the artifact writers -- is reported.
#: Widening this is a deliberate act, and a test asserts it is non-empty.
ALLOWED_SERVICE_MODULES = ("pursuit.services.reporting.replay_verify",)

_SERVICES = "pursuit.services"


class ExitCode(IntEnum):
    """Process exit codes. Structural, not game parameters (the
    `watchdog.WatchdogExit` precedent for naming rather than hardcoding)."""

    OK = 0
    VIOLATIONS = 1
    EMPTY_SCAN = 2


class EmptyScanError(RuntimeError):
    """The scan set was empty, so a clean result would mean nothing."""


def gui_module_paths(root: Path = GUI_ROOT) -> list[Path]:
    """Every module under `root`. Raises rather than returning `[]`."""
    if not root.is_dir():
        raise EmptyScanError(
            f"local-truth gate scanned nothing: {root} does not exist. "
            "07-06 creates it; until then this gate cannot vouch for anything."
        )
    paths = sorted(root.rglob("*.py"))
    if not paths:
        raise EmptyScanError(f"local-truth gate scanned nothing: {root} holds no modules.")
    return paths


def bound_module_names(tree: ast.AST) -> list[str]:
    """Every dotted module name this source binds. An `ImportFrom` yields
    both the module and each `module.name`, so `from pursuit.sdk import
    engine` is seen as `pursuit.sdk.engine` and not merely `pursuit.sdk`."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
            names.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return names


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
    for name in bound_module_names(tree):
        if any(_is_under(name, prefix) for prefix in FORBIDDEN_IMPORTS):
            found.append(f"{path}: imports {name!r} (rules 8-9 -- reaches the true board)")
        elif _is_under(name, _SERVICES) and not _service_is_allowed(name):
            found.append(f"{path}: imports {name!r} (not the allowlisted reporting read path)")
    return found


def _field_violations(path: Path, tree: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr not in TRUE_POSITION_FIELDS:
            continue
        if isinstance(node.value, ast.Attribute) and node.value.attr == "state":
            found.append(f"{path}: reads .state.{node.attr} (rule 9 -- the objective board)")
    return found


def find_violations(root: Path = GUI_ROOT) -> list[str]:
    """One message per violation; `[]` only after a NON-EMPTY scan."""
    violations: list[str] = []
    for path in gui_module_paths(root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations.extend(_import_violations(path, tree))
        violations.extend(_field_violations(path, tree))
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
