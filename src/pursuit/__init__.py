"""Pursuit — cops-and-robbers game engine package."""

from pursuit.shared.version import VERSION

#: Sec14 professional packaging: the distribution version, exposed where a
#: consumer looks for it. RE-EXPORTED, never re-typed -- `shared/version.py` is
#: the single source Table 5's "versioning starts at 1.00" row is measured
#: against, and a second literal here would be a value that can drift from the
#: one the gate reads. `tests/unit/test_package_version.py` asserts both halves:
#: that the two agree, and that no version literal is written in this file.
__version__ = VERSION

#: Sec14 professional packaging. This package imports nothing, so `__all__`
#: declares its SUBMODULE INVENTORY -- the documented meaning of `__all__` on a
#: package. Derived from the tracked tree and re-derived on every run by
#: `tests/unit/test_package_exports.py`, so a module added here without being
#: exported, or exported after being deleted, fails that test rather than
#: leaving a decorative list behind.
__all__ = (
    "config_keys", "constants", "gui", "main", "network", "sdk", "security",
    "services", "shared", "strategy",
)
