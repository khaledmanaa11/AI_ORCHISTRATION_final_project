"""The split-build driver, exercised end to end on a miniature repository (08-10).

A MINIATURE SOURCE REPO, NOT A MOCK. `build_one` is the piece where a mistake is
invisible in review and obvious on disk -- a banner that was never injected, a
provenance file that was written but never staged, a commit that picked up
something the manifest did not list. So the test builds a real git repository,
runs the real driver against it, and counts what landed.

THE DRIVER'S EXIT CONTRACT IS `check_submission.py`'s (D-82): 0 all rows pass,
1 any row fails, 2 nothing was built or nothing was checked. The refusal path --
a destination inside the source repository -- is asserted to return 2 AND to
leave nothing behind.
"""

from __future__ import annotations

import json
import subprocess

from tests.unit.submission_gate_helpers import REPO_ROOT, load

driver = load("build_split_repos")


def _mini_source(tmp_path):
    root = tmp_path / "mini"
    (root / "src").mkdir(parents=True)
    (root / "config" / "police").mkdir(parents=True)
    (root / "README.md").write_text("# Mini\n\nbody\n", encoding="utf-8")
    (root / "src" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "config" / "police" / "role.json").write_text("{}\n", encoding="utf-8")
    (root / "config" / "police" / "games_played.json").write_text("{}\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nauthors = [{ name = "A B", email = "a@b.c" }]\n', encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit",
                    "--no-verify", "-m", "seed"], cwd=root, check=True, capture_output=True)
    return root


def test_build_one_produces_a_committed_repository_with_the_banner(tmp_path) -> None:
    source = _mini_source(tmp_path)
    plan = driver.plan_build(source)
    built = driver.build_one(source, tmp_path / "out-police", "police", False, plan)
    dest = tmp_path / "out-police"
    assert built["copied"] == 4, built
    assert built["staged"] == 5, "the provenance document must be staged too"
    assert len(built["excluded"]) == 1
    assert built["excluded"][0]["path"] == "config/police/games_played.json"
    assert "<!-- split-repo-banner" in (dest / "README.md").read_text(encoding="utf-8")
    assert (dest / "docs" / "REPO-SPLIT.md").is_file()
    tracked = subprocess.run(["git", "ls-files"], cwd=dest, capture_output=True,
                             text=True, check=True).stdout.splitlines()
    assert len(tracked) == 5
    assert "config/police/games_played.json" not in tracked


def test_the_built_repository_has_one_commit_and_no_remote(tmp_path) -> None:
    source = _mini_source(tmp_path)
    driver.build_one(source, tmp_path / "out-thief", "thief", False, driver.plan_build(source))
    dest = tmp_path / "out-thief"
    count = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=dest,
                           capture_output=True, text=True, check=True).stdout.strip()
    remote = subprocess.run(["git", "remote"], cwd=dest, capture_output=True,
                            text=True, check=True).stdout.strip()
    assert count == "1"
    assert remote == ""


def test_verify_one_returns_a_row_per_property_and_never_an_empty_list(tmp_path) -> None:
    source = _mini_source(tmp_path)
    driver.build_one(source, tmp_path / "out", "police", False, driver.plan_build(source))
    rows = driver.verify_one(tmp_path / "out", source, "police", with_gates=False)
    assert len(rows) == 9
    names = [row.name for row in rows]
    assert len(set(names)) == len(names)
    assert not driver.overall(())


def test_both_outputs_are_built_from_one_manifest_and_one_timestamp(tmp_path) -> None:
    """Re-deriving per role would let a mid-build edit land in one repo only."""
    source = _mini_source(tmp_path)
    out = tmp_path / "both"
    code = driver.main(["--dest", str(out), "--source", str(source),
                        "--json", str(tmp_path / "evidence.json")])
    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert code == 1, "a miniature source cannot satisfy rule 50 -- an honest FAIL"
    assert [entry["role"] for entry in evidence] == ["police", "thief"]
    assert len({entry["source_commit"] for entry in evidence}) == 1
    assert len({entry["generated"] for entry in evidence}) == 1
    assert len({entry["staged"] for entry in evidence}) == 1
    assert len({entry["commit"] for entry in evidence}) == 2


def test_a_destination_inside_this_repository_exits_2_and_builds_nothing(capsys) -> None:
    target = REPO_ROOT / "should-never-exist"
    assert driver.main(["--dest", str(target)]) == 2
    assert "REFUSED" in capsys.readouterr().out
    assert not target.exists()
