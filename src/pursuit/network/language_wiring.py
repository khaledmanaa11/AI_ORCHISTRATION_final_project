"""Build the LLM half of a process's language pipeline, once (D-34, D-35, D-52).

Deviation (Rule 3 - blocking): not in 04-12-PLAN.md's `files_modified`, but
required to keep `agent_wiring.py` under the 150-code-line gate once it grows
a fifth config file to load -- "split files, never compress" (CLAUDE.md).
Mirrors this phase's own established precedent (e.g. `handshake_wire.py` /
`handshake_evaluate.py`).

Everything here is constructed ONCE per process and held for the game's
duration -- the Gatekeeper, the Provider, the HintBank -- matching 04-09's
`Reliability` / 04-10's `HintBank` ownership precedent (CLAUDE.md rule 2:
never a live object shared between the cop and thief processes).
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

from pursuit.services.llm.bluff import BluffContext
from pursuit.services.llm.budget import DegradeLevel
from pursuit.services.llm.decode import DecodeContext
from pursuit.services.llm.gatekeeper import Gatekeeper
from pursuit.services.llm.hintbank import HintBank
from pursuit.services.llm.provider import Provider, get_provider_class
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.shared.deception_config import DeceptionParams
from pursuit.shared.language_config import LanguageParams
from pursuit.shared.language_model_config import ModelKey

#: TemplateProvider's constructor requires a non-empty phrase sequence, but
#: the content is inert in this wiring: decode_hint() short-circuits before
#: ever calling TemplateProvider.complete() (D-52), and compose() never
#: calls a TemplateProvider either (04-10 carry-over L) -- HintBank supplies
#: every template-path hint instead. This phrase exists only to satisfy the
#: constructor contract.
_INERT_TEMPLATE_PHRASES = ("no additional information.",)

#: Deterministic fallback when `belief.json`'s `belief.seed` is null -- the
#: language layer's own RNGs (deception, hint bank) still need a seed so a
#: replay reproduces byte-identically. A DIFFERENT constant from
#: `strategy/registry.py`'s `_FALLBACK_BELIEF_SEED`: this seeds a distinct
#: stream (LANG-01's rotation/lie draws, not belief sampling), not the same
#: number reused for two purposes.
_FALLBACK_LANGUAGE_SEED = 20260810

_log = logging.getLogger(__name__)


@dataclass
class LanguageRuntime:
    """Everything one turn's language half needs, built once and held for
    the game (D-34). `bluff_context.degrade_level` is the one field that
    goes stale mid-game (04-10 carry-over K) -- refresh it from
    `gatekeeper.budget.level` before every `compose_outgoing` call rather
    than reading it here."""

    decode_context: DecodeContext
    bluff_context: BluffContext
    gatekeeper: Gatekeeper
    deception_config: DeceptionParams
    deception_rng: random.Random


def _resolve_seed(seed: int | None, *, label: str) -> int:
    """`seed`, or a logged deterministic fallback -- a missing seed is
    never silently non-deterministic (rule 20's replay viewer must still
    reproduce the game)."""
    if seed is not None:
        return seed
    _log.warning(
        "%s: seed is null; deriving fallback seed %d (set an explicit seed "
        "for a league game's own replay log)", label, _FALLBACK_LANGUAGE_SEED,
    )
    return _FALLBACK_LANGUAGE_SEED


def _build_provider(model: dict, gatekeeper: Gatekeeper) -> Provider:
    """The configured `model.provider`, constructed with whatever that
    class needs -- `get_provider_class` already validated the name at
    config-load time (`shared/language_model_config.py`)."""
    provider_cls = get_provider_class(model[ModelKey.PROVIDER.value])
    if provider_cls is TemplateProvider:
        return TemplateProvider(phrases=_INERT_TEMPLATE_PHRASES)
    return provider_cls(
        gatekeeper=gatekeeper,
        model_id=model[ModelKey.MODEL_ID.value],
        max_tokens=model[ModelKey.MAX_TOKENS.value],
        timeout_seconds=model[ModelKey.TIMEOUT_SECONDS.value],
    )


def build_language_runtime(
    *,
    language: LanguageParams,
    deception: DeceptionParams,
    board_size: int,
    seed: int | None,
) -> LanguageRuntime:
    """Construct the whole language runtime for one process, one game.

    `seed` is `belief.json`'s `belief.seed` (or None) -- reused here as the
    SOURCE seed for two independent `random.Random` streams (deception,
    hint bank), each offset so neither replays the other's draws.
    """
    resolved = _resolve_seed(seed, label="language_wiring")
    gatekeeper = Gatekeeper(params=language)
    provider = _build_provider(language.model, gatekeeper)
    word_limit = language.model[ModelKey.HINT_WORD_LIMIT.value]
    arena = language.model[ModelKey.GAME_ARENA.value]

    decode_context = DecodeContext(
        provider=provider, board_size=board_size, arena=arena, word_limit=word_limit,
    )
    hint_bank = HintBank(rng=random.Random(resolved + 1))
    bluff_context = BluffContext(
        provider=provider, degrade_level=DegradeLevel.FULL, arena=arena,
        word_limit=word_limit, hint_bank=hint_bank,
    )
    return LanguageRuntime(
        decode_context=decode_context,
        bluff_context=bluff_context,
        gatekeeper=gatekeeper,
        deception_config=deception,
        deception_rng=random.Random(resolved + 2),
    )
