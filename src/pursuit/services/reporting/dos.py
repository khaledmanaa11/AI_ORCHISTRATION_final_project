"""The DOS detector -- stage 3 of the book's Figure-13 chain (rule 29, D-69).

OQ-2, RESOLVED STRUCTURALLY AND CARRIED VERBATIM (07-PLAN-OUTLINE.md §5):
"the detector latches when the token bucket has been continuously empty across
`retries_before_failure` + 1 attempts. Rule 29 is satisfied, and nothing is
invented. Prefer this over a labelled default whenever a structural definition
exists -- a number nobody can source is a number nobody can defend."

Rule 29 mandates a runaway-loop detector and NO document gives it a trip
threshold or a lock duration. Rather than label an invented default, the trip
is DEFINED by a value that already exists and is already floor-checked:
`retries_before_failure`, docs/PARAMETERS.md Table 19 row 4 (minimum 3), read
from reporting.json. `observe()` latches on the observation AFTER
`retries_before_failure` consecutive empty ones -- i.e. across
`retries_before_failure + 1` attempts -- expressed as a strict `>` comparison
against the injected value, so this module holds no threshold of its own.

WHAT COUNTS AS A NUMBER HERE. The only integer literals in this module are a
reset to zero and an increment by one; neither is a parameter, a threshold or
a bound, and `tests/unit/test_reporting_dos.py` asserts structurally that no
numeric literal in this file is ever used as a comparison operand.

LATCHING MEANS LATCHING. Rule 29's sanction is an interface lock, so there is
no `unlock()` and no timeout: once latched, this instance stays latched for
the life of the process. A caller that wants to send again restarts. Nothing
here raises -- the chain turns `locked` into a caller-handled refusal
(rules 28-29).

THE OBSERVATION SEAM. `Gatekeeper._bucket` is private and `_call_with_retry`
is its only other reader, so this detector -- which sits OUTSIDE `submit()`
(D-69) -- observes through `Gatekeeper.bucket_ready`, the read-only property
07-01 added for exactly this. It never touches `_bucket`, and reading the seam
cannot consume a token.
"""


class DosDetector:
    """A latching lock on a runaway outgoing-send loop (rule 29).

    `retries_before_failure` is keyword-only and REQUIRED (QUAL-11) -- it
    comes from `ReportingParams`, already floor-checked against Table 19 row
    4's minimum. One instance per process, never shared between the cop and
    thief (CLAUDE.md rule 2).
    """

    def __init__(self, *, retries_before_failure: int) -> None:
        self._retries_before_failure = retries_before_failure
        self._consecutive_empty = 0
        self._locked = False

    def observe(self, bucket_ready: bool) -> None:
        """Record one attempt's bucket readiness, read off the gatekeeper seam.

        A ready bucket clears the run -- a burst that the rate limit absorbs is
        not an attack. An empty one extends it, and the run latches once it is
        longer than `retries_before_failure`, which is the same "one full retry
        ladder produced nothing" boundary `Gatekeeper._call_with_retry` uses.
        """
        if self._locked:
            return
        if bucket_ready:
            self._consecutive_empty = 0
            return
        self._consecutive_empty += 1
        if self._consecutive_empty > self._retries_before_failure:
            self._locked = True

    @property
    def locked(self) -> bool:
        """True once the interface has latched. Never returns to False."""
        return self._locked

    @property
    def consecutive_empty_observations(self) -> int:
        """The current run length -- exposed so a caller can log how close to
        the latch a legitimate burst came, without reaching into a private."""
        return self._consecutive_empty
