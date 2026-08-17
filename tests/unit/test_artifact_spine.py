"""The `game_uid` join, the one canonical seal, and D7-1's write refusal.

Split from `test_artifact_names.py` at the 150-code-line gate, along the same
seam `artifacts.py`/`artifact_names.py` split on: names and index there, join
and seal and placement here.
"""

import hashlib
import json

import pytest

from pursuit.network.config_hash import canonical_json
from pursuit.services.reporting import artifacts

_GAME_UID = "5efbc5811fabfac4"

# The only parametrize source in this file. Kept as a literal and guarded
# below: a thinned table skips silently and reads green.
_IGNORED_DIRS = ("logs", "logs/police", "run/logs", "logs/thief/nested")


def test_the_ignored_dir_table_is_intact():
    """ANTI-VACUITY GUARD for the one parametrize below."""
    assert len(_IGNORED_DIRS) == 4
    assert all("logs" in case.split("/") for case in _IGNORED_DIRS)


def test_the_header_carries_the_shared_game_uid_and_game_id():
    header = artifacts.artifact_header(game_uid=_GAME_UID, game_id=_GAME_UID)
    assert header == {"game_uid": _GAME_UID, "game_id": _GAME_UID}


def test_the_header_omits_sub_game_index_unless_one_is_given():
    """docs/PARAMETERS.md gives `_g<NN>` to config_/log_ only, so only those
    two carry the field -- contents and filename cannot disagree."""
    assert artifacts.ArtifactField.SUB_GAME_INDEX not in artifacts.artifact_header(
        game_uid=_GAME_UID, game_id=_GAME_UID
    )
    indexed = artifacts.artifact_header(game_uid=_GAME_UID, game_id=_GAME_UID, sub_game_index=2)
    assert indexed[artifacts.ArtifactField.SUB_GAME_INDEX] == 2


def test_the_header_rejects_an_index_its_filename_would_reject():
    """One validation, so a header cannot carry an index no filename can."""
    with pytest.raises(ValueError, match="sub_game_index"):
        artifacts.artifact_header(game_uid=_GAME_UID, game_id=_GAME_UID, sub_game_index=0)
    with pytest.raises(TypeError):
        artifacts.artifact_header(game_uid=_GAME_UID, game_id=_GAME_UID, sub_game_index=True)


def test_the_index_in_the_name_and_the_index_in_the_header_agree():
    """The join docs/PARAMETERS.md:159 requires: one `game_uid` across all
    four, and `<NN>` on exactly the two that carry it in their FILENAME.
    Cross-checked here name-against-header, so a builder that put the field on
    `result_` -- or dropped it from `config_` -- fails on the disagreement."""
    cases = (
        (artifacts.declaration_filename(_GAME_UID), None),
        (artifacts.result_filename(_GAME_UID), None),
        (artifacts.config_filename(_GAME_UID, 1), 1),
        (artifacts.log_filename(_GAME_UID, 1), 1),
    )
    assert len(cases) == 4
    for filename, index in cases:
        header = artifacts.artifact_header(
            game_uid=_GAME_UID, game_id=_GAME_UID, sub_game_index=index
        )
        name_has_index = "_g01" in filename
        header_has_index = artifacts.ArtifactField.SUB_GAME_INDEX in header
        assert name_has_index == header_has_index, filename
        assert name_has_index is (index is not None), filename
        assert header[artifacts.ArtifactField.GAME_UID] == _GAME_UID


def test_the_seal_is_sha256_over_canonical_json_and_nothing_else():
    payload = {"b": 1, "a": {"z": [3, 2, 1]}}
    expected = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    assert artifacts.artifact_digest(payload) == expected


def test_the_seal_ignores_key_order_but_never_array_order():
    """`canonical_json` sorts OBJECT keys recursively and leaves ARRAYS
    alone -- scoring values are ordered [cop, thief] pairs."""
    assert artifacts.artifact_digest({"a": 1, "b": 2}) == artifacts.artifact_digest(
        {"b": 2, "a": 1}
    )
    assert artifacts.artifact_digest({"s": [20, 5]}) != artifacts.artifact_digest({"s": [5, 20]})


def test_digest_matches_accepts_the_true_digest_and_rejects_a_perturbed_one():
    payload = {"game_uid": _GAME_UID}
    digest = artifacts.artifact_digest(payload)
    assert artifacts.artifact_digest_matches(payload, digest) is True
    assert artifacts.artifact_digest_matches({"game_uid": "other"}, digest) is False


def test_digest_matches_inherits_the_strict_digests_match_contract():
    """D-46 keeps ONE digest comparison; a non-str digest must raise out of
    `digests_match` rather than quietly compare False here."""
    with pytest.raises(TypeError):
        artifacts.artifact_digest_matches({"a": 1}, None)


def test_write_artifact_writes_into_the_configured_directory(tmp_path):
    artifact_dir = tmp_path / "game_artifacts"
    payload = {"game_uid": _GAME_UID}
    path = artifacts.write_artifact(
        artifact_dir, artifacts.result_filename(_GAME_UID), payload
    )
    assert path == artifact_dir / f"result_{_GAME_UID}.json"
    assert json.loads(path.read_text(encoding="utf-8")) == payload


@pytest.mark.parametrize("ignored_dir", _IGNORED_DIRS)
def test_write_artifact_refuses_any_path_under_logs(tmp_path, ignored_dir):
    """D7-1 ENFORCED, not merely documented. `.gitignore` ignores `logs/`
    wholesale, so an artifact written there is unreachable to git and rule 50
    is silently broken -- exactly the state `write_declaration` is in today."""
    target = tmp_path
    for part in ignored_dir.split("/"):
        target = target / part
    with pytest.raises(ValueError, match="D7-1"):
        artifacts.write_artifact(target, artifacts.result_filename(_GAME_UID), {})


def test_the_logs_refusal_can_fail(tmp_path):
    """THE COUNTER-CONTROL for the refusal above: the same call with the one
    forbidden path component removed must SUCCEED, so the test is reading the
    guard rather than any old ValueError."""
    allowed = tmp_path / "police"
    path = artifacts.write_artifact(allowed, artifacts.result_filename(_GAME_UID), {})
    assert path.is_file()


def test_write_artifact_refuses_before_it_creates_anything(tmp_path):
    """The guard runs ahead of `durable_write_json`'s mkdir, so a refused
    write leaves no half-made ignored directory behind."""
    target = tmp_path / "logs" / "police"
    with pytest.raises(ValueError, match="D7-1"):
        artifacts.write_artifact(target, artifacts.result_filename(_GAME_UID), {})
    assert not target.exists()
