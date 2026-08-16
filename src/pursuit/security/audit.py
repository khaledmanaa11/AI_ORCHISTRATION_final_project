"""D-67: the Final-Reveal mutual audit.

Hash-verifying a revealed `{state,move,intent,nonce}` payload against
`H_commit` ALONE is bypassable: commit honestly to X, play Y in the
in-game REVEAL, present X at final reveal -- the hash matches and the
forgery survives. `audit_peer_records` closes this by ALSO cross-checking
the revealed composite action dict against the action THIS SIDE actually
observed in that turn's in-game REVEAL envelope (its own wire log).

Rule 36 coverage check: auditing only the entries the PEER chose to
include is itself bypassable -- an opponent sending `{"records": []}`
(the cheapest possible evasion) would otherwise pass vacuously.
`audit_peer_records` ALSO requires every turn THIS side watched fully
exchanged (committed AND revealed in-game) to be present in
`peer_records` at all; a missing one is a mismatch, not a silent skip.

A turn with an observed COMMIT but no observed REVEAL is a legitimately
TRAILING turn, not evidence of anything: `CommitLedger.append` runs
BEFORE the REVEAL send (turn_commit_wait.py), so an abnormal ending can
leave an honest peer with a committed-never-revealed entry in its own
final reveal. Such an entry is `matched=True` once its commit/hash check
out -- there is nothing played that turn to cross-check against.

D-60 committed-state binding (05-05, 05-UAT.md G2): `_audit_one` also reads
`payload.state` -- the peer's own committed record -- and rejects a replay
whose `turn`, `role` or `game_id` disagrees with local truth. That check and
ALL of its reasoning (why `game_id` is checked by MEMBERSHIP in this game's
candidate ids rather than by equality with one of them, and the THREE stated
limitations of that choice) live in the sibling `audit_state.py`, split out
at the 150-code-line gate the moment they landed here. Read that file before
changing the check: two equality shapes were tried and both false-accuse an
honest peer (rules 16/22).

Pure function, no network, no ctx (Task 3's own contract) -- Task 4 wires
this against real `observed_commits`/`observed_reveals`/`peer_records`
built from `ctx.log_path`'s own JSONL and this side's own `CommitLedger`.
The SAME function also audits THIS side's own ledger against what it
actually sent (CONTEXT, locked: symmetric honesty) -- only the caller's
sent/received direction differs; the coverage check applies identically
in both directions, no special-casing needed.
"""

from __future__ import annotations

from pursuit.security import commit_pack
from pursuit.security.audit_record import AuditRecord, all_matched
from pursuit.security.audit_shape import NO_USABLE_TURN, container_detail, join_key_turn
from pursuit.security.audit_state import state_binding_detail

# AuditRecord/all_matched are RE-EXPORTED from audit_record.py (split at the
# 150-code-line gate when this plan's guards landed), so every pre-05-10
# importer of this module resolves unchanged. An immutable tuple, not a list, so
# it is not module-level mutable state (NET-02).
__all__ = ("AuditRecord", "all_matched", "audit_peer_records")

# --- THE BOUNDARY RULE, written where the boundary is --------------------
#
# ANY function that reads a structure the PEER sent must treat malformed input
# as a NAMED MISMATCH, never as an exception. Not a crash, and not a free pass
# either: a peer whose records we cannot parse has not published usable nonces,
# which is exactly what rule 36 sanctions, so it must still LOSE. What changes
# is that we reach a verdict instead of dying before writing one.
#
# This is written once, here, because ONE pattern produced SIX separate defects
# in Phase 5, each found by a different pass and each with the same consequence:
# an unhandled exception on peer-controlled data escapes to main.py and kills
# the process, so WE become the side that published no nonces (rule 36) and our
# own log carries no verdict at all -- the artifact machine B produced on
# 2026-08-13.
#
#   1. `httpx.ConnectError` escaping `call_with_retry` (05-04 found, 05-09 closed).
#   2. The wrapped `RuntimeError("Client failed to connect: ...") from exc`
#      connect shape (05-09 found and closed in flight; a widened tuple ALONE
#      still let the artifact through).
#   3. `commit_pack.verify_reveal(**payload)` raising `TypeError` on any other
#      payload shape (05-05 found and contained at `_audit_one`, below).
#   4. `audit_peer_records` raising on a malformed FINAL_REVEAL -- at the raw
#      `entry["turn"]`, at `_missing_turns`' set comprehension and at the final
#      numeric sort, ALL of them outside instance 3's try/except (05-VERIFICATION
#      found it by probe; 05-10 closed it).
#   5. `commit_pack.build_commit_payload` raising `ValueError` on a
#      peer-controlled `intent` outside {truth, lie}, or on an empty `nonce` --
#      NOT caught by instance 3's `(TypeError, KeyError)`. Found reviewing 05-10,
#      inside the very function that plan hardens; closed by widening below.
#   6. `handshake_step0._step0_verified` raising `AttributeError` on a
#      `step0_declaration` that is not an object -- found sweeping for a sixth
#      during 05-10 and closed in that module the same way.
#
# THE HANDSHAKE CORRIDOR (05-12). Instances 1-6 were found one at a time, each
# by a different pass. 05-12 stopped doing that and swept the corridor: EVERY
# peer-controlled value read between `Envelope.from_dict` and move 1. Four more
# came out of it, and the count is the point -- 05-10 closed instance 6 in this
# very corridor and still left three doors open one function further in.
#
#   7. `config_hash.digests_match` raising `TypeError` on a non-str peer
#      digest, reached UNCONDITIONALLY at `handshake_evaluate.py:118` (config)
#      and, because `agent_entrypoint.py:80,85` always supplies
#      `local_scent_digest`, at `:124-125` (scent) too. BOTH sit OUTSIDE the
#      try/except at `:151-156`, which wraps the DECODE block only -- reading
#      `envelope.payload[DIGEST]` is a plain dict lookup that succeeds for an
#      int. Closed in `config_hash.unusable_peer_digest`, the ONE gate every
#      peer-supplied digest slot now passes; `digests_match` keeps its strict
#      contract for internal callers (D-46).
#   8. `HandshakeResult.peer_game_id` -- read verbatim at
#      `handshake_evaluate.py:162` -- reaching a set constructor (unhashable ->
#      `TypeError`) and a `Path.replace` (traversal, embedded NUL ->
#      `ValueError`, over-long -> `OSError`) inside `adopt_negotiated_game_id`,
#      which has no guard at all. Closed in `game_identity_validate`.
#   9. The SAME `digests_match` raise reached TWICE MORE through
#      `step0_sign.verify_declaration` -- a non-str `step0_digest`, and a
#      non-str `hmac` inside the peer's declaration envelope. Both fire only
#      when the peer ALSO sends a declaration, which is why 05-10's sweep,
#      stopping at the declaration CONTAINER (instance 6), passed straight over
#      them. Closed in `handshake_step0`, and DOWNGRADED rather than aborted:
#      see that module on why an abort there would have been a new
#      false-accusation path bought for no evasion closed.
#
# A TENTH IS A REVIEW FAILURE, NOT A DISCOVERY -- and the seventh through ninth
# say why the bar is that high: instance 7 had a GREEN TEST certifying the
# crash as intended (`test_config_hash.py:131-135`, `pytest.raises(TypeError)`),
# so "the suite is green" has already failed once as evidence here. The rule is
# not "catch exceptions"; it is: name every peer-controlled value a function
# reads, and say what that function returns for each shape it can arrive in.
# -------------------------------------------------------------------------


def _audit_one(
    entry: dict, observed_commits: dict[int, str], observed_reveals: dict[int, dict],
    *, candidate_game_ids: set[str] | None, forbidden_role: str | None,
) -> AuditRecord:
    """Per-entry checks, in order; the FIRST failing check's detail is
    reported -- never computed-but-hidden. See module docstring for why a
    trailing commit-without-reveal is `matched=True`, not a mismatch.

    The SHAPE gate runs first (boundary rule above, instance 4): an entry that
    cannot serve as a join key is a named mismatch carrying `NO_USABLE_TURN`,
    never the raw `entry["turn"]` that used to raise here."""
    turn, shape_detail = join_key_turn(entry)
    if turn is None:
        return AuditRecord(turn=NO_USABLE_TURN, matched=False, detail=shape_detail)
    if turn not in observed_commits:
        return AuditRecord(turn=turn, matched=False, detail=f"turn {turn}: no observed commit")
    # `verify_reveal(h, **payload)` requires EXACTLY {state,move,intent,nonce}
    # with state/move dicts, so any other shape raises out of a function
    # running on PEER-SUPPLIED data -- and nothing upstream catches TypeError
    # (`agent_entrypoint`'s guard is `except ToolError`), so the process would
    # die before recording any verdict and WE would become the side that
    # published no nonces (rule 36). A malformed payload is evidence, so it
    # becomes a named mismatch here rather than an exception. This is the one
    # production call site that sees peer data (grep: the only other caller is
    # scripts/gate6_tamper.py, over records it built itself).
    #
    # ValueError is INSTANCE 5 of the boundary rule above and was missing here
    # until 05-10: `build_commit_payload` raises it -- not TypeError -- for a
    # peer-controlled `intent` outside {truth, lie} and for an empty `nonce`.
    # Measured: `ValueError: build_commit_payload: intent must be one of
    # ['lie', 'truth'], got 'maybe'` escaped this clause, escaped
    # `audit_peer_records`, and `agent_entrypoint` guards only ToolError.
    try:
        rehash_ok = commit_pack.verify_reveal(observed_commits[turn], **entry["payload"])
    except (TypeError, KeyError, ValueError) as exc:
        return AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: malformed final-reveal payload -- {exc}",
        )
    if not rehash_ok:
        return AuditRecord(
            turn=turn, matched=False, detail=f"turn {turn}: re-hash does not match H_commit",
        )
    # PLACEMENT IS EXACT: after the re-hash and BEFORE the trailing-commit
    # early return below. Placed after it, a replayed record would take the
    # trailing-commit exemption -- matched=True -- and skip the state checks
    # entirely, which is the exact shape of the bug 06-05 already fixed once.
    state_detail = state_binding_detail(
        entry, candidate_game_ids=candidate_game_ids, forbidden_role=forbidden_role,
    )
    if state_detail is not None:
        return AuditRecord(turn=turn, matched=False, detail=state_detail)
    if turn not in observed_reveals:
        return AuditRecord(
            turn=turn, matched=True,
            detail=f"turn {turn}: trailing commit, no in-game reveal observed -- hash verified",
        )
    if entry["payload"]["move"] != observed_reveals[turn]:
        return AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: revealed action does not match what was actually played (D-67)",
        )
    return AuditRecord(turn=turn, matched=True, detail=f"turn {turn}: matched")


def _missing_turns(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
) -> list[AuditRecord]:
    """Rule 36 coverage check: a turn watched FULLY exchanged (committed
    AND revealed in-game) but simply absent from `peer_records` -- e.g.
    every turn, via an empty `{"records": []}` -- is itself a mismatch.

    An entry we cannot parse REPORTS NO TURN and is skipped when building
    `reported`; the check keeps running for every other entry. The whole check
    must NOT bail on one malformed entry: a peer would then append a single
    garbage record and this coverage check would silently vanish for ALL of its
    valid turns -- the `{"records": []}` evasion re-opened through a side
    door."""
    reported = {turn for turn, _ in map(join_key_turn, peer_records) if turn is not None}
    fully_exchanged = set(observed_commits) & set(observed_reveals)
    return [
        AuditRecord(
            turn=turn, matched=False,
            detail=f"turn {turn}: committed and revealed in-game but absent from final reveal",
        )
        for turn in sorted(fully_exchanged - reported)
    ]


def audit_peer_records(
    observed_commits: dict[int, str], observed_reveals: dict[int, dict], peer_records: list[dict],
    *, candidate_game_ids: set[str] | None = None, forbidden_role: str | None = None,
) -> list[AuditRecord]:
    """Audit every `peer_records` entry (`{"turn","h_commit","payload":
    {"state","move","intent","nonce"}}`) against what THIS side observed on
    the wire, PLUS the coverage check above. A genuinely turn-less game
    (nothing fully exchanged, nothing claimed) returns an empty list --
    vacuously matched, correctly (a game that died at handshake has
    nothing to audit).

    *candidate_game_ids* and *forbidden_role* (05-05) enable the two
    OPTIONAL halves of the committed-state binding; both default to None
    (that half skipped), so every pre-existing caller and fixture is
    untouched. `state.turn == entry["turn"]` needs no parameter and is
    ALWAYS enforced: `commit_own_action` passes ONE `turn` to both the
    record and the append, so it holds for every honest ledger by
    construction. `agent_audit_wiring.run_final_audit` is the production
    supplier -- the SAME `ctx.candidate_game_ids` set for both directions,
    passed through unchanged and never reconstructed, with `forbidden_role`
    the only per-direction difference.

    Total over peer-supplied input (the boundary rule above): an unreadable
    CONTAINER is one named mismatch and nothing else -- it does not fall through
    to the coverage check, so an unparseable peer and the `{"records": []}`
    evasion stay distinguishable in our own evidence even though both lose."""
    container = container_detail(peer_records)
    if container is not None:
        return [AuditRecord(turn=NO_USABLE_TURN, matched=False, detail=container)]
    records = [
        _audit_one(
            entry, observed_commits, observed_reveals,
            candidate_game_ids=candidate_game_ids, forbidden_role=forbidden_role,
        )
        for entry in peer_records
    ]
    records.extend(_missing_turns(observed_commits, observed_reveals, peer_records))
    records.sort(key=lambda record: record.turn)
    return records
