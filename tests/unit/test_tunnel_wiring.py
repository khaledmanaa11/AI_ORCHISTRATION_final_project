"""Tests for tunnel_wiring.py -- build_tunnel_manager, exchange_block,
run_with_tunnel (CLOUD-01). Added beyond 05-01-PLAN.md's own literal
`files_modified` list per CLAUDE.md's "every module gets a test file"
testing rule (04-03-SUMMARY.md precedent) -- this module was split out of
agent_lifecycle.py at the 150-code-line gate, itself authorised by the
plan's own Task 3 text.
"""

import pytest

from pursuit.network import tunnel_wiring
from pursuit.network.tunnel_manager import TunnelManager
from pursuit.shared.network_config import load_network_config
from pursuit.shared.tunnel_config import load_tunnel_config

_TUNNEL_PARAMS = load_tunnel_config("config/police/tunnel.json")
_NETWORK_PARAMS = load_network_config("config/police/network.json")


def test_build_tunnel_manager_none_when_tunnel_file_absent(tmp_path) -> None:
    """Tunnel-off default: an agent config dir with no tunnel.json at all."""
    assert tunnel_wiring.build_tunnel_manager(tmp_path, _NETWORK_PARAMS) is None


def test_build_tunnel_manager_none_when_domain_env_unset(monkeypatch) -> None:
    """Tunnel-off default: the file exists but the opt-in signal doesn't --
    every existing loopback test and dev flow lands exactly here."""
    monkeypatch.delenv(_TUNNEL_PARAMS.domain_env, raising=False)
    assert tunnel_wiring.build_tunnel_manager("config/police", _NETWORK_PARAMS) is None


def test_build_tunnel_manager_returns_a_manager_when_opted_in(monkeypatch) -> None:
    monkeypatch.setenv(_TUNNEL_PARAMS.domain_env, "peer.ngrok-free.app")
    mgr = tunnel_wiring.build_tunnel_manager("config/police", _NETWORK_PARAMS)
    assert isinstance(mgr, TunnelManager)
    assert mgr.params == _TUNNEL_PARAMS


def test_exchange_block_carries_the_url_and_env_name_never_a_secret_value() -> None:
    block = tunnel_wiring.exchange_block("https://peer.ngrok-free.app", _TUNNEL_PARAMS)
    assert "https://peer.ngrok-free.app" in block
    assert _TUNNEL_PARAMS.secret_env in block
    assert _TUNNEL_PARAMS.secret_header in block


async def test_run_with_tunnel_none_runs_body_directly() -> None:
    """tunnel=None -- the test/dev default -- is a transparent pass-through."""
    calls = []

    async def body():
        calls.append("body")
        return "ok"

    result = await tunnel_wiring.run_with_tunnel(None, body)
    assert result == "ok"
    assert calls == ["body"]


async def test_run_with_tunnel_starts_before_body_and_stops_after(capsys) -> None:
    order = []

    class _FakeTunnel:
        public_url = "https://peer.ngrok-free.app"
        params = _TUNNEL_PARAMS

        def start(self):
            order.append("start")

        def stop(self):
            order.append("stop")

    async def body():
        order.append("body")
        return "ok"

    result = await tunnel_wiring.run_with_tunnel(_FakeTunnel(), body)

    assert order == ["start", "body", "stop"]
    assert result == "ok"
    assert "https://peer.ngrok-free.app" in capsys.readouterr().out


async def test_run_with_tunnel_start_failure_aborts_before_body() -> None:
    """A tunnel that fails to start must abort BEFORE the runtime/handshake
    -- a peer that would play unreachable must never begin the game."""

    class _FailingTunnel:
        params = _TUNNEL_PARAMS

        def start(self):
            raise RuntimeError("auth failed")

        def stop(self):
            raise AssertionError("stop must not run when start never succeeded")

    called = []

    async def body():
        called.append(True)
        return None

    with pytest.raises(RuntimeError, match="auth failed"):
        await tunnel_wiring.run_with_tunnel(_FailingTunnel(), body)
    assert called == []


async def test_run_with_tunnel_stops_even_when_body_raises() -> None:
    order = []

    class _FakeTunnel:
        public_url = "https://peer.ngrok-free.app"
        params = _TUNNEL_PARAMS

        def start(self):
            order.append("start")

        def stop(self):
            order.append("stop")

    async def body():
        order.append("body")
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await tunnel_wiring.run_with_tunnel(_FakeTunnel(), body)
    assert order == ["start", "body", "stop"]
