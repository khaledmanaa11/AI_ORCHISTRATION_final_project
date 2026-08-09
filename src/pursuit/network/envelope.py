"""D-06 typed message envelope.

Every message that crosses the wire between the two peers is an Envelope,
fixed at exactly four keys: {type, turn, sender, payload}. Phase-4 hints and
Phase-6 commit-reveal data arrive later as NEW MessageType members with their
own payload shapes — never as new top-level envelope keys. That invariant is
what lets the protocol grow without a reshape.

Ownership boundary: this module validates wire SHAPE only. It does not
validate that `turn` is in range (the state machine, 02-03, owns turn
ordering) and does not validate that a `move` payload's coordinates are on
the board (the SDK engine, Phase 1, owns board bounds). Keeping range checks
out of this module is also why it contains zero numeric literals.
"""

from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """The nine message kinds on the wire (D-05, D-47, D-58).

    Phase-4 added HINT as a NEW MEMBER of this same enum — never a second
    envelope shape (see module docstring). Phase-6 adds the four
    commit-reveal kinds (COMMIT, ACK, REVEAL, FINAL_REVEAL) the same way:
    additive members only, the four-key Envelope shape never changes.
    """

    HANDSHAKE = "handshake"
    MOVE = "move"
    BARRIER = "barrier"
    GAME_OVER = "game_over"
    HINT = "hint"
    COMMIT = "commit"
    ACK = "ack"
    REVEAL = "reveal"
    FINAL_REVEAL = "final_reveal"


class EnvelopeKey:
    """Protocol-local wire key names for Envelope.to_dict()/from_dict().

    Lives here, not in pursuit.constants, because these are protocol-local
    names owned by this plan, not project-wide structural constants.
    """

    TYPE = "type"
    TURN = "turn"
    SENDER = "sender"
    PAYLOAD = "payload"


REQUIRED_KEYS = frozenset({EnvelopeKey.TYPE, EnvelopeKey.TURN, EnvelopeKey.SENDER, EnvelopeKey.PAYLOAD})


def _require_non_bool_int(value: object, label: str) -> None:
    """Reject anything that is not a plain int, bool included (bool < int)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Envelope.{label} must be an int, got {type(value).__name__}")


@dataclass(frozen=True)
class Envelope:
    """The fixed four-field message envelope (D-06).

    Immutable by construction (NET-02): a decoded envelope can be handed to
    the orchestrator with no risk of a handler mutating shared state under it.
    """

    type: MessageType
    turn: int
    sender: str
    payload: dict

    def to_dict(self) -> dict:
        """Serialize to a plain, JSON-native dict (enum -> its string value)."""
        return {
            EnvelopeKey.TYPE: self.type.value,
            EnvelopeKey.TURN: self.turn,
            EnvelopeKey.SENDER: self.sender,
            EnvelopeKey.PAYLOAD: self.payload,
        }

    @staticmethod
    def from_dict(data: dict) -> "Envelope":
        """Fail-loud decode of an attacker-controlled wire dict.

        Raises
        ------
        TypeError
            Non-dict input, non-int/bool turn, non-str sender, non-dict payload.
        KeyError
            Any of the four required keys is missing.
        ValueError
            An unexpected extra key is present, the sender is empty/blank, or
            the type value does not name a known MessageType member.
        """
        if not isinstance(data, dict):
            raise TypeError(f"Envelope.from_dict expects a dict, got {type(data).__name__}")

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise KeyError(f"Envelope missing required key(s): {sorted(missing)}")

        extra = data.keys() - REQUIRED_KEYS
        if extra:
            raise ValueError(f"Envelope has unexpected key(s): {sorted(extra)}")

        turn = data[EnvelopeKey.TURN]
        _require_non_bool_int(turn, "turn")

        sender = data[EnvelopeKey.SENDER]
        if not isinstance(sender, str):
            raise TypeError(f"Envelope.sender must be a str, got {type(sender).__name__}")
        if not sender.strip():
            raise ValueError("Envelope.sender must not be empty or whitespace-only")

        payload = data[EnvelopeKey.PAYLOAD]
        if not isinstance(payload, dict):
            raise TypeError(f"Envelope.payload must be a dict, got {type(payload).__name__}")

        raw_type = data[EnvelopeKey.TYPE]
        try:
            message_type = MessageType(raw_type)
        except ValueError as exc:
            known = sorted(m.value for m in MessageType)
            raise ValueError(f"Unknown Envelope type {raw_type!r}; known types: {known}") from exc

        return Envelope(type=message_type, turn=turn, sender=sender, payload=payload)
