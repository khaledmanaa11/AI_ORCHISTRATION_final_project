"""DosDetector -- OQ-2's structural latch (Figure 13 stage 3, rule 29).

The threshold under test is not a number this module owns: it is
`retries_before_failure`, docs/PARAMETERS.md Table 19 row 4, injected. So the
tests are parametrized over several values of it, and the boundary is asserted
on BOTH sides -- one observation short of the latch must NOT lock, or the
"latches" test would pass against a detector that locks immediately.
"""

import ast
from pathlib import Path

import pytest

from pursuit.services.llm import Gatekeeper
from pursuit.services.reporting import DosDetector
from tests.unit.services.test_bucket import FakeClock
from tests.unit.services.test_gatekeeper import FakeSleep
from tests.unit.test_gatekeeper_params import MailShapedParams, _ok

#: Table 19 row 4's floor is 3; a config may raise it. Both readings are
#: exercised so the latch is proven to track the INJECTED value, not a
#: constant that happens to equal it.
_RETRY_SETTINGS = (3, 5)

_DOS_MODULE = (
    Path(__file__).resolve().parents[2] / "src" / "pursuit" / "services" / "reporting" / "dos.py"
)


@pytest.mark.parametrize("retries", _RETRY_SETTINGS)
def test_one_observation_short_of_the_latch_does_not_lock(retries: int) -> None:
    """The boundary control. Without it, `test_latches...` would pass against a
    detector that latched on the very first empty observation."""
    detector = DosDetector(retries_before_failure=retries)
    for _ in range(retries):
        detector.observe(bucket_ready=False)
    assert detector.consecutive_empty_observations == retries
    assert detector.locked is False


@pytest.mark.parametrize("retries", _RETRY_SETTINGS)
def test_latches_across_retries_before_failure_plus_one_empty_attempts(retries: int) -> None:
    detector = DosDetector(retries_before_failure=retries)
    for _ in range(retries + 1):
        detector.observe(bucket_ready=False)
    assert detector.locked is True


@pytest.mark.parametrize("retries", _RETRY_SETTINGS)
def test_a_ready_bucket_clears_the_run(retries: int) -> None:
    """A burst the rate limiter absorbs is not an attack."""
    detector = DosDetector(retries_before_failure=retries)
    for _ in range(retries):
        detector.observe(bucket_ready=False)
    detector.observe(bucket_ready=True)
    assert detector.consecutive_empty_observations == 0
    for _ in range(retries):
        detector.observe(bucket_ready=False)
    assert detector.locked is False


@pytest.mark.parametrize("retries", _RETRY_SETTINGS)
def test_a_latched_lock_never_clears(retries: int) -> None:
    """Rule 29's sanction is an interface lock -- there is no unlock and no
    timeout, so a recovered bucket does not buy the loop another chance.

    The run length is asserted too, and that is not decoration. A probe that
    deleted `observe`'s early return for a latched detector left this test
    green when it only checked `locked`: the latch itself survived, but the
    EVIDENCE of the run that caused it was silently reset to zero by the first
    ready observation. Post-mortem reachability is the point of exposing the
    counter at all, so the counter is pinned here as well."""
    detector = DosDetector(retries_before_failure=retries)
    for _ in range(retries + 1):
        detector.observe(bucket_ready=False)
    for _ in range(retries * 3):
        detector.observe(bucket_ready=True)
    assert detector.locked is True
    assert detector.consecutive_empty_observations == retries + 1
    assert not hasattr(detector, "unlock")


def test_the_retry_settings_table_is_not_empty() -> None:
    """An empty parametrize list SKIPS silently. Assert the table has cases
    before trusting any of the four tests that iterate it."""
    assert len(_RETRY_SETTINGS) == 2


def test_no_numeric_literal_in_dos_py_is_ever_a_comparison_operand() -> None:
    """OQ-2: the trip is structural. The only integers in this module are a
    reset to zero and an increment by one -- never a threshold. Parsed rather
    than grepped, and asserted on the property that actually matters: no
    comparison in this file is made against a number."""
    tree = ast.parse(_DOS_MODULE.read_text(encoding="utf-8"))
    operands = [
        node.value
        for compare in ast.walk(tree)
        if isinstance(compare, ast.Compare)
        for node in [*compare.comparators, compare.left]
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float)
    ]
    assert operands == []
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
    }
    assert literals <= {0, 1}


async def test_the_detector_reads_a_real_gatekeepers_seam(retries: int = 3) -> None:
    """Production reachability, end to end: the detector is driven off
    `Gatekeeper.bucket_ready`, the seam 07-01 added -- not off a hand-written
    bool. A bucket of capacity 3 goes empty after 3 sends, and the detector
    then latches on the 4th consecutive empty observation."""
    gk = Gatekeeper(
        params=MailShapedParams(requests_per_minute=3),
        clock=FakeClock(),
        sleep=FakeSleep(),
    )
    detector = DosDetector(retries_before_failure=retries)
    for _ in range(3):
        detector.observe(gk.bucket_ready)
        await gk.submit(_ok, estimated_tokens=0)
    assert detector.locked is False
    for _ in range(retries + 1):
        assert gk.bucket_ready is False
        detector.observe(gk.bucket_ready)
    assert detector.locked is True
