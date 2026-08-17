"""Rules 39-40 on the mail path, and the honesty of `test_mail_sink_dry_run.py`.

Three subjects, all about what must NOT be somewhere:

* no credential reaches git -- `.env-example` carries the two env-var NAMES
  with dummy values, `.gitignore` still excludes the files they point at, and
  every shipped `reporting.json` still reads `dry_run`;
* the dry-run sink's test file does not smuggle in a REPORT-04 claim. That is
  checked by an AST identifier scan rather than a text search, so the prose in
  its docstring (which legitimately NAMES 429 and scope in explaining that it
  asserts neither) cannot make the check either pass or fail dishonestly. Every
  scan is paired with a control file where the scan DOES find something.
* NO SOURCE OR TEST FILE IS GIT-IGNORED. This file was originally written as
  `test_gmail_secrets.py` and `.gitignore:26`'s `*_secret*` -- a rules-39-40
  guard that is correct and must not be weakened -- swallowed it silently. A
  test file git ignores is a test that never runs in CI and never reaches the
  grader, which is the most complete form of the vacuity this phase keeps
  finding. Renamed, and the class of mistake is now checked rather than
  remembered.
"""

import ast
import json
import re
from pathlib import Path

import pytest

from pursuit.services.reporting.gmail_sink import GMAIL_SEND_SCOPE
from pursuit.shared.reporting_config import ReportingMode, load_reporting_config
from tests.unit.gitignore_probe import git_available, git_ignored
from tests.unit.gmail_fixtures import CONFIG_ROOT, TOO_MANY_REQUESTS

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = REPO_ROOT / ".env-example"
GITIGNORE = REPO_ROOT / ".gitignore"
DRY_RUN_TEST = Path(__file__).with_name("test_mail_sink_dry_run.py")
LIVE_TEST = Path(__file__).with_name("test_gmail_sink.py")
FIXTURES = Path(__file__).with_name("gmail_fixtures.py")

SHIPPED_ROLES = ("police", "thief")
DUMMY_VALUE = re.compile(r"^your-[a-z0-9-]+-here$")

#: The names that would mean the dry-run sink's test file was asserting
#: something only the live path can prove.
LIVE_PATH_NAMES = frozenset({
    "GmailSink", "GmailRetryableError", "GmailScopeError", "GmailCredentialsError",
    "build_gmail_transport", "require_send_only_scope", "load_send_only_credentials",
    "Gatekeeper", "ReportingChain", "FakeGmailTransport", "build_mail_chain",
})

#: Written into `.gitignore` before the OAuth code existed, with a comment
#: saying so. A plan that adds the OAuth code must not remove them.
OAUTH_IGNORE_ENTRIES = (
    "credentials.json", "client_secret*.json", "token.json", "token.pickle", "*.token", ".env",
)


def _identifiers(path: Path) -> set[str]:
    """Every name, attribute and import in a module -- ignoring all prose,
    because a docstring is an `ast.Constant`, not an `ast.Name`."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Import | ast.ImportFrom):
            names.update(alias.name for alias in node.names)
    return names


def _int_literals(path: Path) -> set[int]:
    return {
        node.value
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant) and isinstance(node.value, int)
    }


def _env_example_values() -> dict[str, str]:
    entries = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            name, _, value = stripped.partition("=")
            entries[name] = value
    return entries


@pytest.mark.parametrize("role", SHIPPED_ROLES)
def test_both_env_var_names_have_a_dummy_entry_in_env_example(role):
    params = load_reporting_config(CONFIG_ROOT / role / "reporting.json")
    entries = _env_example_values()
    for name in (params.credentials_env_var, params.token_env_var):
        assert name in entries, f"{name} is named by reporting.json but absent from .env-example"
        assert DUMMY_VALUE.match(entries[name]), f"{name} carries a non-dummy value"


def test_the_shipped_roles_table_is_not_empty():
    assert len(SHIPPED_ROLES) == 2


@pytest.mark.parametrize("role", SHIPPED_ROLES)
def test_every_shipped_config_still_transmits_nothing(role):
    raw = json.loads((CONFIG_ROOT / role / "reporting.json").read_text(encoding="utf-8"))
    assert raw["reporting"]["mode"] == ReportingMode.DRY_RUN.value


@pytest.mark.parametrize("entry", OAUTH_IGNORE_ENTRIES)
def test_the_oauth_secret_ignore_entries_survive_this_plan(entry):
    lines = {line.strip() for line in GITIGNORE.read_text(encoding="utf-8").splitlines()}
    assert entry in lines


def test_the_oauth_ignore_table_is_not_empty():
    assert len(OAUTH_IGNORE_ENTRIES) == 6


def test_env_example_holds_no_value_long_enough_to_be_a_real_credential():
    """Every value is a `your-...-here` placeholder, so nothing here can be a
    pasted key, token or path."""
    offenders = [
        name for name, value in _env_example_values().items()
        if not (DUMMY_VALUE.match(value) or value.endswith("_here"))
    ]
    assert offenders == []


def test_the_dry_run_test_file_makes_no_live_path_claim():
    assert _identifiers(DRY_RUN_TEST) & LIVE_PATH_NAMES == set()


def test_control_the_live_path_scan_finds_names_in_the_live_test_file():
    """Without this the scan above would pass against a broken parser."""
    assert _identifiers(LIVE_TEST) & LIVE_PATH_NAMES != set()


def test_the_dry_run_test_file_carries_no_429_literal():
    assert TOO_MANY_REQUESTS not in _int_literals(DRY_RUN_TEST)


def test_control_the_literal_scan_finds_429_where_it_belongs():
    assert TOO_MANY_REQUESTS in _int_literals(FIXTURES)


def test_the_send_scope_is_googles_own_send_only_identifier():
    assert GMAIL_SEND_SCOPE == "https://www.googleapis.com/auth/gmail.send"


def test_no_source_or_test_file_is_swallowed_by_gitignore():
    """A `.gitignore` secret pattern silently ate this very file once. It fails
    rather than skips without git: a gate that reports OK for having looked at
    nothing is worse than no gate (the D7-6 standard)."""
    assert git_available(), "git is unavailable, so this gate cannot vouch for anything"
    sources = [
        path
        for root in ("src", "tests", "training", "scripts")
        for path in (REPO_ROOT / root).rglob("*.py")
        if "__pycache__" not in path.parts
    ]
    assert len(sources) > 100, "the scan found almost nothing, so it proves nothing"
    assert git_ignored(sources) == []


def test_control_the_gitignore_scan_finds_a_file_that_is_ignored():
    """Without this, the scan above would pass against a broken subprocess
    call. `.env` is ignored on purpose and always has been."""
    assert git_ignored([REPO_ROOT / ".env"]) != []
