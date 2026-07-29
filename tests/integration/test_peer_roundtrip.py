"""§10.4 gate criterion 1 (GATE-1): "A geometric message sent by agent A over
localhost is received and decoded correctly by agent B."

What this proves: the real four-tool surface (D-05, `register_tools`) plus
the real typed envelope (D-06, `Envelope`) carry a type=move payload {x, y}
from one peer to the other with coordinates intact, and the receiving tool
acks immediately rather than blocking on the recipient's own turn (D-07).

LIMITATION: these tests use FastMCP's in-memory transport
(`Client(server_instance)`) -- same objects, same handlers, same codec, but
no socket, and therefore not literally "over localhost". The localhost hop
is exercised by the standalone two-terminal launch (D-02), run outside
pytest in Task 4 of plan 02-10 and recorded in 02-10-SUMMARY.md.
"""

from __future__ import annotations

from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.peer_runtime import PeerRuntime


def _wire_args(envelope: Envelope) -> dict:
    """The wire shares no `type` key (the tool name already carries the
    kind, D-06) -- the same drop 02-09's turn_actions.py performs before
    calling `receive_move`."""
    return {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}


async def _send_move(
    sender_role: str, dest: tuple[int, int], turn: int, target: PeerRuntime
) -> tuple[Envelope, object]:
    """Compose a type=move Envelope and deliver it to `target`'s real
    `receive_move` tool over the in-memory transport (RESEARCH Pattern 5)."""
    from tests.integration.conftest import client_for

    envelope = Envelope(
        type=MessageType.MOVE, turn=turn, sender=sender_role,
        payload={"x": dest[0], "y": dest[1]},
    )
    async with client_for(target) as client:
        ack = await client.call_tool("receive_move", _wire_args(envelope))
    return envelope, ack


async def test_move_envelope_decoded_by_peer(peer_pair, default_params):
    """GATE-1, NET-03, NET-08, D-05, D-06, D-07."""
    police, thief = peer_pair
    sent, ack = await _send_move("police", default_params.cop_start, 1, thief)

    # 1. An immediate ack -- it returned at all, without waiting on peer B's turn (D-07).
    assert ack.data["status"] == "ack"
    assert ack.data["turn"] == sent.turn

    # 2. One-way travel only: peer B's queue holds exactly the one item, peer A's is empty.
    assert thief.queue.qsize() == 1
    assert police.queue.qsize() == 0

    # 3. Decoding the queued item reconstructs peer A's envelope exactly. Per 02-06's
    #    design (tools.py's _accept), the queue already holds a real Envelope, not a dict.
    decoded = thief.queue.get_nowait()
    assert isinstance(decoded, Envelope)
    assert decoded == sent
    assert decoded.type is MessageType.MOVE
    assert decoded.turn == sent.turn
    assert decoded.sender == sent.sender

    # 4. The coordinates specifically: exact and still int, never silently coerced.
    x, y = decoded.payload["x"], decoded.payload["y"]
    assert (x, y) == default_params.cop_start
    assert isinstance(x, int) and not isinstance(x, bool)
    assert isinstance(y, int) and not isinstance(y, bool)


async def test_coordinates_survive_round_trip(peer_pair, default_params):
    """GATE-1, NET-08, D-06 -- every board position is fixture-derived.

    `0` and `1` (index arithmetic) are the only integer literals in this
    test; board_size itself is never typed out (CLAUDE.md rule 1)."""
    _police, thief = peer_pair
    positions = [
        default_params.cop_start,
        default_params.thief_start,
        (0, 0),
        (default_params.board_size - 1, default_params.board_size - 1),
    ]

    for turn, dest in enumerate(positions, start=1):
        sent, ack = await _send_move("police", dest, turn, thief)
        assert ack.data["status"] == "ack"

        decoded = thief.queue.get_nowait()
        assert isinstance(decoded, Envelope)
        x, y = decoded.payload["x"], decoded.payload["y"]
        assert (x, y) == dest == (sent.payload["x"], sent.payload["y"])
        assert isinstance(x, int) and not isinstance(x, bool)
        assert isinstance(y, int) and not isinstance(y, bool)
