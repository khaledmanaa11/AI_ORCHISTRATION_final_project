"""wordcount.py: one tokenisation rule, used everywhere (D-45, D-44).

No network I/O; nothing here calls a provider.
"""

import pytest

from pursuit.services.llm.wordcount import count, truncate

LIMIT = 15  # PARAMETERS.md Table 14 row 2, passed in as the caller would


def test_empty_string_counts_zero():
    assert count("") == 0


def test_whitespace_only_counts_zero():
    assert count("   \n\t  ") == 0


def test_a_plain_sentence_counts_by_whitespace():
    assert count("I am near the docks") == 5


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("well-known-place", 1),
        ("don't stop", 2),
        ("north, near the docks.", 4),
        ("(3, 4) is not far", 5),
    ],
)
def test_hyphens_contractions_and_punctuation_do_not_change_the_count(text, expected):
    """Each is a place two implementations of "obvious" disagree --
    str.split() never looks inside a token, so all three count as ONE word."""
    assert count(text) == expected


def test_empty_string_truncates_to_empty_without_raising():
    assert truncate("", LIMIT) == ""


@pytest.mark.parametrize("n", [LIMIT - 1, LIMIT])
def test_at_or_under_the_limit_is_returned_unchanged(n):
    text = " ".join(["word"] * n)
    assert truncate(text, LIMIT) == text


def test_one_over_the_limit_is_cut_and_punctuated():
    text = " ".join(["word"] * (LIMIT + 1))
    result = truncate(text, LIMIT)
    assert count(result) <= LIMIT
    assert result.endswith(".")


@pytest.mark.parametrize("n", [LIMIT - 1, LIMIT, LIMIT + 1, LIMIT + 20, 1])
def test_count_of_truncate_never_exceeds_the_limit(n):
    text = " ".join([f"word{i}" for i in range(n + 5)])
    assert count(truncate(text, LIMIT)) <= LIMIT


@pytest.mark.parametrize("stopword", ["and", "of", "near", "to", "with", "toward"])
def test_truncation_never_ends_on_a_conjunction_or_preposition(stopword):
    """A sentence whose (limit)-th word, once cut, would land ON a
    conjunction/preposition -- it must be dropped instead."""
    text = " ".join(["word"] * (LIMIT - 1) + [stopword, "extra"])
    result = truncate(text, LIMIT)
    last_word = result.rstrip(".").split()[-1].lower()
    assert last_word != stopword


def test_truncation_keeps_at_least_one_word_even_when_every_word_is_a_stopword():
    text = " ".join(["of"] * (LIMIT + 1))
    result = truncate(text, LIMIT)
    assert result != ""
    assert count(result) >= 1


def test_truncated_text_strips_leftover_punctuation_before_the_closing_period():
    text = " ".join(["word"] * LIMIT) + ", extra words that push it over"
    result = truncate(text, LIMIT)
    assert result.count(".") == 1
    assert not result.endswith(",.")


def test_truncate_is_idempotent_on_its_own_output():
    text = " ".join(["word"] * (LIMIT + 5))
    once = truncate(text, LIMIT)
    assert truncate(once, LIMIT) == once
