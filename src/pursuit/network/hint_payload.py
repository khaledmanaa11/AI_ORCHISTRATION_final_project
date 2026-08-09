"""D-47 hint payload shape: free text plus the pre-committed intent flag.

Split from envelope.py at the 150-code-line gate (Segal Table 5), mirroring
the handshake.py / handshake_wire.py split (02-08/02-09): envelope.py stays
a four-key, payload-agnostic shape validator (its own ownership-boundary
docstring is unchanged by this plan except for the one new MessageType
member); this module owns the HINT payload's internal shape.

`assert_no_coordinates` sits on the SEND path only (LANG-02, rule 27):
incoming text is data, logged as received, never censored -- semantic
judgement of a hint belongs to the strategy layer, not to a transport
module (see tools.py's receive_hint, which never imports this guard). The
check itself now lives in `shared/hint_guard.py` (04-10), re-exported
here unchanged -- see that module's docstring for why.
"""

from __future__ import annotations

from enum import Enum

from pursuit.network.envelope import Envelope, MessageType
from pursuit.shared.deception_types import Intent  # noqa: F401 -- re-export
from pursuit.shared.hint_guard import assert_no_coordinates  # noqa: F401 -- re-export

# Intent is imported, not declared here. 04-08's planner DECIDES the flag and
# lives under strategy/, which may not import pursuit.network at all
# (STRAT-03, enforced by scripts/check_no_llm_in_strategy.py), so the type
# moved to shared/deception_types.py and this module re-exports it -- every
# existing `from pursuit.network.hint_payload import Intent` still resolves.


class HintKey(str, Enum):
    """Hint payload key constants -- house pattern, mirrors ConfigKey /
    EnvelopeKey / handshake_wire.HandshakeKey. An Enum (not a plain class)
    so validate_hint_payload can iterate the required key set."""

    TEXT = "text"
    INTENT = "intent"
    TURN = "turn"


def validate_hint_payload(payload: dict) -> None:
    """Structural check only (shape, not content): all three HintKey
    fields present, `intent` one of Intent's values. Raises KeyError /
    ValueError, matching Envelope.from_dict's own fail-loud house style."""
    for key in HintKey:
        if key.value not in payload:
            raise KeyError(f"hint payload missing required key: {key.value!r}")
    intent = payload[HintKey.INTENT.value]
    if intent not in (Intent.TRUTH.value, Intent.LIE.value):
        raise ValueError(f"hint payload intent must be 'truth' or 'lie', got {intent!r}")


def build_hint(text: str, intent: Intent, turn: int, sender: str) -> Envelope:
    """Construct one outgoing HINT envelope (mirrors handshake_wire.build_offer).
    `intent` is a required, strongly-typed argument with no default, so a
    caller cannot build a hint without committing it in advance (LANG-03)."""
    assert_no_coordinates(text)
    payload = {
        HintKey.TEXT.value: text,
        HintKey.INTENT.value: intent.value,
        HintKey.TURN.value: turn,
    }
    validate_hint_payload(payload)
    return Envelope(type=MessageType.HINT, turn=turn, sender=sender, payload=payload)
