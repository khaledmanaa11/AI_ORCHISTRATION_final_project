"""LLM services package -- the gatekeeper, rate limiting and budget (D-34).

Every external call in the project passes through ``Gatekeeper.submit()``
(QUAL-03). This is the package's public surface -- import from here, not
from the sibling modules directly, so 04-06/04-07/04-10 and Phase 7's
Gmail integration code against one stable import path.
"""

from pursuit.services.llm.bucket import TokenBucket
from pursuit.services.llm.budget import DegradeLevel, TokenBudget
from pursuit.services.llm.gatekeeper import CallResult, Gatekeeper, GatekeeperOverflow

__all__ = (
    "CallResult",
    "DegradeLevel",
    "Gatekeeper",
    "GatekeeperOverflow",
    "TokenBucket",
    "TokenBudget",
)
