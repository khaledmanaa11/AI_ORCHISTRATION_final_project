"""bluff.py: the structural no-raise/no-bare-except proof, and the
adversarial property test (Task 3 verify bullet 6). Split from
test_bluff.py at the 150-code-line gate -- see that module's docstring.
"""

import ast
import inspect
import random

from pursuit.services.llm.bluff import compose
from pursuit.services.llm.provider import LlmFailure, LlmFailureReason
from pursuit.services.llm.wordcount import count
from pursuit.shared.deception_types import ClaimKind, Intent
from pursuit.shared.hint_guard import assert_no_coordinates
from tests.unit.services.test_bluff import WORD_LIMIT, _context, _plan, _result, declaration


def test_compose_contains_no_raise_statement():
    """Verification item 6: compose() has no failure mode."""
    tree = ast.parse(inspect.getsource(compose))
    assert [node for node in ast.walk(tree) if isinstance(node, ast.Raise)] == []


def test_compose_contains_no_bare_except():
    tree = ast.parse(inspect.getsource(compose))
    bare = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is None
    ]
    assert bare == []


class _AdversarialProvider:
    """Returns a fresh adversarial outcome, driven by an injected rng, on
    every call -- including a second adversarial outcome on a retry."""

    def __init__(self, rng: random.Random):
        self._rng = rng
        self.calls = 0

    async def complete(self, *, system_prompt, user_prompt, schema=None):
        self.calls += 1
        outcome = _adversarial_outcome(self._rng)
        if outcome == "RAISE":
            raise RuntimeError("adversarial provider failure")
        return outcome


def _adversarial_outcome(rng: random.Random):
    roll = rng.random()
    if roll < 0.15:
        return LlmFailure(rng.choice(list(LlmFailureReason)), "mocked")
    if roll < 0.25:
        return "RAISE"
    if roll < 0.35:
        return _result("")
    if roll < 0.40:
        return _result("   \t  ")
    if roll < 0.55:
        row, col = rng.randint(0, 6), rng.randint(0, 6)
        return _result(f"I am hiding at {row},{col} right now for sure")
    if roll < 0.75:
        n = rng.randint(WORD_LIMIT + 1, WORD_LIMIT + 40)
        words = ["word", "near", "the", "docks", "and", "of", "to", "toward"]
        return _result(" ".join(rng.choice(words) for _ in range(n)))
    n = rng.randint(1, WORD_LIMIT)
    words = ["Right", "now", "I'm", "near", "the", "docks", "heading", "east"]
    return _result(" ".join(rng.choice(words) for _ in range(n)))


_ADVERSARIAL_PLANS = (
    _plan(ClaimKind.LOCATION, Intent.TRUTH),
    _plan(ClaimKind.LOCATION, Intent.LIE),
    _plan(ClaimKind.HEADING, Intent.TRUTH),
    _plan(ClaimKind.HEADING, Intent.LIE),
    declaration(ClaimKind.BARRIER),
    declaration(ClaimKind.CAPTURE),
)


def test_the_adversarial_plan_table_covers_every_claim_kind():
    """Non-vacuity guard for the property test below (05-15). The table is
    indexed modulo its OWN length, so silently losing the two declaration
    entries leaves 300 iterations that still PASS while never exercising
    either always-true kind -- the vacuous shape 05-13 and 05-14 each caught
    in their own controls. Pinned as a test, not a module-level assert: an
    import-time failure here would fail COLLECTION for the whole directory,
    which is precisely the blast radius this plan was sequenced to avoid."""
    assert len(_ADVERSARIAL_PLANS) == 6
    assert {plan.kind for plan in _ADVERSARIAL_PLANS} == set(ClaimKind)
    assert [plan.kind for plan in _ADVERSARIAL_PLANS].count(ClaimKind.BARRIER) == 1


async def test_compose_never_raises_and_always_returns_a_legal_hint():
    """Property test over hundreds of adversarial mock completions: the
    result is always non-empty, always in-limit, always coordinate-free,
    and compose() itself never raises."""
    rng = random.Random(20260809)
    for i in range(300):
        provider = _AdversarialProvider(rng)
        plan = _ADVERSARIAL_PLANS[i % len(_ADVERSARIAL_PLANS)]
        context = _context(provider, seed=i)
        result = await compose(plan, context)
        assert isinstance(result, str)
        assert result.strip() != ""
        assert count(result) <= WORD_LIMIT
        assert_no_coordinates(result)  # must not raise
