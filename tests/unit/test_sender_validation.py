"""06-06 item 4: an inbound envelope must actually come from the opponent.

`_accept` took the `sender` field straight off the wire and enqueued it.
`turn_actions` then feeds that field into `engine_agent(...)` and
`record_action(ctx, move_envelope.sender, ...)`, so a peer stamping OUR own
role writes into our own half of the turn buffer -- `maybe_resolve` can then
never fire, and the game silently stalls instead of rejecting the message.

All five audit lenses that swept this code chased `turn`; none read
`sender`. These tests cover the field they missed.
"""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from pursuit.network.envelope import MessageType
from pursuit.network.orchestrator import opponent_role
from pursuit.network.peer_runtime import build_server
from pursuit.network.tools import _accept


def test_opponent_role_is_defined_once_and_is_symmetric():
    assert opponent_role("police") == "thief"
    assert opponent_role("thief") == "police"
    with pytest.raises(ValueError, match="unknown role"):
        opponent_role("referee")


async def test_accept_enqueues_when_the_sender_is_the_expected_opponent():
    queue: asyncio.Queue = asyncio.Queue()
    ack = await _accept(queue, MessageType.COMMIT, 1, "thief", {"h_commit": "x"}, "thief")

    assert ack["status"] == "ack"
    assert queue.qsize() == 1


async def test_accept_rejects_a_spoofed_sender_and_enqueues_nothing():
    """The spoof that matters: the peer claims to be US."""
    queue: asyncio.Queue = asyncio.Queue()

    with pytest.raises(ToolError, match="unexpected sender 'police'"):
        await _accept(queue, MessageType.COMMIT, 1, "police", {"h_commit": "x"}, "thief")

    assert queue.qsize() == 0, "a rejected envelope must never reach the turn loop"


async def test_accept_rejects_an_unknown_third_party():
    queue: asyncio.Queue = asyncio.Queue()

    with pytest.raises(ToolError, match="unexpected sender 'referee'"):
        await _accept(queue, MessageType.REVEAL, 2, "referee", {}, "thief")

    assert queue.qsize() == 0


async def test_no_expected_sender_accepts_anything_pre_06_06_behaviour():
    """Default None must leave every existing caller and test untouched."""
    queue: asyncio.Queue = asyncio.Queue()
    await _accept(queue, MessageType.COMMIT, 1, "anyone-at-all", {"h_commit": "x"})

    assert queue.qsize() == 1


async def test_the_check_is_live_through_a_real_registered_tool():
    """Not just the helper: prove it through a real FastMCP round trip, so
    the wiring from register_tools down to the handler is exercised."""
    queue: asyncio.Queue = asyncio.Queue()
    server = build_server(queue, "police-peer", expected_sender="thief")

    async with Client(server) as client:
        good = await client.call_tool(
            "receive_commit", {"turn": 1, "sender": "thief", "payload": {"h_commit": "x"}},
        )
        assert good is not None
        assert queue.qsize() == 1

        with pytest.raises(ToolError):
            await client.call_tool(
                "receive_commit", {"turn": 1, "sender": "police", "payload": {"h_commit": "x"}},
            )

    assert queue.qsize() == 1, "the spoofed call must not have enqueued anything"


async def test_handshake_is_deliberately_exempt():
    """The handshake NEGOTIATES the peer's role -- checking it there would
    reject the very message that establishes the fact. respond_to_handshake
    evaluates peer_role itself."""
    queue: asyncio.Queue = asyncio.Queue()
    server = build_server(queue, "police-peer", expected_sender="thief")

    async with Client(server) as client:
        reply = await client.call_tool(
            "handshake", {"turn": 0, "sender": "police", "payload": {}},
        )

    assert reply is not None
    assert queue.qsize() == 1
