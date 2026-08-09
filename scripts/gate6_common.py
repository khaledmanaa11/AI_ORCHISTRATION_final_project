"""Shared bootstrap + small helpers for the GATE-6 measurement scripts
(06-04) -- mirrors gate4_games.py's own sys.path bootstrap and the
gate4_*/gate5_* file-per-concern split (scripts/ is outside the coverage
gate, matching that precedent; the 150-code-line house limit is still
honored by hand, per this plan's own hard rule).

GATE-6 needs zero credentials and zero env vars (06-PLAN-OUTLINE.md Sec5):
ANTHROPIC_API_KEY is explicitly cleared here so a grader's own shell
environment can never turn this into a live-API run by accident, mirroring
tests/integration/test_step0_and_audit.py's own `monkeypatch.delenv` -- the
whole flow (Step-0 collection, commit-reveal, the Final-Reveal audit) plays
correctly through the language layer's existing no-key fallback (04-12).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ.pop("ANTHROPIC_API_KEY", None)

from pursuit.network.agent_wiring import AgentConfig, load_agent_config  # noqa: E402

POLICE_DIR = "config/police"
THIEF_DIR = "config/thief"


def load_configs() -> tuple[AgentConfig, AgentConfig]:
    """The REAL, shipped configs -- never a synthetic override (must_haves:
    "measure_gate6.py runs entirely on localhost against the real, shipped
    config/police and config/thief")."""
    return load_agent_config(POLICE_DIR), load_agent_config(THIEF_DIR)


def events(log_path: Path) -> list[dict]:
    """Every JSONL record in append order; `[]` for a log that was never
    written (e.g. a run that aborted before move 1)."""
    if not log_path.exists():
        return []
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def ledger_path(ctx) -> Path:
    """D-64's `<log-file-stem>.ledger.jsonl` convention -- the SAME formula
    turn_commit_wait.py/agent_audit_wiring.py already use internally."""
    return ctx.log_path.parent / f"{ctx.log_path.stem}.ledger.jsonl"


def wire_log_text(log_path: Path) -> str:
    """Raw file text for the grep-style nonce-absence check (D-64: the
    nonce never rides the wire-mirroring log)."""
    return log_path.read_text(encoding="utf-8") if log_path.exists() else ""
