"""Find every queue-pull site BY READING THE SOURCE (05-18).

Not a `test_*.py` file on purpose -- pytest never collects it (the
`_fakes_agent.py` / `_early_reveal_fixtures.py` precedent).

WHY AN AST WALK AND NOT A LIST. Five instances of one defect class --
05-09, 05-10, 05-15, 05-17 and deferred item #18 -- were each "an unexpected
envelope type at a layer boundary is mishandled", and every one was found by
grepping outward AFTER the previous fix rather than by review. A hand-written
list of the sites to check is a snapshot: it is correct on the day it is
typed and silently stale the day someone adds a pull, which is exactly the
mechanism by which this class kept regenerating. Enumerating from source
means a NEW site is covered on the day it lands and cannot opt out -- the
test that consumes this module FAILS on a discovered site it has no driver
for.

THE RULE, stated once. A pull site is a function that can OBSERVE an
envelope's TYPE. Mechanically, in two stages over `src/pursuit/network/`:

  SEED     a top-level function whose body -- including nested closures,
           which is where `_pull` lives in two of them -- reads the inbound
           queue: it names a `.queue` attribute, or calls `.get`/`.get_nowait`
           on something named queue.
  CLOSURE  iterated to a fixpoint: any top-level function that CALLS a
           member of the set whose own return annotation mentions
           `Envelope`.

The annotation is what BOUNDS the closure, and that is deliberate. Without
it the set would climb through every caller up to `run_agent`; with it the
set stops exactly where the Envelope stops flowing outward -- so
`turn_actions.await_opponent_turn` is IN (it binds one and reads its type)
while `turn_commit.initiate` is OUT (its leg returns a hash, not an
envelope). Every one of the five historical instances sits inside the set
this produces.
"""

from __future__ import annotations

import ast
import pathlib

NETWORK_PACKAGE = pathlib.Path(__file__).resolve().parents[2] / "src" / "pursuit" / "network"

_QUEUE = "queue"
_GETTERS = {"get", "get_nowait"}
_ENVELOPE = "Envelope"


def _top_level_functions(path: pathlib.Path) -> list[ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef | ast.FunctionDef)]


def _reads_the_inbound_queue(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Attribute):
            continue
        if sub.attr == _QUEUE:
            return True
        if sub.attr in _GETTERS and isinstance(sub.value, ast.Name) and _QUEUE in sub.value.id:
            return True
    return False


def _names_called(node: ast.AST) -> set[str]:
    called = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        if isinstance(sub.func, ast.Name):
            called.add(sub.func.id)
        elif isinstance(sub.func, ast.Attribute):
            called.add(sub.func.attr)
    return called


def _yields_an_envelope(node: ast.AST) -> bool:
    return node.returns is not None and _ENVELOPE in ast.unparse(node.returns)


def pull_sites() -> dict[str, str]:
    """`{function name: defining module}` for every queue-pull site.

    Raises rather than returning an empty mapping: an empty enumeration is
    the vacuity trap this whole module exists to avoid (an empty pytest
    `parametrize` set is a SILENT SKIP, and a control that skips is a
    control that cannot fail). A rename or a moved package must break this
    loudly, not quietly stop testing anything."""
    functions: dict[str, tuple[str, ast.AST]] = {}
    for path in sorted(NETWORK_PACKAGE.glob("*.py")):
        for function in _top_level_functions(path):
            functions[function.name] = (path.name, function)

    sites = {name for name, (_, fn) in functions.items() if _reads_the_inbound_queue(fn)}
    while True:
        yielding = {name for name in sites if _yields_an_envelope(functions[name][1])}
        found = {
            name for name, (_, fn) in functions.items()
            if name not in sites and _names_called(fn) & yielding
        }
        if not found:
            break
        sites |= found

    if not sites:
        raise AssertionError(
            f"ZERO pull sites discovered under {NETWORK_PACKAGE} -- the enumeration is "
            "vacuous and every case built on it would pass without testing anything",
        )
    return {name: functions[name][0] for name in sorted(sites)}
