"""Tests for secret_wiring.resolve_shared_secret (D-56). Added beyond
05-02-PLAN.md's own literal `files_modified` list per CLAUDE.md's "every
module gets a test file" rule (04-03-SUMMARY.md / 05-01-SUMMARY.md
precedent) -- this module was split out of agent_wiring.py at the
150-code-line gate.
"""

from pursuit.network import secret_wiring
from pursuit.shared.tunnel_config import load_tunnel_config

_TUNNEL_PARAMS = load_tunnel_config("config/police/tunnel.json")


def test_none_when_tunnel_file_absent(tmp_path) -> None:
    """Tunnel-off default: an agent config dir with no tunnel.json at all."""
    assert secret_wiring.resolve_shared_secret(tmp_path) is None


def test_none_when_secret_env_unset(monkeypatch) -> None:
    """The file exists but the secret env var doesn't -- every existing
    loopback test and dev flow lands exactly here."""
    monkeypatch.delenv(_TUNNEL_PARAMS.secret_env, raising=False)
    assert secret_wiring.resolve_shared_secret("config/police") is None


def test_returns_header_and_value_when_secret_env_set(monkeypatch) -> None:
    monkeypatch.setenv(_TUNNEL_PARAMS.secret_env, "s3cr3t-value")
    result = secret_wiring.resolve_shared_secret("config/police")
    assert result == (_TUNNEL_PARAMS.secret_header, "s3cr3t-value")


def test_is_independent_of_the_domain_env_var(monkeypatch) -> None:
    """D-56 is orthogonal to D-54/D-55's tunnel lifecycle: the secret can be
    resolved even when the tunnel's own opt-in var is unset."""
    monkeypatch.delenv(_TUNNEL_PARAMS.domain_env, raising=False)
    monkeypatch.setenv(_TUNNEL_PARAMS.secret_env, "s3cr3t-value")
    result = secret_wiring.resolve_shared_secret("config/police")
    assert result == (_TUNNEL_PARAMS.secret_header, "s3cr3t-value")
