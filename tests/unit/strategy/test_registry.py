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


# --- STRAT-03 / STRAT-07 package-wide structural isolation gates ---------

_FORBIDDEN_IMPORTS = (
    # STRAT-07 (rule 25): an LLM-chosen move is disqualification-grade, so
    # the decision path must be structurally unable to reach a language
    # model, an HTTP client, subprocess, or a raw socket. Named deny-list,
    # not a prose promise -- see 03-02-PLAN.md's verify step for the
    # temporarily-add-then-revert proof that this test can actually fail.
    "socket",
    "subprocess",
    "http",
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "openai",
    "anthropic",
    "google.generativeai",
    "cohere",
)


def _strategy_module_paths() -> list[pathlib.Path]:
    return sorted(pathlib.Path("src/pursuit/strategy").rglob("*.py"))


def _imported_module_names(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_strategy_package_imports_no_networking() -> None:
    """STRAT-03: strategy must be usable and testable with no networking."""
    for path in _strategy_module_paths():
        for name in _imported_module_names(path):
            assert not name.startswith("pursuit.network"), f"{path} imports {name!r}"


def test_strategy_package_has_no_llm_or_subprocess_path() -> None:
    """STRAT-07: rule 25 -- the decision path must never reach an LLM."""
    for path in _strategy_module_paths():
        for name in _imported_module_names(path):
            top = name.split(".")[0]
            assert name not in _FORBIDDEN_IMPORTS, f"{path} imports {name!r}"
            assert top not in _FORBIDDEN_IMPORTS, f"{path} imports {name!r}"
