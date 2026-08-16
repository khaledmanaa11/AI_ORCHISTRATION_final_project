"""run_with_tunnel() watch-task LIFECYCLE suite (05-11, CLOUD-01, D-55) --
the other half of test_tunnel_wiring_monitor.py, split at the 150-code-line
gate, not by test meaning (that file measured 157 with these cases in; same
precedent as test_tunnel_manager_reconnect.py). Shared config fixtures are
imported from the monitor file (QUAL-02), never re-derived.
"""

import asyncio

from pursuit.network import tunnel_wiring
from tests.unit.test_tunnel_wiring_monitor import _NETWORK_PARAMS, _TUNNEL_PARAMS

# Test scaffolding only, NOT a PARAMETERS.md value: a "sleep forever"
# sentinel the teardown cancels long before it could ever elapse.
_NEVER_SECONDS = 3600


class _LifecycleTunnel:
    params = _TUNNEL_PARAMS
    network_params = _NETWORK_PARAMS
    public_url = "https://peer.ngrok-free.app"

    def __init__(self, order: list[str]) -> None:
        self._order = order

    def start(self):
        self._order.append("start")

    def stop(self):
        self._order.append("stop")


async def test_run_with_tunnel_watch_lives_exactly_as_long_as_body() -> None:
    order: list[str] = []

    async def fake_monitor(tunnel):
        order.append("watch-start")
        try:
            await asyncio.sleep(_NEVER_SECONDS)
        except asyncio.CancelledError:
            order.append("watch-cancelled")
            raise

    async def body():
        await asyncio.sleep(0)  # yield once so the watch task gets scheduled
        order.append("body")
        return "ok"

    result = await tunnel_wiring.run_with_tunnel(
        _LifecycleTunnel(order), body, monitor=fake_monitor
    )

    assert result == "ok"
    assert order == ["start", "watch-start", "body", "watch-cancelled", "stop"]


async def test_run_with_tunnel_survives_a_watch_that_already_gave_up() -> None:
    """An exhausted watch returns before body ends -- teardown's cancel is a
    no-op on a finished task and the game result is untouched."""
    order: list[str] = []

    async def fake_monitor(tunnel):
        order.append("watch-done")

    async def body():
        await asyncio.sleep(0)
        return "ok"

    result = await tunnel_wiring.run_with_tunnel(
        _LifecycleTunnel(order), body, monitor=fake_monitor
    )

    assert result == "ok"
    assert order == ["start", "watch-done", "stop"]


async def test_run_with_tunnel_survives_a_watch_that_died_raising(capsys) -> None:
    """A watch bug must never mask a resolved game or skip the teardown --
    the contained-print + unconditional stop() shape (05-11)."""
    order: list[str] = []

    async def dying_monitor(tunnel):
        raise RuntimeError("watch bug")

    async def body():
        await asyncio.sleep(0)
        return "ok"

    result = await tunnel_wiring.run_with_tunnel(
        _LifecycleTunnel(order), body, monitor=dying_monitor
    )

    assert result == "ok"
    assert order == ["start", "stop"]
    assert tunnel_wiring.TUNNEL_WATCH_ERROR_LINE in capsys.readouterr().out


async def test_run_with_tunnel_none_starts_no_watch() -> None:
    """tunnel-off (every loopback test and dev flow): no task, no monitor."""

    async def exploding_monitor(tunnel):  # pragma: no cover - must never run
        raise AssertionError("no watch may start when tunnel is None")

    async def body():
        return "ok"

    result = await tunnel_wiring.run_with_tunnel(None, body, monitor=exploding_monitor)
    assert result == "ok"
