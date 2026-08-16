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
from pursuit.strategy import deception as deception_module
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.deception import ROLES, plan_deception
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
def test_an_always_true_declaration_is_built_through_the_constructor_itself(kind):
    """05-15 (G10) re-specification of `test_declare_truthfully_builds_the_
    always_true_kinds`. The FACT it pinned is unchanged and still pinned: a
    barrier or capture claim exists as a TRUTH-flagged plan and is never a
    lie. What changed is the path -- `declare_truthfully` was a convenience
    wrapper with zero production callers, and `DeceptionPlan.__post_init__`
    (never the wrapper) is the gate. Constructing it directly here is the
    point, not an inconvenience."""
    plan = DeceptionPlan(intent=Intent.TRUTH, kind=kind)
    assert plan.intent is Intent.TRUTH
    assert plan.kind is kind
    assert plan.is_lie is False


@pytest.mark.parametrize("role", ROLES)
def test_a_policy_kind_always_carries_its_own_content(role, start_state, default_params, config, belief):
    """05-15 (G10) re-specification of `test_declare_truthfully_refuses_a_
    policy_kind`. That test pinned "a LOCATION/HEADING claim must carry a
    sector or a heading and must come from a policy, never from the
    always-true shortcut". With the shortcut deleted the second half is
    `test_the_dispatcher_exposes_no_always_true_shortcut` below; the FIRST
    half is this -- and it is pinned against the real policies rather than
    against the wrapper's own error message, which is strictly stronger."""
    rng = random.Random(11)
    for _ in range(50):
        plan = plan_deception(role, start_state, default_params, belief, rng, config)
        assert plan.kind in (ClaimKind.LOCATION, ClaimKind.HEADING)
        if plan.kind is ClaimKind.LOCATION:
            assert plan.claimed_region is not None
        else:
            assert plan.claimed_heading is not None


def test_the_dispatcher_exposes_no_always_true_shortcut():
    """05-15 (G10) re-specification of `test_declare_truthfully_takes_no_
    intent_argument`, which pinned "there is nowhere to pass the wrong
    flag". There is now no shortcut at all: this module exposes no
    always-true constructor AND cannot even name an always-true kind, so
    re-adding one is not a silent change -- it needs an import this test
    fails on. `plan_deception` is asserted present as the control, so the
    introspection cannot pass by looking at the wrong object."""
    public = {name for name in dir(deception_module) if not name.startswith("_")}
    assert "plan_deception" in public  # control: we really are reading the module
    assert "declare_truthfully" not in public
    assert not public & {"ALWAYS_TRUE_KINDS", "ClaimKind", "Intent"}


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
