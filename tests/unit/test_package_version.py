"""Sec14 professional packaging -- `__version__` on the package (08-03).

WHY THE SECOND TEST IS THE IMPORTANT ONE. `pursuit.__version__ == VERSION` is
satisfied just as well by `__version__ = "1.00"` typed into `__init__.py`, and
that spelling is the defect this test exists to prevent: two version literals in
two files, one of which Table 5's T5-06 row reads and one of which nobody reads
until they disagree. The repository is already carrying one instance of exactly
that (`shared/version.py` `1.00` against `pyproject.toml` `1.00.0`, registered as
T5-06 and owned by 08-11). So the file is PARSED and required to contain no
version-shaped literal at all, which only a re-export can satisfy.
"""

from __future__ import annotations

import re
from pathlib import Path

import pursuit
from pursuit.shared.version import VERSION

INIT = Path(pursuit.__file__)
#: Any dotted numeric literal -- `"1.00"`, `"1.00.0"`, `'2.0'`.
_VERSION_LITERAL = re.compile(r"""["']\d+\.\d[\d.]*["']""")


def test_the_package_exposes_a_version() -> None:
    assert getattr(pursuit, "__version__", None), "pursuit declares no __version__"


def test_the_exposed_version_is_the_single_source_of_truth() -> None:
    assert pursuit.__version__ == VERSION


def test_the_init_file_contains_no_version_literal_of_its_own() -> None:
    """A re-export can pass this; a second typed literal cannot."""
    source = INIT.read_text(encoding="utf-8")
    literals = _VERSION_LITERAL.findall(source)
    assert not literals, (
        f"{INIT.name} writes its own version literal(s) {literals}; the version "
        f"must be re-exported from shared/version.py, which is the source T5-06 reads"
    )


def test_the_literal_detector_actually_matches_a_literal() -> None:
    """The control: an all-clear from a pattern that matches nothing is not one."""
    assert _VERSION_LITERAL.findall('__version__ = "1.00"')
    assert _VERSION_LITERAL.findall("__version__ = '1.00.0'")
