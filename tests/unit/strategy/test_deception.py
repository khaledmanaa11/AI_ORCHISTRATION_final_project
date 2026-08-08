"""strategy/deception.py: the dispatcher, and the claims that can never lie.

Rule 25 / STRAT-07 is structural here, and `test_the_planner_imports_no_model_client`
is the assertion that keeps it that way.
"""

import pathlib
import random

import pytest

from pursuit.shared.deception_config import load_deception_config
from pursuit.shared.deception_types import (
    ALWAYS_TRUE_KINDS,
    ClaimKind,
    DeceptionPlan,
    Intent,
)
from pursuit.shared.inference import Region
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.deception import ROLES, declare_truthfully, plan_deception
from pursuit.strategy.regions import region_of

_CONFIG = pathlib.Path(__file__).parents[3] / "config" / "police"


@pytest.fixture
def config():
    return load_deception_config(_CONFIG / "deception.json")


@pytest.fixture
def belief(default_params):
    return BeliefMap(board_size=default_params.board_size, role="cop")


@pytest.mark.parametrize("role", ROLES)
def test_every_dispatch_path_returns_a_plan(role, start_state, default_params, config, belief):
    """LANG-01: a turn always carries a hint, so a policy that cannot think of
    a good lie returns a truthful claim -- never None."""
    plan = plan_deception(role, start_state, default_params, belief, random.Random(0), config)
    assert isinstance(plan, DeceptionPlan)
    assert plan.kind is ClaimKind.LOCATION
    assert plan.claimed_region in set(Region)


@pytest.mark.parametrize("role", ROLES)
def test_the_plan_records_the_true_sector_for_its_own_seat(
    role, start_state, default_params, config, belief
):
    plan = plan_deception(role, start_state, default_params, belief, random.Random(0), config)
    own_cell = start_state.cop if role == "cop" else start_state.thief
    assert plan.true_region is region_of(own_cell, default_params.board_size)


@pytest.mark.parametrize("role", ["referee", "COP", "", None, "thief "])
def test_an_unknown_role_is_rejected(role, start_state, default_params, config, belief):
    with pytest.raises(ValueError, match="role must be one of"):
        plan_deception(role, start_state, default_params, belief, random.Random(0), config)


@pytest.mark.parametrize("kind", sorted(ALWAYS_TRUE_KINDS, key=lambda k: k.value))
def test_declare_truthfully_builds_the_always_true_kinds(kind):
    plan = declare_truthfully(kind)
    assert plan.intent is Intent.TRUTH
    assert plan.kind is kind
    assert plan.is_lie is False


@pytest.mark.parametrize("kind", [ClaimKind.LOCATION, ClaimKind.HEADING])
def test_declare_truthfully_refuses_a_policy_kind(kind):
    """A location or heading claim carries content and must come from a
    policy, never from the always-true shortcut."""
    with pytest.raises(ValueError, match="only for"):
        declare_truthfully(kind)


def test_declare_truthfully_takes_no_intent_argument():
    """The caller cannot pass the wrong flag because there is nowhere to."""
    import inspect

    assert "intent" not in inspect.signature(declare_truthfully).parameters


@pytest.mark.parametrize("role", ROLES)
def test_no_policy_can_produce_an_always_true_kind(
    role, start_state, default_params, config, belief
):
    """The constructor gate is the last line, not the only one."""
    rng = random.Random(5)
    for _ in range(200):
        plan = plan_deception(role, start_state, default_params, belief, rng, config)
        assert plan.kind not in ALWAYS_TRUE_KINDS


@pytest.mark.parametrize("role", ROLES)
def test_the_intent_flag_exists_before_any_text_does(
    role, start_state, default_params, config, belief
):
    """LANG-03 / book Sec5.3.1: the flag is committed in advance. The returned
    object carries meaning and no phrasing at all -- 04-10 adds that later, and
    cannot revisit either field."""
    plan = plan_deception(role, start_state, default_params, belief, random.Random(0), config)
    assert plan.intent in (Intent.TRUTH, Intent.LIE)
    assert not set(vars(plan)) & {"text", "hint", "phrase", "message"}


def test_both_seats_run_from_separate_config_instances(start_state, default_params, belief):
    """CLAUDE.md rule 2: no shared live object between the cop and the thief."""
    cop_config = load_deception_config(_CONFIG / "deception.json")
    thief_config = load_deception_config(_CONFIG / "deception.json")
    assert cop_config is not thief_config
    assert plan_deception(
        "cop", start_state, default_params, belief, random.Random(0), cop_config
    ) is not plan_deception(
        "thief", start_state, default_params, belief, random.Random(0), thief_config
    )


def test_the_planner_imports_no_model_client():
    """The structural proof of rule 25 and STRAT-07, run as a unit test as
    well as in CI -- the same find_violations() the gate script calls."""
    import importlib.util

    root = pathlib.Path(__file__).parents[3]
    spec = importlib.util.spec_from_file_location(
        "llm_gate", root / "scripts" / "check_no_llm_in_strategy.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.find_violations() == []
