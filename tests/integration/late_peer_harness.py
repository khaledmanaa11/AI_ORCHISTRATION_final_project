"""05-UAT.md G1 missing[4]: the SEQUENCED two-peer harness, split from
`test_late_peer_teardown.py` at the 150-code-line gate (test files obey it
too). Not a `test_*.py` file on purpose -- pytest never collects it as a
test module (the `tests/unit/_fakes_agent.py` precedent).

Why a new harness at all. `test_step0_and_audit.py:100` runs both turn
loops in ONE `asyncio.gather` over in-memory `Client(server)` transports
and never tears anything down, so it cannot express a staggered or
torn-down peer at all -- structurally the reason nothing caught the bug
that cost the 2026-08-13 round. This harness instead (a) binds REAL
loopback sockets, so `stop_runtime` genuinely closes a listener the peer is
still talking to, and (b) sequences the two sides instead of gathering
them.

What keeps it from testing a fiction. There is no in-process path to two
`run_agent`s playing each other: `default_context` binds a real
`PeerRuntime` to `cfg.net.host`/`port` with no hook to swap
`ctx.runtime.client`, and `scripts/dev_launch.py` uses `subprocess.Popen`,
not coroutines. So this harness performs the three teardown steps itself,
paired the way 05-05 pairs adoption proofs: THIS file proves the sequence
behaves correctly, and `test_agent_entrypoint.py`'s exact `order == [...]`
lists prove `run_agent` really performs those same three NAMED steps in
that order. Neither alone is enough; together they are. If the two ever
diverge, one of them is wrong -- that is a finding, not a merge conflict.

The watchdog is deliberately NOT started here: a real `Watchdog`'s default
exit action is `os._exit(1)`, which would kill the pytest process. Its
NET-07 property is proven in `tests/unit/test_agent_teardown.py` against an
INJECTED exit_action instead -- and, since 05-13, ACROSS THE AUDIT ITSELF
in `tests/unit/test_audit_watchdog.py`, which arms a real `Watchdog` on an
injected clock. That gap is worth naming rather than leaving implied: this
harness runs the real audit with the freeze detector switched off, so a
100%-green run of THIS file was never evidence that the audit outlives
`watchdog_threshold`. It did not (05-UAT.md G6).
"""

from __future__ import annotations

import asyncio
import dataclasses

from pursuit.network import agent_lifecycle
from pursuit.network.agent_audit_wiring import declare_step0, run_final_audit, write_declaration
from pursuit.network.agent_lifecycle import start_server, stop_runtime, stop_watchdog
from pursuit.network.agent_teardown import linger_for_peer
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import make_client_caller, perform_handshake
from pursuit.network.orchestrator import run_turn_loop
from pursuit.shared.scent_config import scent_digest
from tests.integration.test_secret_channel import _free_port, _wait_until_accepting

# Test scaffolding only -- NOT PARAMETERS.md values, and no config file is
# touched (the `_fakes_agent._FAST_TIMEOUT` precedent, which already runs
# tests at backoff_seconds=0). The PRODUCTION bounds stay whatever
# config/*/network.json says; this only keeps one integration test from
# spending 30 s per wait and 5 s per linger.
_RESPONSE_TIMEOUT = 5
_BACKOFF_SECONDS = 1
_LATE_SECONDS = 0.3
_ACCEPT_TIMEOUT = 2.0


def _paired_configs():
    """Two real AgentConfigs aimed at each other over freshly-probed
    loopback ports, never the real 8001/8002 pair (so this test can never
    collide with a dev-launched agent)."""
    cfg_a, cfg_b = load_agent_config("config/police"), load_agent_config("config/thief")
    port_a, port_b = _free_port(), _free_port()
    net_a = dataclasses.replace(
        cfg_a.net, host="127.0.0.1", port=port_a,
        opponent_url=f"http://127.0.0.1:{port_b}/mcp",
        response_timeout=_RESPONSE_TIMEOUT, backoff_seconds=_BACKOFF_SECONDS,
    )
    net_b = dataclasses.replace(net_a, port=port_b, opponent_url=f"http://127.0.0.1:{port_a}/mcp")
    return dataclasses.replace(cfg_a, net=net_a), dataclasses.replace(cfg_b, net=net_b)


async def _handshake(ctx, cfg, *, step0_digest, declaration, game_uid):
    async with ctx.runtime.client() as client:
        return await perform_handshake(
            machine=ctx.machine, reporter=ctx.reporter,
            local_digest=config_digest(cfg.config_dir / "game_params.json"),
            local_role=ctx.role, call_peer=make_client_caller(client),
            local_scent_digest=scent_digest(cfg.scent),
            local_step0_digest=step0_digest, local_game_id=game_uid,
            local_step0_declaration=declaration,
        )


async def _play_over_real_sockets(cfg_a, cfg_b, *, game_uid, log_dir):
    """Both servers up on real loopback ports, Step-0 + handshake both
    directions, then both turn loops to a real board outcome."""
    digest_a, decl_a = await declare_step0(cfg_a)
    digest_b, decl_b = await declare_step0(cfg_b)
    ctx_a = agent_lifecycle.default_context(
        cfg_a, game_uid=game_uid, log_path=log_dir / "police" / "a.jsonl",
        local_step0_digest=digest_a, local_game_id=game_uid, local_step0_declaration=decl_a,
    )
    ctx_b = agent_lifecycle.default_context(
        cfg_b, game_uid=game_uid, log_path=log_dir / "thief" / "b.jsonl",
        local_step0_digest=digest_b, local_game_id=game_uid, local_step0_declaration=decl_b,
    )
    await start_server(ctx_a)
    await start_server(ctx_b)
    for cfg in (cfg_a, cfg_b):
        await _wait_until_accepting(cfg.net.port, timeout=_ACCEPT_TIMEOUT)

    result_a = await _handshake(ctx_a, cfg_a, step0_digest=digest_a, declaration=decl_a,
                                game_uid=game_uid)
    result_b = await _handshake(ctx_b, cfg_b, step0_digest=digest_b, declaration=decl_b,
                                game_uid=game_uid)
    assert result_a.agreed and result_b.agreed, f"{result_a}; {result_b}"
    write_declaration(ctx_a, cfg_a, result_a, decl_a)
    write_declaration(ctx_b, cfg_b, result_b, decl_b)

    outcome_a, outcome_b = await asyncio.gather(run_turn_loop(ctx_a), run_turn_loop(ctx_b))
    return outcome_a, outcome_b, ctx_a, ctx_b


async def late_peer_round(tmp_path, *, linger: bool):
    """A reaches the end of its turn loop first and audits; B arrives LATE
    and pushes its FINAL_REVEAL while A is already tearing down.

    A's teardown is the three steps `run_agent` performs, in that exact
    order. `linger=False` is the revert probe -- the pre-Task-2 shape, kept
    HERE rather than by editing source, so the probe is re-runnable.
    """
    cfg_a, cfg_b = _paired_configs()
    outcome_a, outcome_b, ctx_a, ctx_b = await _play_over_real_sockets(
        cfg_a, cfg_b, game_uid="late-peer-teardown", log_dir=tmp_path,
    )
    audit_a_task = asyncio.create_task(run_final_audit(ctx_a, board_outcome=outcome_a))
    await asyncio.sleep(_LATE_SECONDS)
    audit_b_task = asyncio.create_task(run_final_audit(ctx_b, board_outcome=outcome_b))

    audit_a = await audit_a_task
    stop_watchdog(ctx_a)
    if linger:
        await linger_for_peer(ctx_a)
    await stop_runtime(ctx_a)

    # B's audit is allowed to FAIL outright and is returned as evidence
    # rather than raised: without the linger it does (deferred-items.md #1),
    # and a probe that explodes inside the harness cannot be asserted on.
    # The linger=True test asserts peer_error is None, so nothing is
    # silently swallowed on the path that matters.
    audit_b, peer_error = None, None
    try:
        audit_b = await audit_b_task
    except Exception as exc:
        peer_error = exc
    finally:
        stop_watchdog(ctx_b)
        await stop_runtime(ctx_b)
    return {
        "final_a": audit_a if audit_a is not None else outcome_a,
        "final_b": audit_b if audit_b is not None else outcome_b,
        "peer_error": peer_error,
        "ctx_a": ctx_a, "ctx_b": ctx_b,
    }
