"""The publishable file set for a split repository (08-10, D-76/D-77).

EVERY COUNT IS ASSERTED, never just an exit code. The failure mode this whole
plan is written against is a gate that reports OK for having looked at nothing:
`check_line_limit.sh`'s no-argument form enumerates through `git ls-files`, which
is EMPTY in a freshly `git init`ed tree, so it exits 0 having scanned zero files.
A manifest builder has the same shape, so the tests below assert the SIZE of what
was enumerated and the SIZE of what was subtracted.

THE COUNTER EXCLUSION IS TESTED ON A PLANTED INPUT. `config/*/games_played.json`
is gitignored, so the real tracked set never contains it and a test that only
looked at the real set would pass without the exclusion existing at all.
"""

from __future__ import annotations

import pytest

from tests.unit.submission_gate_helpers import REPO_ROOT, load

manifest_mod = load("split_manifest")

COUNTERS = (
    "config/police/games_played.json",
    "config/police/games_played.prev.json",
    "config/thief/games_played.json",
    "config/thief/games_played.prev.json",
)


def test_tracked_paths_enumerates_the_real_repository() -> None:
    paths = manifest_mod.tracked_paths(REPO_ROOT)
    assert len(paths) > 900, f"only {len(paths)} tracked paths -- enumeration looked at nothing"
    assert "README.md" in paths
    assert "config/police/game_params.json" in paths
    assert ".env" not in paths
    assert "police_thief_p2p.pdf" not in paths


@pytest.mark.parametrize("counter", COUNTERS)
def test_every_counter_shape_is_excluded(counter: str) -> None:
    assert manifest_mod.exclusion_reason(counter), f"{counter} would be published"


@pytest.mark.parametrize(
    "kept", ["config/police/role.json", "config/thief/league.json", "src/pursuit/__init__.py"]
)
def test_ordinary_paths_are_not_excluded(kept: str) -> None:
    assert manifest_mod.exclusion_reason(kept) == ""


def test_build_manifest_subtracts_planted_counters() -> None:
    planted = ("README.md", "config/police/role.json", *COUNTERS)
    result = manifest_mod.build_manifest(planted)
    assert result.count == 2, f"included {result.included}"
    assert set(result.included) == {"README.md", "config/police/role.json"}
    assert len(result.excluded) == len(COUNTERS)
    assert {path for path, _ in result.excluded} == set(COUNTERS)
    assert all(reason for _, reason in result.excluded)


@pytest.mark.parametrize("forbidden", [".env", "police_thief_p2p.pdf", "docs/.env"])
def test_a_tracked_forbidden_path_raises_rather_than_being_filtered(forbidden: str) -> None:
    with pytest.raises(manifest_mod.ForbiddenPathError) as excinfo:
        manifest_mod.build_manifest(("README.md", forbidden))
    assert forbidden in str(excinfo.value)


def test_an_empty_input_raises_instead_of_producing_an_empty_repository() -> None:
    with pytest.raises(manifest_mod.EmptyManifestError):
        manifest_mod.build_manifest(())


def test_a_manifest_of_only_counters_raises_too() -> None:
    with pytest.raises(manifest_mod.EmptyManifestError):
        manifest_mod.build_manifest(COUNTERS)


def test_the_real_manifest_ships_both_role_config_directories() -> None:
    result = manifest_mod.manifest_for(REPO_ROOT)
    per_role = manifest_mod.role_config_files(result)
    assert set(per_role) == set(manifest_mod.ROLES)
    for role, files in per_role.items():
        assert len(files) >= 14, f"{role} ships only {len(files)} config files"
        assert not [path for path in files if "games_played" in path]


def test_the_real_manifest_is_large_and_carries_the_rule_50_floor() -> None:
    result = manifest_mod.manifest_for(REPO_ROOT)
    assert result.count > 900, f"manifest holds {result.count} paths"
    for required in ("README.md", "LICENSE", "pyproject.toml", ".env-example"):
        assert required in result.included
    assert [path for path in result.included if path.startswith("docs/PRD")]
    assert [path for path in result.included if path.startswith("tests/")]
