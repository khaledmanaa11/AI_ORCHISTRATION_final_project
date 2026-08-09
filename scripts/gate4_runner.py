"""The two GATE-4 run modes (04-14 Task 1/2): --mocked (full seeded set,
no key) and --live (one real game plus the D-33 liveness assertion).

Live-run constraint honoured here, not just at the call site: `_run_live`
attempts NOTHING against the network when `ANTHROPIC_API_KEY` is absent --
it returns the PENDING marker immediately, before building any config or
provider. Per the plan's own rule: template-path numbers must never be
reported as live ones.
"""

from __future__ import annotations

import os

from gate4_fixtures import (
    build_live_provider,
    score_fixture_language_live,
    score_fixture_language_mocked,
)
from gate4_games import GATE4_SEEDS, run_one_game, run_seeded_set
from gate4_report import build_report, token_cost_usd
from gate4_scent import measure_decay_law, measure_handshake_digest

from pursuit.network.agent_wiring import load_agent_config

RERUN_COMMAND = "ANTHROPIC_API_KEY=... uv run python scripts/measure_gate4.py --live"


def _decode_fixture_summary(results_by_language: dict) -> dict:
    summary = {}
    for language, results in results_by_language.items():
        matched = sum(1 for r in results if r.matched)
        summary[language] = {
            "cases": len(results),
            "matched": matched,
            "accuracy": matched / len(results) if results else 0.0,
            "failures": [r.case_id for r in results if not r.matched],
        }
    return summary


async def run_mocked() -> dict:
    cfg_a = load_agent_config("config/police")
    cfg_b = load_agent_config("config/thief")
    games = await run_seeded_set(mocked=True)
    decay = measure_decay_law(cfg_a)
    handshake = measure_handshake_digest(cfg_a, cfg_b)
    fixtures = {
        "en": await score_fixture_language_mocked("en"),
        "he": await score_fixture_language_mocked("he"),
    }
    live = {
        "status": "PENDING",
        "reason": "ANTHROPIC_API_KEY not set on the measurement machine",
        "rerun_command": RERUN_COMMAND,
        "what_it_will_prove": [
            "response.model names Haiku 4.5 (liveness, guards against D-33 masking a dead key)",
            "provider calls > 0 and token usage > 0 (not the template fallback)",
            "real per-turn latency against the watchdog threshold",
            "real token spend from response.usage, in tokens and USD",
            "real decode accuracy on the EN/HE fixtures via the actual model",
        ],
    }
    word_limit = cfg_a.language.model["hint_word_limit"]
    return build_report(
        mode="mocked",
        games=games,
        decay=decay,
        handshake=handshake,
        fixtures=_decode_fixture_summary(fixtures),
        word_limit=word_limit,
        live=live,
    )


async def run_live() -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "mode": "live",
            "seeds": [],
            "live": {
                "status": "PENDING",
                "reason": "ANTHROPIC_API_KEY not set on this machine -- no live call attempted",
                "rerun_command": RERUN_COMMAND,
            },
        }

    cfg_a = load_agent_config("config/police")
    word_limit = cfg_a.language.model["hint_word_limit"]
    game = await run_one_game(seed=GATE4_SEEDS[0], belief_enabled=True, mocked=False)
    fixtures = {
        "en": await score_fixture_language_live("en", build_live_provider(cfg_a)),
        "he": await score_fixture_language_live("he", build_live_provider(cfg_a)),
    }

    reached_model = bool(game.served_model) and "haiku" in game.served_model.lower()
    calls = game.token_spend.get("calls", 0)
    input_tokens = game.token_spend.get("input_tokens", 0)
    output_tokens = game.token_spend.get("output_tokens", 0)
    live_ok = reached_model and calls > 0 and (input_tokens + output_tokens) > 0

    return {
        "mode": "live",
        "seeds": [game.seed],
        "live": {
            "status": "COMPLETED" if live_ok else "VOID",
            "served_model": game.served_model,
            "provider_calls": calls,
            "token_usage": input_tokens + output_tokens,
            "assertion": (
                "response.model names Haiku 4.5 and calls/tokens > 0"
                if live_ok
                else "LIVE MEASUREMENT VOID: the liveness assertion failed -- "
                "see served_model/provider_calls/token_usage above; do not treat "
                "any number below as a live result"
            ),
        },
        "wall_time_seconds": {
            "mean": sum(game.per_turn_seconds) / len(game.per_turn_seconds)
            if game.per_turn_seconds
            else 0.0,
            "n": len(game.per_turn_seconds),
        },
        "token_spend": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": token_cost_usd(input_tokens, output_tokens),
        },
        "decode_fixture_accuracy": _decode_fixture_summary(fixtures),
        "outcome": game.outcome,
        "hints_sent": game.hints_total,
        "turns_played": game.turns_completed,
        "word_limit": word_limit,
    }
