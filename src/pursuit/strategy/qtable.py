"""JSON-persisted Q-table with per-key visit counts (STRAT-01, D-02, D-08).

Persistence is JSON only -- never pickle (D-02): JSON object keys must be
strings, so this module keeps that constraint explicit rather than papering
over it with a tuple key that would silently stringify on save and fail to
match on load. Values and visit counts live together per state key in the
schema below, so a save/load cycle can never desynchronize them:

    {"version": 1, "table": {"<key>": {"values": {"<action>": <q>, ...},
                                        "visits": <int>}}}

load() is fail-loud: malformed JSON, a missing schema version, an
out-of-range action index, or a key `encoding.decode_state` cannot parse
each raise with the offending detail -- an empty table loads cleanly and
plays like a random agent, which is exactly the failure that would waste an
overnight run, so this module never degrades silently to one.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.constants import Action
from pursuit.shared.durable_write import durable_write_json, load_json_with_fallback
from pursuit.strategy.encoding import decode_state

SCHEMA_VERSION = 1
_ACTION_COUNT = len(Action)

# Retry/backoff mechanics for save()'s durable write -- structural, not a
# game value or RL hyperparameter (same exemption already established for
# prior.py's _MASS_TOLERANCE and pathfind.py's UNREACHABLE sentinel).
_SAVE_RETRIES = 3
_SAVE_BACKOFF_SECONDS = 0.1


class QTable:
    """Per-role Q-value table keyed by `encoding.encode_state` output."""

    def __init__(self) -> None:
        self._values: dict[str, dict[int, float]] = {}
        self._visits: dict[str, int] = {}

    def get(self, key: str, action: int) -> float:
        """Unseen (key, action) defaults to 0.0."""
        return self._values.get(key, {}).get(int(action), 0.0)

    def set(self, key: str, action: int, value: float) -> None:
        self._values.setdefault(key, {})[int(action)] = float(value)

    def bump_visit(self, key: str) -> None:
        self._visits[key] = self._visits.get(key, 0) + 1

    def visits(self, key: str) -> int:
        """Unseen key has 0 visits -- the STRAT-02 fallback trigger reads this (D-08)."""
        return self._visits.get(key, 0)

    def copy(self) -> QTable:
        """Shallow-independent snapshot: mutating the copy never touches
        self, and vice versa. 03-08's sparring pool uses this to admit a
        past-self checkpoint into its ring buffer without reaching into
        another module's private attributes (QUAL-02)."""
        clone = QTable()
        clone._values = {key: dict(actions) for key, actions in self._values.items()}
        clone._visits = dict(self._visits)
        return clone

    def best_action(self, key: str) -> int:
        """Argmax action for `key`; ties break to the smallest action index,
        deterministically, so a replayed game reproduces the same move."""
        best_value = self.get(key, 0)
        best_action = 0
        for action in range(1, _ACTION_COUNT):
            value = self.get(key, action)
            if value > best_value:
                best_value, best_action = value, action
        return best_action

    def save(self, path: Path | str) -> None:
        """Write this table crash-safely (D-15, D-24) -- see durable_write."""
        payload = {"version": SCHEMA_VERSION, "table": self._to_table_payload()}
        durable_write_json(path, payload, retries=_SAVE_RETRIES, backoff=_SAVE_BACKOFF_SECONDS)

    def _to_table_payload(self) -> dict:
        keys = set(self._values) | set(self._visits)
        return {
            key: {
                "values": {str(a): v for a, v in self._values.get(key, {}).items()},
                "visits": self._visits.get(key, 0),
            }
            for key in keys
        }

    @classmethod
    def load(cls, path: Path | str) -> QTable:
        """Load a table saved by `save()`; fails loud, never partially populated."""
        raw = load_json_with_fallback(path)
        table = cls()
        table._load_from_payload(raw, source=str(path))
        return table

    def _load_from_payload(self, raw: object, *, source: str) -> None:
        _validate_top_level(raw, source=source)
        for key, entry in raw["table"].items():
            decode_state(key)  # fails loud on an unparseable key (D-02)
            _validate_entry(entry, key=key, source=source)
            for action_str, value in entry.get("values", {}).items():
                action = _validate_action_index(action_str, key=key, source=source)
                self._values.setdefault(key, {})[action] = float(value)
            self._visits[key] = int(entry["visits"])


def _validate_top_level(raw: object, *, source: str) -> None:
    if not isinstance(raw, dict):
        raise ValueError(f"{source}: qtable file must contain a JSON object")
    if "version" not in raw:
        raise ValueError(f"{source}: qtable file missing required 'version' field")
    if "table" not in raw or not isinstance(raw["table"], dict):
        raise ValueError(f"{source}: qtable file missing required 'table' object")


def _validate_entry(entry: object, *, key: str, source: str) -> None:
    if not isinstance(entry, dict) or "visits" not in entry:
        raise ValueError(f"{source}: qtable entry {key!r} missing required 'visits' field")


def _validate_action_index(action_str: str, *, key: str, source: str) -> int:
    try:
        action = int(action_str)
    except ValueError as exc:
        raise ValueError(
            f"{source}: qtable entry {key!r} has non-integer action index {action_str!r}"
        ) from exc
    if not 0 <= action < _ACTION_COUNT:
        raise ValueError(f"{source}: qtable entry {key!r} has out-of-range action index {action}")
    return action
