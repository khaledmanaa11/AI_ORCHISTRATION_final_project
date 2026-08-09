"""D-63: Step-0 declaration collection + the persisted games-played counter."""

from __future__ import annotations

import subprocess

import pytest

from pursuit.security import step0_collect
from pursuit.security.step0_collect import DeclarationField, GamesPlayedField

_EXPECTED_KEYS = {
    DeclarationField.ROLE, DeclarationField.TEAM_CODE, DeclarationField.OS,
    DeclarationField.CPU, DeclarationField.RAM_GB, DeclarationField.GPU,
    DeclarationField.LLM_NAME, DeclarationField.CODE_VERSION,
    DeclarationField.GAMES_PLAYED_SO_FAR, DeclarationField.COMMIT_HASH,
}


def test_collect_declaration_has_exactly_the_documented_keys():
    declaration = step0_collect.collect_declaration(
        role="police", team_code="khm-mn17", llm_name="claude-haiku-4-5",
        code_version="1.00", games_played=0,
    )
    assert set(declaration.keys()) == _EXPECTED_KEYS
    assert declaration[DeclarationField.ROLE] == "police"
    assert declaration[DeclarationField.GAMES_PLAYED_SO_FAR] == 0
    assert declaration[DeclarationField.COMMIT_HASH]  # non-empty, real git hash


def test_a_failing_nvidia_smi_yields_the_honest_not_detected_shape(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError("nvidia-smi not on PATH")

    monkeypatch.setattr(subprocess, "run", _raise)
    gpu = step0_collect._collect_gpu()
    assert gpu == {"present": False, "detail": "not detected"}


def test_a_failing_git_command_raises_loudly(monkeypatch):
    def _raise(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["git", "rev-parse", "HEAD"])

    monkeypatch.setattr(subprocess, "run", _raise)
    with pytest.raises(subprocess.CalledProcessError):
        step0_collect._git_commit_hash()


def test_games_played_round_trips_through_record_then_read(tmp_path):
    path = tmp_path / "games_played.json"
    assert step0_collect.read_games_played(path) == 0  # missing file -> 0, never raises

    step0_collect.record_game_played(path)
    assert step0_collect.read_games_played(path) == 1

    step0_collect.record_game_played(path)
    assert step0_collect.read_games_played(path) == 2


def test_read_games_played_on_a_malformed_file_returns_zero(tmp_path):
    path = tmp_path / "games_played.json"
    path.write_text("not json at all", encoding="utf-8")
    assert step0_collect.read_games_played(path) == 0


def test_read_games_played_on_a_non_dict_or_missing_field_returns_zero(tmp_path):
    import json

    path = tmp_path / "games_played.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert step0_collect.read_games_played(path) == 0

    path.write_text(json.dumps({GamesPlayedField.COUNT: True}), encoding="utf-8")
    assert step0_collect.read_games_played(path) == 0  # bool is an int subtype -- rejected
