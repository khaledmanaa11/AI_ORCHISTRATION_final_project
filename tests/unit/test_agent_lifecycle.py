"""Wiring tests: NET-02 isolation, engine_agent/load_role, reporter durability,
the shutdown lifecycle, and the NET-09 inbound-handshake-seam wiring gate.

Resilience tests (freeze handler, watchdog-from-config, port release) live in
tests/unit/test_agent_lifecycle_resilience.py -- split at the 150-code-line
gate, not by test meaning. Shared fakes (FakeReporter/FakeWatchdog/FakeClient/
FakeRuntime) live in test_orchestrator.py and are imported here (QUAL-02).
"""

import ast
import asyncio
import contextlib
import dataclasses
import json
import pathlib

import pytest
from fastmcp import Client

from pursuit.network import agent_lifecycle, handshake
from pursuit.network.config_hash import config_digest, digests_match
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.state_machine import State, TransitionSeverity
from pursuit.shared.scent_config import load_scent_model, scent_digest
from tests.unit._fakes_agent import FakeReporter, FakeWatchdog

_STATIC_TARGETS = (
    "src/pursuit/network/orchestrator.py",
    "src/pursuit/network/agent_lifecycle.py",
)


def test_engine_agent_maps_role_to_sdk_name():
    assert agent_lifecycle.engine_agent("police") == "cop"
    assert agent_lifecycle.engine_agent("thief") == "thief"
    with pytest.raises(ValueError):
        agent_lifecycle.engine_agent("referee")


def test_load_role_reads_the_per_agent_config():
    assert agent_lifecycle.load_role("config/police") == "police"
    assert agent_lifecycle.load_role("config/thief") == "thief"


def test_two_agents_share_no_runtime_state(tmp_path):
    """THE NET-02 GATE -- the single most important test in this plan."""
    police_cfg = agent_lifecycle.load_agent_config("config/police")
    thief_cfg = agent_lifecycle.load_agent_config("config/thief")

    class _FakeRuntime:
        def __init__(self):
            self.queue = asyncio.Queue()

    a = agent_lifecycle.build_context(
        police_cfg, game_uid="game-a", log_path=tmp_path / "a.jsonl",
        runtime=_FakeRuntime(), watchdog=FakeWatchdog(), reporter=FakeReporter(),
    )
    b = agent_lifecycle.build_context(
        thief_cfg, game_uid="game-b", log_path=tmp_path / "b.jsonl",
        runtime=_FakeRuntime(), watchdog=FakeWatchdog(), reporter=FakeReporter(),
    )

    assert a.machine is not b.machine
    assert a.runtime is not b.runtime
    assert a.runtime.queue is not b.runtime.queue
    assert a.watchdog is not b.watchdog
    assert a.state is not b.state
    assert a.log_path != b.log_path
    assert a.game_uid != b.game_uid
    assert a.role != b.role

    a.machine.attempt(State.HANDSHAKE)
    a.state = dataclasses.replace(a.state, turn=a.state.turn + 1)
    assert b.machine.state is State.INIT
    assert b.state.turn == 0


async def test_handshake_tool_answers_a_real_peer(tmp_path):
    """THE NET-09 WIRING GATE -- proves 02-08's responder is bound behind the
    REAL handshake tool, not merely present and unwired. 04-12: the real
    responder now opts into the D-46 scent lock (`local_scent_digest`), so
    this test's own hand-built offer must carry one too, exactly like a
    real peer's `default_context`-built offer does."""
    police = agent_lifecycle.default_context(
        agent_lifecycle.load_agent_config("config/police"),
        game_uid="g-police", log_path=tmp_path / "police.jsonl",
    )
    thief = agent_lifecycle.default_context(
        agent_lifecycle.load_agent_config("config/thief"),
        game_uid="g-thief", log_path=tmp_path / "thief.jsonl",
    )

    police_scent_digest = scent_digest(load_scent_model(pathlib.Path("config/police") / "scent.json"))
    offer = handshake.build_offer(
        config_digest(pathlib.Path("config/police") / "game_params.json"), police.role,
        local_scent_digest=police_scent_digest,
    )
    args = {k: v for k, v in offer.to_dict().items() if k != EnvelopeKey.TYPE}

    async with Client(thief.runtime.server) as client:
        result = await client.call_tool(handshake.HANDSHAKE_TOOL, args)

    assert "status" not in result.data
    reply = Envelope.from_dict(result.data)
    assert reply.type is MessageType.HANDSHAKE
    assert reply.sender == thief.role
    assert reply.payload[handshake.HandshakeKey.DIGEST] == config_digest(
        pathlib.Path("config/thief") / "game_params.json"
    )
    assert digests_match(
        reply.payload[handshake.HandshakeKey.DIGEST],
        offer.payload[handshake.HandshakeKey.DIGEST],
    ) is True
    assert thief.machine.state is not State.ERROR


def test_modules_declare_no_module_level_mutable_state():
    """THE NET-02 STATIC GATE: no module-level container or constructed
    instance in either module -- only imports, constants, functions, classes.
    Also scans the two files each split into at the 150-line gate
    (agent_wiring.py, turn_actions.py), if present, for the same property."""
    targets = list(_STATIC_TARGETS)
    for extra in ("agent_wiring.py", "turn_actions.py"):
        path = pathlib.Path("src/pursuit/network") / extra
        if path.exists():
            targets.append(str(path))
    for path in targets:
        tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                assert not isinstance(
                    node.value,
                    (ast.Dict, ast.List, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp, ast.Call),
                ), f"{path}: module-level mutable/constructed state at line {node.lineno}"


def test_transition_reporter_writes_illegal_transitions_to_jsonl(tmp_path):
    log_path = tmp_path / "reporter.jsonl"
    reporter = agent_lifecycle.make_transition_reporter(log_path, game_uid="g1", role="police")
    reporter(
        current=State.INIT, target=State.GAME_OVER,
        severity=TransitionSeverity.PROTOCOL_VIOLATION, reason="not in table",
    )
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "illegal_transition"


class _TaskRuntime:
    """A runtime whose shutdown cancels a real, injected asyncio.Task -- no
    socket, no fastmcp, matching PeerRuntime's own stop() contract."""

    def __init__(self, task):
        self.shutdowns = 0
        self.task = task

    async def stop(self):
        self.shutdowns += 1
        if not self.task.done():
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task


async def test_shutdown_cancels_the_server_task(tmp_path):
    cfg = agent_lifecycle.load_agent_config("config/police")
    task = asyncio.create_task(asyncio.sleep(999))
    runtime = _TaskRuntime(task)
    ctx = agent_lifecycle.build_context(
        cfg, game_uid="g1", log_path=tmp_path / "shutdown.jsonl",
        runtime=runtime, watchdog=FakeWatchdog(), reporter=FakeReporter(),
    )

    await agent_lifecycle.shutdown_cleanly(ctx)
    assert task.done()
    assert runtime.shutdowns == 1
    assert ctx.watchdog.stopped is True

    await agent_lifecycle.shutdown_cleanly(ctx)  # idempotent -- must not raise
    assert runtime.shutdowns == 2
