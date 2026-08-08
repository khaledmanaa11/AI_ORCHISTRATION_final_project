"""Standalone CI-runnable promotion of 03-02's structural STRAT-07 import gate.

Walks every module under `src/pursuit/strategy/` and fails if any of them
imports a name that could reach an LLM, an HTTP client, `subprocess`, a raw
`socket`, `pursuit.network`, or `pursuit.services` (rule 25 / STRAT-07,
STRAT-03). Deliberately a plain `ast` walk over source text: it never
imports `pursuit` itself, so it has zero dependency on the package being
installed and runs identically from a bare checkout in CI.

The `pursuit.services` case closes a hole this script had until plan 04-01:
`src/pursuit/services/` was an empty placeholder, so nothing under it could
be imported; Phase 4 fills it with `services/llm/`, and from that point a
strategy module could `from pursuit.services.llm.decode import decode_hint`
and reach a language model from inside the decision path with this script
still printing OK. `pursuit.shared` stays unguarded on purpose -- it is the
legal seam for cross-cutting types (e.g. `pursuit.shared.state.GameState`),
and strategy modules already import it freely.

`tests/integration/test_strategy_pluggable.py` (GATE-3) loads this exact
module by file path and calls `find_violations()` directly -- the pytest
suite and this CI-facing script are proven to run the SAME logic, not two
copies of it (QUAL-02), promoting `test_registry.py`'s original 03-02 check.

Usage::

    uv run python scripts/check_no_llm_in_strategy.py
    bash scripts/check_no_llm_in_strategy.sh   # the CI-facing wrapper
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

STRATEGY_ROOT = Path(__file__).resolve().parent.parent / "src" / "pursuit" / "strategy"

# STRAT-07 (rule 25): the decision path must be structurally unable to reach
# a language model, an HTTP client, subprocess, or a raw socket.
FORBIDDEN_IMPORTS = (
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


def strategy_module_paths(root: Path = STRATEGY_ROOT) -> list[Path]:
    return sorted(root.rglob("*.py"))


def imported_module_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def find_violations(root: Path = STRATEGY_ROOT) -> list[str]:
    """Return one message per forbidden/networking import found; `[]` if clean.

    `root` is overridable so a test can point this at a synthetic tmp_path
    tree (proving the negative case) without ever mutating real source under
    `src/pursuit/strategy/`.
    """
    violations = []
    for path in strategy_module_paths(root):
        for name in imported_module_names(path):
            top = name.split(".")[0]
            if name == "pursuit.network" or name.startswith("pursuit.network."):
                violations.append(f"{path}: imports {name!r} (STRAT-03 -- networking)")
            elif name == "pursuit.services" or name.startswith("pursuit.services."):
                violations.append(
                    f"{path}: imports {name!r} (STRAT-07 -- reaches an LLM via services)"
                )
            elif name in FORBIDDEN_IMPORTS or top in FORBIDDEN_IMPORTS:
                violations.append(
                    f"{path}: imports {name!r} (STRAT-07 -- LLM/HTTP/subprocess/socket)"
                )
    return violations


def main() -> int:
    violations = find_violations()
    for violation in violations:
        print(f"VIOLATION: {violation}")
    if violations:
        print(f"\n{len(violations)} forbidden import(s) found under {STRATEGY_ROOT}.")
        return 1
    print(f"OK: no forbidden imports under {STRATEGY_ROOT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
