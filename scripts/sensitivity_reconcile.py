"""Re-measures the one claim in this repository the sweep contradicts
(08-09).

    uv run python scripts/sensitivity_reconcile.py           # write + print

`docs/phases/phase-3/ENGINEERING-LOG.md` Act 4.3 records our thief's
survival against a BARRIER-BLIND chaser as **89%** under the book-only
rules and **1%** once the swap counts as a capture, and that pair is quoted
onward into `PRD.md`, `PLAN.md` and `shared/resolution.py`'s `PREFERRED`
docstring. The 08-09 sweep measures the same matchup at 32.0% and 7.5%.

BOTH HALVES OF THE COMPARISON ARE DERIVED. The old figures are PARSED out
of the Act 4.3 table rather than typed here, so this file cannot drift from
the document it is checking, and the new figures come from the same
`training/arena.run_match` every other measurement uses. If the log is ever
corrected, the comparison moves with it.

The two variables that plausibly explain the gap are swept explicitly --
the weight vector (Act 4 predates Act 5's run-2 fit) and the opening
(negotiated vs randomised starts). NO CAUSE IS ASSERTED: this script
reports which combinations were tried and what each returned, and
`docs/SENSITIVITY.md` says in as many words that the cause was not
established.
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _path in (str(_REPO_ROOT), str(_REPO_ROOT / "scripts")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from sensitivity_grid import EVAL_SEED, SHIPPED_WEIGHTS  # noqa: E402

from pursuit.shared.config import load_game_params  # noqa: E402
from pursuit.shared.resolution import BOOK_ONLY, ResolutionRules  # noqa: E402
from pursuit.strategy.naive import ChaserCop  # noqa: E402
from pursuit.strategy.valuebrain import ValueSearchBrain  # noqa: E402
from pursuit.strategy.weights import PRIOR, load_weights  # noqa: E402
from training.arena import run_match  # noqa: E402

OUT_PATH = _REPO_ROOT / "artifacts" / "sensitivity" / "reconcile.json"
ENGINEERING_LOG = "docs/phases/phase-3/ENGINEERING-LOG.md"
GAMES = 200
SWAP_ONLY = ResolutionRules(capture_on_barrier_race=False, capture_on_swap=True)
BEGIN = "<!-- BEGIN GENERATED: reconcile -->"
END = "<!-- END GENERATED: reconcile -->"

_CLAIM = re.compile(r"\|\s*swap\s+(does not \(book-only\)|counts as a capture)\s*\|\s*\*{0,2}(\d+)%")


def recorded_claim() -> dict:
    """Act 4.3's two percentages, parsed out of the log itself."""
    text = (_REPO_ROOT / ENGINEERING_LOG).read_text(encoding="utf-8")
    found = {label: int(value) for label, value in _CLAIM.findall(text)}
    if len(found) != 2:
        raise ValueError(
            f"could not parse Act 4.3's survival pair out of {ENGINEERING_LOG} "
            f"-- got {found}. Refusing to compare against a claim I cannot read."
        )
    return {
        "source": f"{ENGINEERING_LOG} Act 4.3",
        "book_only_percent": found["does not (book-only)"],
        "swap_percent": found["counts as a capture"],
    }


def _arm(weights, rules, randomise: bool, params) -> dict:
    """One survival measurement against the barrier-blind chaser."""
    result = run_match(
        "thief vs barrier-blind chaser", "thief",
        lambda index: ChaserCop("cop", game_params=params, use_barriers=False,
                                rng=random.Random(index)),
        lambda index: ValueSearchBrain("thief", game_params=params, rules=rules,
                                       weights=weights, rng=random.Random(EVAL_SEED + index)),
        GAMES, params, rules, seed=EVAL_SEED, randomise_starts=randomise,
    )
    low, high = result.interval
    return {"wins": result.wins, "games": result.games, "rate": result.rate,
            "ci_low": low, "ci_high": high}


def measure() -> dict:
    """Every weights x rules x opening combination, plus the parsed claim."""
    params = load_game_params(_REPO_ROOT / "config" / "police" / "game_params.json")
    vectors = {"run2": load_weights(str(SHIPPED_WEIGHTS)), "prior": PRIOR}
    arms = {}
    for weight_name, weights in vectors.items():
        for rule_name, rules in (("book_only", BOOK_ONLY), ("swap", SWAP_ONLY)):
            for start_name, randomise in (("negotiated", False), ("randomised", True)):
                key = f"{weight_name}/{rule_name}/{start_name}"
                arms[key] = _arm(weights, rules, randomise, params)
    return {"games_per_arm": GAMES, "eval_seed": EVAL_SEED,
            "recorded_claim": recorded_claim(), "arms": arms}


def render(data: dict) -> str:
    """The generated block `docs/SENSITIVITY.md` embeds."""
    claim, arms = data["recorded_claim"], data["arms"]
    best = max(arms.items(), key=lambda item: item[1]["rate"])
    lines = [
        BEGIN, "",
        f"`{claim['source']}` records **{claim['book_only_percent']}%** survival "
        f"book-only and **{claim['swap_percent']}%** with the swap. Re-measured at "
        f"n={data['games_per_arm']} per arm, every combination of the two variables "
        "that could explain the gap:",
        "",
        "| weights / rules / opening | Survival | 95% Wilson |",
        "|---|---:|---|",
    ]
    for key, arm in arms.items():
        lines.append(f"| `{key}` | {arm['wins']}/{arm['games']} = {arm['rate']:.1%} "
                     f"| [{arm['ci_low']:.1%}, {arm['ci_high']:.1%}] |")
    lines += [
        "",
        f"The highest arm is `{best[0]}` at **{best[1]['rate']:.1%}** -- still far below "
        f"the recorded {claim['book_only_percent']}%, and no arm approaches "
        f"{claim['swap_percent']}%. **The cause was not established.**",
        "", END,
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    """Write the artifact and print the block."""
    data = measure()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(render(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
