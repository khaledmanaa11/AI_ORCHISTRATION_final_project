#!/usr/bin/env sh
# Rules 8-9 CI gate: nothing under src/pursuit/gui/ may reach the objective
# board state -- neither by importing a package that hands out a GameState
# or an AgentContext, nor by reading `.state.cop`/`.state.thief`/
# `.state.barriers` off a live context. Rule 9's sanction is PROJECT
# DISQUALIFICATION (docs/RULES.md:30), which is why this is its own CI job
# step rather than one assertion inside the pytest run.
#
# Exits 2 -- not 0 -- when the scan set is EMPTY. src/pursuit/gui/ does not
# exist until 07-06, and a gate that reports OK for having looked at
# nothing is worse than no gate.
#
# Usage:
#   scripts/check_local_truth.sh
set -eu

script_dir=$(dirname "$0")
uv run python "$script_dir/check_local_truth.py"
