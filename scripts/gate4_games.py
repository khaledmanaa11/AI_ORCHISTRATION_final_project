"""Runs the GATE-4 seeded two-peer games and extracts every per-game number
straight from the real `AgentContext`s and event-log JSONL that
`play_two_peer_game` (04-12's own harness, RESUME.md carry-over W) produces
-- no bespoke instrumentation added to `src/` (04-14-PLAN.md must_haves:
"the measurement describes the shipped game and not a special build").
"""

from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from gate4_beliefspy import BeliefDeltaLog, spy_belief_deltas  # noqa: E402
from gate4_mockprovider import wire_mocked_provider  # noqa: E402

from pursuit.network.agent_wiring import AgentConfig, load_agent_config  # noqa: E402
from pursuit.shared.hint_guard import assert_no_coordinates  # noqa: E402
from tests.integration.two_peer_game import play_two_peer_game  # noqa: E402

_CFG_A_DIR = "config/police"
_CFG_B_DIR = "config/thief"

#: Fixed, arbitrary seeds for the measurement's own seeded set -- distinct
#: from the production belief.seed (20260809) so this run never accidentally
#: replays a real graded game's RNG stream. Reproducible by construction:
#: rerunning --mocked with these same seeds must reproduce the same numbers.
GATE4_SEEDS: tuple[int, ...] = (30260801, 30260802, 30260803)


def _with_seed(cfg: AgentConfig, seed: int) -> AgentConfig:
    toggle = dataclasses.replace(cfg.belief.belief, seed=seed)
    return dataclasses.replace(cfg, belief=dataclasses.replace(cfg.belief, belief=toggle))


def _with_belief_enabled(cfg: AgentConfig, enabled: bool) -> AgentConfig:
    toggle = dataclasses.replace(cfg.belief.belief, enabled=enabled)
    return dataclasses.replace(cfg, belief=dataclasses.replace(cfg.belief, belief=toggle))


@dataclass
class GameMeasurement:
    seed: int
    belief_enabled: bool
    outcome: str
    turns_completed: int
    per_turn_seconds: list[float]
    hints_total: int
    hints_word_counts: list[int]
    intent_counts: dict
    coordinate_leaks: int
    token_spend: dict
    served_model: str | None
    belief: BeliefDeltaLog | None


def _events(log_path: Path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _language_turns(records: list[dict]) -> list[dict]:
    return [r for r in records if r["event"] == "language_turn"]


def _per_turn_wall_seconds(turns: list[dict]) -> list[float]:
    """Consecutive-turn wall-clock deltas, straight from the JSONL's own
    ISO-8601 `timestamp` field -- no separate stopwatch instrumentation."""
    stamps = [datetime.fromisoformat(r["timestamp"]) for r in turns]
    return [(stamps[i] - stamps[i - 1]).total_seconds() for i in range(1, len(stamps))]


def _coordinate_leaks(records: list[dict]) -> int:
    leaks = 0
    for record in records:
        if record["event"] == "language_turn":
            try:
                assert_no_coordinates(record["outgoing_hint"]["text"])
            except ValueError:
                leaks += 1
        elif record["event"] == "message_sent" and record["envelope"].get("type") == "move":
            payload = record["envelope"].get("payload", {})
            if "x" in payload or "y" in payload:
                leaks += 1
    return leaks


async def run_one_game(
    *, seed: int, belief_enabled: bool, mocked: bool, spy: bool = True
) -> GameMeasurement:
    """One real two-peer game (`play_two_peer_game`), seeded and configured
    for exactly one (seed, belief_enabled) cell of the measurement's grid."""
    cfg_a = _with_belief_enabled(_with_seed(load_agent_config(_CFG_A_DIR), seed), belief_enabled)
    cfg_b = _with_belief_enabled(_with_seed(load_agent_config(_CFG_B_DIR), seed), belief_enabled)
    wire = wire_mocked_provider if mocked else None
    belief_log = BeliefDeltaLog()
    do_spy = spy and belief_enabled

    with tempfile.TemporaryDirectory() as tmp:
        log_dir = Path(tmp)
        game_uid = f"gate4-{seed}-{belief_enabled}-{mocked}"
        if do_spy:
            with spy_belief_deltas(belief_log):
                outcome_a, outcome_b, ctx_a, _ = await play_two_peer_game(
                    cfg_a, cfg_b, game_uid=game_uid, log_dir=log_dir, wire=wire
                )
        else:
            outcome_a, outcome_b, ctx_a, _ = await play_two_peer_game(
                cfg_a, cfg_b, game_uid=game_uid, log_dir=log_dir, wire=wire
            )
        assert outcome_a == outcome_b, "rules 46-48: both sides must agree on the ending"

        records = _events(log_dir / "a.jsonl")
        turns = _language_turns(records)
        word_counts = [len(r["outgoing_hint"]["text"].split()) for r in turns]
        intent_counts = {"truth": 0, "lie": 0}
        for r in turns:
            intent_counts[r["outgoing_hint"]["intent"]] += 1

        provider = ctx_a.language.decode_context.provider if ctx_a.language else None
        served_model = getattr(provider, "served_model", None)
        if mocked:
            # RecordedResponseProvider bypasses AnthropicProvider entirely,
            # so the real gatekeeper.budget never sees a call -- read the
            # mocked provider's own (clearly-labelled-simulated) counters.
            token_spend = provider.report() if provider is not None else {}
        else:
            token_spend = ctx_a.language.gatekeeper.budget.report() if ctx_a.language else {}

    return GameMeasurement(
        seed=seed,
        belief_enabled=belief_enabled,
        outcome=outcome_a.value,
        turns_completed=ctx_a.state.turn,
        per_turn_seconds=_per_turn_wall_seconds(turns),
        hints_total=len(turns),
        hints_word_counts=word_counts,
        intent_counts=intent_counts,
        coordinate_leaks=_coordinate_leaks(records),
        token_spend=token_spend,
        served_model=served_model,
        belief=belief_log if do_spy else None,
    )


async def run_seeded_set(*, mocked: bool) -> dict:
    """Belief ON and OFF, every seed in GATE4_SEEDS, mocked or live."""
    games: dict = {"belief_on": [], "belief_off": []}
    for seed in GATE4_SEEDS:
        games["belief_on"].append(
            await run_one_game(seed=seed, belief_enabled=True, mocked=mocked)
        )
        games["belief_off"].append(
            await run_one_game(seed=seed, belief_enabled=False, mocked=mocked, spy=False)
        )
    return games


def cop_win_rate(games: list[GameMeasurement]) -> float:
    from pursuit.constants import Outcome

    if not games:
        return 0.0
    wins = sum(1 for g in games if g.outcome == Outcome.CAPTURE.value)
    return wins / len(games)
