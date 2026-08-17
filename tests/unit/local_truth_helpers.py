"""Loading the rules 8-9 gate BY FILE PATH -- once, for every test that asks
it a question.

Extracted here when 07-08's import-allowlist tests would have made a THIRD
copy of the same four helpers (CLAUDE.md Table 5: extract at 2+ copies into a
shared module). `test_check_local_truth.py` and `test_gui_structural.py` each
carried their own `_check`/`_tree`; three spellings of "load the gate" is
exactly how a suite ends up certifying a gate that is not the one CI runs.

LOADED BY FILE PATH, not imported, and that is load-bearing rather than
stylistic: `scripts/check_local_truth.py` is designed never to import
`pursuit`, so it runs from a bare checkout with nothing installed, and it
lives outside any package. Loading it this way is what proves the pytest suite
and the `quality-gate.yml` job run the SAME logic rather than two copies of it
(QUAL-02, the `test_strategy_pluggable.py` pattern).

Not a `test_*.py` module, so pytest collects nothing from it.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib

REPO_ROOT = pathlib.Path(__file__).parents[2]
GATE_SCRIPT = REPO_ROOT / "scripts" / "check_local_truth.py"
GUI_ROOT = REPO_ROOT / "src" / "pursuit" / "gui"


def load_gate():
    """The gate module itself, freshly loaded from `scripts/`."""
    spec = importlib.util.spec_from_file_location("check_local_truth", GATE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_tree(root: pathlib.Path, sources: dict) -> pathlib.Path:
    """A synthetic `gui/` tree -- the counter-control every clean verdict in
    these tests is paired with."""
    root.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        (root / name).write_text(source, encoding="utf-8")
    return root


def gui_trees() -> dict:
    """The REAL shipped package, parsed: `{path -> ast.Module}`."""
    return {
        path: ast.parse(path.read_text(encoding="utf-8"))
        for path in sorted(GUI_ROOT.rglob("*.py"))
    }
