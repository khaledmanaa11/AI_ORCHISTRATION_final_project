"""Cumulative token budget with a graded degrade ladder (D-35).

``TokenBudget`` accumulates input/output tokens per call and reports a
``DegradeLevel``: ``FULL`` -> ``SHORT_PROMPT`` -> ``TEMPLATE_ONLY``, crossing
at the configured thresholds (``LanguageParams.short_prompt_threshold_tokens``
/ ``.template_only_threshold_tokens``, both engineering defaults -- D-18
discipline, floor-checked for strict ordering by ``shared/language_config.py``,
not by this module). ``TEMPLATE_ONLY`` is the floor: nothing here ever raises
on exhaustion, and the level never regresses within one ``TokenBudget``'s
lifetime (one instance = one series), even though ``reserve()``/``settle()``'s
optimistic accounting could otherwise make the running total dip transiently.

``reserve(estimate)`` is called before a call is admitted
(``Gatekeeper.submit``, ``gatekeeper.py``) so the degrade level reflects every
queued call immediately, not just completed ones; ``settle(...)`` reconciles
with the observed usage afterwards, topping up the running total when actual
usage exceeds the estimate but never letting it fall back below where
``reserve()`` already pushed it.

``budget_for_params`` at the foot of this module is the D-68 seam: it turns a
config params object into the ladder above, or into ``None`` for a caller that
has no concept of a token (Phase 7's mail gatekeeper). It lives here, beside
the class it constructs, rather than in ``gatekeeper.py`` -- that file is at
135 of its 150 permitted code lines and CLAUDE.md says split, never compress.
"""

from enum import Enum

from pursuit.shared.gatekeeper_params import BudgetParams


class DegradeLevel(Enum):
    """D-35's three-rung ladder, ordered low-degrade to high-degrade."""

    FULL = "full"
    SHORT_PROMPT = "short_prompt"
    TEMPLATE_ONLY = "template_only"


_LEVEL_ORDER = (DegradeLevel.FULL, DegradeLevel.SHORT_PROMPT, DegradeLevel.TEMPLATE_ONLY)


class TokenBudget:
    """Cumulative spend tracker for one token-budget series (D-35).

    ``token_budget``, ``short_prompt_threshold`` and
    ``template_only_threshold`` are keyword-only and REQUIRED -- no default
    in source (QUAL-11); callers supply ``LanguageParams``' already
    floor-checked values. A fresh instance per series only -- never a shared
    live object (CLAUDE.md rule 2: no runtime state shared between the cop
    and thief processes).
    """

    def __init__(
        self,
        *,
        token_budget: int,
        short_prompt_threshold: int,
        template_only_threshold: int,
    ) -> None:
        self._token_budget = token_budget
        self._short_prompt_threshold = short_prompt_threshold
        self._template_only_threshold = template_only_threshold
        self._calls = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._reserved = 0
        self._level = DegradeLevel.FULL

    def reserve(self, estimated_tokens: int) -> None:
        """Optimistically count ``estimated_tokens`` before the call runs."""
        self._reserved += estimated_tokens
        self._advance()

    def settle(self, *, input_tokens: int, output_tokens: int, estimated_tokens: int) -> None:
        """Reconcile one call's real usage against its own prior ``reserve()``.

        Only the excess over ``estimated_tokens`` (if any) adds to the
        running total beyond what ``reserve()`` already counted -- "a call
        that returns more tokens than estimated still lands in the running
        total."
        """
        self._reserved = max(0, self._reserved - estimated_tokens)
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._calls += 1
        self._advance()

    def _advance(self) -> None:
        """Recompute the level from the current total; ratchet forward only."""
        total = self._input_tokens + self._output_tokens + self._reserved
        if total >= self._template_only_threshold:
            computed = DegradeLevel.TEMPLATE_ONLY
        elif total >= self._short_prompt_threshold:
            computed = DegradeLevel.SHORT_PROMPT
        else:
            computed = DegradeLevel.FULL
        if _LEVEL_ORDER.index(computed) > _LEVEL_ORDER.index(self._level):
            self._level = computed

    @property
    def level(self) -> DegradeLevel:
        """Current degrade level -- never regresses within this instance's life."""
        return self._level

    def report(self) -> dict:
        """A plain, ``json.dumps``-serializable spend summary for the league email."""
        return {
            "calls": self._calls,
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "level": self._level.value,
            "budget": self._token_budget,
        }


def budget_for_params(params: object) -> "TokenBudget | None":
    """The D-35 ladder for a token-spending caller, or ``None`` for one that
    spends no tokens (D-68).

    Carrying Table 18's three budget rows IS what distinguishes the two
    callers: ``LanguageParams`` has them and gets a real ``TokenBudget`` with
    exactly the thresholds it always got; ``ReportingParams`` has none of them
    and gets ``None``, because a Gmail send has no token concept
    (``CallResult``'s docstring: "a call with no concept of tokens (Phase 7
    Gmail) passes 0 for both"). No caller has to pass a flag, so no caller can
    pass the wrong one.
    """
    if not isinstance(params, BudgetParams):
        return None
    return TokenBudget(
        token_budget=params.token_budget_per_series,
        short_prompt_threshold=params.short_prompt_threshold_tokens,
        template_only_threshold=params.template_only_threshold_tokens,
    )
