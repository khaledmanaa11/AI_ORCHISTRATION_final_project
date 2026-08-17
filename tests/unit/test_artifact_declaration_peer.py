"""The PEER half of the declaration artifact, and the outside-the-signature
container's validation.

Split from `test_artifact_declaration.py` at the 150-code-line gate. The peer
half is its own subject: everything under `declarations.peer` is whatever the
opponent sent, so `security/audit.py`'s boundary rule applies -- an ill-shaped
value is EVIDENCE (False) and never an exception that takes the artifact
writer down with it.
"""

import pytest

from pursuit.security.step0_sign import SignKey
from pursuit.services.reporting import artifact_declaration as decl
from tests.unit.artifact_declaration_fixtures import (
    SECRET,
    make_artifact,
    make_context,
    make_envelope,
)

# Shapes a peer can legally put on the wire that no digest can be read from.
_MALFORMED_PEER_ENVELOPES = (
    "not-a-dict",
    7,
    [],
    {},
    {"declaration": "a string, not the ten keys", "digest": "0" * 64},
    {"declaration": {"role": "thief"}, "digest": 12345},
)

_BAD_CONTEXTS = (
    ({"repo_urls": "not-a-dict"}, TypeError),
    ({"mcp_server_addresses": None}, TypeError),
    ({"token_ceiling": True}, TypeError),
    ({"token_ceiling": "200000"}, TypeError),
    ({"token_ceiling": 0}, ValueError),
    ({"token_ceiling": -1}, ValueError),
    ({"start_time": ""}, ValueError),
    ({"start_time": 17}, ValueError),
    ({"end_time": 17}, TypeError),
)


def test_the_peer_tables_are_intact():
    """ANTI-VACUITY GUARD for both parametrize sources below."""
    assert len(_MALFORMED_PEER_ENVELOPES) == 6
    assert len(_BAD_CONTEXTS) == 9


@pytest.mark.parametrize("malformed", _MALFORMED_PEER_ENVELOPES)
def test_a_malformed_peer_envelope_is_evidence_not_an_exception(malformed):
    artifact = make_artifact(peer_envelope=malformed)
    assert decl.verify_embedded_declarations(artifact, secret=None)["peer"] is False


def test_a_non_string_hmac_from_a_peer_is_rejected_without_raising():
    """`verify_declaration` would hand a non-str to `digests_match`, whose
    strict D-46 contract raises TypeError. The guard turns that into a verdict."""
    envelope = make_envelope(SECRET)
    envelope[SignKey.HMAC] = ["not", "a", "string"]
    artifact = make_artifact(peer_envelope=envelope)
    assert decl.verify_embedded_declarations(artifact, secret=SECRET)["peer"] is False


def test_the_malformed_peer_check_can_fail():
    """COUNTER-CONTROL: a WELL-formed peer envelope must verify True, so the
    table above is reading the guard rather than a blanket False."""
    artifact = make_artifact(peer_envelope=make_envelope(SECRET, role="thief"))
    assert decl.verify_embedded_declarations(artifact, secret=SECRET)["peer"] is True


def test_an_unsigned_peer_verifies_on_its_digest_alone():
    """`sign_declaration(secret=None)` produces `signed: False, hmac: None`;
    signed and unsigned peers must not be conflated."""
    envelope = make_envelope(None, role="thief")
    assert envelope[SignKey.SIGNED] is False
    artifact = make_artifact(peer_envelope=envelope)
    assert decl.verify_embedded_declarations(artifact, secret=None)["peer"] is True


@pytest.mark.parametrize(("override", "expected"), _BAD_CONTEXTS)
def test_the_outside_content_container_fails_loud(override, expected):
    """A malformed context must raise rather than write a malformed artifact
    -- and `token_ceiling=True` is in the table because bool is an int
    subclass and would otherwise ship a ceiling of 1."""
    good = make_context()
    fields = {
        "repo_urls": good.repo_urls,
        "mcp_server_addresses": good.mcp_server_addresses,
        "token_ceiling": good.token_ceiling,
        "start_time": good.start_time,
        "end_time": good.end_time,
    }
    with pytest.raises(expected):
        decl.DeclarationContext(**{**fields, **override})


def test_an_aborted_game_may_carry_a_null_end_time():
    """An honest null beats a fabricated timestamp."""
    good = make_context()
    context = decl.DeclarationContext(
        repo_urls=good.repo_urls,
        mcp_server_addresses=good.mcp_server_addresses,
        token_ceiling=good.token_ceiling,
        start_time=good.start_time,
        end_time=None,
    )
    assert context.end_time is None


def test_the_context_invents_no_number():
    """Every field is required: there is no default for `token_ceiling`, so a
    caller without an agreed ceiling gets a TypeError instead of a number."""
    with pytest.raises(TypeError):
        decl.DeclarationContext(repo_urls={}, mcp_server_addresses={})
