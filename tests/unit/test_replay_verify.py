"""The three verdicts, and the proof that each one is reachable.

A viewer that can only ever say `Verified OK` is a decoration, not a
verification, so this file spends most of its length making the OTHER two
happen: four separate single-field tampers, and an artifact with nothing in it.

THE FOUR TAMPERS ARE FOUR TESTS, deliberately, not one `parametrize` case
built from `TAMPERABLE_FIELDS`. An emptied or thinned table SKIPS silently --
this phase has found that twice -- and a verifier that re-hashed only `move`
would pass a one-case test. The table is still asserted complete below, so a
FIFTH `verify_reveal` input added upstream fails here rather than going
unchecked.
"""

from __future__ import annotations

from pursuit.services.reporting.artifact_log import verify_log_turns
from pursuit.services.reporting.replay_verify import (
    NOTHING_TO_VERIFY,
    VERIFIED_OK,
    VerdictState,
    banner_colour,
    check_turns,
)
from tests.unit import replay_fixtures as fx

#: Not turn 0. A verifier that always named the first turn would pass a
#: tamper test aimed at the first turn and tell a grader nothing.
TAMPER_INDEX = 2
TAMPER_TURN = 2
FIRST_TURN = 0


def _tampered(field: str):
    """One field flipped, then RESEALED -- so the verdict below is earned by
    the per-turn re-hash and not by the artifact seal (see the fixtures)."""
    return fx.verdict(fx.reseal(fx.tamper(fx.artifact(), field, index=TAMPER_INDEX)))


def _assert_names_the_tampered_turn(verdict) -> None:
    assert verdict.state is VerdictState.FAILED
    assert verdict.banner != VERIFIED_OK
    assert f"turn {TAMPER_TURN}" in verdict.banner, verdict.banner
    assert f"turn {FIRST_TURN}" not in verdict.banner, "the banner named turn 0, not the tamper"
    assert verdict.verified == fx.COMMITTED_TURNS - 1
    assert verdict.committed == fx.COMMITTED_TURNS


def test_a_clean_artifact_shows_the_words_the_gate_quotes():
    """Sec10.4 criterion 3, verbatim -- equality, not a substring, so a
    banner that merely CONTAINED the phrase would fail here."""
    verdict = fx.verdict(fx.artifact())
    assert verdict.banner == VERIFIED_OK
    assert verdict.state is VerdictState.OK and verdict.is_ok
    assert verdict.committed == fx.COMMITTED_TURNS > 0, "a zero-turn OK proves nothing"
    assert verdict.verified == verdict.committed


def test_a_tampered_state_fails_and_names_the_turn():
    _assert_names_the_tampered_turn(_tampered(fx.TurnField.STATE))


def test_a_tampered_move_fails_and_names_the_turn():
    _assert_names_the_tampered_turn(_tampered(fx.TurnField.MOVE))


def test_a_tampered_intent_fails_and_names_the_turn():
    _assert_names_the_tampered_turn(_tampered(fx.TurnField.INTENT))


def test_a_tampered_nonce_fails_and_names_the_turn():
    _assert_names_the_tampered_turn(_tampered(fx.TurnField.NONCE))


def test_all_four_verify_reveal_inputs_are_covered_above():
    """The anti-vacuity floor for the four tests above: a fifth input added to
    `commit_pack.build_commit_payload` must fail HERE, loudly, rather than
    quietly going untested."""
    assert len(fx.TAMPERABLE_FIELDS) == 4
    assert set(fx.TAMPERERS) == set(fx.TAMPERABLE_FIELDS)


def test_an_artifact_with_no_committed_turn_is_neither_ok_nor_failed():
    """`all_matched([])` is True and so is `all(...)` over nothing. The state
    is asserted specifically, not merely `!= OK`: a viewer that reported
    FAILED here would be accusing an opponent of a game that has no turns."""
    verdict = fx.verdict(fx.artifact(committed=0))
    assert verdict.state is VerdictState.NOTHING_TO_VERIFY
    assert verdict.banner == NOTHING_TO_VERIFY
    assert verdict.banner != VERIFIED_OK and not verdict.is_ok
    assert (verdict.verified, verdict.committed) == (0, 0)


def test_an_artifact_with_an_empty_turns_list_is_nothing_to_verify():
    verdict = fx.verdict(fx.empty_artifact())
    assert verdict.state is VerdictState.NOTHING_TO_VERIFY
    assert verdict.banner != VERIFIED_OK


def test_the_three_banners_are_three_distinct_strings():
    """The counter-control for every `!= VERIFIED_OK` above: they differ
    because the states differ, not because one of them is empty."""
    banners = {
        fx.verdict(fx.artifact()).banner,
        fx.verdict(fx.reseal(fx.tamper(fx.artifact(), fx.TurnField.NONCE))).banner,
        fx.verdict(fx.artifact(committed=0)).banner,
    }
    assert len(banners) == 3
    assert all(banner for banner in banners), "an empty banner is not a verdict"


def test_every_state_has_its_own_colour_and_ok_is_not_the_failure_one():
    """`banner_colour`'s ONLY caller is `gui/replay_panels.py`, which
    `pyproject.toml:38` omits from coverage -- 07-06 found the same shape in
    `lit_cells` and wired it rather than excusing it. The colour is not
    decoration either: a `FAILED` banner painted the OK green would be a lie
    on the one screen a grader screenshots, and a state with no entry would
    raise `KeyError` at render time rather than at import."""
    colours = [banner_colour(state) for state in VerdictState]
    assert len(colours) == len(set(colours)) == 3
    assert banner_colour(VerdictState.OK) != banner_colour(VerdictState.FAILED)
    assert banner_colour(VerdictState.NOTHING_TO_VERIFY) != banner_colour(VerdictState.OK)


def test_the_trailing_game_over_turn_is_not_counted_as_committed():
    """It has wire records and no ledger entry. Counting it would report
    `4/5` on a perfectly honest game and read as a failure."""
    artifact = fx.artifact()
    assert len(artifact[fx.LogArtifactField.TURNS]) == fx.COMMITTED_TURNS + 1
    checks = check_turns(artifact)
    assert len(checks) == fx.COMMITTED_TURNS + 1
    assert sum(1 for check in checks if check.committed) == fx.COMMITTED_TURNS
    assert checks[-1].committed is False and checks[-1].ok is False


def test_the_verdict_agrees_with_the_builders_own_counter():
    """`artifact_log.verify_log_turns` counts the same thing by a different
    route (07-05's entry point). The two are pinned against each other on both
    a clean artifact and a tampered one, so neither can drift alone."""
    clean = fx.artifact()
    assert verify_log_turns(clean) == (
        fx.verdict(clean).verified, fx.verdict(clean).committed,
    )
    broken = fx.reseal(fx.tamper(fx.artifact(), fx.TurnField.MOVE, index=TAMPER_INDEX))
    assert verify_log_turns(broken) == (fx.verdict(broken).verified, fx.verdict(broken).committed)
    assert verify_log_turns(broken)[0] < verify_log_turns(broken)[1], "the tamper did not land"
