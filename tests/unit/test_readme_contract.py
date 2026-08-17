"""The root README is graded under rule 42, so the suite judges it (08-06).

`scripts/check_submission.py` already asks whether the README is COMPLETE.
These tests ask the questions that gate does not: whether the commands it
documents can be RUN, whether its links resolve, and whether it overstates in
the four places this project can least afford it -- mail, phase status, the
shipped strategy, and the games-played value (rule 38).

EVERY checker gets an anti-vacuity control. A test that a violation list is
empty is worthless unless the same function is shown to produce a NON-empty
list on text that deserves one, so each check is fired deliberately here.
"""

from __future__ import annotations

import pathlib

from tests.unit import readme_contract_checks as checks

README = pathlib.Path(checks.REPO_ROOT) / "README.md"


def readme() -> str:
    return README.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Sec2.1's seven items and Sec9.4.2's six sections
# --------------------------------------------------------------------------

def test_all_seven_segal_21_items_have_a_heading():
    assert checks.missing_headings(readme(), checks.SEGAL_21_HEADINGS) == []


def test_all_six_academic_942_sections_have_a_heading():
    assert checks.missing_headings(readme(), checks.ACADEMIC_942_HEADINGS) == []


def test_the_heading_checks_fire_on_a_file_with_no_headings():
    for table in (checks.SEGAL_21_HEADINGS, checks.ACADEMIC_942_HEADINGS):
        assert len(checks.missing_headings("no headings here", table)) == len(table)


# --------------------------------------------------------------------------
# Nothing documented may be unrunnable or unreachable
# --------------------------------------------------------------------------

def test_every_relative_link_and_image_resolves():
    assert checks.broken_relative_links(readme()) == []


def test_the_link_check_fires_on_an_absent_image():
    planted = "![shot](docs/assets/definitely-not-here.png)"
    assert checks.broken_relative_links(planted) == ["docs/assets/definitely-not-here.png"]


def test_the_link_check_ignores_external_targets():
    assert checks.broken_relative_links("[x](https://example.invalid/a.png)") == []


def test_every_repo_path_in_a_command_block_exists():
    assert checks.commands_naming_absent_paths(readme()) == []


def test_the_command_check_fires_on_the_deleted_run_1_plotter():
    planted = "```bash\nuv run python training/plot_curves.py out\n```"
    assert checks.commands_naming_absent_paths(planted) == ["training/plot_curves.py"]


def test_the_command_check_ignores_placeholder_paths():
    planted = "```bash\nuv run x --artifact game_artifacts/police/log_<game_id>_g01.json\n```"
    assert checks.commands_naming_absent_paths(planted) == []


# --------------------------------------------------------------------------
# The four overstatements this project can least afford
# --------------------------------------------------------------------------

def test_the_shipped_mail_mode_is_stated():
    assert checks.shipped_mail_modes(), "no shipped reporting.json was read"
    assert checks.mail_honesty_violations(readme()) == []


def test_the_mail_check_fires_when_the_readme_is_silent():
    assert checks.shipped_mail_modes() == {"dry_run"}
    assert sorted(checks.mail_honesty_violations("mail is fully working")) == [
        "dry_run", "pending",
    ]


def test_no_unverified_phase_reads_as_verified():
    assert checks.unverified_phases(), "nothing to judge -- every phase has a verification"
    assert checks.phase_status_violations(readme()) == []


def test_the_phase_check_fires_on_a_row_that_omits_the_caveat():
    number = checks.unverified_phases()[0]
    planted = f"| {number} | Reporting shell | Complete |"
    assert checks.phase_status_violations(planted)


def test_the_readme_names_the_brain_the_shipped_config_selects():
    assert checks.shipped_brain_modules(), "no brain module was derived from config/"
    assert checks.unnamed_shipped_brain(readme()) == []


def test_the_brain_check_fires_on_text_that_never_names_it():
    assert checks.unnamed_shipped_brain("a trained tabular policy") == \
        checks.shipped_brain_modules()


def test_no_games_played_counter_value_appears_in_the_readme():
    assert checks.games_played_leaks(readme()) == []


def counter_value() -> str:
    """The shipped counter's value here, or a same-shaped stand-in.

    `config/*/games_played.json` is gitignored live state (D-77): it does not
    exist in a fresh clone, and it does not exist in either split repository.
    Until 08-10 this test read it unconditionally and failed in both -- an
    assertion about the DETECTOR that could not run wherever the development
    machine's untracked files were missing. The real value is still preferred
    whenever it is present, so the detector goes on being proven against the
    number actually on disk here.
    """
    leaked = checks.REPO_ROOT / "config" / "police" / "games_played.json"
    if leaked.is_file():
        return leaked.read_text(encoding="utf-8").split(":")[1].strip(" }\n")
    return "1234"


def test_the_counter_check_fires_when_a_value_is_written_in():
    assert checks.games_played_leaks(f"we have played {counter_value()} games")
