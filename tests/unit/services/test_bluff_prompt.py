"""bluff_prompt.py: D-39's style guide, and the D-36 fence around `intent`.

No network I/O; these are pure string builders.
"""

import pytest

from pursuit.services.llm.bluff_prompt import (
    STYLE_GUIDE,
    build_system_prompt,
    build_user_prompt,
)
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region
from pursuit.strategy.deception import declare_truthfully


def test_system_prompt_names_the_configured_arena():
    prompt = build_system_prompt(arena="New York", word_limit=15)
    assert "New York" in prompt


def test_system_prompt_falls_back_to_generic_language_when_arena_is_empty():
    prompt = build_system_prompt(arena="", word_limit=15)
    assert "New York" not in prompt


def test_system_prompt_falls_back_when_arena_is_whitespace_only():
    prompt = build_system_prompt(arena="   ", word_limit=15)
    assert "New York" not in prompt


def test_system_prompt_interpolates_the_configured_word_limit():
    prompt = build_system_prompt(arena="New York", word_limit=7)
    assert "7" in prompt


def test_system_prompt_contains_the_style_guide_verbatim():
    prompt = build_system_prompt(arena="New York", word_limit=15)
    assert STYLE_GUIDE in prompt


def test_style_guide_instructs_no_meta_commentary_about_honesty():
    """The guide explains WHY concreteness matters (it may say "lie" in
    that rationale) but must instruct the model never to SAY so in the
    hint itself."""
    lowered = STYLE_GUIDE.lower()
    assert "no meta-commentary" in lowered
    assert "never mention hints, lies, truth" in lowered


_LOCATION = DeceptionPlan(
    intent=Intent.LIE, kind=ClaimKind.LOCATION, claimed_region=Region.NORTH, true_region=Region.SOUTH
)
_HEADING = DeceptionPlan(
    intent=Intent.TRUTH,
    kind=ClaimKind.HEADING,
    claimed_heading=DirectionWord.EAST,
    true_heading=DirectionWord.EAST,
)


@pytest.mark.parametrize(
    "plan",
    [_LOCATION, _HEADING, declare_truthfully(ClaimKind.BARRIER), declare_truthfully(ClaimKind.CAPTURE)],
)
def test_user_prompt_never_reveals_the_intent_flag(plan):
    prompt = build_user_prompt(plan)
    assert "truth" not in prompt.lower()
    assert "lie" not in prompt.lower()


def test_user_prompt_states_the_claimed_region_not_the_true_one():
    prompt = build_user_prompt(_LOCATION)
    assert Region.NORTH.value in prompt
    assert Region.SOUTH.value not in prompt


def test_user_prompt_states_the_claimed_heading():
    prompt = build_user_prompt(_HEADING)
    assert DirectionWord.EAST.value in prompt


def test_shorten_prompt_asks_for_a_shorter_retry():
    normal = build_user_prompt(_LOCATION)
    shortened = build_user_prompt(_LOCATION, shorten=True)
    assert normal != shortened
    assert "short" in shortened.lower()


def test_barrier_and_capture_prompts_describe_the_declaration():
    barrier = build_user_prompt(declare_truthfully(ClaimKind.BARRIER))
    capture = build_user_prompt(declare_truthfully(ClaimKind.CAPTURE))
    assert "barrier" in barrier.lower()
    assert "captured" in capture.lower()
