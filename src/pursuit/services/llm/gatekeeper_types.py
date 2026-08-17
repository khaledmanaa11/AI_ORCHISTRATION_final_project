"""``Gatekeeper``'s two caller-facing contract types, split out of
``gatekeeper.py`` at the 150-code-line gate (Segal §19.1 Table 5 --
CLAUDE.md: "split files, never compress code to fit").

Measured with the gate's own awk: adding D-68's optional budget and D-69's
``bucket_ready`` seam to ``gatekeeper.py`` took it to 153/150. Moving the two
types a caller imports -- rather than the machinery only ``Gatekeeper``
itself runs -- keeps the split on a meaning boundary instead of an arbitrary
one, and is the same precedent as
``shared/language_config.py`` -> ``shared/language_model_config.py`` (04-06).

Nothing about the public import path changes: ``gatekeeper.py`` imports both
names and uses both, so
``from pursuit.services.llm.gatekeeper import CallResult, GatekeeperOverflow``
still resolves, and the package surface in ``services/llm/__init__.py`` is
untouched.
"""

from dataclasses import dataclass


class GatekeeperOverflow(Exception):  # noqa: N818 -- name fixed by 04-07's must_haves contract
    """The FIFO queue is already at ``queue_depth`` (Table 19 row 5, QUAL-05).

    Callers MUST catch this and apply the deterministic fallback (D-33) --
    it is not a crash and must never propagate unhandled into the turn loop.
    Phase 7's reporting chain reuses this same shape for every refusal it
    raises in front of the gatekeeper (D-69, SEGAL §4: "On overflow: FIFO
    queue, not rejection and not a crash").
    """


@dataclass(frozen=True)
class CallResult:
    """What every ``fn`` passed to ``Gatekeeper.submit()`` must return.

    ``value`` is opaque to the gatekeeper -- an LLM provider's response, a
    Gmail send receipt, anything (D-34). ``input_tokens``/``output_tokens`` are
    the observed usage settled against the budget; a call with no concept
    of tokens (Phase 7 Gmail) passes 0 for both -- required, not defaulted,
    so every ``fn`` author states its usage explicitly (QUAL-11).
    """

    value: object
    input_tokens: int
    output_tokens: int
