"""GATE-4 criterion 2: the locked scent decay law, verified against the
shipped `ScentField`/`strategy/scent.py` module (not a special build), plus
the handshake scent-digest match both peers would compute (04-14 Task 1,
D-46/D-50, rule 23).

The network event log carries no per-turn scent-field snapshot (04-12
logs `belief_entropy`/`belief_argmax`/`reliability`, not the scent grids
themselves), so this measurement instead drives the REAL production
`ScentField`/`scent.py` functions directly with the locked, loaded
`scent.json` model -- the exact objects the real game mutates every turn --
rather than re-deriving the law by hand. See docs/phases/phase-4/
GATE-4-MEASUREMENT.md for why this is the faithful reading of "extracted
from the shipped game, not a special build" for a quantity the JSONL does
not carry.
"""

from __future__ import annotations

from dataclasses import dataclass

from pursuit.network.agent_wiring import AgentConfig
from pursuit.shared.scent_config import scent_digest
from pursuit.strategy import scent
from pursuit.strategy.scentfield import ScentField

#: >= the plan's own "10 turns" floor (must_haves #2).
_DECAY_ONLY_TURNS = 12
_SOURCE_CELL = (3, 3)
_PROBE_BOARD_SIZE = 7


@dataclass(frozen=True)
class ScentDecayResult:
    turns: int
    max_deviation: float
    per_turn: list[dict]


def measure_decay_law(cfg: AgentConfig) -> ScentDecayResult:
    """Emit once at `_SOURCE_CELL`, decay-only for `_DECAY_ONLY_TURNS`
    turns (no re-emission), and compare the shipped `ScentField`'s own
    reading at the source cell against the closed-form
    `scent.expected_strength_after()` -- the same locked model object the
    real handshake digest covers (D-46, D-50)."""
    field = ScentField(model=cfg.scent, board_size=_PROBE_BOARD_SIZE)
    field.emit_own(_SOURCE_CELL)
    per_turn: list[dict] = []
    max_deviation = 0.0
    for turn in range(1, _DECAY_ONLY_TURNS + 1):
        field.advance()
        actual = field.strength("own", _SOURCE_CELL)
        expected = scent.expected_strength_after(cfg.scent, turn)
        deviation = abs(actual - expected)
        max_deviation = max(max_deviation, deviation)
        per_turn.append(
            {"turn": turn, "actual": actual, "expected": expected, "deviation": deviation}
        )
    return ScentDecayResult(turns=_DECAY_ONLY_TURNS, max_deviation=max_deviation, per_turn=per_turn)


@dataclass(frozen=True)
class HandshakeDigestResult:
    matched: bool
    police_digest: str
    thief_digest: str


def measure_handshake_digest(cfg_a: AgentConfig, cfg_b: AgentConfig) -> HandshakeDigestResult:
    """The exact digest both real peers compute and exchange at handshake
    (`agent_lifecycle.default_context`/`run_agent`, D-46) -- reused
    directly rather than re-derived, so this can never disagree with what
    a real handshake actually checks (`handshake_evaluate.compare_named_digest`)."""
    digest_a = scent_digest(cfg_a.scent)
    digest_b = scent_digest(cfg_b.scent)
    return HandshakeDigestResult(matched=digest_a == digest_b, police_digest=digest_a, thief_digest=digest_b)
