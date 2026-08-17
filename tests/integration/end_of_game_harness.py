"""One real two-peer game, its audit, and its real Step-0 declaration --
everything `report_game_end` needs, assembled once.

Not a `test_*.py` module on purpose (the `two_peer_game.py` precedent): pytest
never collects it, so the reporting cases and the watchdog cases share ONE
copy of the setup.

THE STEP-0 DECLARATION IS THE REAL ONE. `declare_step0` runs
`step0_collect.collect_declaration`, which shells out to `git rev-parse HEAD`
-- so the `commit_hash` these tests assert on is the commit the test process
is actually running, not a fixture string. Reading the games-played counter is
all it does to `config/`, and the session guard blocks writes, not reads.
"""

from __future__ import annotations

import asyncio

from pursuit.network.agent_audit_wiring import declare_step0, run_final_audit
from pursuit.network.agent_wiring import load_agent_config
from tests.integration.two_peer_game import play_two_peer_game


class AlwaysFailingSink:
    """A transport that never delivers. Every attempt raises, which is exactly
    what `MailSink`'s contract asks a failing sink to do -- "a sink that
    swallows a failure and returns a receipt anyway would report a delivery
    that never happened"."""

    def __init__(self) -> None:
        self.attempts = 0

    async def send(self, report: dict) -> object:
        self.attempts += 1
        raise RuntimeError("simulated mail transport failure")


async def no_wait(_seconds: float) -> None:
    """`Gatekeeper`'s injected sleep seam, wired to nothing."""
    return None


async def played_seats(tmp_path, monkeypatch, uid):
    """A finished, audited game, from BOTH seats.

    Returns `[(cfg, ctx, outcome, declaration_envelope), ...]` -- police
    first -- i.e. what each of the two `agent_entrypoint.run_agent` processes
    holds at the moment it calls the hook. Both seats are needed because they
    share a repository, and therefore a configured artifact directory.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid=uid, log_dir=tmp_path,
    )
    assert outcome_a is not None and outcome_a == outcome_b
    await asyncio.gather(
        run_final_audit(ctx_a, board_outcome=outcome_a),
        run_final_audit(ctx_b, board_outcome=outcome_b),
    )
    envelopes = [(await declare_step0(cfg))[1] for cfg in (cfg_a, cfg_b)]
    return [
        (cfg_a, ctx_a, outcome_a, envelopes[0]),
        (cfg_b, ctx_b, outcome_b, envelopes[1]),
    ]


async def played_game(tmp_path, monkeypatch, uid):
    """The police seat of `played_seats` -- the four things one process holds."""
    return (await played_seats(tmp_path, monkeypatch, uid))[0]
