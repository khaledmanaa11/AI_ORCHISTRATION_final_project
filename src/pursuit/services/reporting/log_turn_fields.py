"""What ONE turn of `log_<game_id>_g<NN>.json` contains -- WIRE TRUTH ONLY.

Split out of `log_join.py` at the 150-code-line gate (Segal Table 5) along the
seam the two subjects already had: the join owns READING and KEYING, this leaf
owns the record's SHAPE. Split, never compressed.

RULES 8-9: NOTHING DERIVED FROM `ctx.state` MAY ENTER AN ARTIFACT. 07-11 closed
a disqualifying leak in which the cop's published belief map and opponent scent
were seeded from `ctx.state.thief`, and D7-8 records that
`turn_language.belief_snapshot` still writes that true argmax into every
`language_turn` JSONL record -- correct for the audit log (rule 38), fatal in a
file that is emailed off the machine. So a `language_turn` record is NEVER
copied wholesale: `outgoing_hint` copies exactly the two broadcast keys, and
`LANGUAGE_INTERNAL_FIELDS` names what must never appear so a test can scan the
serialised artifact for each name.

The second reason is verifiability, and it stands on its own: a third party
must be able to recompute every hash from this file alone, and internal
inference is unverifiable noise. Everything below is either a wire envelope's
payload, a value from this side's own nonce ledger, or the peer's own claim
carried verbatim as evidence.
"""

from __future__ import annotations

from pursuit.network.envelope import MessageType
from pursuit.network.turn_commit_wait import H_COMMIT_KEY
from pursuit.security.commit_pack import CommitKey
from pursuit.security.ledger import LedgerField

__all__ = (
    "HINT_BROADCAST_KEYS",
    "LANGUAGE_INTERNAL_FIELDS",
    "OUTGOING_HINT_FIELD",
    "TurnField",
    "WireSide",
    "build_turn_record",
    "outgoing_hint",
)

# The two keys `turn_events.language_turn_record` puts in `outgoing_hint` that
# this peer BROADCAST on the wire -- the hint text and the rule-25 intent flag.
HINT_BROADCAST_KEYS = ("intent", "text")
OUTGOING_HINT_FIELD = "outgoing_hint"

# Every other field of a `language_turn` record. `belief_argmax` is D7-8's true
# cell; `belief_entropy`/`reliability`/`regime` are this side's own inference
# and strategy regime; `token_spend` is our gatekeeper accounting; and
# `incoming_hint` carries our DECODER's outcome/reason verdict rather than the
# peer's words -- the peer's actual words are the received HINT envelope, which
# is wire truth and is carried instead.
LANGUAGE_INTERNAL_FIELDS = frozenset(
    {"belief_argmax", "belief_entropy", "incoming_hint", "regime", "reliability", "token_spend"}
)


class TurnField:
    """One turn record's key names. `docs/PARAMETERS.md:167` requires
    commitments, moves, hints, verdicts, nonce and hash; `hash`/`nonce`/
    `intent`/`state`/`move` are the five `commit_pack.verify_reveal` inputs, so
    a reader re-hashes from the top level with no unpacking rule to guess."""

    TURN = "turn"
    HASH = "hash"
    NONCE = "nonce"
    INTENT = "intent"
    STATE = "state"
    MOVE = "move"
    COMMITMENT = "commitment"
    REVEALED_MOVE = "revealed_move"
    HINT = "hint"
    VERDICT = "verdict"
    PEER_CLAIMED_TURNS = "peer_claimed_turns"


class WireSide:
    """Which leg of the exchange a value came off."""

    SENT = "sent"
    RECEIVED = "received"
    ACKED = "acked"
    OUTGOING = "outgoing"
    SELF = "self"
    PEER = "peer"


def outgoing_hint(language: dict | None) -> dict | None:
    """The broadcast half of a `language_turn` record, by ALLOW-LIST.

    Copies exactly `HINT_BROADCAST_KEYS`, never `**record` and never
    `dict(record)` minus a deny-list: an allow-list stays correct when a future
    plan adds a field to `language_turn_record`, and a deny-list silently ships
    it. That asymmetry is the whole reason this function exists.
    """
    if not isinstance(language, dict):
        return None
    hint = language.get(OUTGOING_HINT_FIELD)
    if not isinstance(hint, dict):
        return None
    return {key: hint.get(key) for key in HINT_BROADCAST_KEYS}


def _h_commit(payload: object) -> str | None:
    """The `h_commit` out of a COMMIT/ACK envelope payload, or None."""
    return payload.get(H_COMMIT_KEY) if isinstance(payload, dict) else None


def build_turn_record(
    *,
    turn: int,
    ledger_record: dict | None,
    sent: dict,
    received: dict,
    language: dict | None,
    verdict: dict,
    peer_claimed_turns: dict,
) -> dict:
    """Assemble one turn. `sent`/`received` map an envelope TYPE to that
    envelope's payload; `ledger_record` is this side's own `{turn, h_commit,
    payload}` for the SAME local turn, or None when no commit was ledgered for
    it (a trailing game-over turn is the ordinary case)."""
    ledger = ledger_record or {}
    payload = ledger.get(LedgerField.PAYLOAD) or {}
    return {
        TurnField.TURN: turn,
        TurnField.HASH: ledger.get(LedgerField.H_COMMIT),
        TurnField.NONCE: payload.get(CommitKey.NONCE.value),
        TurnField.INTENT: payload.get(CommitKey.INTENT.value),
        TurnField.STATE: payload.get(CommitKey.STATE.value),
        TurnField.MOVE: payload.get(CommitKey.MOVE.value),
        TurnField.COMMITMENT: {
            WireSide.SENT: _h_commit(sent.get(MessageType.COMMIT.value)),
            WireSide.RECEIVED: _h_commit(received.get(MessageType.COMMIT.value)),
            WireSide.ACKED: _h_commit(sent.get(MessageType.ACK.value)),
        },
        TurnField.REVEALED_MOVE: {
            WireSide.SENT: sent.get(MessageType.REVEAL.value),
            WireSide.RECEIVED: received.get(MessageType.REVEAL.value),
        },
        TurnField.HINT: {
            WireSide.OUTGOING: outgoing_hint(language),
            WireSide.SENT: sent.get(MessageType.HINT.value),
            WireSide.RECEIVED: received.get(MessageType.HINT.value),
        },
        TurnField.VERDICT: verdict,
        TurnField.PEER_CLAIMED_TURNS: peer_claimed_turns,
    }
