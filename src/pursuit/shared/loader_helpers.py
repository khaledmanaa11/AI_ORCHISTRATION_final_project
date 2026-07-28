"""Shared fail-loud validation helpers for every JSON config loader in the project.

Extracted from shared/config.py at the second consumer (QUAL-02, CLAUDE.md Table 5:
"extract at 2+ copies"). Every loader in the project passes its own source filename
so error messages stay accurate without duplicating the validation logic.
"""


def require_key(data: dict, key: str, *, source: str) -> object:
    """Return data[key]; raise KeyError naming source if key is absent.

    Parameters
    ----------
    data:
        The parsed JSON object to read from.
    key:
        The required top-level (or nested) key.
    source:
        The filename to name in the error message (e.g. "game_params.json").

    Returns
    -------
    object
        The raw value stored at data[key].

    Raises
    ------
    KeyError
        If key is not present in data.
    """
    if key not in data:
        raise KeyError(f"Required key '{key}' missing from {source}")
    return data[key]


def require_int(data: dict, key: str, *, source: str) -> int:
    """Return data[key] as int; raise TypeError if the value is not an int.

    Raises
    ------
    KeyError
        If key is not present in data (checked before the type check).
    TypeError
        If the value stored at data[key] is not an int.
    """
    value = require_key(data, key, source=source)
    if not isinstance(value, int):
        raise TypeError(
            f"{source} field '{key}' must be int, got {type(value).__name__!r}"
        )
    return value


def require_str(data: dict, key: str, *, source: str) -> str:
    """Return data[key] as str; raise TypeError if the value is not a str.

    Raises
    ------
    KeyError
        If key is not present in data (checked before the type check).
    TypeError
        If the value stored at data[key] is not a str.
    """
    value = require_key(data, key, source=source)
    if not isinstance(value, str):
        raise TypeError(
            f"{source} field '{key}' must be str, got {type(value).__name__!r}"
        )
    return value
