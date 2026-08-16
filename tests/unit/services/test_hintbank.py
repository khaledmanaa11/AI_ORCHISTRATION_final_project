"""hintbank.py: the zero-token fallback bank, selection and validation
(D-33, D-39, D-45, LANG-01). No network I/O anywhere in this file.
"""

import json
import pathlib
import random

import pytest

from pursuit.services.llm import hintbank
from pursuit.services.llm.hintbank import HintBank, validate_bank
from pursuit.shared.deception_types import ALWAYS_TRUE_KINDS, ClaimKind, DeceptionPlan, Intent
from pursuit.shared.directions import DirectionWord
from pursuit.shared.inference import Region
from tests.unit.services.test_bluff import declaration

_CONFIG = pathlib.Path(__file__).parents[3] / "config"


def _location(intent: Intent) -> DeceptionPlan:
    return DeceptionPlan(
        intent=intent,
        kind=ClaimKind.LOCATION,
        claimed_region=Region.NORTH,
        true_region=Region.SOUTH if intent is Intent.LIE else Region.NORTH,
    )


def _heading(intent: Intent) -> DeceptionPlan:
    return DeceptionPlan(
        intent=intent,
        kind=ClaimKind.HEADING,
        claimed_heading=DirectionWord.EAST,
        true_heading=DirectionWord.WEST if intent is Intent.LIE else DirectionWord.EAST,
    )


def test_the_shipped_word_limit_validates_every_phrasing():
    """The REAL config/police/language.json number, run through validate_bank
    directly -- this module's own import already ran this exact check
    (see hintbank.py's bottom-of-file self-call); this test makes the
    guarantee explicit and independently re-derives the number rather than
    trusting the module's own cached read."""
    raw = json.loads((_CONFIG / "police" / "language.json").read_text(encoding="utf-8"))
    validate_bank(raw["model"]["hint_word_limit"])  # must not raise


def test_a_too_small_limit_is_caught_by_validate_bank():
    """Proves the guard actually catches an overflow, not just that it
    passes on the real (generously large) shipped number."""
    with pytest.raises(ValueError, match="overflows"):
        validate_bank(1)


@pytest.mark.parametrize("plan_fn", [lambda: _location(Intent.TRUTH), lambda: _location(Intent.LIE)])
def test_select_returns_a_phrasing_containing_the_claimed_region(plan_fn):
    plan = plan_fn()
    bank = HintBank(rng=random.Random(0))
    result = bank.select(plan, arena="New York")
    assert "Central Park" in result  # ARENA_REGION_PLACE[Region.NORTH]


def test_select_uses_the_generic_filler_when_arena_is_empty():
    plan = _location(Intent.TRUTH)
    bank = HintBank(rng=random.Random(0))
    result = bank.select(plan, arena="")
    assert "the north edge" in result
    assert "Central Park" not in result


def test_select_uses_the_generic_filler_when_arena_is_whitespace_only():
    plan = _location(Intent.TRUTH)
    bank = HintBank(rng=random.Random(0))
    result = bank.select(plan, arena="   ")
    assert "Central Park" not in result


def test_select_phrases_a_heading_claim():
    plan = _heading(Intent.LIE)
    bank = HintBank(rng=random.Random(0))
    result = bank.select(plan, arena="")
    assert "moving east" in result


def test_select_phrases_barrier_and_capture_declarations():
    bank = HintBank(rng=random.Random(0))
    barrier = bank.select(declaration(ClaimKind.BARRIER), arena="New York")
    capture = bank.select(declaration(ClaimKind.CAPTURE), arena="New York")
    assert "barrier" in barrier.lower()
    assert "capture" in capture.lower() or "caught" in capture.lower()


def test_a_fixed_seed_reproduces_the_same_sequence():
    plan = _location(Intent.TRUTH)
    first_bank = HintBank(rng=random.Random(7))
    first = [first_bank.select(plan, arena="") for _ in range(4)]
    second_bank = HintBank(rng=random.Random(7))
    second = [second_bank.select(plan, arena="") for _ in range(4)]
    assert first == second


def test_a_different_seed_can_diverge():
    plan = _location(Intent.TRUTH)
    bank_a = HintBank(rng=random.Random(1))
    bank_b = HintBank(rng=random.Random(2))
    a = [bank_a.select(plan, arena="") for _ in range(4)]
    b = [bank_b.select(plan, arena="") for _ in range(4)]
    assert a != b


def test_no_phrasing_repeats_within_one_full_cycle():
    """The window IS the bucket size: every phrasing is used exactly once
    before any repeat, for LIMIT_CYCLES full cycles in a row."""
    plan = _location(Intent.TRUTH)
    bank = HintBank(rng=random.Random(3))
    bucket_size = len(hintbank.BANK[(ClaimKind.LOCATION, Intent.TRUTH)])
    for _ in range(5):  # five full cycles
        cycle = [bank.select(plan, arena="") for _ in range(bucket_size)]
        assert len(set(cycle)) == bucket_size


def test_consecutive_cycles_never_repeat_across_the_boundary():
    plan = _location(Intent.TRUTH)
    bank = HintBank(rng=random.Random(11))
    bucket_size = len(hintbank.BANK[(ClaimKind.LOCATION, Intent.TRUTH)])
    seen = [bank.select(plan, arena="") for _ in range(bucket_size * 6)]
    for i in range(len(seen) - 1):
        assert seen[i] != seen[i + 1]


def test_arena_and_generic_selections_track_independently():
    """Switching arena flavour must not perturb the OTHER flavour's own
    rotation state: interleaving a generic pick still leaves the arena
    queue's own no-repeat-within-a-cycle guarantee intact."""
    plan = _location(Intent.TRUTH)
    bank = HintBank(rng=random.Random(5))
    arena_first = bank.select(plan, arena="New York")
    bank.select(plan, arena="")
    arena_second = bank.select(plan, arena="New York")
    assert arena_first != arena_second
    assert "Central Park" in arena_first
    assert "Central Park" in arena_second


@pytest.mark.parametrize(
    ("kind", "intent"),
    [(kind, intent) for kind in ClaimKind for intent in Intent if not (kind in ALWAYS_TRUE_KINDS and intent is Intent.LIE)],
)
def test_every_legal_kind_intent_pair_selects_without_error(kind, intent):
    """No KeyError for any DeceptionPlan the constructor allows to exist."""
    bank = HintBank(rng=random.Random(0))
    if kind is ClaimKind.LOCATION:
        plan = _location(intent)
    elif kind is ClaimKind.HEADING:
        plan = _heading(intent)
    else:
        plan = declaration(kind)
    result = bank.select(plan, arena="New York")
    assert isinstance(result, str)
    assert result.strip()
