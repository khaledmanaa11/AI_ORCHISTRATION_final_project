"""`docs/QUALITY-25010.md` and `docs/EXTENSION-POINTS.md`: every claim points at
a path that exists (08-07).

THE FAILURE MODE THESE TWO DOCUMENTS INVITE. Sec17 asks for an ISO/IEC 25010
mapping and for documented extension points. The cheap version of the first
lists the eight characteristic names and cites nothing -- which is why
`submission_research._iso_row` refuses a document that names all eight without
citing repo paths, and why this file goes further: EACH characteristic must
carry its own evidence, and every path either document cites must be tracked.

The eight names are parsed out of `docs/SEGAL_GUIDELINES.md` Sec13, never typed
here, so the checklist cannot drift from the standard it claims to follow. A
document citing `training/plot_curves.py` -- deleted in `f3d9847` and left in
the README until 08-06 -- fails on the citation, not on a reviewer noticing.
"""

from __future__ import annotations

import re

from tests.unit.doc_citation_helpers import CITED, cited_paths, unresolved_citations
from tests.unit.submission_gate_helpers import load

common = load("submission_common")
research = load("submission_research")

QUALITY = "docs/QUALITY-25010.md"
EXTENSION = "docs/EXTENSION-POINTS.md"
#: The real seams `.planning/phases/08-.../08-PLAN-OUTLINE.md` Sec9 names.
SEAMS = (
    "src/pursuit/strategy/base.py",
    "src/pursuit/strategy/registry.py",
    "src/pursuit/services/reporting/sink.py",
    "src/pursuit/services/llm/provider.py",
)


_cited = cited_paths
_unresolved = unresolved_citations


def test_both_documents_are_tracked():
    assert common.is_tracked(QUALITY)
    assert common.is_tracked(EXTENSION)


def test_the_quality_model_cites_only_paths_that_exist():
    assert _unresolved(QUALITY) == []


def test_the_extension_points_document_cites_only_paths_that_exist():
    assert _unresolved(EXTENSION) == []


def test_the_citation_scan_is_not_vacuous():
    """An empty citation set would make both tests above pass having read
    nothing -- the exact vacuity D-82's exit-2 contract exists to refuse."""
    assert len(_cited(QUALITY)) >= 20, _cited(QUALITY)
    assert len(_cited(EXTENSION)) >= 10, _cited(EXTENSION)


def test_the_eight_characteristics_come_from_the_extract_not_from_this_test():
    assert len(research._iso_characteristics()) == 8, research._iso_characteristics()


def test_every_characteristic_carries_its_own_repo_evidence():
    """Naming the eight is not the requirement; mapping each one is."""
    text = common.read_tracked(QUALITY)
    sections = re.split(r"^##+ ", text, flags=re.MULTILINE)
    for name in research._iso_characteristics():
        owning = [part for part in sections if part.lower().startswith(name)]
        assert owning, f"no section headed {name!r}"
        assert CITED.findall(owning[0]), f"{name!r} maps to prose, not to a path"


def test_the_documented_extension_points_are_the_real_seams():
    text = common.read_tracked(EXTENSION)
    for seam in SEAMS:
        assert seam in text, seam


def test_the_extension_points_document_names_the_registered_brains():
    """Derived from the registry, so a brain added or withdrawn breaks this."""
    registry = common.read_tracked("src/pursuit/strategy/registry.py")
    text = common.read_tracked(EXTENSION)
    names = re.findall(r"^\s+(\w+_NAME): (\w+),", registry, flags=re.MULTILINE)
    assert len(names) == 3, names
    for _, klass in names:
        assert klass in text, f"{klass} is registered but undocumented"


def test_no_withdrawn_mechanism_is_offered_as_an_extension_point():
    """`docs/PRD_rl_strategy.md` is superseded; `QLearningBrain` never shipped."""
    for path in (QUALITY, EXTENSION):
        assert "QLearningBrain" not in common.read_tracked(path)
