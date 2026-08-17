"""D7-18: the shipped-config guard covers the RULE, not one writer.

`config/{police,thief}/games_played.json` is the rule-37 count this team
declares to the league, and rule 38 (`docs/RULES.md:79`) makes a false one an
ABSOLUTE DISQUALIFICATION. `tests/conftest.py`'s session-autouse guard exists
because one full `pytest` run once advanced both counters by +14 for zero games
played (07-00).

Until 07-09 that guard patched `step0_collect.durable_write_json` and nothing
else, so it caught ONE writer while the rule it enforces is about the TREE.
07-07's revert probe 17 pointed `QuotaManager` at `config/police/` and the
suite wrote `config/police/reporting_quota.json` without a single test failing
for the write.

TWO ASSERTIONS, AND NEITHER SUBSTITUTES FOR THE OTHER. The AST scan proves the
LIST is complete -- a sixth binder fails here rather than escaping silently.
The behavioural cases prove each listed binding is actually WRAPPED at run
time; a correct list that `install` never applied would pass the first and fail
the second.
"""

from __future__ import annotations

import ast
import importlib
import pathlib

import pytest

from pursuit.shared.durable_write import DURABLE_WRITE_BACKOFF_SECONDS, DURABLE_WRITE_RETRIES
from tests._shipped_config_guard import (
    DURABLE_WRITE_BINDERS,
    SHIPPED_CONFIG_ROOT,
    WRITER_ATTR,
    ShippedConfigWriteError,
    is_shipped_config_path,
)

SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
#: `durable_write_json`'s two REQUIRED keyword-only arguments, taken from its
#: own module rather than written down again -- a probe that called it with a
#: shape no production caller uses would be probing the signature, not the guard.
WRITE_KWARGS = {"retries": DURABLE_WRITE_RETRIES, "backoff": DURABLE_WRITE_BACKOFF_SECONDS}
DEFINING_MODULE = "pursuit.shared.durable_write"
#: The anti-vacuity floor for the scan, on `test_log_artifact_reachability.py`'s
#: precedent: an empty `src/` would make the derived set empty and the equality
#: assertion meaningless.
MIN_SCANNED = 100


def _binds_the_writer(path: pathlib.Path) -> bool:
    """True when this module imports `durable_write_json` by NAME.

    By AST, never by substring: six modules discuss `durable_write_json` in
    their docstrings and a text scan would count every one of them.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == DEFINING_MODULE
        and any((alias.asname or alias.name) == WRITER_ATTR for alias in node.names)
        for node in ast.walk(tree)
    )


def _module_name(path: pathlib.Path) -> str:
    return ".".join(path.relative_to(SRC).with_suffix("").parts)


def test_the_binder_list_names_every_module_that_binds_the_writer():
    """A sixth writer fails HERE, not in a grader's inbox."""
    scanned = sorted(SRC.rglob("*.py"))
    assert len(scanned) > MIN_SCANNED, "the scan looked at almost nothing"
    derived = {_module_name(path) for path in scanned if _binds_the_writer(path)}
    derived.add(DEFINING_MODULE)
    assert derived == set(DURABLE_WRITE_BINDERS)


def test_the_list_is_not_empty_and_holds_more_than_the_original_one():
    """The whole point of D7-18 was that ONE binding is not the rule."""
    assert len(DURABLE_WRITE_BINDERS) > 1
    assert "pursuit.security.step0_collect" in DURABLE_WRITE_BINDERS


@pytest.mark.parametrize("module_name", DURABLE_WRITE_BINDERS)
def test_every_binding_refuses_a_write_into_the_shipped_config_tree(module_name):
    """The guard is installed by the session-autouse fixture, so this calls
    the REAL binding a production caller would reach."""
    assert DURABLE_WRITE_BINDERS, "an emptied table would SKIP every case silently"
    module = importlib.import_module(module_name)
    target = SHIPPED_CONFIG_ROOT / "police" / "guard_probe.json"
    with pytest.raises(ShippedConfigWriteError) as caught:
        getattr(module, WRITER_ATTR)(target, {"probe": True}, **WRITE_KWARGS)
    assert "guard_probe.json" in str(caught.value)
    assert not target.exists(), "the guard must raise BEFORE any byte is written"


@pytest.mark.parametrize("module_name", DURABLE_WRITE_BINDERS)
def test_every_binding_still_writes_everywhere_else(module_name, tmp_path):
    """The guard has to DISCRIMINATE. A binding that refused every target
    would pass the case above while breaking every legitimate write."""
    assert DURABLE_WRITE_BINDERS, "an emptied table would SKIP every case silently"
    module = importlib.import_module(module_name)
    target = tmp_path / f"{module_name.replace('.', '_')}.json"
    getattr(module, WRITER_ATTR)(target, {"probe": True}, **WRITE_KWARGS)
    assert target.is_file()


def test_a_relative_shipped_path_is_recognised_too():
    """Every one of the +14 writes arrived as a RELATIVE path, via
    `load_agent_config("config/police")`."""
    assert is_shipped_config_path("config/police/games_played.json")
    assert is_shipped_config_path(SHIPPED_CONFIG_ROOT / "thief" / "games_played.json")


def test_control_a_path_outside_the_tree_is_not_recognised(tmp_path):
    """Without this the predicate could return True for everything and both
    refusal cases above would pass for the wrong reason."""
    assert not is_shipped_config_path(tmp_path / "games_played.json")
    assert not is_shipped_config_path("game_artifacts/police/result_x.json")
