"""Shared utilities — pure library importable by both cop and thief processes."""

#: Sec14 professional packaging. This package imports nothing, so `__all__`
#: declares its SUBMODULE INVENTORY -- the documented meaning of `__all__` on a
#: package. Derived from the tracked tree and re-derived on every run by
#: `tests/unit/test_package_exports.py`, so a module added here without being
#: exported, or exported after being deleted, fails that test rather than
#: leaving a decorative list behind.
__all__ = (
    "absent", "belief_config", "belief_keys", "belief_toggle_config", "board",
    "config", "deception_config", "deception_types", "directions", "display_config",
    "durable_write", "gatekeeper_params", "hint_guard", "hint_likelihood_config",
    "inference", "language_config", "language_model_config", "league_config",
    "league_config_fields", "loader_helpers", "network_config", "outcome",
    "reliability_config", "reporting_config", "reporting_config_fields",
    "resolution", "roles", "scent_config", "scent_kernel",
    "scent_likelihood_config", "security_config", "state", "strategy_config",
    "strategy_schema", "tunnel_config", "version",
)
