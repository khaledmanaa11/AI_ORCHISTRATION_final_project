"""Standalone per-agent league entry point (NET-01, NET-04, D-02).

    uv run python -m pursuit.main --config-dir config/police
    uv run python -m pursuit.main --config-dir config/thief
    uv run python -m pursuit.main --config-dir config/police --check-config

This process is one complete, independent agent. The other side is a
separate process started the SAME way with a different --config-dir. The
two share no runtime state (NET-02) and there is no referee (D-01) --
scripts/dev_launch.py only spawns two copies of this exact command.

A thin shell: it parses --config-dir, loads the resolved config, and hands
off to `agent_lifecycle.run_agent`. It holds no game rule, no turn logic and
no state machine of its own.
"""

from __future__ import annotations

import argparse
import asyncio

from pursuit.network import agent_lifecycle


def build_parser() -> argparse.ArgumentParser:
    """--config-dir names the per-agent directory (NET-01): role and both
    endpoints come from there, and it is the only way the two agents'
    commands differ."""
    parser = argparse.ArgumentParser(description="Run one pursuit agent, standalone.")
    parser.add_argument(
        "--config-dir", required=True,
        help="Per-agent config directory, e.g. config/police or config/thief",
    )
    parser.add_argument(
        "--check-config", action="store_true",
        help="Load and print the resolved role/endpoints, then exit without starting a server.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = agent_lifecycle.load_agent_config(args.config_dir)

    if args.check_config:
        print(f"role={cfg.role}")
        print(f"listen={cfg.net.host}:{cfg.net.port}")
        print(f"opponent_url={cfg.net.opponent_url}")
        return 0

    asyncio.run(agent_lifecycle.run_agent(args.config_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
