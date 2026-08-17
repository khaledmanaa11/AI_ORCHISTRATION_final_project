"""The hook has a production call site, and it is in the RIGHT place.

WHY THIS GATE EXISTS. Every other test in this plan drives `report_game_end`
directly, so deleting the one line in `agent_entrypoint.py` that calls it would
leave the whole suite green while no league game ever reported -- rule 32
disqualifies the points of an unreported game and rule 35 scores ZERO FOR BOTH
TEAMS. That is the same class of hole D7-3/D7-14 name, and the same technique
`test_log_artifact_reachability.py::test_read_all_has_exactly_one_production_
call_site` already uses: assert the ORDER of the real source, not a summary.

WHY THE POSITION IS ASSERTED, NOT JUST THE PRESENCE. In the `finally` block the
hook would run after `stop_watchdog` and `stop_runtime`, i.e. with the
gatekeeper's budget gone and the freeze watchdog already disarmed -- it would
still "be called", and the report would be wrong.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
ENTRYPOINT = SRC / "pursuit/network/agent_entrypoint.py"
HOOK = "report_game_end"
HOOK_MODULE = "pursuit.services.reporting.end_of_game"


def _source() -> str:
    return ENTRYPOINT.read_text(encoding="utf-8")


def test_the_entrypoint_imports_the_hook_from_the_reporting_package():
    """By AST, so a docstring that names it cannot satisfy this."""
    imported = {
        f"{node.module}.{alias.name}"
        for node in ast.walk(ast.parse(_source()))
        if isinstance(node, ast.ImportFrom) and node.module and not node.level
        for alias in node.names
    }
    assert f"{HOOK_MODULE}.{HOOK}" in imported


def test_the_hook_is_awaited_exactly_once_beside_the_games_played_counter():
    """One call, after the counter and before the return -- the two lines that
    define "the game is complete and its result is final"."""
    source = _source()
    assert source.count(f"await {HOOK}(") == 1

    counter = source.index("record_completed_game(cfg, outcome)")
    call = source.index(f"await {HOOK}(")
    returned = source.index("return outcome\n        finally:")
    assert counter < call < returned


def _called_names(statements) -> set[str]:
    return {
        node.func.id
        for statement in statements
        for node in ast.walk(statement)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def test_the_hook_is_in_a_try_body_and_in_no_teardown_finally():
    """`stop_watchdog` disarms the freeze detector and `stop_runtime` closes the
    server; both run in the `finally`. A report from there would still "be
    called" while being built after the gatekeeper's budget and the armed
    watchdog are gone.

    Checked on the SYNTAX, not on source offsets: a first draft compared
    `index(hook)` against `index("stop_watchdog")` and passed against a
    mutation that moved the call to the top of the very `finally` it forbids.
    """
    tries = [node for node in ast.walk(ast.parse(_source())) if isinstance(node, ast.Try)]
    assert len(tries) > 1, "the entrypoint's try blocks were not found"

    assert any(HOOK in _called_names(node.body) for node in tries)
    assert not any(HOOK in _called_names(node.finalbody) for node in tries)


def test_exactly_one_module_in_src_calls_the_hook():
    """A second call site would report the same game twice -- two `result_`
    rewrites and two emails for one sub-game."""
    callers = sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if f"await {HOOK}(" in path.read_text(encoding="utf-8")
    )
    assert callers == ["pursuit/network/agent_entrypoint.py"]
