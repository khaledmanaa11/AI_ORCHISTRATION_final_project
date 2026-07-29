"""§10.4 gate criterion 2: "Cop and thief run as two separate processes ...
with no shared runtime state." Split out of test_turn_lifecycle.py at the
150-code-line gate (QUAL-08, split never compress) -- same criterion, same
LIMITATION, two modules instead of one.

LIMITATION: this module runs in ONE pytest process. It proves that the two
agents share no runtime object and are configured from two independent
config roots -- the conditions that make two processes possible and
non-leaking. It does NOT prove OS-level process separation; that is
demonstrated by the standalone two-terminal launch (D-02), run in Task 4 of
plan 02-10 and recorded in 02-10-SUMMARY.md.
"""

from __future__ import annotations

import pathlib

from pursuit import main
from pursuit.network.event_log import EventType, append_event, build_event
from pursuit.network.state_machine import State, TurnStateMachine
from tests.integration.conftest import read_events


def _no_op_reporter(**_kwargs) -> None:
    """A reporter that never touches disk -- used only where THIS test's own
    subject is queue/machine identity, not the JSONL sink itself."""


async def test_two_runtimes_share_no_runtime_state(
    peer_pair, police_params, thief_params, agent_log_paths
):
    """GATE-2, NET-01, NET-02, D-01, D-16 -- asserted POSITIVELY: mutate one
    side, prove the other is untouched."""
    police, thief = peer_pair

    # 1. Config roots are genuinely distinct -- read from fixtures, never the D-16 port numbers.
    assert police_params is not thief_params
    assert police_params.port != thief_params.port
    assert police_params.opponent_url != thief_params.opponent_url

    # 2. Runtime objects are distinct -- rules out a module-level singleton.
    assert police is not thief
    assert police.server is not thief.server
    assert police.queue is not thief.queue

    # 3. Queue non-leakage: mutate A, prove B is untouched; drain A, B still untouched.
    police.queue.put_nowait(object())
    assert thief.queue.qsize() == 0
    police.queue.get_nowait()
    assert thief.queue.qsize() == 0

    # 4. State-machine non-leakage: no module-level current-state variable to leak through.
    machine_a = TurnStateMachine(_no_op_reporter)
    machine_b = TurnStateMachine(_no_op_reporter)
    machine_a.attempt(State.HANDSHAKE)
    assert machine_a.state is State.HANDSHAKE
    assert machine_b.state is State.INIT

    # 5. Event-log non-leakage: two distinct files, one written, the other never touched.
    log_a, log_b = agent_log_paths
    append_event(
        log_a,
        build_event(game_uid="g-a", turn=0, event=EventType.MESSAGE_SENT, sender="police"),
    )
    assert log_a != log_b
    assert read_events(log_b) == []


def test_entry_point_is_config_dir_parameterised(police_params, thief_params, capsys):
    """GATE-2, NET-01, D-01, D-02 -- one code path, two config roots.

    `--check-config` (02-09) exercises the entry point without binding a
    port (RESEARCH: never a code path that binds a port in this suite)."""
    exit_police = main.main(["--config-dir", "config/police", "--check-config"])
    printed_police = capsys.readouterr().out
    exit_thief = main.main(["--config-dir", "config/thief", "--check-config"])
    printed_thief = capsys.readouterr().out

    assert exit_police == 0
    assert exit_thief == 0
    assert f"{police_params.host}:{police_params.port}" in printed_police
    assert f"{thief_params.host}:{thief_params.port}" in printed_thief
    assert printed_police != printed_thief

    source = pathlib.Path("src/pursuit/main.py").read_text(encoding="utf-8")
    assert "config/police" not in source
    assert "config/thief" not in source
