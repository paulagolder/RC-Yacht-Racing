"""grid_navigation.py - where the cursor goes in the race day window's table.

No tkinter here, so the rules can be tested without a screen.
"""

from __future__ import annotations

from ..model.limits import MAX_PLACES


def next_cell_position(row: int, col: int, n_rows: int, n_cols: int,
                       max_rows: int = MAX_PLACES) -> tuple[int, int, bool]:
    """Where Enter/Tab goes next: down the column.

    Returns (row, col, add_row). add_row is True when the target row does not exist
    yet and the table is still allowed to grow. At the bottom of a full table the
    cursor moves to the top of the next column (wrapping from the last column to the first).
    """
    if row + 1 < n_rows:
        return row + 1, col, False
    if n_rows < max_rows:
        return row + 1, col, True
    return 0, (col + 1) % n_cols, False


def previous_cell_position(row: int, col: int, n_rows: int, n_cols: int) -> tuple[int, int]:
    """Where Shift+Tab / Up goes: up the column, or to the bottom of the previous column."""
    if row > 0:
        return row - 1, col
    return n_rows - 1, (col - 1) % n_cols
