"""Lazy construction of the Anthropic SDK's async client (D-32, D-33, D-34).

build_client() reads ANTHROPIC_API_KEY from the environment ONLY -- never a
config field, never a default, never a file (CLAUDE.md rules 39-40) -- and
returns None when it is unset, so the caller can turn that into
LlmFailure(NO_KEY) without ever constructing a client. max_retries=0 is
deliberate: Gatekeeper (gatekeeper.py, D-34) already owns retry/backoff
(Table 19 rows 3-4); a second retry layer inside the SDK client would
multiply the backoff and risk the watchdog_threshold_seconds deadline.

This module is also the ONE place that names the environment variable, so
has_api_key() exists here rather than at either call site: everybody who
needs to ask "can this process actually reach the model?" -- the startup
warning (network/language_wiring.py) and the declared llm_name
(network/agent_audit_wiring.py) -- asks it here instead of restating the
name or reaching into os.environ themselves.
"""

import os

from anthropic import AsyncAnthropic

#: Public because two network-layer callers name it in operator-facing text.
#: It is the variable's NAME, never its value -- see has_api_key().
API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"


def has_api_key() -> bool:
    """Whether a usable key is present -- PRESENCE only, never the value.

    Returns a plain bool: the key itself is never returned, logged,
    formatted into a message or put into a declaration (CLAUDE.md rules
    39-40). An empty string counts as absent, exactly as build_client()
    already treats it, so both answers agree by construction.
    """
    return bool(os.environ.get(API_KEY_ENV_VAR))


def build_client(*, timeout_seconds: float) -> AsyncAnthropic | None:
    """A fresh AsyncAnthropic client, or None if no key is set.

    Called lazily by AnthropicProvider on its first use and cached there --
    never at import time, never as a module-level singleton here (NET-02
    precedent; also keeps the cop and thief processes trivially isolated,
    CLAUDE.md rule 2, since nothing here is ever a cross-process object).
    """
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        return None
    return AsyncAnthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)
