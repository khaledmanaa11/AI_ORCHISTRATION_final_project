"""The league ledger: it records, it refuses what the book refuses, and it
never seeds itself from `games_played.json`.

The two refusals are rule 52 (one scoring game per opponent) and Table 18
row 5 (max games per team = 10, FIXED). Both are asserted in BOTH directions --
the permitted case has to still pass, or a refusal that refuses everything
would look like a working control.
"""

from __future__ import annotations

import json

import pytest

from pursuit.services.reporting.league_ledger import (
    MAX_GAMES_PER_TEAM,
    LeagueGameField,
    LedgerField,
    LedgerRefusalError,
    entries,
    league_ready,
    ledger_path,
    read_ledger,
    record_league_game,
    scored_opponents,
)

GAME = {"outcome": "cop_win", "commit_hash": "deadbeef"}


def _record(tmp_path, opponent, *, scored=True, game_id=None):
    return record_league_game(
        tmp_path, opponent=opponent, game_id=game_id or f"g-{opponent}", scored=scored, **GAME
    )


def test_a_fresh_ledger_is_empty_and_no_file_is_written_to_read_it(tmp_path):
    assert entries(read_ledger(tmp_path)) == []
    assert not ledger_path(tmp_path).exists()


def test_one_recorded_game_lands_on_disk_with_its_audit_trail(tmp_path):
    _record(tmp_path, "team-alpha")
    written = json.loads(ledger_path(tmp_path).read_text(encoding="utf-8"))
    (row,) = written[LedgerField.ENTRIES]
    assert row[LeagueGameField.OPPONENT] == "team-alpha"
    assert row[LeagueGameField.SCORED] is True
    assert row[LeagueGameField.COMMIT_HASH] == "deadbeef"
    assert row[LeagueGameField.RECORDED_AT]


def test_a_second_scoring_game_against_the_same_opponent_is_refused(tmp_path):
    """Rule 52 -- docs/PARAMETERS.md:86, one scoring game only per opponent."""
    _record(tmp_path, "team-alpha")
    with pytest.raises(LedgerRefusalError, match="rule 52"):
        _record(tmp_path, "team-alpha", game_id="rematch")


def test_a_warm_up_against_an_already_scored_opponent_is_permitted(tmp_path):
    """The other direction: rule 52 permits and encourages unscored warm-ups,
    so a refusal that refused these would be over-broad, not safe."""
    _record(tmp_path, "team-alpha")
    ledger = _record(tmp_path, "team-alpha", scored=False, game_id="warmup")
    assert len(entries(ledger)) == 2
    assert scored_opponents(ledger) == ("team-alpha",)


def test_a_scoring_game_against_a_different_opponent_is_permitted(tmp_path):
    _record(tmp_path, "team-alpha")
    ledger = _record(tmp_path, "team-beta")
    assert scored_opponents(ledger) == ("team-alpha", "team-beta")


def test_the_tenth_game_is_recorded_and_the_eleventh_is_refused(tmp_path):
    """Table 18 row 5 -- max games per team = 10, status FIXED. The bound is
    on ALL recorded games; warm-ups are games any one team played."""
    for index in range(MAX_GAMES_PER_TEAM):
        _record(tmp_path, f"team-{index}", scored=index < 2, game_id=f"g{index}")
    assert len(entries(read_ledger(tmp_path))) == MAX_GAMES_PER_TEAM
    with pytest.raises(LedgerRefusalError, match="row 5"):
        _record(tmp_path, "team-eleven", scored=False, game_id="g10")


def test_a_refused_game_leaves_the_ledger_untouched(tmp_path):
    _record(tmp_path, "team-alpha")
    before = ledger_path(tmp_path).read_text(encoding="utf-8")
    with pytest.raises(LedgerRefusalError):
        _record(tmp_path, "team-alpha", game_id="rematch")
    assert ledger_path(tmp_path).read_text(encoding="utf-8") == before


def test_scored_must_be_stated_explicitly(tmp_path):
    """Defaulting it either way lets rule 52's bound be dodged by omission."""
    with pytest.raises(TypeError, match="explicit bool"):
        record_league_game(
            tmp_path, opponent="team-alpha", game_id="g", scored="yes", **GAME
        )


@pytest.mark.parametrize("field", ["opponent", "game_id", "outcome"])
def test_a_blank_identifying_field_is_refused(tmp_path, field):
    kwargs = {"opponent": "a", "game_id": "b", "outcome": "c", "commit_hash": "d", "scored": True}
    kwargs[field] = "  "
    with pytest.raises(ValueError, match=field):
        record_league_game(tmp_path, **kwargs)


def test_a_corrupt_ledger_raises_rather_than_becoming_a_clean_zero(tmp_path):
    """Silently replacing it would turn a corrupt audit trail into a count of
    zero -- the rule-38 failure mode, arriving as a repair."""
    ledger_path(tmp_path).write_text(json.dumps({"version": "1.00"}), encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        read_ledger(tmp_path)


def test_league_ready_needs_two_scored_games_against_different_opponents(tmp_path):
    """Table 18 row 3 -- minimum games = 2, FIXED; rule 52 makes them
    necessarily different opponents."""
    assert not league_ready(read_ledger(tmp_path))
    _record(tmp_path, "team-alpha")
    assert not league_ready(read_ledger(tmp_path))
    _record(tmp_path, "team-alpha", scored=False, game_id="warmup")
    assert not league_ready(read_ledger(tmp_path)), "two games, one opponent, is not two teams"
    _record(tmp_path, "team-beta")
    assert league_ready(read_ledger(tmp_path))
