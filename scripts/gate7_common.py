"""Shared bootstrap + helpers for the GATE-7 measurement scripts (07-09).

Mirrors `gate6_common.py` exactly: a `sys.path` bootstrap, the REAL shipped
configs, and one file per concern. `scripts/` is scanned by NEITHER gate
(`check_line_limit.sh:18` enumerates `src/** tests/** training/**`;
`pyproject.toml:37` sets `source = ["src", "training"]`), so nothing here is
logic -- every behaviour these scripts measure already lives under `src/` and
is already covered. The 150-code-line limit is honoured by hand and each file
is additionally checked EXPLICITLY BY PATH.

GATE-7 NEEDS ZERO CREDENTIALS. Three environment variables are cleared at
import time so a grader's own shell can never turn a measurement into a live
API call or a live mail send: `ANTHROPIC_API_KEY` (gate6's precedent) plus the
two names `reporting.json` gives for the Gmail credential and token files.
Criterion 1's live half is therefore PENDING by construction here, not by
choice -- see `docs/phases/phase-7/GATE-7-MEASUREMENT.md`.

ONE REAL GAME FEEDS TWO CRITERIA. Criterion 2 needs a published snapshot and
criterion 3 needs a recorded game; playing one game and measuring both off it
is cheaper AND more honest than two games, because the two criteria then
answer for the same run, joined by `game_uid` in the evidence.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

for _name in ("ANTHROPIC_API_KEY", "PURSUIT_GMAIL_CREDENTIALS_PATH", "PURSUIT_GMAIL_TOKEN_PATH"):
    os.environ.pop(_name, None)

from pursuit.network.agent_audit_wiring import run_final_audit  # noqa: E402
from pursuit.network.agent_wiring import AgentConfig, load_agent_config  # noqa: E402
from tests.integration.two_peer_game import play_two_peer_game  # noqa: E402

POLICE_DIR = "config/police"
THIEF_DIR = "config/thief"
SHIPPED_REPORTING = REPO_ROOT / "config" / "police" / "reporting.json"

#: Rule 37/38's per-role counter. Read raw TEXT before and after the whole
#: measurement, exactly as `tests/_shipped_config_guard.read_counters` does:
#: this script plays a real game and must prove it advanced nothing.
SHIPPED_COUNTERS = (
    REPO_ROOT / "config" / "police" / "games_played.json",
    REPO_ROOT / "config" / "thief" / "games_played.json",
)

#: Fixed, so a rerun neither appends to nor duplicates a prior run's evidence.
GAME_UID = "gate7measure"


def load_configs() -> tuple[AgentConfig, AgentConfig]:
    """The REAL, shipped configs -- never a synthetic override."""
    return load_agent_config(POLICE_DIR), load_agent_config(THIEF_DIR)


def counter_snapshot() -> dict[str, str | None]:
    """Raw text of both shipped games-played counters, or None when absent."""
    return {
        path.name: (path.read_text(encoding="utf-8") if path.is_file() else None)
        for path in SHIPPED_COUNTERS
    }


@dataclass(frozen=True)
class RecordedGame:
    """One finished, audited two-peer game and both seats' contexts."""

    uid: str
    outcome_police: object
    outcome_thief: object
    ctx_police: object
    ctx_thief: object

    @property
    def outcomes_agree(self) -> bool:
        return self.outcome_police == self.outcome_thief


async def play_recorded_game(log_dir: Path, *, uid: str = GAME_UID) -> RecordedGame:
    """One real game on the shipped configs, then the final audit -- the order
    `agent_entrypoint.run_agent` uses, and the same helper
    `tests/integration/test_replay_roundtrip.py` drives."""
    cfg_a, cfg_b = load_configs()
    outcome_a, outcome_b, ctx_a, ctx_b = await play_two_peer_game(
        cfg_a, cfg_b, game_uid=uid, log_dir=log_dir,
    )
    await asyncio.gather(
        run_final_audit(ctx_a, board_outcome=outcome_a),
        run_final_audit(ctx_b, board_outcome=outcome_b),
    )
    return RecordedGame(uid, outcome_a, outcome_b, ctx_a, ctx_b)


class RecordingWatchdog:
    """`ctx.watchdog`'s surface, counting touches and freezing nothing.

    `end_of_game_chain.watchdog_touching` wraps the sink with `touch()` on
    entry and in a `finally`; this records that it happened without starting a
    daemon thread whose action is `os._exit`.
    """

    def __init__(self) -> None:
        self.touches = 0

    def touch(self) -> None:
        self.touches += 1


def outcome_name(outcome: object) -> str:
    """An `Outcome` member's value, or its `str` -- never a bare repr."""
    return getattr(outcome, "value", None) or str(outcome)
