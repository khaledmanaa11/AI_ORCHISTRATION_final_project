"""The AST primitives behind `check_local_truth.py`, split out at the
150-code-line gate (Segal Table 5) when 07-06 closed D7-9's three blind
spots and the single file reached 198.

`check_line_limit.sh:18` enumerates `src/** tests/** training/**`, so this
directory is NOT covered by the no-argument form of the size gate and
`pyproject.toml:37` leaves it out of coverage as well. Both halves are
therefore checked EXPLICITLY BY PATH in this plan's verification, and both
are exercised by `tests/unit/test_check_local_truth.py`, which loads the
gate by file path so the suite and the CI job provably run the same code.

Kept in `scripts/` rather than moved under `src/`: 07-03's stated design is
that this gate never imports `pursuit`, so it runs from a bare checkout with
nothing installed. A gate that cannot run when the package is broken is not a
gate.
"""

from __future__ import annotations

import ast

#: `GameState`'s own field names (`shared/state.py`). `barriers_placed` and
#: `turn` are omitted on purpose: both are legitimately displayable, and a
#: rule that flagged them would be routed around rather than obeyed.
TRUE_POSITION_FIELDS = ("cop", "thief", "barriers")

STATE_ATTR = "state"
GETATTR = "getattr"
_MIN_GETATTR_ARGS = 2


def _is_literal_dunder(node: ast.stmt) -> bool:
    """True for `__all__ = ("a", "b")` and nothing that computes or imports.

    Added by 08-03, which gave every package the `__all__` Sec14 requires. The
    admission is deliberately narrow: a single `__dunder__` target whose value
    `ast.literal_eval` accepts. Such a statement binds no name from anywhere and
    evaluates nothing, so it cannot reach the objective board state -- which is
    the only question this module exists to answer. `__version__ = VERSION` is
    NOT admitted, because its value is a Name and a Name came from an import.
    """
    if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
        return False
    target = node.targets[0]
    if not (isinstance(target, ast.Name) and target.id.startswith("__")
            and target.id.endswith("__")):
        return False
    try:
        ast.literal_eval(node.value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False
    return True


def is_package_marker(tree: ast.Module) -> bool:
    """True for a module that declares nothing it could derive anything from --
    a docstring, `__future__` imports, a literal `__all__`, or an empty file.

    The anti-vacuity question. Measured before this existed: a root holding
    one empty `__init__.py` printed `OK: 1 module(s) scanned` and exited 0,
    so the gate could be turned green without a single view module existing.
    That property is untouched by the `__all__` admission above: a `gui/`
    holding only a marker still raises `EmptyScanError`, and the three floors
    in `test_gui_structural.py` still count only substantive modules.
    """
    return all(
        (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
        or (isinstance(node, ast.ImportFrom) and node.module == "__future__")
        or _is_literal_dunder(node)
        for node in tree.body
    )


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


def state_aliases(tree: ast.AST) -> set[str]:
    """Every local name bound to a `.state` object, so `s = ctx.state`
    followed by `s.thief` is seen.

    Measured before this existed: a module doing exactly that, plus
    `getattr(ctx.state, "thief")` and `asdict(s)["cop"]`, passed the gate
    with `violations=[]` and exit 0 -- three separate reads of the true
    position, all invisible.

    A parameter named `state` (`def render(state): ...`) stays out of reach
    of a single-module AST walk, and that limit is stated rather than papered
    over: the recovery tests are what stand behind this gate.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign | ast.AnnAssign) or not is_state_read(node.value):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names.update(target.id for target in targets if isinstance(target, ast.Name))
    return names


def is_state_read(node: object) -> bool:
    """True for a `<anything>.state` expression."""
    return isinstance(node, ast.Attribute) and node.attr == STATE_ATTR


def accessor_key(node: ast.AST) -> str | None:
    """The string key this node uses to reach a field DYNAMICALLY --
    `x["thief"]` or `getattr(x, "thief")` -- else None.

    Checked on the KEY rather than on what it is applied to, which is what
    makes it total over indirections nobody has thought of yet: a view module
    has no legitimate reason to key anything on `cop`, `thief` or `barriers`,
    however it got hold of the mapping.
    """
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        key = node.slice.value
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == GETATTR
        and len(node.args) >= _MIN_GETATTR_ARGS
        and isinstance(node.args[1], ast.Constant)
    ):
        key = node.args[1].value
    else:
        return None
    return key if isinstance(key, str) else None


def field_violations(path: object, tree: ast.AST) -> list[str]:
    """Every read of the objective board state in one module: the direct
    chain, the aliased chain, and the dynamic key."""
    aliases = state_aliases(tree)
    found = []
    for node in ast.walk(tree):
        key = accessor_key(node)
        if key in TRUE_POSITION_FIELDS:
            found.append(f"{path}: keys on {key!r} (rule 9 -- the objective board, indirectly)")
        if not isinstance(node, ast.Attribute) or node.attr not in TRUE_POSITION_FIELDS:
            continue
        if is_state_read(node.value) or (
            isinstance(node.value, ast.Name) and node.value.id in aliases
        ):
            found.append(f"{path}: reads .state.{node.attr} (rule 9 -- the objective board)")
    return found
