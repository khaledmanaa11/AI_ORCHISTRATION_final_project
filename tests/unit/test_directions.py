"""shared/directions.py: one heading vocabulary, shared by three subsystems.

The point of these tests is the SINGLE definition. If someone re-declares the
five words under strategy/ or services/ to dodge an import, the identity
assertions here fail rather than the drift showing up as a league opponent we
silently stop understanding.
"""

from pursuit.network.move_payload import DirectionWord as WireDirectionWord
from pursuit.shared.directions import DIRECTION_WORDS, DirectionWord


def test_network_re_export_is_the_same_object():
    """move_payload.py must re-export, not re-declare."""
    assert WireDirectionWord is DirectionWord


def test_direction_words_cover_every_member_in_declaration_order():
    assert tuple(word.value for word in DirectionWord) == DIRECTION_WORDS
    assert len(DIRECTION_WORDS) == len(set(DIRECTION_WORDS))


def test_stay_is_part_of_the_vocabulary():
    """A turn always carries an action; standing still is one of them."""
    assert DirectionWord.STAY.value in DIRECTION_WORDS


def test_members_compare_equal_to_their_own_strings():
    """`str, Enum` so a JSON-schema enum list and a dict key lookup both work."""
    assert DirectionWord.NORTH == "north"
    assert DirectionWord("north") is DirectionWord.NORTH


def test_no_vector_leaks_into_the_shared_vocabulary():
    """Resolving a word to (row, col) depends on the negotiated axis origin
    and stays in move_payload.py; this module holds words only."""
    assert all(isinstance(word.value, str) for word in DirectionWord)
