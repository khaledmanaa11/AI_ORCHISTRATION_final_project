"""`scripts/check_local_truth.py`: the structural half of the rules 8-9
firewall, and the vacuity it must refuse.

Loaded BY FILE PATH, the `test_strategy_pluggable.py` pattern, so the pytest
suite and the CI job are proven to run the SAME logic rather than two copies
of it (QUAL-02).

The load-bearing case is the EMPTY SCAN. `src/pursuit/gui/` does not exist
until 07-06, and the mould this script copies (`check_no_llm_in_strategy.py`)
would return `[]` from `rglob` over a missing root, find no violations, and
print OK -- a gate that reports success for having looked at nothing. That
failure mode is pinned here in both its forms: a root that does not exist,
and a root that exists with zero modules in it.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

_SCRIPT = pathlib.Path(__file__).parents[2] / "scripts" / "check_local_truth.py"

_LEAKY_MODULES = {
    "imports_engine.py": "from pursuit.sdk import engine\n",
    "imports_state.py": "from pursuit.shared.state import GameState\n",
    "imports_network.py": "from pursuit.network.orchestrator import AgentContext\n",
    "reads_thief.py": "def render(ctx):\n    return ctx.state.thief\n",
    "reads_cop.py": "def render(self):\n    return self.ctx.state.cop\n",
    "reads_barriers.py": "def render(ctx):\n    return ctx.state.barriers\n",
    "imports_llm.py": "from pursuit.services.llm.gatekeeper import Gatekeeper\n",
}

_CLEAN_MODULE = (
    "from pursuit.sdk.local_view import LocalView\n"
    "from pursuit.services.reporting.replay_verify import verify\n"
    "def render(view: LocalView):\n"
    "    return view.own_cell, view.machine_state, verify\n"
)


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


def test_a_missing_root_is_an_error_not_an_ok(tmp_path, capsys):
    """The vacuity that would otherwise ship: `src/pursuit/gui/` does not
    exist until 07-06."""
    check = _check()
    missing = tmp_path / "gui"
    with pytest.raises(check.EmptyScanError):
        check.find_violations(root=missing)
    assert check.main(root=missing) == check.ExitCode.EMPTY_SCAN
    out = capsys.readouterr().out
    assert "ERROR" in out and str(missing) in out
    assert "OK" not in out


def test_a_root_with_zero_modules_is_also_an_error(tmp_path, capsys):
    check = _check()
    empty = tmp_path / "gui"
    empty.mkdir()
    assert check.main(root=empty) == check.ExitCode.EMPTY_SCAN
    assert "ERROR" in capsys.readouterr().out


def test_every_leaky_module_is_reported(tmp_path):
    check = _check()
    assert len(_LEAKY_MODULES) == 7, "a thinned module set would prove less"
    root = _tree(tmp_path / "gui", _LEAKY_MODULES)
    violations = check.find_violations(root=root)
    # ": " and not ":" -- a Windows path starts "C:\", which `split(":")` eats.
    reported = {pathlib.Path(v.split(": ")[0]).name for v in violations}
    assert reported == set(_LEAKY_MODULES), f"missed: {set(_LEAKY_MODULES) - reported}"


def test_a_clean_tree_passes_and_prints_the_module_count(tmp_path, capsys):
    """The counter-control for the gate: it does not simply always report."""
    check = _check()
    root = _tree(tmp_path / "gui", {"live_panels.py": _CLEAN_MODULE})
    assert check.find_violations(root=root) == []
    assert check.main(root=root) == check.ExitCode.OK
    out = capsys.readouterr().out
    assert "OK" in out and "1 module" in out


def test_violations_exit_non_zero_and_are_printed(tmp_path, capsys):
    check = _check()
    root = _tree(tmp_path / "gui", {"reads_thief.py": _LEAKY_MODULES["reads_thief.py"]})
    assert check.main(root=root) == check.ExitCode.VIOLATIONS
    out = capsys.readouterr().out
    assert "VIOLATION" in out and "reads_thief.py" in out


def test_the_services_allowlist_is_explicit_and_non_empty(tmp_path):
    """A gate whose allowlist silently emptied would flag the replay
    viewer's own verification path; one that silently grew would let the
    mail sink into a view."""
    check = _check()
    assert check.ALLOWED_SERVICE_MODULES, "an empty allowlist is not a decision"
    for allowed in check.ALLOWED_SERVICE_MODULES:
        assert allowed.startswith("pursuit.services.")
    root = _tree(tmp_path / "gui", {"replay.py": _CLEAN_MODULE})
    assert check.find_violations(root=root) == []


def test_the_gate_is_wired_to_the_real_gui_package():
    """The root is not a stray path: 07-06 creates exactly this package."""
    check = _check()
    assert check.GUI_ROOT.as_posix().endswith("src/pursuit/gui")
    assert check.GUI_ROOT.parent.is_dir()


def test_nested_gui_subpackages_are_scanned(tmp_path):
    check = _check()
    root = tmp_path / "gui"
    _tree(root / "panels", {"reads_cop.py": _LEAKY_MODULES["reads_cop.py"]})
    assert len(check.gui_module_paths(root=root)) == 1
    assert len(check.find_violations(root=root)) == 1
