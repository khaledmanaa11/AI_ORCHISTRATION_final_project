"""Reads the RECORDED token accounting and derives every figure
`docs/TOKEN-COST.md` publishes (08-09).

NO CALL IS MADE HERE. CLAUDE.md forbids a test or analysis that depends on
a live API, and rule 38 forbids a reported spend that was not measured. So
the only inputs are files already in the tracked set: the one real
Haiku 4.5 game (`gate4_measurement_live.json`, 2026-08-09) and the three
mocked ones beside it. `game_artifacts/` is deliberately UNTRACKED (D7-19)
and is never read -- an analysis that only reproduces on this machine
reproduces nowhere.

THE MOCKED FIGURES ARE NOT A SECOND SAMPLE. Its own note says the per-call
counts are SIMULATED. They are read anyway, for exactly one purpose: the
CALL COUNT per turn is a property of the pipeline and does transfer, so the
two can be compared on that axis and must not be pooled on any other.
`compare_call_rate` is that comparison and it is the only place the two
sources meet.

EMPTY EVIDENCE IS AN ERROR, not a zero. Every reader below raises when its
file is absent or has no usable spend block, because a token-cost analysis
that quietly reports 0 tokens is worse than none.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE = "docs/phases/phase-4/gate4_measurement_live.json"
MOCKED = "docs/phases/phase-4/gate4_measurement_mocked.json"
LANGUAGE_CONFIG = "config/police/language.json"
GAME_PARAMS = "config/police/game_params.json"
#: Table 18 row 5, FIXED. The worst case a team can be asked to play, and
#: therefore the horizon a series budget has to survive.
MAX_GAMES_PER_TEAM = 10
#: Table 18 row 1, FIXED -- what `gate4_report.extrapolate_series_cost`
#: already projects against, quoted here so the two agree.
SERIES_OPPONENTS = 6


def read_json(relative: str) -> dict:
    """One tracked evidence file, or a loud failure."""
    path = REPO_ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"{relative} is missing -- refusing to derive a spend from it")
    return json.loads(path.read_text(encoding="utf-8"))


def live_spend() -> dict:
    """The one real game's measured usage, with its own context."""
    data = read_json(LIVE)
    spend, live = data.get("token_spend", {}), data.get("live", {})
    calls, turns = int(live.get("provider_calls", 0)), int(data.get("turns_played", 0))
    inputs, outputs = int(spend.get("input_tokens", 0)), int(spend.get("output_tokens", 0))
    if not (calls and turns and inputs):
        raise ValueError(f"{LIVE} carries no usable live spend: {spend} / {live}")
    total = inputs + outputs
    return {
        "source": LIVE, "games": 1, "served_model": live.get("served_model"),
        "outcome": data.get("outcome"), "turns": turns, "calls": calls,
        "hints_sent": int(data.get("hints_sent", 0)),
        "input_tokens": inputs, "output_tokens": outputs, "total_tokens": total,
        "cost_usd": float(spend.get("cost_usd", 0.0)),
        "tokens_per_call": total / calls, "tokens_per_turn": total / turns,
        "calls_per_turn": calls / turns, "input_share": inputs / total,
        "usd_per_million_tokens": float(spend.get("cost_usd", 0.0)) / total * 1_000_000,
    }


def mocked_spend() -> dict:
    """The three simulated games, summed. Comparable on CALLS only."""
    data = read_json(MOCKED)
    games = data.get("token_spend", {}).get("games", [])
    turns = int(data.get("criterion_3_hint_every_turn", {}).get("turns_played", 0))
    if not games or not turns:
        raise ValueError(f"{MOCKED} carries no usable per-game spend block")
    calls = sum(int(game.get("calls", 0)) for game in games)
    inputs = sum(int(game.get("input_tokens", 0)) for game in games)
    outputs = sum(int(game.get("output_tokens", 0)) for game in games)
    return {
        "source": MOCKED, "games": len(games), "turns": turns, "calls": calls,
        "input_tokens": inputs, "output_tokens": outputs,
        "total_tokens": inputs + outputs,
        "tokens_per_call": (inputs + outputs) / calls,
        "calls_per_turn": calls / turns,
        "simulated": data.get("token_spend", {}).get("note", ""),
    }


def compare_call_rate(live: dict, mocked: dict) -> dict:
    """Where the mock is faithful and where it is not, as two ratios."""
    return {
        "calls_per_turn_live": live["calls_per_turn"],
        "calls_per_turn_mocked": mocked["calls_per_turn"],
        "calls_per_turn_ratio": live["calls_per_turn"] / mocked["calls_per_turn"],
        "tokens_per_call_ratio": live["tokens_per_call"] / mocked["tokens_per_call"],
    }


def budget_config() -> dict:
    """The shipped ladder and the move ceiling every projection scales by."""
    budget = read_json(LANGUAGE_CONFIG)["budget"]
    params = read_json(GAME_PARAMS)
    return {
        "token_budget_per_series": int(budget["token_budget_per_series"]),
        "short_prompt_threshold_tokens": int(budget["short_prompt_threshold_tokens"]),
        "template_only_threshold_tokens": int(budget["template_only_threshold_tokens"]),
        "move_ceiling": int(params["move_ceiling"]),
        "source": [LANGUAGE_CONFIG, GAME_PARAMS],
    }


def project(live: dict, config: dict) -> dict:
    """Scale the measured per-turn rate to a full-length game and a series.

    The live game ended in a capture at turn 14, well short of the 35-turn
    ceiling, so this EXTRAPOLATES. It is labelled as such everywhere it is
    printed and it assumes the per-turn rate is flat, which one game cannot
    demonstrate.
    """
    per_turn = live["tokens_per_turn"]
    per_game = per_turn * config["move_ceiling"]
    budget = config["token_budget_per_series"]
    return {
        "tokens_per_full_game": per_game,
        "usd_per_full_game": per_game * live["usd_per_million_tokens"] / 1_000_000,
        "games_within_budget": budget / per_game,
        "games_before_short_prompt": config["short_prompt_threshold_tokens"] / per_game,
        "games_before_template_only": config["template_only_threshold_tokens"] / per_game,
        "tokens_for_max_games": per_game * MAX_GAMES_PER_TEAM,
        "max_games_fits_budget": per_game * MAX_GAMES_PER_TEAM <= budget,
        "tokens_for_one_per_opponent": per_game * SERIES_OPPONENTS,
        "max_games_per_team": MAX_GAMES_PER_TEAM,
        "series_opponents": SERIES_OPPONENTS,
    }
