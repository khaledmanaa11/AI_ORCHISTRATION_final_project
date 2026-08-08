"""Tests for TokenBudget -- D-35's cumulative spend + degrade ladder."""

import json

from pursuit.services.llm.budget import DegradeLevel, TokenBudget


def _budget(token_budget: int = 1000, short: int = 400, template: int = 800) -> TokenBudget:
    return TokenBudget(
        token_budget=token_budget,
        short_prompt_threshold=short,
        template_only_threshold=template,
    )


def test_starts_full() -> None:
    assert _budget().level is DegradeLevel.FULL


def test_crosses_to_short_prompt_at_its_threshold() -> None:
    budget = _budget(short=400, template=800)
    budget.settle(input_tokens=300, output_tokens=101, estimated_tokens=0)
    assert budget.level is DegradeLevel.SHORT_PROMPT


def test_crosses_to_template_only_at_its_threshold() -> None:
    budget = _budget(short=400, template=800)
    budget.settle(input_tokens=700, output_tokens=101, estimated_tokens=0)
    assert budget.level is DegradeLevel.TEMPLATE_ONLY


def test_levels_cross_in_order_never_skip_or_regress() -> None:
    """Cumulative totals after each of 4 settles of 60: 60, 120, 180, 240."""
    budget = _budget(short=100, template=200)
    levels = []
    for _ in range(4):
        budget.settle(input_tokens=60, output_tokens=0, estimated_tokens=0)
        levels.append(budget.level)
    assert levels == [
        DegradeLevel.FULL,  # 60 < 100
        DegradeLevel.SHORT_PROMPT,  # 100 <= 120 < 200
        DegradeLevel.SHORT_PROMPT,  # 100 <= 180 < 200
        DegradeLevel.TEMPLATE_ONLY,  # 240 >= 200
    ]


def test_reserve_alone_can_already_raise_the_level() -> None:
    """D-34/D-35: a queued (not yet settled) call already counts."""
    budget = _budget(short=100, template=200)
    budget.reserve(150)
    assert budget.level is DegradeLevel.SHORT_PROMPT


def test_level_never_regresses_after_settle_reconciles_downward() -> None:
    budget = _budget(short=50, template=1000)
    budget.reserve(100)
    assert budget.level is DegradeLevel.SHORT_PROMPT
    budget.settle(input_tokens=1, output_tokens=1, estimated_tokens=100)
    assert budget.level is DegradeLevel.SHORT_PROMPT  # not back down to FULL


def test_excess_usage_over_the_estimate_can_cross_a_threshold() -> None:
    budget = _budget(short=500, template=2000)
    budget.reserve(10)  # tiny estimate, well under the 500 threshold
    assert budget.level is DegradeLevel.FULL
    budget.settle(input_tokens=300, output_tokens=300, estimated_tokens=10)
    assert budget.level is DegradeLevel.SHORT_PROMPT  # 600 > 500


def test_settle_lands_the_full_actual_usage_not_just_the_estimate() -> None:
    budget = _budget(short=1000, template=2000)
    budget.reserve(10)
    budget.settle(input_tokens=400, output_tokens=400, estimated_tokens=10)
    report = budget.report()
    assert report["input_tokens"] == 400
    assert report["output_tokens"] == 400
    assert report["calls"] == 1


def test_exceeding_the_whole_budget_yields_template_only_with_no_exception() -> None:
    budget = _budget(token_budget=1000, short=400, template=800)
    budget.settle(input_tokens=5000, output_tokens=5000, estimated_tokens=0)
    assert budget.level is DegradeLevel.TEMPLATE_ONLY


def test_report_round_trips_through_json_dumps_unchanged() -> None:
    budget = _budget()
    budget.settle(input_tokens=50, output_tokens=25, estimated_tokens=0)
    report = budget.report()
    assert json.loads(json.dumps(report)) == report


def test_report_contains_every_required_field() -> None:
    report = _budget(token_budget=1000).report()
    for key in ("calls", "input_tokens", "output_tokens", "level", "budget"):
        assert key in report
    assert report["budget"] == 1000
    assert report["calls"] == 0


def test_calls_counts_settled_calls_only_not_reservations() -> None:
    budget = _budget()
    budget.reserve(10)
    assert budget.report()["calls"] == 0
    budget.settle(input_tokens=1, output_tokens=1, estimated_tokens=10)
    assert budget.report()["calls"] == 1


def test_multiple_settled_calls_accumulate() -> None:
    budget = _budget(token_budget=10_000, short=10_000, template=10_000)
    for _ in range(3):
        budget.reserve(5)
        budget.settle(input_tokens=10, output_tokens=5, estimated_tokens=5)
    report = budget.report()
    assert report["calls"] == 3
    assert report["input_tokens"] == 30
    assert report["output_tokens"] == 15
