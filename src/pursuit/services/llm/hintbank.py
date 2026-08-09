"""The template bank: `bluff.py`'s total, zero-token fallback (D-33, D-39,
D-45, LANG-01).

`HintBank.select()` never fails, never calls the network, and is validated
against the REAL shipped word limit the moment this module is imported --
see `_shipped_word_limit()` below for why that reads `language.json`
directly rather than through `load_language_config()`/`validate_model_group()`
(that path re-enters `pursuit.services.llm`'s own provider registry, which
would be a genuine circular import if triggered from THIS package's own
import time, the exact class of cycle 04-06's `language_model_config.py`
deviation already worked around for the opposite direction).

Selection uses an injected seeded `random.Random` (same discipline as D-43
and 04-08's deception policies), so a game replays byte-identically. Each
`(ClaimKind, Intent, arena-flavour)` key cycles through a FULL SHUFFLED
PERMUTATION of its own phrasings before any repeat -- the window IS the
bucket size, a structural guarantee rather than a second configured number.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from pursuit.services.llm.hintbank_templates import (
    ARENA_HEADING_PLACE,
    ARENA_REGION_PLACE,
    BANK,
    EVENT_ARENA_CLAUSE,
    EVENT_GENERIC_CLAUSE,
    GENERIC_HEADING_PLACE,
    GENERIC_REGION_PLACE,
)
from pursuit.services.llm.wordcount import count as _count
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.hint_guard import assert_no_coordinates
from pursuit.shared.language_model_config import ModelKey
from pursuit.shared.loader_helpers import require_int

_LANGUAGE_CONFIG_PATH = (
    Path(__file__).resolve().parents[4] / "config" / "police" / "language.json"
)


class HintBank:
    """A total, deterministic phrase bank -- `bluff.py`'s only fallback.

    One instance per game, held for its duration by whoever builds
    `BluffContext` (same ownership pattern as 04-09's `Reliability`): a
    fresh rotation state each game, never persisted, never shared between
    the cop and thief processes (CLAUDE.md rule 2).
    """

    def __init__(self, *, rng: random.Random) -> None:
        self._rng = rng
        self._queues: dict[tuple[ClaimKind, Intent, bool], list[str]] = {}
        self._last: dict[tuple[ClaimKind, Intent, bool], str] = {}

    def select(self, plan: DeceptionPlan, *, arena: str) -> str:
        """One phrasing for `plan`, filled with the real or generic slot
        value depending on whether `arena` is configured (Sec6.5.1).

        `BANK[(plan.kind, plan.intent)]` cannot KeyError for a real
        `DeceptionPlan`: its own `__post_init__` already refuses every
        (kind, intent) combination `BANK` does not cover (LIE on an
        always-true kind), so every reachable plan hits a real entry.
        """
        arena_flavour = bool(arena.strip())
        key = (plan.kind, plan.intent, arena_flavour)
        templates = BANK[(plan.kind, plan.intent)]
        queue = self._queues.get(key)
        if not queue:
            queue = self._fresh_cycle(templates, previous=self._last.get(key))
            self._queues[key] = queue
        template = queue.pop()
        self._last[key] = template
        return template.format(slot=_slot_for(plan, arena_flavour=arena_flavour))

    def _fresh_cycle(self, templates: tuple[str, ...], *, previous: str | None) -> list[str]:
        """A freshly shuffled full cycle of `templates`, popped from the
        end. Swaps away an immediate repeat across the cycle boundary
        (this cycle's first pop landing on the previous cycle's last)."""
        order = list(templates)
        self._rng.shuffle(order)
        if previous is not None and len(order) > 1 and order[-1] == previous:
            order[-1], order[-2] = order[-2], order[-1]
        return order


def _slot_for(plan: DeceptionPlan, *, arena_flavour: bool) -> str:
    """The `{slot}` filler for `plan`, real-place or generic."""
    if plan.kind is ClaimKind.LOCATION:
        table = ARENA_REGION_PLACE if arena_flavour else GENERIC_REGION_PLACE
        return table[plan.claimed_region]
    if plan.kind is ClaimKind.HEADING:
        table = ARENA_HEADING_PLACE if arena_flavour else GENERIC_HEADING_PLACE
        return table[plan.claimed_heading]
    return EVENT_ARENA_CLAUSE if arena_flavour else EVENT_GENERIC_CLAUSE


def _all_slot_fillers(kind: ClaimKind) -> tuple[str, ...]:
    """Every filler `kind` can ever be given, both flavours -- a superset
    of "the longest possible slot filler", used to validate the bank."""
    if kind is ClaimKind.LOCATION:
        return tuple(ARENA_REGION_PLACE.values()) + tuple(GENERIC_REGION_PLACE.values())
    if kind is ClaimKind.HEADING:
        return tuple(ARENA_HEADING_PLACE.values()) + tuple(GENERIC_HEADING_PLACE.values())
    return (EVENT_ARENA_CLAUSE, EVENT_GENERIC_CLAUSE)


def validate_bank(word_limit: int) -> None:
    """Every phrasing in `BANK`, filled with every filler it could ever
    receive, must be within `word_limit` and coordinate-free.

    Raises
    ------
    ValueError
        Naming the offending template and filler -- a template that can
        overflow once its slot is substituted is a bug that must be caught
        here, not discovered mid-game (Task 2 must_haves).
    """
    for (kind, intent), templates in BANK.items():
        for template in templates:
            for filler in _all_slot_fillers(kind):
                text = template.format(slot=filler)
                if _count(text) > word_limit:
                    raise ValueError(
                        f"hintbank: {kind.value}/{intent.value} template {template!r} "
                        f"overflows the configured word limit ({word_limit}) with "
                        f"filler {filler!r}: {text!r}"
                    )
                assert_no_coordinates(text)


def _shipped_word_limit() -> int:
    """The real, currently-shipped `language.json` `model.hint_word_limit`.

    Read directly with `json.load` + `loader_helpers.require_int`, NOT
    through `load_language_config()`/`validate_model_group()` -- that path
    calls back into `pursuit.services.llm.get_provider_class()`, and this
    module is itself part of `pursuit.services.llm`. Triggering that call
    from this module's own import time would risk exactly the circular
    import 04-06 already deferred an import to avoid, in the opposite
    direction. Both role files are byte-identical and asserted so by a
    test, so reading the police file is representative of either.
    """
    with _LANGUAGE_CONFIG_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return require_int(data["model"], ModelKey.HINT_WORD_LIMIT.value, source="language.json")


validate_bank(_shipped_word_limit())
