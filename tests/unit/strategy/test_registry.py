"""Tests for build_brain's fail-loud config resolution (STRAT-03, D-07)."""

import ast
import pathlib
from types import SimpleNamespace

import pytest

from pursuit.constants import MoveSource
from pursuit.strategy import registry
from pursuit.strategy.base import BrainBase, Decision

_STUB_NAME = "tests.stub:StubBrain"


class _StubBrain(BrainBase):
    """Locally-defined stub proving the construction mechanism -- 03-04/03-06
    register the real HeuristicBrain/QLearningBrain classes, not this one."""

    def __init__(self, *, role: str, params) -> None:
        self.role = role
        self.params = params

    def _pick_move(self, obs, state):
        return Decision(move=obs.own_cell, source=MoveSource.HEURISTIC)

    def _decide_move(self, obs, state):
        return self._pick_move(obs, state)


@pytest.fixture(autouse=True)
def _register_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(registry._BRAIN_REGISTRY, _STUB_NAME, _StubBrain)


def _fake_params(brain_class: str) -> SimpleNamespace:
    return SimpleNamespace(brain_class=brain_class)


def test_build_brain_resolves_registered_name() -> None:
    brain = registry.build_brain("cop", _fake_params(_STUB_NAME))
    assert isinstance(brain, _StubBrain)
    assert brain.role == "cop"


def test_build_brain_unknown_name_raises_and_lists_known() -> None:
    with pytest.raises(ValueError) as excinfo:
        registry.build_brain("thief", _fake_params("nonexistent:Nope"))
    message = str(excinfo.value)
    assert "nonexistent:Nope" in message
    assert _STUB_NAME in message


def test_build_brain_never_falls_back_to_a_default() -> None:
    with pytest.raises(ValueError):
        registry.build_brain("cop", _fake_params(""))


def test_registry_module_calls_no_eval_or_exec() -> None:
    """Structural, not string-matched: walks Call nodes for the two names."""
    tree = ast.parse(pathlib.Path("src/pursuit/strategy/registry.py").read_text(encoding="utf-8"))
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not called_names & {"eval", "exec"}
