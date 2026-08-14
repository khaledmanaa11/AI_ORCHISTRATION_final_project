"""D-60's committed state record, READ (05-05, 05-UAT.md G2).

Split out of `audit.py` at the 150-code-line gate (Segal Table 5) the moment
this check and its reasoning landed there. The seam is the one the two files
already describe: `audit.py` owns D-67's payload/coverage audit -- what the
peer CLAIMED versus what we SAW -- while this module owns the anti-replay
STEP BINDING the record itself carries (PRD_commit_reveal.md:121-123).
`audit.py` imports `state_binding_detail` back and calls it from `_audit_one`
at an exact position; see that call site.

Until this module existed the state record was write-only: a probe reported a
forged `{game_id: OTHER-GAME, turn: 99, role: police}` record as "matched",
because the audit only ever re-hashed the whole payload -- which trivially
succeeds on a payload the peer hashed itself.

Pure function, no ctx, no network -- `agent_audit_wiring.run_final_audit`
supplies both parameters.
"""

from __future__ import annotations

from pursuit.security import commit_pack
from pursuit.security.ledger import LedgerField
from pursuit.security.state_record import StateRecordKey


# --- Why game_id is checked by MEMBERSHIP, and what this does NOT contain --
#
# `state.game_id` is validated against the set of ids that were ON THE TABLE
# at handshake -- `{our minted uid, the id the peer published}`, captured
# inside `game_identity.adopt_negotiated_game_id` BEFORE it rebinds
# `ctx.game_uid`. Never equality with one of them. D-61 is a PROJECT
# decision, not a book rule: `handshake_evaluate` reads `peer_game_id`
# unconditionally, nothing requires a peer to adopt ours, and nothing
# requires a peer to keep its own -- so BOTH conventions must pass, on BOTH
# roles. Two equality shapes were considered and BOTH false-accuse (rules
# 16/22):
#   - equality gated on the peer having PUBLISHED an id accuses a symmetric
#     honest opponent that publishes its own id and keeps it, on turn 1 of
#     every game;
#   - equality gated on THIS side having ADOPTED (`game_uid ==
#     negotiated_game_id`) proves only that WE adopted, never that THEY
#     kept. `handshake_wire.build_offer` puts our game_id into the payload
#     and the SAME builder makes the reply, so a foreign peer genuinely sees
#     our id. If it adopts ours while we adopt theirs -- two honest
#     implementations that merely swap conventions -- each side's records
#     carry the id the other side rejects and BOTH declare a technical loss.
#     That shape also silently disables the check in every game we play as
#     police, since police never adopts.
# Membership accepts either convention, rejects a foreign game's id either
# way, and stays live on both roles.
#
# THREE limitations, stated because a fairness trade nobody can read is a
# trade nobody can audit:
#   (a) a peer that publishes NO game_id at handshake is not bound
#       cross-game at all -- the caller passes None and this check is
#       skipped entirely;
#   (b) a peer that publishes a PRIOR GAME'S id at handshake makes that
#       game's records satisfy membership, so this check does not stop a
#       determined cross-game replay either. What contains that residue is
#       `audit._audit_one`'s LAST check, `payload.move !=
#       observed_reveals[turn]`: a replayed record obliges the attacker to have actually
#       played the old move, which `decode_revealed_action` already
#       validated as legal from their current position -- a handicap, not an
#       exploit. It is NOT contained by `verify_reveal`: that re-hashes the
#       peer's payload against whatever `h_commit` string the peer chose to
#       send THIS game, so an attacker simply commits `h_old` and presents
#       the matching old payload and the re-hash passes;
#   (c) considered and DECLINED: a peer deriving a THIRD id (a hash of both,
#       the lexicographic min) is accused under any candidate-set rule. No
#       mechanism can cover an unbounded space of conventions; noted so the
#       next reader knows it was weighed rather than missed.
def state_binding_detail(
    entry: dict, *, candidate_game_ids: set[str] | None, forbidden_role: str | None,
) -> str | None:
    """D-60's committed state record, READ (05-05, 05-UAT.md G2) -- the
    anti-replay step-binding PRD_commit_reveal.md:121-123 says the record
    exists for. Until this function existed the record was write-only: a
    probe reported a forged `{game_id: OTHER-GAME, turn: 99, role: police}`
    record as "matched", because the audit only ever re-hashed the whole
    payload, which trivially succeeds on a payload the peer hashed itself.

    Returns the FIRST failing check's detail, or None when every enabled
    check passes. Runs against PEER-SUPPLIED data, so a state record missing
    any of its D-60 fields is a named mismatch, never a KeyError -- every
    field is read with `.get()`. The `isinstance` guard below is a BACKSTOP,
    not the live containment: with the call order in `_audit_one`,
    `verify_reveal` has already proved `state` is a dict, and a payload where
    it is not becomes a named mismatch there. Kept so a future reordering
    degrades to a mismatch rather than an AttributeError.

    `forbidden_role` is a NEGATIVE check, never equality with the token WE
    expect. `state.role` is the peer's OWN record content; book Sec5.3.1
    shares the canonical-JSON RECIPE, not the contents, and this repo alone
    carries two role vocabularies (`orchestrator.opponent_role` ->
    police/thief, `orchestrator.engine_agent` -> cop/thief). An honest
    opponent writing `"cop"` would be technically-lost by an equality check
    -- the exact false-accusation trap 06-05 recorded as deliberately
    declined. Anchoring on what must NOT appear keeps the property and
    imposes nothing."""
    turn = entry[LedgerField.TURN]
    state = entry.get(LedgerField.PAYLOAD, {}).get(commit_pack.CommitKey.STATE.value)
    if not isinstance(state, dict):
        return f"turn {turn}: committed state record is missing or malformed"
    claimed_turn = state.get(StateRecordKey.TURN.value)
    if claimed_turn != turn:
        return f"turn {turn}: committed state record names turn {claimed_turn!r} (replay)"
    if forbidden_role is not None and state.get(StateRecordKey.ROLE.value) == forbidden_role:
        return (
            f"turn {turn}: committed state record claims to have been written by "
            f"{forbidden_role!r} -- a replay of that side's own commits"
        )
    claimed_game = state.get(StateRecordKey.GAME_ID.value)
    if candidate_game_ids is not None and claimed_game not in candidate_game_ids:
        return (
            f"turn {turn}: committed state record names game {claimed_game!r}, which was not "
            "one of the ids on the table at handshake"
        )
    return None
