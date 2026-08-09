"""TunnelManager.ensure_connected()/stop() suite -- the other half of
test_tunnel_manager.py. Split at the 150-code-line gate, not by test
meaning (see that module's docstring). Shared fakes and helpers
(FakeProcess/RecordingConnect/make_manager/set_tunnel_env) are defined once
there (QUAL-02) and imported here.
"""

import pytest

from tests.unit.test_tunnel_manager import (
    NETWORK_PARAMS,
    FakeProcess,
    RecordingConnect,
    RecordingSleep,
    make_manager,
    set_tunnel_env,
)


def test_ensure_connected_skips_reconnect_when_already_healthy() -> None:
    connect = RecordingConnect()
    sleep = RecordingSleep()
    mgr = make_manager(connect=connect, get_process=lambda: FakeProcess(healthy=True), sleep=sleep)

    assert mgr.ensure_connected() is True
    assert connect.calls == []
    assert sleep.calls == []


def test_ensure_connected_retries_exactly_retry_count_when_persistently_unhealthy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_tunnel_env(monkeypatch)
    connect = RecordingConnect()
    sleep = RecordingSleep()
    mgr = make_manager(
        connect=connect, get_process=lambda: FakeProcess(healthy=False), sleep=sleep
    )

    assert mgr.ensure_connected() is False
    assert len(connect.calls) == NETWORK_PARAMS.retry_count
    assert sleep.calls == [NETWORK_PARAMS.backoff_seconds] * NETWORK_PARAMS.retry_count


def test_ensure_connected_reconnects_to_the_same_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    set_tunnel_env(monkeypatch, domain="steady.ngrok-free.app")
    connect = RecordingConnect()
    mgr = make_manager(connect=connect, get_process=lambda: FakeProcess(healthy=False))

    mgr.ensure_connected()

    domains = {domain for _port, domain in connect.calls}
    assert domains == {"steady.ngrok-free.app"}


def test_ensure_connected_stops_early_once_healthy_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_tunnel_env(monkeypatch)
    connect = RecordingConnect()
    healthy_calls = {"n": 0}

    def get_process():
        healthy_calls["n"] += 1
        return FakeProcess(healthy=healthy_calls["n"] > 1)

    mgr = make_manager(connect=connect, get_process=get_process)

    assert mgr.ensure_connected() is True
    assert len(connect.calls) == 1


def test_stop_calls_disconnect_then_kill_once_each() -> None:
    order: list[str] = []
    mgr = make_manager(
        disconnect=lambda url: order.append(f"disconnect:{url}"),
        kill=lambda: order.append("kill"),
    )
    mgr.public_url = "https://peer.ngrok-free.app"

    mgr.stop()

    assert order == ["disconnect:https://peer.ngrok-free.app", "kill"]


def test_stop_twice_is_safe() -> None:
    calls = {"disconnect": 0, "kill": 0}
    mgr = make_manager(
        disconnect=lambda url: calls.__setitem__("disconnect", calls["disconnect"] + 1),
        kill=lambda: calls.__setitem__("kill", calls["kill"] + 1),
    )
    mgr.public_url = "https://peer.ngrok-free.app"

    mgr.stop()
    mgr.stop()

    assert calls == {"disconnect": 1, "kill": 1}


def test_stop_without_a_url_still_kills() -> None:
    calls = []
    mgr = make_manager(
        disconnect=lambda url: calls.append(("disconnect", url)),
        kill=lambda: calls.append(("kill",)),
    )

    mgr.stop()

    assert calls == [("kill",)]
