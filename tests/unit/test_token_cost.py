"""The token-cost analysis derives from recorded spend, or it fails (08-09).

Every expected value below is RE-DERIVED from the same tracked JSON the
module reads, never typed in. A test that hard-codes `524.9` passes for as
long as nobody re-measures and then silently pins a stale figure as truth --
which is the failure `docs/TOKEN-COST.md` exists to avoid, not to repeat.

The refusals get their own tests because a spend analysis that reports zero
tokens over a missing file is worse than no analysis: it reads as "we spent
almost nothing" instead of "we measured nothing".
"""

from __future__ import annotations

import json

import pytest

from tests.unit.submission_gate_helpers import load

read = load("token_cost_read")
prompts = load("token_cost_prompts")

_LIVE = json.loads((read.REPO_ROOT / read.LIVE).read_text(encoding="utf-8"))
_MOCKED = json.loads((read.REPO_ROOT / read.MOCKED).read_text(encoding="utf-8"))


def test_every_input_is_tracked_and_none_is_a_local_run_artifact():
    """`logs/` is gitignored and `game_artifacts/` is untracked by design
    (D7-19); an analysis fed from either reproduces on one machine only."""
    for relative in (read.LIVE, read.MOCKED, read.LANGUAGE_CONFIG, read.GAME_PARAMS):
        assert not relative.startswith(("logs/", "game_artifacts/")), relative
        assert (read.REPO_ROOT / relative).is_file(), relative


def test_the_live_figures_are_arithmetic_over_the_recorded_file():
    live = read.live_spend()
    spend = _LIVE["token_spend"]
    assert live["input_tokens"] == spend["input_tokens"]
    assert live["output_tokens"] == spend["output_tokens"]
    assert live["calls"] == _LIVE["live"]["provider_calls"]
    total = spend["input_tokens"] + spend["output_tokens"]
    assert live["total_tokens"] == total == _LIVE["live"]["token_usage"]
    assert live["tokens_per_call"] == pytest.approx(total / live["calls"])
    assert live["tokens_per_turn"] == pytest.approx(total / _LIVE["turns_played"])
    assert live["input_share"] == pytest.approx(spend["input_tokens"] / total)


def test_a_missing_evidence_file_raises_rather_than_reporting_zero(monkeypatch):
    monkeypatch.setattr(read, "LIVE", "docs/phases/phase-4/no_such_measurement.json")
    with pytest.raises(FileNotFoundError, match="refusing to derive"):
        read.live_spend()


def test_a_run_that_made_calls_and_recorded_no_tokens_raises(tmp_path, monkeypatch):
    """The vacuity that would NOT crash on its own.

    Calls, turns AND the output total are all non-zero here, so every
    division in `live_spend` is well defined: without the refusal this file
    returns a perfectly well-formed report saying 0 input tokens were spent
    and the input share was 0.0%. That reads as "the language layer is
    cheap" when it means "the input side was never recorded", which is a
    rule-38-class misstatement. Probed by deleting the refusal; the first
    draft of this fixture zeroed BOTH totals and only failed on a
    ZeroDivisionError, which would have passed the moment someone guarded
    the division instead of the evidence.
    """
    hollow = tmp_path / "hollow.json"
    hollow.write_text(json.dumps({
        "turns_played": 14, "token_spend": {"input_tokens": 0, "output_tokens": 439},
        "live": {"provider_calls": 23},
    }), encoding="utf-8")
    monkeypatch.setattr(read, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(read, "LIVE", "hollow.json")
    with pytest.raises(ValueError, match="no usable live spend"):
        read.live_spend()


def test_the_mocked_run_is_summed_over_its_own_games():
    mocked = read.mocked_spend()
    games = _MOCKED["token_spend"]["games"]
    assert mocked["games"] == len(games) == 3
    assert mocked["calls"] == sum(game["calls"] for game in games)
    assert mocked["input_tokens"] == sum(game["input_tokens"] for game in games)
    assert "SIMULATED" in mocked["simulated"]


def test_the_mock_is_comparable_on_calls_and_not_on_tokens():
    """The one honest bridge between the two sources, and its one limit."""
    live, mocked = read.live_spend(), read.mocked_spend()
    comparison = read.compare_call_rate(live, mocked)
    assert comparison["calls_per_turn_ratio"] == pytest.approx(
        live["calls_per_turn"] / mocked["calls_per_turn"])
    assert comparison["calls_per_turn_ratio"] == pytest.approx(1.0, abs=0.05)
    assert comparison["tokens_per_call_ratio"] > 5.0


def test_the_projection_scales_the_measured_rate_by_the_move_ceiling():
    live, config = read.live_spend(), read.budget_config()
    projection = read.project(live, config)
    per_game = live["tokens_per_turn"] * config["move_ceiling"]
    assert projection["tokens_per_full_game"] == pytest.approx(per_game)
    assert projection["games_within_budget"] == pytest.approx(
        config["token_budget_per_series"] / per_game)
    assert projection["max_games_fits_budget"] is (
        per_game * read.MAX_GAMES_PER_TEAM <= config["token_budget_per_series"])


def test_the_hint_sample_is_real_traffic_and_refuses_to_be_empty(tmp_path, monkeypatch):
    hints = prompts.tracked_hints()
    assert len(hints) > 20
    assert all(isinstance(text, str) and text.strip() for text in hints)
    monkeypatch.setattr(prompts, "REPO_ROOT", tmp_path)
    (tmp_path / "docs" / "phases" / "phase-5").mkdir(parents=True)
    with pytest.raises(ValueError, match="refusing to report a prompt size"):
        prompts.tracked_hints()


def test_the_system_prompt_dominates_each_call_and_follows_config():
    sizes = prompts.prompt_sizes(arena="New York", board_size=7, word_limit=15, max_tokens=300)
    assert sizes["decode"]["system_share_of_input_chars"] > 0.85
    assert sizes["bluff"]["system_share_of_input_chars"] > 0.85
    other = prompts.prompt_sizes(arena="", board_size=11, word_limit=15, max_tokens=300)
    assert other["decode"]["system_chars"] != sizes["decode"]["system_chars"]


def test_the_shipped_estimator_over_reserves_against_the_one_real_call():
    sizes = prompts.prompt_sizes(arena="New York", board_size=7, word_limit=15, max_tokens=300)
    calibration = prompts.calibration(sizes, read.live_spend())
    assert calibration["ratio_estimate_over_measured"] > 1.0
    assert calibration["measured_output_per_call"] < sizes["max_tokens_reserved_per_call"]
