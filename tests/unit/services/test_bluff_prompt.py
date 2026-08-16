"""bluff_prompt.py: D-39's style guide, and the D-36 fence around `intent`.

No network I/O; these are pure string builders.
"""

from pathlib import Path

import pytest

from pursuit.services.llm.bluff_prompt import (
    STYLE_GUIDE,
    build_system_prompt,
    build_user_prompt,
)
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region
from tests.unit.services.test_bluff import declaration


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


def test_the_system_prompt_pins_the_first_person():
    """05-UAT G5: machine A's turn-4 hint drifted to "The player is
    currently positioned..." -- a hint the player did not speak."""
    lowered = build_system_prompt(arena="New York", word_limit=15).lower()
    assert "first person" in lowered
    assert 'never "the player"' in lowered


def test_the_system_prompt_no_longer_asks_for_a_claim_written_for_a_player():
    """The exact wording that caused the drift: asked to write FOR someone,
    the model wrote ABOUT them."""
    assert "for a player" not in build_system_prompt(arena="New York", word_limit=15).lower()


_PRD_PATH = Path("docs/PRD_deception.md")
_STYLE_GUIDE_HEADING = "### D-39 style guide"
_FENCE = "```"


def _prd_style_guide_block() -> str:
    """The fenced block docs/PRD_deception.md Sec6 quotes from this module."""
    lines = _PRD_PATH.read_text(encoding="utf-8").splitlines()
    heading = next(i for i, line in enumerate(lines) if line.startswith(_STYLE_GUIDE_HEADING))
    opening = next(i for i, line in enumerate(lines[heading:], heading) if line.startswith(_FENCE))
    closing = next(
        i for i, line in enumerate(lines[opening + 1:], opening + 1) if line.startswith(_FENCE)
    )
    return "\n".join(lines[opening + 1:closing])


def test_the_prd_quotes_the_shipped_style_guide_verbatim():
    """The PRD says "verbatim", so this is the assertion that keeps it
    true -- the doc and the shipped string can never drift apart silently
    (CLAUDE.md: documentation is not optional)."""
    assert _prd_style_guide_block() == STYLE_GUIDE


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
    [_LOCATION, _HEADING, declaration(ClaimKind.BARRIER), declaration(ClaimKind.CAPTURE)],
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
    barrier = build_user_prompt(declaration(ClaimKind.BARRIER))
    capture = build_user_prompt(declaration(ClaimKind.CAPTURE))
    assert "barrier" in barrier.lower()
    assert "captured" in capture.lower()
