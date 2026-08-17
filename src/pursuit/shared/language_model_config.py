"""Validation for language.json's `model` group (D-32, D-52, Table 14, 04-06/04-10).

Split out of language_config.py at the 150-code-line gate (Segal Table 5):
language_config.py already owns the gatekeeper/budget groups and adding
model-group validation inline pushed it over the limit. This module owns
model's key names and validation only; load_language_config() calls
validate_model_group() and otherwise treats `model` as an opaque dict
(LanguageParams.model's type is unchanged).

`hint_word_limit` (04-10, Table 14 row 2) lives HERE rather than in a new
`deception.json` field, per carry-over A in RESUME.md: the emission side
(`services/llm/bluff.py`/`bluff_prompt.py`) and the future decode side
(`DecodeContext.word_limit`, 04-07/04-12) must read the SAME negotiated
number, and both are properties of the LLM channel (`language.json`'s
`model` group already carries the sibling `game_arena`, Table 14 row 1) --
not of the deception POLICY (`deception.json`'s lie-probability/herding
knobs, which govern WHAT is claimed, never how many words phrase it). This
is a deliberate deviation from 04-10-PLAN.md's own `files_modified` list,
recorded in 04-10-SUMMARY.md.
"""

from enum import Enum

from pursuit.shared.loader_helpers import require_int, require_str


class ModelKey(str, Enum):
    """Field names inside language.json's `model` group.

    Structural only -- no numeric literal lives on this enum (D-05
    discipline), matching LanguageKey's own convention.
    """

    PROVIDER = "provider"
    MODEL_ID = "model_id"
    MAX_TOKENS = "max_tokens"
    TIMEOUT_SECONDS = "timeout_seconds"
    EVERY_N_STEPS = "every_n_steps"
    GAME_ARENA = "game_arena"
    HINT_WORD_LIMIT = "hint_word_limit"


def validate_model_group(model: dict, *, source: str) -> None:
    """Validate model.{provider,model_id,max_tokens,timeout_seconds,
    every_n_steps,game_arena}; raises KeyError/TypeError/ValueError naming
    the offending key, exactly like language_config.py's own checks.

    Never touches os.environ and never constructs a client -- a missing
    ANTHROPIC_API_KEY is a call-time NO_KEY LlmFailure (D-33), never a
    load-time error, so a keyless machine can still load config and start
    a game.
    """
    # Deferred import, and it stays deferred. It was written because
    # services.llm.gatekeeper imported language_config.py at ITS top level,
    # and language_config.py imports this module at ITS top level, so
    # importing services.llm back here would cycle. 07-01 retyped
    # `Gatekeeper.__init__` onto shared/gatekeeper_params.py, so that ONE arc
    # of the cycle is gone as of 2026-08-17 -- but shared/ importing the whole
    # services.llm package at module scope would still invert this project's
    # dependency direction and re-arm the cycle the moment any services.llm
    # module reaches back into shared/language_config.py. Safe here because by
    # the time this function runs, this module's top level has finished.
    from pursuit.services.llm import get_provider_class

    provider_name = require_str(model, ModelKey.PROVIDER.value, source=source)
    try:
        get_provider_class(provider_name)
    except ValueError as exc:
        raise ValueError(
            f"{source} field '{ModelKey.PROVIDER.value}' names an unregistered "
            f"provider: {exc}"
        ) from exc

    model_id = require_str(model, ModelKey.MODEL_ID.value, source=source)
    if not model_id:
        raise ValueError(f"{source} field '{ModelKey.MODEL_ID.value}' must be non-empty")

    every_n_steps = require_int(model, ModelKey.EVERY_N_STEPS.value, source=source)
    if every_n_steps < 1:
        raise ValueError(
            f"{source} field '{ModelKey.EVERY_N_STEPS.value}' must be >= 1 -- "
            f"section 10.4 requires a hint every turn, got {every_n_steps}"
        )

    max_tokens = require_int(model, ModelKey.MAX_TOKENS.value, source=source)
    if max_tokens < 1:
        raise ValueError(f"{source} field '{ModelKey.MAX_TOKENS.value}' must be >= 1")

    timeout_seconds = require_int(model, ModelKey.TIMEOUT_SECONDS.value, source=source)
    if timeout_seconds < 1:
        raise ValueError(f"{source} field '{ModelKey.TIMEOUT_SECONDS.value}' must be >= 1")

    require_str(model, ModelKey.GAME_ARENA.value, source=source)  # "" == generic cues

    hint_word_limit = require_int(model, ModelKey.HINT_WORD_LIMIT.value, source=source)
    if hint_word_limit < 1:
        raise ValueError(
            f"{source} field '{ModelKey.HINT_WORD_LIMIT.value}' must be >= 1 -- "
            f"docs/PARAMETERS.md Table 14 row 2 (negotiable), got {hint_word_limit}"
        )
