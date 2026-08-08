"""Pure validation for the Figure-4 emission kernel and the Sec4.5 worked
example (D-50), split out of scent_config.py at the 150-code-line ceiling
(Segal Table 5, CLAUDE.md: split files, never compress code to fit) --
the same reason strategy_schema.py was split out of strategy_config.py.

No pursuit import here on purpose: this is plain numeric validation over
lists and floats, reusable without pulling in JSON loading, ScentKey, or
config_hash. scent_config.py is the only caller.
"""

from __future__ import annotations

import math

#: The source filename named in every error message from this module --
#: shared with scent_config.py so a raised ValueError always reads
#: "scent.json: ..." regardless of which module detected the problem.
SCENT_SOURCE = "scent.json"
_TOLERANCE = 1e-9


def validated_kernel(
    raw: object, *, window: int, source_value: float
) -> tuple[tuple[float, ...], ...]:
    """Return raw as a window x window tuple of floats, or raise ValueError.

    Every entry must lie in [0, source]; the grid must be symmetric under
    both reflections and the transpose (Figure 4 is radial in distance from
    the centre, so all three symmetries hold at once); the centre entry must
    equal source (D-50).
    """
    if not isinstance(raw, list) or len(raw) != window:
        raise ValueError(f"{SCENT_SOURCE}: 'kernel' must have {window} rows")
    rows = [
        _validated_row(row, row_index=i, window=window, source_value=source_value)
        for i, row in enumerate(raw)
    ]
    kernel = tuple(rows)

    centre = window // 2
    if not math.isclose(kernel[centre][centre], source_value, abs_tol=_TOLERANCE):
        raise ValueError(f"{SCENT_SOURCE}: 'kernel' centre entry must equal source")
    _check_symmetry(kernel, window=window)
    return kernel


def check_worked_example(initial: float, after: float, *, source: float, decay: float) -> None:
    """Raise ValueError unless worked_example is exactly what source/decay compute.

    Sec4.5's red box requires both peers verify the SAME numeric example
    before locking -- a file whose example disagrees with its own
    source/decay parameters is internally inconsistent and must be rejected
    before a game starts, not trusted at face value.
    """
    if not math.isclose(initial, source, abs_tol=_TOLERANCE):
        raise ValueError(f"{SCENT_SOURCE}: 'worked_example.initial' must equal 'source'")
    expected = source * (1.0 - decay)
    if not math.isclose(after, expected, abs_tol=_TOLERANCE):
        raise ValueError(
            f"{SCENT_SOURCE}: 'worked_example.after_one_turn'={after} "
            f"!= source*(1-decay)={expected}"
        )


def _validated_row(
    row: object, *, row_index: int, window: int, source_value: float
) -> tuple[float, ...]:
    """Return one kernel row as a tuple of `window` floats within [0, source_value]."""
    if not isinstance(row, list) or len(row) != window:
        raise ValueError(f"{SCENT_SOURCE}: 'kernel' row {row_index} must have {window} entries")
    parsed = []
    for j, entry in enumerate(row):
        if isinstance(entry, bool) or not isinstance(entry, int | float):
            raise ValueError(f"{SCENT_SOURCE}: 'kernel[{row_index}][{j}]' must be numeric")
        value = float(entry)
        if not 0.0 <= value <= source_value:
            raise ValueError(
                f"{SCENT_SOURCE}: 'kernel[{row_index}][{j}]'={value} outside [0, {source_value}]"
            )
        parsed.append(value)
    return tuple(parsed)


def _check_symmetry(kernel: tuple[tuple[float, ...], ...], *, window: int) -> None:
    """Raise ValueError unless kernel is symmetric under both axis
    reflections and the transpose -- the three symmetries Figure 4's
    radial-distance shape requires simultaneously."""
    for i in range(window):
        for j in range(window):
            value = kernel[i][j]
            mirrors = (kernel[window - 1 - i][j], kernel[i][window - 1 - j], kernel[j][i])
            if any(not math.isclose(value, m, abs_tol=_TOLERANCE) for m in mirrors):
                raise ValueError(f"{SCENT_SOURCE}: 'kernel' not symmetric at ({i},{j})")
