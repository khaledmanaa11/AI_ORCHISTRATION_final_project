"""05-12 / G9: the PEER-controlled half of the digest comparison.

Split out of test_config_hash.py at the 150-code-line gate (Segal Table 5)
the moment these cases pushed it to 161 -- the same split test_handshake.py,
audit.py and deadline.py each took in this phase. Nothing was compressed and
nothing was dropped: test_config_hash.py keeps every pre-05-12 case, INCLUDING
the re-specified `test_compare_named_digest_uses_constant_time_compare` the
plan names by line number, and this file holds only what 05-12 adds.

The seam matches the source's: `digests_match` is the STRICT internal idiom
(D-46, `secrets.compare_digest`) and `unusable_peer_digest` /
`compare_named_digest` are the boundary that stands between it and a peer.
"""

from __future__ import annotations

import pytest

from pursuit.network.config_hash import (
    compare_named_digest,
    digests_match,
    unusable_peer_digest,
)

_TYPED = [(1234, "int"), ([1, 2], "list"), ({"a": 1}, "dict"), (True, "bool"), (3.5, "float")]


@pytest.mark.parametrize("bad", [None, 1234, [1, 2], {"a": 1}, True, 3.5])
def test_digests_match_keeps_its_strict_raising_contract(bad):
    """The strict contract is UNCHANGED by this plan and stays directly pinned.

    The G9 containment lands one level up, in `compare_named_digest`, so
    `digests_match` still guards INTERNAL misuse loudly on BOTH sides -- D-46
    fixes `secrets.compare_digest` as the project's one digest idiom, and a
    caller that hands it a non-str has a bug, not a hostile peer."""
    d = "a" * 64
    with pytest.raises(TypeError, match="digests_match requires two str arguments"):
        digests_match(d, bad)
    with pytest.raises(TypeError, match="digests_match requires two str arguments"):
        digests_match(bad, d)


@pytest.mark.parametrize(("remote", "type_name"), _TYPED)
def test_compare_named_digest_contains_a_non_str_remote(remote, type_name):
    """G9: a peer-controlled non-str digest is a NAMED non-agreement.

    `Envelope.from_dict` validates the payload only as a dict, so
    `payload["digest"]` is whatever JSON type the peer chose. Measured at
    `0437559`, every one of these raised `TypeError: digests_match requires
    two str arguments` out of `evaluate()` -- past the try/except that wraps
    the DECODE block only, and out of `run_agent`, whose only guard is
    `except ToolError` -- so WE became the side that published no nonces
    (rule 36) with no verdict in our own log."""
    ok, detail = compare_named_digest("config", "aaaa", remote)
    assert ok is False
    assert detail == f"config digest present in peer payload but not a string: {type_name}"


def test_the_three_non_agreement_details_are_pairwise_distinct():
    """absent / not-a-string / differed must be tellable apart in the log --
    that is the whole reason `compare_named_digest` returns a detail at all,
    and the plan's own control set names exactly these three."""
    details = {
        compare_named_digest("scent", "aaaa", None)[1],
        compare_named_digest("scent", "aaaa", 1234)[1],
        compare_named_digest("scent", "aaaa", "bbbb")[1],
    }
    assert len(details) == 3


def test_the_peer_value_never_reaches_the_detail_only_its_type():
    """The detail is folded into an abort message, echoed to a console AND
    appended to the JSONL log -- and a PEER chooses this value. A bounded type
    name cannot be used to flood either sink; the value itself could."""
    flood = "PEER-CONTROLLED-" + "x" * 10_000
    _ok, detail = compare_named_digest("config", "aaaa", [flood])
    assert "PEER-CONTROLLED" not in detail
    assert detail.endswith("not a string: list")


def test_unusable_peer_digest_is_safety_only_never_convention():
    """THE FAIRNESS CONTROL for this gate (rules 16/22). Any `str` passes and
    reaches the real comparison as EVIDENCE -- a foreign league implementation
    using a shorter, longer, upper-case or non-hex digest is an HONEST peer we
    merely disagree with, and must never be pre-judged by a shape check here.
    05-10 declined `isinstance(turn, int)` for exactly this reason.

    This test FAILS against the tempting stronger rule (a hex/length check),
    which is the discrimination it owes."""
    for foreign in ("", "ABCDEF", "not-a-hex-digest", "z" * 200, "a" * 64):
        assert unusable_peer_digest("config", foreign) is None
    ok, detail = compare_named_digest("config", "aaaa", "AAAA")
    assert ok is False
    assert "mismatch" in detail  # differed, NOT rejected on shape
