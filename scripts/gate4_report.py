"""Assembles the GATE-4 JSON result from every measured piece (04-14 Task
1/2) -- one place the Sec10.4 verdicts are computed FROM the numbers
(must_haves: "each of the three criteria gets a NUMBER, not a verdict...
[and] the document says so with its number", "a pass/fail that follows
from the number").
"""

from __future__ import annotations

from datetime import datetime, timezone

from gate4_games import GATE4_SEEDS, GameMeasurement, cop_win_rate

#: Anthropic's published Claude Haiku 4.5 API pricing (anthropic.com/pricing),
#: USD per million tokens, as read while writing this script (2026-08). This
#: is NOT a docs/PARAMETERS.md value -- that file governs only the book's
#: game numerics (docs/PARAMETERS.md's own header). Reconfirm against the
#: live pricing page before Phase 7's league spend email (PARAMETERS.md
#: Table 18 row 4): a vendor may revise a published rate at any time.
HAIKU_INPUT_USD_PER_MTOK = 1.00
HAIKU_OUTPUT_USD_PER_MTOK = 5.00
_SERIES_OPPONENTS = 6  # PARAMETERS.md Table 18 row 1, fixed
_SERIES_TOKEN_BUDGET = 200_000  # Table 18 row 4, negotiable, our shipped default


def token_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * HAIKU_INPUT_USD_PER_MTOK
        + output_tokens / 1_000_000 * HAIKU_OUTPUT_USD_PER_MTOK
    )


def extrapolate_series_cost(per_game_input: int, per_game_output: int) -> dict:
    """One game's real usage, scaled to a full six-opponent series
    (PARAMETERS.md Table 18 row 1) against the ~200,000 token budget
    (row 4) -- the figure Phase 7's league report states."""
    tokens = _SERIES_OPPONENTS * (per_game_input + per_game_output)
    cost = _SERIES_OPPONENTS * token_cost_usd(per_game_input, per_game_output)
    return {
        "opponents": _SERIES_OPPONENTS,
        "projected_series_tokens": tokens,
        "series_budget": _SERIES_TOKEN_BUDGET,
        "within_budget": tokens <= _SERIES_TOKEN_BUDGET,
        "projected_series_cost_usd": cost,
    }


def _stats(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "p95": 0.0, "n": 0}
    ordered = sorted(values)
    idx = max(0, int(round(0.95 * (len(ordered) - 1))))
    return {"mean": sum(ordered) / len(ordered), "p95": ordered[idx], "n": len(ordered)}


def summarize_criterion_1(games: list[GameMeasurement]) -> dict:
    """must_haves #1: fraction of turns a hint became evidence, and the
    mean absolute posterior change on exactly those turns."""
    evidence_deltas: list[float] = []
    evidence_turns = 0
    total_turns = 0
    for g in games:
        if g.belief is None:
            continue
        evidence_deltas.extend(g.belief.evidence_deltas)
        evidence_turns += len(g.belief.evidence_deltas)
        total_turns += g.belief.turns
    fraction = evidence_turns / total_turns if total_turns else 0.0
    mean_delta = sum(evidence_deltas) / len(evidence_deltas) if evidence_deltas else 0.0
    return {
        "turns_measured": total_turns,
        "evidence_turns": evidence_turns,
        "fraction_hint_became_inference": fraction,
        "mean_absolute_posterior_change_on_evidence_turns": mean_delta,
        "verdict": "PASS" if evidence_turns > 0 and mean_delta > 0.0 else "FAIL",
    }


def summarize_criterion_3(games: list[GameMeasurement], *, word_limit: int) -> dict:
    """must_haves #3: hint every turn, within the word limit, both intents
    observed, intent-before-text (structural), zero outgoing coordinates."""
    all_words = [w for g in games for w in g.hints_word_counts]
    total_hints = sum(g.hints_total for g in games)
    total_turns = sum(g.turns_completed for g in games)
    intent_counts = {"truth": 0, "lie": 0}
    leaks = 0
    for g in games:
        intent_counts["truth"] += g.intent_counts.get("truth", 0)
        intent_counts["lie"] += g.intent_counts.get("lie", 0)
        leaks += g.coordinate_leaks
    within_limit = all(w <= word_limit for w in all_words)
    both_intents = intent_counts["truth"] > 0 and intent_counts["lie"] > 0
    hint_every_turn = total_hints >= total_turns and total_turns > 0
    verdict = "PASS" if (hint_every_turn and within_limit and both_intents and leaks == 0) else "FAIL"
    return {
        "hints_sent": total_hints,
        "turns_played": total_turns,
        "hint_every_turn": hint_every_turn,
        "max_word_count": max(all_words) if all_words else 0,
        "word_limit": word_limit,
        "within_word_limit": within_limit,
        "intent_counts": intent_counts,
        "both_intents_occurred": both_intents,
        "intent_committed_before_text_fraction": 1.0 if total_hints else 0.0,
        "intent_committed_before_text_method": (
            "structural, not timestamp-based: build_deception_plan() (which fixes "
            "plan.intent) returns before compose_outgoing()/compose() is even called -- "
            "`plan` is a required positional argument to compose_outgoing, so no call "
            "that produces hint text can exist without an intent already decided. "
            "Cross-checked against tests/integration/test_language_pipeline.py's own "
            "Figure-7 order spy and tests/integration/test_gate4.py's GATE-4-specific one."
        ),
        "outgoing_coordinate_leaks": leaks,
        "verdict": verdict,
    }


def build_report(
    *, mode: str, games: dict, decay, handshake, fixtures: dict, word_limit: int, live: dict
) -> dict:
    belief_on = games["belief_on"]
    belief_off = games["belief_off"]
    return {
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seeds": list(GATE4_SEEDS),
        "criterion_1_hint_to_inference": summarize_criterion_1(belief_on),
        "criterion_2_scent_decay": {
            "turns": decay.turns,
            "max_deviation": decay.max_deviation,
            "verdict": "PASS" if decay.max_deviation < 1e-6 else "FAIL",
            "handshake_scent_digest_matched": handshake.matched,
            "police_scent_digest": handshake.police_digest,
            "thief_scent_digest": handshake.thief_digest,
        },
        "criterion_3_hint_every_turn": summarize_criterion_3(belief_on, word_limit=word_limit),
        "decode_fixture_accuracy": fixtures,
        "wall_time_seconds": _stats([s for g in belief_on for s in g.per_turn_seconds]),
        "token_spend": {
            "note": (
                "mocked mode uses SIMULATED per-call token counts, never real API usage"
                if mode == "mocked"
                else "real response.usage from the live API"
            ),
            "games": [g.token_spend for g in belief_on],
        },
        "belief_on_off_win_rate": {
            "belief_on_cop_win_rate": cop_win_rate(belief_on),
            "belief_off_cop_win_rate": cop_win_rate(belief_off),
            "note": (
                "Outline Sec1's honesty clause predicts no scoring gain in Regime A; "
                "this is the measured result, reported as-is."
            ),
        },
        "live": live,
    }
