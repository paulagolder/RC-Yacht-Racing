"""sail_number.py - comparing, sorting and writing sail numbers.

Sail numbers are text. They are matched ignoring case, spaces and leading zeros, so "1", "01"
and "   01" are the same boat.
"""

from __future__ import annotations

SAIL_NUMBER_WIDTH = 5      # new sail numbers are written right-aligned, like "   01"


def sail_key(sail_number: str) -> str:
    """The form used to compare sail numbers: '   01' -> '1', ' x1 ' -> 'X1'."""
    key = "".join(sail_number.split()).upper()
    return (key.lstrip("0") or "0") if key.isdigit() else key


def sort_key(sail_number: str) -> tuple:
    """Numbers in number order (2 before 10), then anything else."""
    key = sail_key(sail_number)
    return (0, int(key), "") if key.isdigit() else (1, 0, key)


def format_sail_number(text: str) -> str:
    """'1' -> '   01', '123' -> '  123': at least two digits, right-aligned like the members file."""
    text = text.strip()
    if text.isdigit():
        text = text.zfill(2)
    return text.rjust(SAIL_NUMBER_WIDTH)
