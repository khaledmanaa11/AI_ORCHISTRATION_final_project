"""The four artifact filenames pinned to docs/PARAMETERS.md:165-168, and the
`<NN>` sub-game index (D-72).

The expected names below are TRANSCRIBED FROM THE DOCUMENT as literals, never
read back from the module under test and never built from a directory glob:
an empty or thinned `parametrize` source SKIPS SILENTLY and leaves the whole
file reading green while asserting nothing (07-01 found exactly that hole in
its own single most important control). `test_the_parameters_table_is_intact`
is the guard against that, and it runs first.
"""

import pytest

from pursuit.services.reporting import artifacts

_GAME_ID = "074fc2b16888899e"

# docs/PARAMETERS.md:165-168 verbatim, with <game_id> substituted and <NN>=01.
# `_g<NN>` PRESENT on config_/log_, ABSENT on declaration_/result_.
_PARAMETERS_NAMES = (
    ("declaration", f"declaration_{_GAME_ID}.json"),
    ("config", f"config_{_GAME_ID}_g01.json"),
    ("log", f"log_{_GAME_ID}_g01.json"),
    ("result", f"result_{_GAME_ID}.json"),
)

_BUILDERS = {
    "declaration": lambda: artifacts.declaration_filename(_GAME_ID),
    "config": lambda: artifacts.config_filename(_GAME_ID, 1),
    "log": lambda: artifacts.log_filename(_GAME_ID, 1),
    "result": lambda: artifacts.result_filename(_GAME_ID),
}

# The width is a MINIMUM, not a truncation: 100 widens rather than colliding.
_PADDING_CASES = ((1, "_g01"), (9, "_g09"), (10, "_g10"), (99, "_g99"), (100, "_g100"))
_BAD_INDEX_TYPES = (True, False, "1", 1.0, None, [1])
_BAD_INDEX_VALUES = (0, -1, -99)


def test_the_parameters_table_is_intact():
    """ANTI-VACUITY GUARD -- every parametrize in this file draws on one of
    these tables, and a thinned table would skip silently rather than fail."""
    assert len(_PARAMETERS_NAMES) == 4
    assert set(_BUILDERS) == {kind for kind, _ in _PARAMETERS_NAMES}
    assert len(_PADDING_CASES) == 5
    assert len(_BAD_INDEX_TYPES) == 6
    assert len(_BAD_INDEX_VALUES) == 3


@pytest.mark.parametrize(("kind", "expected"), _PARAMETERS_NAMES)
def test_filename_matches_parameters_character_for_character(kind, expected):
    assert _BUILDERS[kind]() == expected


@pytest.mark.parametrize("kind", ("declaration", "result"))
def test_adding_g_nn_to_an_unindexed_name_fails_the_same_assertion(kind):
    """THE NEGATIVE HALF. Without it the check above is shape-only: it would
    pass just as happily if every builder appended `_g01`."""
    expected = dict(_PARAMETERS_NAMES)[kind]
    wrong = f"{expected.removesuffix('.json')}_g01.json"
    with pytest.raises(AssertionError):
        assert wrong == expected


@pytest.mark.parametrize("kind", ("config", "log"))
def test_dropping_g_nn_from_an_indexed_name_fails_the_same_assertion(kind):
    """And the mirror: a builder that forgot `_g<NN>` must not pass either."""
    expected = dict(_PARAMETERS_NAMES)[kind]
    wrong = expected.replace("_g01", "")
    with pytest.raises(AssertionError):
        assert wrong == expected


@pytest.mark.parametrize(("index", "suffix"), _PADDING_CASES)
def test_sub_game_suffix_zero_pads_to_two_and_widens_beyond(index, suffix):
    assert artifacts.sub_game_suffix(index) == suffix


@pytest.mark.parametrize("bad", _BAD_INDEX_TYPES)
def test_sub_game_suffix_rejects_a_non_int_index(bad):
    """`True` is in this table on purpose: bool is an int subclass, so an
    unguarded builder would name a file `_g01` for it."""
    with pytest.raises(TypeError):
        artifacts.sub_game_suffix(bad)


@pytest.mark.parametrize("bad", _BAD_INDEX_VALUES)
def test_sub_game_suffix_rejects_a_below_one_index(bad):
    with pytest.raises(ValueError, match="sub_game_index"):
        artifacts.sub_game_suffix(bad)


def test_index_starts_at_one_for_a_directory_that_does_not_exist(tmp_path):
    assert artifacts.next_sub_game_index(tmp_path / "absent", _GAME_ID) == 1


def test_index_advances_within_a_game_id_and_restarts_across_them(tmp_path):
    assert artifacts.next_sub_game_index(tmp_path, _GAME_ID) == 1
    (tmp_path / artifacts.config_filename(_GAME_ID, 1)).write_text("{}", encoding="utf-8")
    assert artifacts.next_sub_game_index(tmp_path, _GAME_ID) == 2
    assert artifacts.next_sub_game_index(tmp_path, "a-different-game") == 1


def test_a_log_artifact_alone_also_advances_the_index(tmp_path):
    """Both indexed names count -- a run that wrote log_ but crashed before
    config_ must not hand the NEXT sub-game the same `<NN>`."""
    (tmp_path / artifacts.log_filename(_GAME_ID, 4)).write_text("{}", encoding="utf-8")
    assert artifacts.next_sub_game_index(tmp_path, _GAME_ID) == 5


def test_unindexed_artifacts_never_advance_the_index(tmp_path):
    (tmp_path / artifacts.declaration_filename(_GAME_ID)).write_text("{}", encoding="utf-8")
    (tmp_path / artifacts.result_filename(_GAME_ID)).write_text("{}", encoding="utf-8")
    assert artifacts.next_sub_game_index(tmp_path, _GAME_ID) == 1


def test_durable_write_rotation_generations_do_not_advance_the_index(tmp_path):
    """`durable_write_json` leaves `.prev`/`.tmp` generations beside its
    target; counting one would skip a `<NN>` and break the join."""
    stem = artifacts.config_filename(_GAME_ID, 1).removesuffix(".json")
    for generation in (".prev.json", ".tmp.json"):
        (tmp_path / f"{stem}{generation}").write_text("{}", encoding="utf-8")
    assert artifacts.next_sub_game_index(tmp_path, _GAME_ID) == 1


def test_a_game_id_is_escaped_before_it_becomes_a_pattern(tmp_path):
    """`game_id` is NEGOTIATED WITH A PEER (D-61), so it is not ours to trust
    as a regex fragment. The direction that matters is a metacharacter id
    matching SOMEONE ELSE'S artifact: unescaped, `a.c` matches `axc` and hands
    this game an index derived from another game's files."""
    (tmp_path / artifacts.config_filename("axc", 7)).write_text("{}", encoding="utf-8")
    assert artifacts.next_sub_game_index(tmp_path, "a.c") == 1
    (tmp_path / artifacts.config_filename("a.c", 2)).write_text("{}", encoding="utf-8")
    assert artifacts.next_sub_game_index(tmp_path, "a.c") == 3
    assert artifacts.next_sub_game_index(tmp_path, "axc") == 8


def test_any_entry_holding_the_name_counts_even_a_directory(tmp_path):
    """The index exists so the NEXT write cannot collide, and a directory
    occupying an artifact's name collides just as hard as a file does."""
    (tmp_path / artifacts.config_filename(_GAME_ID, 3)).mkdir()
    assert artifacts.next_sub_game_index(tmp_path, _GAME_ID) == 4
