#!/usr/bin/env sh
# STRAT-07 / rule 25 CI gate: the language model must never be reachable
# from the move-decision path. Promotes 03-02's pytest-only structural
# import check (tests/unit/strategy/test_registry.py) into a standalone,
# CI-runnable script per 03-10-PLAN.md Task 1 -- named so it can be its own
# job step (AI-SPEC Sec5 "CI/CD Integration"), independent of the pytest run.
#
# Usage:
#   scripts/check_no_llm_in_strategy.sh
set -eu

script_dir=$(dirname "$0")
uv run python "$script_dir/check_no_llm_in_strategy.py"
