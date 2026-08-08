"""Zero-token, zero-network provider (D-52's book default; D-33's floor).

The actual phrase bank belongs to 04-10's hintbank.py -- this module only
selects one phrase from an injected sequence, so it never depends on what
the phrases say. Always available: no key, no client, no network, ever.
"""

import random
from collections.abc import Sequence

from pursuit.services.llm.provider import LlmResult, register_provider


class TemplateProvider:
    """Selects one phrase from an injected, non-empty sequence per call.

    rng is an injected seam (default a fresh random.Random()) so a test can
    supply a seeded one and assert a specific choice -- same pattern as the
    clock/sleep seams in bucket.py/gatekeeper.py.
    """

    def __init__(self, *, phrases: Sequence[str], rng: random.Random | None = None) -> None:
        if not phrases:
            raise ValueError("TemplateProvider requires at least one phrase")
        self._phrases = tuple(phrases)
        self._rng = rng if rng is not None else random.Random()

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict | None = None,
    ) -> LlmResult:
        """Selection only -- the prompts and schema are never read."""
        return LlmResult(
            text=self._rng.choice(self._phrases),
            parsed=None,
            input_tokens=0,
            output_tokens=0,
            model=None,
        )


register_provider("template", TemplateProvider)
