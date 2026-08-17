"""Where a call's input tokens actually go, and how well the shipped
estimator predicts them (08-09).

The live game measured 505.8 INPUT tokens per call against 19.1 output.
That asymmetry is the whole optimization story, so this module measures the
two things that make it up: the SYSTEM prompts, which are rebuilt and
re-sent on every single call because Haiku 4.5's cacheable-prefix minimum
(4096 tokens) is far above anything either prompt needs -- a fact both
prompt modules already state in their docstrings -- and the USER half,
which for the decoder is one opponent sentence.

THE USER SENTENCES ARE REAL. All 79 come out of the tracked phase-5 wire
logs, so the decode-side figure is measured against traffic this project
actually received rather than against an invented example.

`_estimate_tokens` IS THE SHIPPED HEURISTIC, imported rather than
reimplemented. It is `chars // 4 + max_tokens` and it is what
`TokenBudget.reserve()` counts BEFORE a call runs, so if it is wrong the
degrade ladder trips at the wrong time. Comparing it against the one real
measurement is the only calibration this project has; n = 1 game and the
document says so.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.services.llm import bluff_prompt, decode_prompt
from pursuit.services.llm.anthropic_provider import _estimate_tokens
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.inference import Region

REPO_ROOT = Path(__file__).resolve().parent.parent
WIRE_LOG_ROOT = "docs/phases/phase-5"
HINT_ENVELOPE = "hint"


def tracked_hints() -> tuple:
    """Every hint sentence in the tracked phase-5 wire logs, in file order."""
    texts = []
    for path in sorted((REPO_ROOT / WIRE_LOG_ROOT).rglob("*.jsonl")):
        if path.name.endswith(".ledger.jsonl"):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            envelope = json.loads(line).get("envelope") or {}
            if envelope.get("type") == HINT_ENVELOPE:
                text = (envelope.get("payload") or {}).get("text")
                if text:
                    texts.append(text)
    if not texts:
        raise ValueError(
            f"no hint envelopes found under {WIRE_LOG_ROOT} -- refusing to "
            "report a prompt size over an empty sample"
        )
    return tuple(texts)


def _plan() -> DeceptionPlan:
    """A representative composed claim -- the only kind either policy builds."""
    return DeceptionPlan(
        intent=Intent.LIE, kind=ClaimKind.LOCATION,
        claimed_region=Region.NORTHEAST, true_region=Region.SOUTHWEST,
    )


def prompt_sizes(*, arena: str, board_size: int, word_limit: int, max_tokens: int) -> dict:
    """Both prompts' measured character size and their estimated reservation.

    Every argument comes from `config/police/language.json` and
    `game_params.json`; nothing here is a literal, so a config change moves
    these numbers and the regenerated document moves with it.
    """
    hints = tracked_hints()
    decode_system = decode_prompt.build_system_prompt(arena=arena, board_size=board_size)
    bluff_system = bluff_prompt.build_system_prompt(arena=arena, word_limit=word_limit)
    bluff_user = bluff_prompt.build_user_prompt(_plan())
    decode_users = [decode_prompt.build_user_prompt(text) for text in hints]
    decode_estimates = [
        _estimate_tokens(decode_system, user, max_tokens=max_tokens) for user in decode_users
    ]
    return {
        "hint_sample": {
            "n": len(hints), "source": WIRE_LOG_ROOT,
            "mean_chars": sum(len(text) for text in hints) / len(hints),
            "max_chars": max(len(text) for text in hints),
        },
        "decode": _leg(decode_system, decode_users, decode_estimates),
        "bluff": _leg(bluff_system, [bluff_user],
                      [_estimate_tokens(bluff_system, bluff_user, max_tokens=max_tokens)]),
        "max_tokens_reserved_per_call": max_tokens,
    }


def _leg(system: str, users: list, estimates: list) -> dict:
    """One call kind: the fixed system half, the variable user half."""
    mean_user = sum(len(user) for user in users) / len(users)
    return {
        "system_chars": len(system),
        "system_words": len(system.split()),
        "user_chars_mean": mean_user,
        "system_share_of_input_chars": len(system) / (len(system) + mean_user),
        "estimated_tokens_mean": sum(estimates) / len(estimates),
    }


def calibration(sizes: dict, live: dict) -> dict:
    """The shipped estimate against the one real per-call measurement.

    The estimate covers input AND the full `max_tokens` output ceiling, so
    it is compared against measured input + output per call, which is the
    same quantity `TokenBudget` accumulates.
    """
    estimated = (sizes["decode"]["estimated_tokens_mean"]
                 + sizes["bluff"]["estimated_tokens_mean"]) / 2
    measured = live["tokens_per_call"]
    return {
        "estimated_tokens_per_call": estimated,
        "measured_tokens_per_call": measured,
        "ratio_estimate_over_measured": estimated / measured,
        "output_ceiling_share_of_estimate": sizes["max_tokens_reserved_per_call"] / estimated,
        "measured_output_per_call": live["output_tokens"] / live["calls"],
        "sample": "one live game (n=1), 23 provider calls",
    }
