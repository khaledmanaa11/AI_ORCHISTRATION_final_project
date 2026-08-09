"""LLM services package -- the gatekeeper, rate limiting, budget and the
provider layer (D-34, D-52).

Every external call in the project passes through ``Gatekeeper.submit()``
(QUAL-03). This is the package's public surface -- import from here, not
from the sibling modules directly, so 04-07/04-10 and Phase 7's Gmail
integration code against one stable import path.

Importing this package also runs ``template_provider.py``'s and
``anthropic_provider.py``'s ``register_provider()`` calls, so the registry
(``get_provider_class()``) is always fully populated by the time any
caller -- including ``shared/language_config.py``'s load-time validation,
via a deferred import that avoids a services.llm <-> shared cycle -- asks
for it.

``hintbank``'s own module-level ``validate_bank()`` call (04-10) also runs
here, transitively, the moment this package is imported: importing it
proves the REAL shipped ``language.json`` word limit validates every
template bank phrasing, not a mirrored constant (see ``hintbank.py``'s
own docstring for why it reads that file directly instead of through
``shared/language_config.py``).
"""

from pursuit.services.llm.anthropic_provider import AnthropicProvider
from pursuit.services.llm.bluff import BluffContext, compose
from pursuit.services.llm.bucket import TokenBucket
from pursuit.services.llm.budget import DegradeLevel, TokenBudget
from pursuit.services.llm.decode import DecodeContext, decode_hint
from pursuit.services.llm.decode_schema import DECODE_SCHEMA
from pursuit.services.llm.gatekeeper import CallResult, Gatekeeper, GatekeeperOverflow
from pursuit.services.llm.hintbank import HintBank, validate_bank
from pursuit.services.llm.provider import (
    LlmFailure,
    LlmFailureReason,
    LlmResult,
    Provider,
    get_provider_class,
)
from pursuit.services.llm.template_provider import TemplateProvider
from pursuit.services.llm.wordcount import count as count_words
from pursuit.services.llm.wordcount import truncate as truncate_hint

__all__ = (
    "DECODE_SCHEMA",
    "AnthropicProvider",
    "BluffContext",
    "CallResult",
    "DecodeContext",
    "DegradeLevel",
    "Gatekeeper",
    "GatekeeperOverflow",
    "HintBank",
    "LlmFailure",
    "LlmFailureReason",
    "LlmResult",
    "Provider",
    "TemplateProvider",
    "TokenBucket",
    "TokenBudget",
    "compose",
    "count_words",
    "decode_hint",
    "get_provider_class",
    "truncate_hint",
    "validate_bank",
)
