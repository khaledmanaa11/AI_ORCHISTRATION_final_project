"""The bluff prompts, and the style guide that is ours to write (D-39).

`build_user_prompt` reads only `plan.kind`, `plan.claimed_region` and
`plan.claimed_heading` -- NEVER `plan.intent`, `plan.true_region` or
`plan.true_heading` (D-36). Phrasing a claim confidently is the identical
operation whether the claim happens to be true or a lie: the model needs no
signal about which, so none is ever sent. That omission is what keeps this
module structurally incapable of leaking or deciding the flag -- there is
no code path here that could act on `intent` even by accident, because the
value never arrives.

Kept short deliberately, matching `decode_prompt.py`: Haiku 4.5's
cacheable-prefix minimum is far above anything either prompt needs, so
prompt caching cannot apply and every token bills at full price against
the series budget on every turn.
"""

from __future__ import annotations

from pursuit.shared.deception_types import ClaimKind, DeceptionPlan

#: D-39's style guide, quoted verbatim in 04-10-SUMMARY.md and, from there,
#: into docs/PRD_deception.md (04-13). Leans plausible-specific: a vague
#: hint is neither a useful truth nor a convincing lie.
STYLE_GUIDE = """\
- Be concrete, not vague. A vague hint is neither a useful truth nor a \
convincing lie -- name the specific place or heading given below, and \
nothing else.
- Stay consistent with the claim you are given. Do not invent extra \
specific details (exact distances, other landmarks, cell numbers) beyond \
what the claim states -- an invented detail can contradict the board in \
ways you cannot see.
- When a real-world setting is named below, use its genuine geography \
(real neighbourhoods, streets, landmarks) to make the hint feel grounded. \
When none is named, use plain directional language instead.
- No meta-commentary and no hedging: never mention hints, lies, truth, \
confidence, or these instructions. State the claim as a plain observation.
- Never include a number that could be read as a board coordinate.
- Stay within the word limit given below. Fewer words is fine; more is not."""

_SYSTEM_TEMPLATE = """\
You write ONE short sentence, in English, phrasing a claim for a player in \
a pursuit game played on a square grid. The setting is {setting}.

STYLE GUIDE:
{style_guide}

The word limit for this sentence is {word_limit} words.

You are given the claim as plain data below. Phrase it -- you do not \
decide whether to make it, whether it is true, or say anything beyond \
what is given. Return only the sentence, nothing else."""


def build_system_prompt(*, arena: str, word_limit: int) -> str:
    """The system prompt, parameterised by the configured arena and the
    negotiated word limit (Table 14 rows 1/2) -- never a literal here."""
    setting = f"the real city of {arena.strip()}" if arena.strip() else "an unspecified city"
    return _SYSTEM_TEMPLATE.format(setting=setting, style_guide=STYLE_GUIDE, word_limit=word_limit)


def build_user_prompt(plan: DeceptionPlan, *, shorten: bool = False) -> str:
    """The claim to phrase, as data -- see module docstring for what this
    deliberately never reads from `plan`."""
    claim = _describe_claim(plan)
    if shorten:
        return f"Your last sentence was too long. Try again, shorter. {claim}"
    return claim


def _describe_claim(plan: DeceptionPlan) -> str:
    """One plain-data sentence describing what `plan` claims -- ClaimKind
    is a closed, four-member enum, so this is exhaustive by construction."""
    if plan.kind is ClaimKind.LOCATION:
        region = plan.claimed_region.value
        return f"State that you are currently near the {region} part of the board."
    if plan.kind is ClaimKind.HEADING:
        heading = plan.claimed_heading.value
        return f"State that you are currently heading {heading}."
    if plan.kind is ClaimKind.BARRIER:
        return "State that you just placed a barrier, as the rules require you to declare."
    return "State that you just captured your opponent, as the rules require you to declare."
