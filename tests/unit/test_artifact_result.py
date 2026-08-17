"""`result_<game_id>.json`: one file per SERIES, and rule 54's TWO numbers.

THE REPORT-07 TEST IS `test_the_series_total_is_the_sum_of_two_sub_games`, and
it drives TWO sub-games on purpose. With one game played, the per-game and the
per-series totals are equal, so a single-game test cannot tell an accumulator
from an implementation that writes `budget.report()` into both slots -- it
passes either way. The assertion is STRICT (`>` each game, `==` their sum), not
`>=`, for the same reason.
"""

from __future__ import annotations

import json

from pursuit.services.llm.budget import TokenBudget
from pursuit.services.reporting.artifact_result import (
    ResultArtifactField,
    SubGameField,
    TokensField,
    read_series,
    record_sub_game,
    verify_result_artifact,
)
from pursuit.services.reporting.artifacts import ArtifactField, result_filename
from pursuit.services.reporting.result_agreement import AgreementRecord

GAME_ID = "seriesone"
COMMIT_A = "0123456789abcdef0123456789abcdef01234567"
COMMIT_B = "89abcdef0123456789abcdef0123456789abcdef"

# Test scaffolding only -- NOT docs/PARAMETERS.md values. `TokenBudget` takes
# its three thresholds keyword-only and required, and none of them affects the
# `report()` figures this file sums.
_CEILING, _SHORT, _TEMPLATE = 1_000_000, 500_000, 900_000
GAME_ONE_TOKENS = (100, 40)
GAME_TWO_TOKENS = (7, 3)

AGREEMENT = AgreementRecord(
    own_outcome="capture", peer_outcome="capture", peer_claim_present=True,
    audit_verdict={"matched": True, "turn": 5}, agreed=True, reason="agree",
).to_dict()


def _budget(input_tokens: int, output_tokens: int) -> TokenBudget:
    budget = TokenBudget(
        token_budget=_CEILING, short_prompt_threshold=_SHORT, template_only_threshold=_TEMPLATE,
    )
    budget.settle(
        input_tokens=input_tokens, output_tokens=output_tokens, estimated_tokens=0,
    )
    return budget


def _record(artifact_dir, *, index, budget, commit_hash=COMMIT_A, game_id=GAME_ID):
    return record_sub_game(
        artifact_dir, game_uid=game_id, game_id=game_id, role="police",
        sub_game_index=index, agreement=AGREEMENT, budget=budget,
        commit_hash=commit_hash, log_artifact=f"log_{game_id}_g{index:02d}.json",
    )


def test_the_series_total_is_the_sum_of_two_sub_games(tmp_path):
    """REPORT-07 / rule 54. Two games, ONE series file."""
    first, _ = _record(tmp_path, index=1, budget=_budget(*GAME_ONE_TOKENS))
    second, path = _record(
        tmp_path, index=2, budget=_budget(*GAME_TWO_TOKENS), commit_hash=COMMIT_B,
    )

    game_one = first[ResultArtifactField.SUB_GAMES][0][SubGameField.TOKENS]
    game_two = second[ResultArtifactField.SUB_GAMES][1][SubGameField.TOKENS]
    series = second[ResultArtifactField.SERIES_TOKENS]
    assert game_one[TokensField.TOTAL_TOKENS] == sum(GAME_ONE_TOKENS)
    assert game_two[TokensField.TOTAL_TOKENS] == sum(GAME_TWO_TOKENS)

    assert series[TokensField.TOTAL_TOKENS] > game_one[TokensField.TOTAL_TOKENS]
    assert series[TokensField.TOTAL_TOKENS] > game_two[TokensField.TOTAL_TOKENS]
    assert series[TokensField.TOTAL_TOKENS] == (
        game_one[TokensField.TOTAL_TOKENS] + game_two[TokensField.TOTAL_TOKENS]
    )
    assert series[TokensField.INPUT_TOKENS] == GAME_ONE_TOKENS[0] + GAME_TWO_TOKENS[0]
    assert series[TokensField.OUTPUT_TOKENS] == GAME_ONE_TOKENS[1] + GAME_TWO_TOKENS[1]
    assert series[TokensField.GAMES_MEASURED] == 2
    assert len(second[ResultArtifactField.SUB_GAMES]) == 2
    assert path.name == result_filename(GAME_ID)
    assert "_g" not in path.name, "docs/PARAMETERS.md:168 -- result_ carries NO _g<NN>"


def test_the_second_rewrite_leaves_the_first_generation_in_prev(tmp_path):
    """`.prev` is the crash window's readable generation (durable_write.py)."""
    _record(tmp_path, index=1, budget=_budget(*GAME_ONE_TOKENS))
    _, path = _record(tmp_path, index=2, budget=_budget(*GAME_TWO_TOKENS))

    prev = path.with_name(f"{path.stem}.prev{path.suffix}")
    assert prev.exists()
    rotated = json.loads(prev.read_text(encoding="utf-8"))
    assert len(rotated[ResultArtifactField.SUB_GAMES]) == 1
    assert rotated[ResultArtifactField.SERIES_TOKENS][TokensField.TOTAL_TOKENS] == sum(
        GAME_ONE_TOKENS
    )


def test_a_game_without_the_language_layer_reports_absence_never_zero(tmp_path):
    """`ctx.language is None` -> an honest marker. The assertion that matters is
    that the field is NOT `0`: a fabricated zero reads as a measurement."""
    artifact, _ = _record(tmp_path, index=1, budget=None)
    tokens = artifact[ResultArtifactField.SUB_GAMES][0][SubGameField.TOKENS]

    assert tokens[TokensField.PRESENT] is False
    # `tokens != 0` was the first draft and it is vacuous -- a dict never
    # equals an int. The check that means something is that NO count appears
    # at all, so there is no zero for a reader to mistake for a measurement.
    # `bool` is excluded explicitly: `present: False` IS `0` under `==`, and
    # the second draft of this line failed on exactly that.
    counts = [v for v in tokens.values() if isinstance(v, int) and not isinstance(v, bool)]
    assert counts == []
    assert TokensField.TOTAL_TOKENS not in tokens
    assert TokensField.INPUT_TOKENS not in tokens
    assert TokensField.DETAIL in tokens
    series = artifact[ResultArtifactField.SERIES_TOKENS]
    assert series[TokensField.GAMES_MEASURED] == 0, "an unmeasured game must not be counted"


def test_an_unmeasured_game_between_two_measured_ones_changes_nothing(tmp_path):
    """The series total absorbs no zero it did not measure."""
    _record(tmp_path, index=1, budget=_budget(*GAME_ONE_TOKENS))
    middle, _ = _record(tmp_path, index=2, budget=None)
    last, _ = _record(tmp_path, index=3, budget=_budget(*GAME_TWO_TOKENS))

    assert middle[ResultArtifactField.SERIES_TOKENS][TokensField.TOTAL_TOKENS] == sum(
        GAME_ONE_TOKENS
    )
    series = last[ResultArtifactField.SERIES_TOKENS]
    assert series[TokensField.TOTAL_TOKENS] == sum(GAME_ONE_TOKENS) + sum(GAME_TWO_TOKENS)
    assert series[TokensField.GAMES_MEASURED] == 2
    assert len(last[ResultArtifactField.SUB_GAMES]) == 3


def test_the_games_played_value_is_unset_and_says_why(tmp_path):
    """Rule 38. 07-00 fixed the mechanism; the VALUE is 07-10's human decision,
    so nothing here may write an integer into this slot."""
    artifact, _ = _record(tmp_path, index=1, budget=_budget(*GAME_ONE_TOKENS))
    declared = artifact[ResultArtifactField.GAMES_PLAYED_DECLARED]

    assert not isinstance(declared, int)
    assert declared[TokensField.PRESENT] is False
    detail = declared[TokensField.DETAIL]
    assert "GAMES-PLAYED-RECONSTRUCTION.md" in detail, "the reader is told where the value comes from"
    assert "declaration_" in detail, "and where this game's declared figure actually is"


def test_each_sub_game_carries_the_commit_hash_its_own_code_ran_on(tmp_path):
    """docs/PARAMETERS.md:152-153 mandatory rule 5: code may change between
    games, and every game's report names the commit it ran on."""
    _record(tmp_path, index=1, budget=_budget(*GAME_ONE_TOKENS), commit_hash=COMMIT_A)
    artifact, _ = _record(
        tmp_path, index=2, budget=_budget(*GAME_TWO_TOKENS), commit_hash=COMMIT_B,
    )
    hashes = [sub[SubGameField.COMMIT_HASH] for sub in artifact[ResultArtifactField.SUB_GAMES]]

    assert hashes == [COMMIT_A, COMMIT_B]
    assert artifact[ResultArtifactField.COMMIT_HASH] == COMMIT_B
    assert artifact[ArtifactField.GAME_ID] == GAME_ID


def test_the_written_artifact_verifies_its_own_seal(tmp_path):
    _, path = _record(tmp_path, index=1, budget=_budget(*GAME_ONE_TOKENS))
    assert verify_result_artifact(path)
    assert read_series(tmp_path, GAME_ID) == json.loads(path.read_text(encoding="utf-8"))
