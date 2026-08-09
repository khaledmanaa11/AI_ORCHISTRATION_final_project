"""D-66/SEC-07: a forced cop barrier placement travels over the wire inside
the committed action for the first time, round-trips identically on both
engines, and respects the quota. Split from `test_commit_reveal_protocol.py`
at the 150-code-line gate.
"""

from __future__ import annotations

import json

from pursuit.constants import MoveSource
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.brain_wiring import inner_brain
from pursuit.sdk.actions import barrier_cells
from pursuit.strategy.base import Decision
from tests.integration.two_peer_game import play_two_peer_game


class _OneShotBarrierBrain:
    """A raw (non-`BeliefAdapter`) brain: on its FIRST `_decide_move` call
    only, places a barrier instead of delegating -- D-66's own note that
    the `ctx.choose_move` override seam never carries a barrier, so a raw
    `_decide_move` implementation is the only path that can script one.
    Every later call delegates to the game's REAL underlying `BrainBase`
    (unwrapped via `inner_brain`, since the real brain may itself be
    `BeliefAdapter`-wrapped, which has no `_decide_move`), so the game
    still finishes normally on legal moves."""

    def __init__(self, real_brain, params):
        self._real = inner_brain(real_brain)
        self._params = params
        self._fired = False

    def _decide_move(self, obs, state):  # noqa: ARG002 -- BrainBase's own seam
        if not self._fired:
            self._fired = True
            cell = barrier_cells(state, self._params)[0]
            return Decision(move=obs.own_cell, source=MoveSource.HEURISTIC, barrier=cell)
        return self._real._decide_move(obs, state)  # noqa: SLF001


def _wire_forced_barrier(ctx) -> None:
    if ctx.role == "police":
        ctx.brain = _OneShotBarrierBrain(ctx.brain, ctx.params)


async def test_forced_cop_barrier_round_trips_identically_on_both_engines(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")

    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid="commit-reveal-barrier", log_dir=tmp_path, wire=_wire_forced_barrier,
    )
    assert outcome_a is not None and outcome_a == outcome_b

    events_a = [
        json.loads(line) for line in (tmp_path / "a.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    barrier_reveals = [
        r for r in events_a
        if r["event"] == "message_sent"
        and r.get("envelope", {}).get("type") == "reveal"
        and r["envelope"]["payload"].get("barrier") is not None
    ]
    assert barrier_reveals, "the forced barrier turn never produced a barrier-bearing REVEAL"
    assert barrier_reveals[0]["envelope"]["payload"]["move"] == {"kind": "move", "direction": "stay"}

    # Both sides independently resolved the SAME barrier cell and count --
    # the receiver's own move_payload.decode/is_legal(BARRIER) branch
    # accepted it, never silently dropped it (SEC-07's substance).
    assert ctx_a.state.barriers == ctx_b.state.barriers
    assert ctx_a.state.barriers_placed == ctx_b.state.barriers_placed
    assert ctx_a.state.barriers_placed >= 1
    assert ctx_a.state.barriers_placed <= cfg_a.params.barrier_quota
