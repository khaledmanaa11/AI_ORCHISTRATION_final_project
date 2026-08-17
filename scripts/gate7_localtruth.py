"""Sec10.4 criterion 2 -- the live GUI displays state, and ONLY local truth.

Three measurements, none of which is sufficient alone:

1. The rules 8-9 structural gate (`scripts/check_local_truth.py`) over the
   REAL shipped `src/pursuit/gui/`, recording BOTH the violation count AND the
   module count. A zero/zero result is a FAIL: a gate that judged nothing is
   worse than no gate, which is why this script also drives the gate's own
   empty-scan control and records exit code 2 for it.
2. The PUBLISHED SNAPSHOT of a real game, scanned for the three field names
   that would carry the objective board (`TRUE_POSITION_FIELDS`). The live
   process is fed by this file and by nothing else (D-76), so the file IS the
   attack surface.
3. The shipped entry point launched as a SUBPROCESS, exit code recorded.
   Never a module-scope `import pursuit.gui.live_app`: `tkinter.Tk()` raises
   on a machine with no display, and one criterion's environment must not be
   able to fail the whole gate.

WHAT THIS CANNOT MEASURE, STATED SO NO CLEAN VERDICT IS MISTAKEN FOR ONE.
Whether a HUMAN could invert the true cell out of what a panel PAINTS is asked
by `tests/unit/test_gui_recovery.py` and `tests/unit/test_local_truth_recovery.py`
(07-11's runtime recovery work), and whether the screenshot is
presentation-grade is 07-10's aesthetic call. Neither is a number.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from gate7_common import REPO_ROOT

from pursuit.sdk.view_publish import snapshot_path_for

GATE_SCRIPT = REPO_ROOT / "scripts" / "check_local_truth.py"
GUI_ROOT = REPO_ROOT / "src" / "pursuit" / "gui"
LIVE_APP_MODULE = "pursuit.gui.live_app"

#: The interval THIS MEASUREMENT was taken with. OQ-6: no document in this
#: project states a UI refresh interval, so nothing under `src/` carries one
#: and `--refresh-ms` is required with no default. The operator states it; this
#: script is an operator, and it states it here rather than in the repository.
GATE_REFRESH_MS = 500


def _load_gate():
    """The CI gate itself, loaded BY FILE PATH -- the same loader
    `tests/unit/local_truth_helpers.py` uses, so the suite, the CI job and this
    measurement all run ONE copy of the logic."""
    spec = importlib.util.spec_from_file_location("check_local_truth", GATE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _empty_scan_control(gate, tmp: Path) -> dict:
    """The gate must be LOUD about having judged nothing, in both its forms."""
    missing = tmp / "does-not-exist"
    marker_only = tmp / "marker-only"
    marker_only.mkdir(parents=True, exist_ok=True)
    (marker_only / "__init__.py").write_text('"""Bare package marker."""\n', encoding="utf-8")
    return {
        "missing_root_exit_code": int(gate.main(missing)),
        "package_marker_only_exit_code": int(gate.main(marker_only)),
        "expected_exit_code": int(gate.ExitCode.EMPTY_SCAN),
    }


def _names_in(payload: object, fields: tuple[str, ...]) -> list[str]:
    """Every one of `fields` used as a KEY anywhere in the published tree."""
    found: list[str] = []
    if isinstance(payload, dict):
        found.extend(key for key in payload if key in fields)
        for value in payload.values():
            found.extend(_names_in(value, fields))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_names_in(item, fields))
    return found


def _snapshot_evidence(ctx: object, gate) -> dict:
    path = snapshot_path_for(ctx.log_path)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return {
        "published": payload is not None,
        "top_level_keys": sorted(payload) if isinstance(payload, dict) else [],
        "true_position_fields_present": _names_in(payload, gate.TRUE_POSITION_FIELDS),
        "own_cell": payload.get("own_cell") if isinstance(payload, dict) else None,
    }


def _launch(ctx: object) -> dict:
    """`python -m pursuit.gui.live_app --once` against this seat's snapshot."""
    argv = [
        sys.executable, "-m", LIVE_APP_MODULE,
        "--snapshot", str(snapshot_path_for(ctx.log_path)),
        "--refresh-ms", str(GATE_REFRESH_MS), "--once",
    ]
    completed = subprocess.run(
        argv, cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return {
        "returncode": completed.returncode,
        "refresh_ms": GATE_REFRESH_MS,
        "stderr_tail": completed.stderr.strip().splitlines()[-1:] or [],
    }


def measure_local_truth(game: object, tmp: Path) -> dict:
    """Criterion 2's evidence, joined to criterion 3 by `game_uid`."""
    gate = _load_gate()
    modules = [path.name for path in gate.gui_module_paths(GUI_ROOT)]
    violations = gate.find_violations(GUI_ROOT)
    return {
        "game_uid": game.uid,
        "structural_gate": {
            "modules_scanned": len(modules),
            "module_names": sorted(modules),
            "violation_count": len(violations),
            "violations": violations,
            "exit_code": int(gate.main(GUI_ROOT)),
            "allowed_service_modules": list(gate.ALLOWED_SERVICE_MODULES),
        },
        "empty_scan_control": _empty_scan_control(gate, tmp),
        "published_snapshot": {
            "police": _snapshot_evidence(game.ctx_police, gate),
            "thief": _snapshot_evidence(game.ctx_thief, gate),
            "true_position_fields": list(gate.TRUE_POSITION_FIELDS),
        },
        "live_app_launch": {
            "police": _launch(game.ctx_police),
            "thief": _launch(game.ctx_thief),
        },
        "not_measured_here": (
            "whether a human could INVERT the true cell out of what a panel paints "
            "(tests/unit/test_gui_recovery.py, tests/unit/test_local_truth_recovery.py), "
            "and whether the README screenshot is presentation-grade (07-10)"
        ),
    }
