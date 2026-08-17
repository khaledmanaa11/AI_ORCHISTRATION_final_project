"""The shipped commit-reveal-ON path's turn source, pinned structurally (08-05).

WHY A STRUCTURAL TEST AND NOT A BEHAVIOURAL ONE. Deferred item #13's repair
threads a `played_turn` into `turn_commit.initiate`, and the SAME function's
ON branch feeds `commit_own_action` -- the D-59 hash input and the D-64 ledger
join key. A wrong number there is a rules 19/22 TECHNICAL LOSS, not an evidence
blemish, which is exactly why 05-14 declined to make this change in passing.

A behavioural test can show the two values agree TODAY. It cannot show that the
ON path is still reading the source it was designed to read, and "they happened
to be equal in the case I wrote" is how a hash input drifts. So this module
reads `turn_commit.py`'s own AST and asserts three things that must remain true
however the code is refactored:

  1. `played_turn` is REQUIRED and keyword-only -- no default can silently
     reintroduce the defect for a caller that forgets it;
  2. both entry points still bind `turn = ctx.state.turn` and still pass that
     NAME to `commit_own_action(turn=...)`;
  3. `played_turn` is referenced ONLY inside the toggle-off early return.

Empirically confirmed alongside this: a deterministic ON-path drive (nonce
pinned) produced a byte-identical fingerprint before and after the repair --
same three pushes, same turns, same `h_commit`, same ledger record.
"""

from __future__ import annotations

import ast
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "src" / "pursuit" / "network" / "turn_commit.py"
PLAYED_TURN = "played_turn"
TURN = "turn"
COMMIT_CALL = "commit_own_action"
TOGGLE_ATTR = "commit_reveal"
#: Both D-58 entry points that commit an action under a turn number.
COMMITTING_FUNCTIONS = ("initiate", "await_and_respond")


def function_named(name: str) -> ast.AsyncFunctionDef:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    found = [
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name
    ]
    assert len(found) == 1, f"expected exactly one `{name}` in {MODULE.name}, got {len(found)}"
    return found[0]


def toggle_off_branch(function: ast.AST) -> ast.If:
    """The `if not ctx.security.commit_reveal:` guard inside *function*."""
    guards = [
        node for node in ast.walk(function)
        if isinstance(node, ast.If) and TOGGLE_ATTR in ast.unparse(node.test)
    ]
    assert len(guards) == 1, f"expected exactly one {TOGGLE_ATTR} guard, got {len(guards)}"
    return guards[0]


def test_played_turn_is_required_and_keyword_only() -> None:
    """A default would let the next caller reintroduce #13 by omission."""
    args = function_named("initiate").args
    names = [arg.arg for arg in args.kwonlyargs]
    assert PLAYED_TURN in names, f"`initiate` has no keyword-only {PLAYED_TURN}: {names}"
    default = args.kw_defaults[names.index(PLAYED_TURN)]
    assert default is None, f"{PLAYED_TURN} carries a default, so a caller can omit it"
    assert PLAYED_TURN not in [arg.arg for arg in args.args], "it must not be positional"


def test_both_committing_entry_points_still_read_ctx_state_turn() -> None:
    """The D-59 / D-64 source. Untouched by #13's repair, and pinned here."""
    for name in COMMITTING_FUNCTIONS:
        body = ast.unparse(function_named(name))
        assert f"{TURN} = ctx.state.{TURN}" in body, (
            f"`{name}` no longer binds {TURN} from ctx.state -- the D-59 hash input "
            f"and the D-64 ledger join key come from that binding"
        )


def test_commit_own_action_is_still_fed_the_ctx_state_turn_binding() -> None:
    """Not `played_turn`, and not an expression -- the plain name `turn`."""
    checked = 0
    for name in COMMITTING_FUNCTIONS:
        for node in ast.walk(function_named(name)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id != COMMIT_CALL:
                continue
            keywords = {kw.arg: ast.unparse(kw.value) for kw in node.keywords}
            assert keywords.get(TURN) == TURN, (
                f"`{name}` calls {COMMIT_CALL} with turn={keywords.get(TURN)!r}"
            )
            checked += 1
    assert checked == len(COMMITTING_FUNCTIONS), (
        f"found {checked} {COMMIT_CALL} call(s), expected one per committing entry point"
    )


def test_played_turn_is_used_only_inside_the_toggle_off_branch() -> None:
    """The containment that makes the ON path byte-identical BY CONSTRUCTION."""
    function = function_named("initiate")
    branch = toggle_off_branch(function)
    inside = sum(
        1 for node in ast.walk(branch)
        if isinstance(node, ast.Name) and node.id == PLAYED_TURN
    )
    everywhere = sum(
        1 for node in ast.walk(function)
        if isinstance(node, ast.Name) and node.id == PLAYED_TURN
    )
    assert inside >= 1, f"{PLAYED_TURN} is not used in the toggle-off branch at all"
    assert inside == everywhere, (
        f"{PLAYED_TURN} is referenced {everywhere - inside} time(s) OUTSIDE the "
        f"toggle-off branch -- the commit-reveal-ON path must not see it"
    )


def test_the_ast_helpers_are_not_finding_nothing() -> None:
    """The control. Every assertion above is over a parse that could be empty."""
    function = function_named("initiate")
    assert isinstance(function, ast.AsyncFunctionDef)
    assert len(function.body) > 3, "the parsed body is implausibly small"
    assert isinstance(toggle_off_branch(function), ast.If)
