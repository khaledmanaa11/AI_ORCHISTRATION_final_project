"""`declaration_<game_id>.json`: the wrapper must add nothing inside the
signature (D-71).

The envelopes are built by the REAL `step0_sign.sign_declaration` over the
real §5.5 key set and re-verified by the REAL `step0_sign.verify_declaration`
AFTER a round trip through the writer and back off disk. A hand-rolled digest
would prove only that this file agrees with itself.

The peer-supplied boundary half lives in `test_artifact_declaration_peer.py`,
split at the 150-code-line gate; both draw on
`tests/unit/artifact_declaration_fixtures.py`.
"""

import json

import pytest

from pursuit.security.step0_sign import SignKey
from pursuit.services.reporting import artifact_declaration as decl
from tests.unit.artifact_declaration_fixtures import (
    GAME_UID,
    SEC55,
    SECRET,
    SECRETS,
    make_artifact,
    make_context,
    make_envelope,
)

_OUTSIDE_FIELDS = (
    "repo_urls", "mcp_server_addresses", "token_ceiling", "start_time", "end_time",
)


def test_the_declaration_fixtures_are_intact():
    """ANTI-VACUITY GUARD -- a thinned §5.5 set, `_SECRETS` or
    `_OUTSIDE_FIELDS` would make the parametrized tests below skip silently
    and leave this file reading green."""
    assert len(SEC55) == 10
    assert len(SECRETS) == 2
    assert len(_OUTSIDE_FIELDS) == 5


def _round_trip(tmp_path, artifact, secret):
    path = decl.write_declaration_artifact(tmp_path / "game_artifacts", artifact, secret=secret)
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("secret", SECRETS)
def test_both_signatures_still_verify_after_the_wrap_and_a_round_trip(tmp_path, secret):
    """THE TEST THAT MATTERS. One perturbed byte inside either signed payload
    and this fails."""
    artifact = decl.build_declaration_artifact(
        game_uid=GAME_UID,
        game_id=GAME_UID,
        own_envelope=make_envelope(secret),
        peer_envelope=make_envelope(secret, role="thief"),
        context=make_context(),
    )
    reloaded = _round_trip(tmp_path, artifact, secret)
    assert decl.verify_embedded_declarations(reloaded, secret=secret) == {"own": True, "peer": True}


@pytest.mark.parametrize("secret", SECRETS)
def test_a_key_injected_inside_the_signed_dict_fails_verification(tmp_path, secret):
    """THE COUNTER-CONTROL D-71 EXISTS FOR. Adding one field inside the signed
    declaration is what would abort every game at the handshake, so the check
    above must be able to catch it -- and the writer must refuse to ship it."""
    artifact = make_artifact(own_secret=secret)
    artifact["declarations"]["own"][decl.ENVELOPE_DECLARATION_KEY]["repo_url"] = "injected"
    assert decl.verify_embedded_declarations(artifact, secret=secret) == {"own": False}
    with pytest.raises(ValueError, match="failed re-verification"):
        decl.write_declaration_artifact(tmp_path / "game_artifacts", artifact, secret=secret)


def test_a_perturbed_digest_also_fails():
    artifact = make_artifact()
    artifact["declarations"]["own"][SignKey.DIGEST] = "0" * 64
    assert decl.verify_embedded_declarations(artifact, secret=None) == {"own": False}


@pytest.mark.parametrize("field", _OUTSIDE_FIELDS)
def test_the_outside_content_is_outside_every_signature(field):
    """PARAMETERS' remaining content sits at the TOP LEVEL and inside no
    signed dict -- which is why the signatures above survive it."""
    artifact = make_artifact(own_secret=SECRET)
    signed = artifact["declarations"]["own"][decl.ENVELOPE_DECLARATION_KEY]
    assert field in artifact
    assert field not in signed


def test_the_signed_key_set_is_exactly_the_ten_sec55_keys():
    signed = make_artifact(own_secret=SECRET)["declarations"]["own"]
    assert set(signed[decl.ENVELOPE_DECLARATION_KEY]) == set(SEC55)


def test_the_envelope_is_embedded_verbatim():
    """Stored by reference and unaltered: the wrapper reads no key inside the
    envelope and writes none."""
    envelope = make_envelope(SECRET)
    before = json.dumps(envelope, sort_keys=True)
    artifact = decl.build_declaration_artifact(
        game_uid=GAME_UID, game_id=GAME_UID, own_envelope=envelope,
        peer_envelope=None, context=make_context(),
    )
    assert artifact["declarations"]["own"] is envelope
    assert json.dumps(envelope, sort_keys=True) == before


def test_a_digest_only_peer_gets_an_honest_absence(tmp_path):
    """No fabricated empty declaration: `peer` is null and the artifact says
    why, and the absence contributes no verification verdict."""
    reloaded = _round_trip(tmp_path, make_artifact(), None)
    assert reloaded["declarations"]["peer"] is None
    assert reloaded["peer_declaration_status"] == decl.PEER_ABSENT_DETAIL
    assert decl.verify_embedded_declarations(reloaded, secret=None) == {"own": True}


def test_the_artifact_is_named_and_placed_by_the_spine(tmp_path):
    path = decl.write_declaration_artifact(
        tmp_path / "game_artifacts", make_artifact(), secret=None
    )
    assert path.name == f"declaration_{GAME_UID}.json"


def test_the_writer_inherits_the_d7_1_refusal(tmp_path):
    """It goes through `artifacts.write_artifact`, so `logs/` is refused here
    too -- the one tree today's declaration precursor actually lands in."""
    with pytest.raises(ValueError, match="D7-1"):
        decl.write_declaration_artifact(tmp_path / "logs" / "police", make_artifact(), secret=None)
