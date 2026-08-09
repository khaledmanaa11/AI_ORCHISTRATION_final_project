"""One word-counting rule, used by the validator, the retry decision and the
truncator alike (D-45, D-44, LANG-01).

`count()` and `truncate()` share exactly one rule: split on whitespace, a
token is a word -- Python's own `str.split()` with no argument, which
collapses runs of whitespace and drops leading/trailing whitespace. This is
deliberately the LEAST clever rule available. An opponent scoring our hint
for rule 26 compliance counts it the obvious way -- by eye, on whitespace --
and a tokenizer that disagrees with that (splitting "well-known" into two
words, treating "don't" as two, or stripping trailing punctuation before
counting) would let our own validator and an opponent's referee-side check
silently disagree about whether a hint obeys the limit, unfalsifiable until
a game is scored. That is a protocol risk, not a feature -- D-44 restricts
outgoing hints to English specifically because whitespace-splitting an
English sentence IS the obvious count; the same rule applied to Hebrew or a
mixed-script string would not be.

Hyphenated words, contractions and trailing punctuation therefore all count
as ONE word each, by construction: `str.split()` never looks inside a
token, so "well-known-place", "don't" and "docks," are each exactly one
whitespace token, whatever punctuation or internal structure they carry.
"""

from __future__ import annotations

import string

# Short function words that would leave a truncated hint sounding cut off
# if left dangling as the LAST word -- conjunctions and simple prepositions.
# Not exhaustive by design: this is a last-resort cosmetic polish on
# machine- or template-sourced English, not a full grammar, and a dangling
# word that slips through is still a legal, in-limit hint either way.
_TRAILING_STOPWORDS = frozenset(
    {
        "and", "or", "but", "nor", "so", "yet",
        "of", "in", "on", "at", "to", "for", "with", "by", "from", "near",
        "toward", "towards", "under", "over", "around", "along", "past",
        "through", "into", "onto", "upon", "across", "behind", "beside",
        "between", "among", "within", "without", "up", "down", "off", "about",
    }
)


def count(text: str) -> int:
    """The number of whitespace-separated tokens in `text`.

    Empty or whitespace-only input counts as zero; never raises.
    """
    return len(text.split())


def truncate(text: str, limit: int) -> str:
    """`text` cut to at most `limit` words, ending like a real sentence
    rather than announcing that it was cut short.

    Already-in-limit text (including empty text) is returned unchanged --
    truncation is a last resort, not a normaliser, and `compose()` only
    ever calls this once a completion is already known to be over `limit`.
    Over the limit, this keeps the first `limit` words, drops a trailing
    conjunction or preposition (never emptying the result down to nothing),
    strips any leftover punctuation and closes with a single period.
    """
    words = text.split()
    if len(words) <= limit:
        return text

    kept = words[:limit]
    while len(kept) > 1 and _bare(kept[-1]) in _TRAILING_STOPWORDS:
        kept.pop()

    sentence = " ".join(kept).rstrip(string.punctuation + " ")
    return f"{sentence}." if sentence else ""


def _bare(word: str) -> str:
    """`word` lowercased with surrounding punctuation stripped, so a
    stopword-membership check ignores a trailing comma or period."""
    return word.strip(string.punctuation).lower()
