"""`config_<game_id>_g<NN>.json`: locked to the same config the game was.

The digest half and the byte-identity half. The seal / round-trip half lives
in `test_artifact_config_seal.py`, split at the 150-code-line gate; both draw
on `tests/unit/artifact_config_fixtures.py`.
"""

import hashlib
import json
import shutil

import pytest

from pursuit.network.config_hash import canonical_json, config_digest
from pursuit.services.reporting import artifact_config
from pursuit.shared.scent_config import load_scent_model, scent_digest
from tests.unit.artifact_config_fixtures import GAME_UID, ROLES, build, config_dir

# Values that identify ONE agent and must never reach an artifact rule 11
# requires to be byte-identical on both sides.
_PER_AGENT_LEAKS = ("opponent_url", "8001", "8002", "role", "team_code", "khm-mn17")


def test_the_role_and_leak_tables_are_intact():
    """ANTI-VACUITY GUARD for every parametrize in this file."""
    assert len(ROLES) == 2
    assert len(_PER_AGENT_LEAKS) == 6
    assert len(artifact_config.AGREED_CONFIG_STEMS) == 3


@pytest.mark.parametrize("role", ROLES)
def test_embedded_game_params_recomputes_to_the_handshake_digest(role):
    """THE LOAD-BEARING ASSERTION. SHA-256 over `canonical_json` of the
    embedded object must equal `config_digest(config_dir/game_params.json)` --
    the exact string `agent_entrypoint.py:80` puts on the handshake wire."""
    artifact = build(role)
    embedded = artifact[artifact_config.ConfigArtifactField.CONFIG]["game_params"]
    recomputed = hashlib.sha256(canonical_json(embedded).encode("utf-8")).hexdigest()
    on_the_wire = config_digest(config_dir(role) / "game_params.json")
    assert recomputed == on_the_wire
    assert artifact[artifact_config.ConfigArtifactField.HANDSHAKE_DIGESTS]["game_params"] == (
        on_the_wire
    )


@pytest.mark.parametrize("role", ROLES)
def test_embedded_scent_recomputes_to_the_handshake_scent_digest(role):
    """The second digest actually exchanged before move 1 (D-46)."""
    artifact = build(role)
    embedded = artifact[artifact_config.ConfigArtifactField.CONFIG]["scent"]
    recomputed = hashlib.sha256(canonical_json(embedded).encode("utf-8")).hexdigest()
    on_the_wire = scent_digest(load_scent_model(config_dir(role) / "scent.json"))
    assert recomputed == on_the_wire
    assert artifact[artifact_config.ConfigArtifactField.HANDSHAKE_DIGESTS]["scent"] == on_the_wire


def test_the_digest_assertion_fails_on_a_mutated_config(tmp_path):
    """COUNTER-CONTROL. A digest assertion that cannot fail is not an
    assertion: mutate ONE value in a copied game_params.json and the
    recomputed digest must stop matching the unmutated handshake digest."""
    mutated_dir = tmp_path / "police"
    shutil.copytree(config_dir("police"), mutated_dir)
    params_path = mutated_dir / "game_params.json"
    params = json.loads(params_path.read_text(encoding="utf-8"))
    params["barrier_quota"] = params["barrier_quota"] + 1
    params_path.write_text(json.dumps(params), encoding="utf-8")

    artifact = artifact_config.build_config_artifact(
        mutated_dir, game_uid=GAME_UID, game_id=GAME_UID, sub_game_index=1
    )
    embedded = artifact[artifact_config.ConfigArtifactField.CONFIG]["game_params"]
    recomputed = hashlib.sha256(canonical_json(embedded).encode("utf-8")).hexdigest()
    unmutated = config_digest(config_dir("police") / "game_params.json")
    assert recomputed != unmutated
    with pytest.raises(AssertionError):
        assert recomputed == unmutated


def test_both_roles_produce_a_byte_identical_artifact(tmp_path):
    """Rule 11: "identical byte-for-byte on both sides". Proved by writing
    both and diffing the FILES, not by trusting the builder."""
    written = [
        artifact_config.write_config_artifact(
            tmp_path / role, config_dir(role),
            game_uid=GAME_UID, game_id=GAME_UID, sub_game_index=1,
        )
        for role in ROLES
    ]
    assert written[0].read_bytes() == written[1].read_bytes()
    assert written[0].name == f"config_{GAME_UID}_g01.json"


def test_the_byte_identity_check_can_fail(tmp_path):
    """COUNTER-CONTROL for the check above: a one-value difference between
    the two config trees must break byte identity."""
    left, right = tmp_path / "l", tmp_path / "r"
    shutil.copytree(config_dir("police"), left / "cfg")
    shutil.copytree(config_dir("thief"), right / "cfg")
    params_path = right / "cfg" / "game_params.json"
    params = json.loads(params_path.read_text(encoding="utf-8"))
    params["move_ceiling"] = params["move_ceiling"] + 1
    params_path.write_text(json.dumps(params), encoding="utf-8")

    paths = [
        artifact_config.write_config_artifact(
            side / "out", side / "cfg", game_uid=GAME_UID, game_id=GAME_UID, sub_game_index=1
        )
        for side in (left, right)
    ]
    assert paths[0].read_bytes() != paths[1].read_bytes()


@pytest.mark.parametrize("leak", _PER_AGENT_LEAKS)
def test_no_per_agent_value_reaches_the_artifact(leak):
    """network.json (D-04) and role.json are excluded, so nothing that
    differs between the two agents -- or identifies the team -- appears."""
    assert leak not in canonical_json(build("police"))


def test_the_leak_check_can_fail():
    """COUNTER-CONTROL: the same search over a config tree that DOES embed
    network.json must find the leak, so the check above is not vacuous."""
    polluted = dict(build("police"))
    polluted["network"] = json.loads(
        (config_dir("police") / "network.json").read_text(encoding="utf-8")
    )
    assert "opponent_url" in canonical_json(polluted)


def test_the_artifact_carries_the_join_and_the_index():
    artifact = build("police")
    assert artifact["game_uid"] == GAME_UID
    assert artifact["game_id"] == GAME_UID
    assert artifact["sub_game_index"] == 1


def test_language_json_carries_no_handshake_digest():
    """It is shipped identically by both sides but never exchanged, so
    claiming a handshake digest for it would assert an agreement never made."""
    artifact = build("police")
    digests = artifact[artifact_config.ConfigArtifactField.HANDSHAKE_DIGESTS]
    assert set(digests) == {"game_params", "scent"}
    assert "language" in artifact[artifact_config.ConfigArtifactField.CONFIG]
