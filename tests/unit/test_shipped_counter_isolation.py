"""07-00 -- DEFECT 2, WRONG SCOPE: the test suite could write the SHIPPED,
league-facing games-played counter, and did, on every run.

MEASURED AT HEAD `de32c0b`, ONE full `uv run pytest tests/` (1539 passed,
96.64%), reading the two gitignored files immediately before and after:

    config/police/games_played.json   1895 -> 1909   (+14)
    config/thief/games_played.json    1888 -> 1902   (+14)

Zero games were played. Three integration files call `write_declaration`
with `load_agent_config("config/police")`, so `cfg.config_dir` IS the real
shipped directory and `cfg.config_dir / "games_played.json"` IS the real
counter. The two files also disagree by SEVEN although these two agents
have only ever played each other, which is independent proof the number
does not count games.

Rule 37 makes that number a declaration; rule 38 (`docs/RULES.md:79`) makes
declaring it falsely an ABSOLUTE DISQUALIFICATION.

WHAT IS PINNED HERE. Not "tests should be careful" -- the seam itself:
`tests/_shipped_config_guard.py` wraps the durable write the counter goes
through so a shipped-config target RAISES before a single byte is written,
and `tests/conftest.py` installs it for the whole session and separately
re-reads both counters at session end. Both halves are checked below, in
both directions: it must FIRE on the shipped tree and must NOT fire on a
throwaway path, or it would be a blanket block rather than a guard.

NON-DESTRUCTIVE BY CONSTRUCTION. No case here writes -- or attempts to
write -- the real counter file itself. The path predicate is asserted
DIRECTLY against both real counter paths (a pure function, no I/O), and the
raising behaviour is exercised against a sacrificial name inside the config
tree that no production code reads. A version of this file that pointed a
write attempt at the real counter would corrupt it the moment the guard
regressed, which is the opposite of what it is for.
"""

from __future__ import annotations

import pytest

from pursuit.security import step0_collect
from tests import _shipped_config_guard as guard

_SACRIFICE = "__guard_probe_never_read_by_production__.json"
_PROBE_RETRIES, _PROBE_BACKOFF = 1, 0.0
"""`durable_write_json`'s two keyword-only knobs. Supplied so the probe
below drives a write that WOULD SUCCEED if the guard were absent -- omit
them and the call dies of TypeError instead, which makes the case pass for
a reason that has nothing to do with the guard. Found by running the
silent-redirect probe, not by reading the test."""


def test_the_guard_covers_both_real_counter_paths():
    """The predicate, asserted directly on the two paths that matter. Pure
    function, no I/O, so this cannot itself advance anything."""
    assert len(guard.SHIPPED_COUNTERS) == 2
    for counter in guard.SHIPPED_COUNTERS:
        assert counter.name == "games_played.json"
        assert guard.is_shipped_config_path(counter), counter


def test_the_guard_resolves_relative_and_dotdot_paths():
    """`load_agent_config("config/police")` hands production a RELATIVE
    path, and that is exactly the shape every one of the +14 writes had. A
    guard that only recognised absolute paths would have missed all of
    them."""
    assert guard.is_shipped_config_path("config/police/games_played.json")
    assert guard.is_shipped_config_path(guard.REPO_ROOT / "logs" / ".." / "config" / "thief")
    assert not guard.is_shipped_config_path(guard.REPO_ROOT / "logs")


def test_a_write_into_the_shipped_config_tree_fails_loudly():
    """The mechanism must RAISE, not quietly redirect. A redirect would
    make the suite green while hiding the NEXT production path that writes
    the config tree at the wrong moment -- which is precisely how this
    defect survived from Phase 6 into Phase 7 with a document certifying it
    as correct behaviour (`docs/phases/phase-6/GATE-6-MEASUREMENT.md`).

    Aimed at a sacrificial name, never at the real counter, and driven with
    arguments a real write would accept, so a guard that had been removed
    or turned into a redirect is caught by the ASSERTIONS rather than by an
    incidental TypeError. `not target.exists()` is the half that separates
    "refused before writing" from "wrote, then complained"; the `finally`
    keeps a regression from leaving the tree dirty."""
    target = guard.SHIPPED_CONFIG_ROOT / "police" / _SACRIFICE
    try:
        with pytest.raises(guard.ShippedConfigWriteError) as excinfo:
            step0_collect.durable_write_json(
                target, {"games_played": 1},
                retries=_PROBE_RETRIES, backoff=_PROBE_BACKOFF,
            )

        assert not target.exists(), "the guard raised only AFTER writing -- too late"
        assert "games_played" in str(excinfo.value)
    finally:
        for stray in target.parent.glob(f"{_SACRIFICE}*"):
            stray.unlink()


def test_the_snapshot_can_actually_see_a_change(tmp_path, monkeypatch):
    """The session assertion in `conftest.py` compares two `read_counters()`
    dicts. If that function could not observe a write, the comparison would
    be vacuous and the whole second half of the seam would be decoration.
    Pinned against throwaway files, so the real counters are never touched:
    the point is that the OBSERVER works, not where it points."""
    fake = tmp_path / "games_played.json"
    fake.write_text('{"games_played": 41}', encoding="utf-8")
    monkeypatch.setattr(guard, "SHIPPED_COUNTERS", (fake,))

    before = guard.read_counters()
    fake.write_text('{"games_played": 42}', encoding="utf-8")
    after = guard.read_counters()

    assert before != after
    assert (before[str(fake)], after[str(fake)]) == (
        '{"games_played": 41}', '{"games_played": 42}',
    )


def test_the_guard_lets_a_throwaway_path_through(tmp_path):
    """The discriminating half. Without this, a guard that blocked every
    write would pass the case above while breaking every legitimate
    `tmp_path` round trip -- and `test_step0_collect.py`'s own
    record-then-read case is exactly such a round trip."""
    counter = tmp_path / "games_played.json"

    step0_collect.record_game_played(counter)

    assert step0_collect.read_games_played(counter) == 1
    assert not guard.is_shipped_config_path(counter)


def test_the_session_snapshot_reads_the_real_files():
    """The second, independent half of the seam: `conftest.py` snapshots
    both counters at session start and re-reads them at session end, so a
    write that reaches them by a route the patch does NOT cover is still
    caught -- late, but caught. Pinned because a snapshot that silently
    read nothing would make that assertion vacuous."""
    snapshot = guard.read_counters()

    assert set(snapshot) == {str(path) for path in guard.SHIPPED_COUNTERS}
    assert all(value is not None for value in snapshot.values()), (
        "both shipped counters must exist for the session assertion to mean anything"
    )
