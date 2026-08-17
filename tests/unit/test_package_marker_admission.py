"""What `is_package_marker` may admit, and what it must still refuse (08-03).

WHY THIS WIDENING NEEDED ITS OWN CONTROLS. 08-03 gave every package the `__all__`
Sec14 requires, which turned `src/pursuit/gui/__init__.py` from a bare docstring
into a module with a statement in it -- and the rules 8-9 firewall promptly and
correctly failed, because a module with a statement is a module it must judge.
The cheap way out was to special-case the filename `__init__.py`, which would
have blinded the gate to a real `__init__.py` that imported `GameState`. The
admission implemented instead is by SHAPE: one `__dunder__` target, a value
`ast.literal_eval` accepts. Every test below is the refusal half.

`ast.literal_eval` is the discriminator on purpose: a value it accepts contains
no Name, no Call and no Attribute, so the statement cannot have come from an
import and cannot read anything.
"""

from __future__ import annotations

import ast

from tests.unit.local_truth_helpers import load_gate as _check

#: Sources the widening must ADMIT -- they declare nothing derivable.
_ADMITTED = {
    "docstring only": '"""Doc."""\n',
    "empty": "",
    "future import": "from __future__ import annotations\n",
    "literal __all__": '"""Doc."""\n__all__ = ("a", "b")\n',
    "literal __all__ list": "__all__ = ['a']\n",
    "literal __version__": '__version__ = "1.00"\n',
}
#: Sources it must still REFUSE -- each declares something a gate must judge.
_REFUSED = {
    "a name-valued dunder": "__version__ = VERSION\n",
    "a call-valued dunder": "__all__ = tuple(names)\n",
    "an attribute-valued dunder": "__all__ = mod.NAMES\n",
    "a non-dunder assignment": "names = ('a',)\n",
    "a single-underscore assignment": "_names = ('a',)\n",
    "an import of the engine": "from pursuit.sdk import engine\n",
    "a function": "def render(ctx):\n    return ctx.state.thief\n",
    "a dunder plus a real import": '__all__ = ("a",)\nfrom pursuit.sdk import engine\n',
}


def test_the_two_tables_are_populated() -> None:
    """Anti-vacuity: an emptied table makes every loop below pass silently."""
    assert len(_ADMITTED) >= 4
    assert len(_REFUSED) >= 6


def test_every_admitted_shape_is_a_marker() -> None:
    scan = _check().scan
    for label, source in _ADMITTED.items():
        assert scan.is_package_marker(ast.parse(source)), label


def test_every_refused_shape_is_still_judged() -> None:
    scan = _check().scan
    for label, source in _REFUSED.items():
        assert not scan.is_package_marker(ast.parse(source)), label


def test_a_leaky_init_file_is_still_a_violation(tmp_path) -> None:
    """The whole point: `__init__.py` is admitted by SHAPE, never by NAME."""
    check = _check()
    root = tmp_path / "gui"
    root.mkdir(parents=True)
    (root / "__init__.py").write_text(
        '"""Doc."""\n__all__ = ("panel",)\n\n\ndef render(ctx):\n'
        "    return ctx.state.thief\n",
        encoding="utf-8",
    )
    violations = check.find_violations(root=root)
    assert violations, "a leaky __init__.py was waved through"
    assert any("__init__.py" in line for line in violations)


def test_a_package_holding_only_a_marker_still_refuses_to_certify(tmp_path) -> None:
    """The anti-vacuity property the widening must not have cost."""
    check = _check()
    root = tmp_path / "gui"
    root.mkdir(parents=True)
    (root / "__init__.py").write_text('"""Doc."""\n__all__ = ("panel",)\n', encoding="utf-8")
    assert check.main(root=root) == check.ExitCode.EMPTY_SCAN
