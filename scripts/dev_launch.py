"""Convenience launcher for local iteration. Each agent also starts
standalone in its own terminal with `uv run python -m pursuit.main
--config-dir config/police|config/thief` -- the standalone path is the
league path (D-02). This script holds no game state, coordinates nothing,
and is not a referee (D-01).

    uv run python scripts/dev_launch.py

It spawns the two standalone commands above as subprocesses and waits for
both. It imports NOTHING from the agent's own package, reads no per-agent
numeric configuration, decodes no wire message and holds no board snapshot
of any kind, and passes no data between the two children beyond their own
fixed --config-dir argument. Deleting this script changes nothing about how
a league game runs.
"""

import subprocess
import sys

_CONFIG_DIRS = ("config/police", "config/thief")


def _command(config_dir: str) -> list[str]:
    return [sys.executable, "-m", "pursuit.main", "--config-dir", config_dir]


def main() -> int:
    processes = [subprocess.Popen(_command(config_dir)) for config_dir in _CONFIG_DIRS]
    exit_code = 0
    try:
        for process in processes:
            code = process.wait()
            exit_code = exit_code or code
    except KeyboardInterrupt:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait()
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
