"""The two generated documents a split repository carries (08-10).

RULE 49 WANTS TWO REAL, CROSS-LINKED REPOSITORY LINKS. They do not exist: the
repositories are created and pushed by a human at 08-12. So both links are
written as a STATED-ABSENT marker and the tests assert that no URL-shaped string
survives anywhere in either document.

A PLACEHOLDER WOULD BE WORSE THAN A HOLE. `https://github.com/<user>/pursuit-cop`
reads as done to every human and every grep that goes looking, and nothing later
in the pipeline distinguishes it from a real link. A hole announces itself. This
is the discipline 08-04 already applied to `league.json`, whose loader refuses a
placeholder outright when `reporting.mode = live` (D-81).

THE INJECTION ANCHOR IS CHECKED, NOT ASSUMED. A splitter that cannot find the
README's H1 and returns the text unchanged produces a repository with no
cross-link while reporting success -- so `inject` raises, both when the anchor is
missing and when the banner is already there.
"""

from __future__ import annotations

#: Each role's companion repository.
COMPANION = {"police": "thief", "thief": "police"}
#: How each role's agent is named in prose.
ROLE_NOUN = {"police": "cop", "thief": "thief"}
#: The machine-checkable marker `split_verify` looks for in a built README.
MARKER = "<!-- split-repo-banner"
#: The stated-absent value. Not a URL, not a placeholder, not empty.
URL_ABSENT = "**NOT ASSIGNED — the repository is not created or pushed yet (08-12)**"


class MissingAnchorError(RuntimeError):
    """The README has no `# ` heading, or already carries a banner."""


class EmptyBuildError(RuntimeError):
    """A provenance document was asked to describe a zero-file build."""


def banner(role: str, source_commit: str, generated: str) -> str:
    """The rule-49 cross-link block for *role*, with both links stated absent."""
    other = COMPANION[role]
    return "\n".join((
        f"{MARKER} role={role} source={source_commit} -->",
        "",
        f"> **This is the `{role}` repository — the {ROLE_NOUN[role]} agent — one half of a",
        "> two-repository submission (rule 49).** It is generated from the development",
        f"> repository at commit `{source_commit}` on {generated} by",
        "> `scripts/build_split_repos.py`, from `git ls-files` and nothing else.",
        ">",
        "> | Rule-49 link | Value |",
        "> |---|---|",
        f"> | This repository (`{role}`) | {URL_ABSENT} |",
        f"> | Companion repository (`{other}`) | {URL_ABSENT} |",
        ">",
        "> **Both links are stated absent rather than filled with a plausible-looking",
        "> value.** Inventing one would read as done to every human and every search that",
        f"> went looking for it. `config/{role}/league.json` carries the same two fields and",
        "> its loader refuses a placeholder when reporting runs live. Filling them in is a",
        "> human step.",
        ">",
        "> Both `config/police/` and `config/thief/` ship here: the test suite loads both",
        "> seats, so a repository carrying one of them could not run its own gates. The two",
        "> agents remain separate PROCESSES with no shared runtime state (rule 2); these are",
        "> two static directories of JSON.",
        ">",
        "> The live games-played counters are deliberately absent — see",
        "> `docs/REPO-SPLIT.md`.",
        "",
    ))


def inject(readme_text: str, banner_text: str) -> str:
    """Place *banner_text* immediately after the README's first `# ` heading."""
    if MARKER in readme_text:
        raise MissingAnchorError(
            "this README already carries a split banner; injecting a second one would "
            "ship two contradictory rule-49 blocks."
        )
    lines = readme_text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            head = lines[: index + 1]
            tail = lines[index + 1:]
            return "\n".join([*head, "", banner_text.rstrip("\n"), *tail]) + "\n"
    raise MissingAnchorError(
        "the README has no top-level `# ` heading, so the rule-49 cross-link block has "
        "nowhere to go. Refusing to return the README unchanged: a split repository "
        "without its cross-link is the defect this build exists to prevent."
    )


def provenance(role: str, source_commit: str, generated: str, included: int,
               excluded: tuple[tuple[str, str], ...]) -> str:
    """`docs/REPO-SPLIT.md` for the built repository: what shipped, and what did not."""
    if included <= 0:
        raise EmptyBuildError(
            f"provenance asked to describe a build of {included} files. An empty "
            "repository passes every gate by looking at nothing."
        )
    rows = "\n".join(f"| `{path}` | {reason} |" for path, reason in excluded) or \
        "| _(none)_ | the tracked set carried nothing that had to be subtracted |"
    return "\n".join((
        f"# Repository split — the `{role}` half",
        "",
        f"Generated {generated} from the development repository at commit "
        f"`{source_commit}` by `scripts/build_split_repos.py`.",
        "",
        "## How the file list was derived",
        "",
        "`git ls-files` on the source repository, minus the subtractions below. **Never a",
        "directory walk**: the development tree holds an untracked `.env` and an untracked",
        "copy of the course book, and a walk would publish a live credential and a",
        "copyrighted text in one step. The tracked set contains neither, by construction.",
        "",
        f"**Files in this repository: {included}.**",
        "",
        "## What was subtracted, and why",
        "",
        "| Path | Reason |",
        "|---|---|",
        rows,
        "",
        "The live games-played counters (`config/*/games_played*.json`) are the number this",
        "team declares to the league. They are gitignored in the source repository, so they",
        "were never in the tracked set; the build subtracts them BY NAME as well, so a",
        "future force-add cannot carry them here. Misreporting that number is an absolute",
        "disqualification, and a stale copy travelling inside a public repository is a way",
        "to misreport it by accident.",
        "",
        "## Both seats' configuration ships",
        "",
        "`config/police/` and `config/thief/` are both present. The test suite loads both,",
        "so a repository carrying one could not run its own quality gates. The two agents",
        "are still separate processes with no shared runtime state (rule 2).",
        "",
        "## Before your first commit here",
        "",
        "```bash",
        "git config core.hooksPath scripts/hooks   # the 150-line + ruff pre-commit gate",
        "uv sync                                   # uv only; there is no requirements file",
        "```",
        "",
    ))
