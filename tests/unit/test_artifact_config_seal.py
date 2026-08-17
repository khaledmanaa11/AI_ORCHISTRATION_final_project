"""The config artifact's own seal, and the post-write round trip.

Split from `test_artifact_config.py` at the 150-code-line gate. The seal is a
distinct subject from the handshake digests: those prove the artifact and the
GAME were locked to one config, this proves the FILE on disk still carries
what the builder put in it.
"""

import json

import pytest

from pursuit.services.reporting import artifact_config, artifacts
from tests.unit.artifact_config_fixtures import GAME_UID, build, config_dir

_FIELD = artifact_config.ConfigArtifactField


def _write(tmp_path):
    return artifact_config.write_config_artifact(
        tmp_path / "out", config_dir("police"),
        game_uid=GAME_UID, game_id=GAME_UID, sub_game_index=1,
    )


def test_the_built_artifact_seals_its_own_embedded_config():
    artifact = build("police")
    config = artifact[_FIELD.CONFIG]
    sealed = artifact[_FIELD.CONFIG_DIGEST]
    assert artifacts.artifact_digest_matches(config, sealed) is True
    assert artifacts.artifact_digest_matches({**config, "extra": 1}, sealed) is False


def test_the_written_file_verifies_against_its_own_seal(tmp_path):
    assert artifact_config.verify_config_artifact(_write(tmp_path)) is True


def test_the_post_write_seal_check_can_fail(tmp_path):
    """COUNTER-CONTROL: tamper with the written FILE and the same check that
    passed above must fail -- otherwise it verifies nothing about the round
    trip through `durable_write_json` and back."""
    path = _write(tmp_path)
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered[_FIELD.CONFIG]["game_params"]["barrier_quota"] = 999
    path.write_text(json.dumps(tampered), encoding="utf-8")
    assert artifact_config.verify_config_artifact(path) is False


def test_a_failed_post_write_check_refuses_to_ship_the_artifact(tmp_path, monkeypatch):
    """The writer must RAISE, not return a path to an artifact it could not
    re-verify -- the config half of the promise `write_declaration_artifact`
    makes for signatures."""
    monkeypatch.setattr(artifact_config, "verify_config_artifact", lambda _path: False)
    with pytest.raises(ValueError, match="failed seal re-verification"):
        _write(tmp_path)


def test_a_second_sub_game_writes_beside_the_first_and_seals_too(tmp_path):
    """The `<NN>` index and the seal compose: `_g02` is a separate file with
    its own valid seal, and `_g01` is untouched."""
    first = _write(tmp_path)
    index = artifacts.next_sub_game_index(tmp_path / "out", GAME_UID)
    assert index == 2
    second = artifact_config.write_config_artifact(
        tmp_path / "out", config_dir("thief"),
        game_uid=GAME_UID, game_id=GAME_UID, sub_game_index=index,
    )
    assert second.name == f"config_{GAME_UID}_g02.json"
    assert first.is_file()
    assert artifact_config.verify_config_artifact(first) is True
    assert artifact_config.verify_config_artifact(second) is True
