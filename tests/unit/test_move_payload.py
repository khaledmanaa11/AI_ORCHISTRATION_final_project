"""Tests for the D-53 direction-token move/barrier codec (move_payload.py)."""

from pursuit.network.move_payload import ActionKind, DirectionWord, Origin, decode, encode, is_legal
from pursuit.sdk.actions import thief_actions
from pursuit.shared.state import GameState

_ALL_DIRECTIONS = [
    ((3, 3), (2, 3)),  # north
    ((3, 3), (4, 3)),  # south
    ((3, 3), (3, 4)),  # east
    ((3, 3), (3, 2)),  # west
    ((3, 3), (3, 3)),  # stay
]


def test_encode_contains_no_integer_cell_reference():
    payload = encode((3, 3), (2, 3), ActionKind.MOVE)
    assert payload == {"kind": "move", "direction": "north"}


def test_round_trip_every_direction_on_a_7x7_board(default_params):
    for pre, post in _ALL_DIRECTIONS:
        payload = encode(pre, post, ActionKind.MOVE)
        resolved = decode(payload, pre, default_params)
        assert resolved.ok
        assert resolved.cell == post
        assert resolved.kind is ActionKind.MOVE


def test_legacy_xy_payload_decodes_to_the_same_action(default_params):
    pre, post = (3, 3), (2, 3)
    direction_result = decode(encode(pre, post, ActionKind.MOVE), pre, default_params)
    legacy_result = decode({"x": post[0], "y": post[1]}, pre, default_params)
    assert legacy_result.ok
    assert legacy_result.cell == direction_result.cell == post


def test_barrier_target_relative_to_the_cop(default_params):
    cop = (0, 0)
    self_payload = encode(cop, cop, ActionKind.BARRIER)
    assert self_payload == {"kind": "barrier", "direction": "stay"}
    neighbor_payload = encode(cop, (0, 1), ActionKind.BARRIER)
    resolved = decode(neighbor_payload, cop, default_params)
    assert resolved.ok
    assert resolved.kind is ActionKind.BARRIER
    assert resolved.cell == (0, 1)


def test_decode_rejects_diagonal_legacy_payload(default_params):
    resolved = decode({"x": 4, "y": 4}, (3, 3), default_params)
    assert not resolved.ok
    assert "orthogonal" in resolved.reason


def test_decode_rejects_off_board_step(default_params):
    resolved = decode({"direction": "north"}, (0, 0), default_params)
    assert not resolved.ok
    assert "off-board" in resolved.reason


def test_decode_rejects_garbage_direction_string(default_params):
    resolved = decode({"direction": "sideways"}, (3, 3), default_params)
    assert not resolved.ok
    assert resolved.reason


def test_decode_rejects_non_dict_payload(default_params):
    resolved = decode("garbage", (3, 3), default_params)
    assert not resolved.ok


def test_decode_rejects_payload_missing_both_shapes(default_params):
    resolved = decode({}, (3, 3), default_params)
    assert not resolved.ok


def test_decode_rejects_bool_as_legacy_coordinate(default_params):
    resolved = decode({"x": True, "y": 3}, (3, 3), default_params)
    assert not resolved.ok
    assert "int" in resolved.reason


def test_decode_never_raises_and_never_returns_stay_on_failure(default_params):
    for bad_payload in ({"direction": "diagonal"}, {"x": 99, "y": 99}, {}, "nope"):
        resolved = decode(bad_payload, (3, 3), default_params)
        assert resolved.ok is False
        assert resolved.cell is None


def test_encode_raises_for_a_non_orthogonal_pair():
    try:
        encode((0, 0), (1, 1), ActionKind.MOVE)
    except ValueError:
        return
    raise AssertionError("expected ValueError for a diagonal encode() request")


def test_flipping_origin_flips_the_sense_of_north(default_params):
    top_left = decode({"direction": "north"}, (3, 3), default_params, origin=Origin.TOP_LEFT.value)
    bottom_left = decode(
        {"direction": "north"}, (3, 3), default_params, origin=Origin.BOTTOM_LEFT.value
    )
    assert top_left.cell == (2, 3)
    assert bottom_left.cell == (4, 3)
    assert top_left.cell != bottom_left.cell


def test_flipping_origin_round_trips_encode_too():
    payload = encode((3, 3), (4, 3), ActionKind.MOVE, origin=Origin.BOTTOM_LEFT.value)
    assert payload["direction"] == DirectionWord.NORTH.value


def test_is_legal_true_for_a_real_legal_move(default_params, start_state):
    dest = thief_actions(start_state, default_params)[0]
    resolved = decode(encode(start_state.thief, dest, ActionKind.MOVE), start_state.thief, default_params)
    assert is_legal(start_state.thief, resolved, start_state, default_params)


def test_is_legal_false_for_a_move_onto_a_barrier(default_params, start_state):
    barriered = GameState(
        cop=start_state.cop,
        thief=start_state.thief,
        barriers=frozenset({(start_state.thief[0] - 1, start_state.thief[1])}),
        barriers_placed=1,
        turn=0,
    )
    resolved = decode({"direction": "north"}, start_state.thief, default_params)
    assert resolved.ok  # geometry alone does not know about barriers
    assert not is_legal(start_state.thief, resolved, barriered, default_params)


def test_is_legal_false_when_not_ok():
    failed = decode({}, (3, 3), None)
    assert is_legal((3, 3), failed, None, None) is False


def test_is_legal_barrier_on_cops_own_cell(default_params, start_state):
    resolved = decode({"kind": "barrier", "direction": "stay"}, start_state.cop, default_params)
    assert is_legal(start_state.cop, resolved, start_state, default_params)


def test_is_legal_true_for_a_real_legal_cop_move(default_params, start_state):
    resolved = decode({"direction": "stay"}, start_state.cop, default_params)
    assert is_legal(start_state.cop, resolved, start_state, default_params)


def test_is_legal_false_for_a_cell_matching_neither_cop_nor_thief(default_params, start_state):
    off_path = (start_state.cop[0], start_state.cop[1])
    while off_path in (start_state.cop, start_state.thief):
        off_path = (off_path[0] + 1, off_path[1])
    resolved = decode({"direction": "stay"}, off_path, default_params)
    assert resolved.ok
    assert not is_legal(off_path, resolved, start_state, default_params)
