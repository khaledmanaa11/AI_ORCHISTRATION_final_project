#!/usr/bin/env sh
# Rules 8-9 CI gate: nothing under src/pursuit/gui/ may reach the objective
# board state -- neither by importing a package that hands out a GameState
# or an AgentContext, nor by reading `.state.cop`/`.state.thief`/
# `.state.barriers` off a live context -- directly, through a local alias,
# or through a dynamic key such as getattr(x, "thief") or d["cop"] (07-06
# closed all three, D7-9). Rule 9's sanction is PROJECT DISQUALIFICATION
# (docs/RULES.md:30), which is why this is its own CI job step rather than
# one assertion inside the pytest run.
#
# Exits 2 -- not 0 -- when the scan JUDGED NOTHING: a missing root, a root
# with no modules, or a root holding only bare package markers. 07-06 turned
# this gate green by writing modules that pass it, never by softening it, and
# an empty __init__.py provably does not satisfy it.
#
# Usage:
#   scripts/check_local_truth.sh
set -eu

script_dir=$(dirname "$0")
uv run python "$script_dir/check_local_truth.py"
