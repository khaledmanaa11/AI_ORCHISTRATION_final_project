"""SDK layer — all game logic is exposed through this package."""

#: Sec14 professional packaging. This package imports nothing, so `__all__`
#: declares its SUBMODULE INVENTORY -- the documented meaning of `__all__` on a
#: package. Derived from the tracked tree and re-derived on every run by
#: `tests/unit/test_package_exports.py`, so a module added here without being
#: exported, or exported after being deleted, fails that test rather than
#: leaving a decorative list behind.
__all__ = (
    "actions", "engine", "local_view", "resolve", "terminal", "view_builder",
    "view_publish", "view_render", "view_snapshot", "view_text",
)
