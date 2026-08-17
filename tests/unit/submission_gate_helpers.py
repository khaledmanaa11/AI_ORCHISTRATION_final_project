"""Loader for the `scripts/submission_*.py` audit modules (08-01).

Loaded BY PATH, the `local_truth_helpers.load_gate` pattern, so the pytest suite
and the CLI a grader runs are proven to exercise the SAME code rather than two
copies of it (QUAL-02). `scripts/` is on neither the coverage `source` list nor
`check_line_limit.sh`'s glob, so without these tests the audit would be the one
piece of logic in the repository nothing measures -- which is exactly the trap
the 08 outline names.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def load(module_name: str):
    """Import `scripts/<module_name>.py` under its own name.

    `scripts/` is prepended to `sys.path` because these modules import each
    other flatly (`from submission_common import ...`), the same bootstrap
    `check_submission.py` performs for itself.
    """
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = SCRIPTS / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
