"""D-46 / rule 23 scent-digest suite for the D-08 handshake.

Split from tests/unit/test_handshake.py at the 150-code-line gate (QUAL-02: the shared
fakes -- FakeReporter/fake_caller/peer_reply -- live there and are imported here, not
duplicated), the same split pattern test_handshake_abort.py and test_handshake_client.py
already use. Covers the four cases plan 04-02's Task 2 requires: both digests agree, config
differs, scent differs, scent absent from the peer's payload -- plus the mutated-kernel
end-to-end case and the pre-04-12 backward-compatible skip path (see handshake_evaluate.py's
_compare_offer docstring).
"""

import dataclasses

from pursuit.network.config_hash import config_digest
from pursuit.network.handshake import HandshakeOutcome, perform_handshake, respond_to_handshake
from pursuit.network.state_machine import State, TurnStateMachine
from pursuit.shared.scent_config import load_scent_model, scent_digest
from tests.unit.test_handshake import FakeReporter, fake_caller, peer_reply

_CONFIG_DIGEST = config_digest("config/police/game_params.json")
_SCENT_MODEL = load_scent_model("config/police/scent.json")
_SCENT_DIGEST = scent_digest(_SCENT_MODEL)
_SHIPPED_SCENT_DIGEST = "c0e63220b31f5b82a0354534ff5cc12abd6fc1fd45460a8c4794c8150cff4c9e"

# A one-cell-family kernel mutation (all four corners, the smallest symmetric orbit) --
# proves a scent.json that would still LOAD (kernel stays symmetric, centre untouched)
# nonetheless produces a different digest and voids the lock (rule 23).
_MUTATED_KERNEL = tuple(
    tuple(0.05 if (r, c) in {(0, 0), (0, 4), (4, 0), (4, 4)} else v for c, v in enumerate(row))
    for r, row in enumerate(_SCENT_MODEL.kernel)
)
_MUTATED_MODEL = dataclasses.replace(_SCENT_MODEL, kernel=_MUTATED_KERNEL)
_MUTATED_SCENT_DIGEST = scent_digest(_MUTATED_MODEL)


def test_mutation_fixture_actually_changes_the_digest():
    """Sanity check on the fixture itself -- the corner mutation is not a no-op."""
    assert _MUTATED_SCENT_DIGEST != _SCENT_DIGEST


def test_real_scent_config_pair_agrees_and_pins_shipped_digest():
    """D-46 end to end on the ACTUAL repo files -- the value 04-01-SUMMARY.md ships and the
    league opponent must be sent before a match."""
    police = scent_digest(load_scent_model("config/police/scent.json"))
    thief = scent_digest(load_scent_model("config/thief/scent.json"))
    assert police == thief == _SHIPPED_SCENT_DIGEST


async def test_both_digests_agree_including_scent():
    """Case 1: config AND scent both match -> AGREED, state advances, nothing reported."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_scent_digest=_SCENT_DIGEST,
        call_peer=fake_caller(peer_reply(_CONFIG_DIGEST, "thief", peer_scent_digest=_SCENT_DIGEST)),
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "scent" in result.detail
    assert machine.state is State.HANDSHAKE
    assert reporter.calls == []


async def test_config_mismatch_named_even_when_scent_would_agree():
    """Case 2: config differs -> CONFIG_MISMATCH is named, regardless of a matching scent
    digest -- config is checked first and its failure is never masked."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    wrong_config = "0" * len(_CONFIG_DIGEST)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_scent_digest=_SCENT_DIGEST,
        call_peer=fake_caller(peer_reply(wrong_config, "thief", peer_scent_digest=_SCENT_DIGEST)),
    )
    assert result.outcome is HandshakeOutcome.CONFIG_MISMATCH
    assert "config" in result.detail
    assert machine.state is State.ERROR


async def test_scent_digest_mismatch_aborts_naming_scent():
    """Case 3: config matches, scent differs -> SCENT_MISMATCH, named in the detail, ERROR."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    wrong_scent = "0" * len(_SCENT_DIGEST)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_scent_digest=_SCENT_DIGEST,
        call_peer=fake_caller(peer_reply(_CONFIG_DIGEST, "thief", peer_scent_digest=wrong_scent)),
    )
    assert result.outcome is HandshakeOutcome.SCENT_MISMATCH
    assert result.aborted is True
    assert machine.state is State.ERROR
    assert "scent" in result.detail
    assert _SCENT_DIGEST in result.detail and wrong_scent in result.detail


async def test_scent_digest_absent_from_peer_aborts_naming_absent_key():
    """Case 4: WE opted in, the peer's reply carries no scent key at all -> a mismatch, and
    the detail says ABSENT, not "differed" (an operator must tell the two apart)."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_scent_digest=_SCENT_DIGEST,
        call_peer=fake_caller(peer_reply(_CONFIG_DIGEST, "thief")),  # no scent key sent
    )
    assert result.outcome is HandshakeOutcome.SCENT_MISMATCH
    assert machine.state is State.ERROR
    assert "absent" in result.detail
    assert "differ" not in result.detail.lower()


async def test_local_not_opted_in_skips_scent_even_if_peer_sends_one():
    """A call site not yet migrated to pass local_scent_digest (pre-04-12) still gets a
    config-only AGREEMENT even when the peer's reply happens to carry a scent digest -- we
    never validate what we did not ourselves ask to validate."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        call_peer=fake_caller(
            peer_reply(_CONFIG_DIGEST, "thief", peer_scent_digest="anything-at-all")
        ),
    )
    assert result.outcome is HandshakeOutcome.AGREED
    assert "scent" not in result.detail


async def test_mutated_scent_kernel_aborts_via_perform_handshake():
    """A one-cell-family kernel mutation on the PEER's side aborts the initiator end to end
    (rule 23)."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    result = await perform_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="police",
        local_scent_digest=_SCENT_DIGEST,
        call_peer=fake_caller(
            peer_reply(_CONFIG_DIGEST, "thief", peer_scent_digest=_MUTATED_SCENT_DIGEST)
        ),
    )
    assert result.outcome is HandshakeOutcome.SCENT_MISMATCH
    assert machine.state is State.ERROR


def test_mutated_scent_kernel_aborts_via_respond_to_handshake():
    """The SAME mutation aborts the RESPONDER too (NET-03 symmetry) -- a one-cell kernel
    difference voids the game on BOTH sides before move 1, not just the initiator's."""
    reporter = FakeReporter()
    machine = TurnStateMachine(reporter)
    _, result = respond_to_handshake(
        machine=machine, reporter=reporter, local_digest=_CONFIG_DIGEST, local_role="thief",
        local_scent_digest=_MUTATED_SCENT_DIGEST,
        incoming=peer_reply(_CONFIG_DIGEST, "police", peer_scent_digest=_SCENT_DIGEST),
    )
    assert result.outcome is HandshakeOutcome.SCENT_MISMATCH
    assert machine.state is State.ERROR
