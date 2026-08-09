"""Tests for the locked scent model loader (D-46, D-49, D-50, LANG-04, LANG-07).

The property this file protects: scent.json is cryptographically LOCKED
before a game starts (rule 23), so a self-inconsistent or mismatched file
must be rejected loudly at load time, never trusted and discovered wrong
mid-game.
"""

import dataclasses
import json
import pathlib

import pytest

from pursuit.shared.scent_config import ScentKey, load_scent_model, scent_digest

_CONFIG = pathlib.Path(__file__).parent.parent.parent / "config"
_POLICE = _CONFIG / "police" / "scent.json"
_THIEF = _CONFIG / "thief" / "scent.json"


def _valid_data() -> dict:
    return json.loads(_POLICE.read_text(encoding="utf-8"))


def _write(tmp_path, data) -> pathlib.Path:
    path = tmp_path / "scent.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_police_and_thief_files_are_byte_identical():
    assert _POLICE.read_bytes() == _THIEF.read_bytes()


def test_police_and_thief_models_digest_equal():
    assert scent_digest(load_scent_model(_POLICE)) == scent_digest(load_scent_model(_THIEF))


def test_shipped_model_matches_table_16():
    """PARAMETERS.md Table 16 -- the three fixed values, all `fixed`."""
    model = load_scent_model(_POLICE)
    assert (model.source, model.decay, model.window) == (0.9, 0.10, 5)


def test_shipped_kernel_matches_figure_4():
    model = load_scent_model(_POLICE)
    assert model.kernel[2][2] == 0.9
    assert model.kernel[1][2] == 0.62
    assert model.kernel[0][0] == 0.04


def test_shipped_worked_example_is_0_9_to_0_81():
    model = load_scent_model(_POLICE)
    assert (model.worked_example_initial, model.worked_example_after) == (0.9, 0.81)


def test_mutated_kernel_entry_changes_digest():
    model = load_scent_model(_POLICE)
    before = scent_digest(model)
    bumped_row = tuple(
        0.5 if col == 0 else value for col, value in enumerate(model.kernel[0])
    )
    mutated = dataclasses.replace(model, kernel=(bumped_row, *model.kernel[1:]))
    assert scent_digest(mutated) != before


def test_missing_top_level_key_raises(tmp_path):
    data = _valid_data()
    del data["decay"]
    with pytest.raises(KeyError, match="decay"):
        load_scent_model(_write(tmp_path, data))


def test_non_numeric_source_raises_type_error(tmp_path):
    data = _valid_data()
    data["source"] = "high"
    with pytest.raises(TypeError):
        load_scent_model(_write(tmp_path, data))


def test_even_window_rejected(tmp_path):
    data = _valid_data()
    data["window"] = 4
    with pytest.raises(ValueError, match="window"):
        load_scent_model(_write(tmp_path, data))


def test_kernel_wrong_row_count_rejected(tmp_path):
    data = _valid_data()
    data["kernel"] = data["kernel"][:-1]
    with pytest.raises(ValueError, match="kernel"):
        load_scent_model(_write(tmp_path, data))


def test_kernel_row_wrong_length_rejected(tmp_path):
    data = _valid_data()
    data["kernel"][0] = data["kernel"][0][:-1]
    with pytest.raises(ValueError, match="kernel"):
        load_scent_model(_write(tmp_path, data))


def test_kernel_entry_non_numeric_rejected(tmp_path):
    data = _valid_data()
    data["kernel"][0][0] = "high"
    with pytest.raises(ValueError, match="must be numeric"):
        load_scent_model(_write(tmp_path, data))


def test_kernel_entry_bool_rejected(tmp_path):
    """bool is a subclass of int in Python and must not pass silently as numeric."""
    data = _valid_data()
    data["kernel"][0][0] = True
    with pytest.raises(ValueError, match="must be numeric"):
        load_scent_model(_write(tmp_path, data))


def test_kernel_entry_above_source_rejected(tmp_path):
    data = _valid_data()
    data["kernel"][0][0] = 1.5
    with pytest.raises(ValueError):
        load_scent_model(_write(tmp_path, data))


def test_kernel_entry_negative_rejected(tmp_path):
    data = _valid_data()
    data["kernel"][0][0] = -0.01
    with pytest.raises(ValueError):
        load_scent_model(_write(tmp_path, data))


def test_kernel_not_symmetric_rejected(tmp_path):
    data = _valid_data()
    data["kernel"][0][1] = 0.10  # in-range, but breaks the mirror at row 0
    with pytest.raises(ValueError, match="symmetric"):
        load_scent_model(_write(tmp_path, data))


def test_kernel_centre_must_equal_source(tmp_path):
    data = _valid_data()
    data["kernel"][2][2] = 0.5
    with pytest.raises(ValueError, match="centre"):
        load_scent_model(_write(tmp_path, data))


def test_tampered_worked_example_rejected_naming_the_key(tmp_path):
    data = _valid_data()
    data["worked_example"]["after_one_turn"] = 0.5
    with pytest.raises(ValueError, match="worked_example.after_one_turn"):
        load_scent_model(_write(tmp_path, data))


def test_worked_example_initial_must_equal_source(tmp_path):
    data = _valid_data()
    data["worked_example"]["initial"] = 0.5
    with pytest.raises(ValueError, match="worked_example.initial"):
        load_scent_model(_write(tmp_path, data))


def test_scent_key_str_is_plain_string():
    """json.dumps must emit the field name, not 'ScentKey.SOURCE'."""
    assert str(ScentKey.SOURCE) == "source"
    assert json.loads(json.dumps({str(ScentKey.SOURCE): 0.9})) == {"source": 0.9}


def test_digest_is_lowercase_sha256_hex():
    digest = scent_digest(load_scent_model(_POLICE))
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


def test_digest_is_deterministic_across_loads():
    assert scent_digest(load_scent_model(_POLICE)) == scent_digest(load_scent_model(_POLICE))
