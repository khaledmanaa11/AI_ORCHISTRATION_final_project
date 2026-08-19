"""The live dashboard: one window per agent PROCESS (D-76).

NOTHING IN THIS PACKAGE MAY DERIVE ANYTHING, and the reason is measured
rather than stylistic. `pyproject.toml:38` omits `*/gui/*` from coverage, so
a mapping placed here -- what colour a cell takes, how a probability becomes
a shade, how a timer is formatted -- would be untested AND invisible to the
`fail_under = 85` gate, and would look exactly like a gate that had passed.
Every derivation therefore lives in `pursuit.sdk.view_render` /
`pursuit.sdk.view_text`, and the modules here construct widgets and read
attributes. Nothing may be parked in `scripts/` either:
`scripts/check_line_limit.sh:18` enumerates `src/** tests/** training/**` and
`pyproject.toml:37` sets `source = ["src", "training"]`, so that directory
escapes BOTH gates.

NOTHING HERE MAY REACH THE OBJECTIVE BOARD STATE (rules 8-9; rule 9's
sanction is project disqualification). This process is fed by a published
`LocalView` snapshot and cannot hold the live agent context, or the true
joint position on it, at all -- that is the whole point of D-76's separate
process, and `scripts/check_local_truth.py` enforces it over every module in
this package on every CI run. The four forbidden spellings are deliberately
absent from this package even as PROSE, so the plan's own grep over `gui/` is
clean without anyone having to read past a docstring to decide.

Entry point::

    uv run python -m pursuit.gui.live_app --snapshot logs/police/<uid>.view.json --refresh-ms <N>
"""

#: Sec14 professional packaging. This package imports nothing, so `__all__`
#: declares its SUBMODULE INVENTORY -- the documented meaning of `__all__` on a
#: package. Derived from the tracked tree and re-derived on every run by
#: `tests/unit/test_package_exports.py`, so a module added here without being
#: exported, or exported after being deleted, fails that test rather than
#: leaving a decorative list behind.
__all__ = (
    "live_app", "live_panels", "live_sidebar", "replay_app", "replay_panels",
    "replay_viewer", "widgets",
)
