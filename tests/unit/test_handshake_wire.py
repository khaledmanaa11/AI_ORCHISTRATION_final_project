"""Wire-shape suite for the D-08 handshake envelope (D-06, D-46).

Isolated from tests/unit/test_handshake.py's orchestration suite (QUAL-02: one concern per
file): this file only asserts what build_offer/HandshakeKey put ON THE WIRE, never touches
perform_handshake/respond_to_handshake or the state machine.
"""

from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.handshake_wire import HANDSHAKE_TURN, HandshakeKey, build_offer


def test_wire_vocabulary_is_fixed():
    """The key names are a fixed vocabulary (D-46) -- a typo here cannot silently produce an
    absent digest, because both this test and the loader read the SAME enum member."""
    assert HandshakeKey.DIGEST == "digest"
    assert HandshakeKey.SCENT_DIGEST == "scent_digest"


def test_offer_without_scent_digest_carries_one_key():
    """Pre-migration call sites (no local_scent_digest) build a legal, config-only offer --
    the key is OMITTED, never sent as null."""
    offer = build_offer("cfg-digest", "police")
    assert offer.payload == {HandshakeKey.DIGEST: "cfg-digest"}
    assert HandshakeKey.SCENT_DIGEST not in offer.payload


def test_offer_with_scent_digest_carries_exactly_two_keys():
    """THE Task-1 gate: exactly the two documented keys, no others, once a scent digest is
    supplied (D-46)."""
    offer = build_offer("cfg-digest", "police", local_scent_digest="scent-digest")
    assert offer.payload == {
        HandshakeKey.DIGEST: "cfg-digest",
        HandshakeKey.SCENT_DIGEST: "scent-digest",
    }
    assert set(offer.payload) == {HandshakeKey.DIGEST, HandshakeKey.SCENT_DIGEST}


def test_offer_shape_is_the_fixed_envelope():
    """build_offer never grows a new envelope-level key -- only PAYLOAD carries the second
    digest (see handshake.py's module docstring: the shape does not change)."""
    offer = build_offer("cfg-digest", "police", local_scent_digest="scent-digest")
    assert offer.type is MessageType.HANDSHAKE
    assert offer.turn == HANDSHAKE_TURN
    assert offer.sender == "police"


def test_offer_round_trips_through_envelope_to_dict_and_from_dict():
    """Both digests survive a full wire round-trip; Envelope's REQUIRED_KEYS check (untouched
    by this plan) still accepts the resulting dict."""
    offer = build_offer("cfg-digest", "police", local_scent_digest="scent-digest")
    wire_dict = offer.to_dict()
    assert set(wire_dict) == {
        EnvelopeKey.TYPE, EnvelopeKey.TURN, EnvelopeKey.SENDER, EnvelopeKey.PAYLOAD,
    }

    decoded = Envelope.from_dict(wire_dict)
    assert decoded == offer
    assert decoded.payload[HandshakeKey.DIGEST] == "cfg-digest"
    assert decoded.payload[HandshakeKey.SCENT_DIGEST] == "scent-digest"


def test_config_only_offer_still_round_trips():
    """The backward-compatible (no scent digest) shape is ALSO a legal envelope."""
    offer = build_offer("cfg-digest", "thief")
    decoded = Envelope.from_dict(offer.to_dict())
    assert decoded == offer
    assert HandshakeKey.SCENT_DIGEST not in decoded.payload
