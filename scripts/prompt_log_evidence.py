"""Measures what the shipped prompts actually produced, per remote round
(08-09, Segal Sec8.3 "sample outputs received, iterative refinements").

    uv run python scripts/prompt_log_evidence.py            # print the block

Every sentence counted here was really sent over the wire and is in the
tracked `docs/phases/phase-5/remote-round-*/` logs. That makes one prompt
revision measurable rather than asserted: `bluff_prompt.py`'s system prompt
was rewritten on 2026-08-14 (`50ac2fe`) after a hint arrived in the THIRD
PERSON, and the rounds either side of that date are both on disk.

THE THIRD-PERSON TEST IS A NARROW MECHANICAL PROXY and the document says so
where it prints the number. It matches a sentence whose SUBJECT is a named
third party ("The player is ...", "They are ..."); it does not judge grammar
and it would not catch a subtler drift. It is reported because it is exactly
the failure the revision targeted, not because it is a complete measure of
prompt quality.

`scripts/` is on neither the coverage list nor the 150-line glob, so this
file is split by hand and checked explicitly by path, like its `gate7_*`
and `submission_*` siblings.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUND_ROOT = "docs/phases/phase-5"
HINT_ENVELOPE = "hint"
#: PARAMETERS.md Table 14 row 2, negotiable, our shipped value. Read from
#: config rather than typed, by `word_limit()` below.
LANGUAGE_CONFIG = "config/police/language.json"
#: A sentence ABOUT a third party rather than about the speaker.
_THIRD_PERSON = re.compile(r"^\s*(the\s+(player|agent|thief|cop|opponent)|they|he|she)\b", re.I)
#: Rule: "Never include a number that could be read as a board coordinate."
_DIGIT = re.compile(r"\d")
BEGIN = "<!-- BEGIN GENERATED: prompt-evidence -->"
END = "<!-- END GENERATED: prompt-evidence -->"


def word_limit() -> int:
    """The negotiated hint word limit the prompt is parameterised by."""
    config = json.loads((REPO_ROOT / LANGUAGE_CONFIG).read_text(encoding="utf-8"))
    return int(config["model"]["hint_word_limit"])


def hint_rounds() -> dict:
    """Per remote round: every hint sentence it carried, in file order."""
    rounds: dict = {}
    root = REPO_ROOT / ROUND_ROOT
    for path in sorted(root.rglob("*.jsonl")):
        if path.name.endswith(".ledger.jsonl"):
            continue
        name = path.relative_to(root).parts[0]
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            envelope = record.get("envelope") or {}
            if envelope.get("type") != HINT_ENVELOPE:
                continue
            text = (envelope.get("payload") or {}).get("text")
            if text:
                rounds.setdefault(name, {"texts": [], "first_seen": record.get("timestamp", "")})
                rounds[name]["texts"].append(text)
    if not rounds:
        raise ValueError(
            f"no hint envelopes under {ROUND_ROOT} -- refusing to report a "
            "prompt's behaviour over an empty sample"
        )
    return {name: _score(data) for name, data in sorted(rounds.items())}


def _score(data: dict) -> dict:
    """One round's counts. `texts` is kept so a reader can check the calls."""
    texts = data["texts"]
    words = [len(text.split()) for text in texts]
    third = [text for text in texts if _THIRD_PERSON.match(text)]
    return {
        "date": data["first_seen"][:10],
        "hints": len(texts),
        "third_person": len(third),
        "third_person_examples": third,
        "max_words": max(words),
        "mean_words": sum(words) / len(words),
        "with_digits": sum(1 for text in texts if _DIGIT.search(text)),
        "texts": texts,
    }


def render(rounds: dict, limit: int) -> str:
    """The generated block `docs/PROMPT_LOG.md` embeds."""
    total = sum(entry["hints"] for entry in rounds.values())
    drift = sum(entry["third_person"] for entry in rounds.values())
    lines = [
        BEGIN, "",
        f"**{total}** hint sentences really sent, across **{len(rounds)}** remote rounds "
        f"in tracked `{ROUND_ROOT}/` wire logs. Word limit in force: **{limit}** "
        "(`config/police/language.json`, Table 14 row 2, negotiable).",
        "",
        "| Round | Date | Hints | Third-person subject | Max words | Mean words | "
        "Contains a digit |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name, entry in rounds.items():
        lines.append(
            f"| `{name}` | {entry['date']} | {entry['hints']} | {entry['third_person']} "
            f"| {entry['max_words']} | {entry['mean_words']:.1f} | {entry['with_digits']} |"
        )
    lines += ["", f"Totals: **{drift}** third-person sentence(s) in {total}; "
              f"**{max(entry['max_words'] for entry in rounds.values())}** words is the "
              f"longest sentence ever sent, against a limit of {limit}."]
    for name, entry in rounds.items():
        for example in entry["third_person_examples"]:
            lines.append(f"- The one drift, in `{name}`: *\"{example}\"*")
    return "\n".join([*lines, "", END])


def main(argv=None) -> int:
    """Print the block, so the document is never hand-typed."""
    print(render(hint_rounds(), word_limit()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
