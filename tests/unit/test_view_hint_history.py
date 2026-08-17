"""`HintHistory`: the caller-owned, append-only hint log -- split out of
`test_view_builder.py` at the 150-code-line gate (Segal Table 5). Split,
never compressed.

Peer data is hostile by 05-12's boundary rule: `ctx.incoming_hints[sender]`
is whatever arrived over the wire, and `tools.receive_hint` validates it as
nothing more than `isinstance(payload, dict)`. The accumulator must be TOTAL
over it -- a view that raises is a dashboard that dies mid-game -- and a
field it cannot trust must be DROPPED, never coerced into something
plausible.
"""

from __future__ import annotations

from pursuit.sdk.view_builder import HintHistory, build_local_view
from tests.unit import local_view_fixtures as fx

_HOSTILE_PAYLOADS = (
    {},
    {"text": None},
    {"text": 17, "intent": "lie", "turn": 1},
    {"text": "ok", "intent": "maybe", "turn": "3"},
    {"text": "ok", "intent": "truth", "turn": True},
    {"text": "ok", "intent": ["truth"], "turn": [1]},
    "not a dict at all",
)


def test_incoming_hints_are_recorded_with_the_senders_claimed_intent(
    tmp_path, default_params, network_params
):
    """`claimed_intent` is the SENDER's own flag -- what the opponent
    asserts about its own honesty, never a verdict we reached."""
    view = fx.honest_view(tmp_path, default_params, network_params)
    assert len(view.hints) == 1
    assert view.hints[0].sender == "thief"
    assert view.hints[0].claimed_intent == "lie"
    assert view.hints[0].text == fx.INCOMING_HINT["text"]
    assert view.hints[0].turn == fx.INCOMING_HINT["turn"]


def test_hint_history_is_append_only_and_deduplicated(
    tmp_path, default_params, network_params
):
    """`ctx.incoming_hints` holds the LAST hint per sender and is never
    cleared, so a refresh loop re-reads the same one on every tick."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    history = HintHistory()
    for _ in range(3):
        build_local_view(ctx, history)
    assert len(history.entries) == 1
    ctx.incoming_hints = {"thief": {"text": "second", "intent": "truth", "turn": 3}}
    view = build_local_view(ctx, history)
    assert [h.text for h in view.hints] == [fx.INCOMING_HINT["text"], "second"]


def test_a_repeated_text_on_a_later_turn_is_not_swallowed(
    tmp_path, default_params, network_params
):
    """Dedupe is per (sender, whole entry) -- saying the same thing twice is
    a real event, and a log that hid it would misrepresent the channel."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    history = HintHistory()
    build_local_view(ctx, history)
    ctx.incoming_hints = {"thief": {**fx.INCOMING_HINT, "turn": 5}}
    build_local_view(ctx, history)
    assert [h.turn for h in history.entries] == [2, 5]


def test_two_histories_in_one_interpreter_share_nothing(
    tmp_path, default_params, network_params
):
    """NET-02 / rule 2: the accumulator is an instance the caller owns, so
    two agent processes -- or two windows -- never observe each other."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    first, second = HintHistory(), HintHistory()
    build_local_view(ctx, first)
    assert first.entries and second.entries == []


def test_recorded_outgoing_hints_join_the_same_log():
    """Our own hints are the one entry whose intent flag is a fact."""
    history = HintHistory()
    history.record_outgoing(turn=5, text="I am heading south", intent="truth")
    history.record_outgoing(turn=6, text="I am heading south", intent="lie")
    assert [(h.sender, h.turn, h.claimed_intent) for h in history.entries] == [
        ("self", 5, "truth"),
        ("self", 6, "lie"),
    ]


def test_an_unrecognised_outgoing_intent_is_dropped_not_coerced():
    history = HintHistory()
    history.record_outgoing(turn=1, text="x", intent="probably")
    assert history.entries[0].claimed_intent is None


def test_hostile_hint_payloads_never_raise_and_never_fabricate(
    tmp_path, default_params, network_params
):
    """Total over peer data. `True` is an `int` subclass and would render as
    turn 1; an unknown intent means 'the sender declared nothing we
    understand', which is not the same fact as 'truth'."""
    assert len(_HOSTILE_PAYLOADS) == 7, "a thinned payload set would prove less"
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    for payload in _HOSTILE_PAYLOADS:
        ctx.incoming_hints = {"thief": payload}
        view = build_local_view(ctx, HintHistory())
        for hint in view.hints:
            assert isinstance(hint.text, str)
            assert hint.turn is None or type(hint.turn) is int
            assert hint.claimed_intent in (None, "truth", "lie")


def test_a_hostile_payload_that_is_all_noise_yields_no_entry_at_all(
    tmp_path, default_params, network_params
):
    """Counter-control for the loop above: it would pass vacuously against
    a builder that dropped EVERY hint, so pin both outcomes."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    ctx.incoming_hints = {"thief": {"text": 17}}
    assert build_local_view(ctx, HintHistory()).hints == ()
    ctx.incoming_hints = {"thief": {"text": "ok", "intent": "maybe", "turn": True}}
    kept = build_local_view(ctx, HintHistory()).hints
    assert len(kept) == 1
    assert (kept[0].text, kept[0].turn, kept[0].claimed_intent) == ("ok", None, None)
