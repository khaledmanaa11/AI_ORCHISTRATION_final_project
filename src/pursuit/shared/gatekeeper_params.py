"""The type ``Gatekeeper`` is written against, so ONE gatekeeper class can
serve both the LLM path (Phase 4) and the mail path (Phase 7) -- D-68, and
SEGAL §4's "build **one** gatekeeper satisfying both".

WHY A NEW FILE. Segal §19.1 Table 5 caps a source file at 150 CODE lines and
CLAUDE.md says "split files, never compress code to fit". Measured on
2026-08-17 with the gate's own awk (`scripts/check_line_limit.sh`):
``services/llm/gatekeeper.py`` = 135/150, ``shared/language_config.py`` =
139/150, ``network/language_wiring.py`` = 129/150. Neither of the two
plausible hosts had room for this, so it lands here rather than being
squeezed in. (07-PLAN-OUTLINE.md §5's claim that ``gatekeeper.py`` "is at 89
counted lines" was measured wrong; the numbers above are the gate's.)

WHY PROTOCOLS AND NOT A SHARED BASE DATACLASS. A base class would change
``LanguageParams``' runtime shape -- its MRO and its dataclass field order --
in the same commit that this plan must prove leaves Phase 4's LLM behaviour
byte-identical. Structural typing changes NOTHING at runtime for the shipped
LLM path: ``LanguageParams`` already has every field named here, so it
already satisfies both protocols with a zero-line diff, and the new
``ReportingParams`` satisfies ``GatekeeperParams`` alone.

NO NUMERIC LITERAL LIVES HERE. The Table-19 floors stay in
``shared/language_config.py``'s ``GATEKEEPER_MINIMA``, which
``shared/reporting_config.py`` imports rather than re-declaring (CLAUDE.md
Table 5: "extract at 2+ copies", no duplication).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class GatekeeperParams(Protocol):
    """docs/PARAMETERS.md Table 19's seven rows, as a structural contract.

    Rows 1-5 carry MINIMUM status and row 6-7 are negotiable; every loader
    that produces one of these floor-checks rows 1-5 itself. ``Gatekeeper``
    reads six of the seven -- ``watchdog_threshold_seconds`` belongs to the
    freeze watchdog, not to the gatekeeper -- but the contract carries the
    whole table so a params object can never satisfy it by accident.

    ``@runtime_checkable`` so a test can assert satisfaction directly
    (``isinstance``); it is never used to branch in production code.
    """

    requests_per_minute: int
    parallel_requests: int
    wait_after_error_seconds: int
    retries_before_failure: int
    queue_depth: int
    response_timeout_seconds: int
    watchdog_threshold_seconds: int


@runtime_checkable
class BudgetParams(Protocol):
    """Table 18 row 4's series ceiling plus D-35's two degrade thresholds.

    Separate from ``GatekeeperParams`` because this is exactly what tells the
    two callers apart (D-68): the LLM path spends tokens and carries these
    three fields, the mail path has no concept of a token and carries none of
    them. ``budget_for_params`` (``services/llm/budget.py``) reads that
    difference, which is why the mail gatekeeper gets ``budget = None``
    without any caller having to say so.
    """

    token_budget_per_series: int
    short_prompt_threshold_tokens: int
    template_only_threshold_tokens: int
