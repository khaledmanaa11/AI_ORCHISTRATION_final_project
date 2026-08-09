"""Tests for TunnelManager.start()/healthy() and its production defaults
(CLOUD-01, D-54, D-55).

Every pyngrok call is injected as a fake -- zero real processes, zero real
sleeps, zero ngrok.exe (see tunnel_manager.py's own module docstring).

The reconnect (`ensure_connected`) and `stop()` suite lives in
test_tunnel_manager_reconnect.py -- split out at the 150-code-line gate, not
by test meaning. It imports the fakes and `_manager`/`_set_env` helpers
defined here (QUAL-02).
"""

import pytest

from pursuit.network.tunnel_manager import TunnelManager
from pursuit.shared.network_config import load_network_config
from pursuit.shared.tunnel_config import load_tunnel_config

TUNNEL_PARAMS = load_tunnel_config("config/police/tunnel.json")
NETWORK_PARAMS = load_network_config("config/police/network.json")
AUTHTOKEN_ENV = TUNNEL_PARAMS.authtoken_env
DOMAIN_ENV = TUNNEL_PARAMS.domain_env


class FakeTunnel:
    def __init__(self, url: str) -> None:
        self.public_url = url


class FakeProcess:
    def __init__(self, *, healthy: bool) -> None:
        self._healthy = healthy

    def healthy(self) -> bool:
        return self._healthy


class RecordingConnect:
    """Fake ngrok.connect -- records every (port, domain) call, returns a
    fresh fake tunnel each time."""

    def __init__(self, url: str = "https://fake.ngrok-free.app") -> None:
        self.calls: list[tuple[int, str]] = []
        self._url = url

    def __call__(self, port: int, *, domain: str) -> FakeTunnel:
        self.calls.append((port, domain))
        return FakeTunnel(self._url)


class RecordingSleep:
    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def make_manager(*, connect=None, get_process=None, disconnect=None, kill=None, sleep=None):
    return TunnelManager(
        TUNNEL_PARAMS,
        NETWORK_PARAMS,
        connect=connect or RecordingConnect(),
        disconnect=disconnect or (lambda url: None),
        kill=kill or (lambda: None),
        get_process=get_process or (lambda: FakeProcess(healthy=True)),
        sleep=sleep or RecordingSleep(),
        clock=lambda: 0.0,
    )


def set_tunnel_env(monkeypatch: pytest.MonkeyPatch, *, authtoken="tok", domain="peer.ngrok-free.app"):
    if authtoken is None:
        monkeypatch.delenv(AUTHTOKEN_ENV, raising=False)
    else:
        monkeypatch.setenv(AUTHTOKEN_ENV, authtoken)
    if domain is None:
        monkeypatch.delenv(DOMAIN_ENV, raising=False)
    else:
        monkeypatch.setenv(DOMAIN_ENV, domain)


def test_start_stores_the_public_url(monkeypatch: pytest.MonkeyPatch) -> None:
    set_tunnel_env(monkeypatch)
    connect = RecordingConnect("https://peer.ngrok-free.app")
    mgr = make_manager(connect=connect)

    mgr.start()

    assert mgr.public_url == "https://peer.ngrok-free.app"
    assert connect.calls == [(NETWORK_PARAMS.port, "peer.ngrok-free.app")]


def test_start_raises_naming_missing_authtoken(monkeypatch: pytest.MonkeyPatch) -> None:
    set_tunnel_env(monkeypatch, authtoken=None)
    mgr = make_manager()
    with pytest.raises(KeyError, match=AUTHTOKEN_ENV):
        mgr.start()


def test_start_raises_naming_missing_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    set_tunnel_env(monkeypatch, domain=None)
    mgr = make_manager()
    with pytest.raises(KeyError, match=DOMAIN_ENV):
        mgr.start()


def test_start_propagates_the_connect_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    set_tunnel_env(monkeypatch)

    def _boom(port, *, domain):
        raise RuntimeError("domain already taken")

    mgr = make_manager(connect=_boom)
    with pytest.raises(RuntimeError, match="domain already taken"):
        mgr.start()


def test_healthy_wraps_get_process() -> None:
    unhealthy = make_manager(get_process=lambda: FakeProcess(healthy=False))
    assert unhealthy.healthy() is False
    healthy = make_manager(get_process=lambda: FakeProcess(healthy=True))
    assert healthy.healthy() is True


def test_default_callables_bind_the_real_pyngrok_functions() -> None:
    """No injected seams -- confirms the production defaults wire up. Only
    the function objects are referenced/compared here -- nothing is ever
    called, so this never touches a real process or the network."""
    from pyngrok import ngrok

    mgr = TunnelManager(TUNNEL_PARAMS, NETWORK_PARAMS)
    assert mgr._connect is ngrok.connect
    assert mgr._disconnect is ngrok.disconnect
    assert mgr._kill is ngrok.kill
    assert mgr._get_process is ngrok.get_ngrok_process
