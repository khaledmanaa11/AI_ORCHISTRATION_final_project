"""D-63: Step-0 declaration auto-collect + the persisted games-played counter.

Every field is gathered automatically -- OS/CPU/RAM via `platform`/`psutil`,
GPU best-effort via `nvidia-smi` (an honest `{"present": False, "detail":
"not detected"}` on ANY failure, never a fabricated GPU -- critical honesty
requirement), the exact commit hash via `git rev-parse HEAD` (raises loudly
on failure, never a blank hash, rules 24/53). Nothing here is hand-typed;
the sanity display is a single non-blocking `print` line (rule 24's own
corr. c -- league games run unattended, never `input()`).

`read_games_played`/`record_game_played` are plain functions over a
caller-given path (no `pursuit.network` dependency) -- rule 37/38: the
counter is read BEFORE the game and incremented exactly once, at game end,
via `pursuit.shared.durable_write`'s existing crash-safe write/read pair
(Phase 3's own QTable.save() checkpoint precedent, not a new scheme).
"""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

import psutil

from pursuit.shared.durable_write import durable_write_json, load_json_with_fallback

# Structural constants, not PARAMETERS.md values: a byte->GB unit conversion
# and QTable.save()'s own local durable-write retry/backoff precedent
# (03-05-SUMMARY.md: "_SAVE_RETRIES=3/_SAVE_BACKOFF_SECONDS=0.1s"), reused
# here for the SAME class of small, local, crash-safe JSON write.
_BYTES_PER_GB = 1024**3
_COUNTER_RETRIES = 3
_COUNTER_BACKOFF_SECONDS = 0.1


class DeclarationField:
    """§5.5 field names -- structural, avoids magic strings (house pattern)."""

    ROLE = "role"
    TEAM_CODE = "team_code"
    OS = "os"
    CPU = "cpu"
    RAM_GB = "ram_gb"
    GPU = "gpu"
    LLM_NAME = "llm_name"
    CODE_VERSION = "code_version"
    GAMES_PLAYED_SO_FAR = "games_played_so_far"
    COMMIT_HASH = "commit_hash"


class GamesPlayedField:
    """The one field the per-role counter file carries."""

    COUNT = "games_played"


def _collect_cpu() -> dict:
    """`psutil.cpu_count()` plus a best-effort frequency reading -- some
    platforms/containers raise or return None for `cpu_freq()`; an honest
    `None` there, never a fabricated frequency."""
    freq_mhz = None
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq is not None:
            freq_mhz = cpu_freq.current
    except (OSError, NotImplementedError, AttributeError, RuntimeError):
        freq_mhz = None
    return {"cores": psutil.cpu_count(), "freq_mhz": freq_mhz}


def _collect_gpu() -> dict:
    """Best-effort `nvidia-smi` probe. ANY failure (missing binary, no GPU,
    driver error) yields the honest not-detected shape -- never an invented
    GPU or VRAM figure (critical honesty requirement)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, check=True,
        )
        name, _, vram = result.stdout.strip().partition(",")
        return {"present": True, "name": name.strip(), "vram": vram.strip()}
    except (OSError, subprocess.CalledProcessError):
        return {"present": False, "detail": "not detected"}


def _git_commit_hash() -> str:
    """`git rev-parse HEAD`, the first `subprocess` caller in `src/pursuit/`
    (RESEARCH §12). Raises loudly on failure -- never a blank hash."""
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def collect_declaration(
    *, role: str, team_code: str, llm_name: str, code_version: str, games_played: int,
) -> dict:
    """Assemble the full §5.5 field set, entirely auto-collected."""
    declaration = {
        DeclarationField.ROLE: role,
        DeclarationField.TEAM_CODE: team_code,
        DeclarationField.OS: platform.platform(),
        DeclarationField.CPU: _collect_cpu(),
        DeclarationField.RAM_GB: psutil.virtual_memory().total / _BYTES_PER_GB,
        DeclarationField.GPU: _collect_gpu(),
        DeclarationField.LLM_NAME: llm_name,
        DeclarationField.CODE_VERSION: code_version,
        DeclarationField.GAMES_PLAYED_SO_FAR: games_played,
        DeclarationField.COMMIT_HASH: _git_commit_hash(),
    }
    print(f"[Step-0] declaration collected: {declaration}")  # non-blocking sanity line
    return declaration


def read_games_played(path: Path | str) -> int:
    """Rule 37: the counter BEFORE this game. `0` for a fresh team/role, or
    on any malformed/absent file -- never raises."""
    try:
        data = load_json_with_fallback(path)
    except (FileNotFoundError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0
    value = data.get(GamesPlayedField.COUNT, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def record_game_played(path: Path | str) -> None:
    """Rule 37/38: increment by exactly one, durably, at game end only."""
    current = read_games_played(path)
    durable_write_json(
        path, {GamesPlayedField.COUNT: current + 1},
        retries=_COUNTER_RETRIES, backoff=_COUNTER_BACKOFF_SECONDS,
    )
