"""07-03's rules 8-9 gate, run against the REAL `src/pursuit/gui/` package --
plus the three blind spots 07-06 measured open and closed (D7-9).

THE MODULE COUNT IS THE WHOLE POINT of the first test. `find_violations`
returning `[]` proves nothing on its own: it returned `[]` for three years'
worth of nothing while the package did not exist, which is why 07-03 made an
empty scan a loud failure and why this file asserts a non-zero count beside
every clean verdict.

The gate is loaded BY FILE PATH (the `test_strategy_pluggable.py` pattern),
so the suite and the CI job provably run the same logic.

`gui/` IS COVERAGE-OMITTED (`pyproject.toml:38`), so "no logic in `gui/`" is
not a style preference -- logic there is untested AND invisible to the
`fail_under = 85` gate. The last four tests enforce it structurally: no
arithmetic, no string building, and no import outside `pursuit.sdk` /
`pursuit.gui`. Each is paired with a synthetic control proving the scan can
fail.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib

_SCRIPT = pathlib.Path(__file__).parents[2] / "scripts" / "check_local_truth.py"
GUI_ROOT = pathlib.Path(__file__).parents[2] / "src" / "pursuit" / "gui"

#: The panel a debugging shortcut produces, in the three encodings 07-06
#: measured passing the gate before it was hardened.
_INDIRECT = {
    "direct.py": "def render(ctx):\n    return ctx.state.thief\n",
    "aliased.py": "def render(ctx):\n    s = ctx.state\n    return s.thief\n",
    "dynamic.py": "def render(ctx):\n    return getattr(ctx.state, 'cop')\n",
    "keyed.py": "def render(payload):\n    return payload['barriers']\n",
}

_CLEAN = (
    "from pursuit.sdk.local_view import LocalView\n"
    "def render(view: LocalView):\n    return view.own_cell\n"
)

_ARITHMETIC_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_STRING_BUILDERS = ("join", "format")
_ALLOWED_PACKAGES = ("pursuit.sdk", "pursuit.gui")
_MIN_GUI_MODULES = 2


def _check():
    spec = importlib.util.spec_from_file_location("check_local_truth", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree(root: pathlib.Path, sources: dict) -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        (root / name).write_text(source, encoding="utf-8")
    return root


def _gui_trees() -> dict:
    return {
        path: ast.parse(path.read_text(encoding="utf-8"))
        for path in sorted(GUI_ROOT.rglob("*.py"))
    }


def _arithmetic(tree: ast.AST) -> list[str]:
    """Arithmetic `BinOp`s only. `X | None` in an annotation is a `BitOr` and
    is deliberately not one of them."""
    return [
        type(node.op).__name__
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp | ast.AugAssign) and isinstance(node.op, _ARITHMETIC_OPS)
    ]


def _string_building(tree: ast.AST) -> list[str]:
    """f-strings and `.join`/`.format` calls -- every way a module builds a
    string it was not handed."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            found.append("f-string")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _STRING_BUILDERS
        ):
            found.append(node.func.attr)
    return found


def test_the_real_gui_package_passes_and_the_scan_was_not_empty():
    check = _check()
    scanned = check.gui_module_paths()
    assert len(scanned) >= _MIN_GUI_MODULES, f"the gate judged almost nothing: {scanned}"
    assert check.find_violations() == []
    assert check.main() == check.ExitCode.OK


def test_a_leaky_module_added_to_the_same_tree_would_be_reported(tmp_path):
    """The counter-control for the verdict above: the identical function,
    over a tree that differs only by one panel."""
    check = _check()
    root = _tree(tmp_path / "gui", {**_INDIRECT, "clean.py": _CLEAN})
    reported = {pathlib.Path(v.split(": ")[0]).name for v in check.find_violations(root=root)}
    assert reported == set(_INDIRECT), f"missed: {set(_INDIRECT) - reported}"


def test_a_root_of_bare_package_markers_is_not_a_pass(tmp_path, capsys):
    """D7-9's anti-vacuity hole, measured open before this: an empty
    `__init__.py` alone printed `OK: 1 module(s) scanned` and exited 0, so
    the gate could be turned green without a view layer existing."""
    check = _check()
    root = _tree(tmp_path / "gui", {"__init__.py": '"""A docstring and nothing else."""\n'})
    assert check.main(root=root) == check.ExitCode.EMPTY_SCAN
    assert "ERROR" in capsys.readouterr().out
    _tree(root, {"panel.py": _CLEAN})
    assert check.main(root=root) == check.ExitCode.OK


def test_the_real_package_is_more_than_its_marker():
    """The same question asked of the shipped tree rather than a fixture."""
    check = _check()
    trees = _gui_trees()
    substantive = [path.name for path, tree in trees.items() if not check.scan.is_package_marker(tree)]
    assert len(substantive) >= _MIN_GUI_MODULES, substantive


def test_a_pyw_panel_is_scanned_alongside_the_py_modules(tmp_path):
    """The Windows "no console window" suffix -- exactly what a GUI entry
    point gets renamed to, and invisible to `rglob('*.py')`."""
    check = _check()
    root = _tree(tmp_path / "gui", {"clean.py": _CLEAN})
    (root / "panel.pyw").write_text(_INDIRECT["direct.py"], encoding="utf-8")
    assert len(check.gui_module_paths(root=root)) == 2
    assert [v for v in check.find_violations(root=root) if "panel.pyw" in v]


def test_no_gui_module_performs_arithmetic():
    """Every pixel bound, grid position and bucket index is computed in
    `sdk/view_render.py`, where coverage can see it."""
    offenders = {path.name: ops for path, tree in _gui_trees().items() if (ops := _arithmetic(tree))}
    assert offenders == {}, f"derivation under a coverage-omitted directory: {offenders}"


def test_no_gui_module_builds_a_string():
    """Every sidebar line, including the newline join, is built in
    `sdk/view_text.py`."""
    offenders = {
        path.name: kinds for path, tree in _gui_trees().items() if (kinds := _string_building(tree))
    }
    assert offenders == {}, f"string building under a coverage-omitted directory: {offenders}"


def test_both_logic_scans_are_not_no_ops(tmp_path):
    """ANTI-VACUITY for the two tests above: the identical scans, over a
    module that does exactly what they forbid, must report it."""
    source = "def render(n, parts):\n    return f'{n * 2}' + ', '.join(parts)\n"
    tree = ast.parse(source)
    assert sorted(_arithmetic(tree)) == ["Add", "Mult"], "string + is caught as Add"
    assert sorted(_string_building(tree)) == ["f-string", "join"]
    assert _arithmetic(ast.parse("def f(x: int | None): ...\n")) == [], "an annotation is not arithmetic"


def test_gui_imports_only_the_sdk_read_model_and_its_own_package():
    check = _check()
    checked = 0
    for path, tree in _gui_trees().items():
        if check.scan.is_package_marker(tree):
            continue
        bound = [n for n in check.scan.bound_module_names(tree) if n.startswith("pursuit")]
        assert bound, f"{path.name} binds no pursuit name at all"
        for name in bound:
            assert name.startswith(_ALLOWED_PACKAGES), f"{path.name} imports {name}"
        checked += 1
    assert checked >= _MIN_GUI_MODULES, "the import scan visited almost nothing"
