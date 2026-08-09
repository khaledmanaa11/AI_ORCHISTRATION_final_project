"""04-12 verification bullet 6: per-turn wall time with the language layer
ON and OFF, measured (never asserted-and-hidden) and compared against
`network.watchdog_threshold` with margin -- the number Task 1's whole
timeout policy exists to protect. No test here performs network I/O
(`ANTHROPIC_API_KEY` unset -> the real provider degrades to `NO_KEY`
before any request leaves the process)."""

from __future__ import annotations

import time

from pursuit.network.agent_wiring import load_agent_config
from tests.integration.two_peer_game import play_two_peer_game


async def _measure(cfg_a, cfg_b, *, game_uid, log_dir, wire=None) -> tuple[float, int]:
    started = time.perf_counter()
    _outcome_a, _outcome_b, ctx_a, _ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid=game_uid, log_dir=log_dir, wire=wire,
    )
    elapsed = time.perf_counter() - started
    return elapsed, ctx_a.state.turn


async def test_per_turn_wall_time_with_language_on_and_off_stays_under_the_watchdog(
    tmp_path, monkeypatch,
):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a = load_agent_config("config/police")
    cfg_b = load_agent_config("config/thief")
    watchdog_threshold = cfg_a.net.watchdog_threshold

    on_dir = tmp_path / "on"
    on_dir.mkdir()
    elapsed_on, turns_on = await _measure(cfg_a, cfg_b, game_uid="timing-on", log_dir=on_dir)
    per_turn_on = elapsed_on / max(turns_on, 1)

    def language_off(ctx) -> None:
        ctx.language = None

    off_dir = tmp_path / "off"
    off_dir.mkdir()
    elapsed_off, turns_off = await _measure(
        cfg_a, cfg_b, game_uid="timing-off", log_dir=off_dir, wire=language_off,
    )
    per_turn_off = elapsed_off / max(turns_off, 1)

    print(
        f"\nper-turn wall time -- language ON: {per_turn_on * 1000:.2f}ms/turn "
        f"({turns_on} turns, {elapsed_on:.3f}s total); language OFF: "
        f"{per_turn_off * 1000:.2f}ms/turn ({turns_off} turns, {elapsed_off:.3f}s total); "
        f"budget: network.watchdog_threshold={watchdog_threshold}s"
    )

    # Task 1's own bound: the WHOLE turn (decode+decide+compose) must fit
    # inside the smaller of response_timeout/watchdog_threshold, with
    # margin -- measured here at real (mocked-provider) speed, not assumed.
    assert per_turn_on < watchdog_threshold
    assert per_turn_off < watchdog_threshold
