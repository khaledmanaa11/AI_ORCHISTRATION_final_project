"""Builds `artifacts/token_cost/token_cost.json` and renders the block
`docs/TOKEN-COST.md` publishes (08-09).

    uv run python scripts/token_cost_report.py            # write the artifact
    uv run python scripts/token_cost_report.py --render   # print the markdown

The document does not carry a number this file did not produce.
`tests/unit/test_research_docs.py` re-renders from the committed artifact
and compares against the committed document, so hand-editing a figure into
`docs/TOKEN-COST.md` fails the suite rather than reaching a grader.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _path in (str(_REPO_ROOT), str(_REPO_ROOT / "scripts")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from token_cost_prompts import calibration, prompt_sizes  # noqa: E402
from token_cost_read import (  # noqa: E402
    GAME_PARAMS,
    LANGUAGE_CONFIG,
    budget_config,
    compare_call_rate,
    live_spend,
    mocked_spend,
    project,
    read_json,
)

OUT_PATH = _REPO_ROOT / "artifacts" / "token_cost" / "token_cost.json"
BEGIN = "<!-- BEGIN GENERATED: token-cost -->"
END = "<!-- END GENERATED: token-cost -->"


def build() -> dict:
    """Every derived figure, from tracked evidence only."""
    live, mocked, config = live_spend(), mocked_spend(), budget_config()
    language, params = read_json(LANGUAGE_CONFIG), read_json(GAME_PARAMS)
    sizes = prompt_sizes(
        arena=language["model"]["game_arena"],
        board_size=params["board_size"],
        word_limit=language["model"]["hint_word_limit"],
        max_tokens=language["model"]["max_tokens"],
    )
    return {
        "live": live, "mocked": mocked, "config": config,
        "call_rate_comparison": compare_call_rate(live, mocked),
        "projection": project(live, config),
        "prompt_sizes": sizes,
        "estimator_calibration": calibration(sizes, live),
    }


def _measured_table(data: dict) -> list:
    live, cmp_ = data["live"], data["call_rate_comparison"]
    return [
        "| Measured, one live game | Value | Where from |",
        "|---|---:|---|",
        f"| served model | `{live['served_model']}` | `{live['source']}` |",
        f"| turns played (ended in {live['outcome']}) | {live['turns']} | same |",
        f"| provider calls | {live['calls']} | same |",
        f"| input tokens | {live['input_tokens']:,} | `response.usage` |",
        f"| output tokens | {live['output_tokens']:,} | `response.usage` |",
        f"| **input share of spend** | **{live['input_share']:.1%}** | derived |",
        f"| tokens per call | {live['tokens_per_call']:.1f} | derived |",
        f"| tokens per turn | {live['tokens_per_turn']:.1f} | derived |",
        f"| calls per turn | {live['calls_per_turn']:.3f} | derived |",
        f"| cost | ${live['cost_usd']:.6f} | `gate4_report.token_cost_usd` |",
        f"| effective $/M tokens | ${live['usd_per_million_tokens']:.4f} | derived |",
        f"| calls per turn, 3 MOCKED games | {cmp_['calls_per_turn_mocked']:.3f} "
        f"(ratio {cmp_['calls_per_turn_ratio']:.3f}) | `{data['mocked']['source']}` |",
        f"| tokens per call, live / mocked | **{cmp_['tokens_per_call_ratio']:.2f}x** "
        "| the mock's counts are SIMULATED |",
    ]


def _projection_table(data: dict) -> list:
    proj, config = data["projection"], data["config"]
    fits = "**NO**" if not proj["max_games_fits_budget"] else "yes"
    return [
        "| Projected to a full-length game and a series | Value |",
        "|---|---:|",
        f"| move ceiling scaled to | {config['move_ceiling']} turns |",
        f"| tokens per full-length game | {proj['tokens_per_full_game']:,.0f} |",
        f"| cost per full-length game | ${proj['usd_per_full_game']:.5f} |",
        f"| series budget (Table 18 row 4, negotiable) | {config['token_budget_per_series']:,} |",
        f"| full-length games the budget covers | {proj['games_within_budget']:.2f} |",
        f"| games before `SHORT_PROMPT` ({config['short_prompt_threshold_tokens']:,}) "
        f"| {proj['games_before_short_prompt']:.2f} |",
        f"| games before `TEMPLATE_ONLY` ({config['template_only_threshold_tokens']:,}) "
        f"| {proj['games_before_template_only']:.2f} |",
        f"| tokens for {proj['max_games_per_team']} games (Table 18 row 5, FIXED) "
        f"| {proj['tokens_for_max_games']:,.0f} |",
        f"| **does the maximum series fit the budget?** | {fits} |",
    ]


def _prompt_table(data: dict) -> list:
    sizes, cal = data["prompt_sizes"], data["estimator_calibration"]
    sample = sizes["hint_sample"]
    return [
        "| Where the input goes | decode call | bluff call |",
        "|---|---:|---:|",
        f"| system prompt, characters | {sizes['decode']['system_chars']:,} "
        f"| {sizes['bluff']['system_chars']:,} |",
        f"| user half, mean characters | {sizes['decode']['user_chars_mean']:.1f} "
        f"| {sizes['bluff']['user_chars_mean']:.1f} |",
        "| **system share of input characters** "
        f"| **{sizes['decode']['system_share_of_input_chars']:.1%}** "
        f"| **{sizes['bluff']['system_share_of_input_chars']:.1%}** |",
        f"| shipped estimate, tokens reserved | {sizes['decode']['estimated_tokens_mean']:.1f} "
        f"| {sizes['bluff']['estimated_tokens_mean']:.1f} |",
        "",
        f"Hint sample: **{sample['n']}** real sentences from tracked `{sample['source']}` "
        f"wire logs, mean {sample['mean_chars']:.1f} characters, max {sample['max_chars']}.",
        "",
        "| Estimator calibration (`_estimate_tokens`) | Value |",
        "|---|---:|",
        f"| estimated tokens per call | {cal['estimated_tokens_per_call']:.1f} |",
        f"| measured tokens per call | {cal['measured_tokens_per_call']:.1f} |",
        f"| **estimate / measured** | **{cal['ratio_estimate_over_measured']:.2f}x** |",
        f"| `max_tokens` ceiling as a share of the estimate "
        f"| {cal['output_ceiling_share_of_estimate']:.1%} |",
        f"| measured output tokens per call | {cal['measured_output_per_call']:.1f} |",
        f"| sample | {cal['sample']} |",
    ]


def render(data: dict) -> str:
    """The generated block, between its two markers."""
    lines = [BEGIN, ""]
    for table in (_measured_table(data), _projection_table(data), _prompt_table(data)):
        lines.extend(table)
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main(argv=None) -> int:
    """Write the artifact, or print the block the document embeds."""
    parser = argparse.ArgumentParser(description="Token-cost analysis from recorded spend")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args(argv)

    data = build()
    if args.render:
        print(render(data))
        return 0
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"token-cost analysis -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
