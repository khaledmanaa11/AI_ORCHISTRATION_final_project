"""`notebooks/analysis.ipynb` runs on a clean checkout, or it is decoration
(08-09).

The 08 outline names the trap: "a notebook that reads `logs/` is empty on a
clean checkout because `logs/` is gitignored". `game_artifacts/` is the same
hazard for the opposite reason -- it is deliberately UNTRACKED (D7-19), so a
notebook fed from it plots beautifully here and nothing at all for a grader.

BOTH HALVES ARE PARSED, NOT GREPPED. A substring scan for `'logs/'` would
fire on the notebook's own prose AND on the guard list inside its setup
cell, so it would have to be weakened until it caught nothing. Instead the
input manifest is `ast.literal_eval`ed out of the code and each path is put
to `git ls-files`, and the import list is read off the AST and held to an
allowlist -- which is what actually makes the notebook offline.
"""

from __future__ import annotations

import ast
import json
import subprocess

import pytest

from tests.unit.submission_gate_helpers import REPO_ROOT, load

common = load("submission_common")

NOTEBOOK = "notebooks/analysis.ipynb"
#: Everything the notebook is allowed to import. `matplotlib` draws, `json`
#: and `pathlib` read tracked files. Nothing here can open a socket.
ALLOWED_IMPORTS = {"json", "pathlib", "matplotlib", "matplotlib.pyplot"}


def _cells() -> list:
    return json.loads((REPO_ROOT / NOTEBOOK).read_text(encoding="utf-8"))["cells"]


def _code() -> str:
    return "\n".join(
        "".join(cell["source"]) for cell in _cells() if cell["cell_type"] == "code"
    )


def _tree() -> ast.Module:
    return ast.parse(_code())


def _inputs() -> dict:
    """The INPUTS manifest, read off the AST rather than re-typed here."""
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "INPUTS"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("the notebook declares no INPUTS manifest")


def test_the_notebook_is_tracked_and_parses():
    assert common.is_tracked(NOTEBOOK), f"{NOTEBOOK} must reach a grader"
    assert len(_cells()) >= 6
    assert _tree().body, "the notebook has no executable code"


def test_every_declared_input_is_tracked_and_is_not_a_local_run_artifact():
    manifest = _inputs()
    assert len(manifest) >= 4, manifest
    for name, path in manifest.items():
        assert not path.startswith(("logs/", "game_artifacts/", "/")), f"{name}: {path}"
        assert common.is_tracked(path), f"{name}: {path} is not in `git ls-files`"


def test_the_notebook_imports_nothing_that_can_reach_a_network():
    imported = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert imported, "no imports found -- the AST walk is looking at nothing"
    assert imported <= ALLOWED_IMPORTS, imported - ALLOWED_IMPORTS


def test_no_credential_is_read_by_name():
    """`os.environ` never appears, so no key can be picked up implicitly."""
    code = _code()
    for forbidden in ("os.environ", "getenv", "API_KEY", "anthropic"):
        assert forbidden not in code, forbidden


def test_the_notebook_executes_end_to_end_offline(tmp_path):
    """The acceptance itself: `nbconvert --execute` exits 0.

    Slow (tens of seconds) because it starts a kernel and renders three
    figures. It is kept in the suite anyway: every other test here checks
    what the notebook SAYS it does, and only this one checks that it runs.
    Output goes to `tmp_path` so a run never dirties the committed file.
    """
    pytest.importorskip("nbconvert")
    completed = subprocess.run(
        ["uv", "run", "jupyter", "nbconvert", "--to", "notebook", "--execute",
         "--output-dir", str(tmp_path), "--output", "executed.ipynb", NOTEBOOK],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=900,
    )
    assert completed.returncode == 0, completed.stderr[-3000:]
    executed = json.loads((tmp_path / "executed.ipynb").read_text(encoding="utf-8"))
    figures = [
        output for cell in executed["cells"] for output in cell.get("outputs", [])
        if "image/png" in output.get("data", {})
    ]
    assert len(figures) >= 3, f"expected a figure per analysis section, got {len(figures)}"
